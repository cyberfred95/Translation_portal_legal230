import os
import re

from django.core.files.uploadedfile import InMemoryUploadedFile
from preferences import preferences

from domains.models import Domain
from stats.calculator import StatsProcessor


def get_translate_data(request, for_statistic=False):
    translate_data = {
        'source_language': request.POST.get('source_language'),
        'target_language': request.POST.get('target_language'),
    }
    domain = Domain.objects.filter(french_name=request.POST.get('domain_name')).first()
    if not domain:
        domain = Domain.objects.filter(name=request.POST.get('domain_name')).first()

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
    print(file.name)
    return file


def get_word_count(segment):
    result = 0
    result += len(str(segment).split())
    return result


def get_text_from_file(file: InMemoryUploadedFile, api_key) -> list:
    try:
        texts = StatsProcessor(api_key).get_texts(file=file)
    except UnicodeEncodeError:
        raise ValueError("Invalid characters in file name")

    formated_texts = [
        word
        for text in texts['texts']
        for word in re.sub(r'<[^>]*>', '', text['text']).split()
    ]
    return formated_texts

