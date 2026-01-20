"""
Active Trail API health check.
"""
from typing import Dict, Any, Optional
from django.conf import settings

from .base import BaseExternalAPIHealthCheck
from ..base import HealthCheckResult


class ActiveTrailHealthCheck(BaseExternalAPIHealthCheck):
    """
    Check Active Trail API by sending a real test email.
    
    Sends an email to the health-check user using a random template.
    """
    
    def __init__(self):
        super().__init__()
        self.service_name = 'Active Trail'
    
    def _check(self) -> HealthCheckResult:
        """Test Active Trail by sending a real email."""
        # Verify API key is configured
        api_key_error = self._verify_api_key_configured()
        if api_key_error:
            return api_key_error
        
        # Get health-check user
        test_user_error = self._verify_test_user_configured()
        if test_user_error:
            return test_user_error
        
        # Test by sending real email
        try:
            result = self._send_test_email()
            
            if result['success']:
                return self._create_success_result(
                    message="Active Trail email sent successfully",
                    details={
                        'configured': True,
                        'api_key_prefix': self._mask_api_key(self._get_api_key()),
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
                message=f"Active Trail email test failed: {str(e)}",
                error=e
            )
    
    def _verify_test_user_configured(self) -> Optional[HealthCheckResult]:
        """Verify health-check user is configured."""
        test_user_email = getattr(settings, 'HEALTH_CHECK_USER_EMAIL', None)
        if not test_user_email:
            return self._create_error_result(
                message="HEALTH_CHECK_USER_EMAIL not configured in .env",
                details={'configured': False}
            )
        return None
    
    def _get_api_key_setting_name(self) -> str:
        """Get Active Trail API key setting name."""
        return 'ACTIVE_TRAIL_API_KEY'
    
    def _test_api_connection(self, api_key: str) -> Dict[str, Any]:
        """Test Active Trail API by sending email."""
        return self._send_test_email()
    
    def _send_test_email(self) -> Dict[str, Any]:
        """
        Send a real test email via Active Trail.
        
        Selects a random template and sends to HEALTH_CHECK_USER_EMAIL.
        """
        try:
            import random
            from emails.models import EmailSettings, EmailType
            from emails.send_email import send_email
            
            # Get random template
            random_template = self._get_random_template()
            if isinstance(random_template, dict):  # Error response
                return random_template
            
            # Get EmailType
            email_type = self._get_email_type(random_template)
            if isinstance(email_type, dict):  # Error response
                return email_type
            
            # Send email
            test_user_email = getattr(settings, 'HEALTH_CHECK_USER_EMAIL', None)
            test_data = self._get_test_email_data()
            
            error_response = send_email(
                email=test_user_email,
                email_type=email_type,
                language=random_template.language,
                dict_pairs=test_data
            )
            
            if error_response:
                return self._create_email_error_result(random_template, error_response)
            
            return self._create_email_success_result(random_template, test_user_email)
            
        except ImportError as e:
            return {'success': False, 'error': f'Email module not available: {str(e)}', 
                    'details': {'error_type': 'ImportError'}}
        except Exception as e:
            return {'success': False, 'error': f'Unexpected error: {str(e)}', 
                    'details': {'error_type': type(e).__name__}}
    
    def _get_random_template(self):
        """Get a random email template from database."""
        import random
        from emails.models import EmailSettings
        
        templates = list(EmailSettings.objects.all())
        if not templates:
            return {'success': False, 'error': 'No email templates configured', 
                    'details': {'templates_count': 0}}
        return random.choice(templates)
    
    def _get_email_type(self, template):
        """Get EmailType enum from template."""
        from emails.models import EmailType
        
        try:
            return EmailType[template.email_type]
        except (KeyError, AttributeError):
            return {'success': False, 'error': f'Invalid email type: {template.email_type}',
                    'details': {'email_type': template.email_type}}
    
    def _get_test_email_data(self) -> Dict[str, str]:
        """Get generic test data for email template variables."""
        return {
            'user_name': 'Health Check Test',
            'test_message': 'Automated health check test email',
            'timestamp': 'Health check automated test'
        }
    
    def _create_email_error_result(self, template, error_response) -> Dict[str, Any]:
        """Create error result for failed email sending."""
        return {
            'success': False,
            'error': f'Failed to send email: {str(error_response)}',
            'details': {
                'template_id': template.template_id,
                'email_type': template.email_type,
                'language': template.language
            }
        }
    
    def _create_email_success_result(self, template, recipient: str) -> Dict[str, Any]:
        """Create success result for sent email."""
        return {
            'success': True,
            'details': {
                'email_sent': True,
                'recipient': recipient,
                'template_id': template.template_id,
                'email_type': template.email_type,
                'subject': template.subject,
                'language': template.language,
                'note': 'Real email sent to health-check user'
            }
        }
