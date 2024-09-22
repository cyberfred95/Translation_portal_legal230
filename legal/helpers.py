from preferences import preferences

from domains.models import Domain


def get_translate_data(request):
    translate_data = {
        'source_language': request.POST.get('source_language'),
        'target_language': request.POST.get('target_language'),
    }

    if preferences.MainSettings.algorithm == preferences.MainSettings.AlgorithmChoices.template:
        return {'template_name': request.POST.get('domain_name')}

    elif preferences.MainSettings.algorithm == preferences.MainSettings.AlgorithmChoices.domains:
        if request.LANGUAGE_CODE == 'fr':
            translate_data['domain_name'] = Domain.objects.get(french_name=request.POST.get(
                'translation_name')).name if request.LANGUAGE_CODE == 'fr' else request.POST.get('POST')

    return translate_data
