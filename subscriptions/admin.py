import stripe
from django.contrib import admin
from django.contrib import messages
from django.db import models
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import SubscriptionType, UserSubscription, CountHistory, CountMetered
from .tasks import process_daily_subscription_renewals
from .permissions import is_user_subscription_active
from .stripe_utils import (
    StripeCheckoutConfigurationError,
    create_metered_checkout_session,
    list_active_stripe_prices,
)
from legal.admin.utils import create_clickable_link


# Constants for translated fields (used in multiple admin classes)
TRANSLATED_FIELDS = (
    'translated_symbols_count',
    'translated_words_count',
    'translated_files_count',
)


def get_active_status_values():
    """
    Return the list of status values considered active (displayed in green).
    """
    active_statuses = []
    for choice in UserSubscription.UserSubscriptionChoices:
        value = getattr(choice, 'value', choice)
        if is_user_subscription_active(value):
            active_statuses.append(value)
    return active_statuses


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


@admin.register(CountMetered)
class CountMeteredAdmin(admin.ModelAdmin):
    list_display = (
        'date',
        'user_subscription',
        'reported',
        'stripe_usage_record_id',
        'daily_translated_symbols_count',
        'daily_translated_words_count',
        'daily_translated_files_count',
    )
    list_filter = ('date', 'reported')
    search_fields = ('user_subscription__user__email', 'stripe_usage_record_id')
    autocomplete_fields = ('user_subscription',)
    readonly_fields = (
        'daily_translated_symbols_count',
        'daily_translated_words_count',
        'daily_translated_files_count',
    )


