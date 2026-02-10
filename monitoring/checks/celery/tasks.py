"""
Celery task execution health check.
"""
from typing import Dict, Any
from celery.exceptions import TimeoutError as CeleryTimeoutError

from .base import BaseCeleryHealthCheck
from ..base import HealthCheckResult
from ...constants import (
    CELERY_TASK_TIMEOUT_SECONDS,
    CELERY_TASK_EXPIRES_SECONDS,
    CELERY_TEST_TASK_INPUT,
    CELERY_TEST_TASK_EXPECTED_OUTPUT
)


class CeleryTaskExecutionHealthCheck(BaseCeleryHealthCheck):
    """
    Check Celery task execution capability.
    
    Verifies that workers can actually execute a simple test task.
    """
    
    def __init__(self):
        super().__init__()
        self.service_name = 'Celery Task Execution'
    
    def _check(self) -> HealthCheckResult:
        """Test Celery task execution."""
        try:
            task_result = self._execute_test_task()
            
            if task_result['success']:
                return self._create_success_result(
                    message="Celery workers can execute tasks successfully",
                    details=task_result['details']
                )
            else:
                return self._create_error_result(
                    message=task_result['error'],
                    details=task_result.get('details')
                )
                
        except ImportError as e:
            return self._create_error_result(
                message="Test task not found",
                error=e
            )
        except Exception as e:
            return self._create_error_result(
                message=f"Task execution check failed: {str(e)}",
                error=e
            )
    
    def _execute_test_task(self) -> Dict[str, Any]:
        """
        Execute a test task and return the result.
        
        Uses polling instead of .get() to avoid issues when called from within a task.
        
        Returns:
            Dictionary with success status, error message, and details
        """
        import time
        from celery.result import AsyncResult
        from ...tasks import health_check_test_task
        
        # Execute test task asynchronously
        async_result = health_check_test_task.apply_async(
            args=[CELERY_TEST_TASK_INPUT],
            expires=CELERY_TASK_EXPIRES_SECONDS
        )
        
        # Poll for result instead of using .get() (which is forbidden within tasks)
        start_time = time.time()
        poll_interval = 0.5  # Check every 0.5 seconds
        
        while (time.time() - start_time) < CELERY_TASK_TIMEOUT_SECONDS:
            # Check if task is ready
            if async_result.ready():
                try:
                    # Get result without blocking
                    task_output = async_result.result
                    
                    if task_output == CELERY_TEST_TASK_EXPECTED_OUTPUT:
                        return {
                            'success': True,
                            'details': {
                                'task_id': async_result.id,
                                'task_result': task_output,
                                'task_state': async_result.state
                            }
                        }
                    else:
                        return {
                            'success': False,
                            'error': f"Task returned unexpected result: {task_output}",
                            'details': {
                                'task_id': async_result.id,
                                'expected': CELERY_TEST_TASK_EXPECTED_OUTPUT,
                                'got': task_output
                            }
                        }
                except Exception as e:
                    return {
                        'success': False,
                        'error': f"Task failed with exception: {str(e)}",
                        'details': {
                            'task_id': async_result.id,
                            'exception_type': type(e).__name__
                        }
                    }
            
            # Wait before next check
            time.sleep(poll_interval)
        
        # Timeout
        return {
            'success': False,
            'error': f"Task execution timed out after {CELERY_TASK_TIMEOUT_SECONDS} seconds",
            'details': {'task_id': async_result.id, 'state': async_result.state}
        }
