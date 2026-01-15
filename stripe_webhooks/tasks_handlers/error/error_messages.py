"""
Error message templates for Stripe webhook responses.

This module defines HTTP status codes and error message templates used
throughout the Stripe webhook system. Each template includes a formatted
error message and corresponding HTTP status code for consistent error handling.
"""

# HTTP status codes for error responses
CODE_BAD_REQUEST = 400
CODE_NOT_FOUND = 404
CODE_INTERNAL_ERROR = 500
CODE_NOT_IMPLEMENTED = 501
CODE_UNKNOWN_ERROR = 520

ERROR_MESSAGES_TEMPLATE: dict[str, dict[str, str | int]] = {
    # Payload validation errors
    "unknown_event": {
        "message": "Unknown event type '{event_type}'",
        "code": CODE_NOT_IMPLEMENTED
    },
    "not_found_id": {
        "message": "Id in payload not found",
        "code": CODE_BAD_REQUEST
    },
    "not_found_customer_id": {
        "message": "Customer id in payload not found",
        "code": CODE_BAD_REQUEST
    },
    "not_found_name": {
        "message": "Name in payload not found",
        "code": CODE_BAD_REQUEST
    },
    "not_found_item_data": {
        "message": "Item data in payload not found",
        "code": CODE_BAD_REQUEST
    },
    "not_found_status": {
        "message": "Status in payload not found",
        "code": CODE_BAD_REQUEST
    },
    "not_found_cancel_at": {
        "message": "Cancel at in payload not found",
        "code": CODE_BAD_REQUEST
    },
    "not_found_ended_at": {
        "message": "Ended at in payload not found",
        "code": CODE_BAD_REQUEST
    },
    "not_found_email": {
        "message": "Email in payload not found",
        "code": CODE_BAD_REQUEST
    },
    "not_found_language": {
        "message": "Language in payload not found",
        "code": CODE_BAD_REQUEST
    },
    "not_found_quantity": {
        "message": "Quantity in payload item data not found",
        "code": CODE_BAD_REQUEST
    },
    "not_found_current_period_start": {
        "message": "Current period start in payload item data not found",
        "code": CODE_BAD_REQUEST
    },
    "not_found_current_period_end": {
        "message": "Current period end in payload item data not found",
        "code": CODE_BAD_REQUEST
    },
    "not_found_stripe_product_id": {
        "message": "Stripe product id in payload item data not found",
        "code": CODE_BAD_REQUEST
    },
    "not_found_subscription_item_id": {
        "message": "Subscription item id in payload item data not found",
        "code": CODE_BAD_REQUEST
    },
    "not_found_interval": {
        "message": "Interval in payload item data not found",
        "code": CODE_BAD_REQUEST
    },
    "invalid_interval": {
        "message": "Invalid interval '{interval}' in payload item data, must be one of: week, month, year",
        "code": CODE_BAD_REQUEST
    },

    # Database lookup errors
    "not_found_user_by_stripe_customer_id": {
        "message": "User with stripe_customer_id '{stripe_customer_id}' not found",
        "code": CODE_NOT_FOUND
    },
    "not_found_subscriptionType_by_stripe_product_id": {
        "message": "SubscriptionType with stripe_product_id '{stripe_product_id}' not found",
        "code": CODE_NOT_FOUND
    },
    "not_found_userSubscription_by_stripe_subscription_id": {
        "message": "UserSubscription with stripe_subscription_id '{stripe_subscription_id}' not found",
        "code": CODE_NOT_FOUND
    },
    "not_found_userGroup_by_group_name": {
        "message": "UserGroup with name '{group_name}' not found",
        "code": CODE_NOT_FOUND
    },
    "not_found_userGroup_by_id": {
        "message": "UserGroup with id '{group_id}' not found",
        "code": CODE_NOT_FOUND
    },
    "not_found_emailSettings_by_email_type_and_language": {
        "message": "EmailSettings with email_type '{email_type}' and language '{language}' not found",
        "code": CODE_NOT_FOUND
    },
    "not_found_userSubscriptions_active": {
        "message": "No active userSubscriptions found for stripe_subscription_id '{stripe_subscription_id}'",
        "code": CODE_NOT_FOUND
    },
    "not_found_subscription_for_user": {
        "message": "No subscription found for user with stripe_customer_id '{user_stripe_customer_id}'",
        "code": CODE_NOT_FOUND
    },
    "multiple_subscriptions_found_for_user": {
        "message": "Multiple subscriptions ({subscription_count}) found for user with stripe_customer_id '{user_stripe_customer_id}', expected exactly one",
        "code": CODE_BAD_REQUEST
    },
    "no_stripe_subscription_id_for_user": {
        "message": "User subscription exists but has no stripe_subscription_id for user with stripe_customer_id '{user_stripe_customer_id}'",
        "code": CODE_INTERNAL_ERROR
    },

    # Business logic validation errors
    "user_count_from_userGroup_by_group_id": {
        "message": "User count from UserGroup with id '{group_id}' is 0",
        "code": CODE_INTERNAL_ERROR
    },
    "buyer_count_from_userSubscription_list": {
        "message": "{found_amount} buyer(s) found in userSubscription list ({strip_subscription_id})",
        "code": CODE_INTERNAL_ERROR
    },
    "quantity_user_subscription_invalid": {
        "message": "Invalid quantity '{quantity}' for user subscription, must be a positive integer > 0",
        "code": CODE_BAD_REQUEST
    },
    "invalid_customer_id": {
        "message": "Invalid customer_id: cannot be empty or None",
        "code": CODE_BAD_REQUEST
    },

    # General system errors
    "exception": {
        "message": "An exception occurred in function '{function_name}': {exception_type} - {exception_message}",
        "code": CODE_INTERNAL_ERROR
    },
}
