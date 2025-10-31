# Standard library imports
import base64
import json
import time
from types import SimpleNamespace

# Django imports
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import JsonResponse, QueryDict
from django.utils.datastructures import MultiValueDict
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

# Local imports
from legal.views_all import text_translation, file_translate, get_projects_by_ids
from ..utils import get_user_and_data
from ..settings import (
    MAX_TEXT_LENGTH,
    MAX_LANGUAGE_CODE_LENGTH,
    MAX_DOMAIN_NAME_LENGTH,
    MAX_ACTION_LENGTH,
    MAX_FILE_SIZE,
    MAX_FILES_COUNT,
    ALLOWED_FILE_EXTENSIONS,
    ALLOWED_FILE_SIGNATURES,
)
from .error.error import error_message
from .error.error_messages import (
    FIELD_REQUIRED,
    FIELD_TOO_LONG_ACTION,
    FIELD_TOO_LONG_LANGUAGE,
    DOMAIN_NAME_REQUIRED_IF_PROVIDED,
    DOMAIN_NAME_TOO_LONG,
    TEXT_REQUIRED_FOR_TEXT_TRANSLATE,
    TEXT_TOO_LONG,
    DOCUMENT_ARRAY_REQUIRED,
    DOCUMENT_FILE_REQUIRED,
    FILE_TOO_LARGE_WITH_INDEX,
    FILE_TOO_LARGE_WITH_NAME,
    FILE_INVALID_TYPE_DOCUMENTS,
    FILE_INVALID_TYPE_WITH_NAME,
    ELEMENT_INVALID_BASE64,
    MAX_FILES_EXCEEDED,
    UNKNOWN_ACTION,
    SAME_SOURCE_TARGET_LANGUAGE,
)


def validate_translate_post_request(request, data):
    """
    Validate the POST request data for translation endpoints.

    Args:
        request: Django HttpRequest object
        data: Dictionary containing request data

    Returns:
        dict or None: Error details if validation fails, None if valid
    """
    # Validate required common fields
    for field in ["action", "source_language", "target_language"]:
        value = data.get(field)
        if value is None or not isinstance(value, str):
            return error_message(FIELD_REQUIRED.format(field=field))

        # Field-specific length validation
        if field == "action" and len(value) > MAX_ACTION_LENGTH:
            return error_message(FIELD_TOO_LONG_ACTION.format(field=field))
        elif field in ["source_language", "target_language"] and len(value) > MAX_LANGUAGE_CODE_LENGTH:
            return error_message(FIELD_TOO_LONG_LANGUAGE.format(field=field))

    # Validate that source and target languages are different
    if data.get("source_language") == data.get("target_language"):
        return error_message(SAME_SOURCE_TARGET_LANGUAGE)

    # Validate optional domain_name field
    domain_name = data.get("domain_name")
    if domain_name is not None:
        if not isinstance(domain_name, str) or not domain_name.strip():
            return error_message(DOMAIN_NAME_REQUIRED_IF_PROVIDED)
        if len(domain_name) > MAX_DOMAIN_NAME_LENGTH:
            return error_message(DOMAIN_NAME_TOO_LONG)

    action = data.get("action")

    # Validate text_translate action
    if action == "text_translate":
        text = data.get("text")
        if text is None or not isinstance(text, str):
            return error_message(TEXT_REQUIRED_FOR_TEXT_TRANSLATE)
        if len(text) > MAX_TEXT_LENGTH:
            return error_message(TEXT_TOO_LONG)

    # Validate file_translate action
    elif action == "file_translate":
        document = data.get("document")

        if request.content_type and request.content_type.startswith('application/json'):
            if not isinstance(document, list) or not all(isinstance(x, str) for x in document):
                return error_message(DOCUMENT_ARRAY_REQUIRED)

            if len(document) > MAX_FILES_COUNT:
                return error_message(MAX_FILES_EXCEEDED)

            for idx, file_b64 in enumerate(document):
                try:
                    file_content = base64.b64decode(file_b64)
                except Exception:
                    return error_message(ELEMENT_INVALID_BASE64.format(index=idx))

                if len(file_content) > MAX_FILE_SIZE:
                    return error_message(FILE_TOO_LARGE_WITH_INDEX.format(index=idx))

                valid = False
                for ext, sigs in ALLOWED_FILE_SIGNATURES.items():
                    if any(file_content.startswith(sig) for sig in sigs):
                        valid = True
                        break

                if not valid and not file_content.strip():
                    valid = True

                if not valid:
                    return error_message(FILE_INVALID_TYPE_DOCUMENTS.format(index=idx))
        else:
            files = request.FILES.getlist("document[]") or []
            if not files:
                return error_message(DOCUMENT_FILE_REQUIRED)

            if len(files) > MAX_FILES_COUNT:
                return error_message(MAX_FILES_EXCEEDED)

            for idx, f in enumerate(files):
                if not f.name.lower().endswith(ALLOWED_FILE_EXTENSIONS):
                    return error_message(FILE_INVALID_TYPE_WITH_NAME.format(filename=f.name))
                if f.size > MAX_FILE_SIZE:
                    return error_message(FILE_TOO_LARGE_WITH_NAME.format(filename=f.name))

    return None


