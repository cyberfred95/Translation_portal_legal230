import os
import csv
import tempfile
import logging
import uuid
import threading
from django.contrib import admin
from django.shortcuts import render, redirect
from django.urls import path
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django import forms
from django.core.cache import cache
from .models import Glossary
from .forms import GlossaryAdminForm
from languages.models import Language
from domains.models import Domain

logger = logging.getLogger(__name__)


class BatchUploadForm(forms.Form):
    csv_file = forms.FileField(
        label="CSV Description File",
        help_text="CSV file containing the structure: file,source_language,target_language,domain. Existing glossaries will be updated.",
        widget=forms.FileInput(attrs={'accept': '.csv'})
    )
    zip_file = forms.FileField(
        label="Glossaries ZIP File",
        help_text="ZIP file containing all glossary files listed in the CSV",
        widget=forms.FileInput(attrs={'accept': '.zip'})
    )

    def clean_csv_file(self):
        csv_file = self.cleaned_data.get('csv_file')
        if csv_file:
            if csv_file.size == 0:
                raise forms.ValidationError(
                    "The CSV file is empty. Please select a valid file.")
            if not csv_file.name.lower().endswith('.csv'):
                raise forms.ValidationError(
                    "The file must be in CSV format.")
        return csv_file

    def clean_zip_file(self):
        zip_file = self.cleaned_data.get('zip_file')
        if zip_file:
            if zip_file.size == 0:
                raise forms.ValidationError(
                    "The ZIP file is empty. Please select a valid file.")
            if not zip_file.name.lower().endswith('.zip'):
                raise forms.ValidationError(
                    "The file must be in ZIP format.")
        return zip_file


class SourceLanguageFilter(admin.SimpleListFilter):
    title = 'source language'
    parameter_name = 'source_language'

    def lookups(self, request, model_admin):
        ids = set(Glossary.objects.values_list('source_language', flat=True))
        languages = Language.objects.filter(id__in=ids)
        return [(lang.id, lang.name) for lang in languages]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(source_language=self.value())
        return queryset


class TargetLanguageFilter(admin.SimpleListFilter):
    title = 'target language'
    parameter_name = 'target_language'

    def lookups(self, request, model_admin):
        ids = set(Glossary.objects.values_list('target_language', flat=True))
        languages = Language.objects.filter(id__in=ids)
        return [(lang.id, lang.name) for lang in languages]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(target_language=self.value())
        return queryset


class DomainFilter(admin.SimpleListFilter):
    title = 'domain'
    parameter_name = 'domain'

    def lookups(self, request, model_admin):
        ids = set(Glossary.objects.values_list('domain', flat=True))
        domains = Domain.objects.filter(id__in=ids)
        return [(dom.id, dom.name) for dom in domains]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(domain=self.value())
        return queryset


class UserFilter(admin.SimpleListFilter):
    title = 'user'
    parameter_name = 'user'

    def lookups(self, request, model_admin):
        return [
            ('__all__', 'Created by a User'),
            ('__none__', 'Created by an admin')
        ]

    def queryset(self, request, queryset):
        if self.value() == '__none__':
            return queryset.filter(user__isnull=True)
        elif self.value() == '__all__':
            return queryset.exclude(user__isnull=True)
        return queryset


