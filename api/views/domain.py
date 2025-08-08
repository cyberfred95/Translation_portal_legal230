# Django imports
from django.db import models
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

# Local imports
from glossaries.models import Domain, Glossary
from languages.models import Language
from ..utils import get_user_and_data
from ..settings import MAX_LANGUAGE_CODE_LENGTH, MAX_DOMAIN_ID
from .error.error import error_message
from .error.error_messages import (
    FIELD_REQUIRED_IF_PROVIDED,
    FIELD_TOO_LONG_LANGUAGE,
    ID_OUT_OF_RANGE_DOMAIN,
    ID_MUST_BE_INTEGER,
    DOMAIN_ID_MUST_BE_INTEGER,
    SOURCE_LANGUAGE_NOT_FOUND,
    TARGET_LANGUAGE_NOT_FOUND,
)


def partial_domain_to_json(domain):
    """
    Convert a Domain object to a simplified JSON representation.

    Args:
        domain: Domain object to convert

    Returns:
        dict: Simplified domain data with id, domain_group, and name
    """
    return {
        "id": domain.id,
        "domain_group": domain.domain_group.name if domain.domain_group else None,
        "name": domain.name,
    }


def validate_domain_default_glossaries_get_request(data, id_domain=None):
    """
    Validate GET request data for domain default glossaries endpoint.

    Args:
        data: Dictionary containing request data
        id_domain: Optional domain ID to validate

    Returns:
        dict or None: Error details if validation fails, None if valid
    """
    for field in ["source_language", "target_language"]:
        value = data.get(field)
        if value is not None:
            if not isinstance(value, str) or not value.strip():
                return error_message(FIELD_REQUIRED_IF_PROVIDED.format(field=field))
            if len(value) > MAX_LANGUAGE_CODE_LENGTH:
                return error_message(FIELD_TOO_LONG_LANGUAGE.format(field=field))

    if id_domain is not None:
        try:
            id_domain_int = int(id_domain)
            if id_domain_int < 0 or id_domain_int > MAX_DOMAIN_ID:
                return error_message(ID_OUT_OF_RANGE_DOMAIN.format(field="id_domain"))
        except (ValueError, TypeError):
            return error_message(ID_MUST_BE_INTEGER.format(field="id_domain"))

    return None


def filter_glossaries(data, id_domain, request):
    """
    Filter glossaries based on domain, languages, and user group.

    Args:
        data: Dictionary containing filtering parameters
        id_domain: Domain ID to filter by
        request: Django HttpRequest object for user context

    Returns:
        tuple: (glossary_list, error_message) where error_message is None on success
    """

    source_language = data.get("source_language")
    target_language = data.get("target_language")
    user_group = getattr(request.user, "group", None)

    glossaries = Glossary.objects.all()

    # Filter by source language if provided
    if source_language:
        source_language_obj = Language.objects.filter(
            abbreviation__iexact=source_language
        ).first()
        if not source_language_obj:
            return None, error_message(SOURCE_LANGUAGE_NOT_FOUND)
        glossaries = glossaries.filter(source_language=source_language_obj)

    # Filter by target language if provided
    if target_language:
        target_language_obj = Language.objects.filter(
            abbreviation__iexact=target_language
        ).first()
        if not target_language_obj:
            return None, error_message(TARGET_LANGUAGE_NOT_FOUND.format(language=target_language))
        glossaries = glossaries.filter(target_language=target_language_obj)

    # Filter by domain if provided
    if id_domain is not None:
        try:
            id_domain_int = int(id_domain)
            glossaries = glossaries.filter(domain_id=id_domain_int)
        except (ValueError, TypeError):
            return None, error_message(DOMAIN_ID_MUST_BE_INTEGER)

    # Filter by user group (public glossaries or user's group glossaries)
    glossaries = glossaries.filter(
        models.Q(group=None) | models.Q(group=user_group)
    )

    glossary_list = [g.to_json(request) for g in glossaries]
    return glossary_list, None


@method_decorator(csrf_exempt, name='dispatch')
class DomainListAPIView(View):
    """
    API view for handling domain list requests.

    Provides endpoints to retrieve all available domains with their
    basic information for domain selection in translation services.
    """

    def get(self, request):
        """
        Handle GET requests to retrieve all domains.

        Args:
            request: Django HttpRequest object

        Returns:
            JsonResponse: List of domains with id, domain_group, and name
        """
        request.user, _, error_msg = get_user_and_data(
            request, with_data=False)
        if error_msg:
            return JsonResponse(error_msg, status=400)

        domains = Domain.objects.all()
        data = [partial_domain_to_json(domain) for domain in domains]
        return JsonResponse(data, status=200, safe=False)


@method_decorator(csrf_exempt, name='dispatch')
class DomainDefaultGlossariesAPIView(View):
    """
    API view for handling domain-specific glossary requests.

    Provides endpoints to retrieve glossaries filtered by domain,
    source/target languages, and user access permissions.
    """

    def get(self, request, id_domain):
        """
        Handle GET requests to retrieve glossaries for a specific domain.

        Args:
            request: Django HttpRequest object
            id_domain: Domain ID to filter glossaries

        Returns:
            JsonResponse: List of filtered glossaries or error messages
        """
        request.user, data, error_msg = get_user_and_data(
            request, with_data=True, from_query=True
        )
        if error_msg:
            return JsonResponse(error_msg, status=400)

        if (error_msg := validate_domain_default_glossaries_get_request(data, id_domain)):
            return JsonResponse(error_msg, status=400)

        glossary_list, error_msg = filter_glossaries(data, id_domain, request)
        if error_msg:
            return JsonResponse(error_msg, status=400)

        return JsonResponse(glossary_list, status=200, safe=False)
