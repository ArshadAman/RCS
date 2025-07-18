from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .models import Payment, Plan
from .serializers import PaymentSerializer
import logging

logger = logging.getLogger(__name__)

@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def paypal_webhook(request):
    """Handle PayPal webhook events to verify payment status and update plan."""
    event = request.data
    event_type = event.get('event_type')
    resource = event.get('resource', {})
    order_id = resource.get('id')
    logger.info(f"Received PayPal webhook: {event_type} for order {order_id}")
    if not order_id:
        return Response({'error': 'No order id'}, status=400)
    try:
        payment = Payment.objects.get(paypal_order_id=order_id)
    except Payment.DoesNotExist:
        return Response({'error': 'Payment not found'}, status=404)
    # Handle completed payment
    if event_type == 'CHECKOUT.ORDER.APPROVED' or event_type == 'PAYMENT.CAPTURE.COMPLETED':
        payment.status = 'completed'
        payment.save()
        # Upgrade plan
        plan, _ = Plan.objects.get_or_create(company=payment.company)
        plan.plan_type = payment.plan_type
        if plan.plan_type == 'basic':
            plan.review_limit = 50
        elif plan.plan_type == 'standard':
            plan.review_limit = 500
        elif plan.plan_type == 'premium':
            plan.review_limit = 5000
        plan.save()
    elif event_type == 'PAYMENT.CAPTURE.REFUNDED':
        payment.status = 'refunded'
        payment.save()
    elif event_type == 'PAYMENT.CAPTURE.DENIED':
        payment.status = 'failed'
        payment.save()
    return Response({'status': payment.status, 'payment': PaymentSerializer(payment).data})
