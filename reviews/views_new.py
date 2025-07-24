from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import ValidationError, PermissionDenied
from django.db.models import Q, Avg, Count
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.core.mail import send_mail
from django.conf import settings
import uuid
import qrcode
from io import BytesIO
import base64

from .models import (
    Business, Review, ReviewImage, ReviewLike, Category, Order, 
    SurveyQuestion, Plan, Badge, QRFeedback, ReviewAnswer, ReviewCriteria,
    ReviewCriteriaRating, EmailTemplate, WidgetSettings
)
from .serializers import (
    BusinessSerializer, BusinessCreateSerializer, ReviewSerializer,
    ReviewCreateSerializer, ReviewLikeSerializer, CategorySerializer,
    OrderSerializer, SurveyQuestionSerializer,
    PlanSerializer, BadgeSerializer, QRFeedbackSerializer,
    ReviewAnswerSerializer, ReviewCriteriaSerializer, ReviewCriteriaRatingSerializer,
    EmailTemplateSerializer, WidgetSettingsSerializer, PublicReviewSerializer
)
from .permissions import IsBusinessOwnerOrReadOnly


# Helper functions
def _calculate_recommendation_percentage(reviews):
    """Calculate recommendation percentage from reviews"""
    if reviews.exists():
        recommended_count = reviews.filter(would_recommend=True).count()
        return round((recommended_count / reviews.count()) * 100, 1)
    return 0

def _get_rating_distribution(reviews):
    """Get rating distribution from reviews"""
    distribution = {}
    for i in range(1, 6):
        distribution[str(i)] = reviews.filter(overall_rating=i).count()
    return distribution

