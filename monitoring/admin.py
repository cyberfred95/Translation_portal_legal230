"""
Admin interface for monitoring system.
"""
from django.contrib import admin
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils.html import format_html

from .models import HealthCheckResult, HealthCheckRun
from .runner import run_all_health_checks
from .constants import STATUS_COLORS, SERVICE_DESCRIPTIONS


def format_colored_status(status: str) -> str:
    """
    Format status with color coding for admin display.
    
    Args:
        status: Status string ('success', 'warning', 'error')
    
    Returns:
        HTML formatted status string
    """
    color = STATUS_COLORS.get(status, 'gray')
    return format_html(
        '<span style="color: {}; font-weight: bold;">{}</span>',
        color,
        status.upper()
    )


def format_run_result_message(run_result: dict) -> tuple[str, str]:
    """
    Format health check run result into message and level.
    
    Args:
        run_result: Dictionary with run results
    
    Returns:
        Tuple of (message, level) where level is 'error', 'warning', or 'success'
    """
    failed = run_result['failed_checks']
    warnings = run_result['warning_checks']
    total = run_result['total_checks']
    time_ms = run_result['total_execution_time_ms']
    
    if failed > 0:
        return (
            f"Health checks completed with {failed} failures and {warnings} warnings. Total time: {time_ms}ms",
            'error'
        )
    elif warnings > 0:
        return (
            f"Health checks completed with {warnings} warnings. Total time: {time_ms}ms",
            'warning'
        )
    else:
        return (
            f"All {total} health checks passed successfully! Total time: {time_ms}ms",
            'success'
        )


class HealthCheckResultAdmin(admin.ModelAdmin):
    """
    Admin interface for health check results.
    
    Features:
    - Service name tooltips with short descriptions
    - Full service descriptions on detail pages
    - Color-coded status display
    """
    
    class Media:
        css = {
            'all': ('monitoring/css/admin_custom.css',)
        }
    
    list_display = [
        'service_name_with_tooltip',
        'status',
        'category',
        'timestamp',
        'execution_time_ms',
        'colored_status'
    ]
    list_filter = ['status', 'category', 'timestamp']
    search_fields = ['service_name', 'message']
    readonly_fields = [
        'timestamp',
        'category',
        'service_name',
        'status',
        'message',
        'details',
        'execution_time_ms'
    ]
    date_hierarchy = 'timestamp'
    
    # Helper methods
    
    def _get_service_descriptions(self, service_name: str) -> tuple[str, str]:
        """
        Get short and long descriptions for a service.
        
        Args:
            service_name: Name of the service
            
        Returns:
            Tuple of (short_description, long_description)
        """
        descriptions = SERVICE_DESCRIPTIONS.get(service_name, {})
        return (
            descriptions.get('short', service_name),
            descriptions.get('long', '')
        )
    
    def _build_service_description_html(self, service_name: str, long_description: str) -> str:
        """
        Build HTML for service description display.
        
        Args:
            service_name: Name of the service
            long_description: Long description text
            
        Returns:
            HTML string for description
        """
        if not long_description:
            return ''
        
        return f'<strong>What is "{service_name}"?</strong><br><span style="color: #666;">{long_description}</span>'
    
    # Admin methods
    
    def get_fieldsets(self, request, obj=None):
        """Build dynamic fieldsets with service description."""
        description_html = ''
        
        if obj:
            _, long_desc = self._get_service_descriptions(obj.service_name)
            description_html = self._build_service_description_html(obj.service_name, long_desc)
        
        return (
            (None, {
                'description': description_html,
                'fields': (),
            }),
            ('Check Results', {
                'fields': ('service_name', 'category', 'status', 'message', 'timestamp', 'execution_time_ms'),
            }),
            ('Technical Details', {
                'fields': ('details',),
                'classes': ('collapse',),
            }),
        )
    
    def service_name_with_tooltip(self, obj):
        """Display service name with short description tooltip."""
        short_desc, _ = self._get_service_descriptions(obj.service_name)
        
        return format_html(
            '<span title="{}" style="cursor: help; border-bottom: 1px dotted #999;">{}</span>',
            short_desc,
            obj.service_name
        )
    service_name_with_tooltip.short_description = 'Service Name'
    service_name_with_tooltip.admin_order_field = 'service_name'
    
    def colored_status(self, obj):
        """Display status with color coding."""
        return format_colored_status(obj.status)
    colored_status.short_description = 'Status'
    
    def has_add_permission(self, request):
        """Disable manual addition of health check results."""
        return False


