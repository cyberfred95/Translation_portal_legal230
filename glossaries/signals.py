import os

import requests
from django.conf import settings
from django.db.models.signals import pre_delete, post_save
from django.dispatch import receiver
from preferences import preferences

from .helpers import get_glossary_username
from .models import Glossary
from .services import AIGlossaryService


@receiver(post_save, sender=Glossary)
def create_glossary_on_service(sender, instance: Glossary, created, **kwargs):
    ai_glossary_service = AIGlossaryService()

    if created:
        instance.glossary_id = ai_glossary_service.create_glossary(instance)
        instance.save()

    if instance.file:
        if instance.glossary_id:
            ai_glossary_service.update_glossary(instance)

        instance.name = os.path.splitext(os.path.basename(instance.file.name))[0]

        instance.file.delete(save=False)
        instance.file = None

        if instance._state.adding is False:
            instance.save()


@receiver(pre_delete, sender=Glossary)
def delete_glossary_from_service(sender, instance: Glossary, **kwargs):
    AIGlossaryService().delete_glossary(instance)
