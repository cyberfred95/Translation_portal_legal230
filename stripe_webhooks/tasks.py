"""
Celery tasks for processing Stripe webhook events.

This module defines the main task for handling incoming Stripe webhook events,
including event validation, storage, and delegation to appropriate handlers
based on the event type.
"""

from datetime import datetime

from celery import shared_task
from pytz import timezone as pytz_timezone

from .models import StripeEvent
from .tasks_handlers.customer_handlers import CUSTOMER_EVENT_HANDLERS
from .tasks_handlers.customer_subscription_handlers import CUSTOMER_SUBSCRIPTION_EVENT_HANDLERS
from .tasks_handlers.customer_tax_id_handlers import CUSTOMER_TAX_ID_EVENT_HANDLERS
from .tasks_handlers.invoice_payment_succeeded import INVOICE_EVENT_HANDLERS
from .tasks_handlers.error.error import HttpResponse, error_message, exception_error

# Combine all event handlers into a single registry
EVENT_HANDLERS = {
    **CUSTOMER_EVENT_HANDLERS,
    **CUSTOMER_SUBSCRIPTION_EVENT_HANDLERS,
    **CUSTOMER_TAX_ID_EVENT_HANDLERS,
    **INVOICE_EVENT_HANDLERS
}


def handle_default_event(event_type: str) -> HttpResponse:
    return error_message("unknown_event", event_type=event_type)


@shared_task
def handle_event(event: dict) -> HttpResponse:
    """
    Main task for processing Stripe webhook events.

    This function processes incoming Stripe webhook events by:
    1. Extracting event metadata
    2. Cleaning up any existing event records with the same ID
    3. Creating a new event record in the database
    4. Delegating to the appropriate handler based on event type
    5. Updating the event record with the processing result

    Args:
        event (dict): The complete Stripe webhook event payload.

    Returns:
        HttpResponse: Result of the event processing.
    """
    # Extract event metadata
    event_type = str(event.get('type', ''))
    data = event.get('data', {})
    status = data.get('object', {}).get('status', None)
    created_at = event.get('created', None)
    event_id = event.get('id', '')

    # Clean up any existing event record with the same ID
    try:
        existing_event = StripeEvent.objects.filter(event_id=event_id).first()
        if existing_event:
            existing_event.delete()
    except Exception as error:
        return exception_error(error)

    # Create new event record
    try:
        created_datetime = None
        if created_at:
            created_datetime = datetime.fromtimestamp(
                created_at,
                tz=pytz_timezone('Europe/Paris')
            )

        event_record = StripeEvent.objects.create(
            event_id=event_id,
            event_type=event_type,
            data=data,
            status=status,
            created_at=created_datetime
        )
    except Exception as error:
        return exception_error(error)

    # Get appropriate handler and process the event
    handler = EVENT_HANDLERS.get(
        event_type,
        lambda payload: handle_default_event(event_type)
    )
    result = handler(data.get('object', {}))

    # Update event record with processing result
    try:
        event_record.code_response = result.code
        event_record.http_response = {
            "message": result.message,
            "exception": str(result.exception) if result.exception else None
        }
        event_record.save()
    except Exception as error:
        return exception_error(error)

    return result
