from django.contrib import admin
from django.urls import reverse, path
from django.utils.html import format_html
from django.shortcuts import redirect
from django.contrib import messages
from django.http import JsonResponse
from django.db import models
from .models import SubscriptionType, UserSubscription, CountHistory
from .tasks import process_daily_subscription_renewals
from legal.admin.utils import create_clickable_link


# Constants for translated fields (used in multiple admin classes)
TRANSLATED_FIELDS = ('translated_symbols_count',
                     'translated_words_count', 'translated_files_count')


@admin.register(CountHistory)
class CountHistoryAdmin(admin.ModelAdmin):
    list_display = (
        'formatted_start_date', 'clickable_user_subscription', 'clickable_subscription_type',
        'custom_symbols_count', 'custom_words_count', 'custom_files_count'
    )

    readonly_fields = ('start_date', 'clickable_user_subscription',
                       'clickable_subscription_type') + TRANSLATED_FIELDS

    fieldsets = (
        (None, {
            'fields': ('start_date', 'clickable_user_subscription', 'clickable_subscription_type')
        }),
        ('Translated Statistics', {
            'fields': (TRANSLATED_FIELDS,)
        }),
    )

    search_fields = ('user_subscription__user__email',
                     'subscription_type__name')
    list_filter = ('subscription_type', 'start_date')

    def formatted_start_date(self, obj):
        """Format start_date to display month/year (day)"""
        return obj.start_date.strftime('%m/%y (%d)') if obj.start_date else '-'
    formatted_start_date.short_description = 'Start Date'
    formatted_start_date.admin_order_field = 'start_date'

    def clickable_user_subscription(self, obj):
        """Create a clickable link to the UserSubscription admin page"""
        return create_clickable_link(obj, 'subscriptions', 'usersubscription', 'user_subscription')
    clickable_user_subscription.short_description = 'User Subscription'
    clickable_user_subscription.admin_order_field = 'user_subscription'

    def clickable_subscription_type(self, obj):
        """Create a clickable link to the SubscriptionType admin page"""
        return create_clickable_link(obj, 'subscriptions', 'subscriptiontype', 'subscription_type')
    clickable_subscription_type.short_description = 'Subscription Type'
    clickable_subscription_type.admin_order_field = 'subscription_type'

    def custom_symbols_count(self, obj):
        """Display translated_symbols_count with custom column name"""
        return obj.translated_symbols_count
    custom_symbols_count.short_description = 'Symbols'
    custom_symbols_count.admin_order_field = 'translated_symbols_count'

    def custom_words_count(self, obj):
        """Display translated_words_count with custom column name"""
        return obj.translated_words_count
    custom_words_count.short_description = 'Words'
    custom_words_count.admin_order_field = 'translated_words_count'

    def custom_files_count(self, obj):
        """Display translated_files_count with custom column name"""
        return obj.translated_files_count
    custom_files_count.short_description = 'Files'
    custom_files_count.admin_order_field = 'translated_files_count'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


class NoStripeCustomerFilter(admin.SimpleListFilter):
    title = 'User Type'
    parameter_name = 'user_type'

    def lookups(self, request, model_admin):
        return (
            ('licence', 'Licence'),
            ('buyer', 'Buyer'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'licence':
            return queryset.filter(user__stripe_customer_id__isnull=True)
        elif self.value() == 'buyer':
            return queryset.filter(user__stripe_customer_id__isnull=False)
        return queryset


@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'subscription', 'status', 'user_type',
        'start_date', 'end_date', 'stripe_subscription_id'
    )
    list_filter = (
        NoStripeCustomerFilter, 'status', 'subscription',
        'start_date', 'end_date'
    )
    search_fields = (
        'stripe_subscription_id', 'user__email', 'user__username'
    )
    ordering = ('-start_date',)

    change_list_template = "admin/subscriptions/usersubscription/change_list.html"

    def get_urls(self):
        """Add custom URLs for manual task execution."""
        urls = super().get_urls()
        custom_urls = [
            path('manual-renewal/', self.admin_site.admin_view(self.manual_renewal_view),
                 name='subscriptions_usersubscription_manual_renewal'),
        ]
        return custom_urls + urls

    def manual_renewal_view(self, request):
        """Execute the daily subscription renewal task manually."""
        if request.method == 'POST':
            try:
                # Execute the task synchronously
                result = process_daily_subscription_renewals()

                # Add success message with results
                messages.success(
                    request,
                    f"Manual renewal completed successfully! "
                    f"Renewed: {result['renewed_count']}, "
                    f"Errors: {result['error_count']}, "
                    f"Total processed: {result['total_processed']}"
                )
            except Exception as e:
                messages.error(
                    request, f"Error during manual renewal: {str(e)}")

        return redirect('admin:subscriptions_usersubscription_changelist')

    fieldsets = (
        (None, {
            'fields': ('user', 'subscription', 'status', 'stripe_subscription_id')
        }),
        ('Allowed Limits', {
            'fields': (
                'max_symbols_count', 'max_words_count',
                'max_files_count', 'custom_glossaries_count'
            )
        }),
        ('Translated Statistics', {
            'fields': TRANSLATED_FIELDS
        }),
        ('Access Permissions', {
            'fields': (
                'access_to_writing', 'access_to_official_glossaries',
                'access_to_sso'
            )
        }),
        ('Dates', {
            'fields': ('start_date', 'end_date')
        }),
    )

    readonly_fields = TRANSLATED_FIELDS

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Filter available users to exclude those who already have a subscription."""
        if db_field.name == "user":
            # Get users who already have a subscription
            users_with_subscription = UserSubscription.objects.filter(
                user__isnull=False
            ).values_list('user_id', flat=True)

            # Check if we're editing an existing subscription
            current_user_id = None
            if hasattr(request, 'resolver_match') and request.resolver_match:
                if 'object_id' in request.resolver_match.kwargs:
                    try:
                        current_subscription = UserSubscription.objects.get(
                            pk=request.resolver_match.kwargs['object_id']
                        )
                        if current_subscription.user:
                            current_user_id = current_subscription.user.id
                    except UserSubscription.DoesNotExist:
                        pass

            # Filter out users with subscriptions, but include the current user if editing
            if current_user_id:
                # For edit page: exclude other users with subscriptions, but include current user
                kwargs["queryset"] = db_field.related_model.objects.filter(
                    models.Q(id=current_user_id) | ~models.Q(
                        id__in=users_with_subscription)
                )
            else:
                # For add page: exclude all users with subscriptions
                kwargs["queryset"] = db_field.related_model.objects.exclude(
                    id__in=users_with_subscription
                )

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def user_type(self, obj):
        return "Buyer" if obj.user.stripe_customer_id else "Licence"
    user_type.short_description = "Type"


@admin.register(SubscriptionType)
class SubscriptionTypeAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'price', 'max_symbols_count',
        'max_words_count', 'max_files_count', 'custom_glossaries_count', 'id'
    )
    search_fields = ('name',)
