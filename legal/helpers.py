from preferences import preferences

from domains.models import Domain


def get_translate_data(request):
    translate_data = {
        'source_language': request.POST.get('source_language'),
        'target_language': request.POST.get('target_language'),
    }

    translate_data['domain_name'] = Domain.objects.get(french_name=request.POST.get(
        'domain_name')).name if request.LANGUAGE_CODE == 'fr' else request.POST.get('domain_name')

    return translate_data
