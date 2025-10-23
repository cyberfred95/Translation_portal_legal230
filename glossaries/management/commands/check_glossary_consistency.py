"""
Django management command to check consistency between local glossaries and remote API.

Usage:
    python manage.py check_glossary_consistency [options]

Examples:
    # Check local glossaries against remote API (default mode)
    python manage.py check_glossary_consistency

    # Show all glossaries checked (verbose mode)
    python manage.py check_glossary_consistency --verbose

    # Only display glossaries without remote ID
    python manage.py check_glossary_consistency --idNullOnly

    # Delete glossaries without remote ID (with confirmation)
    python manage.py check_glossary_consistency --delIdIsNull

Options:
    --verbose           Show detailed output for each glossary checked
                        Default: False (only shows problems)
                        Use this to see all glossaries, not just errors

    --idNullOnly        Skip API verification and only display glossaries without glossary_id
                        Default: False
                        Useful for quick audit without API calls

    --delIdIsNull       Delete local glossaries that do not have a glossary_id
                        Default: False
                        WARNING: Destructive operation! Requires confirmation.

    -h, --help          Show this help message and exit
"""
import requests
from django.core.management.base import BaseCommand
from django.conf import settings
from preferences import preferences
from glossaries.models import Glossary
from glossaries.helpers import get_glossary_username


