from celery import shared_task
from django.conf import settings
from preferences import preferences
import requests
from .models import Prompt, PromptTranslation
from legal.constants import EN

from stats.calculator import StatsProcessor


@shared_task
def refresh_prompts():
    existing_prompts = Prompt.objects.all()
    prompts = requests.post(
        settings.CUSTOM_MT_CONSOLE_URL + "gpt_playground/api/get-prompts-list",
        headers={
            'token': settings.CLOUDSTORAGE_API_KEY
        }
    )

    existing_prompts_names = [prompt.translations.filter(language=EN).first().name for prompt in
                              existing_prompts]
    cmt_prompt_names = []
    for prompt in prompts.json().get('data', []):
        cmt_prompt_names.append(prompt['name'])
        if prompt['name'] not in existing_prompts_names:
            new_prompt = Prompt.objects.create(
                temperature=float(prompt['temperature']),
                gpt_model=prompt['gpt_model'],
                prompt=prompt['prompt'],
            )
            english_translation = PromptTranslation.objects.create(
                language=EN,
                prompt=new_prompt,
                name=prompt['name'],
                description=prompt['description'],
            )

    for prompt in existing_prompts:
        if prompt.translations.filter(language='en').first().name not in cmt_prompt_names:
            prompt.delete()


@shared_task
def send_statistic_request(api_key, texts: list, user_uuid, gpt_model: str, file_name="Text writing"):
    StatsProcessor(api_key=api_key).send_writing_request(texts=texts, user_uuid=user_uuid, gpt_model=gpt_model,
                                                         file_name=file_name)
