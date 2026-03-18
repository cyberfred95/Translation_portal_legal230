"""
Base class for LARA Bridge health checks.
"""
import logging
from typing import Any, Dict, Optional

from django.conf import settings

from ..base import BaseHealthCheck, HealthCheckResult
from ...constants import (
    HealthCheckCategory,
    LARA_REQUEST_TIMEOUT_SECONDS
)

logger = logging.getLogger(__name__)


class BaseLaraHealthCheck(BaseHealthCheck):
    """
    Base class for LARA Bridge health checks.
    
    Provides common functionality for LARA API access and authentication.
    """
    
    def __init__(self):
        super().__init__()
        self.category = HealthCheckCategory.TRANSLATION
    
    def _get_lara_config(self) -> Dict[str, str]:
        """Get LARA API configuration from settings."""
        return {
            'api_url': getattr(settings, 'LARA_API_URL', None),
            'access_key_id': getattr(settings, 'LARA_ACCESS_KEY_ID', None),
            'access_key_secret': getattr(settings, 'LARA_ACCESS_KEY_SECRET', None)
        }
    
    def _verify_lara_configured(self) -> Optional[HealthCheckResult]:
        """
        Verify LARA is properly configured.
        
        Returns:
            HealthCheckResult if error, None if configured
        """
        config = self._get_lara_config()
        
        if not config['api_url']:
            return self._create_error_result(
                message="LARA_API_URL not configured in settings",
                details={'configured': False}
            )
        
        if not config['access_key_id'] or not config['access_key_secret']:
            return self._create_error_result(
                message="LARA access keys not configured in settings",
                details={'configured': False, 'api_url': config['api_url']}
            )
        
        return None
    
    def _get_test_user(self) -> Optional[Any]:
        """
        Get test user for health checks.

        Uses user configured in HEALTH_CHECK_USER_EMAIL setting.
        Returns None if not configured - no fallback.

        Returns:
            User instance or None if not configured/found
        """
        from django.contrib.auth import get_user_model

        User = get_user_model()
        test_user_email = getattr(settings, 'HEALTH_CHECK_USER_EMAIL', None)

        if not test_user_email:
            logger.warning("HEALTH_CHECK_USER_EMAIL not configured in .env")
            return None

        try:
            return User.objects.get(email=test_user_email)
        except User.DoesNotExist:
            logger.error(f"Test user with email {test_user_email} not found in database")
            return None
    
    def _verify_test_user(self) -> Optional[HealthCheckResult]:
        """Verify test user exists and is configured."""
        test_user = self._get_test_user()
        if test_user:
            return None
        
        test_user_email = getattr(settings, 'HEALTH_CHECK_USER_EMAIL', None)
        if not test_user_email:
            return self._create_error_result(
                message="HEALTH_CHECK_USER_EMAIL not configured in .env",
                details={'configured': False, 'required_setting': 'HEALTH_CHECK_USER_EMAIL'}
            )
        return self._create_error_result(
            message=f"Test user not found in database: {test_user_email}",
            details={'configured': True, 'email': test_user_email, 'found': False}
        )
    
    def _verify_prerequisites(self) -> Optional[HealthCheckResult]:
        """Verify LARA configuration and test user. Returns error or None."""
        config_error = self._verify_lara_configured()
        if config_error:
            return config_error
        return self._verify_test_user()
    
    def _handle_test_result(self, result: Dict[str, Any], success_msg: str) -> HealthCheckResult:
        """
        Process a test result dictionary and return appropriate HealthCheckResult.
        
        Args:
            result: Dictionary with 'success' key and optional 'error', 'details'
            success_msg: Message to use if successful
        
        Returns:
            HealthCheckResult
        """
        return self._create_success_result(
            message=success_msg,
            details=result['details']
        ) if result['success'] else self._create_error_result(
            message=result['error'],
            details=result.get('details')
        )
    
    def _handle_request_errors(self, error_context: str) -> Dict[str, Any]:
        """
        Create standardized error response for common request exceptions.
        
        This is a helper to be used in except blocks.
        
        Args:
            error_context: Description of what was being attempted
        
        Returns:
            Dictionary with error details
        """
        # This method is meant to be called from except blocks
        # So it will capture the current exception
        import sys
        exc_type, exc_value, _ = sys.exc_info()
        
        if exc_type is None:
            return {
                'success': False,
                'error': f"{error_context}: Unknown error",
                'details': {'error_type': 'Unknown'}
            }
        
        error_name = exc_type.__name__
        
        if error_name == 'Timeout':
            return {
                'success': False,
                'error': f"{error_context}: Request timeout after {LARA_REQUEST_TIMEOUT_SECONDS} seconds",
                'details': {'error_type': 'Timeout'}
            }
        elif error_name == 'ConnectionError':
            return {
                'success': False,
                'error': f"{error_context}: Cannot connect to LARA - {str(exc_value)}",
                'details': {'error_type': 'ConnectionError'}
            }
        else:
            return {
                'success': False,
                'error': f"{error_context}: {str(exc_value)}",
                'details': {'error_type': error_name}
            }
