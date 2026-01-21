"""
Base classes and utilities for health checks.
"""
import time
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any


class HealthCheckStatus(Enum):
    """Status of a health check."""
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class HealthCheckResult:
    """Result of a single health check."""
    service_name: str
    status: HealthCheckStatus
    message: str
    category: str
    details: Optional[Dict[str, Any]] = None
    execution_time_ms: Optional[int] = None
    
    def to_dict(self) -> dict:
        """Convert result to dictionary format."""
        return {
            'service_name': self.service_name,
            'status': self.status.value,
            'message': self.message,
            'category': self.category,
            'details': self.details,
            'execution_time_ms': self.execution_time_ms,
        }


class BaseHealthCheck:
    """
    Base class for all health checks.
    
    Provides common functionality like timing, error handling, and result creation.
    
    Subclasses should define:
    - service_name: str - Name of the service being checked
    - category: str - Category of the health check
    """
    
    # Default values (should be overridden by subclasses)
    service_name: str = "Unknown Service"
    category: str = "uncategorized"
    
    def __init__(self):
        # Only set service_name if not already defined by subclass
        if not hasattr(self.__class__, 'service_name') or self.__class__.service_name == BaseHealthCheck.service_name:
            self.service_name = self.__class__.__name__.replace('HealthCheck', '')
        # Category should be defined by subclass, don't override it here
    
    def run(self) -> HealthCheckResult:
        """
        Execute the health check with timing.
        
        Returns:
            HealthCheckResult with status, message, and timing information.
        """
        start_time = time.time()
        
        try:
            result = self._check()
            result.execution_time_ms = self._calculate_execution_time(start_time)
            return result
            
        except Exception as e:
            return self._create_error_result(
                message=f"Health check failed: {str(e)}",
                error=e,
                execution_time_ms=self._calculate_execution_time(start_time)
            )
    
    def _check(self) -> HealthCheckResult:
        """
        Implement the actual health check logic.
        
        Must be overridden by subclasses.
        
        Returns:
            HealthCheckResult with check results.
        """
        raise NotImplementedError("Subclasses must implement _check()")
    
    def _calculate_execution_time(self, start_time: float) -> int:
        """Calculate execution time in milliseconds."""
        return int((time.time() - start_time) * 1000)
    
    def _create_success_result(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ) -> HealthCheckResult:
        """Create a success result."""
        return HealthCheckResult(
            service_name=self.service_name,
            status=HealthCheckStatus.SUCCESS,
            message=message,
            category=self.category,
            details=details
        )
    
    def _create_error_result(
        self,
        message: str,
        error: Optional[Exception] = None,
        details: Optional[Dict[str, Any]] = None,
        execution_time_ms: Optional[int] = None
    ) -> HealthCheckResult:
        """Create an error result."""
        error_details = details or {}
        if error:
            error_details.update({
                'error': str(error),
                'error_type': type(error).__name__
            })
        
        return HealthCheckResult(
            service_name=self.service_name,
            status=HealthCheckStatus.ERROR,
            message=message,
            category=self.category,
            details=error_details,
            execution_time_ms=execution_time_ms
        )
    
    def _create_warning_result(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ) -> HealthCheckResult:
        """Create a warning result."""
        return HealthCheckResult(
            service_name=self.service_name,
            status=HealthCheckStatus.WARNING,
            message=message,
            category=self.category,
            details=details
        )
