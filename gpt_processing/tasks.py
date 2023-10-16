from .gpt_processing import Translate, RewriteForGenderNeutrality, RewriteForOtherGender, \
        RewriteForSimplicity, RewriteInOtherPerson, CleanOutObscenities, Summarize, Summary, SimplifyAText, \
        ReplaceHateSpeech, HidePersonalData, ChangeTheGender
from legal.celery import app


@app.task(name='gpt_process.tasks.start_gpt_process')
def start_gpt_process(action: str, text: list, **kwargs):
    proc = globals()[action](
        text=text,
        **kwargs
    )
    return proc.process()
