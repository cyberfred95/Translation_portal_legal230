"""
Base class for Celery health checks.
"""
from celery import current_app
from celery.app.control import Inspect

from ..base import BaseHealthCheck
from ...constants import HealthCheckCategory


class BaseCeleryHealthCheck(BaseHealthCheck):
    """
    Base class for Celery health checks.
    
    Provides shared functionality for accessing Celery inspector.
    """
    
    def __init__(self):
        super().__init__()
        self.category = HealthCheckCategory.INFRASTRUCTURE
    
    def _get_inspector(self) -> Inspect:
        """Get Celery inspector instance."""
        return current_app.control.inspect()
