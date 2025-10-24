"""
Django management command to cleanup orphan glossary files.

Usage:
    python manage.py cleanup_glossary_files --dry-run  # Just analyze, don't delete
    python manage.py cleanup_glossary_files            # Analyze and cleanup
"""
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from glossaries.models import Glossary


class Command(BaseCommand):
    help = 'Cleanup orphan glossary files and analyze file usage'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Only analyze, do not delete anything',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(self.style.SUCCESS('GLOSSARY FILES CLEANUP ANALYSIS'))
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write('')

        # 1. Analyze glossaries with files in DB
        self.stdout.write(self.style.WARNING('1. Analyzing glossaries in database...'))
        self.stdout.write('')

        glossaries_with_files = Glossary.objects.exclude(file='').exclude(file__isnull=True)
        glossaries_without_files = Glossary.objects.filter(file='') | Glossary.objects.filter(file__isnull=True)

        self.stdout.write(f'Total glossaries: {Glossary.objects.count()}')
        self.stdout.write(f'  - With files: {glossaries_with_files.count()}')
        self.stdout.write(f'  - Without files (normal): {glossaries_without_files.count()}')
        self.stdout.write('')

        # Show breakdown by type
        admin_with_files = glossaries_with_files.filter(user__isnull=True, group__isnull=True).count()
        user_with_files = glossaries_with_files.filter(user__isnull=False).count()
        group_with_files = glossaries_with_files.filter(group__isnull=False).count()

        self.stdout.write('Glossaries WITH files (should be 0 normally):')
        self.stdout.write(f'  - Admin/Default glossaries: {admin_with_files}')
        self.stdout.write(f'  - User glossaries: {user_with_files}')
        self.stdout.write(f'  - Group glossaries: {group_with_files}')
        self.stdout.write('')

        if glossaries_with_files.exists():
            self.stdout.write(self.style.WARNING('⚠️  WARNING: Some glossaries still have files attached!'))
            self.stdout.write('These files should have been deleted after API upload.')
            self.stdout.write('')

            for glossary in glossaries_with_files[:10]:  # Show first 10
                owner = glossary.user or glossary.group or 'Admin/Default'
                self.stdout.write(f'  - ID {glossary.id}: {glossary.name} (owner: {owner}, file: {glossary.file.name})')

            if glossaries_with_files.count() > 10:
                self.stdout.write(f'  ... and {glossaries_with_files.count() - 10} more')
            self.stdout.write('')

        # 2. Analyze physical files
        self.stdout.write(self.style.WARNING('2. Analyzing physical files in media/glossaries/...'))
        self.stdout.write('')

        glossaries_dir = os.path.join(settings.MEDIA_ROOT, 'glossaries')

        if not os.path.exists(glossaries_dir):
            self.stdout.write(self.style.ERROR(f'Directory does not exist: {glossaries_dir}'))
            return

        # Get all files in directory
        physical_files = []
        for root, dirs, files in os.walk(glossaries_dir):
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, settings.MEDIA_ROOT)
                physical_files.append({
                    'path': file_path,
                    'relative': relative_path,
                    'name': file,
                    'size': os.path.getsize(file_path)
                })

        self.stdout.write(f'Physical files found: {len(physical_files)}')

        if len(physical_files) == 0:
            self.stdout.write(self.style.SUCCESS('✅ No physical files - directory is clean!'))
            return

        # Calculate total size
        total_size = sum(f['size'] for f in physical_files)
        total_size_mb = total_size / (1024 * 1024)

        self.stdout.write(f'Total size: {total_size_mb:.2f} MB')
        self.stdout.write('')

        # 3. Find orphan files (files not referenced in DB)
        self.stdout.write(self.style.WARNING('3. Finding orphan files...'))
        self.stdout.write('')

        orphan_files = []
        referenced_files = []

        for physical_file in physical_files:
            # Check if file is referenced in DB
            is_referenced = Glossary.objects.filter(file=physical_file['relative']).exists()

            if is_referenced:
                referenced_files.append(physical_file)
            else:
                orphan_files.append(physical_file)

        self.stdout.write(f'Orphan files (not in DB): {len(orphan_files)}')
        self.stdout.write(f'Referenced files (in DB): {len(referenced_files)}')
        self.stdout.write('')

        if orphan_files:
            orphan_size = sum(f['size'] for f in orphan_files)
            orphan_size_mb = orphan_size / (1024 * 1024)

            self.stdout.write(self.style.ERROR(f'⚠️  {len(orphan_files)} orphan files found ({orphan_size_mb:.2f} MB)'))
            self.stdout.write('These files can be safely deleted:')
            self.stdout.write('')

            for orphan in orphan_files[:20]:  # Show first 20
                size_kb = orphan['size'] / 1024
                self.stdout.write(f'  - {orphan["name"]} ({size_kb:.1f} KB)')

            if len(orphan_files) > 20:
                self.stdout.write(f'  ... and {len(orphan_files) - 20} more')
            self.stdout.write('')

            # Cleanup action
            if dry_run:
                self.stdout.write(self.style.WARNING('🔍 DRY RUN MODE - No files will be deleted'))
                self.stdout.write(f'Run without --dry-run to delete {len(orphan_files)} orphan files')
            else:
                self.stdout.write(self.style.WARNING(f'🗑️  Deleting {len(orphan_files)} orphan files...'))
                deleted_count = 0
                deleted_size = 0

                for orphan in orphan_files:
                    try:
                        os.remove(orphan['path'])
                        deleted_count += 1
                        deleted_size += orphan['size']
                        self.stdout.write(f'  ✓ Deleted: {orphan["name"]}')
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'  ✗ Error deleting {orphan["name"]}: {str(e)}'))

                deleted_size_mb = deleted_size / (1024 * 1024)
                self.stdout.write('')
                self.stdout.write(self.style.SUCCESS(f'✅ Deleted {deleted_count} files ({deleted_size_mb:.2f} MB freed)'))
        else:
            self.stdout.write(self.style.SUCCESS('✅ No orphan files found!'))

        # 4. Recommendations
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(self.style.SUCCESS('RECOMMENDATIONS'))
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write('')

        if glossaries_with_files.exists():
            self.stdout.write(self.style.WARNING('⚠️  Some glossaries still have file references:'))
            self.stdout.write('   This might indicate that the API upload failed or was interrupted.')
            self.stdout.write('   Consider investigating these glossaries.')
            self.stdout.write('')

        if referenced_files:
            self.stdout.write(self.style.WARNING(f'⚠️  {len(referenced_files)} files are still referenced in DB:'))
            self.stdout.write('   These files should normally be deleted after API upload.')
            self.stdout.write('   If API uploads are working correctly, these should disappear soon.')
            self.stdout.write('')

        if not orphan_files and not glossaries_with_files.exists():
            self.stdout.write(self.style.SUCCESS('✅ Everything looks clean!'))
            self.stdout.write('   - No orphan files')
            self.stdout.write('   - No glossaries with file references')
            self.stdout.write('   - System is working as expected')

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(self.style.SUCCESS('END OF ANALYSIS'))
        self.stdout.write(self.style.SUCCESS('=' * 80))
