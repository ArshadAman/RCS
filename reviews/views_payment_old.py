from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
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

# Payment CRUD views
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def payment_list_create_view(request):
    """List payments or create a new payment"""
    
    if request.method == 'GET':
        if request.user.is_staff:
            queryset = Payment.objects.all()
        else:
            queryset = Payment.objects.filter(company__owner=request.user)
        
        serializer = PaymentSerializer(queryset, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = PaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        company = serializer.validated_data.get('company')
        if company.owner != request.user:
            raise PermissionDenied("You can only create payments for your own companies")
        
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def payment_detail_view(request, pk):
    """Retrieve, update or delete a specific payment"""
    
    try:
        if request.user.is_staff:
            payment = Payment.objects.get(pk=pk)
        else:
            payment = Payment.objects.get(pk=pk, company__owner=request.user)
    except Payment.DoesNotExist:
        return Response({'error': 'Payment not found'}, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        serializer = PaymentSerializer(payment)
        return Response(serializer.data)
    
    elif request.method in ['PUT', 'PATCH']:
        # Check permissions
        if not request.user.is_staff and payment.company.owner != request.user:
            raise PermissionDenied("You can only modify your own payments")
        
        partial = request.method == 'PATCH'
        serializer = PaymentSerializer(payment, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    
    elif request.method == 'DELETE':
        # Check permissions
        if not request.user.is_staff and payment.company.owner != request.user:
            raise PermissionDenied("You can only delete your own payments")
        
        payment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def payment_pricing_view(request):
    """Get plan pricing information"""
    return Response(PLAN_PRICING)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def payment_setup_vault_view(request):
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


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def payment_create_token_view(request):
    """Create payment token from setup token"""
    setup_token_id = request.data.get('setup_token_id')
    
    if not setup_token_id:
        return Response({'error': 'Setup token ID required'}, status=400)
        
    try:
        payment_token = create_payment_token(setup_token_id)
        return Response(payment_token)
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def payment_create_order_view(request):
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


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def payment_capture_view(request):
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


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def payment_company_plan_view(request):
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
