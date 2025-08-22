import csv
import io
import os.path

import django.core.exceptions
import openpyxl
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db.models.functions import Lower
from django.core.paginator import Paginator
from django.views.generic import TemplateView
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import Group
from django.db.models import Count, Q

from rest_framework import status
from rest_framework.generics import RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import serializers

from domains.models import Domain
from languages.models import Language
from subscriptions.permissions import SubscribedPermission
from users.models import User
from .models import Glossary
from .processor import GlossaryProcessor
from .serializers import GlossarySerializer
from .paginators import APIViewPagination, TemplateViewPagination


# Create your views here.

class UserGlossariesView(TemplateView):
    template_name = 'glossaries.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        glossaries_data, pagination_context = self.get_glossaries()
        context['glossaries'] = glossaries_data
        context['translate_languages'] = self.get_languages()
        context['paginator'] = pagination_context
        return context

    def get_languages(self):
        if self.request.LANGUAGE_CODE == 'fr':
            return Language.objects.order_by('french_name').all()
        return Language.objects.order_by('name').all()

    def get_glossaries(self):
        tmp_glossaries = Glossary.objects.filter(user=self.request.user)

        paginator = TemplateViewPagination()
        paginated_glossaries = paginator.paginate_queryset(
            tmp_glossaries, self.request)

        formatted_glossaries = [
            glossary.to_json(self.request)
            for glossary in paginated_glossaries
        ]
        return formatted_glossaries, paginator.get_paginated_context()


class UserGlossariesView2(TemplateView):
    template_name = 'glossaries_2.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        glossaries_data, pagination_context = self.get_glossaries()
        context['glossaries'] = glossaries_data
        context['translate_languages'] = self.get_languages()
        context['paginator'] = pagination_context
        return context

    def get_languages(self):
        if self.request.LANGUAGE_CODE == 'fr':
            return Language.objects.order_by('french_name').all()
        return Language.objects.order_by('name').all()

    def get_glossaries(self):
        tmp_glossaries = Glossary.objects.filter(user=self.request.user)

        paginator = TemplateViewPagination()
        paginated_glossaries = paginator.paginate_queryset(
            tmp_glossaries, self.request)

        formatted_glossaries = [
            glossary.to_json(self.request)
            for glossary in paginated_glossaries
        ]
        return formatted_glossaries, paginator.get_paginated_context()


class AddGlossaryView(APIView):
    permission_classes = (SubscribedPermission, IsAuthenticated)

    @staticmethod
    def validate(request):
        if not request.user.is_staff:
            user_subscription = request.user.subscriptions.first()
            if user_subscription.custom_glossaries_count > 0:
                user_glossaries_count = Glossary.objects.filter(
                    user=request.user).count()
                if user_glossaries_count + 1 > user_subscription.custom_glossaries_count:
                    raise serializers.ValidationError({
                        "detail": "You are not allowed to add more glossaries. Please contact your group administator"})

        languages_list = Language.objects.all().values_list(
            Lower('abbreviation'), flat=True)
        if request.data["source_language"] == request.data["target_language"]:
            raise serializers.ValidationError(
                {"detail": _("Source and target languages cannot be the same")})
        if request.data["source_language"] not in languages_list:
            raise serializers.ValidationError(
                {"detail": _("Invalid source language")})
        if request.data["target_language"] not in languages_list:
            raise serializers.ValidationError(
                {"detail": _("Invalid target language")})

        gloss_file = request.FILES.get('file')
        processor = GlossaryProcessor()
        if os.path.splitext(gloss_file.name)[1] == '.csv':
            request.FILES['file'] = processor.convert_file_to_utf_8(gloss_file)
        try:
            processor.validate_file(gloss_file)
        except django.core.exceptions.ValidationError as e:
            raise serializers.ValidationError({"detail": str(list(e)[0])})

    def post(self, request):
        self.validate(request)
        gloss_file = request.FILES.get('file')
        source_language = Language.objects.get(
            abbreviation__iexact=request.data.get('source_language').upper())
        target_language = Language.objects.get(
            abbreviation__iexact=request.data.get('target_language').upper())

        glossary = Glossary.objects.create(
            user=request.user,
            source_language=source_language,
            target_language=target_language,
            file=gloss_file,
        )
        return Response(GlossarySerializer(glossary).data, status=status.HTTP_201_CREATED)


class SingleGlossaryView(RetrieveUpdateDestroyAPIView):
    serializer_class = GlossarySerializer

    def get_object(self):
        return Glossary.objects.filter(user=self.request.user, id=self.kwargs['pk']).first()


class GlossariesListAPIView(APIView):
    permission_classes = (SubscribedPermission, IsAuthenticated)

    def post(self, request, *args, **kwargs):
        if 'source_language' and 'target_language' and 'domain_name' not in request.data:
            return Response(
                {"detail": "provide source_language, target_language and domain_name"},
                status=status.HTTP_400_BAD_REQUEST
            )
        glossaries = Glossary.objects.filter(
            source_language__abbreviation=request.data.get(
                'source_language').upper(),
            target_language__abbreviation=request.data.get(
                'target_language').upper()
        )
        user_glossaries = glossaries.filter(
            user=request.user, group__isnull=True
        )
        group_glossaries = glossaries.filter(
            group=request.user.group,
            group__isnull=False
        )
        glossaries = user_glossaries | group_glossaries

        return Response(GlossarySerializer(glossaries, many=True).data, status=status.HTTP_200_OK)


