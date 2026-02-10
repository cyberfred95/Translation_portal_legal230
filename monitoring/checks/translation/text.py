"""
LARA text translation health check.
"""
import time
import requests
from typing import Dict, Any

from .base import BaseLaraHealthCheck, User
from ..base import HealthCheckResult
from ...constants import (
    LARA_TEST_TEXT_SOURCE,
    LARA_TEST_TEXT_TARGET_LANGUAGE,
    LARA_TEST_TEXT_SOURCE_LANGUAGE,
    LARA_REQUEST_TIMEOUT_SECONDS
)


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
            return self._handle_test_result(result, "LARA text translation is working")
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
