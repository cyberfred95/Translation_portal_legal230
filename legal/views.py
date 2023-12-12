from django.views.generic import TemplateView, View, DetailView, ListView
from django.http import JsonResponse, HttpResponseBadRequest, Http404, HttpResponseNotFound, FileResponse
from .helpers import MicrosoftCustomProvider
from .credentials import providers, languages, provider_models
from .mail_helpers import send_file_translation, send_text_translation, send_expert_revision_text, \
    send_expert_revision_file
import base64
from rest_framework.decorators import api_view
from django.views.decorators.csrf import csrf_exempt


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
    send_text_translation(user_id=request.user.id, text=request.POST.get('text'))
    return translator.translate(data=request.POST.get('text'))


def text_translation(request):
    provider_key = request.POST.get('provider_key')
    if providers[provider_key]['provider'] == 'ms':
        return ms_text_translation(request, providers[provider_key])
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
    file = request.FILES['document'].read()
    result_data = translator.translate_file(
        file=file,
        mime_type=ext
    )
    b_64 = base64.b64encode(file)
    send_file_translation(user_id=request.user.id, base64_attachment=b_64.decode(encoding='utf-8'),
                          file_name=request.FILES['document'].name)

    return FileResponse(
        [result_data],
        filename=request.FILES['document'].name
    )


def file_translate(request):
    provider_key = request.POST.get('provider_key')
    if providers[provider_key]['provider'] == 'ms':
        return ms_file_translation(request, providers[provider_key])

    print('base')
    return None


class TranslateView(TemplateView):
    template_name = "translate.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        provs = {}
        for provider in provider_models:
            provider_data = provider_models.get(provider)
            provs[f'{provider}'] = []
            for key in provider_data:
                provs[f'{provider}'].append({
                    'key': key,
                    'title': provider_data[key]['title'],
                    'title_fr': provider_data[key]['title_fr'],
                    'source_lng': provider_data[key]['source_lng'],
                    'target_lng': provider_data[key]['target_lng'],
                    'provider': provider_data[key]['provider']
                })
        print(provs)
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


@csrf_exempt
@api_view(['POST'])
def expert_revision(request):
    text = request.POST['result']
    send_expert_revision_text(user_id=request.user.id, text=text)
    return JsonResponse({})


@csrf_exempt
@api_view(['POST'])
def expert_revision_file(request):
    file = request.FILES['file'].read()
    b_64 = base64.b64encode(file)
    send_expert_revision_file(user_id=request.user.id, base64_attachment=b_64.decode(encoding='utf-8'),
                              file_name=request.FILES['file'].name)
    return JsonResponse({})
