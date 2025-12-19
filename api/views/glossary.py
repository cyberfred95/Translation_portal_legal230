# Standard library imports
import base64

# Django imports
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import JsonResponse, QueryDict
from django.utils.datastructures import MultiValueDict
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

# Third-party imports
from rest_framework.response import Response as DRFResponse

# Local imports
from glossaries.models import Glossary
from glossaries.views import AddGlossaryView
from ..utils import get_user_and_data, detect_glossary_file_type
from ..settings import (
    MAX_GLOSSARY_NAME_LENGTH,
    MAX_LANGUAGE_CODE_LENGTH,
    MAX_GLOSSARY_FILE_SIZE,
    ALLOWED_GLOSSARY_EXTENSIONS,
    MAX_GLOSSARY_ID,
)
from .error.error_messages import (
    FIELD_REQUIRED,
    FIELD_TOO_LONG_GLOSSARY_NAME,
    FIELD_TOO_LONG_LANGUAGE,
    FILE_BASE64_REQUIRED,
    FILE_UPLOAD_REQUIRED,
    FILE_INVALID_BASE64,
    FILE_TOO_LARGE_GLOSSARY,
    FILE_INVALID_TYPE_CSV_XLSX,
    FILE_INVALID_TYPE_CSV_XLSX_UPLOAD,
    ID_OUT_OF_RANGE_GLOSSARY,
    ID_MUST_BE_INTEGER,
    USER_GLOSSARY_NOT_FOUND,
)
from .error.success_messages import GLOSSARY_DELETED_SUCCESSFULLY
from .error.error import error_message, success_message


def validate_glossary_request(request, data):
    """
    Validate glossary request data for both JSON and form submissions.
    
    Note: source_language and target_language are no longer required as they are
    automatically detected from the CSV file.

    Args:
        request: Django HttpRequest object
        data: Dictionary containing request data

    Returns:
        dict or None: Error details if validation fails, None if valid
    """
    # Only validate name if provided (optional for form submissions)
    name = data.get("name")
    if name is not None:
        if not isinstance(name, str):
            return error_message(FIELD_REQUIRED.format(field="name"))
        if len(name) > MAX_GLOSSARY_NAME_LENGTH:
            return error_message(FIELD_TOO_LONG_GLOSSARY_NAME.format(field="name"))
    
    # source_language and target_language are no longer required
    # They are automatically detected from the CSV file

    # Validate glossary file
    if request.content_type and request.content_type.startswith('application/json'):
        glossary_b64 = data.get("file")
        if not glossary_b64 or not isinstance(glossary_b64, str):
            return error_message(FILE_BASE64_REQUIRED)

        try:
            file_content = base64.b64decode(glossary_b64)
        except Exception:
            return error_message(FILE_INVALID_BASE64)

        if len(file_content) > MAX_GLOSSARY_FILE_SIZE:
            return error_message(FILE_TOO_LARGE_GLOSSARY)

        ext, _ = detect_glossary_file_type(file_content)
        if ext not in ALLOWED_GLOSSARY_EXTENSIONS:
            return error_message(FILE_INVALID_TYPE_CSV_XLSX)
    else:
        glossary_file = request.FILES.get('file')
        if glossary_file is None:
            return error_message(FILE_UPLOAD_REQUIRED)
        if not glossary_file.name.lower().endswith(ALLOWED_GLOSSARY_EXTENSIONS):
            return error_message(FILE_INVALID_TYPE_CSV_XLSX_UPLOAD)
        if glossary_file.size > MAX_GLOSSARY_FILE_SIZE:
            return error_message(FILE_TOO_LARGE_GLOSSARY)

    return None


def inject_glossary_from_json_file(request, data):
    """
    Inject base64 glossary file into the request object.

    Args:
        request: Django HttpRequest object to modify
        data: Dictionary containing request data with base64 file
    """
    glossary_b64 = data.get("file")
    # Use name from data if provided, otherwise use default
    name = data.get('name', 'glossary')
    file_name = name

    if glossary_b64:
        file_content = base64.b64decode(glossary_b64)
        ext, content_type = detect_glossary_file_type(file_content)
        complete_file_name = f"{file_name}{ext}"
        glossary_file = SimpleUploadedFile(
            complete_file_name, file_content, content_type=content_type
        )

        if hasattr(request, 'files') and isinstance(request._files, MultiValueDict):
            request._files.setlist('file', [glossary_file])
        else:
            request._files = MultiValueDict({'file': [glossary_file]})


def inject_glossary_from_form_urlencoded_file(request):
    """
    Prepare request data for multipart/form-data submissions.

    Args:
        request: Django HttpRequest object to modify
    """
    # Only include file in request.data, not language fields (they're auto-detected)
    request.data = {}
    # File is already in request.FILES, no need to add it to request.data