class ActiveWithoutStripeFilter(admin.SimpleListFilter):
    title = 'Abonnement manuel'
    parameter_name = 'active_without_stripe'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'Abonnement manuel'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(
                status__in=get_active_status_values(),
                stripe_subscription_id__isnull=True,
            )
        return queryset


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
        'subscription', 'clickable_user', 'colored_status', 'user_type',
        'truncated_stripe_subscription_id', 'formatted_start_date', 'formatted_end_date'
    )
    list_filter = (
        ActiveWithoutStripeFilter, NoStripeCustomerFilter, 'status',
        'subscription', 'start_date', 'end_date'
    )
    search_fields = (
        'stripe_subscription_id', 'user__email', 'user__username'
    )
    ordering = ('-start_date',)

    change_list_template = "admin/subscriptions/usersubscription/change_list.html"

    def changelist_view(self, request, extra_context=None):
        """
        Inject custom context for the changelist template, including the number
        of active subscriptions (green status) without a Stripe ID.
        """
        extra_context = extra_context or {}
        active_statuses = get_active_status_values()
        extra_context["active_without_stripe_count"] = UserSubscription.objects.filter(
            status__in=active_statuses,
            stripe_subscription_id__isnull=True,
        ).count()
        extra_context["api_subscription_types"] = SubscriptionType.objects.filter(
            product_type=SubscriptionType.ProductChoices.API
        ).order_by("name")
        return super().changelist_view(request, extra_context=extra_context)

    def get_urls(self):
        """Add custom URLs for manual task execution."""
        urls = super().get_urls()
        custom_urls = [
            path('manual-renewal/', self.admin_site.admin_view(self.manual_renewal_view),
                 name='subscriptions_usersubscription_manual_renewal'),
            path(
                'api-prices/',
                self.admin_site.admin_view(self.api_prices_view),
                name='subscriptions_usersubscription_api_prices',
            ),
            path(
                'api-checkout/',
                self.admin_site.admin_view(self.checkout_session_view),
                name='subscriptions_usersubscription_checkout_session',
            ),
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

    def api_prices_view(self, request):
        """Return the Stripe price IDs for a given product."""
        product_id = request.GET.get('product_id')
        if not product_id:
            return JsonResponse({'error': 'product_id requis'}, status=400)

        try:
            prices = list_active_stripe_prices(product_id)
        except stripe.error.StripeError as exc:
            return JsonResponse({'error': str(exc)}, status=502)
        except Exception as exc:  # pragma: no cover - defensive
            return JsonResponse({'error': str(exc)}, status=500)

        return JsonResponse({'prices': prices})

    def checkout_session_view(self, request):
        """Create a Stripe Checkout session and redirect the admin to Stripe."""
        if request.method != 'POST':
            messages.error(request, "Méthode non autorisée.")
            return redirect('admin:subscriptions_usersubscription_changelist')

        price_id = request.POST.get('price_id')
        if not price_id:
            messages.error(request, "Veuillez sélectionner un Price ID.")
            return redirect('admin:subscriptions_usersubscription_changelist')

        # Check if SERPA (payment method collection) is required
        with_serpa = request.POST.get('with_serpa', 'true').lower() == 'true'

        try:
            session = create_metered_checkout_session(price_id, with_serpa=with_serpa)
        except StripeCheckoutConfigurationError as exc:
            messages.error(request, str(exc))
            return redirect('admin:subscriptions_usersubscription_changelist')
        except stripe.error.StripeError as exc:
            messages.error(request, f"Erreur Stripe : {exc}")
            return redirect('admin:subscriptions_usersubscription_changelist')

        return redirect(session.url)

    fieldsets = (
        (None, {
            'fields': ('user', 'subscription', 'status', 'stripe_subscription_id', 'api_key')
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

    def clickable_user(self, obj):
        """Create a clickable link to the User admin page"""
        return create_clickable_link(obj, 'users', 'user', 'user')
    clickable_user.short_description = 'User'
    clickable_user.admin_order_field = 'user__username'

    def user_type(self, obj):
        """Display user type with colors: Buyer in gold, Licence in cyan"""
        if obj.user.stripe_customer_id:
            return format_html(
                '<span style="color: #FFD700; font-weight: bold;">Buyer</span>'
            )
        return format_html(
            '<span style="color: #00CED1; font-weight: bold;">Licence</span>'
        )
    user_type.short_description = "Type"

    def colored_status(self, obj):
        """Display status in green if subscription is active, red otherwise"""
        status_display = obj.get_status_display()
        if is_user_subscription_active(obj.status):
            return format_html(
                '<span style="color: green; font-weight: bold;">{}</span>',
                status_display
            )
        return format_html(
            '<span style="color: red; font-weight: bold;">{}</span>',
            status_display
        )
    colored_status.short_description = 'Status'
    colored_status.admin_order_field = 'status'

    def formatted_start_date(self, obj):
        """Display start_date in DD/MM/YYYY format"""
        if obj.start_date:
            return obj.start_date.strftime('%d/%m/%Y')
        return '-'
    formatted_start_date.short_description = 'Start Date'
    formatted_start_date.admin_order_field = 'start_date'

    def formatted_end_date(self, obj):
        """Display end_date in DD/MM/YYYY format"""
        if obj.end_date:
            return obj.end_date.strftime('%d/%m/%Y')
        return '-'
    formatted_end_date.short_description = 'End Date'
    formatted_end_date.admin_order_field = 'end_date'

    def truncated_stripe_subscription_id(self, obj):
        """Display truncated stripe_subscription_id (first 4 chars + [...] + last 4 chars)"""
        if obj.stripe_subscription_id:
            subscription_id = obj.stripe_subscription_id
            if len(subscription_id) > 8:
                return f"{subscription_id[:4]}[...]{subscription_id[-4:]}"
            return subscription_id
        return '-'
    truncated_stripe_subscription_id.short_description = 'Stripe Subscription ID'
    truncated_stripe_subscription_id.admin_order_field = 'stripe_subscription_id'


class UserSubscriptionInline(admin.TabularInline):
    """Inline display of UserSubscriptions for a SubscriptionType."""
    model = UserSubscription
    fields = ('clickable_user', 'clickable_status', 'start_date', 'end_date', 'stripe_subscription_id')
    readonly_fields = ('clickable_user', 'clickable_status', 'start_date', 'end_date', 'stripe_subscription_id')
    extra = 0
    can_delete = False
    can_add = False
    ordering = ('-start_date',)

    def clickable_user(self, obj):
        """Create a clickable link to the User admin page"""
        return create_clickable_link(obj, 'users', 'user', 'user')
    clickable_user.short_description = 'User'
    clickable_user.admin_order_field = 'user__username'

    def clickable_status(self, obj):
        """Create a clickable link to the UserSubscription admin page"""
        return create_clickable_link(obj, 'subscriptions', 'usersubscription', display_field='status')
    clickable_status.short_description = 'Status'
    clickable_status.admin_order_field = 'status'

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(SubscriptionType)
class SubscriptionTypeAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'stripe', 'product_type', 'user_subscription_count', 'formatted_price', 'symbols', 'word', 'files', 'glossaries'
    )
    search_fields = ('name',)
    inlines = [UserSubscriptionInline]

    def stripe(self, obj):
        """Display Stripe logo if Stripe Product ID exists"""
        if obj.stripe_product_id:
            return mark_safe(f'<i class="ph ph-stripe-logo" style="color: #635bff; font-size: 1.5em;" title="{obj.stripe_product_id}"></i>')
        return "-"
    stripe.short_description = 'STRIPE'
    stripe.admin_order_field = 'stripe_product_id'

    def product_type(self, obj):
        """Display the product type choice"""
        return obj.get_product_type_display()
    product_type.short_description = 'TYPE'
    product_type.admin_order_field = 'product_type'

    class Media:
        css = {
            'all': (
                'https://unpkg.com/@phosphor-icons/web@2.0.3/src/regular/style.css',
            )
        }

    def formatted_price(self, obj):
        """Display price with custom formatting and 2 decimal places"""
        return f"{obj.price:,.2f}".replace(",", " ") + " €"
    formatted_price.short_description = 'PRICE'
    formatted_price.admin_order_field = 'price'

    def symbols(self, obj):
        """Display max_symbols_count with custom column name and formatting"""
        if obj.max_symbols_count == -1:
            return "∞"
        return f"{obj.max_symbols_count:,}".replace(",", " ")
    symbols.short_description = 'SYMBOLS'
    symbols.admin_order_field = 'max_symbols_count'

    def word(self, obj):
        """Display max_words_count with custom column name and formatting"""
        if obj.max_words_count == -1:
            return "∞"
        return f"{obj.max_words_count:,}".replace(",", " ")
    word.short_description = 'WORD'
    word.admin_order_field = 'max_words_count'

    def files(self, obj):
        """Display max_files_count with custom column name and formatting"""
        if obj.max_files_count == -1:
            return "∞"
        return f"{obj.max_files_count:,}".replace(",", " ")
    files.short_description = 'FILES'
    files.admin_order_field = 'max_files_count'

    def glossaries(self, obj):
        """Display custom_glossaries_count with custom column name and formatting"""
        if obj.custom_glossaries_count == -1:
            return "∞"
        return f"{obj.custom_glossaries_count:,}".replace(",", " ")
    glossaries.short_description = 'GLOSSARIES'
    glossaries.admin_order_field = 'custom_glossaries_count'

    def user_subscription_count(self, obj):
        """Display count of UserSubscription for this SubscriptionType"""
        count = UserSubscription.objects.filter(subscription=obj).count()
        return count
    user_subscription_count.short_description = 'SUBSCRIBERS'
    user_subscription_count.admin_order_field = 'user_subscription_count'
