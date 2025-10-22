import os
import tempfile
import logging
from django.contrib import admin
from django.shortcuts import render, redirect
from django.urls import path
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django import forms
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
                    'target_language', 'domain',  'created_at']
    list_filter = [DomainFilter, SourceLanguageFilter,
                   TargetLanguageFilter, UserFilter, 'created_at']
    search_fields = ['name', 'domain__name']

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('batch-upload/', self.admin_site.admin_view(self.batch_upload_view),
                 name='glossary_batch_upload'),
            path('process-batch/', self.admin_site.admin_view(self.process_batch_view),
                 name='glossary_process_batch'),
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
                        # Store paths in session for processing
                        request.session['batch_csv_path'] = temp_csv.name
                        request.session['batch_zip_path'] = temp_zip.name

                        logger.info(
                            "Files stored in session, rendering success page")

                        context.update({
                            'csv_filename': csv_file.name,
                            'zip_filename': zip_file.name,
                            'ready_to_process': True,
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

    @method_decorator(csrf_exempt)
    def process_batch_view(self, request):
        logger.info(f"Process batch view accessed. Method: {request.method}")

        if request.method == 'POST':
            try:
                csv_path = request.session.get('batch_csv_path')
                zip_path = request.session.get('batch_zip_path')

                logger.info(
                    f"Session paths - CSV: {csv_path}, ZIP: {zip_path}")

                if not csv_path or not zip_path:
                    logger.error("Files not found in session")
                    return JsonResponse({'error': 'Files not found. Please try again.'})

                # Verify files exist
                if not os.path.exists(csv_path):
                    logger.error(f"CSV file not found: {csv_path}")
                    return JsonResponse({'error': f'CSV file not found: {csv_path}'})

                if not os.path.exists(zip_path):
                    logger.error(f"ZIP file not found: {zip_path}")
                    return JsonResponse({'error': f'ZIP file not found: {zip_path}'})

                logger.info("Starting batch processing")
                results = Glossary.glossaries_batch(csv_path, zip_path)
                logger.info(f"Batch processing completed: {results}")

                # Clean up temporary files
                try:
                    if os.path.exists(csv_path):
                        os.unlink(csv_path)
                        logger.info(f"Cleaned up CSV file: {csv_path}")
                    if os.path.exists(zip_path):
                        os.unlink(zip_path)
                        logger.info(f"Cleaned up ZIP file: {zip_path}")
                except Exception as cleanup_error:
                    logger.warning(f"Error cleaning up files: {cleanup_error}")

                # Clear session
                request.session.pop('batch_csv_path', None)
                request.session.pop('batch_zip_path', None)
                logger.info("Session cleared")

                return JsonResponse({
                    'success': True,
                    'created': results['created'],
                    'total_rows': results['total_rows'],
                    'errors': results['errors']
                })

            except Exception as e:
                logger.error(
                    f"Error in process_batch_view: {str(e)}", exc_info=True)
                return JsonResponse({'error': f'Processing error: {str(e)}'})

        logger.error("Invalid method for process_batch_view")
        return JsonResponse({'error': 'Method not allowed'})

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_batch_upload'] = True
        return super().changelist_view(request, extra_context)
