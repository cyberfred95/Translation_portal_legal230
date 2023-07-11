from django.views.generic import TemplateView
from rest_framework.decorators import api_view
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.response import Response
from celery.result import AsyncResult
from .tasks import start_gpt_process


class GPTProcessingView(TemplateView):

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['langs'] = {'en', 'fr'}
        return context

    template_name = "gpt_processing.html"


@csrf_exempt
@api_view(['POST'])
def gpt_process(request):
    data = request.data
    if 'action' in data:
        task = start_gpt_process.delay(
            action=data['action'],
            text=data['text'],
            **data['prompt']
        )
        return Response({
            'task_id': task.task_id
        }, status=status.HTTP_200_OK)
    return Response({}, status=status.HTTP_400_BAD_REQUEST)


@csrf_exempt
@api_view(['POST'])
def gpt_check(request):
    result = []
    tasks = request.data
    for task in tasks:
        task_result = AsyncResult(task)
        tmp_res = {}
        tmp_res.update({
            "task_id": task,
            "task_status": task_result.status,
        })
        if hasattr(task_result, "result"):
            tmp_res.update({
                "result": task_result.result
            })
        result.append(tmp_res)
        print(result)
    return Response(result, status=status.HTTP_200_OK)
