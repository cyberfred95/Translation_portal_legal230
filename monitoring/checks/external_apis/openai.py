"""
OpenAI API health check.
"""
from typing import Dict, Any

from .base import BaseExternalAPIHealthCheck


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
            return self._create_api_error_result("Unexpected error", e)
