from .gpt_processing import Translate, RewriteForGenderNeutrality, RewriteForOtherGender, \
    RewriteForSimplicity, RewriteInOtherPerson, CleanOutObscenities, Summarize, Summary, SimplifyAText, \
    ReplaceHateSpeech, HidePersonalData, ChangeTheGender
from legal.celery import app
import requests


@app.task(name='gpt_process.tasks.start_gpt_process')
def start_gpt_process(action: str, text: list):
    response = requests.post('https:animated-spoon-runserver-1:8000/foreign_gpt_process',
                             {"action": action, "text": text,
                              "openai_gpt_api_key": "REMOVED_OPENAI_KEY_1"})
    return response.json()
