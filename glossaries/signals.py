"""
Django signals for glossary model.

Handles automatic synchronization with LARA backend on save/delete.
"""
import logging
import os

from django.core.exceptions import ValidationError
from django.db.models.signals import pre_delete, post_save
from django.dispatch import receiver

from .models import Glossary
from .services import LaraGlossaryService
from .services.lara_client import LaraClientError

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Glossary)
def sync_glossary_to_lara(sender, instance: Glossary, created, **kwargs):
    """
    Synchronize glossary with LARA backend on save.

    On create: Creates glossary in LARA and stores glossary_id.
    On update with file: Updates glossary in LARA with new file content.

    Args:
        sender: Model class
        instance: Glossary instance being saved
        created: True if this is a new record
    """
    # Prevent recursive signal calls
    if getattr(instance, '_skip_signal', False):
        return

    # Skip if no file to process
    if not _has_valid_file(instance):
        if created:
            logger.warning(f"New glossary {instance.name} has no file, skipping LARA sync")
        return

    service = LaraGlossaryService()

    try:
        if created:
            _handle_create(instance, service)
        else:
            _handle_update(instance, service)

        # Cleanup file after successful sync
        _cleanup_and_save(instance)

    except ValidationError as e:
        logger.error(f"Validation error for glossary {instance.name}: {e}")
        if created:
            instance.delete()
        raise

    except LaraClientError as e:
        logger.error(f"LARA error for glossary {instance.name}: {e}")
        if created:
            instance.delete()
        raise

    except Exception as e:
        logger.error(f"Unexpected error for glossary {instance.name}: {e}", exc_info=True)
        if created:
            instance.delete()
        raise


def _has_valid_file(instance: Glossary) -> bool:
    """Check if instance has a valid file on disk."""
    if not instance.file or not hasattr(instance.file, 'name') or not instance.file.name:
        return False

    if hasattr(instance.file, 'path'):
        return os.path.exists(instance.file.path)

    return False


def _handle_create(instance: Glossary, service: LaraGlossaryService) -> None:
    """Handle glossary creation in LARA."""
    logger.info(f"Creating glossary in LARA: {instance.name}")

    glossary_id = service.create_glossary(instance)
    instance.glossary_id = glossary_id

    # Save glossary_id without triggering signal
    instance._skip_signal = True
    instance.save(update_fields=['glossary_id'])


def _handle_update(instance: Glossary, service: LaraGlossaryService) -> None:
    """Handle glossary update in LARA."""
    if instance.glossary_id:
        logger.info(f"Updating glossary in LARA: {instance.glossary_id}")
        service.update_glossary(instance)
    else:
        logger.info(f"No glossary_id, creating in LARA: {instance.name}")
        glossary_id = service.create_glossary(instance)
        instance.glossary_id = glossary_id


def _cleanup_and_save(instance: Glossary) -> None:
    """Clean up file and save instance."""
    # Update name from file
    if instance.file and instance.file.name:
        instance.name = os.path.splitext(os.path.basename(instance.file.name))[0]

    # Delete file from disk
    try:
        instance.file.delete(save=False)
    except Exception as e:
        logger.warning(f"Failed to delete file for {instance.name}: {e}")

    instance.file = None

    # Save changes without triggering signal
    if not instance._state.adding:
        instance._skip_signal = True
        instance.save()


@receiver(pre_delete, sender=Glossary)
def delete_glossary_from_lara(sender, instance: Glossary, **kwargs):
    """
    Delete glossary from LARA backend before local deletion.

    Args:
        sender: Model class
        instance: Glossary instance being deleted
    """
    if not instance.glossary_id:
        return

    logger.info(f"Deleting glossary from LARA: {instance.glossary_id}")

    try:
        service = LaraGlossaryService()
        service.delete_glossary(instance)
    except Exception as e:
        # Log but don't block local deletion
        logger.error(f"Failed to delete glossary from LARA: {instance.name} - {e}")
