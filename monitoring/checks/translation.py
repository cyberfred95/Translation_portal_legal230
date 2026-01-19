"""
Health checks for LARA Bridge translation services.
"""
import logging
import requests
import time
from typing import Dict, Any, Optional
from django.conf import settings
from django.contrib.auth import get_user_model

from .base import BaseHealthCheck, HealthCheckResult
from ..constants import (
    HealthCheckCategory,
    LARA_TEST_TEXT_SOURCE,
    LARA_TEST_TEXT_TARGET_LANGUAGE,
    LARA_TEST_TEXT_SOURCE_LANGUAGE,
    LARA_REQUEST_TIMEOUT_SECONDS
)

logger = logging.getLogger(__name__)
User = get_user_model()


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
    
    def _get_test_user(self) -> Optional[User]:
        """
        Get test user for health checks.
        
        Uses user configured in HEALTH_CHECK_USER_EMAIL setting.
        Returns None if not configured - no fallback.
        
        Returns:
            User instance or None if not configured/found
        """
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


class LaraTextTranslationHealthCheck(BaseLaraHealthCheck):
    """
    Check LARA text translation functionality.
    
    Verifies that text can be translated through LARA Bridge.
    """
    
    def __init__(self):
        super().__init__()
        self.service_name = 'LARA Text Translation'
    
    def _check(self) -> HealthCheckResult:
        """Test LARA text translation."""
        prereq_error = self._verify_prerequisites()
        if prereq_error:
            return prereq_error
        
        test_user = self._get_test_user()
        
        try:
            result = self._test_text_translation(test_user)
            return self._create_success_result(
                message="LARA text translation is working",
                details=result['details']
            ) if result['success'] else self._create_error_result(
                message=result['error'],
                details=result.get('details')
            )
        except Exception as e:
            return self._create_error_result(
                message=f"LARA text translation check failed: {str(e)}",
                error=e
            )
    
    def _test_text_translation(self, user: User) -> Dict[str, Any]:
        """
        Test text translation through LARA API.
        
        Args:
            user: User to use for the test
        
        Returns:
            Dictionary with success status and details
        """
        config = self._get_lara_config()
        
        # Prepare request
        url = f"{config['api_url']}/api/lara/translate-text"
        headers = {'Content-Type': 'application/json'}
        
        payload = {
            'accessKeyId': config['access_key_id'],
            'accessKeySecret': config['access_key_secret'],
            'text': LARA_TEST_TEXT_SOURCE,
            'source': LARA_TEST_TEXT_SOURCE_LANGUAGE,
            'target': LARA_TEST_TEXT_TARGET_LANGUAGE,
            'userToken': str(user.id)
        }
        
        try:
            start_time = time.time()
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=LARA_REQUEST_TIMEOUT_SECONDS
            )
            execution_time = int((time.time() - start_time) * 1000)
            
            if response.status_code == 200:
                data = response.json()
                translated_text = data.get('translation', '')  # LARA returns 'translation', not 'translated_text'
                
                if translated_text:
                    return {
                        'success': True,
                        'details': {
                            'source_text': LARA_TEST_TEXT_SOURCE,
                            'translated_text': translated_text,
                            'source_language': LARA_TEST_TEXT_SOURCE_LANGUAGE,
                            'target_language': LARA_TEST_TEXT_TARGET_LANGUAGE,
                            'execution_time_ms': execution_time,
                            'status_code': response.status_code
                        }
                    }
                else:
                    return {
                        'success': False,
                        'error': "Translation returned empty result",
                        'details': {
                            'status_code': response.status_code,
                            'response': data
                        }
                    }
            else:
                return {
                    'success': False,
                    'error': f"LARA API returned status {response.status_code}",
                    'details': {
                        'status_code': response.status_code,
                        'response': response.text[:200]
                    }
                }
                
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError, Exception):
            return self._handle_request_errors("Text translation")


