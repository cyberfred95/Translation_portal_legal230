"""
Success message templates for Stripe webhook responses.

This module defines HTTP status codes and success message templates used
throughout the Stripe webhook system. Each template includes a formatted
message and corresponding HTTP status code for consistent response handling.
"""

# HTTP status codes for success responses
CODE_OK = 200
CODE_CREATED = 201
CODE_PARTIAL_CONTENT = 206

SUCCESS_MESSAGES_TEMPLATE: dict[str, dict[str, str | int]] = {
    # Checkout session messages
    "checkout_session_completed": {
        "message": "Checkout session completed successfully",
        "code": CODE_OK
    },

    # Customer operation messages
    "customer_created": {
        "message": "Customer created successfully",
        "code": CODE_CREATED
    },
    "customer_updated": {
        "message": "Customer updated successfully",
        "code": CODE_OK
    },
    "customer_identical": {
        "message": "Nothing to update in User '{username}'",
        "code": CODE_OK
    },
    "customer_deleted": {
        "message": "Customer deleted successfully",
        "code": CODE_OK
    },

    # Customer subscription operation messages
    "customer_subscription_created": {
        "message": "({quantity}) UserSubscription stripe id '{stripe_subscription_id}' "
        "created with status {status} ({payload_status})",
        "code": CODE_CREATED
    },
    "customer_subscription_updated": {
        "message": "({quantity}) UserSubscription stripe id '{stripe_subscription_id}' "
        "updated: status={status} ({payload_status}), changed_fields=[{changed_fields}]",
        "code": CODE_OK
    },
    "customer_subscription_identical": {
        "message": "Nothing to update in UserSubscription stripe id '{stripe_subscription_id}'",
        "code": CODE_OK
    },
    "customer_subscription_deleted": {
        "message": "({quantity}) UserSubscription stripe id '{stripe_subscription_id}' "
        "and their respective User are deactivated",
        "code": CODE_OK
    },
    "customer_subscription_trial_will_end": {
        "message": "Customer subscription trial will end",
        "code": CODE_OK
    },
    "customer_subscription_trial_will_end_no_email": {
        "message": "User subscription trial will end, but user(s) '{username_list}' "
        "ha(s/ve) no email",
        "code": CODE_PARTIAL_CONTENT
    },

    # Customer tax ID operation messages
    "customer_tax_id_created": {
        "message": "User with stripe id '{stripe_customer_id}', is now attached "
        "to group '{group_name}'",
        "code": CODE_CREATED
    },
    "customer_tax_id_created_temporary": {
        "message": "User with stripe id '{stripe_customer_id}', not found, "
        "a temporary group has been created",
        "code": CODE_CREATED
    },

    # Invoice operation messages
    "invoice_payment_succeeded": {
        "message": "Invoice payment succeeded",
        "code": CODE_OK
    },
    "invoice_payment_failed": {
        "message": "Invoice payment failed",
        "code": CODE_OK
    },
    "invoice_payment_action_required": {
        "message": "Invoice payment action required",
        "code": CODE_OK
    },
    "invoice_upcoming": {
        "message": "Invoice upcoming",
        "code": CODE_OK
    },


    # Payment method operation messages
    "invoice_payment_succeeded": {
        "message": "Invoice payment succeeded, all userSubscriptions with the stripe_id '{stripe_subscription_id}' has been reset, creating {countHistory_count} countHistory records",
        "code": CODE_CREATED
    },

    # Idempotency messages
    "event_already_processed": {
        "message": "Event '{event_id}' already processed successfully, skipping",
        "code": CODE_OK
    },
}
