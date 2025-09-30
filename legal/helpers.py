import os
import re
import logging
from io import BytesIO
from urllib.parse import urlparse

import requests
from django.contrib.auth.hashers import check_password
from django.core.files.uploadedfile import InMemoryUploadedFile
from preferences import preferences
import base64
from domains.models import Domain
from stats.calculator import StatsProcessor

logger = logging.getLogger(__name__)


def get_translate_data(request, for_statistic=False):
    translate_data = {
        'source_language': request.POST.get('source_language'),
        'target_language': request.POST.get('target_language'),
    }
    domain = Domain.objects.filter(
        french_name=request.POST.get('domain_name')).first()
    if not domain:
        domain = Domain.objects.filter(
            name=request.POST.get('domain_name')).first()

    if not domain and preferences.DefaultTranslation.enabled:
        if for_statistic:
            translate_data['domain_name'] = preferences.DefaultTranslation.name
        else:
            translate_data[
                'template_name'] = f"Custom.MT Default Template {request.POST.get('source_language')} {request.POST.get('target_language')}"
    else:
        translate_data['domain_name'] = domain.name if request.LANGUAGE_CODE == 'fr' else request.POST.get(
            'domain_name')

    return translate_data


def lowercase_file_extension(file: InMemoryUploadedFile) -> InMemoryUploadedFile:
    # Split the file name and extension
    name, ext = os.path.splitext(file.name)
    # Lowercase the extension
    file.name = f"{name}{ext.lower()}"
    return file


def get_word_count(segment):
    result = 0
    result += len(str(segment).split())
    return result


def get_text_from_file(file: InMemoryUploadedFile, api_key):
    logger.info(f"[DEBUG] get_text_from_file appelée pour: {file.name}")
    try:
        logger.info(f"[DEBUG] Appel de StatsProcessor avec api_key: {bool(api_key)}")
        texts = StatsProcessor(api_key).get_texts(file=file)
        logger.info(f"[DEBUG] Réponse StatsProcessor reçue: {bool(texts)}")
        
        if texts and 'texts' in texts:
            logger.info(f"[DEBUG] Nombre de segments de texte: {len(texts['texts'])}")
        else:
            logger.error(f"[DEBUG] Réponse invalide de StatsProcessor: {texts}")
            
    except UnicodeEncodeError as e:
        logger.error(f"[DEBUG] UnicodeEncodeError: {e}")
        raise ValueError({"detail": "Invalid characters in file name"})
    except Exception as e:
        logger.error(f"[DEBUG] Exception dans get_text_from_file: {e}")
        raise

    if not texts or 'texts' not in texts:
        logger.error("[DEBUG] Pas de données textuelles retournées")
        return [], []

    formated_texts = [
        word
        for text in texts['texts']
        for word in re.sub(r'<[^>]*>', '', text['text']).split()
    ]
    file.seek(0)
    logger.info(f"[DEBUG] Traitement terminé - mots formatés: {len(formated_texts)}")
    return formated_texts, [text['text'] for text in texts['texts']]


def get_project_file(file_url) -> InMemoryUploadedFile:
    response = requests.get(file_url)
    file_content = BytesIO(response.content)

    object_key = urlparse(file_url).path.lstrip('/')
    file_name = object_key.split('/')[-1]

    in_memory_file = InMemoryUploadedFile(
        file_content,
        None,
        file_name,
        response.headers.get('Content-Type', 'application/octet-stream'),
        len(response.content),
        None
    )

    return in_memory_file


def password_valid(request):
    if not request.data.get('password'):
        return False
    password = base64.b64decode(request.data.get('password'))
    if not check_password(password, request.user.password):
        return False
    return True


def rename_file(file: InMemoryUploadedFile, file_name: str = None):
    if not file_name:
        file_extension = os.path.splitext(file.name)[1]
        file.name = f'file{file_extension}'
    else:
        file.name = file_name
    return file


def get_main_settings():
    """
    Get the main settings instance.
    Returns None if no settings are configured.
    """
    try:
        from settings.models import MainSettings
        return MainSettings.objects.first()
    except Exception:
        return None
