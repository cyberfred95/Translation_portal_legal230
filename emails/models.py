from enum import Enum

from django.conf import settings
from django.db import models


class EmailType(Enum):

    USER_CREATED = "USER_CREATED"
    ADDIN_CREATED = "ADDIN_CREATED"

    SUBSCRIPTION_UPDATED_QUANTITY_ADMIN = "SUBSCRIPTION_UPDATED_QUANTITY_ADMIN"
    SUBSCRIPTION_UPDATED_INACTIVE_ADMIN = "SUBSCRIPTION_UPDATED_INACTIVE_ADMIN"
    SUBSCRIPTION_UPDATED_INACTIVE = "SUBSCRIPTION_UPDATED_INACTIVE"
    SUBSCRIPTION_NEED_PAYMENT_ADMIN = "SUBSCRIPTION_NEED_PAYMENT_ADMIN"
    SUBSCRIPTION_DELETED_ADMIN = "SUBSCRIPTION_DELETED_ADMIN"
    SUBSCRIPTION_DELETED = "SUBSCRIPTION_DELETED"
    SUBSCRIPTION_TRIALS_WILL_END_ADMIN = "SUBSCRIPTION_TRIALS_WILL_END_ADMIN"
    SUBSCRIPTION_TRIALS_WILL_END = "SUBSCRIPTION_TRIALS_WILL_END"
    
    USER_MANAGEMENT_INVITATION = "USER_MANAGEMENT_INVITATION"
    USER_MANAGEMENT_QUOTE = "USER_MANAGEMENT_QUOTE"
    USER_MANAGEMENT_RESET_PASSWORD = "USER_MANAGEMENT_RESET_PASSWORD"
    
    USER_ADM_TR_FILE = "USER_ADM_TR_FILE"

class EmailSettings(models.Model):

    email_type = models.CharField(
        max_length=64,
        choices=[(etype.value, etype.value) for etype in EmailType],
        verbose_name="Type d'email",
        help_text="The type of email this setting applies to"
    )
    language = models.CharField(
        max_length=8,
        choices=settings.LANGUAGES,
        verbose_name="Language",
        help_text="Language code for this email template"
    )
    template_id = models.IntegerField(
        verbose_name="ID du template",
        help_text="Active Trail template identifier"
    )
    subject = models.CharField(
        max_length=128,
        verbose_name="Sujet",
        help_text="Email subject line"
    )

    def __str__(self):

        return f"{self.email_type} – {self.language}"

    class Meta:

        verbose_name = "Email Setting"
        verbose_name_plural = "Email Settings"
        unique_together = (("email_type", "language"),)
        ordering = ['email_type', 'language']
        indexes = [
            models.Index(fields=['email_type', 'language']),
        ]
