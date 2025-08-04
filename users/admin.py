from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import User
from .models import UserGroup
from stripe_webhooks.tasks_handlers.helper.stripe_session import get_stripe_customer_session_url
from legal.admin.utils import create_clickable_link


class UserDisplayMixin:
    """Mixin for common user display methods."""

    def language_code(self, obj):
        return obj.language
    language_code.short_description = 'Language'

    def stripe_session(self, obj):
        if obj.stripe_customer_id:
            error_response, session_url = get_stripe_customer_session_url(
                obj.stripe_customer_id)
            if error_response:
                return format_html('<span style="color: red;">{error_response}</span>')
            return format_html(
                '<a href="{}" target="_blank" style="background-color: #635bff; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px;">Stripe</a>',
                session_url
            )
        return '-'
    stripe_session.short_description = 'Stripe Link'


class UserInline(UserDisplayMixin, admin.TabularInline):
    """Inline display of users in a group."""
    model = User
    fields = ('clickable_username', 'is_active', 'email', 'first_name', 'last_name',
              'language_code', 'stripe_customer_id', 'stripe_session', 'date_joined')
    readonly_fields = ('clickable_username', 'is_active', 'email', 'first_name', 'last_name',
                       'language_code', 'stripe_customer_id', 'stripe_session', 'date_joined')
    extra = 0
    can_delete = False

    def clickable_username(self, obj):
        """Create a clickable link to the User admin page"""
        return create_clickable_link(obj, 'users', 'user', display_field='username')
    clickable_username.short_description = 'Username'
    clickable_username.admin_order_field = 'username'

    def has_add_permission(self, request, obj=None):
        return False


class UserGroupAdmin(admin.ModelAdmin):
    fields = ['name', 'api_key', 'admin']
    list_display = ('name', 'user_count')
    inlines = [UserInline]

    def user_count(self, obj):
        """Display the number of users associated with this group"""
        count = obj.user_set.count()
        return f"{count} user{'s' if count != 1 else ''}"
    user_count.short_description = 'Number of users'
    user_count.admin_order_field = 'user_count'


admin.site.register(UserGroup, UserGroupAdmin)


class CustomUserAdmin(UserDisplayMixin, UserAdmin):
    ordering = ('-date_joined',)
    list_display = ('username', 'is_active', 'email', 'first_name',
                    'last_name', 'language_code', 'stripe_customer_id', 'stripe_session', 'date_joined')

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('email', 'uuid', 'language')}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'group'),
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    readonly_fields = ['uuid']


# Register the User model with the custom admin class
admin.site.register(User, CustomUserAdmin)
