import requests
from django.core.management.base import BaseCommand
from django.conf import settings
from preferences import preferences


class Command(BaseCommand):
    help = 'Test the remote API endpoint to list all glossaries'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            default='admin',
            help='Username to filter glossaries (default: admin)'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            default=False,
            help='Show detailed information for each glossary'
        )

    def handle(self, *args, **options):
        username = options['username']
        verbose = options['verbose']

        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(self.style.SUCCESS('TEST API GET_GLOSSARY_LIST'))
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write('')

        # Display configuration
        api_url = preferences.MainSettings.glossaries_url
        self.stdout.write('📋 Configuration:')
        self.stdout.write(f'  API URL: {api_url}')
        self.stdout.write(f'  GLOSSARY_SYSTEM: {settings.GLOSSARY_SYSTEM}')
        self.stdout.write(f'  Username: {username}')
        self.stdout.write(f'  API Key configured: {bool(settings.GLOSSARY_API_KEY)}')
        self.stdout.write('')

        # Try the endpoint
        url = api_url + 'get_glossary_list'

        params = {
            "system": settings.GLOSSARY_SYSTEM,
            "username": username,
        }

        headers = {
            "API-KEY": settings.GLOSSARY_API_KEY
        }

        self.stdout.write(f'🔄 Calling API endpoint: {url}')
        self.stdout.write(f'   Method: GET')
        self.stdout.write(f'   Query params: {params}')
        self.stdout.write('')

        try:
            import time

            # Try different methods
            methods_to_try = [
                ('GET with params', 'get', {'params': params}),
                ('GET with json body', 'get', {'json': params}),
                ('GET without params', 'get', {}),
            ]

            for method_desc, method, kwargs in methods_to_try:
                self.stdout.write(f'🔄 Trying: {method_desc}')
                start_time = time.time()

                if method == 'get':
                    response = requests.get(url, headers=headers, timeout=30, **kwargs)
                else:
                    response = requests.post(url, headers=headers, timeout=30, **kwargs)

                duration = time.time() - start_time

                self.stdout.write(f'   Response time: {duration:.3f}s')
                self.stdout.write(f'   HTTP Status: {response.status_code}')

                if response.status_code == 200:
                    self.stdout.write(self.style.SUCCESS(f'   ✅ SUCCESS with {method_desc}!'))
                    self.stdout.write('')
                    break
                elif response.status_code != 403 and response.status_code != 405:
                    # Different error, might be progress
                    self.stdout.write(f'   Response: {response.text[:200]}')
                    self.stdout.write('')
                else:
                    self.stdout.write(f'   ❌ Failed')
                    self.stdout.write('')

            duration = time.time() - start_time

            self.stdout.write(f'⏱️  Final Response time: {duration:.3f}s')
            self.stdout.write(f'📊 Final HTTP Status: {response.status_code}')
            self.stdout.write('')

            if response.status_code == 200:
                self.stdout.write(self.style.SUCCESS('✅ SUCCESS - API returned 200 OK'))
                self.stdout.write('')

                try:
                    data = response.json()

                    # Try to determine the response structure
                    self.stdout.write('📦 Response structure:')
                    if isinstance(data, dict):
                        self.stdout.write(f'  Type: Dictionary with {len(data)} keys')
                        self.stdout.write(f'  Keys: {list(data.keys())}')

                        # Common patterns for list responses
                        if 'glossaries' in data:
                            glossaries = data['glossaries']
                            self.stdout.write('')
                            self.stdout.write(self.style.SUCCESS(f'✅ Found {len(glossaries)} glossaries'))
                            self._display_glossaries(glossaries, verbose)
                        elif 'items' in data:
                            items = data['items']
                            self.stdout.write('')
                            self.stdout.write(self.style.SUCCESS(f'✅ Found {len(items)} items'))
                            self._display_glossaries(items, verbose)
                        elif 'data' in data:
                            items = data['data']
                            self.stdout.write('')
                            self.stdout.write(self.style.SUCCESS(f'✅ Found {len(items)} items'))
                            self._display_glossaries(items, verbose)
                        else:
                            self.stdout.write('')
                            self.stdout.write('Full response:')
                            import json
                            self.stdout.write(json.dumps(data, indent=2))

                    elif isinstance(data, list):
                        self.stdout.write(f'  Type: List with {len(data)} items')
                        self.stdout.write('')
                        self.stdout.write(self.style.SUCCESS(f'✅ Found {len(data)} glossaries'))
                        self._display_glossaries(data, verbose)
                    else:
                        self.stdout.write(f'  Type: {type(data)}')
                        self.stdout.write(f'  Value: {data}')

                except ValueError as e:
                    self.stdout.write(self.style.ERROR(f'❌ Failed to parse JSON response: {e}'))
                    self.stdout.write('')
                    self.stdout.write('Raw response (first 1000 chars):')
                    self.stdout.write(response.text[:1000])

            elif response.status_code == 404:
                self.stdout.write(self.style.ERROR('❌ 404 NOT FOUND - Endpoint does not exist'))
                self.stdout.write('')
                self.stdout.write('Possible reasons:')
                self.stdout.write('  - The endpoint path is incorrect')
                self.stdout.write('  - The API version has changed')
                self.stdout.write('  - The endpoint is not available for this system')

            elif response.status_code == 401 or response.status_code == 403:
                self.stdout.write(self.style.ERROR(f'❌ {response.status_code} UNAUTHORIZED/FORBIDDEN'))
                self.stdout.write('')
                self.stdout.write('Authentication issue:')
                self.stdout.write('  - Check API-KEY is correct')
                self.stdout.write('  - Check user permissions')

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

    def _display_glossaries(self, glossaries, verbose):
        """Display glossary list"""
        if not glossaries:
            self.stdout.write('  (No glossaries found)')
            return

        self.stdout.write('')
        self.stdout.write('Glossaries:')
        self.stdout.write('-' * 80)

        for i, glossary in enumerate(glossaries, 1):
            if isinstance(glossary, dict):
                # Try common field names
                glossary_id = glossary.get('glossary_id') or glossary.get('id') or glossary.get('_id') or 'N/A'
                name = glossary.get('name') or glossary.get('glossary_name') or 'N/A'

                self.stdout.write(f'{i}. ID: {glossary_id} | Name: {name}')

                if verbose:
                    # Show all fields
                    for key, value in glossary.items():
                        if key not in ['glossary_id', 'id', '_id', 'name', 'glossary_name']:
                            self.stdout.write(f'   {key}: {value}')
                    self.stdout.write('')
            else:
                self.stdout.write(f'{i}. {glossary}')

        self.stdout.write('-' * 80)
        self.stdout.write(f'Total: {len(glossaries)} glossaries')
