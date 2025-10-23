import csv
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from glossaries.models import Glossary
from languages.models import Language
from domains.models import Domain


class Command(BaseCommand):
    help = '''Compare local glossaries database with a CSV file.

    CSV format: file,source_language,target_language,domain[,user,group]
    '''

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to CSV file to compare')
        parser.add_argument('--verbose', action='store_true', default=False,
                            help='Show all glossaries, not just differences')

    def handle(self, *args, **options):
        csv_file = options['csv_file']
        self.verbose = options['verbose']

        if not os.path.exists(csv_file):
            self.stdout.write(self.style.ERROR(f'❌ CSV file not found: {csv_file}'))
            return

        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(self.style.SUCCESS('COMPARAISON BASE LOCALE <-> CSV'))
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write('')

        # Parse CSV file
        csv_glossaries = self._parse_csv(csv_file)
        if csv_glossaries is None:
            return

        # Get local glossaries
        local_glossaries = self._get_local_glossaries()

        # Compare
        self._compare_glossaries(local_glossaries, csv_glossaries)

    def _parse_csv(self, csv_file):
        """Parse CSV file and return list of glossary definitions"""
        self.stdout.write('📄 Lecture du fichier CSV...')

        glossaries = []
        try:
            with open(csv_file, 'r', encoding='utf-8-sig') as csvfile:
                reader = csv.DictReader(csvfile)

                # Verify CSV structure
                expected_columns = {'file', 'source_language', 'target_language', 'domain'}
                actual_columns = set(reader.fieldnames) if reader.fieldnames else set()

                if not expected_columns.issubset(actual_columns):
                    self.stdout.write(self.style.ERROR(
                        f'❌ Invalid CSV structure. Expected columns: {expected_columns}, Found: {actual_columns}'
                    ))
                    return None

                for row_num, row in enumerate(reader, start=2):
                    # Extract filename without extension
                    filename = row['file']
                    name = os.path.splitext(os.path.basename(filename))[0]

                    glossaries.append({
                        'name': name,
                        'file': filename,
                        'source': row['source_language'].upper(),
                        'target': row['target_language'].upper(),
                        'domain': row['domain'],
                        'user': row.get('user', ''),
                        'group': row.get('group', ''),
                        'row': row_num
                    })

            self.stdout.write(self.style.SUCCESS(f'✓ CSV lu avec succès: {len(glossaries)} glossaires trouvés'))
            self.stdout.write('')
            return glossaries

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error reading CSV: {str(e)}'))
            return None

    def _get_local_glossaries(self):
        """Get all glossaries from local database"""
        self.stdout.write('💾 Récupération des glossaires de la base locale...')

        glossaries = []
        for glossary in Glossary.objects.all():
            # Extract name from file
            if glossary.file:
                name = os.path.splitext(os.path.basename(glossary.file.name))[0]
            else:
                name = glossary.name

            owner_type = 'admin'
            owner_value = ''
            if glossary.user:
                owner_type = 'user'
                owner_value = glossary.user.username
            elif glossary.group:
                owner_type = 'group'
                owner_value = glossary.group.name

            glossaries.append({
                'id': glossary.id,
                'name': name,
                'source': glossary.source_language.abbreviation.upper(),
                'target': glossary.target_language.abbreviation.upper(),
                'domain': glossary.domain.name if glossary.domain else '',
                'owner_type': owner_type,
                'owner_value': owner_value,
                'glossary_id': glossary.glossary_id or ''
            })

        self.stdout.write(self.style.SUCCESS(f'✓ Base locale lue: {len(glossaries)} glossaires trouvés'))
        self.stdout.write('')
        return glossaries

    def _compare_glossaries(self, local_glossaries, csv_glossaries):
        """Compare local and CSV glossaries"""
        self.stdout.write(self.style.WARNING('🔍 Comparaison en cours...'))
        self.stdout.write('')

        # Create lookup dictionaries
        # Key: (source, target, domain, owner)
        # NOTE: Filename is NOT part of the key because batch upload identifies
        # existing glossaries by lang+domain+owner, not by filename
        def make_key(g, from_csv=False):
            if from_csv:
                owner = g['user'] if g['user'] else (g['group'] if g['group'] else '')
                return (g['source'], g['target'], g['domain'], owner)
            else:
                return (g['source'], g['target'], g['domain'], g['owner_value'])

        local_dict = {make_key(g): g for g in local_glossaries}
        csv_dict = {make_key(g, True): g for g in csv_glossaries}

        # Find differences
        only_in_local = []
        only_in_csv = []
        in_both = []

        for key in local_dict:
            if key in csv_dict:
                in_both.append((local_dict[key], csv_dict[key]))
            else:
                only_in_local.append(local_dict[key])

        for key in csv_dict:
            if key not in local_dict:
                only_in_csv.append(csv_dict[key])

        # Display statistics
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(self.style.SUCCESS('STATISTIQUES'))
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write('')
        self.stdout.write(f'Total dans la base locale: {len(local_glossaries)}')
        self.stdout.write(f'Total dans le CSV: {len(csv_glossaries)}')
        self.stdout.write(f'Présents dans les deux: {len(in_both)}')
        self.stdout.write(self.style.WARNING(f'Uniquement dans la base locale: {len(only_in_local)}'))
        self.stdout.write(self.style.WARNING(f'Uniquement dans le CSV: {len(only_in_csv)}'))
        self.stdout.write('')

        # Display glossaries in both (if verbose)
        if self.verbose and in_both:
            self.stdout.write(self.style.SUCCESS('=' * 80))
            self.stdout.write(self.style.SUCCESS(f'✓ PRÉSENTS DANS LES DEUX ({len(in_both)})'))
            self.stdout.write(self.style.SUCCESS('=' * 80))
            self.stdout.write('')
            for local_g, csv_g in in_both:
                owner = f"User: {local_g['owner_value']}" if local_g['owner_type'] == 'user' else \
                        f"Group: {local_g['owner_value']}" if local_g['owner_type'] == 'group' else \
                        "Admin/Default"
                self.stdout.write(
                    f"  ✓ Local ID {local_g['id']}: {local_g['name']} "
                    f"({local_g['source']}->{local_g['target']}, "
                    f"domain: {local_g['domain']}, owner: {owner})"
                )
                self.stdout.write(f"      CSV row {csv_g['row']}: {csv_g['file']}")
                if local_g['glossary_id']:
                    self.stdout.write(f"      Remote ID: {local_g['glossary_id']}")
                self.stdout.write('')

        # Display glossaries only in local
        if only_in_local:
            self.stdout.write(self.style.WARNING('=' * 80))
            self.stdout.write(self.style.WARNING(f'⚠️  UNIQUEMENT DANS LA BASE LOCALE ({len(only_in_local)})'))
            self.stdout.write(self.style.WARNING('=' * 80))
            self.stdout.write('')
            self.stdout.write('Ces glossaires existent localement mais ne sont pas dans le CSV:')
            self.stdout.write('')
            for g in only_in_local:
                owner = f"User: {g['owner_value']}" if g['owner_type'] == 'user' else \
                        f"Group: {g['owner_value']}" if g['owner_type'] == 'group' else \
                        "Admin/Default"
                self.stdout.write(
                    f"  Local ID {g['id']}: {g['name']} "
                    f"({g['source']}->{g['target']}, "
                    f"domain: {g['domain']}, owner: {owner})"
                )
                if g['glossary_id']:
                    self.stdout.write(f"    Remote ID: {g['glossary_id']}")
            self.stdout.write('')

        # Display glossaries only in CSV
        if only_in_csv:
            self.stdout.write(self.style.WARNING('=' * 80))
            self.stdout.write(self.style.WARNING(f'⚠️  UNIQUEMENT DANS LE CSV ({len(only_in_csv)})'))
            self.stdout.write(self.style.WARNING('=' * 80))
            self.stdout.write('')
            self.stdout.write('Ces glossaires sont dans le CSV mais n\'existent pas localement:')
            self.stdout.write('')
            for g in only_in_csv:
                owner = f"User: {g['user']}" if g['user'] else \
                        f"Group: {g['group']}" if g['group'] else \
                        "Admin/Default"
                self.stdout.write(
                    f"  CSV row {g['row']}: {g['file']} "
                    f"({g['source']}->{g['target']}, "
                    f"domain: {g['domain']}, owner: {owner})"
                )
            self.stdout.write('')

        # Recommendations
        if only_in_local or only_in_csv:
            self.stdout.write(self.style.WARNING('💡 RECOMMANDATIONS:'))
            if only_in_local:
                self.stdout.write('  - Glossaires uniquement dans la base locale:')
                self.stdout.write('    → Ajoutez-les au CSV si vous voulez les inclure dans votre référence')
                self.stdout.write('    → Ou supprimez-les de la base si ils ne sont plus nécessaires')
            if only_in_csv:
                self.stdout.write('  - Glossaires uniquement dans le CSV:')
                self.stdout.write('    → Chargez-les via le batch upload pour les ajouter à la base locale')
            self.stdout.write('')
