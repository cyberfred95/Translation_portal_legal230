from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils import timezone
from django.utils.html import format_html
from django.urls import reverse
from .models import User
from .models import UserGroup
from stripe_webhooks.tasks_handlers.helper.stripe_session import get_stripe_customer_session_url
from subscriptions.permissions import is_user_subscription_active
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
                return format_html('<span style="color: red;">Error</span>')
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
    fields = ['name', 'admin']
    list_display = ('name', 'id', 'user_count')
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
    list_display = ('username', 'is_active', 'email',
                    'user_group', 'user_subscription', 'truncated_stripe_customer_id', 'stripe_session', 'formatted_date_joined')

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('email', 'uuid', 'stripe_customer_id', 'language')}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'group'),
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    readonly_fields = ['uuid']

    def formatted_date_joined(self, obj):
        """Display date_joined in DD/MM/YYYY format (local time)"""
        if obj.date_joined:
            local_time = timezone.localtime(obj.date_joined)
            return local_time.strftime('%d/%m/%Y')
        return '-'
    formatted_date_joined.short_description = 'Date Joined'
    formatted_date_joined.admin_order_field = 'date_joined'

    def truncated_stripe_customer_id(self, obj):
        """Display truncated stripe_customer_id (first 4 chars + [...] + last 4 chars)"""
        if obj.stripe_customer_id:
            customer_id = obj.stripe_customer_id
            if len(customer_id) > 8:
                return f"{customer_id[:4]}[...]{customer_id[-4:]}"
            return customer_id
        return '-'
    truncated_stripe_customer_id.short_description = 'Stripe Customer ID'
    truncated_stripe_customer_id.admin_order_field = 'stripe_customer_id'

    def user_group(self, obj):
        """Display user group name as clickable link"""
        if obj.group:
            return create_clickable_link(obj, 'users', 'usergroup', 'group')
        return '-'
    user_group.short_description = 'Group'
    user_group.admin_order_field = 'group'

    def user_subscription(self, obj):
        """Display user subscription with different states (only active subscriptions)"""
        all_subscriptions = obj.subscriptions.all()
        active_subscriptions = [
            sub for sub in all_subscriptions
            if is_user_subscription_active(sub.status)
        ]
        count = len(active_subscriptions)
        
        if count == 0:
            return format_html(
                '<span style="color: orange; font-weight: bold;">no subscription</span>'
            )
        elif count == 1:
            subscription = active_subscriptions[0]
            subscription_name = subscription.subscription.name
            url = reverse('admin:subscriptions_usersubscription_change', args=[subscription.pk])
            return format_html(
                '<a href="{}" style="font-weight: bold;">{}</a>',
                url, subscription_name
            )
        else:
            return format_html(
                '<span style="color: red; font-weight: bold;">multiples subscription</span>'
            )
    user_subscription.short_description = 'Subscription'
    user_subscription.admin_order_field = 'subscriptions'


# Register the User model with the custom admin class
admin.site.register(User, CustomUserAdmin)