class LaraDocumentTranslationHealthCheck(BaseLaraHealthCheck):
    """
    Check LARA document translation functionality.
    
    Performs a full document translation test:
    - Uploads a test .txt file
    - Waits for translation to complete
    - Verifies the result
    - Deletes the test document
    """
    
    def __init__(self):
        super().__init__()
        self.service_name = 'LARA Document Translation'
    
    def _check(self) -> HealthCheckResult:
        """Test LARA document translation with real file upload."""
        prereq_error = self._verify_prerequisites()
        if prereq_error:
            return prereq_error
        
        test_user = self._get_test_user()
        
        # Test document translation
        document_id = None
        try:
            # Upload document
            upload_result = self._upload_test_document(test_user)
            if not upload_result['success']:
                return self._create_error_result(
                    message=f"Failed to upload document: {upload_result['error']}",
                    details=upload_result.get('details')
                )
            
            document_id = upload_result['document_id']
            upload_time = upload_result['execution_time_ms']
            
            # Wait for translation to complete
            wait_result = self._wait_for_translation(document_id)
            if not wait_result['success']:
                return self._create_error_result(
                    message=f"Translation failed: {wait_result['error']}",
                    details=wait_result.get('details')
                )
            
            wait_time = wait_result['execution_time_ms']
            
            # Delete test document
            self._delete_test_document(document_id)
            
            return self._create_success_result(
                message="LARA document translation completed successfully",
                details={
                    'upload_time_ms': upload_time,
                    'translation_time_ms': wait_time,
                    'total_time_ms': upload_time + wait_time,
                    'document_id': document_id,
                    'status': wait_result.get('final_status')
                }
            )
            
        except Exception as e:
            # Cleanup: try to delete document if it was created
            if document_id:
                try:
                    self._delete_test_document(document_id)
                except:
                    pass
            
            return self._create_error_result(
                message=f"LARA document translation check failed: {str(e)}",
                error=e
            )
    
    def _upload_test_document(self, user: User) -> Dict[str, Any]:
        """
        Upload a test document for translation.
        
        Args:
            user: User to use for the test
        
        Returns:
            Dictionary with success status, document_id, and execution time
        """
        from io import BytesIO
        
        config = self._get_lara_config()
        url = f"{config['api_url']}/api/lara/translate-document"
        
        # Create a simple test file
        test_content = "Health check test document. This is a test."
        test_file = BytesIO(test_content.encode('utf-8'))
        test_file.name = 'health_check_test.txt'
        
        # Prepare multipart form data
        files = {'file': ('health_check_test.txt', test_file, 'text/plain')}
        data = {
            'accessKeyId': config['access_key_id'],
            'accessKeySecret': config['access_key_secret'],
            'source': 'en',
            'target': 'fr',
            'userToken': str(user.id)
        }
        
        try:
            start_time = time.time()
            response = requests.post(
                url,
                files=files,
                data=data,
                timeout=LARA_REQUEST_TIMEOUT_SECONDS
            )
            execution_time = int((time.time() - start_time) * 1000)
            
            if response.status_code in [200, 201]:
                data = response.json()
                document_id = data.get('id') or data.get('document_id')
                
                if document_id:
                    return {
                        'success': True,
                        'document_id': document_id,
                        'execution_time_ms': execution_time
                    }
                else:
                    return {
                        'success': False,
                        'error': "No document ID in response",
                        'details': {'response': data}
                    }
            else:
                return {
                    'success': False,
                    'error': f"Upload failed with status {response.status_code}",
                    'details': {
                        'status_code': response.status_code,
                        'response': response.text[:200]
                    }
                }
                
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError, Exception):
            return self._handle_request_errors("Document upload")
    
    def _wait_for_translation(self, document_id: str, max_wait_seconds: int = 60) -> Dict[str, Any]:
        """
        Wait for document translation to complete.
        
        Args:
            document_id: ID of the document to check
            max_wait_seconds: Maximum time to wait (default 60s)
        
        Returns:
            Dictionary with success status and final status
        """
        config = self._get_lara_config()
        url = f"{config['api_url']}/api/lara/document-status/{document_id}"
        
        start_time = time.time()
        poll_interval = 2  # Check every 2 seconds
        
        while (time.time() - start_time) < max_wait_seconds:
            try:
                response = requests.get(url, timeout=LARA_REQUEST_TIMEOUT_SECONDS)
                
                if response.status_code == 200:
                    data = response.json()
                    status = data.get('status', '').lower()
                    
                    # Check if translation is complete
                    if status in ['translated', 'completed', 'done']:
                        execution_time = int((time.time() - start_time) * 1000)
                        return {
                            'success': True,
                            'final_status': status,
                            'execution_time_ms': execution_time
                        }
                    elif status in ['error', 'failed']:
                        return {
                            'success': False,
                            'error': f"Translation failed with status: {status}",
                            'details': {'error_message': data.get('error_message') or data.get('error_reason')}
                        }
                    
                    # Still processing, wait and retry
                    time.sleep(poll_interval)
                else:
                    return {
                        'success': False,
                        'error': f"Status check failed with code {response.status_code}",
                        'details': {'status_code': response.status_code}
                    }
                    
            except Exception as e:
                return {
                    'success': False,
                    'error': f"Error checking status: {str(e)}",
                    'details': {'error_type': type(e).__name__}
                }
        
        # Timeout
        return {
            'success': False,
            'error': f"Translation timeout after {max_wait_seconds} seconds",
            'details': {'timeout': max_wait_seconds}
        }
    
    def _delete_test_document(self, document_id: str) -> Dict[str, Any]:
        """
        Delete a test document.
        
        Args:
            document_id: ID of the document to delete
        
        Returns:
            Dictionary with success status
        """
        config = self._get_lara_config()
        url = f"{config['api_url']}/api/lara/documents/{document_id}/delete"
        
        try:
            response = requests.delete(url, timeout=LARA_REQUEST_TIMEOUT_SECONDS)
            
            if response.status_code in [200, 204]:
                return {'success': True}
            else:
                return {
                    'success': False,
                    'error': f"Delete failed with status {response.status_code}"
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f"Error deleting document: {str(e)}"
            }


