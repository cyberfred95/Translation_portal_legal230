from django.views.generic import TemplateView, View, DetailView, ListView
from django.http import JsonResponse, HttpResponseBadRequest, Http404, HttpResponseNotFound, FileResponse
from .helpers import MicrosoftCustomProvider
from .credentials import providers, languages
from .mail_helpers import send_file_translation, send_text_translation


def get_file_ext(filename):
    split = filename.split('.')
    return split[-1]


def ms_text_translation(request, creds):
    translator = MicrosoftCustomProvider(
        key=creds['key'],
        category=creds['category_id'],
        source_lang=creds['source_lng'],
        target_lang=creds['target_lng']
    )
    return translator.translate(data=request.POST.get('text'))


def text_translation(request):
    source_language = request.POST.get('source_language')
    target_language = request.POST.get('target_language')
    provider = request.POST.get('provider')
    for key in providers:
        if providers[key]['source_lng'] == source_language and \
                providers[key]['target_lng'] == target_language and \
                providers[key]['provider'] == provider:
            print(key)
            if providers[key]['provider'] == 'ms':
                return ms_text_translation(request, providers[key])
    print('base')
    return None

def ms_file_translation(request, creds):
    ext = get_file_ext(request.FILES['document'].name)

    # if ext == 'txt':
    #     translator = MicrosoftCustomProvider(
    #         key=creds['key'],
    #         category=creds['category_id'],
    #         source_lang=creds['source_lng'],
    #         target_lang=creds['target_lng']
    #     )
    #     result = translator.translate(data=request.FILES['document'].read().decode("utf-8"))
    #     return FileResponse(
    #         result,
    #         filename=request.FILES['document'].name
    #     )

    translator = MicrosoftCustomProvider(
        key=creds['key'],
        category=creds['category_id'],
        source_lang=creds['source_lng'],
        target_lang=creds['target_lng']
    )

    result_data = translator.translate_file(
        file=request.FILES['document'].read(),
        mime_type=ext
    )
    return FileResponse(
        [result_data],
        filename=request.FILES['document'].name
    )


def file_translate(request):
    source_language = request.POST.get('source_language')
    target_language = request.POST.get('target_language')
    provider = request.POST.get('provider')
    for key in providers:
        if providers[key]['source_lng'] == source_language and \
                providers[key]['target_lng'] == target_language and \
                providers[key]['provider'] == provider:
            print(key)
            if providers[key]['provider'] == 'ms':
                return ms_file_translation(request, providers[key])

    print('base')
    return None


class TranslateView(TemplateView):
    template_name = "translate.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        provs = []
        for key in providers:
            provs.append({
                'key': key,
                'title': providers[key]['title'],
                'source_lng': providers[key]['source_lng'],
                'target_lng': providers[key]['target_lng'],
                'provider': providers[key]['provider']
            })
        context['providers'] = provs
        context['languages'] = languages
        return context

    def post(self, request):
        if not request.is_ajax():
            return HttpResponseBadRequest()
        if request.POST.get('action') == 'text_translate':
            return JsonResponse({'result': text_translation(request)})
        if request.POST.get('action') == 'file_translate':
            return file_translate(request)
        return JsonResponse({})
