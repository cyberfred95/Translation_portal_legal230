"""
Glossary service for LARA backend operations.

Handles glossary creation, update, and deletion through LARA backend API.
Replaces direct Custom.MT API calls.
"""
import csv
import io
import logging
import os

import openpyxl
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import InMemoryUploadedFile

from .lara_client import LaraClient, LaraClientError
from ..processor import GlossaryProcessor

logger = logging.getLogger(__name__)


class LaraGlossaryService:
    """
    Service layer for glossary operations via LARA backend.

    This service:
    - Validates glossary files before upload
    - Converts XLSX files to CSV format
    - Communicates with LARA backend for CRUD operations
    """

    def __init__(self):
        self._client = None
        self._processor = GlossaryProcessor()

    @property
    def client(self) -> LaraClient:
        """Lazy initialization of LARA client."""
        if self._client is None:
            self._client = LaraClient()
        return self._client

    def _get_glossary_name(self, glossary) -> str:
        """
        Generate glossary name from file or model name.

        Args:
            glossary: Glossary model instance

        Returns:
            Glossary name string
        """
        if glossary.name:
            return glossary.name

        if glossary.file and hasattr(glossary.file, 'name'):
            return os.path.splitext(os.path.basename(glossary.file.name))[0]

        return f"glossary_{glossary.pk}"

    def _get_user_uuid(self, glossary) -> str:
        """
        Get user UUID for personal glossary identification.

        Args:
            glossary: Glossary model instance

        Returns:
            User UUID string or None for system glossaries
        """
        if glossary.user:
            return str(glossary.user.uuid)
        if glossary.group:
            return f"group_{glossary.group.id}"
        return None

    def _convert_xlsx_to_csv(self, xlsx_file) -> InMemoryUploadedFile:
        """
        Convert XLSX file to CSV format.

        Args:
            xlsx_file: Django file object containing XLSX data

        Returns:
            InMemoryUploadedFile containing CSV data
        """
        # Open XLSX file
        if hasattr(xlsx_file, 'open'):
            xlsx_file.open('rb')

        try:
            workbook = openpyxl.load_workbook(xlsx_file.file, data_only=True)
            sheet = workbook.active

            # Write to CSV in memory
            output = io.StringIO()
            writer = csv.writer(output)

            for row in sheet.iter_rows(values_only=True):
                # Filter out None values and empty rows
                if any(cell is not None for cell in row):
                    writer.writerow(row)

            output.seek(0)

            # Create new filename with .csv extension
            base_name = os.path.splitext(os.path.basename(xlsx_file.name))[0]
            csv_filename = f"{base_name}.csv"

            # Create InMemoryUploadedFile
            csv_bytes = output.getvalue().encode('utf-8')
            csv_file = InMemoryUploadedFile(
                file=io.BytesIO(csv_bytes),
                field_name='glossary_file',
                name=csv_filename,
                content_type='text/csv',
                size=len(csv_bytes),
                charset='utf-8'
            )

            logger.info(f"Converted XLSX to CSV: {csv_filename}")
            return csv_file

        finally:
            if hasattr(xlsx_file, 'close'):
                xlsx_file.close()

    def _prepare_file(self, glossary):
        """
        Validate and prepare glossary file for upload.

        Converts XLSX to CSV if needed.

        Args:
            glossary: Glossary model instance

        Returns:
            File object ready for upload

        Raises:
            ValidationError: If file validation fails
        """
        if not glossary.file:
            raise ValidationError("No file provided for glossary")

        # Validate file structure
        self._processor.validate_file(glossary.file)

        # Reopen file after validation (processor may have closed it)
        if hasattr(glossary.file, 'seek'):
            try:
                glossary.file.seek(0)
            except ValueError:
                # File was closed, reopen it
                if hasattr(glossary.file, 'open'):
                    glossary.file.open('rb')

        # Convert XLSX to CSV if needed
        file_ext = os.path.splitext(glossary.file.name)[1].lower()
        if file_ext == '.xlsx':
            return self._convert_xlsx_to_csv(glossary.file)

        # For CSV files, ensure UTF-8 encoding
        if file_ext == '.csv':
            return self._processor.convert_file_to_utf_8(glossary.file)

        return glossary.file

    def create_glossary(self, glossary) -> str:
        """
        Create a glossary in LARA backend.

        Args:
            glossary: Glossary model instance with file attached

        Returns:
            LARA glossary ID

        Raises:
            ValidationError: If file validation fails
            LaraClientError: If LARA API call fails
        """
        logger.info(f"Creating glossary: {self._get_glossary_name(glossary)}")

        # Prepare file
        try:
            prepared_file = self._prepare_file(glossary)
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"File preparation error: {e}")
            raise ValidationError(f"File preparation failed: {str(e)}")

        # Get glossary parameters
        glossary_name = self._get_glossary_name(glossary)
        user_uuid = self._get_user_uuid(glossary)

        # Call LARA backend
        success, glossary_id, error = self.client.create_glossary(
            glossary_file=prepared_file,
            user_glossary_name=glossary_name,
            uuid=user_uuid
        )

        if not success:
            logger.error(f"LARA create failed: {error}")
            raise LaraClientError(f"Glossary creation failed: {error}")

        logger.info(f"Glossary created with ID: {glossary_id}")
        return glossary_id

    def update_glossary(self, glossary) -> None:
        """
        Update a glossary in LARA backend.

        Args:
            glossary: Glossary model instance with new file attached

        Raises:
            ValidationError: If file validation fails or no glossary_id
            LaraClientError: If LARA API call fails
        """
        if not glossary.glossary_id:
            raise ValidationError("Cannot update glossary without glossary_id")

        logger.info(f"Updating glossary: {glossary.glossary_id}")

        # Prepare file
        try:
            prepared_file = self._prepare_file(glossary)
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"File preparation error: {e}")
            raise ValidationError(f"File preparation failed: {str(e)}")

        # Call LARA backend
        glossary_name = self._get_glossary_name(glossary)
        success, error = self.client.update_glossary(
            glossary_id=glossary.glossary_id,
            glossary_file=prepared_file,
            user_glossary_name=glossary_name
        )

        if not success:
            logger.error(f"LARA update failed: {error}")
            raise LaraClientError(f"Glossary update failed: {error}")

        logger.info(f"Glossary updated: {glossary.glossary_id}")

    def delete_glossary(self, glossary) -> None:
        """
        Delete a glossary from LARA backend.

        Args:
            glossary: Glossary model instance

        Raises:
            LaraClientError: If LARA API call fails
        """
        if not glossary.glossary_id:
            logger.warning("Cannot delete glossary without glossary_id")
            return

        logger.info(f"Deleting glossary: {glossary.glossary_id}")

        success, error = self.client.delete_glossary(glossary.glossary_id)

        if not success:
            logger.error(f"LARA delete failed: {error}")
            raise LaraClientError(f"Glossary deletion failed: {error}")

        logger.info(f"Glossary deleted: {glossary.glossary_id}")