def handle_add_glossary_post(request):
    """
    Handle glossary addition through the existing AddGlossaryView.

    Args:
        request: Django HttpRequest object

    Returns:
        JsonResponse: Response from the glossary addition process
    """
    add_glossary_view = AddGlossaryView()
    drf_response = add_glossary_view.post(request)

    if isinstance(drf_response, DRFResponse):
        return JsonResponse(drf_response.data, status=drf_response.status_code, safe=False)
    return drf_response


def prepare_request_for_json_glossary(request, data):
    """
    Prepare request object for JSON glossary submissions.

    Args:
        request: Django HttpRequest object to modify
        data: Dictionary containing request data
    """
    request.POST = QueryDict('', mutable=True)
    for k, v in data.items():
        if k != "file":
            request.POST[k] = v

    inject_glossary_from_json_file(request, data)

    # Create request.data with necessary data
    request.data = {**data}
    request.data.pop("file", None)
    if request.FILES.get('file'):
        request.data['file'] = request.FILES.get('file')


def validate_glossary_id(id_glossary):
    """
    Validate glossary ID to prevent integer overflow attacks.

    Args:
        id_glossary: The glossary ID to validate

    Returns:
        dict or None: Error details if validation fails, None if valid
    """
    if id_glossary is not None:
        try:
            id_glossary_int = int(id_glossary)
            if id_glossary_int < 0 or id_glossary_int > MAX_GLOSSARY_ID:
                return error_message(ID_OUT_OF_RANGE_GLOSSARY.format(field="id_glossary"))
        except (ValueError, TypeError):
            return error_message(ID_MUST_BE_INTEGER.format(field="id_glossary"))
    return None


@method_decorator(csrf_exempt, name='dispatch')
class GlossaryAPIView(View):
    """
    API view for handling glossary creation requests.

    Supports both JSON and form-data submissions for creating new glossaries
    with proper validation and file handling.
    """

    def post(self, request):
        """
        Handle POST requests for glossary creation.

        Args:
            request: Django HttpRequest object

        Returns:
            JsonResponse: Creation result or error messages
        """
        request.user, data, error_msg = get_user_and_data(request)
        if error_msg:
            return JsonResponse(error_msg, status=400)

        if (error_msg := validate_glossary_request(request, data)):
            return JsonResponse(error_msg, status=400)

        if request.content_type and request.content_type.startswith('application/json'):
            prepare_request_for_json_glossary(request, data)
        else:
            inject_glossary_from_form_urlencoded_file(request)

        return handle_add_glossary_post(request)


@method_decorator(csrf_exempt, name='dispatch')
class GlossaryExistAPIView(View):
    """
    API view for handling existing glossary operations.

    Provides endpoints to retrieve, update, and delete existing glossaries
    with proper user isolation and validation.
    """

    def get(self, request, id_glossary=None):
        """
        Handle GET requests to retrieve glossaries.

        Args:
            request: Django HttpRequest object
            id_glossary: Optional glossary ID for specific retrieval

        Returns:
            JsonResponse: Glossary data or list of glossaries
        """
        user, _, error_msg = get_user_and_data(request, with_data=False)
        if error_msg:
            return JsonResponse(error_msg, status=400)

        # Validate glossary ID if provided
        if id_glossary is not None:
            if (error_msg := validate_glossary_id(id_glossary)):
                return JsonResponse(error_msg, status=400)

        # Retrieve glossaries for the user
        glossaries = Glossary.objects.filter(user=user)
        if id_glossary is not None:
            glossary = glossaries.filter(id=id_glossary).first()
            if not glossary:
                return JsonResponse(
                    error_message(USER_GLOSSARY_NOT_FOUND),
                    status=404,
                    safe=False
                )
            return JsonResponse(glossary.to_json(request), status=200)

        return JsonResponse([g.to_json(request) for g in glossaries], status=200, safe=False)

    def delete(self, request, id_glossary=None):
        """
        Handle DELETE requests to remove glossaries.

        Args:
            request: Django HttpRequest object
            id_glossary: Glossary ID to delete

        Returns:
            JsonResponse: Deletion confirmation or error messages
        """
        user, _, error_msg = get_user_and_data(request, with_data=False)
        if error_msg:
            return JsonResponse(error_msg, status=400)

        # Validate glossary ID
        if (error_msg := validate_glossary_id(id_glossary)):
            return JsonResponse(error_msg, status=400)

        try:
            glossary = Glossary.objects.get(user=user, id=id_glossary)
        except Glossary.DoesNotExist:
            return JsonResponse(
                error_message(USER_GLOSSARY_NOT_FOUND),
                status=404,
                safe=False
            )

        glossary.delete()
        return JsonResponse(success_message(GLOSSARY_DELETED_SUCCESSFULLY), status=204, safe=False)
