"""
API URL Configuration for Legal230 Application

This module defines the URL patterns for the REST API endpoints,
including routes for translation, domain, language, and glossary
management with proper versioning.
"""

# Django imports
from django.urls import path

# Local imports
from .views.domain import DomainListAPIView, DomainDefaultGlossariesAPIView
from .views.glossary import GlossaryAPIView, GlossaryExistAPIView
from .views.language import LanguageAPIView
from .views.translate import TranslateAPIView
from .views.stripe import StripePortalSessionView, StripePricingPageUrlView
from .views.swagger import SwaggerUIView, SwaggerYAMLView
from .views.internal import (
    InternalDomainGroupsView,
    InternalUsersView,
    InternalUserDetailView,
    InternalSubscriptionByApiKeyView,
)


# API version configuration
API_VERSION = 'v1/'

urlpatterns = [
    # Documentation
    path(API_VERSION + 'docs/', SwaggerUIView.as_view(), name='api-swagger-ui'),
    path(API_VERSION + 'swagger.yaml', SwaggerYAMLView.as_view(), name='api-swagger-yaml'),

    # Domain endpoints
    path(
        API_VERSION + 'domains/',
        DomainListAPIView.as_view(),
        name='api-domain-list'
    ),
    path(
        API_VERSION + 'domain/<int:id_domain>/glossaries/',
        DomainDefaultGlossariesAPIView.as_view(),
        name='api-domain-glossaries'
    ),

    # Glossary endpoints
    path(
        API_VERSION + 'glossary/',
        GlossaryAPIView.as_view(),
        name='api-glossary'
    ),
    path(
        API_VERSION + 'glossary/<int:id_glossary>/',
        GlossaryExistAPIView.as_view(),
        name='api-glossary-exist'
    ),
    path(
        API_VERSION + 'glossaries/',
        GlossaryExistAPIView.as_view(),
        name='api-glossaries'
    ),

    # Language endpoints
    path(
        API_VERSION + 'languages/',
        LanguageAPIView.as_view(),
        name='api-languages'
    ),

    # Translation endpoints
    path(
        API_VERSION + 'translate/',
        TranslateAPIView.as_view(),
        name='api-translate'
    ),

    # Stripe endpoints
    path(
        API_VERSION + 'stripe-portal-session/',
        StripePortalSessionView.as_view(),
        name='api-stripe-portal-session'
    ),
    path(
        API_VERSION + 'stripe-pricing-page-url/',
        StripePricingPageUrlView.as_view(),
        name='api-stripe-pricing-page-url'
    ),

    # ==========================================================================
    # Internal API endpoints (service-to-service, restricted to Docker network)
    # ==========================================================================
    path(
        'internal/domain-groups/',
        InternalDomainGroupsView.as_view(),
        name='api-internal-domain-groups'
    ),
    path(
        'internal/users/',
        InternalUsersView.as_view(),
        name='api-internal-users'
    ),
    path(
        'internal/users/<uuid:uuid>/',
        InternalUserDetailView.as_view(),
        name='api-internal-user-detail'
    ),
    path(
        'internal/subscription-by-api-key/',
        InternalSubscriptionByApiKeyView.as_view(),
        name='api-internal-subscription-by-api-key'
    ),
]