class LaraGlossaryHealthCheck(BaseLaraHealthCheck):
    """
    Check LARA glossary endpoint accessibility.
    
    Note: Full glossary creation requires CSV file upload.
    This check verifies the endpoint is accessible without creating actual glossaries.
    """
    
    def __init__(self):
        super().__init__()
        self.service_name = 'LARA Glossary'
    
    def _check(self) -> HealthCheckResult:
        """Test LARA glossary endpoint accessibility."""
        prereq_error = self._verify_prerequisites()
        if prereq_error:
            return prereq_error
        
        try:
            result = self._test_glossary_endpoint()
            return self._create_success_result(
                message="LARA glossary endpoint is accessible",
                details=result['details']
            ) if result['success'] else self._create_error_result(
                message=result['error'],
                details=result.get('details')
            )
        except Exception as e:
            return self._create_error_result(
                message=f"LARA glossary check failed: {str(e)}",
                error=e
            )
    
    def _test_glossary_endpoint(self) -> Dict[str, Any]:
        """
        Test glossary endpoint accessibility.
        
        Note: Glossary creation requires CSV file upload (multipart/form-data).
        We test with HEAD request to check endpoint accessibility.
        
        Returns:
            Dictionary with success status and details
        """
        config = self._get_lara_config()
        
        # Test with HEAD request to check endpoint
        url = f"{config['api_url']}/api/lara/glossaries-list/create/"
        headers = {'Content-Type': 'application/json'}
        
        try:
            response = requests.head(
                url,
                headers=headers,
                timeout=LARA_REQUEST_TIMEOUT_SECONDS
            )
            
            # Any response (including 400/405) means endpoint is accessible
            return {
                'success': True,
                'details': {
                    'endpoint_accessible': True,
                    'status_code': response.status_code,
                    'note': 'Full glossary test requires CSV file upload'
                }
            }
            
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError, Exception):
            return self._handle_request_errors("Glossary endpoint check")
