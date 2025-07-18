from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.conf import settings
from .models import Payment, Company, Plan
from .serializers import PaymentSerializer
from .paypal import create_paypal_order, capture_paypal_order

class PaymentViewSet(viewsets.ModelViewSet):
    """API for PayPal payment and plan upgrade"""
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Payment.objects.all()
        return Payment.objects.filter(company__owner=self.request.user)

    @action(detail=False, methods=['post'])
    def create_paypal_order(self, request):
        """Create a PayPal order for plan upgrade"""
        company_id = request.data.get('company_id')
        plan_type = request.data.get('plan_type')
        amount = request.data.get('amount')
        currency = request.data.get('currency', 'USD')
        return_url = request.data.get('return_url')
        cancel_url = request.data.get('cancel_url')
        company = get_object_or_404(Company, id=company_id, owner=request.user)
        order = create_paypal_order(
            amount=amount,
            currency=currency,
            plan_type=plan_type,
            company_name=company.name,
            return_url=return_url,
            cancel_url=cancel_url
        )
        Payment.objects.create(
            company=company,
            plan_type=plan_type,
            paypal_order_id=order['id'],
            amount=amount,
            currency=currency,
            status='created',
            raw_response=order
        )
        return Response(order)

    @action(detail=False, methods=['post'])
    def capture(self, request):
        """Capture a PayPal order and upgrade plan if successful"""
        paypal_order_id = request.data.get('paypal_order_id')
        payment = get_object_or_404(Payment, paypal_order_id=paypal_order_id)
        capture_result = capture_paypal_order(paypal_order_id)
        payment.status = 'completed' if capture_result['status'] == 'COMPLETED' else 'failed'
        payment.raw_response = capture_result
        payment.save()
        if payment.status == 'completed':
            # Upgrade plan
            plan, _ = Plan.objects.get_or_create(company=payment.company)
            plan.plan_type = payment.plan_type
            # Optionally set review_limit based on plan_type
            if plan.plan_type == 'basic':
                plan.review_limit = 50
            elif plan.plan_type == 'standard':
                plan.review_limit = 500
            elif plan.plan_type == 'premium':
                plan.review_limit = 5000
            plan.save()
        return Response({'status': payment.status, 'payment': PaymentSerializer(payment).data})
