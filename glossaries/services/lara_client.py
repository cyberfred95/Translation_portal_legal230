"""
HTTP client for LARA backend API.

Handles communication with the LARA Django backend for glossary operations.
"""
import logging
from typing import Dict, Optional, Tuple
from dataclasses import dataclass

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

# Request timeout in seconds
REQUEST_TIMEOUT = 120


@dataclass
class LaraResponse:
    """Response wrapper for LARA API calls."""
    success: bool
    data: Optional[Dict] = None
    error: Optional[str] = None
    status_code: int = 0


class LaraClientError(Exception):
    """Exception raised for LARA client errors."""
    pass


class LaraClient:
    """
    HTTP client for LARA backend glossary API.

    Endpoints:
        - POST /create/: Create a new glossary
        - POST /<id>/update/: Update an existing glossary
        - POST /<id>/delete/: Delete a glossary
    """

    def __init__(self):
        self.base_url = getattr(settings, 'LARA_API_URL', '')
        if not self.base_url:
            raise LaraClientError("LARA_API_URL not configured in settings")

        self.glossaries_url = f"{self.base_url}/api/lara/glossaries-list"

    def _make_request(
        self,
        method: str,
        endpoint: str,
        files: Optional[Dict] = None,
        data: Optional[Dict] = None,
        timeout: int = REQUEST_TIMEOUT
    ) -> LaraResponse:
        """
        Execute HTTP request to LARA backend.

        Args:
            method: HTTP method (POST, DELETE)
            endpoint: API endpoint path
            files: Files to upload
            data: Form data
            timeout: Request timeout in seconds

        Returns:
            LaraResponse with success status and data/error
        """
        url = f"{self.glossaries_url}{endpoint}"

        try:
            logger.info(f"LARA request: {method} {url}")

            response = requests.request(
                method=method,
                url=url,
                files=files,
                data=data,
                timeout=timeout
            )

            logger.info(f"LARA response: {response.status_code}")

            # Parse JSON response
            try:
                response_data = response.json()
            except ValueError:
                response_data = {'raw': response.text[:500]}

            if response.status_code >= 400:
                error_msg = response_data.get('error', response.text[:200])
                logger.error(f"LARA error: {error_msg}")
                return LaraResponse(
                    success=False,
                    error=error_msg,
                    status_code=response.status_code
                )

            return LaraResponse(
                success=True,
                data=response_data,
                status_code=response.status_code
            )

        except requests.exceptions.Timeout:
            error_msg = f"LARA request timeout after {timeout}s"
            logger.error(error_msg)
            return LaraResponse(success=False, error=error_msg)

        except requests.exceptions.ConnectionError as e:
            error_msg = f"LARA connection error: {str(e)}"
            logger.error(error_msg)
            return LaraResponse(success=False, error=error_msg)

        except requests.exceptions.RequestException as e:
            error_msg = f"LARA request error: {str(e)}"
            logger.error(error_msg)
            return LaraResponse(success=False, error=error_msg)

    def create_glossary(
        self,
        glossary_file,
        user_glossary_name: str,
        uuid: Optional[str] = None
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Create a new glossary via LARA backend.

        Args:
            glossary_file: Django file object (FieldFile or UploadedFile)
            user_glossary_name: Display name for the glossary
            uuid: User UUID for personal glossaries (None for system glossaries)

        Returns:
            Tuple of (success, glossary_id or None, error message or None)
        """
        # Prepare file for upload
        if hasattr(glossary_file, 'open'):
            glossary_file.open('rb')

        try:
            files = {
                'glossary_file': (
                    glossary_file.name,
                    glossary_file,
                    'text/csv'
                )
            }

            data = {'user_glossary_name': user_glossary_name}
            if uuid:
                data['uuid'] = uuid

            response = self._make_request(
                method='POST',
                endpoint='/create/',
                files=files,
                data=data
            )

            if response.success:
                glossary_id = response.data.get('glossary_id')
                logger.info(f"Glossary created: {glossary_id}")
                return True, glossary_id, None

            return False, None, response.error

        finally:
            if hasattr(glossary_file, 'close'):
                glossary_file.close()

    def update_glossary(
        self,
        glossary_id: str,
        glossary_file,
        user_glossary_name: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Update an existing glossary via LARA backend.

        Args:
            glossary_id: LARA glossary ID
            glossary_file: New CSV file
            user_glossary_name: Optional new display name

        Returns:
            Tuple of (success, error message or None)
        """
        if hasattr(glossary_file, 'open'):
            glossary_file.open('rb')

        try:
            files = {
                'glossary_file': (
                    glossary_file.name,
                    glossary_file,
                    'text/csv'
                )
            }

            data = {}
            if user_glossary_name:
                data['user_glossary_name'] = user_glossary_name

            response = self._make_request(
                method='POST',
                endpoint=f'/{glossary_id}/update/',
                files=files,
                data=data if data else None
            )

            if response.success:
                logger.info(f"Glossary updated: {glossary_id}")
                return True, None

            return False, response.error

        finally:
            if hasattr(glossary_file, 'close'):
                glossary_file.close()

    def delete_glossary(self, glossary_id: str) -> Tuple[bool, Optional[str]]:
        """
        Delete a glossary via LARA backend.

        Args:
            glossary_id: LARA glossary ID

        Returns:
            Tuple of (success, error message or None)
        """
        response = self._make_request(
            method='POST',
            endpoint=f'/{glossary_id}/delete/'
        )

        if response.success:
            logger.info(f"Glossary deleted: {glossary_id}")
            return True, None

        return False, response.error
