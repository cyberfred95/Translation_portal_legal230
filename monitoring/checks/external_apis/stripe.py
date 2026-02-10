"""
Stripe API health check.
"""
from typing import Dict, Any

from .base import BaseExternalAPIHealthCheck


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
