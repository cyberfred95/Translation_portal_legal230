import os
import csv
import zipfile
import tempfile
import logging
from django.core.files.base import ContentFile
from django.db import models

from languages.models import Language
from users.models import User, UserGroup
from django.core.validators import FileExtensionValidator
from domains.models import Domain
from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)


class Glossary(models.Model):
    name = models.CharField(max_length=255, blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)
    group = models.ForeignKey(UserGroup, on_delete=models.SET_NULL, blank=True, null=True)
    file = models.FileField(upload_to='glossaries/', validators=[FileExtensionValidator(['csv', 'xlsx'])])
    glossary_id = models.CharField(max_length=255, blank=True, null=True)
    source_language = models.ForeignKey(
        Language,
        on_delete=models.CASCADE,
        related_name='source_language_glossaries'
    )
    target_language = models.ForeignKey(
        Language,
        on_delete=models.CASCADE,
        related_name='target_language_glossaries'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    domain = models.ForeignKey(
        Domain, on_delete=models.SET_NULL, blank=True, null=True, related_name='glossaries')

    class Meta:
        verbose_name = 'Glossary'
        verbose_name_plural = 'Glossaries'

    def clean(self):
        if self.user and self.group:
            raise ValidationError(
                "You cannot select both a user and a group at the same time.")

        if self.pk:

            existing_default_glossaries = Glossary.objects.filter(
                domain=self.domain,
                source_language=self.source_language,
                target_language=self.target_language,
                group__isnull=True,
                user__isnull=True
            )
            if not self.group and not self.user:
                existing_default_glossaries = existing_default_glossaries.exclude(
                    pk=self.pk)

                if existing_default_glossaries.exists():
                    raise ValidationError(
                        "A default glossary for this language pair and domain already exists.")

                if not self.domain:
                    raise ValidationError("You must choose a domain for default glossary.")

        if not self.domain and not self.user and not self.group:
            raise ValidationError("You have to choose domain or user or group")

        existing_glossary_filters = {
            'domain': self.domain,
            'source_language': self.source_language,
            'target_language': self.target_language
        }

        if self.user:
            if Glossary.objects.filter(**existing_glossary_filters, user=self.user).exclude(pk=self.pk).exists():
                raise ValidationError(
                    "A glossary for this language pair and domain and user already exists")
        elif self.group:
            if Glossary.objects.filter(**existing_glossary_filters, group=self.group).exclude(pk=self.pk).exists():
                raise ValidationError(
                    "A glossary for this language pair and domain and user already exists")

        super().clean()

    def save(self, *args, **kwargs):

        if not self.name and self.file:
            self.name = os.path.splitext(os.path.basename(self.file.name))[0]

        super(Glossary, self).save(*args, **kwargs)

    def to_json(self, request):
        return {
            "id": self.id,
            "name": self.name,
            "source_language": self.source_language.abbreviation.upper(),
            "target_language": self.target_language.abbreviation.upper(),
            "created_at": self.created_at,
        }

    @staticmethod
    def glossaries_batch(csv_file_path, zip_file_path=None, base_directory=None):
        """
        Batch load glossaries from a CSV file.

        Args:
            csv_file_path: Path to the CSV file containing glossary information
            zip_file_path: Path to the ZIP file containing glossary files (optional)
            base_directory: Base directory where glossary files are located (optional, ignored if zip_file_path is provided)

        Returns:
            dict: Summary of the batch operation with success/error counts
        """
        logger.info(
            f"Starting batch processing - CSV: {csv_file_path}, ZIP: {zip_file_path}")

        results = {
            'created': 0,
            'errors': [],
            'total_rows': 0
        }

        # Verify CSV file exists
        if not os.path.exists(csv_file_path):
            error_msg = f"CSV file not found: {csv_file_path}"
            logger.error(error_msg)
            results['errors'].append(error_msg)
            return results

        # Verify ZIP file exists if provided
        if zip_file_path and not os.path.exists(zip_file_path):
            error_msg = f"ZIP file not found: {zip_file_path}"
            logger.error(error_msg)
            results['errors'].append(error_msg)
            return results

        temp_dir = None
        try:
            # Extract ZIP file if provided
            if zip_file_path:
                logger.info("Extracting ZIP file")
                temp_dir = tempfile.mkdtemp()
                logger.info(f"Created temp directory: {temp_dir}")

                try:
                    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
                        # List contents of ZIP file
                        zip_contents = zip_ref.namelist()
                        logger.info(f"ZIP file contents: {zip_contents}")

                        zip_ref.extractall(temp_dir)
                        logger.info(f"ZIP extracted to: {temp_dir}")

                        # Verify extraction was successful
                        if not os.path.exists(temp_dir):
                            error_msg = f"Temp directory not created: {temp_dir}"
                            logger.error(error_msg)
                            results['errors'].append(error_msg)
                            return results

                        # List extracted files recursively
                        extracted_files = []
                        for root, dirs, files in os.walk(temp_dir):
                            for file in files:
                                full_path = os.path.join(root, file)
                                relative_path = os.path.relpath(
                                    full_path, temp_dir)
                                extracted_files.append(relative_path)
                                logger.info(f"Extracted file: {full_path}")

                        logger.info(f"All extracted files: {extracted_files}")

                        if not extracted_files:
                            error_msg = "No files were extracted from ZIP"
                            logger.error(error_msg)
                            results['errors'].append(error_msg)
                            return results

                except zipfile.BadZipFile as e:
                    error_msg = f"Invalid ZIP file: {str(e)}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
                    return results

                working_directory = temp_dir
            else:
                working_directory = base_directory
                logger.info(f"Using base directory: {base_directory}")

            logger.info("Reading CSV file")
            with open(csv_file_path, 'r', encoding='utf-8') as csvfile:
                # Read the first few lines to debug
                csvfile.seek(0)
                first_lines = [csvfile.readline().strip() for _ in range(5)]
                logger.info(f"First 5 lines of CSV: {first_lines}")

                csvfile.seek(0)
                reader = csv.DictReader(csvfile)

                # Verify CSV structure
                expected_columns = {
                    'file', 'source_language', 'target_language', 'domain'}
                actual_columns = set(
                    reader.fieldnames) if reader.fieldnames else set()
                logger.info(f"CSV columns: {actual_columns}")

                if not expected_columns.issubset(actual_columns):
                    error_msg = f"Invalid CSV structure. Expected columns: {expected_columns}, Found: {actual_columns}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
                    return results

                # Start at 2 to account for header
                for row_num, row in enumerate(reader, start=2):
                    results['total_rows'] += 1
                    logger.info(f"Processing row {row_num}: {row}")

                    try:
                        # Get file path and normalize it (convert Windows paths to Unix)
                        file_path = row['file'].strip()
                        original_file_path = file_path

                        # Convert Windows backslashes to forward slashes
                        file_path = file_path.replace('\\', '/')
                        logger.info(f"Normalized file path: {file_path}")

                        # Extract just the filename for searching
                        filename_only = os.path.basename(file_path)
                        logger.info(f"Filename only: {filename_only}")

                        found_file_path = None

                        if working_directory:
                            # First, try the direct path
                            direct_path = os.path.join(
                                working_directory, file_path)
                            logger.info(f"Trying direct path: {direct_path}")

                            if os.path.exists(direct_path):
                                found_file_path = direct_path
                                logger.info(
                                    f"Found at direct path: {found_file_path}")
                            else:
                                # Try just the filename in the root of working directory
                                root_path = os.path.join(
                                    working_directory, filename_only)
                                logger.info(f"Trying root path: {root_path}")

                                if os.path.exists(root_path):
                                    found_file_path = root_path
                                    logger.info(
                                        f"Found at root path: {found_file_path}")
                                else:
                                    # Search recursively for the file
                                    logger.info(
                                        f"Searching recursively for: {filename_only}")
                                    for root, dirs, files in os.walk(working_directory):
                                        logger.info(
                                            f"Checking directory: {root}, files: {files}")
                                        if filename_only in files:
                                            found_file_path = os.path.join(
                                                root, filename_only)
                                            logger.info(
                                                f"Found file recursively: {found_file_path}")
                                            break

                                        # Also try case-insensitive search
                                        for file in files:
                                            if file.lower() == filename_only.lower():
                                                found_file_path = os.path.join(
                                                    root, file)
                                                logger.info(
                                                    f"Found file with case-insensitive match: {found_file_path}")
                                                break
                                        if found_file_path:
                                            break

                        # Verify file exists
                        if not found_file_path or not os.path.exists(found_file_path):
                            # List all files in working directory for debugging
                            if working_directory and os.path.exists(working_directory):
                                all_files = []
                                for root, dirs, files in os.walk(working_directory):
                                    for file in files:
                                        all_files.append(
                                            os.path.join(root, file))
                                logger.info(
                                    f"All available files in working directory: {all_files}")

                            error_msg = f"Row {row_num} (Fichier: {original_file_path}) - Fichier non trouvé dans le ZIP (recherché: {filename_only})"
                            logger.warning(error_msg)
                            results['errors'].append(error_msg)
                            continue

                        logger.info(
                            f"File found successfully: {found_file_path}")

                        # Get or create domain
                        domain_name = row['domain'].strip()
                        domain, created = Domain.objects.get_or_create(
                            name=domain_name)
                        logger.info(
                            f"Domain: {domain_name} ({'created' if created else 'existing'})")

                        # Get languages
                        source_lang_code = row['source_language'].strip()
                        target_lang_code = row['target_language'].strip()

                        try:
                            # Try to find language by abbreviation first, then by name
                            source_language = None
                            try:
                                source_language = Language.objects.get(
                                    abbreviation=source_lang_code)
                                logger.info(
                                    f"Source language found by abbreviation: {source_language}")
                            except Language.DoesNotExist:
                                try:
                                    source_language = Language.objects.get(
                                        name=source_lang_code)
                                    logger.info(
                                        f"Source language found by name: {source_language}")
                                except Language.DoesNotExist:
                                    # Try case-insensitive search
                                    source_language = Language.objects.filter(
                                        abbreviation__iexact=source_lang_code
                                    ).first()
                                    if not source_language:
                                        source_language = Language.objects.filter(
                                            name__iexact=source_lang_code
                                        ).first()
                                    if source_language:
                                        logger.info(
                                            f"Source language found by case-insensitive search: {source_language}")

                            if not source_language:
                                raise Language.DoesNotExist()

                        except Language.DoesNotExist:
                            # List all available languages for debugging
                            all_languages = Language.objects.all().values('id', 'name', 'abbreviation')
                            logger.info(
                                f"Available languages: {list(all_languages)}")
                            error_msg = f"Row {row_num} (Fichier: {row['file']}) - Langue source '{source_lang_code}' non trouvée"
                            logger.error(error_msg)
                            results['errors'].append(error_msg)
                            continue

                        try:
                            # Try to find language by abbreviation first, then by name
                            target_language = None
                            try:
                                target_language = Language.objects.get(
                                    abbreviation=target_lang_code)
                                logger.info(
                                    f"Target language found by abbreviation: {target_language}")
                            except Language.DoesNotExist:
                                try:
                                    target_language = Language.objects.get(
                                        name=target_lang_code)
                                    logger.info(
                                        f"Target language found by name: {target_language}")
                                except Language.DoesNotExist:
                                    # Try case-insensitive search
                                    target_language = Language.objects.filter(
                                        abbreviation__iexact=target_lang_code
                                    ).first()
                                    if not target_language:
                                        target_language = Language.objects.filter(
                                            name__iexact=target_lang_code
                                        ).first()
                                    if target_language:
                                        logger.info(
                                            f"Target language found by case-insensitive search: {target_language}")

                            if not target_language:
                                raise Language.DoesNotExist()

                        except Language.DoesNotExist:
                            # List all available languages for debugging
                            all_languages = Language.objects.all().values('id', 'name', 'abbreviation')
                            logger.info(
                                f"Available languages: {list(all_languages)}")
                            error_msg = f"Row {row_num} (Fichier: {row['file']}) - Langue cible '{target_lang_code}' non trouvée"
                            logger.error(error_msg)
                            results['errors'].append(error_msg)
                            continue

                        # Check if glossary already exists (default glossary without user/group)
                        existing_glossary = Glossary.objects.filter(
                            domain=domain,
                            source_language=source_language,
                            target_language=target_language,
                            user__isnull=True,
                            group__isnull=True
                        ).first()

                        # Read file content and create ContentFile to avoid path issues
                        file_name = os.path.basename(found_file_path)

                        with open(found_file_path, 'rb') as f:
                            file_content = f.read()
                            # Use ContentFile which doesn't depend on file path
                            django_file = ContentFile(
                                file_content, name=file_name)

                            if existing_glossary:
                                # Update existing glossary
                                logger.info(
                                    f"Row {row_num}: Updating existing glossary for {source_lang_code}-{target_lang_code} in {domain_name}")

                                # Update the file and name
                                existing_glossary.file = django_file
                                existing_glossary.name = os.path.splitext(file_name)[0]

                                # Save and let the post_save signal handle API update
                                existing_glossary.save()

                                logger.info(f"Successfully updated glossary: {existing_glossary.name}")
                                results['created'] += 1
                            else:
                                # Create new glossary
                                logger.info(f"Row {row_num}: Creating new glossary for {source_lang_code}-{target_lang_code} in {domain_name}")

                                glossary = Glossary(
                                    domain=domain,
                                    source_language=source_language,
                                    target_language=target_language,
                                    file=django_file,
                                    name=os.path.splitext(file_name)[0]
                                )

                                # Save and let the post_save signal handle API creation and update
                                glossary.save()

                                logger.info(f"Successfully created glossary: {glossary.name}")
                                results['created'] += 1

                    except Exception as e:
                        # Extract more meaningful error messages
                        error_detail = str(e)

                        # Get the filename being processed
                        filename_info = f"Fichier: {row.get('file', 'inconnu')}"

                        # Check if it's a JSON error from the API
                        if 'glossary_id' in error_detail and 'Input should be a valid string' in error_detail:
                            error_msg = f"Row {row_num} ({filename_info}) - L'API de glossaire a échoué - vérifiez que le service de glossaire est accessible et que le fichier est valide"
                        elif "The 'file' attribute has no file associated with it" in error_detail:
                            error_msg = f"Row {row_num} ({filename_info}) - Le fichier du glossaire n'a pas pu être traité correctement"
                        else:
                            error_msg = f"Row {row_num} ({filename_info}) - {error_detail}"

                        logger.error(error_msg, exc_info=True)
                        results['errors'].append(error_msg)

        except Exception as e:
            error_msg = f"Error processing files: {str(e)}"
            logger.error(error_msg, exc_info=True)
            results['errors'].append(error_msg)
        finally:
            # Clean up temporary directory
            if temp_dir and os.path.exists(temp_dir):
                logger.info(f"Cleaning up temporary directory: {temp_dir}")
                try:
                    import shutil
                    shutil.rmtree(temp_dir)
                    logger.info(
                        f"Successfully cleaned up temporary directory: {temp_dir}")
                except Exception as cleanup_error:
                    logger.error(
                        f"Error cleaning up temporary directory: {cleanup_error}")

        logger.info(f"Batch processing completed: {results}")
        return results
