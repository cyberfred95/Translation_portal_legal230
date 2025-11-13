import os

import requests
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models.signals import pre_delete, post_save
from django.dispatch import receiver

from .helpers import get_glossary_username
from .models import Glossary
from .services import AIGlossaryService


@receiver(post_save, sender=Glossary)
def create_glossary_on_service(sender, instance: Glossary, created, **kwargs):
    import logging
    logger = logging.getLogger(__name__)

    # Prevent recursive signal calls
    if getattr(instance, '_skip_signal', False):
        return

    ai_glossary_service = AIGlossaryService()

    if created:
        try:
            instance.glossary_id = ai_glossary_service.create_glossary(instance)
            # Set flag to prevent recursive call, then save
            instance._skip_signal = True
            instance.save(update_fields=['glossary_id'])
        except ValidationError as e:
            # Re-raise ValidationError so it can be caught by the batch processor
            logger.error(f"Failed to create glossary_id for {instance.name}: {str(e)}", exc_info=True)
            # Delete the instance since validation failed
            instance.delete()
            raise
        except Exception as e:
            logger.error(f"Failed to create glossary_id for {instance.name}: {str(e)}", exc_info=True)
            # Delete the instance since creation failed
            instance.delete()
            # Re-raise the exception so it can be caught by the batch processor
            raise

    # Only process file if it exists and has a valid path
    if instance.file and hasattr(instance.file, 'name') and instance.file.name:
        try:
            # Check if file actually exists on disk
            if hasattr(instance.file, 'path'):
                file_exists = os.path.exists(instance.file.path)
            else:
                file_exists = False

            if file_exists:
                try:
                    if instance.glossary_id:
                        # Glossary already has a remote ID, update it
                        ai_glossary_service.update_glossary(instance)
                    else:
                        # Glossary exists locally but has no remote ID, create it on API
                        instance.glossary_id = ai_glossary_service.create_glossary(instance)
                        # Will be saved after file cleanup below
                except ValidationError as e:
                    # Re-raise ValidationError for update/create failures
                    logger.error(f"Failed to update/create glossary on service for {instance.name}: {str(e)}", exc_info=True)
                    raise
                except Exception as e:
                    logger.error(f"Failed to update/create glossary on service for {instance.name}: {str(e)}", exc_info=True)
                    raise

                instance.name = os.path.splitext(os.path.basename(instance.file.name))[0]

                try:
                    instance.file.delete(save=False)
                except Exception as e:
                    logger.warning(f"Failed to delete file for {instance.name}: {str(e)}")

                instance.file = None

                if instance._state.adding is False:
                    # Set flag to prevent recursive call
                    instance._skip_signal = True
                    # Save with glossary_id if it was just created
                    instance.save()
            else:
                logger.warning(f"File does not exist on disk for glossary {instance.name}, skipping file processing")
        except Exception as e:
            logger.error(f"Error processing file for glossary {instance.name}: {str(e)}", exc_info=True)
            raise


@receiver(pre_delete, sender=Glossary)
def delete_glossary_from_service(sender, instance: Glossary, **kwargs):
    import logging
    logger = logging.getLogger(__name__)

    # Only call API if glossary_id exists
    if instance.glossary_id:
        try:
            AIGlossaryService().delete_glossary(instance)
        except Exception as e:
            logger.error(f"Failed to delete glossary from external service: {instance.name} - {str(e)}", exc_info=True)
            # Don't raise - allow Django deletion to proceed even if API fails
