"""
Adobe PDF Services health check.

Tests the Adobe PDF Services API for PDF to DOCX conversion.
"""
import os
import logging
from typing import Dict, Any, Optional

from ..base import BaseHealthCheck

logger = logging.getLogger(__name__)


class AdobePDFServicesHealthCheck(BaseHealthCheck):
    """
    Health check for Adobe PDF Services API.
    
    Tests:
    - API credentials are configured
    - OAuth authentication works
    - API connectivity
    """
    
    service_name = "Adobe PDF Services"
    category = "document_processing"
    
    # Adobe API endpoints
    AUTH_URL = "https://ims-na1.adobelogin.com/ims/token/v3"
    ASSETS_URL = "https://pdf-services.adobe.io/assets"
    
    # OAuth scope
    OAUTH_SCOPE = (
        'openid,AdobeID,read_organizations,'
        'additional_info.projectedProductContext,additional_info.roles'
    )
    
    def _check(self):
        """
        Execute Adobe PDF Services health check.
        
        Returns:
            HealthCheckResult with success status and details
        """
        from ..base import HealthCheckResult
        
        try:
            # Step 1: Check configuration
            config_result = self._check_configuration()
            if not config_result['success']:
                return self._create_error_result(
                    message=config_result['error'],
                    details=config_result.get('details')
                )
            
            # Step 2: Test authentication
            auth_result = self._test_authentication()
            if not auth_result['success']:
                return self._create_error_result(
                    message=auth_result['error'],
                    details=auth_result.get('details')
                )
            
            # Step 3: Test API connectivity
            api_result = self._test_api_connectivity(auth_result['access_token'])
            if not api_result['success']:
                return self._create_error_result(
                    message=api_result['error'],
                    details=api_result.get('details')
                )
            
            return self._create_success_result(
                message="Adobe PDF Services is accessible and authenticated",
                details={
                    'api': 'adobe-pdf-services',
                    'authentication': 'successful',
                    'api_connectivity': 'ok',
                    'token_expires_in': auth_result.get('expires_in', 'N/A')
                }
            )
            
        except Exception as e:
            logger.error(f"Adobe PDF Services health check failed: {str(e)}", exc_info=True)
            return self._create_error_result(
                message=f"Unexpected error: {str(e)}",
                error=e,
                details={'exception_type': type(e).__name__}
            )
    
    def _check_configuration(self) -> Dict[str, Any]:
        """
        Check if Adobe credentials are configured.
        
        Returns:
            Dictionary with success status
        """
        client_id = os.environ.get('ADOBE_CLIENT_ID')
        client_secret = os.environ.get('ADOBE_CLIENT_SECRET')
        organization_id = os.environ.get('ADOBE_ORGANIZATION_ID')
        
        missing_vars = []
        if not client_id:
            missing_vars.append('ADOBE_CLIENT_ID')
        if not client_secret:
            missing_vars.append('ADOBE_CLIENT_SECRET')
        if not organization_id:
            missing_vars.append('ADOBE_ORGANIZATION_ID')
        
        if missing_vars:
            return {
                'success': False,
                'error': f"Missing environment variables: {', '.join(missing_vars)}",
                'details': {'missing_variables': missing_vars}
            }
        
        return {
            'success': True,
            'details': {
                'client_id': f"{client_id[:8]}..." if len(client_id) > 8 else "***",
                'client_secret': '***',
                'organization_id': f"{organization_id[:20]}..." if len(organization_id) > 20 else "***"
            }
        }
    
    def _test_authentication(self) -> Dict[str, Any]:
        """
        Test OAuth authentication with Adobe PDF Services API.
        
        Returns:
            Dictionary with success status and access token
        """
        try:
            import requests
            
            response = self._make_auth_request(requests)
            
            # Check for authentication errors
            auth_error = self._check_auth_response_status(response)
            if auth_error:
                return auth_error
            
            # Extract and validate token
            return self._extract_access_token(response)
            
        except ImportError:
            return self._error_dict("requests library not available", {'import_error': 'requests'})
        except requests.exceptions.Timeout:
            return self._error_dict("Authentication request timed out", {'error_type': 'timeout_error'})
        except requests.exceptions.RequestException as e:
            logger.error(f"Adobe authentication failed: {str(e)}", exc_info=True)
            return self._error_dict(f"Authentication request failed: {str(e)}", {'exception_type': type(e).__name__})
        except Exception as e:
            return self._error_dict(f"Authentication failed: {str(e)}", {'exception_type': type(e).__name__})
    
    def _make_auth_request(self, requests):
        """Make OAuth authentication request to Adobe."""
        client_id = os.environ.get('ADOBE_CLIENT_ID')
        client_secret = os.environ.get('ADOBE_CLIENT_SECRET')
        
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        data = {
            'client_id': client_id,
            'client_secret': client_secret,
            'grant_type': 'client_credentials',
            'scope': self.OAUTH_SCOPE
        }
        
        return requests.post(self.AUTH_URL, headers=headers, data=data, timeout=10)
    
    def _check_auth_response_status(self, response) -> Optional[Dict[str, Any]]:
        """Check response status and return error if authentication failed."""
        if response.status_code == 401:
            return self._error_dict(
                "Authentication failed: Invalid credentials",
                {'status_code': 401, 'error_type': 'authentication_error'}
            )
        if response.status_code == 403:
            return self._error_dict(
                "API access forbidden: Check subscription status",
                {'status_code': 403, 'error_type': 'authorization_error'}
            )
        
        response.raise_for_status()
        return None
    
    def _extract_access_token(self, response) -> Dict[str, Any]:
        """Extract and validate access token from response."""
        token_data = response.json()
        access_token = token_data.get('access_token')
        
        if not access_token:
            return self._error_dict(
                "No access token received in response",
                {'response_keys': list(token_data.keys())}
            )
        
        expires_in = token_data.get('expires_in', 'N/A')
        
        return {
            'success': True,
            'access_token': access_token,
            'expires_in': f"{expires_in} seconds" if expires_in != 'N/A' else 'N/A',
            'details': {
                'authentication': 'successful',
                'token_type': token_data.get('token_type', 'unknown')
            }
        }
    
    def _error_dict(self, error: str, details: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create error dictionary."""
        return {
            'success': False,
            'error': error,
            'details': details or {}
        }
    
    def _test_api_connectivity(self, access_token: str) -> Dict[str, Any]:
        """
        Test connectivity to Adobe PDF Services API.
        
        Args:
            access_token: OAuth access token
            
        Returns:
            Dictionary with success status
        """
        try:
            import requests
            
            client_id = os.environ.get('ADOBE_CLIENT_ID')
            organization_id = os.environ.get('ADOBE_ORGANIZATION_ID')
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'x-api-key': client_id,
                'x-gw-ims-org-id': organization_id,
                'Content-Type': 'application/json'
            }
            
            # Test with a simple request to the assets endpoint
            # This validates that we can reach the API with valid credentials
            payload = {"mediaType": "application/pdf"}
            
            response = requests.post(
                self.ASSETS_URL,
                headers=headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 401:
                return {
                    'success': False,
                    'error': "API request unauthorized (token may be invalid)",
                    'details': {'status_code': 401}
                }
            
            if response.status_code == 403:
                return {
                    'success': False,
                    'error': "API access forbidden (check organization permissions)",
                    'details': {'status_code': 403}
                }
            
            response.raise_for_status()
            
            # If we get here, the API is accessible
            return {
                'success': True,
                'details': {
                    'api_status': 'accessible',
                    'endpoint': 'assets',
                    'status_code': response.status_code
                }
            }
            
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': "API request timed out",
                'details': {'error_type': 'timeout_error'}
            }
        except requests.exceptions.RequestException as e:
            error_message = str(e)
            logger.error(f"Adobe API connectivity test failed: {error_message}", exc_info=True)
            return {
                'success': False,
                'error': f"API connectivity test failed: {error_message}",
                'details': {'exception_type': type(e).__name__}
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"API test failed: {str(e)}",
                'details': {'exception_type': type(e).__name__}
            }
