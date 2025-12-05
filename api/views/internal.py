"""
Internal API endpoints for service-to-service communication.

These endpoints are restricted to internal Docker network access only.
Used by LARA backend to fetch data from Lexa.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import serializers
from django.conf import settings

from domains.models import Domain, DomainGroup
from users.models import User


# =============================================================================
# Permission class for internal network access
# =============================================================================

class IsInternalNetwork:
    """
    Permission that restricts access to internal Docker network IPs.
    Allows: 127.0.0.1, 172.x.x.x (Docker networks), 10.x.x.x (private)
    """

    ALLOWED_PREFIXES = (
        '127.0.0.1',
        '172.',      # Docker bridge networks
        '10.',       # Private networks
        '192.168.',  # Private networks
    )

    def has_permission(self, request, view):
        # Get the real IP from headers (nginx sets X-Real-IP)
        ip = request.META.get('HTTP_X_REAL_IP') or \
             request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip() or \
             request.META.get('REMOTE_ADDR', '')

        # In DEBUG mode, allow all access for testing
        if settings.DEBUG:
            return True

        # Check if IP is in allowed ranges
        return any(ip.startswith(prefix) for prefix in self.ALLOWED_PREFIXES)


# =============================================================================
# Serializers
# =============================================================================

class InternalDomainSerializer(serializers.ModelSerializer):
    """Serializer for Domain model in internal API."""

    class Meta:
        model = Domain
        fields = ['id', 'name', 'french_name', 'icon', 'featured']


class InternalDomainGroupSerializer(serializers.ModelSerializer):
    """Serializer for DomainGroup with nested domains."""

    domains = InternalDomainSerializer(many=True, read_only=True)

    class Meta:
        model = DomainGroup
        fields = ['id', 'name', 'french_name', 'icon', 'domains']


class InternalUserSerializer(serializers.ModelSerializer):
    """Serializer for User model in internal API."""

    customer_id = serializers.CharField(source='stripe_customer_id')

    class Meta:
        model = User
        fields = [
            'id',
            'uuid',
            'username',
            'email',
            'first_name',
            'last_name',
            'customer_id',
            'language',
            'is_active',
        ]


# =============================================================================
# Views
# =============================================================================

class InternalDomainGroupsView(APIView):
    """
    GET /api/internal/domain-groups/

    Returns list of all domain groups with their associated domains.
    Restricted to internal network access.
    """

    permission_classes = [IsInternalNetwork]

    def get(self, request):
        domain_groups = DomainGroup.objects.prefetch_related('domains').all()
        serializer = InternalDomainGroupSerializer(domain_groups, many=True)
        return Response(serializer.data)


class InternalUsersView(APIView):
    """
    GET /api/internal/users/
    GET /api/internal/users/?customer_id=cus_xxx

    Returns list of users or a specific user by customer_id (Stripe ID).
    Restricted to internal network access.
    """

    permission_classes = [IsInternalNetwork]

    def get(self, request):
        customer_id = request.query_params.get('customer_id')

        if customer_id:
            # Return specific user by customer_id
            try:
                user = User.objects.get(stripe_customer_id=customer_id)
                serializer = InternalUserSerializer(user)
                return Response(serializer.data)
            except User.DoesNotExist:
                return Response(
                    {'error': 'User not found', 'customer_id': customer_id},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            # Return all users (with pagination in production)
            users = User.objects.filter(is_active=True)[:100]  # Limit for safety
            serializer = InternalUserSerializer(users, many=True)
            return Response(serializer.data)


class InternalUserDetailView(APIView):
    """
    GET /api/internal/users/<uuid>/

    Returns user details by UUID.
    Restricted to internal network access.
    """

    permission_classes = [IsInternalNetwork]

    def get(self, request, uuid):
        try:
            user = User.objects.get(uuid=uuid)
            serializer = InternalUserSerializer(user)
            return Response(serializer.data)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found', 'uuid': str(uuid)},
                status=status.HTTP_404_NOT_FOUND
            )