def _send_review_email(order):
    """Send personalized review request email"""
    try:
        subject = f"Please share your feedback for {order.product_service_name}"
        message = f"""
        Hi {order.customer_name},
        
        Thank you for your recent purchase of {order.product_service_name}!
        
        We'd love to hear about your experience. Please click the link below to leave a review:
        {order.review_url}
        
        Your feedback helps us improve and helps other customers make informed decisions.
        
        Best regards,
        {order.business.name}
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[order.customer_email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False


# Business views (one business per user)
@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def business_view(request):
    """Get or update user's business"""
    
    try:
        business = Business.objects.get(owner=request.user)
    except Business.DoesNotExist:
        return Response({'error': 'Business not found. Please create a business first.'}, 
                       status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        serializer = BusinessSerializer(business)
        return Response(serializer.data)
    
    elif request.method in ['PUT', 'PATCH']:
        partial = request.method == 'PATCH'
        serializer = BusinessSerializer(business, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def business_dashboard_view(request):
    """Get dashboard statistics for user's business"""
    
    try:
        business = Business.objects.get(owner=request.user)
    except Business.DoesNotExist:
        return Response({'error': 'Business not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Get reviews for this business
    reviews = Review.objects.filter(business=business, status='published')
    total_reviews = reviews.count()
    
    # Calculate statistics
    avg_rating = reviews.aggregate(avg=Avg('overall_rating'))['avg'] or 0
    recommendation_percentage = _calculate_recommendation_percentage(reviews)
    rating_distribution = _get_rating_distribution(reviews)
    
    # Recent reviews
    recent_reviews = reviews.order_by('-created_at')[:5]
    
    data = {
        'business': BusinessSerializer(business).data,
        'statistics': {
            'total_reviews': total_reviews,
            'average_rating': round(avg_rating, 1),
            'recommendation_percentage': recommendation_percentage,
            'rating_distribution': rating_distribution,
        },
        'recent_reviews': ReviewSerializer(recent_reviews, many=True).data,
    }
    
    return Response(data)


# Order views
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def order_list_create_view(request):
    """List orders or create a new order"""
    
    try:
        business = Business.objects.get(owner=request.user)
    except Business.DoesNotExist:
        return Response({'error': 'Business not found'}, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        queryset = Order.objects.filter(user=request.user, business=business)
        
        # Apply ordering
        ordering = request.GET.get('ordering', '-created_at')
        queryset = queryset.order_by(ordering)
        
        serializer = OrderSerializer(queryset, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = OrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Automatically set the user and business
        serializer.save(user=request.user, business=business)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def order_detail_view(request, pk):
    """Retrieve, update or delete a specific order"""
    
    try:
        order = Order.objects.get(pk=pk, user=request.user)
    except Order.DoesNotExist:
        return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        serializer = OrderSerializer(order)
        return Response(serializer.data)
    
    elif request.method in ['PUT', 'PATCH']:
        partial = request.method == 'PATCH'
        serializer = OrderSerializer(order, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    
    elif request.method == 'DELETE':
        order.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def order_send_review_request_view(request, pk):
    """Send review request email to customer"""
    
    try:
        order = Order.objects.get(pk=pk, user=request.user)
    except Order.DoesNotExist:
        return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
    
    if order.status != 'pending':
        return Response(
            {'error': 'Order is not in pending status'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Send email
    success = _send_review_email(order)
    
    if success:
        order.status = 'review_sent'
        order.email_sent_at = timezone.now()
        order.save()
        return Response({'message': 'Review request sent successfully'})
    else:
        return Response(
            {'error': 'Failed to send review request'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Review views
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def review_list_create_view(request):
    """List reviews or create a new review"""
    
    try:
        business = Business.objects.get(owner=request.user)
    except Business.DoesNotExist:
        return Response({'error': 'Business not found'}, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        queryset = Review.objects.filter(business=business)
        
        # Apply ordering
        ordering = request.GET.get('ordering', '-created_at')
        queryset = queryset.order_by(ordering)
        
        serializer = ReviewSerializer(queryset, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = ReviewCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Enforce plan review limit
        plan = getattr(request.user, 'plan', None)
        if plan is not None:
            review_limit = plan.review_limit
            current_review_count = Review.objects.filter(business=business).count()
            if current_review_count >= review_limit:
                raise ValidationError(f"Review limit reached for your current plan ({plan.get_plan_type_display()}). Please upgrade your plan to add more reviews.")
        
        review = serializer.save(business=business)
        return Response(ReviewSerializer(review).data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def review_detail_view(request, pk):
    """Retrieve, update or delete a specific review"""
    
    try:
        business = Business.objects.get(owner=request.user)
        review = Review.objects.get(pk=pk, business=business)
    except (Business.DoesNotExist, Review.DoesNotExist):
        return Response({'error': 'Review not found'}, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        serializer = ReviewSerializer(review)
        return Response(serializer.data)
    
    elif request.method in ['PUT', 'PATCH']:
        partial = request.method == 'PATCH'
        serializer = ReviewSerializer(review, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    
    elif request.method == 'DELETE':
        review.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def review_approve_view(request, pk):
    """Approve a review"""
    
    try:
        business = Business.objects.get(owner=request.user)
        review = Review.objects.get(pk=pk, business=business)
    except (Business.DoesNotExist, Review.DoesNotExist):
        return Response({'error': 'Review not found'}, status=status.HTTP_404_NOT_FOUND)
    
    review.status = 'published'
    review.save()
    
    return Response({'message': 'Review approved successfully'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def review_reject_view(request, pk):
    """Reject a review"""
    
    try:
        business = Business.objects.get(owner=request.user)
        review = Review.objects.get(pk=pk, business=business)
    except (Business.DoesNotExist, Review.DoesNotExist):
        return Response({'error': 'Review not found'}, status=status.HTTP_404_NOT_FOUND)
    
    review.status = 'rejected'
    review.save()
    
    return Response({'message': 'Review rejected successfully'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def review_respond_view(request, pk):
    """Add business response to review"""
    
    try:
        business = Business.objects.get(owner=request.user)
        review = Review.objects.get(pk=pk, business=business)
    except (Business.DoesNotExist, Review.DoesNotExist):
        return Response({'error': 'Review not found'}, status=status.HTTP_404_NOT_FOUND)
    
    response_text = request.data.get('response')
    if not response_text:
        return Response(
            {'error': 'Response text is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    review.business_response = response_text
    review.response_date = timezone.now()
    review.responded_by = request.user
    review.save()
    
    return Response({'message': 'Response added successfully'})


# Review Criteria views
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def review_criteria_list_create_view(request):
    """List review criteria or create a new review criteria"""
    
    if request.method == 'GET':
        queryset = ReviewCriteria.objects.filter(user=request.user)
        
        # Apply filters
        is_active = request.GET.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        # Apply ordering
        ordering = request.GET.get('ordering', 'order')
        queryset = queryset.order_by(ordering)
        
        serializer = ReviewCriteriaSerializer(queryset, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = ReviewCriteriaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def review_criteria_detail_view(request, pk):
    """Retrieve, update or delete a specific review criteria"""
    
    try:
        criteria = ReviewCriteria.objects.get(pk=pk, user=request.user)
    except ReviewCriteria.DoesNotExist:
        return Response({'error': 'Review criteria not found'}, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        serializer = ReviewCriteriaSerializer(criteria)
        return Response(serializer.data)
    
    elif request.method in ['PUT', 'PATCH']:
        partial = request.method == 'PATCH'
        serializer = ReviewCriteriaSerializer(criteria, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    
    elif request.method == 'DELETE':
        criteria.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# Widget views
@api_view(['GET'])
@permission_classes([AllowAny])
def widget_data(request, user_id):
    """Get widget data for public display"""
    try:
        business = Business.objects.get(owner__id=user_id)
        
        # Get widget settings
        widget_settings = getattr(business.owner, 'widget_settings', None)
        
        # Get reviews for this business
        reviews = Review.objects.filter(
            business=business,
            status='published'
        ).order_by('-created_at')
        
        # Get statistics
        total_reviews = reviews.count()
        avg_rating = reviews.aggregate(avg=Avg('overall_rating'))['avg'] or 0
        recommendation_percentage = _calculate_recommendation_percentage(reviews)
        
        # Get recent reviews based on widget settings
        display_count = widget_settings.display_count if widget_settings else 5
        recent_reviews = reviews[:display_count]
        
        data = {
            'business': BusinessSerializer(business).data,
            'widget_settings': WidgetSettingsSerializer(widget_settings).data if widget_settings else None,
            'statistics': {
                'total_reviews': total_reviews,
                'average_rating': round(avg_rating, 1),
                'recommendation_percentage': recommendation_percentage,
            },
            'recent_reviews': PublicReviewSerializer(recent_reviews, many=True).data,
        }
        
        return Response(data)
    
    except Business.DoesNotExist:
        return Response(
            {'error': 'Business not found'},
            status=status.HTTP_404_NOT_FOUND
        )


# Categories
@api_view(['GET'])
@permission_classes([AllowAny])
def category_list_view(request):
    """List all active categories"""
    categories = Category.objects.filter(is_active=True)
    serializer = CategorySerializer(categories, many=True)
    return Response(serializer.data)


# Public review submission
@api_view(['GET'])
@permission_classes([AllowAny])
def public_review_form(request, token):
    """Get review form data for public review submission"""
    try:
        order = Order.objects.get(review_link_token=token)
        
        # Check if order is still valid
        if order.status not in ['pending', 'review_sent']:
            return Response(
                {'error': 'Review link is no longer valid'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get review criteria for the user
        criteria = ReviewCriteria.objects.filter(
            user=order.user,
            is_active=True
        ).order_by('order')
        
        data = {
            'order': OrderSerializer(order).data,
            'business': BusinessSerializer(order.business).data,
            'criteria': ReviewCriteriaSerializer(criteria, many=True).data,
        }
        
        return Response(data)
    
    except Order.DoesNotExist:
        return Response(
            {'error': 'Invalid review token'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def submit_public_review(request, token):
    """Submit a public review using token"""
    try:
        order = Order.objects.get(review_link_token=token)
        
        if order.status not in ['pending', 'review_sent']:
            return Response(
                {'error': 'Review link is no longer valid'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if review already exists
        if hasattr(order, 'review'):
            return Response(
                {'error': 'Review already submitted for this order'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create review
        serializer = PublicReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        review = serializer.save(
            order=order,
            business=order.business,
            reviewer_email=order.customer_email,
            reviewer_name=order.customer_name
        )
        
        # Update order status
        order.status = 'completed'
        order.save()
        
        return Response({
            'message': 'Review submitted successfully',
            'review': ReviewSerializer(review).data
        }, status=status.HTTP_201_CREATED)
        
    except Order.DoesNotExist:
        return Response(
            {'error': 'Invalid review token'},
            status=status.HTTP_404_NOT_FOUND
        )
