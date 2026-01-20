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
