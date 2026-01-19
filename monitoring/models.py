"""
Models for storing monitoring and health check results.
"""
from django.db import models
from django.utils import timezone


class HealthCheckResult(models.Model):
    """
    Store results of health checks for monitoring and historical tracking.
    """
    
    STATUS_CHOICES = [
        ('success', 'Success'),
        ('warning', 'Warning'),
        ('error', 'Error'),
    ]
    
    CATEGORY_CHOICES = [
        ('infrastructure', 'Infrastructure'),
        ('external_api', 'External API'),
        ('translation', 'Translation'),
        ('database', 'Database'),
        ('docker', 'Docker'),
    ]
    
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    service_name = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    message = models.TextField()
    details = models.JSONField(null=True, blank=True)
    execution_time_ms = models.IntegerField(
        null=True,
        blank=True,
        help_text="Execution time in milliseconds"
    )
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp', 'status']),
            models.Index(fields=['service_name', '-timestamp']),
        ]
        verbose_name = 'Health Check Result'
        verbose_name_plural = 'Health Check Results'
    
    def __str__(self):
        return f"{self.service_name} - {self.status} at {self.timestamp}"
    
    def is_successful(self) -> bool:
        """Check if the health check was successful."""
        return self.status == 'success'
    
    def has_error(self) -> bool:
        """Check if the health check has an error."""
        return self.status == 'error'


class HealthCheckRun(models.Model):
    """
    Store information about complete health check runs.
    """
    
    TRIGGER_CHOICES = [
        ('manual', 'Manual'),
        ('scheduled', 'Scheduled (Celery)'),
    ]
    
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    trigger = models.CharField(max_length=20, choices=TRIGGER_CHOICES)
    total_checks = models.IntegerField(default=0)
    successful_checks = models.IntegerField(default=0)
    failed_checks = models.IntegerField(default=0)
    warning_checks = models.IntegerField(default=0)
    total_execution_time_ms = models.IntegerField(null=True, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Health Check Run'
        verbose_name_plural = 'Health Check Runs'
    
    def __str__(self):
        return f"Health Check Run at {self.timestamp} ({self.trigger})"
    
    def is_successful(self) -> bool:
        """Check if all health checks in this run were successful."""
        return self.failed_checks == 0 and self.warning_checks == 0
    
    def has_failures(self) -> bool:
        """Check if any health checks failed."""
        return self.failed_checks > 0
    
    def success_rate(self) -> float:
        """Calculate the success rate as a percentage."""
        if self.total_checks == 0:
            return 0.0
        return (self.successful_checks / self.total_checks) * 100
