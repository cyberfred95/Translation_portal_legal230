"""
Django Admin Utilities for Legal230 Application

This module provides utility functions for Django admin interfaces
across all applications in the Legal230 project.
"""

from django.urls import reverse
from django.utils.html import format_html


def create_clickable_link(obj, app_label, model_name, field_name=None, display_field=None):
    """
    Create a clickable link for Django admin to navigate to objects.

    Args:
        obj: The Django model instance
        app_label: The Django app label for the target model
        model_name: The model name for the target object
        field_name: Optional. The field name to access a related object. 
                   If None, creates a link to the object itself.
        display_field: Optional. The field name to display as text. 
                      If None, uses str(target_obj).

    Returns:
        str: HTML formatted clickable link or '-' if no object

    Examples:
        # Link to a related object
        def clickable_user_subscription(self, obj):
            return create_clickable_link(obj, 'subscriptions', 'usersubscription', 'user_subscription')

        # Link to the object itself with custom display field
        def clickable_username(self, obj):
            return create_clickable_link(obj, 'users', 'user', display_field='username')

        # Link to the object itself with default display
        def clickable_name(self, obj):
            return create_clickable_link(obj, 'users', 'user')
    """
    # Determine target object
    if field_name:
        # Access related object via field_name
        target_obj = getattr(obj, field_name, None)
    else:
        # Use the object itself
        target_obj = obj

    if target_obj:
        url = reverse(
            f'admin:{app_label}_{model_name}_change', args=[target_obj.pk])

        # Determine display text
        if display_field:
            display_text = getattr(target_obj, display_field, str(target_obj))
        else:
            display_text = str(target_obj)

        return format_html('<a href="{}" style="font-weight: bold;">{}</a>', url, display_text)

    return '-'
