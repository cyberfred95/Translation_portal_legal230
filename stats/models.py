from django.db import models
from users.models import User


# Create your models here.


class UserStats(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    chars = models.BigIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "User statistics"
        verbose_name_plural = "User statistics"