@admin.register(Glossary)
class GlossaryAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'source_language',
                    'target_language', 'domain', 'has_remote_id', 'created_at']
    list_filter = [DomainFilter, SourceLanguageFilter,
                   TargetLanguageFilter, UserFilter, 'created_at']
    search_fields = ['name', 'domain__name']

    def has_remote_id(self, obj):
        """Display whether glossary has a remote glossary_id"""
        from django.utils.html import format_html

        if obj.glossary_id:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ True</span>'
            )
        else:
            return format_html(
                '<span style="color: red; font-weight: bold;">✗ False</span>'
            )

    has_remote_id.short_description = 'Remote ID'
    has_remote_id.admin_order_field = 'glossary_id'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('batch-upload/', self.admin_site.admin_view(self.batch_upload_view),
                 name='glossary_batch_upload'),
            path('process-batch/', self.admin_site.admin_view(self.process_batch_view),
                 name='glossary_process_batch'),
            path('batch-progress/', self.admin_site.admin_view(self.batch_progress_view),
                 name='glossary_batch_progress'),
            path('check-consistency/', self.admin_site.admin_view(self.check_consistency_view),
                 name='glossary_check_consistency'),
            path('check-consistency-progress/', self.admin_site.admin_view(self.check_consistency_progress_view),
                 name='glossary_check_consistency_progress'),
            path('process-consistency-check/', self.admin_site.admin_view(self.process_consistency_check_view),
                 name='glossary_process_consistency_check'),
            path('compare-csv/', self.admin_site.admin_view(self.compare_csv_view),
                 name='glossary_compare_csv'),
            path('process-csv-comparison/', self.admin_site.admin_view(self.process_csv_comparison_view),
                 name='glossary_process_csv_comparison'),
            path('csv-comparison-progress/', self.admin_site.admin_view(self.csv_comparison_progress_view),
                 name='glossary_csv_comparison_progress'),
        ]
        return custom_urls + urls

    def batch_upload_view(self, request):
        logger.info(f"Batch upload view accessed. Method: {request.method}")
        context = dict(
            self.admin_site.each_context(request),
            opts=self.model._meta,
            app_label=self.model._meta.app_label,
            app_list=self.admin_site.get_app_list(request),
            has_permission=True,
            is_nav_sidebar_enabled=True,
            available_apps=self.admin_site.get_app_list(request),
        )

        if request.method == 'POST':
            try:
                logger.info("Processing POST request for batch upload")
                logger.info(f"POST data: {request.POST}")
                logger.info(f"FILES data: {list(request.FILES.keys())}")

                # Log file details if present
                if 'csv_file' in request.FILES:
                    csv_file = request.FILES['csv_file']
                    logger.info(
                        f"CSV file received: name={csv_file.name}, size={csv_file.size}, content_type={csv_file.content_type}")
                else:
                    logger.error("CSV file not found in request.FILES")

                if 'zip_file' in request.FILES:
                    zip_file = request.FILES['zip_file']
                    logger.info(
                        f"ZIP file received: name={zip_file.name}, size={zip_file.size}, content_type={zip_file.content_type}")
                else:
                    logger.error("ZIP file not found in request.FILES")

                form = BatchUploadForm(request.POST, request.FILES)

                if form.is_valid():
                    logger.info("Form is valid, processing files")
                    # Store files temporarily
                    csv_file = form.cleaned_data['csv_file']
                    zip_file = form.cleaned_data['zip_file']

                    logger.info(
                        f"Cleaned CSV file: {csv_file.name}, size: {csv_file.size}")
                    logger.info(
                        f"Cleaned ZIP file: {zip_file.name}, size: {zip_file.size}")

                    # Save files temporarily
                    temp_csv = tempfile.NamedTemporaryFile(
                        delete=False, suffix='.csv')
                    temp_zip = tempfile.NamedTemporaryFile(
                        delete=False, suffix='.zip')

                    # Write CSV file
                    csv_file.seek(0)  # Reset file pointer
                    for chunk in csv_file.chunks():
                        temp_csv.write(chunk)
                    temp_csv.close()

                    # Write ZIP file
                    zip_file.seek(0)  # Reset file pointer
                    for chunk in zip_file.chunks():
                        temp_zip.write(chunk)
                    temp_zip.close()

                    logger.info(
                        f"Temporary files created: CSV={temp_csv.name}, ZIP={temp_zip.name}")

                    # Verify files were written correctly
                    csv_size = os.path.getsize(temp_csv.name)
                    zip_size = os.path.getsize(temp_zip.name)
                    logger.info(
                        f"Temporary file sizes: CSV={csv_size}, ZIP={zip_size}")

                    if csv_size == 0:
                        logger.error("CSV file was written with 0 bytes")
                        os.unlink(temp_csv.name)
                        os.unlink(temp_zip.name)
                        messages.error(
                            request, "The CSV file could not be saved properly.")
                        form = BatchUploadForm()
                    elif zip_size == 0:
                        logger.error("ZIP file was written with 0 bytes")
                        os.unlink(temp_csv.name)
                        os.unlink(temp_zip.name)
                        messages.error(
                            request, "The ZIP file could not be saved properly.")
                        form = BatchUploadForm()
                    else:
                        # Generate a unique batch ID for this upload
                        batch_id = str(uuid.uuid4())

                        # Store paths in session for processing
                        request.session['batch_csv_path'] = temp_csv.name
                        request.session['batch_zip_path'] = temp_zip.name
                        request.session['batch_id'] = batch_id

                        # Clear any previous batch progress in cache
                        cache.delete(f'batch_progress_{batch_id}')

                        logger.info(
                            f"Files stored in session with batch_id: {batch_id}, rendering success page")

                        context.update({
                            'csv_filename': csv_file.name,
                            'zip_filename': zip_file.name,
                            'ready_to_process': True,
                            'batch_id': batch_id,
                        })
                        return render(request, 'admin/glossaries/batch_upload.html', context)
                else:
                    logger.error(f"Form validation errors: {form.errors}")
                    logger.error(
                        f"Form non-field errors: {form.non_field_errors()}")
                    # Don't use messages.error for form errors, let the template handle them
            except Exception as e:
                logger.error(
                    f"Error in batch_upload_view POST: {str(e)}", exc_info=True)
                messages.error(
                    request, f"Error during file loading: {str(e)}")
                form = BatchUploadForm()
        else:
            logger.info("GET request for batch upload form")
            form = BatchUploadForm()

        context.update({
            'form': form,
        })
        return render(request, 'admin/glossaries/batch_upload.html', context)

    def batch_progress_view(self, request):
        """Return current batch processing progress"""
        try:
            batch_id = request.GET.get('batch_id')
            if not batch_id:
                logger.error("No batch_id provided")
                return JsonResponse({'error': 'No batch_id provided'}, status=400)

            # Support DELETE method to clear progress
            if request.method == 'DELETE':
                cache.delete(f'batch_progress_{batch_id}')
                logger.info(f"Batch progress cleared from cache for batch_id: {batch_id}")
                return JsonResponse({'status': 'cleared'}, status=200)

            # Get progress from cache
            cache_key = f'batch_progress_{batch_id}'
            progress_data = cache.get(cache_key, {})

            if not progress_data:
                logger.debug(f"No progress data found in cache for batch_id: {batch_id}")
                progress_data = {'status': 'waiting', 'message': 'En attente de démarrage...'}

            return JsonResponse(progress_data, status=200)
        except Exception as e:
            logger.error(f"Error in batch_progress_view: {str(e)}", exc_info=True)
            return JsonResponse({'error': str(e)}, status=500)

    def process_batch_view(self, request):
        """Process batch glossary upload in background thread - returns immediately"""
        logger.info(f"Process batch view accessed. Method: {request.method}")

        # Wrap entire method in try/except to ensure we always return JSON
        try:
            if request.method != 'POST':
                logger.error("Invalid method for process_batch_view")
                return JsonResponse({'error': 'Method not allowed'}, status=405)

            csv_path = request.session.get('batch_csv_path')
            zip_path = request.session.get('batch_zip_path')
            batch_id = request.session.get('batch_id')

            logger.info(
                f"Session paths - CSV: {csv_path}, ZIP: {zip_path}, batch_id: {batch_id}")

            if not csv_path or not zip_path or not batch_id:
                logger.error("Files or batch_id not found in session")
                return JsonResponse({'error': 'Files not found. Please try again.'}, status=400)

            # Verify files exist
            if not os.path.exists(csv_path):
                logger.error(f"CSV file not found: {csv_path}")
                return JsonResponse({'error': f'CSV file not found: {csv_path}'}, status=404)

            if not os.path.exists(zip_path):
                logger.error(f"ZIP file not found: {zip_path}")
                return JsonResponse({'error': f'ZIP file not found: {zip_path}'}, status=404)

            # Initialize progress tracking in cache (timeout: 2 hours)
            cache_key = f'batch_progress_{batch_id}'
            cache.set(cache_key, {
                'status': 'processing',
                'current_row': 0,
                'total_rows': 0,
                'created': 0,
                'message': 'Démarrage du traitement...'
            }, timeout=7200)

            # Store results in cache (will be set by the thread)
            results_cache_key = f'batch_results_{batch_id}'

            # Define the background processing function
            def process_in_background():
                try:
                    logger.info(f"[Thread {batch_id}] Starting background batch processing")

                    # Define progress callback
                    def progress_callback(message, row_num, created, total_rows):
                        progress_data = {
                            'status': 'processing',
                            'current_row': row_num or total_rows,
                            'total_rows': total_rows,
                            'created': created,
                            'message': message
                        }
                        cache.set(cache_key, progress_data, timeout=7200)
                        logger.info(f"[Thread {batch_id}] Progress: {message} (row: {row_num}, created: {created}, total: {total_rows})")

                    # Execute the batch processing
                    results = Glossary.glossaries_batch(csv_path, zip_path, progress_callback=progress_callback)
                    logger.info(f"[Thread {batch_id}] Batch processing completed: {results}")

                    # Store results in cache
                    cache.set(results_cache_key, results, timeout=7200)

                    # Update progress to complete
                    cache.set(cache_key, {
                        'status': 'completed',
                        'current_row': results['total_rows'],
                        'total_rows': results['total_rows'],
                        'created': results['created'],
                        'updated': results['updated'],
                        'message': 'Traitement terminé',
                        'errors': results.get('errors', [])
                    }, timeout=7200)

                    # Clean up temporary files
                    try:
                        if os.path.exists(csv_path):
                            os.unlink(csv_path)
                            logger.info(f"[Thread {batch_id}] Cleaned up CSV file: {csv_path}")
                        if os.path.exists(zip_path):
                            os.unlink(zip_path)
                            logger.info(f"[Thread {batch_id}] Cleaned up ZIP file: {zip_path}")
                    except Exception as cleanup_error:
                        logger.warning(f"[Thread {batch_id}] Error cleaning up files: {cleanup_error}")

                except Exception as e:
                    # Update progress to error in cache
                    logger.error(f"[Thread {batch_id}] Error in background processing: {str(e)}", exc_info=True)
                    cache.set(cache_key, {
                        'status': 'error',
                        'message': f'Erreur: {str(e)}'
                    }, timeout=7200)

                    # Store error results
                    cache.set(results_cache_key, {
                        'success': False,
                        'error': str(e),
                        'created': 0,
                        'total_rows': 0,
                        'errors': [str(e)]
                    }, timeout=7200)

            # Start the background thread
            thread = threading.Thread(target=process_in_background, daemon=True)
            thread.start()
            logger.info(f"Background thread started for batch_id: {batch_id}")

            # Return immediately - the thread will continue processing
            return JsonResponse({
                'success': True,
                'message': 'Traitement lancé en arrière-plan',
                'batch_id': batch_id,
                'status': 'started'
            }, status=202)  # 202 Accepted

        except Exception as e:
            # Update progress to error in cache
            batch_id = request.session.get('batch_id')
            if batch_id:
                cache_key = f'batch_progress_{batch_id}'
                cache.set(cache_key, {
                    'status': 'error',
                    'message': f'Erreur: {str(e)}'
                }, timeout=7200)

            # Catch ANY exception and return as JSON
            logger.error(
                f"Error in process_batch_view: {str(e)}", exc_info=True)
            return JsonResponse({
                'error': f'Processing error: {str(e)}',
                'success': False
            }, status=500)

    def check_consistency_view(self, request):
        """View to check glossary consistency with remote API"""
        from django.conf import settings
        from preferences import preferences

        context = dict(
            self.admin_site.each_context(request),
            opts=self.model._meta,
            app_label=self.model._meta.app_label,
            has_permission=True,
        )

        if request.method == 'GET':
            # Check if we need to display results
            show_results = request.GET.get('show_results')
            if show_results:
                results_cache_key = f'check_results_{show_results}'
                results = cache.get(results_cache_key)
                if results:
                    context.update({'results': results})
                    return render(request, 'admin/glossaries/check_consistency_results.html', context)

            # Display the check options page
            context.update({
                'glossary_system': settings.GLOSSARY_SYSTEM,
                'glossary_api_key': '***' if settings.GLOSSARY_API_KEY else 'NOT SET',
                'glossaries_url': preferences.MainSettings.glossaries_url,
                'total_glossaries': Glossary.objects.count(),
                'with_id': Glossary.objects.exclude(glossary_id__isnull=True).exclude(glossary_id='').count(),
                'without_id': Glossary.objects.filter(glossary_id__isnull=True).count() +
                             Glossary.objects.filter(glossary_id='').count(),
            })
            return render(request, 'admin/glossaries/check_consistency.html', context)

        elif request.method == 'POST':
            # Store options in session and prepare for async processing
            verbose = request.POST.get('verbose') == 'on'
            id_null_only = request.POST.get('id_null_only') == 'on'

            # Generate a unique check ID
            check_id = str(uuid.uuid4())

            # Store options in session
            request.session['check_verbose'] = verbose
            request.session['check_id_null_only'] = id_null_only
            request.session['check_id'] = check_id

            # Clear any previous check progress in cache
            cache.delete(f'check_progress_{check_id}')

            context.update({
                'glossary_system': settings.GLOSSARY_SYSTEM,
                'verbose': verbose,
                'id_null_only': id_null_only,
                'check_id': check_id,
                'ready_to_process': True,
            })
            return render(request, 'admin/glossaries/check_consistency.html', context)

    def check_consistency_progress_view(self, request):
        """Return current consistency check progress"""
        try:
            check_id = request.GET.get('check_id')
            if not check_id:
                return JsonResponse({'error': 'No check_id provided'}, status=400)

            # Support DELETE method to clear progress
            if request.method == 'DELETE':
                cache.delete(f'check_progress_{check_id}')
                return JsonResponse({'status': 'cleared'}, status=200)

            # Get progress from cache
            cache_key = f'check_progress_{check_id}'
            progress_data = cache.get(cache_key, {})

            if not progress_data:
                progress_data = {'status': 'waiting', 'message': 'En attente de démarrage...'}

            return JsonResponse(progress_data, status=200)
        except Exception as e:
            logger.error(f"Error in check_consistency_progress_view: {str(e)}", exc_info=True)
            return JsonResponse({'error': str(e)}, status=500)

    def process_consistency_check_view(self, request):
        """Process consistency check in background thread"""
        try:
            if request.method != 'POST':
                return JsonResponse({'error': 'Method not allowed'}, status=405)

            from django.conf import settings
            from preferences import preferences
            from glossaries.helpers import get_glossary_username
            import requests

            verbose = request.session.get('check_verbose', False)
            id_null_only = request.session.get('check_id_null_only', False)
            check_id = request.session.get('check_id')

            if not check_id:
                return JsonResponse({'error': 'Check ID not found in session'}, status=400)

            # Initialize progress tracking in cache
            cache_key = f'check_progress_{check_id}'
            cache.set(cache_key, {
                'status': 'processing',
                'current': 0,
                'total': 0,
                'message': 'Démarrage de la vérification...'
            }, timeout=7200)

            # Define the background processing function
            def process_in_background():
                try:
                    results = {
                        'verbose': verbose,
                        'id_null_only': id_null_only,
                        'glossary_system': settings.GLOSSARY_SYSTEM,
                        'total_glossaries': Glossary.objects.count(),
                    }

                    if id_null_only:
                        # Only show glossaries without ID
                        glossaries_without_id = Glossary.objects.filter(
                            glossary_id__isnull=True
                        ) | Glossary.objects.filter(glossary_id='')

                        results['without_id_count'] = glossaries_without_id.count()
                        results['without_id_list'] = []

                        cache.set(cache_key, {
                            'status': 'processing',
                            'current': 0,
                            'total': results['without_id_count'],
                            'message': 'Lecture des glossaires sans ID...'
                        }, timeout=7200)

                        for glossary in glossaries_without_id:
                            owner = 'Admin/Default'
                            if glossary.user:
                                owner = f'User: {glossary.user.username}'
                            elif glossary.group:
                                owner = f'Group: {glossary.group.name}'

                            results['without_id_list'].append({
                                'id': glossary.id,
                                'name': glossary.name,
                                'source': glossary.source_language.abbreviation,
                                'target': glossary.target_language.abbreviation,
                                'domain': glossary.domain.name if glossary.domain else 'No domain',
                                'owner': owner,
                            })
                    else:
                        # Check glossaries with ID against remote API
                        glossaries = Glossary.objects.exclude(glossary_id__isnull=True).exclude(glossary_id='')

                        stats = {
                            'total': glossaries.count(),
                            'found': 0,
                            'not_found': 0,
                            'errors': 0,
                        }

                        found_list = []
                        not_found_list = []
                        error_list = []

                        cache.set(cache_key, {
                            'status': 'processing',
                            'current': 0,
                            'total': stats['total'],
                            'message': 'Vérification en cours...'
                        }, timeout=7200)

                        # Use concurrent execution for faster processing
                        from concurrent.futures import ThreadPoolExecutor, as_completed
                        import time

                        def check_single_glossary(glossary):
                            """Check a single glossary against remote API"""
                            start_time = time.time()

                            owner = 'Admin/Default'
                            if glossary.user:
                                owner = f'User: {glossary.user.username}'
                            elif glossary.group:
                                owner = f'Group: {glossary.group.name}'

                            glossary_info = {
                                'id': glossary.id,
                                'name': glossary.name,
                                'source': glossary.source_language.abbreviation,
                                'target': glossary.target_language.abbreviation,
                                'domain': glossary.domain.name if glossary.domain else 'No domain',
                                'owner': owner,
                                'glossary_id': glossary.glossary_id,
                            }

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

                                # Log first request for debugging
                                import logging
                                logger = logging.getLogger(__name__)
                                if glossary.id == glossaries_list[0].id:
                                    logger.info(f"API Request - URL: {url}")
                                    logger.info(f"API Request - Payload: {payload}")
                                    logger.info(f"API Request - Has API-KEY: {bool(settings.GLOSSARY_API_KEY)}")

                                api_start = time.time()
                                response = requests.post(url, headers=headers, json=payload, timeout=60)
                                api_duration = time.time() - api_start

                                total_duration = time.time() - start_time
                                glossary_info['api_time'] = f"{api_duration:.3f}s"
                                glossary_info['total_time'] = f"{total_duration:.3f}s"

                                if response.status_code == 200:
                                    return ('found', glossary_info)
                                elif response.status_code == 404:
                                    return ('not_found', glossary_info)
                                else:
                                    glossary_info['error'] = f"HTTP {response.status_code}"
                                    return ('error', glossary_info)
                            except requests.exceptions.Timeout:
                                total_duration = time.time() - start_time
                                glossary_info['total_time'] = f"{total_duration:.3f}s"
                                glossary_info['error'] = "Timeout (60s)"
                                return ('error', glossary_info)
                            except Exception as e:
                                total_duration = time.time() - start_time
                                glossary_info['total_time'] = f"{total_duration:.3f}s"
                                glossary_info['error'] = str(e)
                                return ('error', glossary_info)

                        # Process glossaries concurrently with 20 workers
                        glossaries_list = list(glossaries)
                        completed = 0
                        api_times = []

                        with ThreadPoolExecutor(max_workers=20) as executor:
                            future_to_glossary = {executor.submit(check_single_glossary, g): g for g in glossaries_list}

                            for future in as_completed(future_to_glossary):
                                completed += 1
                                result_type, glossary_info = future.result()

                                # Track API response times
                                if 'api_time' in glossary_info:
                                    try:
                                        api_times.append(float(glossary_info['api_time'].replace('s', '')))
                                    except:
                                        pass

                                if result_type == 'found':
                                    stats['found'] += 1
                                    if verbose:
                                        found_list.append(glossary_info)
                                elif result_type == 'not_found':
                                    stats['not_found'] += 1
                                    not_found_list.append(glossary_info)
                                else:  # error
                                    stats['errors'] += 1
                                    error_list.append(glossary_info)

                                # Update progress every 10 glossaries
                                if completed % 10 == 0 or completed == stats['total']:
                                    cache.set(cache_key, {
                                        'status': 'processing',
                                        'current': completed,
                                        'total': stats['total'],
                                        'found': stats['found'],
                                        'not_found': stats['not_found'],
                                        'errors': stats['errors'],
                                        'message': f'Vérification {completed}/{stats["total"]}...'
                                    }, timeout=7200)

                        # Calculate timing statistics
                        if api_times:
                            stats['avg_api_time'] = f"{sum(api_times) / len(api_times):.3f}s"
                            stats['min_api_time'] = f"{min(api_times):.3f}s"
                            stats['max_api_time'] = f"{max(api_times):.3f}s"

                        results['stats'] = stats
                        results['found_list'] = found_list
                        results['not_found_list'] = not_found_list
                        results['error_list'] = error_list

                    # Store results in cache
                    results_cache_key = f'check_results_{check_id}'
                    cache.set(results_cache_key, results, timeout=7200)

                    # Update progress to complete
                    cache.set(cache_key, {
                        'status': 'completed',
                        'message': 'Vérification terminée',
                        'results': results
                    }, timeout=7200)

                except Exception as e:
                    logger.error(f"Error in background check: {str(e)}", exc_info=True)
                    cache.set(cache_key, {
                        'status': 'error',
                        'message': f'Erreur: {str(e)}'
                    }, timeout=7200)

            # Start the background thread
            thread = threading.Thread(target=process_in_background, daemon=True)
            thread.start()
            logger.info(f"Background check thread started for check_id: {check_id}")

            # Return immediately
            return JsonResponse({
                'success': True,
                'message': 'Vérification lancée en arrière-plan',
                'check_id': check_id,
                'status': 'started'
            }, status=202)

        except Exception as e:
            logger.error(f"Error in process_consistency_check_view: {str(e)}", exc_info=True)
            return JsonResponse({
                'error': f'Processing error: {str(e)}',
                'success': False
            }, status=500)

    def compare_csv_view(self, request):
        """View for uploading CSV file to compare with local database"""
        logger.info(f"Compare CSV view accessed. Method: {request.method}")

        context = dict(
            self.admin_site.each_context(request),
            opts=self.model._meta,
            app_label=self.model._meta.app_label,
            has_permission=True,
        )

        if request.method == 'POST':
            csv_file = request.FILES.get('csv_file')
            if not csv_file:
                context['error'] = 'Aucun fichier CSV fourni'
                return render(request, 'admin/glossaries/compare_csv.html', context)

            # Save CSV temporarily
            import tempfile
            import uuid

            comparison_id = str(uuid.uuid4())
            temp_dir = tempfile.gettempdir()
            csv_path = os.path.join(temp_dir, f'compare_{comparison_id}.csv')

            try:
                with open(csv_path, 'wb+') as destination:
                    for chunk in csv_file.chunks():
                        destination.write(chunk)
                logger.info(f"CSV file saved to: {csv_path}")

                # Store path in session
                request.session['comparison_csv_path'] = csv_path
                request.session['comparison_id'] = comparison_id

                # Redirect to processing
                context['csv_uploaded'] = True
                context['comparison_id'] = comparison_id
                return render(request, 'admin/glossaries/compare_csv.html', context)

            except Exception as e:
                logger.error(f"Error saving CSV file: {str(e)}", exc_info=True)
                context['error'] = f'Erreur lors de la sauvegarde du fichier: {str(e)}'
                return render(request, 'admin/glossaries/compare_csv.html', context)

        return render(request, 'admin/glossaries/compare_csv.html', context)

    def process_csv_comparison_view(self, request):
        """Process CSV comparison in background thread"""
        logger.info(f"Process CSV comparison view accessed. Method: {request.method}")

        try:
            if request.method != 'POST':
                return JsonResponse({'error': 'Method not allowed'}, status=405)

            csv_path = request.session.get('comparison_csv_path')
            comparison_id = request.session.get('comparison_id')

            if not csv_path or not comparison_id:
                return JsonResponse({'error': 'CSV file not found in session'}, status=400)

            if not os.path.exists(csv_path):
                return JsonResponse({'error': f'CSV file not found: {csv_path}'}, status=404)

            # Initialize progress tracking
            cache_key = f'csv_comparison_progress_{comparison_id}'
            cache.set(cache_key, {
                'status': 'processing',
                'message': 'Démarrage de la comparaison...'
            }, timeout=7200)

            # Background processing function
            def process_in_background():
                try:
                    logger.info(f"[Thread {comparison_id}] Starting CSV comparison")

                    # Parse CSV
                    csv_glossaries = self._parse_csv_for_comparison(csv_path)

                    # Get local glossaries
                    local_glossaries = self._get_local_glossaries_for_comparison()

                    # Compare
                    results = self._compare_local_csv(local_glossaries, csv_glossaries)

                    # Store results in cache
                    results_cache_key = f'csv_comparison_results_{comparison_id}'
                    cache.set(results_cache_key, results, timeout=7200)

                    # Update progress to complete
                    cache.set(cache_key, {
                        'status': 'completed',
                        'message': 'Comparaison terminée'
                    }, timeout=7200)

                    # Clean up temporary file
                    try:
                        if os.path.exists(csv_path):
                            os.remove(csv_path)
                            logger.info(f"Cleaned up temp CSV: {csv_path}")
                    except Exception as e:
                        logger.error(f"Error cleaning up temp file: {e}")

                except Exception as e:
                    logger.error(f"Error in background comparison: {str(e)}", exc_info=True)
                    cache.set(cache_key, {
                        'status': 'error',
                        'message': f'Erreur: {str(e)}'
                    }, timeout=7200)

            # Start background thread
            thread = threading.Thread(target=process_in_background, daemon=True)
            thread.start()
            logger.info(f"Background comparison thread started for comparison_id: {comparison_id}")

            return JsonResponse({
                'success': True,
                'message': 'Comparaison lancée en arrière-plan',
                'comparison_id': comparison_id,
                'status': 'started'
            }, status=202)

        except Exception as e:
            logger.error(f"Error in process_csv_comparison_view: {str(e)}", exc_info=True)
            return JsonResponse({
                'error': f'Processing error: {str(e)}',
                'success': False
            }, status=500)

    def csv_comparison_progress_view(self, request):
        """Check progress of CSV comparison"""
        comparison_id = request.GET.get('comparison_id')
        if not comparison_id:
            return JsonResponse({'error': 'comparison_id required'}, status=400)

        cache_key = f'csv_comparison_progress_{comparison_id}'
        progress_data = cache.get(cache_key)

        if not progress_data:
            return JsonResponse({'error': 'Comparison not found'}, status=404)

        if progress_data.get('status') == 'completed':
            # Get results
            results_cache_key = f'csv_comparison_results_{comparison_id}'
            results = cache.get(results_cache_key)

            if results:
                # Render results page
                context = dict(
                    self.admin_site.each_context(request),
                    opts=self.model._meta,
                    results=results,
                )
                html = render(request, 'admin/glossaries/compare_csv_results.html', context).content.decode('utf-8')
                return JsonResponse({
                    'status': 'completed',
                    'html': html
                })

        return JsonResponse(progress_data)

    def _parse_csv_for_comparison(self, csv_file):
        """Parse CSV file for comparison"""
        glossaries = []
        with open(csv_file, 'r', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile)
            for row_num, row in enumerate(reader, start=2):
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
        return glossaries

    def _get_local_glossaries_for_comparison(self):
        """Get local glossaries for comparison"""
        glossaries = []
        for glossary in Glossary.objects.all():
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
        return glossaries

    def _compare_local_csv(self, local_glossaries, csv_glossaries):
        """Compare local and CSV glossaries"""
        def make_key(g, from_csv=False):
            # The key is based on how batch upload identifies glossaries:
            # domain, source_language, target_language, and owner (user/group/admin)
            # NOTE: The file name is NOT part of the key because batch upload
            # identifies existing glossaries by lang+domain+owner, not by filename
            if from_csv:
                owner = g['user'] if g['user'] else (g['group'] if g['group'] else '')
                return (g['source'], g['target'], g['domain'], owner)
            else:
                return (g['source'], g['target'], g['domain'], g['owner_value'])

        # Detect duplicates in CSV
        csv_keys_count = {}
        csv_duplicates = []
        for g in csv_glossaries:
            key = make_key(g, True)
            if key in csv_keys_count:
                csv_keys_count[key].append(g)
            else:
                csv_keys_count[key] = [g]

        # Find duplicates (keys with more than one entry)
        for key, entries in csv_keys_count.items():
            if len(entries) > 1:
                csv_duplicates.append({
                    'key': key,
                    'entries': entries,
                    'count': len(entries)
                })

        local_dict = {make_key(g): g for g in local_glossaries}
        csv_dict = {make_key(g, True): g for g in csv_glossaries}

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

        return {
            'total_local': len(local_glossaries),
            'total_csv': len(csv_glossaries),
            'unique_csv': len(csv_dict),
            'csv_duplicates': csv_duplicates,
            'in_both': in_both,
            'only_in_local': only_in_local,
            'only_in_csv': only_in_csv
        }

    def changelist_view(self, request, extra_context=None):
        from django.conf import settings
        extra_context = extra_context or {}
        extra_context['show_batch_upload'] = True
        extra_context['glossary_system'] = settings.GLOSSARY_SYSTEM
        return super().changelist_view(request, extra_context)
