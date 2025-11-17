import os
import re
from io import BytesIO
from urllib.parse import urlparse, unquote
from datetime import datetime

import requests
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.core.files.uploadedfile import InMemoryUploadedFile
from preferences import preferences
import base64
from domains.models import Domain
from stats.calculator import StatsProcessor


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
        lang_code = getattr(request, 'LANGUAGE_CODE', 'en')
        translate_data['domain_name'] = domain.name if lang_code == 'fr' else request.POST.get('domain_name')

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
    try:
        texts = StatsProcessor(api_key).get_texts(file=file)
    except UnicodeEncodeError:
        raise ValueError({"detail": "Invalid characters in file name"})

    formated_texts = [
        word
        for text in texts['texts']
        for word in re.sub(r'<[^>]*>', '', text['text']).split()
    ]
    file.seek(0)
    return formated_texts, [text['text'] for text in texts['texts']]


def get_project_file(file_url) -> InMemoryUploadedFile:
    response = requests.get(file_url)
    content = getattr(response, 'content', b'')
    if not isinstance(content, (bytes, bytearray)):
        content = b''
    file_content = BytesIO(content)

    object_key = urlparse(file_url).path.lstrip('/')
    file_name = object_key.split('/')[-1]

    in_memory_file = InMemoryUploadedFile(
        file_content,
        None,
        file_name,
        getattr(response, 'headers', {}).get('Content-Type', 'application/octet-stream'),
        len(content),
        None
    )

    return in_memory_file


def password_valid(request):
    data = getattr(request, 'data', request.POST)
    if not data.get('password'):
        return False
    raw = data.get('password')
    try:
        password = base64.b64decode(raw)
    except Exception:
        password = raw.encode('utf-8')
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


def get_user_emails_map(user_tokens):
    """
    Récupère un dictionnaire mapping UUID -> email pour une liste de tokens utilisateurs.
    
    Args:
        user_tokens: Liste de UUID (strings) des utilisateurs
        
    Returns:
        dict: Dictionnaire {uuid: email} pour les utilisateurs trouvés
    """
    if not user_tokens:
        return {}
    
    UserModel = get_user_model()
    return {
        str(user_obj['uuid']): user_obj['email']
        for user_obj in UserModel.objects.filter(uuid__in=user_tokens).values('uuid', 'email')
    }


def process_projects(projects_data, user, email_map=None):
    """
    Traite une liste de projets depuis l'API pour les préparer à l'affichage.
    
    Args:
        projects_data: Liste de dictionnaires de projets depuis l'API
        user: Utilisateur Django
        email_map: Dictionnaire optionnel {uuid: email} pour enrichir les projets
        
    Returns:
        list: Liste de projets enrichis avec les données nécessaires
    """
    for project in projects_data:
        # Extraction du nom de fichier depuis l'URL
        file_name = urlparse(project['source_file']).path.lstrip('/').split('/')[-1]
        project['source_file_name'] = unquote(file_name)
        
        # Parsing de la date de création
        project['created_at'] = datetime.fromisoformat(
            project['created_at'].replace('Z', '+00:00')
        )
        
        # Détermination du type de document
        project['document_type'] = (
            'text' if project['source_file_name'].lower().endswith('.txt') 
            else 'document'
        )
        
        # Ajout de l'email utilisateur si staff et email_map fourni
        if user.is_staff and email_map:
            token = project.get('user_custom_mt_token')
            project['user_email'] = email_map.get(str(token)) if token else None
    
    return projects_data


def extract_user_tokens_from_projects(projects_data):
    """
    Extrait les tokens utilisateurs uniques depuis une liste de projets.
    
    Args:
        projects_data: Liste de dictionnaires de projets
        
    Returns:
        list: Liste de tokens utilisateurs uniques (UUID strings)
    """
    return list({
        project.get('user_custom_mt_token')
        for project in projects_data
        if project.get('user_custom_mt_token')
    })


