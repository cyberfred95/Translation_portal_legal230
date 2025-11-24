import logging

from django.utils.timezone import now

from subscriptions.models import SubscriptionType


logger = logging.getLogger(__name__)


def translation_allowed(request, symbols_count: int, words_count: int, files_count: int = None) -> bool:
    if request.user.is_staff:
        return True

    user_subscription = request.user.subscriptions.first()

    def files_allowed() -> bool:
        if user_subscription.max_files_count < 0 or user_subscription.translated_files_count + files_count < user_subscription.max_files_count:
            return True

        return False

    def words_allowed() -> bool:
        if user_subscription.max_words_count < 0 or user_subscription.translated_words_count + words_count < user_subscription.max_words_count:
            return True
        return False

    def symbols_allowed() -> bool:
        if user_subscription.max_symbols_count < 0 or user_subscription.translated_symbols_count + symbols_count < user_subscription.max_symbols_count:
            return True
        return False

    if files_count:
        if files_allowed() and words_allowed() and symbols_allowed():
            return True
        else:
            return False
    else:

        if words_allowed() and symbols_allowed():
            return True
        else:
            return False


def add_translations(request, words_count: int, symbols_count: int, files_count: int = None):
    if not request.user.group:
        return

    user_subscription = request.user.subscriptions.first()
    if not user_subscription:
        return

    _increment_subscription_totals(
        user_subscription,
        words_count,
        symbols_count,
        files_count,
    )

    if _is_api_subscription(user_subscription):
        _increment_daily_metered_usage(
            user_subscription,
            words_count,
            symbols_count,
            files_count,
        )


def _increment_subscription_totals(user_subscription, words_count, symbols_count, files_count):
    user_subscription.translated_words_count += words_count
    user_subscription.translated_symbols_count += symbols_count
    update_fields = [
        'translated_words_count',
        'translated_symbols_count',
    ]

    if files_count:
        user_subscription.translated_files_count += files_count
        update_fields.append('translated_files_count')

    user_subscription.save(update_fields=update_fields)


def _increment_daily_metered_usage(user_subscription, words_count, symbols_count, files_count):
    count_metered = _get_active_metered_entry(user_subscription)
    if not count_metered:
        return

    count_metered.daily_translated_words_count += words_count
    count_metered.daily_translated_symbols_count += symbols_count

    update_fields = [
        'daily_translated_words_count',
        'daily_translated_symbols_count',
    ]

    if files_count:
        count_metered.daily_translated_files_count += files_count
        update_fields.append('daily_translated_files_count')

    count_metered.save(update_fields=update_fields)


def _get_active_metered_entry(user_subscription):
    try:
        count_metered = user_subscription.get_today_count_metered()
    except ValueError as error:
        logger.error(
            "Multiple CountMetered entries detected for subscription %s: %s",
            user_subscription.id,
            error,
        )
        return None

    if count_metered is None:
        logger.error(
            "No CountMetered entry found for subscription %s on %s.",
            user_subscription.id,
            now().date(),
        )
        return None

    if count_metered.reported:
        logger.error(
            "Attempt to update already reported CountMetered for subscription %s on %s.",
            user_subscription.id,
            count_metered.date,
        )
        return None

    return count_metered


def _is_api_subscription(user_subscription):
    return (
        user_subscription.subscription
        and user_subscription.subscription.product_type == SubscriptionType.ProductChoices.API
    )
