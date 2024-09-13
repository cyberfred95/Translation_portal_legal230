from django.db import models

from users.models import User


# Create your models here.

class Glossary(models.Model):
    name = models.CharField(max_length=255)
    default = models.BooleanField(default=False),
    user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)
    file = models.FileField(upload_to='glossaries/')
    source_language = models.CharField(max_length=255)
    target_language = models.CharField(max_length=255)
