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
from .constants import STATUS_COLORS


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
    """Admin interface for health check results."""
    
    list_display = [
        'service_name',
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
            status = 'error'
            text = 'FAILURES'
        elif obj.warning_checks > 0:
            status = 'warning'
            text = 'WARNINGS'
        else:
            status = 'success'
            text = 'ALL PASSED'
        
        return format_colored_status(status.replace('error', 'red').replace('warning', 'orange').replace('success', 'green'))
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
    
    def run_health_checks_view(self, request):
        """View to manually trigger all health checks."""
        if request.method == 'POST':
            run_result = run_all_health_checks(trigger='manual')
            message, level = format_run_result_message(run_result)
            
            # Display appropriate message
            if level == 'error':
                messages.error(request, message)
            elif level == 'warning':
                messages.warning(request, message)
            else:
                messages.success(request, message)
            
            return redirect('admin:monitoring_healthcheckrun_changelist')
        
        # GET request - show confirmation page
        return render(request, 'admin/monitoring/run_health_checks.html', {
            'title': 'Run Health Checks',
            'opts': self.model._meta,
            'has_permission': True,
        })


admin.site.register(HealthCheckResult, HealthCheckResultAdmin)
admin.site.register(HealthCheckRun, HealthCheckRunAdmin)