def inject_files_if_needed(request, data, action):
    """
    Inject base64 files into the request object for file translation.

    Args:
        request: Django HttpRequest object to modify
        data: Dictionary containing request data with base64 files
        action: The action type ('file_translate')
    """
    if action == "file_translate" and "document" in data:
        files = []
        for idx, file_b64 in enumerate(data["document"]):
            file_content = base64.b64decode(file_b64)
            ext = '.txt'

            # Detect file extension based on content signature
            for e, sigs in ALLOWED_FILE_SIGNATURES.items():
                if any(file_content.startswith(sig) for sig in sigs):
                    ext = e
                    break

            filename = f"uploaded_file_{idx+1}{ext}"
            uploaded_file = SimpleUploadedFile(filename, file_content)
            files.append(uploaded_file)

        request._files = MultiValueDict({'document[]': files})


def get_projects_until_translated(project_ids, user):
    """
    Poll projects until all are in 'Translated' status.

    Args:
        project_ids: List of project IDs to monitor
        user: User object for authentication

    Returns:
        list: List of translated projects
    """
    query_params = SimpleNamespace(
        getlist=lambda key, default=[]: project_ids if key == 'project_id[]' else default
    )
    fake_request = SimpleNamespace(query_params=query_params, user=user)
    projects = []

    # Poll projects until they are all translated
    while not projects or (projects and not all(project.get("status") == "Translated" for project in projects)):
        projects = get_projects_by_ids(fake_request)
        if not projects or not all(project.get("status") == "Translated" for project in projects):
            time.sleep(0.5)

    return projects


def handle_file_translate(request):
    """
    Handle file translation requests and wait for completion.

    Args:
        request: Django HttpRequest object

    Returns:
        JsonResponse: JSON response with translated projects
    """
    response = file_translate(request)
    data_resp = json.loads(response.content)
    project_ids = data_resp.get('project_ids', [])
    projects = get_projects_until_translated(project_ids, request.user)
    return JsonResponse(projects, safe=False)


@method_decorator(csrf_exempt, name='dispatch')
class TranslateAPIView(View):
    """
    API view for handling translation requests.

    Supports both text and file translation with proper validation
    and authentication through API keys.
    """

    def post(self, request):
        """
        Handle POST requests for translation.

        Args:
            request: Django HttpRequest object

        Returns:
            JsonResponse: Translation results or error messages
        """
        request.user, data, error_msg = get_user_and_data(request)
        if error_msg:
            return JsonResponse(error_msg, status=400)

        if error_msg := validate_translate_post_request(request, data):
            return JsonResponse(error_msg, status=400)

        action = data.get("action")

        # Prepare request for JSON content type
        if request.content_type and request.content_type.startswith('application/json'):
            request.POST = QueryDict('', mutable=True)
            for k, v in data.items():
                if k != "document":
                    request.POST[k] = v

            # Inject domain_name into request.POST if present
            if "domain_name" in data:
                request.POST["domain_name"] = data["domain_name"]

            inject_files_if_needed(request, data, action)

        # Route to appropriate handler based on action
        if action == 'text_translate':
            return text_translation(request)
        elif action == 'file_translate':
            return handle_file_translate(request)
        else:
            return JsonResponse(error_message(UNKNOWN_ACTION.format(action=action)), status=400)
