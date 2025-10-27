import requests
from django.core.management.base import BaseCommand
from django.conf import settings
from preferences import preferences
from glossaries.models import Glossary


class Command(BaseCommand):
    help = 'Test the remote API endpoint to get glossary metadata (without entries)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--glossary-id',
            type=str,
            help='Specific glossary_id to test (if not provided, will pick one randomly from database)'
        )
        parser.add_argument(
            '--username',
            type=str,
            help='Username for the API call (optional - filled from API-KEY if not provided)'
        )
        parser.add_argument(
            '--system',
            type=str,
            help='System name (optional - filled from API-KEY if not provided)'
        )
        parser.add_argument(
            '--no-optional-params',
            action='store_true',
            help='Do not send optional system/username parameters'
        )

    def handle(self, *args, **options):
        glossary_id = options.get('glossary_id')
        username = options.get('username')
        system = options.get('system')
        no_optional = options.get('no_optional_params', False)

        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(self.style.SUCCESS('TEST API GET_GLOSSARY METADATA'))
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write('')

        # If no glossary_id provided, pick one from database
        if not glossary_id:
            self.stdout.write('🔍 No glossary_id provided, picking one from database...')
            glossary = Glossary.objects.exclude(glossary_id__isnull=True).exclude(glossary_id='').first()

            if glossary:
                glossary_id = glossary.glossary_id
                self.stdout.write(f'   Found glossary: {glossary.name}')
                self.stdout.write(f'   Local ID: {glossary.id}')
                self.stdout.write(f'   Remote glossary_id: {glossary_id}')
                self.stdout.write('')
            else:
                self.stdout.write(self.style.ERROR('❌ No glossaries with glossary_id found in database'))
                self.stdout.write('   Please provide a glossary_id with --glossary-id option')
                return

        # Display configuration
        api_url = preferences.MainSettings.glossaries_url
        self.stdout.write('📋 Configuration:')
        self.stdout.write(f'  API URL: {api_url}')
        if not no_optional:
            self.stdout.write(f'  GLOSSARY_SYSTEM: {system or settings.GLOSSARY_SYSTEM}')
            self.stdout.write(f'  Username: {username or "(from API-KEY)"}')
        else:
            self.stdout.write(f'  Mode: Without optional params (system/username)')
        self.stdout.write(f'  Glossary ID: {glossary_id}')
        self.stdout.write(f'  API Key configured: {bool(settings.GLOSSARY_API_KEY)}')
        self.stdout.write('')

        # Call the endpoint
        url = api_url + 'get_glossary_info'

        # Build payload - only glossary_id is required
        payload = {
            "glossary_id": glossary_id,
        }

        # Add optional params (unless --no-optional-params is used)
        if not no_optional:
            # Use provided values or defaults
            payload["system"] = system if system else settings.GLOSSARY_SYSTEM
            payload["username"] = username if username else "admin"

        headers = {
            "API-KEY": settings.GLOSSARY_API_KEY
        }

        self.stdout.write(f'🔄 Calling API endpoint: {url}')
        self.stdout.write(f'   Method: POST')
        self.stdout.write(f'   Payload: {payload}')
        self.stdout.write('')

        try:
            import time
            start_time = time.time()

            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=30
            )

            duration = time.time() - start_time

            self.stdout.write(f'⏱️  Response time: {duration:.3f}s')
            self.stdout.write(f'📊 HTTP Status: {response.status_code}')
            self.stdout.write('')

            if response.status_code == 200:
                self.stdout.write(self.style.SUCCESS('✅ SUCCESS - API returned 200 OK'))
                self.stdout.write('')

                try:
                    data = response.json()

                    # Display metadata
                    self.stdout.write(self.style.SUCCESS('📦 Glossary Metadata:'))
                    self.stdout.write('-' * 80)

                    # Common metadata fields
                    metadata_fields = [
                        ('id', 'ID'),
                        ('name', 'Name'),
                        ('description', 'Description'),
                        ('languages', 'Languages'),
                        ('created_at', 'Created At'),
                        ('updated_at', 'Updated At'),
                        ('entry_count', 'Entry Count'),
                        ('entries', 'Entries'),
                    ]

                    for field_key, field_label in metadata_fields:
                        if field_key in data:
                            value = data[field_key]
                            if field_key == 'entries' and isinstance(value, list):
                                self.stdout.write(f'  {field_label}: {len(value)} entries')
                            elif field_key == 'languages' and isinstance(value, list):
                                self.stdout.write(f'  {field_label}: {" → ".join(value)}')
                            else:
                                self.stdout.write(f'  {field_label}: {value}')

                    # Show all other fields
                    self.stdout.write('')
                    self.stdout.write('All fields in response:')
                    for key, value in data.items():
                        if key not in [f[0] for f in metadata_fields]:
                            if isinstance(value, (list, dict)):
                                self.stdout.write(f'  {key}: {type(value).__name__} (length: {len(value)})')
                            else:
                                self.stdout.write(f'  {key}: {value}')

                    self.stdout.write('-' * 80)

                    # Full JSON response
                    self.stdout.write('')
                    self.stdout.write('📄 Full JSON Response:')
                    import json
                    formatted_json = json.dumps(data, indent=2, ensure_ascii=False)

                    # If entries list is long, truncate it
                    if 'entries' in data and isinstance(data['entries'], list) and len(data['entries']) > 5:
                        data_copy = data.copy()
                        data_copy['entries'] = data['entries'][:5] + ['... (truncated)']
                        formatted_json = json.dumps(data_copy, indent=2, ensure_ascii=False)
                        self.stdout.write('(Note: Entries list truncated to first 5 for display)')

                    self.stdout.write(formatted_json)

                except ValueError as e:
                    self.stdout.write(self.style.ERROR(f'❌ Failed to parse JSON response: {e}'))
                    self.stdout.write('')
                    self.stdout.write('Raw response (first 1000 chars):')
                    self.stdout.write(response.text[:1000])

            elif response.status_code == 404:
                self.stdout.write(self.style.ERROR('❌ 404 NOT FOUND - Glossary not found'))
                self.stdout.write('')
                self.stdout.write('Possible reasons:')
                self.stdout.write(f'  - Glossary ID {glossary_id} does not exist on remote API')
                self.stdout.write(f'  - System "{settings.GLOSSARY_SYSTEM}" is incorrect')
                self.stdout.write(f'  - Username "{username}" does not have access to this glossary')
                self.stdout.write('')
                self.stdout.write('Response body:')
                self.stdout.write(response.text)

            elif response.status_code == 401 or response.status_code == 403:
                self.stdout.write(self.style.ERROR(f'❌ {response.status_code} UNAUTHORIZED/FORBIDDEN'))
                self.stdout.write('')
                self.stdout.write('Authentication issue:')
                self.stdout.write('  - Check API-KEY is correct')
                self.stdout.write('  - Check user permissions')
                self.stdout.write('')
                self.stdout.write('Response body:')
                self.stdout.write(response.text)

            else:
                self.stdout.write(self.style.ERROR(f'❌ HTTP {response.status_code}'))
                self.stdout.write('')
                self.stdout.write('Response body:')
                self.stdout.write(response.text[:1000])

        except requests.exceptions.Timeout:
            self.stdout.write(self.style.ERROR('❌ REQUEST TIMEOUT (30s)'))
            self.stdout.write('')
            self.stdout.write('The API did not respond within 30 seconds.')

        except requests.exceptions.ConnectionError as e:
            self.stdout.write(self.style.ERROR(f'❌ CONNECTION ERROR'))
            self.stdout.write('')
            self.stdout.write(f'Error: {str(e)}')
            self.stdout.write('Check network connectivity and API URL.')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ UNEXPECTED ERROR: {str(e)}'))
            import traceback
            self.stdout.write('')
            self.stdout.write('Traceback:')
            self.stdout.write(traceback.format_exc())