class Command(BaseCommand):
    help = '''Check consistency between local glossaries database and remote API.

This command helps you:
  • Verify local glossaries exist on remote API (default mode)
  • Find glossaries without remote ID (--idNullOnly)
  • Delete orphan glossaries (--delIdIsNull)

Use --help for detailed information and examples.
'''

    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            default=False,
            help='[Default: False] Show detailed output for each glossary checked. By default, only problems are shown.',
        )
        parser.add_argument(
            '--idNullOnly',
            action='store_true',
            default=False,
            help='[Default: False] Skip API verification and only display glossaries without glossary_id. Useful for quick audit.',
        )
        parser.add_argument(
            '--delIdIsNull',
            action='store_true',
            default=False,
            help='[Default: False] Delete local glossaries that do not have a glossary_id. WARNING: Destructive! Requires confirmation.',
        )

    def handle(self, *args, **options):
        self.verbose = options['verbose']
        id_null_only = options['idNullOnly']
        del_id_is_null = options['delIdIsNull']

        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(self.style.SUCCESS('GLOSSARY CONSISTENCY CHECK'))
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write('')

        # Display configuration
        self.stdout.write(self.style.WARNING('Configuration:'))
        self.stdout.write(f'  GLOSSARY_SYSTEM: {settings.GLOSSARY_SYSTEM}')
        self.stdout.write(f'  GLOSSARY_API_KEY: {"*" * 10 if settings.GLOSSARY_API_KEY else "NOT SET"}')
        self.stdout.write(f'  Glossaries URL: {preferences.MainSettings.glossaries_url}')
        self.stdout.write(f'  Verbose mode: {"ON" if self.verbose else "OFF"}')
        self.stdout.write(f'  ID Null Only mode: {"ON" if id_null_only else "OFF"}')
        self.stdout.write(f'  Delete ID Null mode: {"ON" if del_id_is_null else "OFF"}')
        self.stdout.write('')

        # If delIdIsNull mode, delete glossaries without ID and exit
        if del_id_is_null:
            self._delete_glossaries_without_id()
            return

        # If idNullOnly mode, skip all checks and only show glossaries without ID
        if id_null_only:
            self._display_id_null_only()
            return

        if not settings.GLOSSARY_SYSTEM:
            self.stdout.write(self.style.ERROR('❌ GLOSSARY_SYSTEM is not configured!'))
            return

        if not settings.GLOSSARY_API_KEY:
            self.stdout.write(self.style.ERROR('❌ GLOSSARY_API_KEY is not configured!'))
            return

        # Default mode: check local glossaries against remote API
        self._check_local_to_remote()

    def _check_local_to_remote(self):
        """Check if local glossaries exist on remote API"""
        self.stdout.write(self.style.WARNING('Checking LOCAL glossaries against REMOTE API...'))
        self.stdout.write('')

        # Get all glossaries with glossary_id (already uploaded to API)
        glossaries = Glossary.objects.exclude(glossary_id__isnull=True).exclude(glossary_id='')
        total_count = glossaries.count()

        # Get glossaries without glossary_id
        glossaries_without_id = Glossary.objects.filter(glossary_id__isnull=True) | Glossary.objects.filter(glossary_id='')
        without_id_count = glossaries_without_id.count()

        self.stdout.write(f'Total glossaries in local database: {Glossary.objects.count()}')
        self.stdout.write(f'  - Glossaries with glossary_id (uploaded): {total_count}')
        self.stdout.write(f'  - Glossaries WITHOUT glossary_id: {without_id_count}')
        self.stdout.write('')

        if total_count == 0:
            self.stdout.write(self.style.WARNING('⚠️  No glossaries with glossary_id found in local database'))
            # Still show glossaries without ID
            self._display_glossaries_without_id(glossaries_without_id)
            return

        # Statistics
        stats = {
            'found': 0,
            'not_found': 0,
            'errors': 0
        }

        not_found_list = []
        error_list = []

        self.stdout.write('Checking each glossary on remote API...')
        if not self.verbose:
            self.stdout.write('(Use --verbose to see all glossaries checked)')
        self.stdout.write('')

        for i, glossary in enumerate(glossaries, 1):
            owner = glossary.user or glossary.group or 'Admin/Default'
            glossary_info = f'ID {glossary.id}: {glossary.name} ({glossary.source_language.abbreviation}->{glossary.target_language.abbreviation}, owner: {owner})'

            # Show progress every 10 glossaries (only in non-verbose mode)
            if not self.verbose and i % 10 == 0:
                self.stdout.write(f'Progress: {i}/{total_count}...')

            # Check if glossary exists on remote API
            exists, error = self._check_glossary_exists(glossary)

            if error:
                stats['errors'] += 1
                error_list.append({
                    'glossary': glossary_info,
                    'glossary_id': glossary.glossary_id,
                    'error': error
                })
                # Always show errors
                self.stdout.write(self.style.ERROR(f'  ✗ {glossary_info} - ERROR: {error}'))
            elif exists:
                stats['found'] += 1
                # Only show success if verbose mode
                if self.verbose:
                    self.stdout.write(self.style.SUCCESS(f'  ✓ {glossary_info} - glossary_id: {glossary.glossary_id}'))
            else:
                stats['not_found'] += 1
                not_found_list.append({
                    'glossary': glossary_info,
                    'glossary_id': glossary.glossary_id
                })
                # Always show not found
                self.stdout.write(self.style.ERROR(f'  ✗ {glossary_info} - NOT FOUND (glossary_id: {glossary.glossary_id})'))

        # Summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(self.style.SUCCESS('SUMMARY'))
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write('')
        self.stdout.write(f'Total checked: {total_count}')
        self.stdout.write(self.style.SUCCESS(f'  ✓ Found on remote: {stats["found"]}'))
        self.stdout.write(self.style.ERROR(f'  ✗ Not found on remote: {stats["not_found"]}'))
        self.stdout.write(self.style.ERROR(f'  ✗ Errors: {stats["errors"]}'))
        self.stdout.write('')

        if not_found_list:
            self.stdout.write(self.style.ERROR('Glossaries NOT FOUND on remote API:'))
            for item in not_found_list:
                self.stdout.write(f'  - {item["glossary"]} (glossary_id: {item["glossary_id"]})')
            self.stdout.write('')

        if error_list:
            self.stdout.write(self.style.ERROR('Glossaries with ERRORS:'))
            for item in error_list:
                self.stdout.write(f'  - {item["glossary"]} (glossary_id: {item["glossary_id"]})')
                self.stdout.write(f'    Error: {item["error"]}')
            self.stdout.write('')

        # Recommendations
        if stats['not_found'] > 0:
            self.stdout.write(self.style.WARNING('⚠️  RECOMMENDATIONS:'))
            self.stdout.write('  - Consider re-uploading missing glossaries')
            self.stdout.write('  - Or remove the glossary_id from local database if they should not exist remotely')
            self.stdout.write('')

        # Display glossaries without glossary_id
        self._display_glossaries_without_id(glossaries_without_id)

    def _check_glossary_exists(self, glossary):
        """
        Check if a glossary exists on remote API by trying to fetch it.
        Returns (exists: bool, error: str|None)
        """
        try:
            url = preferences.MainSettings.glossaries_url + 'get_glossary'
            payload = {
                "system": settings.GLOSSARY_SYSTEM,
                "username": get_glossary_username(glossary),
                "glossary_id": glossary.glossary_id,
            }
            headers = {
                "API-KEY": settings.GLOSSARY_API_KEY
            }

            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=10
            )

            if response.status_code == 200:
                return True, None
            elif response.status_code == 404:
                return False, None
            else:
                return False, f"HTTP {response.status_code}: {response.text[:100]}"

        except requests.exceptions.Timeout:
            return False, "Request timeout"
        except requests.exceptions.ConnectionError:
            return False, "Connection error"
        except Exception as e:
            return False, str(e)

    def _display_glossaries_without_id(self, glossaries_without_id):
        """Display detailed information about glossaries without glossary_id"""
        if glossaries_without_id.count() == 0:
            return

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(self.style.SUCCESS('GLOSSARIES WITHOUT glossary_id (NOT UPLOADED TO API)'))
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write('')
        self.stdout.write(f'Total: {glossaries_without_id.count()} glossaries')
        self.stdout.write('')

        # Group by type
        admin_glossaries = glossaries_without_id.filter(user__isnull=True, group__isnull=True)
        user_glossaries = glossaries_without_id.filter(user__isnull=False)
        group_glossaries = glossaries_without_id.filter(group__isnull=False)

        if admin_glossaries.exists():
            self.stdout.write(self.style.WARNING(f'Admin/Default glossaries: {admin_glossaries.count()}'))
            for glossary in admin_glossaries:
                domain = glossary.domain.name if glossary.domain else 'No domain'
                self.stdout.write(f'  - Local ID {glossary.id}: {glossary.name} ({glossary.source_language.abbreviation}->{glossary.target_language.abbreviation}, domain: {domain}) [NO REMOTE ID]')
            self.stdout.write('')

        if user_glossaries.exists():
            self.stdout.write(self.style.WARNING(f'User glossaries: {user_glossaries.count()}'))
            for glossary in user_glossaries:
                domain = glossary.domain.name if glossary.domain else 'No domain'
                user = glossary.user.username if glossary.user else 'Unknown'
                self.stdout.write(f'  - Local ID {glossary.id}: {glossary.name} ({glossary.source_language.abbreviation}->{glossary.target_language.abbreviation}, user: {user}, domain: {domain}) [NO REMOTE ID]')
            self.stdout.write('')

        if group_glossaries.exists():
            self.stdout.write(self.style.WARNING(f'Group glossaries: {group_glossaries.count()}'))
            for glossary in group_glossaries:
                domain = glossary.domain.name if glossary.domain else 'No domain'
                group = glossary.group.name if glossary.group else 'Unknown'
                self.stdout.write(f'  - Local ID {glossary.id}: {glossary.name} ({glossary.source_language.abbreviation}->{glossary.target_language.abbreviation}, group: {group}, domain: {domain}) [NO REMOTE ID]')
            self.stdout.write('')

        self.stdout.write(self.style.WARNING('⚠️  These glossaries have not been uploaded to the remote API yet.'))
        self.stdout.write('')

    def _display_id_null_only(self):
        """Display only glossaries without glossary_id (idNullOnly mode)"""
        self.stdout.write(self.style.WARNING('ID NULL ONLY MODE - Displaying only glossaries without glossary_id'))
        self.stdout.write('')

        # Get glossaries without glossary_id
        glossaries_without_id = Glossary.objects.filter(glossary_id__isnull=True) | Glossary.objects.filter(glossary_id='')
        without_id_count = glossaries_without_id.count()

        self.stdout.write(f'Total glossaries in local database: {Glossary.objects.count()}')
        self.stdout.write(f'  - Glossaries with glossary_id (uploaded): {Glossary.objects.exclude(glossary_id__isnull=True).exclude(glossary_id="").count()}')
        self.stdout.write(f'  - Glossaries WITHOUT glossary_id: {without_id_count}')
        self.stdout.write('')

        if without_id_count == 0:
            self.stdout.write(self.style.SUCCESS('✅ All glossaries have been uploaded to the API!'))
            self.stdout.write('   No glossaries without glossary_id found.')
            return

        # Display detailed list
        self._display_glossaries_without_id(glossaries_without_id)

    def _delete_glossaries_without_id(self):
        """Delete glossaries without glossary_id (delIdIsNull mode)"""
        self.stdout.write(self.style.ERROR('=' * 80))
        self.stdout.write(self.style.ERROR('⚠️  DELETE MODE - REMOVING GLOSSARIES WITHOUT glossary_id'))
        self.stdout.write(self.style.ERROR('=' * 80))
        self.stdout.write('')

        # Get glossaries without glossary_id
        glossaries_without_id = Glossary.objects.filter(glossary_id__isnull=True) | Glossary.objects.filter(glossary_id='')
        without_id_count = glossaries_without_id.count()

        self.stdout.write(f'Total glossaries in local database: {Glossary.objects.count()}')
        self.stdout.write(f'  - Glossaries with glossary_id (uploaded): {Glossary.objects.exclude(glossary_id__isnull=True).exclude(glossary_id="").count()}')
        self.stdout.write(f'  - Glossaries WITHOUT glossary_id (TO DELETE): {without_id_count}')
        self.stdout.write('')

        if without_id_count == 0:
            self.stdout.write(self.style.SUCCESS('✅ No glossaries to delete!'))
            self.stdout.write('   All glossaries have a glossary_id.')
            return

        # Group by type for display
        admin_glossaries = glossaries_without_id.filter(user__isnull=True, group__isnull=True)
        user_glossaries = glossaries_without_id.filter(user__isnull=False)
        group_glossaries = glossaries_without_id.filter(group__isnull=False)

        # Display what will be deleted
        self.stdout.write(self.style.WARNING(f'Glossaries that will be DELETED:'))
        self.stdout.write('')

        if admin_glossaries.exists():
            self.stdout.write(self.style.WARNING(f'Admin/Default glossaries: {admin_glossaries.count()}'))
            for glossary in admin_glossaries:
                domain = glossary.domain.name if glossary.domain else 'No domain'
                self.stdout.write(f'  - Local ID {glossary.id}: {glossary.name} ({glossary.source_language.abbreviation}->{glossary.target_language.abbreviation}, domain: {domain})')
            self.stdout.write('')

        if user_glossaries.exists():
            self.stdout.write(self.style.WARNING(f'User glossaries: {user_glossaries.count()}'))
            for glossary in user_glossaries:
                domain = glossary.domain.name if glossary.domain else 'No domain'
                user = glossary.user.username if glossary.user else 'Unknown'
                self.stdout.write(f'  - Local ID {glossary.id}: {glossary.name} ({glossary.source_language.abbreviation}->{glossary.target_language.abbreviation}, user: {user}, domain: {domain})')
            self.stdout.write('')

        if group_glossaries.exists():
            self.stdout.write(self.style.WARNING(f'Group glossaries: {group_glossaries.count()}'))
            for glossary in group_glossaries:
                domain = glossary.domain.name if glossary.domain else 'No domain'
                group = glossary.group.name if glossary.group else 'Unknown'
                self.stdout.write(f'  - Local ID {glossary.id}: {glossary.name} ({glossary.source_language.abbreviation}->{glossary.target_language.abbreviation}, group: {group}, domain: {domain})')
            self.stdout.write('')

        # Confirmation prompt
        self.stdout.write(self.style.ERROR('⚠️  WARNING: This action cannot be undone!'))
        self.stdout.write('')

        # Ask for confirmation
        confirm = input(f'Are you sure you want to DELETE {without_id_count} glossaries? Type "yes" to confirm: ')

        if confirm.lower() != 'yes':
            self.stdout.write(self.style.WARNING('❌ Deletion cancelled by user.'))
            return

        # Proceed with deletion
        self.stdout.write('')
        self.stdout.write(self.style.ERROR(f'Deleting {without_id_count} glossaries...'))
        self.stdout.write('')

        deleted_count = 0
        error_count = 0

        for glossary in glossaries_without_id:
            try:
                glossary_info = f'Local ID {glossary.id}: {glossary.name}'
                glossary.delete()
                deleted_count += 1
                self.stdout.write(self.style.SUCCESS(f'  ✓ Deleted: {glossary_info}'))
            except Exception as e:
                error_count += 1
                self.stdout.write(self.style.ERROR(f'  ✗ Failed to delete {glossary_info}: {str(e)}'))

        # Summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(self.style.SUCCESS('DELETION SUMMARY'))
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write('')
        self.stdout.write(f'Total to delete: {without_id_count}')
        self.stdout.write(self.style.SUCCESS(f'  ✓ Successfully deleted: {deleted_count}'))
        if error_count > 0:
            self.stdout.write(self.style.ERROR(f'  ✗ Failed to delete: {error_count}'))
        self.stdout.write('')

        if deleted_count == without_id_count:
            self.stdout.write(self.style.SUCCESS('✅ All glossaries without glossary_id have been deleted!'))
        elif deleted_count > 0:
            self.stdout.write(self.style.WARNING(f'⚠️  {deleted_count} glossaries deleted, but {error_count} failed.'))
        else:
            self.stdout.write(self.style.ERROR('❌ No glossaries were deleted.'))
