from celery import shared_task
from preferences import preferences
import requests
from .models import Prompt, PromptTranslation
from legal.constants import EN


@shared_task
def refresh_prompts():
    existing_prompts = Prompt.objects.all()
    prompts = requests.post(
        "https://console.custom.mt/gpt_playground/api/get-prompts-list",
        headers={
            'token': preferences.MainSettings.api_key
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
