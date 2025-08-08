
"""
Handlers for resetting user subscription counters and creating count history records.

This module provides functions to reset counters on UserSubscription objects and to create CountHistory records for audit and tracking purposes.
"""

from subscriptions.models import UserSubscription, CountHistory
from .set_userSubscription import reset_userSubscription_counts
from ..error.error import HttpResponse, exception_error


def reset_subscriptions(
    user_subscription_list: list[UserSubscription],
) -> tuple[HttpResponse | None, list[CountHistory] | None]:
    """
    Reset counters and create a count history record for each UserSubscription.

    Args:
        user_subscription_list (list[UserSubscription]): List of UserSubscription objects to process.

    Returns:
        tuple[HttpResponse | None, list[CountHistory] | None]:
            Error response and None if an error occurs, otherwise None and the list of created CountHistory objects.
    """
    count_histories = []
    try:
        for user_subscription in user_subscription_list:
            # Create a CountHistory record for the current UserSubscription
            error_response, count_history = create_countHistory(
                user_subscription)
            if error_response:
                return error_response, None
            count_histories.append(count_history)
            # Reset the counters on the UserSubscription
            error_response, _ = reset_userSubscription_counts(
                user_subscription)
            if error_response:
                return error_response, None
        return None, count_histories
    except Exception as error:
        return exception_error(error), None


def create_countHistory(
    user_subscription: UserSubscription,
) -> tuple[HttpResponse | None, CountHistory | None]:
    """
    Create a CountHistory record for a given UserSubscription.

    Args:
        user_subscription (UserSubscription): The UserSubscription instance for which to create the history.

    Returns:
        tuple[HttpResponse | None, CountHistory | None]:
            Error response and None if an error occurs, otherwise None and the created CountHistory object.
    """
    try:
        # Create a new CountHistory record for the given UserSubscription
        count_history = CountHistory.objects.create(
            user_subscription=user_subscription,
            subscription_type=user_subscription.subscription,
            start_date=user_subscription.start_date,
            translated_symbols_count=user_subscription.translated_symbols_count,
            translated_words_count=user_subscription.translated_words_count,
            translated_files_count=user_subscription.translated_files_count
        )
        count_history.save()
        return None, count_history
    except Exception as error:
        return exception_error(error), None
