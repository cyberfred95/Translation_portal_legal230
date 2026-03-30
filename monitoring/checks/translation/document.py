"""
LARA document translation health check.
"""
import time
import requests
from typing import Any, Dict
from io import BytesIO

from .base import BaseLaraHealthCheck
from ..base import HealthCheckResult
from ...constants import LARA_REQUEST_TIMEOUT_SECONDS


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
    
    def _upload_test_document(self, user: Any) -> Dict[str, Any]:
        """
        Upload a test document for translation.
        
        Args:
            user: User to use for the test
        
        Returns:
            Dictionary with success status, document_id, and execution time
        """
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
            'userToken': str(user.uuid)
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
