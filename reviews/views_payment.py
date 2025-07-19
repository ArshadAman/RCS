from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.conf import settings
from .models import Payment, Company, Plan
from .serializers import PaymentSerializer
from .paypal import create_paypal_order, capture_paypal_order, create_vault_setup_token, create_payment_token

# Plan pricing configuration
PLAN_PRICING = {
    'basic': {'amount': 29.99, 'review_limit': 100},
    'standard': {'amount': 99.99, 'review_limit': 1000},
    'premium': {'amount': 199.99, 'review_limit': 10000},
}

class PaymentViewSet(viewsets.ModelViewSet):
    """API for PayPal payment and plan upgrade"""
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Payment.objects.all()
        return Payment.objects.filter(company__owner=self.request.user)

    @action(detail=False, methods=['get'])
    def pricing(self, request):
        """Get plan pricing information"""
        return Response(PLAN_PRICING)

    @action(detail=False, methods=['post'])
    def setup_vault(self, request):
        """Setup vault for recurring payments"""
        company_id = request.data.get('company_id')
        plan_type = request.data.get('plan_type')
        return_url = request.data.get('return_url')
        cancel_url = request.data.get('cancel_url')
        
        if not all([company_id, plan_type, return_url, cancel_url]):
            return Response({'error': 'Missing required fields'}, status=400)
            
        company = get_object_or_404(Company, id=company_id, owner=request.user)
        
        try:
            setup_token = create_vault_setup_token(
                plan_type=plan_type,
                company_name=company.name,
                return_url=return_url,
                cancel_url=cancel_url
            )
            return Response(setup_token)
        except Exception as e:
            return Response({'error': str(e)}, status=500)

    @action(detail=False, methods=['post'])
    def create_payment_token(self, request):
        """Create payment token from setup token"""
        setup_token_id = request.data.get('setup_token_id')
        
        if not setup_token_id:
            return Response({'error': 'Setup token ID required'}, status=400)
            
        try:
            payment_token = create_payment_token(setup_token_id)
            return Response(payment_token)
        except Exception as e:
            return Response({'error': str(e)}, status=500)
        """Create a PayPal order for plan upgrade"""
        company_id = request.data.get('company_id')
        plan_type = request.data.get('plan_type')
        
        if plan_type not in PLAN_PRICING:
            return Response({'error': 'Invalid plan type'}, status=400)
        
        amount = PLAN_PRICING[plan_type]['amount']
        currency = request.data.get('currency', 'USD')
        return_url = request.data.get('return_url', f"{settings.FRONTEND_URL}/payment/success")
        cancel_url = request.data.get('cancel_url', f"{settings.FRONTEND_URL}/payment/cancel")
        
        company = get_object_or_404(Company, id=company_id, owner=request.user)
        
        try:
            order = create_paypal_order(
                amount=amount,
                currency=currency,
                plan_type=plan_type,
                company_name=company.name,
                return_url=return_url,
                cancel_url=cancel_url
            )
            
            # Store payment record
            payment = Payment.objects.create(
                company=company,
                plan_type=plan_type,
                paypal_order_id=order['id'],
                amount=amount,
                currency=currency,
                status='created',
                raw_response=order
            )
            
            return Response({
                'order_id': order['id'],
                'approval_url': next(link['href'] for link in order['links'] if link['rel'] == 'approve'),
                'payment_id': payment.id
            })
            
        except Exception as e:
            return Response({'error': str(e)}, status=500)

    @action(detail=False, methods=['post'])
    def capture(self, request):
        """Capture a PayPal order and upgrade plan if successful"""
        paypal_order_id = request.data.get('paypal_order_id')
        
        if not paypal_order_id:
            return Response({'error': 'PayPal order ID required'}, status=400)
        
        try:
            payment = get_object_or_404(Payment, paypal_order_id=paypal_order_id)
            
            # Only allow company owner to capture their own payments
            if payment.company.owner != request.user and not request.user.is_staff:
                return Response({'error': 'Permission denied'}, status=403)
            
            capture_result = capture_paypal_order(paypal_order_id)
            
            # Update payment status
            if capture_result['status'] == 'COMPLETED':
                payment.status = 'completed'
                payment.raw_response = capture_result
                payment.save()
                
                # Upgrade or create plan
                plan, created = Plan.objects.get_or_create(
                    company=payment.company,
                    defaults={'plan_type': payment.plan_type}
                )
                
                if not created:
                    plan.plan_type = payment.plan_type
                
                # Set review limit based on plan
                plan.review_limit = PLAN_PRICING[payment.plan_type]['review_limit']
                plan.save()
                
                return Response({
                    'status': 'success',
                    'payment': PaymentSerializer(payment).data,
                    'plan': {
                        'type': plan.plan_type,
                        'review_limit': plan.review_limit
                    }
                })
            else:
                payment.status = 'failed'
                payment.raw_response = capture_result
                payment.save()
                return Response({'status': 'failed', 'message': 'Payment capture failed'}, status=400)
                
        except Exception as e:
            return Response({'error': str(e)}, status=500)

    @action(detail=False, methods=['get'])
    def company_plan(self, request):
        """Get current plan for user's company"""
        company_id = request.query_params.get('company_id')
        if not company_id:
            return Response({'error': 'Company ID required'}, status=400)
            
        company = get_object_or_404(Company, id=company_id, owner=request.user)
        
        try:
            plan = company.plan
            return Response({
                'company': company.name,
                'plan_type': plan.plan_type,
                'review_limit': plan.review_limit,
                'current_reviews': company.reviews.count()
            })
        except Plan.DoesNotExist:
            return Response({
                'company': company.name,
                'plan_type': 'free',
                'review_limit': 10,
                'current_reviews': company.reviews.count()
            })
