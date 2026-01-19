"""
Health checks for external API services (OpenAI, Stripe, Active Trail, Adobe).
"""
import logging
from typing import Dict, Any, Optional
from abc import abstractmethod
from django.conf import settings

from .base import BaseHealthCheck, HealthCheckResult
from ..constants import (
    HealthCheckCategory,
    API_KEY_MASK_PREFIX_LENGTH,
    API_KEY_MASK_SUFFIX_LENGTH,
    API_REQUEST_TIMEOUT_SECONDS
)

logger = logging.getLogger(__name__)


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


class OpenAIHealthCheck(BaseExternalAPIHealthCheck):
    """Check OpenAI API connectivity and authentication."""
    
    def __init__(self):
        super().__init__()
        self.service_name = 'OpenAI'
    
    def _get_api_key_setting_name(self) -> str:
        """Get OpenAI API key setting name."""
        return 'OPENAI_API_KEY'
    
    def _test_api_connection(self, api_key: str) -> Dict[str, Any]:
        """Test OpenAI API with a minimal request."""
        try:
            from openai import OpenAI, AuthenticationError, RateLimitError, APIError
            
            client = OpenAI(api_key=api_key)
            
            # Make a minimal test request (list models is lightweight)
            try:
                models = client.models.list()
                model_count = len(list(models.data))
                
                return {
                    'success': True,
                    'details': {
                        'models_available': model_count,
                        'api_responsive': True
                    }
                }
                
            except AuthenticationError as e:
                return self._create_api_error_result("Authentication failed", e, 'AuthenticationError')
            except RateLimitError as e:
                return self._create_api_error_result("Rate limit exceeded", e, 'RateLimitError')
            except APIError as e:
                return self._create_api_error_result("API error", e, 'APIError')
                
        except ImportError as e:
            return self._create_api_error_result("OpenAI library not installed", e, 'ImportError')
        except Exception as e:
            return self._create_api_error_result("Unexpected error", e, type(e).__name__)
    
    def _create_api_error_result(self, message: str, error: Exception, error_type: str) -> Dict[str, Any]:
        """Create standardized error result for API calls."""
        return {
            'success': False,
            'error': f"{message}: {str(error)}",
            'details': {'error_type': error_type}
        }


class StripeHealthCheck(BaseExternalAPIHealthCheck):
    """Check Stripe API connectivity and authentication."""
    
    def __init__(self):
        super().__init__()
        self.service_name = 'Stripe'
    
    def _get_api_key_setting_name(self) -> str:
        """Get Stripe API key setting name."""
        return 'STRIPE_API_KEY'
    
    def _test_api_connection(self, api_key: str) -> Dict[str, Any]:
        """Test Stripe API with a minimal request."""
        try:
            import stripe
            
            stripe.api_key = api_key
            
            # Make a minimal test request (retrieve account is lightweight)
            try:
                account = stripe.Account.retrieve()
                
                return {
                    'success': True,
                    'details': {
                        'account_id': account.id,
                        'account_type': getattr(account, 'type', 'unknown'),
                        'api_responsive': True
                    }
                }
                
            except stripe.error.AuthenticationError as e:
                return self._create_api_error_result("Authentication failed", e)
            except stripe.error.RateLimitError as e:
                return self._create_api_error_result("Rate limit exceeded", e)
            except stripe.error.StripeError as e:
                return self._create_api_error_result("Stripe error", e)
                
        except ImportError as e:
            return self._create_api_error_result("Stripe library not installed", e)
        except Exception as e:
            return self._create_api_error_result("Unexpected error", e)
    
    def _create_api_error_result(self, message: str, error: Exception) -> Dict[str, Any]:
        """Create standardized error result for API calls."""
        return {
            'success': False,
            'error': f"{message}: {str(error)}",
            'details': {'error_type': type(error).__name__}
        }


class ActiveTrailHealthCheck(BaseExternalAPIHealthCheck):
    """Check Active Trail API connectivity and authentication."""
    
    def __init__(self):
        super().__init__()
        self.service_name = 'Active Trail'
    
    def _check(self) -> HealthCheckResult:
        """Test Active Trail API connectivity (override to include URL)."""
        # Verify API key is configured
        api_key_error = self._verify_api_key_configured()
        if api_key_error:
            return api_key_error
        
        api_key = self._get_api_key()
        api_url = self._get_api_url()
        
        # Test API connection
        try:
            result = self._test_api_connection_with_url(api_key, api_url)
            
            if result['success']:
                return self._create_success_result(
                    message="Active Trail API is accessible",
                    details={
                        'configured': True,
                        'api_key_prefix': self._mask_api_key(api_key),
                        'api_url': api_url,
                        **result.get('details', {})
                    }
                )
            else:
                return self._create_error_result(
                    message=result['error'],
                    details=result.get('details')
                )
                
        except Exception as e:
            return self._create_error_result(
                message=f"Active Trail API check failed: {str(e)}",
                error=e
            )
    
    def _get_api_key_setting_name(self) -> str:
        """Get Active Trail API key setting name."""
        return 'ACTIVE_TRAIL_API_KEY'
    
    def _get_api_url(self) -> str:
        """Get Active Trail API URL from settings."""
        return getattr(
            settings,
            'ACTIVE_TRAIL_SEND_EMAIL_REQUEST_URL',
            'https://webapi.mymarketing.co.il/api/OperationalMessage/Message'
        )
    
    def _test_api_connection(self, api_key: str) -> Dict[str, Any]:
        """Not used for Active Trail (uses _test_api_connection_with_url instead)."""
        return {'success': False, 'error': 'Use _test_api_connection_with_url'}
    
    def _test_api_connection_with_url(self, api_key: str, api_url: str) -> Dict[str, Any]:
        """
        Test Active Trail API endpoint accessibility.
        
        Note: We only test if the endpoint is reachable, not sending actual emails.
        """
        try:
            import requests
            
            headers = {
                "Authorization": api_key,
                "Content-Type": "application/json"
            }
            
            try:
                response = requests.head(
                    api_url,
                    headers=headers,
                    timeout=API_REQUEST_TIMEOUT_SECONDS
                )
                
                # Active Trail returns various status codes
                # We consider it successful if we get any response (endpoint is up)
                return {
                    'success': True,
                    'details': {
                        'endpoint_reachable': True,
                        'status_code': response.status_code
                    }
                }
                
            except requests.exceptions.Timeout:
                return self._create_request_error_result("Request timeout", 'Timeout')
            except requests.exceptions.ConnectionError as e:
                return self._create_request_error_result(f"Cannot connect: {str(e)}", 'ConnectionError')
            except requests.exceptions.RequestException as e:
                return self._create_request_error_result(f"Request error: {str(e)}", type(e).__name__)
                
        except ImportError as e:
            return self._create_request_error_result(f"Requests library not installed: {str(e)}", 'ImportError')
        except Exception as e:
            return self._create_request_error_result(f"Unexpected error: {str(e)}", type(e).__name__)
    
    def _create_request_error_result(self, error_message: str, error_type: str) -> Dict[str, Any]:
        """Create standardized error result for request errors."""
        return {
            'success': False,
            'error': error_message,
            'details': {'error_type': error_type}
        }
