"""
Document processing libraries health check.

Tests the availability of python-docx and python-pptx libraries.
"""
import logging
from typing import Dict, Any

from ..base import BaseHealthCheck

logger = logging.getLogger(__name__)


class DocumentLibrariesHealthCheck(BaseHealthCheck):
    """
    Health check for document processing libraries.
    
    Tests:
    - python-docx library import
    - python-pptx library import
    - Basic functionality of each library
    """
    
    service_name = "Document Libraries (docx/pptx)"
    category = "document_processing"
    
    def _check(self):
        """
        Execute document libraries health check.
        
        Returns:
            HealthCheckResult with success status and details
        """
        from ..base import HealthCheckResult
        
        try:
            results = {}
            
            # Test python-docx
            docx_result = self._test_python_docx()
            results['python-docx'] = docx_result
            
            # Test python-pptx
            pptx_result = self._test_python_pptx()
            results['python-pptx'] = pptx_result
            
            # Check if any failed
            failed_libraries = [
                lib for lib, result in results.items() 
                if not result['success']
            ]
            
            if failed_libraries:
                return self._create_error_result(
                    message=f"Failed to load libraries: {', '.join(failed_libraries)}",
                    details=results
                )
            
            return self._create_success_result(
                message="All document processing libraries are available",
                details={
                    'python-docx': {
                        'status': 'available',
                        'version': results['python-docx'].get('version', 'unknown')
                    },
                    'python-pptx': {
                        'status': 'available',
                        'version': results['python-pptx'].get('version', 'unknown')
                    }
                }
            )
            
        except Exception as e:
            logger.error(f"Document libraries health check failed: {str(e)}", exc_info=True)
            return self._create_error_result(
                message=f"Unexpected error: {str(e)}",
                error=e,
                details={'exception_type': type(e).__name__}
            )
    
    def _test_python_docx(self) -> Dict[str, Any]:
        """
        Test python-docx library availability.
        
        Returns:
            Dictionary with success status
        """
        try:
            from docx import Document
            import docx
            
            # Get version if available
            version = getattr(docx, '__version__', 'unknown')
            
            # Test basic functionality - create empty document
            doc = Document()
            
            return {
                'success': True,
                'version': version,
                'details': {
                    'import': 'success',
                    'basic_functionality': 'ok'
                }
            }
            
        except ImportError as e:
            return {
                'success': False,
                'error': f"Failed to import python-docx: {str(e)}",
                'details': {'import': 'failed'}
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"python-docx test failed: {str(e)}",
                'details': {
                    'import': 'success',
                    'basic_functionality': 'failed',
                    'exception_type': type(e).__name__
                }
            }
    
    def _test_python_pptx(self) -> Dict[str, Any]:
        """
        Test python-pptx library availability.
        
        Returns:
            Dictionary with success status
        """
        try:
            from pptx import Presentation
            import pptx
            
            # Get version if available
            version = getattr(pptx, '__version__', 'unknown')
            
            # Test basic functionality - create empty presentation
            prs = Presentation()
            
            return {
                'success': True,
                'version': version,
                'details': {
                    'import': 'success',
                    'basic_functionality': 'ok'
                }
            }
            
        except ImportError as e:
            return {
                'success': False,
                'error': f"Failed to import python-pptx: {str(e)}",
                'details': {'import': 'failed'}
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"python-pptx test failed: {str(e)}",
                'details': {
                    'import': 'success',
                    'basic_functionality': 'failed',
                    'exception_type': type(e).__name__
                }
            }
