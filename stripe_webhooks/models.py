from django.db import models


class StripeEvent(models.Model):
    event_id = models.CharField(
        max_length=255,
        unique=True,
        help_text="Unique identifier for the Stripe event"
    )

    event_type = models.CharField(
        max_length=255,
        help_text="Type of Stripe event (e.g., customer.created, invoice.paid)"
    )

    data = models.JSONField(
        help_text="Raw event data from Stripe webhook payload"
    )

    created_at = models.DateTimeField(
        help_text="Timestamp when the event was received"
    )

    status = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Processing status of the webhook event"
    )

    code_response = models.IntegerField(
        blank=True,
        null=True,
        help_text="HTTP response code returned after processing"
    )

    http_response = models.JSONField(
        blank=True,
        null=True,
        help_text="Complete HTTP response data after processing"
    )

    class Meta:
        verbose_name = "Stripe Event"
        verbose_name_plural = "Stripe Events"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['event_type']),
            models.Index(fields=['created_at']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.event_id} - {self.event_type} - {self.status}"

    def __repr__(self):
        return (
            f"StripeEvent(event_id='{self.event_id}', "
            f"event_type='{self.event_type}', status='{self.status}')"
        )