class GetDefaultGlossaryView(APIView):
    permission_classes = (SubscribedPermission, IsAuthenticated)
    serializer_class = GlossarySerializer

    def post(self, request):
        domain_name = request.data.get('domain_name')
        glossary = Glossary.objects.filter(
            source_language__abbreviation=request.data.get(
                'source_language').upper(),
            target_language__abbreviation=request.data.get(
                'target_language').upper()
        ).all()
        if request.LANGUAGE_CODE == 'fr':
            default_glossary = glossary.filter(domain__french_name=domain_name)
            if not default_glossary.exists():
                default_glossary = glossary.filter(domain__name=domain_name)
        else:
            default_glossary = glossary.filter(domain__name=domain_name)
        glossary = default_glossary.first()
        if glossary:
            return Response(GlossarySerializer(glossary).data, status=status.HTTP_200_OK)
        return Response({}, status=status.HTTP_200_OK)


class MyTeamView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """
    Team management view for administrators.
    Only group administrators can access this view.
    """
    template_name = 'myteam.html'
    
    def test_func(self):
        """Check if user is an admin of any group"""
        # Check if user is staff or is admin of their group
        if self.request.user.is_staff:
            return True
        
        # Check if user is admin of their group
        user_group = getattr(self.request.user, 'group', None)
        if user_group:
            return user_group.admin.filter(id=self.request.user.id).exists()
        
        return False
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get team members based on user's group membership
        team_members, paginator_info = self.get_team_members()
        
        # Calculate stats on the full dataset, not just the current page
        stats = self.get_team_stats()
        
        # Get search query to preserve it in the template
        search_query = self.request.GET.get('search', '')
        
        context.update({
            'team_members': team_members,
            'stats': stats,
            'paginator': paginator_info,
            'search_query': search_query
        })
        
        return context
    
    def get_team_members(self):
        """Get team members with pagination and search"""
        # If user is staff, show all users; otherwise show group members
        if self.request.user.is_staff:
            queryset = User.objects.all()
        else:
            # Get users from the same group
            user_group = getattr(self.request.user, 'group', None)
            if user_group:
                queryset = User.objects.filter(group=user_group)
            else:
                queryset = User.objects.none()
        
        # Apply search filter if search parameter is provided
        search_query = self.request.GET.get('search', '').strip()
        if search_query:
            # Search in first_name, last_name, and email fields
            queryset = queryset.filter(
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query) |
                Q(email__icontains=search_query)
            )
        
        # Add annotations for better performance
        queryset = queryset.select_related('group').order_by('first_name', 'last_name')
        
        # Pagination
        paginator = Paginator(queryset, 10)  # 10 users per page
        page_number = self.request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
        
        # Add computed fields for each member
        members_with_data = []
        for user in page_obj:
            member_data = {
                'id': user.id,
                'first_name': user.first_name or 'Unknown',
                'last_name': user.last_name or 'User',
                'email': user.email,
                'initials': self.get_user_initials(user),
                'is_admin': self.check_admin_status(user),
                'is_premium': self.check_premium_status(user),
                'date_joined': user.date_joined,
            }
            members_with_data.append(member_data)
        
        paginator_info = {
            'current_page': page_obj.number,
            'total_pages': paginator.num_pages,
            'has_previous': page_obj.has_previous(),
            'has_next': page_obj.has_next(),
            'previous_page_number': page_obj.previous_page_number() if page_obj.has_previous() else None,
            'next_page_number': page_obj.next_page_number() if page_obj.has_next() else None,
            'page_range': paginator.page_range,
            'has_multiple_pages': paginator.num_pages > 1,
        }
        
        return members_with_data, paginator_info
    
    def get_team_stats(self):
        """Calculate team statistics from the full dataset"""
        # Get the same queryset used for team members, but without pagination
        if self.request.user.is_staff:
            queryset = User.objects.all()
        else:
            # Get users from the same group
            user_group = getattr(self.request.user, 'group', None)
            if user_group:
                queryset = User.objects.filter(group=user_group)
            else:
                queryset = User.objects.none()
        
        # Calculate statistics on the full queryset
        total_users = queryset.count()
        
        # Count admin users
        admin_users = 0
        premium_users = 0
        
        for user in queryset:
            if self.check_admin_status(user):
                admin_users += 1
            if self.check_premium_status(user):
                premium_users += 1
        
        return {
            'total_users': total_users,
            'admin_users': admin_users,
            'premium_users': premium_users,
        }
    
    def get_user_initials(self, user):
        """Generate user initials from first and last name"""
        first_initial = user.first_name[0].upper() if user.first_name else 'U'
        last_initial = user.last_name[0].upper() if user.last_name else 'U'
        return f"{first_initial}{last_initial}"
    
    def check_admin_status(self, user):
        """Check if user is admin of their group"""
        if user.is_staff or user.is_superuser:
            return True
        
        user_group = getattr(user, 'group', None)
        if user_group:
            return user_group.admin.filter(id=user.id).exists()
        
        return False
    
    def check_premium_status(self, user):
        """Check if user has premium subscription"""
        # This would be replaced with actual subscription logic
        # For now, we'll consider staff users as premium
        return user.is_staff or hasattr(user, 'subscription') and getattr(user.subscription, 'is_premium', False)
