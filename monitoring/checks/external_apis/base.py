"""
Base class for external API health checks.
"""
from typing import Dict, Any, Optional
from abc import abstractmethod
from django.conf import settings

from ..base import BaseHealthCheck, HealthCheckResult
from ...constants import (
    HealthCheckCategory,
    API_KEY_MASK_PREFIX_LENGTH,
    API_KEY_MASK_SUFFIX_LENGTH
)


class BaseExternalAPIHealthCheck(BaseHealthCheck):
    """
    Base class for external API health checks.
    
    Provides common functionality for API key validation, masking, and testing.
    Subclasses only need to implement:
    - _get_api_key_setting_name()
    - _test_api_connection()
    """
    
    def __init__(self):
        super().__init__()
        self.category = HealthCheckCategory.EXTERNAL_API
    
    def _check(self) -> HealthCheckResult:
        """Test external API connectivity."""
        # Verify API key is configured
        api_key_error = self._verify_api_key_configured()
        if api_key_error:
            return api_key_error
        
        api_key = self._get_api_key()
        
        # Test API connection
        try:
            result = self._test_api_connection(api_key)
            return self._process_api_test_result(result, api_key)
            
        except Exception as e:
            return self._create_error_result(
                message=f"{self.service_name} API check failed: {str(e)}",
                error=e
            )
    
    def _verify_api_key_configured(self) -> Optional[HealthCheckResult]:
        """
        Verify API key is configured.
        
        Returns:
            HealthCheckResult if error, None if configured
        """
        api_key = self._get_api_key()
        if not api_key:
            setting_name = self._get_api_key_setting_name()
            return self._create_error_result(
                message=f"{setting_name} not configured in settings",
                details={'configured': False}
            )
        return None
    
    def _process_api_test_result(
        self,
        result: Dict[str, Any],
        api_key: str
    ) -> HealthCheckResult:
        """
        Process API test result and create appropriate HealthCheckResult.
        
        Args:
            result: Dictionary with success status and details
            api_key: API key (for masking)
        
        Returns:
            HealthCheckResult
        """
        if result['success']:
            return self._create_success_result(
                message=f"{self.service_name} API is accessible and responding",
                details={
                    'configured': True,
                    'api_key_prefix': self._mask_api_key(api_key),
                    **result.get('details', {})
                }
            )
        else:
            return self._create_error_result(
                message=result['error'],
                details=result.get('details')
            )
    
    def _get_api_key(self) -> Optional[str]:
        """Get API key from settings."""
        setting_name = self._get_api_key_setting_name()
        return getattr(settings, setting_name, None)
    
    def _mask_api_key(self, api_key: str) -> str:
        """
        Mask API key for security.
        
        Shows first N and last M characters based on constants.
        
        Args:
            api_key: API key to mask
        
        Returns:
            Masked API key string
        """
        if len(api_key) > API_KEY_MASK_PREFIX_LENGTH:
            prefix = api_key[:API_KEY_MASK_PREFIX_LENGTH]
            suffix = api_key[-API_KEY_MASK_SUFFIX_LENGTH:]
            return f"{prefix}...{suffix}"
        return "***"
    
    @abstractmethod
    def _get_api_key_setting_name(self) -> str:
        """
        Get the setting name for the API key.
        
        Must be implemented by subclasses.
        
        Returns:
            Setting name (e.g., 'OPENAI_API_KEY')
        """
        raise NotImplementedError("Subclasses must implement _get_api_key_setting_name()")
    
    def _create_api_error_result(self, message: str, error: Exception, error_type: str = None) -> Dict[str, Any]:
        """Create standardized error result for API calls."""
        return {
            'success': False,
            'error': f"{message}: {str(error)}",
            'details': {'error_type': error_type or type(error).__name__}
        }
    
    @abstractmethod
    def _test_api_connection(self, api_key: str) -> Dict[str, Any]:
        """
        Test API connection with the given API key.
        
        Must be implemented by subclasses.
        
        Args:
            api_key: API key to use for testing
        
        Returns:
            Dictionary with 'success' (bool), 'error' (str), 'details' (dict)
        """
        raise NotImplementedError("Subclasses must implement _test_api_connection()")
