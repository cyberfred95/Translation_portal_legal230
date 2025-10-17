import uuid
from django.utils import timezone
import random
import requests
import logging

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.timezone import now
from django.conf import settings

from legal.helpers import get_main_settings

logger = logging.getLogger(__name__)


class UserGroup(models.Model):
    name = models.CharField(max_length=64)
    api_key = models.CharField(
        max_length=256, 
        blank=True, 
        null=True,
        help_text="If not provided, will be automatically generated"
    )
    admin = models.ManyToManyField('users.User', blank=True)
    quote_monthly_number = models.IntegerField(
        default=0, validators=[MinValueValidator(1), MaxValueValidator(9999)])

    def generate_quoting_number(self):
        self.quote_monthly_number += 1
        self.save()
        return f"{now().strftime('%Y/%m')}/{self.quote_monthly_number}"

    def create_api_key(self):
        """
        Create a new API key by calling the cabinet API endpoint.
        Returns the generated API key or None if creation fails.
        """
        try:
            main_settings = get_main_settings()
            if not main_settings or not main_settings.CUSTOM_MT_CONSOLE_URL:
                return None
            
            # Build the API endpoint URL
            url = main_settings.CUSTOM_MT_CONSOLE_URL.rstrip('/') + "/cabinet_api/create_api_key/"
            
            # Prepare request data (following the pattern from text_translation)
            data = {
                "label": str(self.id)
            }
            
            # Prepare headers with authorization token
            headers = {
                "token": main_settings.api_key,
                "Content-Type": "application/json"
            }
            
            # Make the API request (similar pattern to text_translation)
            response = requests.post(url, json=data, headers=headers, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                return result.get('api_key')
            else:
                return None
                
        except requests.RequestException as e:
            return None
        except Exception as e:
            return None

    def save(self, *args, **kwargs):
        """
        Override save to auto-generate API key if empty.
        """
        # If api_key is empty, we need to generate one after getting an ID
        needs_api_key = not self.api_key
        
        if needs_api_key:
            # First save to get an ID
            super().save(*args, **kwargs)
            
            # Now generate API key using the ID
            generated_key = self.create_api_key()
            if generated_key:
                self.api_key = generated_key
            else:
                # Fallback to UUID if API call fails
                self.api_key = str(uuid.uuid4())
            
            # Save again with the API key
            super().save()
        else:
            # Normal save if API key already exists
            super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Group'
        verbose_name_plural = 'Groups'

    def __str__(self):
        return self.name


class User(AbstractUser):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    stripe_customer_id = models.CharField(
        max_length=32, unique=True, verbose_name="Stripe customer ID", null=True, blank=True)
    group = models.ForeignKey(
        UserGroup, on_delete=models.CASCADE, blank=True, null=True)
    language = models.CharField(max_length=32,
                                choices=settings.LANGUAGES, default=settings.LANGUAGE_CODE, verbose_name="Language")
