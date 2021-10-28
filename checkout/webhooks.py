from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from checkout.webhook_handler import StripeWH_Handler
import json
import stripe


@require_POST
@csrf_exempt
def webhook(request):
    """
    Listen for webhooks from Stripe
    """
    # Setup
    stripe.api_key = settings.STRIPE_SECRET_KEY

    # Get webhook data and verify its signature
    payload = request.body
    event = None

    try:
        event = stripe.Event.construct_from(
            json.loads(payload), stripe.api_key
        )
    except ValueError as e:
        # Invalid payload
        return HttpResponse(content=e, status=400)
    except Exception as e:
        return HttpResponse(content=e, status=400)

    # Setup webhook handler
    handler = StripeWH_Handler(request)

    # Map webhook events to relevant hanldler functions
    event_map = {
        'payment_intent.succeeded': handler.handle_payment_intent_succeeded,
        'payment_intent.payment_failed': handler.handle_payment_intent_failed,
    }

    # Get webhook type from Stripe
    event_type = event['type']

    # If a handler exists, get it from the event map
    # Use generic handler by default
    event_handler = event_map.get(event_type, handler.handle_event)

    # Call the event handler with the event
    response = event_handler(event)
    return response
