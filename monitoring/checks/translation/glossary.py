"""
LARA glossary health check.
"""
import time
import requests
from typing import Dict, Any
from io import BytesIO

from .base import BaseLaraHealthCheck, User
from ..base import HealthCheckResult
from ...constants import LARA_REQUEST_TIMEOUT_SECONDS


class LaraGlossaryHealthCheck(BaseLaraHealthCheck):
    """
    Check LARA personal glossary creation.
    
    Creates a real personal glossary using the same endpoint as the UI.
    Personal glossaries don't require a name (auto-generated).
    """
    
    def __init__(self):
        super().__init__()
        self.service_name = 'LARA Glossary'
    
    def _check(self) -> HealthCheckResult:
        """Test LARA personal glossary creation and deletion."""
        prereq_error = self._verify_prerequisites()
        if prereq_error:
            return prereq_error
        
        test_user = self._get_test_user()
        glossary_id = None
        
        try:
            # Create personal glossary
            create_result = self._create_personal_glossary(test_user)
            if not create_result['success']:
                return self._create_error_result(
                    message=f"Failed to create glossary: {create_result['error']}",
                    details=create_result.get('details')
                )
            
            glossary_id = create_result['glossary_id']
            creation_time = create_result['execution_time_ms']
            
            # Delete glossary
            self._delete_glossary(glossary_id)
            
            return self._create_success_result(
                message="LARA personal glossary creation successful",
                details={
                    'creation_time_ms': creation_time,
                    'glossary_id': glossary_id,
                    'glossary_name': create_result.get('glossary_name'),
                    'note': 'Personal glossary (auto-named, no user_glossary_name required)'
                }
            )
            
        except Exception as e:
            # Cleanup: try to delete glossary if it was created
            if glossary_id:
                try:
                    self._delete_glossary(glossary_id)
                except:
                    pass
            
            return self._create_error_result(
                message=f"LARA glossary check failed: {str(e)}",
                error=e
            )
    
    def _create_personal_glossary(self, user: User) -> Dict[str, Any]:
        """
        Create a personal glossary (same as UI).
        
        Uses /create-from-lexa/ endpoint which auto-generates the name.
        No user_glossary_name required!
        
        Args:
            user: User to use for the test
        
        Returns:
            Dictionary with success status, glossary_id, and execution time
        """
        config = self._get_lara_config()
        # Use the personal glossary endpoint (from Lexa)
        url = f"{config['api_url']}/api/lara/glossaries-list/create-from-lexa/"
        
        # Create a simple test CSV
        csv_content = "En,fr\nHealth,Santé"
        csv_file = BytesIO(csv_content.encode('utf-8'))
        
        # Prepare multipart form data and headers
        files = {'glossary_file': ('health_check.csv', csv_file, 'text/csv')}
        data = {
            'accessKeyId': config['access_key_id'],
            'accessKeySecret': config['access_key_secret']
        }
        headers = {
            'X-User-UUID': str(user.uuid)  # User UUID from health-check user
        }
        
        try:
            start_time = time.time()
            response = requests.post(
                url,
                files=files,
                data=data,
                headers=headers,
                timeout=60  # Personal glossary creation can take time
            )
            execution_time = int((time.time() - start_time) * 1000)
            
            if response.status_code in [200, 201]:
                data = response.json()
                glossary_id = data.get('id') or data.get('glossary_id')
                
                if glossary_id:
                    return {
                        'success': True,
                        'glossary_id': glossary_id,
                        'glossary_name': data.get('name', 'N/A'),
                        'execution_time_ms': execution_time
                    }
                else:
                    return {
                        'success': False,
                        'error': "No glossary ID in response",
                        'details': {'response': data}
                    }
            else:
                return {
                    'success': False,
                    'error': f"Creation failed with status {response.status_code}",
                    'details': {
                        'status_code': response.status_code,
                        'response': response.text[:200]
                    }
                }
                
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError, Exception):
            return self._handle_request_errors("Personal glossary creation")
    
    def _delete_glossary(self, glossary_id: str) -> Dict[str, Any]:
        """
        Delete a glossary.
        
        Args:
            glossary_id: ID of the glossary to delete
        
        Returns:
            Dictionary with success status
        """
        config = self._get_lara_config()
        url = f"{config['api_url']}/api/lara/glossaries-list/{glossary_id}/delete/"
        
        try:
            response = requests.delete(url, timeout=LARA_REQUEST_TIMEOUT_SECONDS)
            return {'success': response.status_code in [200, 204]}
        except Exception:
            return {'success': False}
