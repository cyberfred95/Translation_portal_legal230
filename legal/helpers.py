from preferences import preferences


def get_translate_data(request):
    translate_data = {
        'source_language': request.POST.get('source_language'),
        'target_language': request.POST.get('target_language'),
    }

    if preferences.MainSettings.algorithm == preferences.MainSettings.AlgorithmChoices.template:
        translate_data['template_name'] = request.POST.get('translation_name')

    elif preferences.MainSettings.algorithm == preferences.MainSettings.AlgorithmChoices.domains:
        translate_data['domain_name'] = request.POST.get('translation_name')

    return translate_data