class HealthCheckRunAdmin(admin.ModelAdmin):
    """Admin interface for health check runs."""
    
    list_display = [
        'timestamp',
        'trigger',
        'total_checks',
        'successful_checks',
        'failed_checks',
        'warning_checks',
        'total_execution_time_ms',
        'status_summary'
    ]
    list_filter = ['trigger', 'timestamp']
    readonly_fields = [
        'timestamp',
        'trigger',
        'total_checks',
        'successful_checks',
        'failed_checks',
        'warning_checks',
        'total_execution_time_ms'
    ]
    date_hierarchy = 'timestamp'
    
    def status_summary(self, obj):
        """Display summary with color coding."""
        if obj.failed_checks > 0:
            color = STATUS_COLORS['error']
            text = 'FAILURES'
        elif obj.warning_checks > 0:
            color = STATUS_COLORS['warning']
            text = 'WARNINGS'
        else:
            color = STATUS_COLORS['success']
            text = 'ALL PASSED'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            text
        )
    status_summary.short_description = 'Summary'
    
    def has_add_permission(self, request):
        """Disable manual addition of health check runs."""
        return False
    
    def get_urls(self):
        """Add custom URL for running health checks."""
        urls = super().get_urls()
        custom_urls = [
            path(
                'run-health-checks/',
                self.admin_site.admin_view(self.run_health_checks_view),
                name='monitoring_run_health_checks'
            ),
        ]
        return custom_urls + urls
    
    # Health Check Execution Methods
    
    def _create_sse_event(self, event_type: str, data: dict) -> str:
        """
        Create a Server-Sent Event formatted string.
        
        Args:
            event_type: Type of event ('start', 'running', 'progress', 'complete')
            data: Event data dictionary
            
        Returns:
            SSE formatted string
        """
        import json
        event_data = {'type': event_type, **data}
        return f"data: {json.dumps(event_data)}\n\n"
    
    def _update_check_stats(self, stats: dict, result_status: str) -> None:
        """Update check statistics based on result status."""
        if result_status == 'success':
            stats['successful'] += 1
        elif result_status == 'error':
            stats['failed'] += 1
        else:
            stats['warnings'] += 1
        stats['completed'] += 1
    
    def _stream_health_checks(self):
        """
        Generator that streams health check results as SSE events.
        
        Yields:
            SSE formatted strings for each check execution
        """
        import time
        from .runner import get_all_health_checks, run_single_health_check, save_health_check_results, RunSummary
        
        health_checks = get_all_health_checks()
        total = len(health_checks)
        stats = {'completed': 0, 'successful': 0, 'failed': 0, 'warnings': 0}
        results = []  # Store results for DB save
        start_time = time.time()
        
        # Initial event
        yield self._create_sse_event('start', {'total': total})
        
        # Execute and stream each check
        for check in health_checks:
            # Notify which check is running
            yield self._create_sse_event('running', {'service_name': check.service_name})
            
            # Execute check
            result = run_single_health_check(check)
            results.append(result)  # Store for DB save
            self._update_check_stats(stats, result.status.value)
            
            # Send progress with result
            yield self._create_sse_event('progress', {
                'completed': stats['completed'],
                'total': total,
                'check': result.to_dict(),
                'stats': {k: v for k, v in stats.items() if k != 'completed'}
            })
        
        # Save results to database
        summary = RunSummary.from_results(results)
        total_execution_time_ms = int((time.time() - start_time) * 1000)
        save_health_check_results(
            results=results,
            summary=summary,
            total_execution_time_ms=total_execution_time_ms,
            trigger='manual'
        )
        
        # Completion event
        yield self._create_sse_event('complete', {})
    
    def _handle_streaming_request(self):
        """Handle SSE streaming request."""
        from django.http import StreamingHttpResponse
        
        response = StreamingHttpResponse(
            self._stream_health_checks(),
            content_type='text/event-stream'
        )
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'
        return response
    
    def _handle_traditional_post(self):
        """Handle traditional form submission."""
        run_result = run_all_health_checks(trigger='manual')
        message, level = format_run_result_message(run_result)
        
        message_methods = {
            'error': messages.error,
            'warning': messages.warning,
            'success': messages.success
        }
        message_methods[level](self.request, message)
        
        return redirect('admin:monitoring_healthcheckrun_changelist')
    
    def run_health_checks_view(self, request):
        """
        View to manually trigger all health checks.
        
        Supports:
        - Server-Sent Events (SSE) for real-time streaming
        - Traditional form submission as fallback
        """
        self.request = request
        
        if request.method == 'POST':
            # SSE streaming request
            if request.headers.get('Accept') == 'text/event-stream':
                return self._handle_streaming_request()
            # Traditional form submission
            else:
                return self._handle_traditional_post()
        
        # GET request - show page
        return render(request, 'admin/monitoring/run_health_checks.html', {
            'title': 'Run Health Checks',
            'opts': self.model._meta,
            'has_permission': True,
        })


admin.site.register(HealthCheckResult, HealthCheckResultAdmin)
admin.site.register(HealthCheckRun, HealthCheckRunAdmin)
