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
from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
import uuid
import qrcode
from io import BytesIO
import base64

User = get_user_model()

from .models import (
    Business, Review, ReviewImage, ReviewLike, Order, 
    SurveyQuestion, Plan, Badge, QRFeedback, ReviewAnswer, ReviewCriteria,
    ReviewCriteriaRating, EmailTemplate, WidgetSettings, Payment
)
from .serializers import (
    BusinessSerializer, BusinessCreateSerializer, ReviewSerializer,
    ReviewCreateSerializer, ReviewLikeSerializer,
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
@extend_schema(
    operation_id='manage_business',
    tags=['Business'],
    summary='Manage Business',
    description="""
    Manage the authenticated user's business information.
    Each user can only have one business in the system.
    
    **GET:** Retrieve business information
    **POST:** Create a new business (if user doesn't have one)
    **PUT/PATCH:** Update existing business information
    """,
    responses={
        200: BusinessSerializer,
        201: 'Business created successfully',
        404: OpenApiExample(
            'Business Not Found',
            value={'error': 'Business not found. Please create a business first.'},
            response_only=True
        ),
        400: OpenApiExample(
            'Validation Error or Business Already Exists',
            value={'error': 'You already have a business. Use PUT/PATCH to update it.'},
            response_only=True
        )
    },
    examples=[
        OpenApiExample(
            'Create Business Request',
            value={
                'name': 'My Awesome Restaurant',
                'description': 'Best pizza in town!',
                'category': 'Restaurant',
                'address': '123 Main St, City, State 12345',
                'phone_number': '+1-555-123-4567',
                'email': 'contact@myrestaurant.com',
                'website': 'https://myrestaurant.com'
            },
            request_only=True
        ),
        OpenApiExample(
            'Update Business Request',
            value={
                'name': 'My Updated Restaurant',
                'description': 'Best pizza and pasta in town!',
                'address': '456 New St, City, State 12345',
                'phone_number': '+1-555-987-6543'
            },
            request_only=True
        ),
        OpenApiExample(
            'Business Response',
            value={
                'id': 1,
                'name': 'My Awesome Restaurant',
                'description': 'Best pizza in town!',
                'category': 'Restaurant',
                'address': '123 Main St, City, State 12345',
                'phone_number': '+1-555-123-4567',
                'email': 'contact@myrestaurant.com',
                'website': 'https://myrestaurant.com',
                'average_rating': 4.5,
                'total_reviews': 128,
                'is_active': True,
                'created_at': '2025-01-15T10:30:00Z',
                'updated_at': '2025-01-20T14:45:00Z'
            },
            response_only=True
        )
    ]
)
@api_view(['GET', 'POST', 'PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def business_view(request):
    """Get, create, or update user's business"""
    
    if request.method == 'POST':
        # Check if user already has a business
        if Business.objects.filter(owner=request.user).exists():
            return Response(
                {'error': 'You already have a business. Use PUT/PATCH to update it.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create new business
        serializer = BusinessCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        business = serializer.save(owner=request.user)
        return Response(BusinessSerializer(business).data, status=status.HTTP_201_CREATED)
    
    # For GET, PUT, PATCH - business must exist
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


@extend_schema(
    operation_id='get_business_dashboard',
    tags=['Business'],
    summary='Get Business Dashboard Statistics',
    description="""
    Get comprehensive dashboard statistics for the authenticated user's business including:
    - Total reviews and average rating
    - Review breakdown by status (pending, published, rejected)
    - Rating distribution (1-5 stars)
    - Recent reviews and recommendation percentage
    """,
    responses={
        200: OpenApiExample(
            'Dashboard Statistics',
            value={
                'business': {
                    'id': 1,
                    'name': 'My Awesome Restaurant',
                    'average_rating': 4.5,
                    'total_reviews': 128
                },
                'stats': {
                    'total_reviews': 128,
                    'pending_reviews': 5,
                    'published_reviews': 120,
                    'rejected_reviews': 3,
                    'average_rating': 4.5,
                    'recommendation_percentage': 87.5,
                    'rating_distribution': {
                        '1': 2,
                        '2': 5,
                        '3': 15,
                        '4': 45,
                        '5': 61
                    }
                },
                'recent_reviews': [
                    {
                        'id': 45,
                        'reviewer_name': 'John Doe',
                        'overall_rating': 5,
                        'comment': 'Amazing food and service!',
                        'created_at': '2025-01-20T18:30:00Z',
                        'status': 'published'
                    }
                ],
                'orders': {
                    'total_orders': 89,
                    'completed_orders': 85,
                    'pending_orders': 4
                }
            },
            response_only=True
        ),
        404: OpenApiExample(
            'Business Not Found',
            value={'error': 'Business not found'},
            response_only=True
        )
    }
)
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
@extend_schema(
    operation_id='list_create_orders',
    tags=['Orders'],
    summary='List or Create Orders',
    description="""
    Manage customer orders for the authenticated user's business.
    
    **GET:** Returns list of orders with filtering and sorting options
    **POST:** Creates a new customer order that can later be used for review requests
    
    Orders represent customer transactions and are used to generate review request links.
    """,
    parameters=[
        OpenApiParameter(
            name='status',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Filter by order status',
            enum=['pending', 'completed', 'cancelled'],
            required=False
        ),
        OpenApiParameter(
            name='ordering',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Order results by field (prefix with - for descending)',
            enum=['created_at', '-created_at', 'purchase_date', '-purchase_date'],
            required=False
        ),
        OpenApiParameter(
            name='search',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Search in order number, customer name, or product/service name',
            required=False
        )
    ],
    examples=[
        OpenApiExample(
            'Create Order Request',
            value={
                'order_number': 'ORD-2025-001234',
                'customer_name': 'John Doe',
                'customer_email': 'john.doe@example.com',
                'product_service_name': 'Deluxe Pizza Combo',
                'purchase_date': '2025-01-20',
                'amount': 45.99,
                'status': 'completed'
            },
            request_only=True
        ),
        OpenApiExample(
            'Orders List Response',
            value={
                'count': 89,
                'next': 'http://api.example.com/api/orders/?page=2',
                'previous': None,
                'results': [
                    {
                        'id': 123,
                        'order_number': 'ORD-2025-001234',
                        'customer_name': 'John Doe',
                        'customer_email': 'john.doe@example.com',
                        'product_service_name': 'Deluxe Pizza Combo',
                        'purchase_date': '2025-01-20',
                        'amount': 45.99,
                        'status': 'completed',
                        'review_url': 'https://yoursite.com/review/abc123token',
                        'review_sent': True,
                        'created_at': '2025-01-20T14:30:00Z'
                    }
                ]
            },
            response_only=True
        )
    ],
    responses={
        200: 'Success - list of orders',
        201: 'Order created successfully',
        400: OpenApiExample(
            'Validation Error',
            value={'customer_email': ['Enter a valid email address.']},
            response_only=True
        ),
        404: OpenApiExample(
            'Business Not Found',
            value={'error': 'Business not found'},
            response_only=True
        )
    }
)
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


@extend_schema(
    operation_id='order_detail',
    tags=['Orders'],
    summary='Order Detail Operations',
    description="""
    Retrieve, update, or delete a specific order.
    
    GET: Get detailed information about a specific order
    PUT/PATCH: Update order information
    DELETE: Delete an order
    
    Only the business owner can access their orders.
    """,
    parameters=[
        OpenApiParameter(
            name='pk',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
            description='Order ID',
            required=True
        )
    ],
    examples=[
        OpenApiExample(
            'Order Detail Response',
            value={
                'id': 123,
                'order_number': 'ORD-2025-001',
                'customer_name': 'John Doe',
                'customer_email': 'john.doe@example.com',
                'customer_phone': '+1-555-0123',
                'amount': '45.99',
                'status': 'completed',
                'notes': 'Customer requested extra cheese',
                'created_at': '2025-01-20T12:30:00Z',
                'updated_at': '2025-01-20T13:15:00Z',
                'review_token': 'abc123token',
                'review_requested': True,
                'review_sent_at': '2025-01-20T14:00:00Z'
            },
            response_only=True
        ),
        OpenApiExample(
            'Update Order Request',
            value={
                'status': 'completed',
                'notes': 'Order delivered successfully, customer was very satisfied'
            },
            request_only=True
        )
    ],
    responses={
        200: 'Order details retrieved/updated successfully',
        204: 'Order deleted successfully',
        404: OpenApiExample(
            'Order Not Found',
            value={'error': 'Order not found'},
            response_only=True
        ),
        400: OpenApiExample(
            'Validation Error',
            value={'amount': ['A valid number is required.']},
            response_only=True
        ),
        401: OpenApiExample(
            'Authentication Required',
            value={'detail': 'Authentication credentials were not provided.'},
            response_only=True
        )
    }
)
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


@extend_schema(
    operation_id='send_review_request',
    tags=['Orders'],
    summary='Send Review Request',
    description="""
    Send a review request email to the customer for a specific order.
    
    This endpoint triggers an email to be sent to the customer with a unique review token.
    The customer can use this token to submit their review through the public review form.
    
    Order must be in 'pending' status to send review request.
    """,
    parameters=[
        OpenApiParameter(
            name='pk',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
            description='Order ID to send review request for',
            required=True
        )
    ],
    examples=[
        OpenApiExample(
            'Review Request Sent Response',
            value={
                'message': 'Review request sent successfully',
                'order': {
                    'id': 123,
                    'order_number': 'ORD-2025-001',
                    'customer_name': 'John Doe',
                    'customer_email': 'john.doe@example.com',
                    'review_requested': True,
                    'review_sent_at': '2025-01-20T15:30:00Z',
                    'review_token': 'abc123token456'
                }
            },
            response_only=True
        )
    ],
    responses={
        200: 'Review request sent successfully',
        404: OpenApiExample(
            'Order Not Found',
            value={'error': 'Order not found'},
            response_only=True
        ),
        400: OpenApiExample(
            'Invalid Order Status',
            value={'error': 'Order is not in pending status'},
            response_only=True
        ),
        401: OpenApiExample(
            'Authentication Required',
            value={'detail': 'Authentication credentials were not provided.'},
            response_only=True
        )
    }
)
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
@extend_schema(
    operation_id='list_create_reviews',
    tags=['Reviews'],
    summary='List or Create Reviews',
    description="""
    List all reviews for the authenticated user's business or create a new review.
    
    **GET:** Returns paginated list of reviews with filtering options
    **POST:** Creates a new review (usually done via public review submission)
    
    Reviews can be filtered by status, rating, and date range.
    """,
    parameters=[
        OpenApiParameter(
            name='status',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Filter by review status',
            enum=['pending', 'published', 'rejected'],
            required=False
        ),
        OpenApiParameter(
            name='rating',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description='Filter by overall rating (1-5)',
            required=False
        ),
        OpenApiParameter(
            name='search',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Search in review comments and reviewer names',
            required=False
        )
    ],
    examples=[
        OpenApiExample(
            'Create Review Request',
            value={
                'overall_rating': 5,
                'service_rating': 5,
                'quality_rating': 4,
                'value_rating': 5,
                'comment': 'Amazing food and excellent service! Highly recommended.',
                'would_recommend': True,
                'reviewer_name': 'John Doe',
                'reviewer_email': 'john@example.com'
            },
            request_only=True
        ),
        OpenApiExample(
            'Reviews List Response',
            value={
                'count': 128,
                'next': 'http://api.example.com/api/reviews/?page=2',
                'previous': None,
                'results': [
                    {
                        'id': 45,
                        'overall_rating': 5,
                        'service_rating': 5,
                        'quality_rating': 4,
                        'value_rating': 5,
                        'comment': 'Amazing food and excellent service!',
                        'would_recommend': True,
                        'reviewer_name': 'John Doe',
                        'reviewer_email': 'john@example.com',
                        'status': 'published',
                        'business_response': None,
                        'created_at': '2025-01-20T18:30:00Z',
                        'updated_at': '2025-01-20T18:30:00Z'
                    }
                ]
            },
            response_only=True
        )
    ],
    responses={
        200: 'Success - list of reviews or created review',
        201: 'Review created successfully',
        400: OpenApiExample(
            'Validation Error',
            value={'overall_rating': ['This field is required.']},
            response_only=True
        ),
        404: OpenApiExample(
            'Business Not Found',
            value={'error': 'Business not found'},
            response_only=True
        )
    }
)
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


@extend_schema(
    operation_id='review_detail',
    tags=['Reviews'],
    summary='Review Detail Operations',
    description="""
    Retrieve, update, or delete a specific review.
    
    GET: Get detailed information about a specific review
    PUT/PATCH: Update review information (admin only)
    DELETE: Delete a review (admin only)
    
    Only the business owner can access their reviews.
    """,
    parameters=[
        OpenApiParameter(
            name='pk',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
            description='Review ID',
            required=True
        )
    ],
    examples=[
        OpenApiExample(
            'Review Detail Response',
            value={
                'id': 45,
                'overall_rating': 5,
                'service_rating': 5,
                'quality_rating': 4,
                'value_rating': 5,
                'comment': 'Amazing food and excellent service!',
                'would_recommend': True,
                'reviewer_name': 'John Doe',
                'reviewer_email': 'john.doe@example.com',
                'status': 'approved',
                'business_response': 'Thank you for your wonderful feedback!',
                'created_at': '2025-01-20T18:30:00Z',
                'updated_at': '2025-01-20T19:15:00Z',
                'business': {
                    'id': 12,
                    'name': 'Pizza Palace',
                    'email': 'contact@pizzapalace.com'
                }
            },
            response_only=True
        ),
        OpenApiExample(
            'Update Review Request',
            value={
                'status': 'approved',
                'business_response': 'Thank you for your feedback! We appreciate your business.'
            },
            request_only=True
        )
    ],
    responses={
        200: 'Review details retrieved/updated successfully',
        204: 'Review deleted successfully',
        404: OpenApiExample(
            'Review Not Found',
            value={'error': 'Review not found'},
            response_only=True
        ),
        401: OpenApiExample(
            'Authentication Required',
            value={'detail': 'Authentication credentials were not provided.'},
            response_only=True
        )
    }
)
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


@extend_schema(
    operation_id='approve_review',
    tags=['Reviews'],
    summary='Approve Review',
    description="""
    Approve a pending review to make it publicly visible.
    
    Only the business owner can approve reviews for their business.
    Once approved, the review will be displayed on the business profile and widget.
    """,
    parameters=[
        OpenApiParameter(
            name='pk',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
            description='Review ID to approve',
            required=True
        )
    ],
    examples=[
        OpenApiExample(
            'Review Approved Response',
            value={
                'message': 'Review approved successfully',
                'review': {
                    'id': 45,
                    'overall_rating': 5,
                    'comment': 'Amazing food and excellent service!',
                    'status': 'approved',
                    'reviewer_name': 'John Doe',
                    'created_at': '2025-01-20T18:30:00Z',
                    'approved_at': '2025-01-20T19:15:00Z'
                }
            },
            response_only=True
        )
    ],
    responses={
        200: 'Review approved successfully',
        404: OpenApiExample(
            'Review Not Found',
            value={'error': 'Review not found'},
            response_only=True
        ),
        400: OpenApiExample(
            'Already Approved',
            value={'error': 'Review is already approved'},
            response_only=True
        ),
        401: OpenApiExample(
            'Authentication Required',
            value={'detail': 'Authentication credentials were not provided.'},
            response_only=True
        )
    }
)
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


@extend_schema(
    operation_id='reject_review',
    tags=['Reviews'],
    summary='Reject Review',
    description="""
    Reject a pending review to prevent it from being publicly visible.
    
    Only the business owner can reject reviews for their business.
    Rejected reviews will not be displayed publicly but remain in the system for record keeping.
    """,
    parameters=[
        OpenApiParameter(
            name='pk',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
            description='Review ID to reject',
            required=True
        )
    ],
    examples=[
        OpenApiExample(
            'Review Rejected Response',
            value={
                'message': 'Review rejected successfully',
                'review': {
                    'id': 45,
                    'overall_rating': 2,
                    'comment': 'Food was cold and service was slow.',
                    'status': 'rejected',
                    'reviewer_name': 'Jane Smith',
                    'created_at': '2025-01-20T18:30:00Z',
                    'rejected_at': '2025-01-20T19:15:00Z'
                }
            },
            response_only=True
        )
    ],
    responses={
        200: 'Review rejected successfully',
        404: OpenApiExample(
            'Review Not Found',
            value={'error': 'Review not found'},
            response_only=True
        ),
        400: OpenApiExample(
            'Already Rejected',
            value={'error': 'Review is already rejected'},
            response_only=True
        ),
        401: OpenApiExample(
            'Authentication Required',
            value={'detail': 'Authentication credentials were not provided.'},
            response_only=True
        )
    }
)
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


@extend_schema(
    operation_id='respond_to_review',
    tags=['Reviews'],
    summary='Respond to Review',
    description="""
    Add a business response to a customer review.
    
    Business owners can respond to customer reviews to show engagement and provide additional context.
    The response will be displayed publicly alongside the review.
    """,
    parameters=[
        OpenApiParameter(
            name='pk',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
            description='Review ID to respond to',
            required=True
        )
    ],
    examples=[
        OpenApiExample(
            'Add Response Request',
            value={
                'response': 'Thank you for your feedback! We are working to improve our service and appreciate your patience. Please give us another chance!'
            },
            request_only=True
        ),
        OpenApiExample(
            'Response Added Successfully',
            value={
                'message': 'Response added successfully',
                'review': {
                    'id': 45,
                    'overall_rating': 3,
                    'comment': 'Service could be better, but food was good.',
                    'business_response': 'Thank you for your feedback! We are working to improve our service and appreciate your patience.',
                    'reviewer_name': 'Jane Smith',
                    'status': 'approved',
                    'created_at': '2025-01-20T18:30:00Z',
                    'response_added_at': '2025-01-20T20:15:00Z'
                }
            },
            response_only=True
        )
    ],
    responses={
        200: 'Response added successfully',
        404: OpenApiExample(
            'Review Not Found',
            value={'error': 'Review not found'},
            response_only=True
        ),
        400: OpenApiExample(
            'Missing Response',
            value={'error': 'Response text is required'},
            response_only=True
        ),
        401: OpenApiExample(
            'Authentication Required',
            value={'detail': 'Authentication credentials were not provided.'},
            response_only=True
        )
    }
)
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
@extend_schema(
    operation_id='review_criteria_list_create',
    tags=['Review Criteria'],
    summary='List or Create Review Criteria',
    description="""
    List all review criteria for the authenticated business or create a new review criteria.
    
    GET: Retrieve list of all review criteria for the business with optional filtering
    POST: Create a new review criteria for rating specific aspects
    
    Review criteria allow businesses to ask customers to rate specific aspects like service, quality, value, etc.
    """,
    parameters=[
        OpenApiParameter(
            name='is_active',
            type=OpenApiTypes.BOOL,
            location=OpenApiParameter.QUERY,
            description='Filter by active status',
            required=False
        )
    ],
    examples=[
        OpenApiExample(
            'Review Criteria List Response',
            value=[
                {
                    'id': 1,
                    'name': 'Service Quality',
                    'description': 'Rate the quality of customer service',
                    'is_active': True,
                    'order': 1,
                    'created_at': '2025-01-15T10:00:00Z'
                },
                {
                    'id': 2,
                    'name': 'Food Quality',
                    'description': 'Rate the quality and taste of food',
                    'is_active': True,
                    'order': 2,
                    'created_at': '2025-01-15T10:05:00Z'
                },
                {
                    'id': 3,
                    'name': 'Value for Money',
                    'description': 'Rate if the price matches the quality',
                    'is_active': True,
                    'order': 3,
                    'created_at': '2025-01-15T10:10:00Z'
                }
            ],
            response_only=True
        ),
        OpenApiExample(
            'Create Review Criteria Request',
            value={
                'name': 'Atmosphere',
                'description': 'Rate the restaurant atmosphere and ambiance',
                'is_active': True,
                'order': 4
            },
            request_only=True
        ),
        OpenApiExample(
            'Create Review Criteria Response',
            value={
                'id': 4,
                'name': 'Atmosphere',
                'description': 'Rate the restaurant atmosphere and ambiance',
                'is_active': True,
                'order': 4,
                'created_at': '2025-01-20T14:30:00Z'
            },
            response_only=True
        )
    ],
    responses={
        200: 'Review criteria list retrieved successfully',
        201: 'Review criteria created successfully',
        400: OpenApiExample(
            'Validation Error',
            value={'name': ['This field is required.']},
            response_only=True
        ),
        401: OpenApiExample(
            'Authentication Required',
            value={'detail': 'Authentication credentials were not provided.'},
            response_only=True
        )
    }
)
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


@extend_schema(
    operation_id='review_criteria_detail',
    tags=['Review Criteria'],
    summary='Review Criteria Detail Operations',
    description="""
    Retrieve, update, or delete a specific review criteria.
    
    GET: Get detailed information about a specific review criteria
    PUT/PATCH: Update review criteria information
    DELETE: Delete a review criteria
    
    Only the business owner can manage their review criteria.
    """,
    parameters=[
        OpenApiParameter(
            name='pk',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
            description='Review Criteria ID',
            required=True
        )
    ],
    examples=[
        OpenApiExample(
            'Review Criteria Detail Response',
            value={
                'id': 1,
                'name': 'Service Quality',
                'description': 'Rate the quality of customer service provided',
                'is_active': True,
                'order': 1,
                'created_at': '2025-01-15T10:00:00Z',
                'updated_at': '2025-01-20T14:30:00Z'
            },
            response_only=True
        ),
        OpenApiExample(
            'Update Review Criteria Request',
            value={
                'name': 'Customer Service Excellence',
                'description': 'Rate the overall excellence of customer service and staff friendliness',
                'is_active': True,
                'order': 1
            },
            request_only=True
        )
    ],
    responses={
        200: 'Review criteria details retrieved/updated successfully',
        204: 'Review criteria deleted successfully',
        404: OpenApiExample(
            'Review Criteria Not Found',
            value={'error': 'Review criteria not found'},
            response_only=True
        ),
        400: OpenApiExample(
            'Validation Error',
            value={'name': ['This field is required.']},
            response_only=True
        ),
        401: OpenApiExample(
            'Authentication Required',
            value={'detail': 'Authentication credentials were not provided.'},
            response_only=True
        )
    }
)
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
@extend_schema(
    operation_id='widget_data',
    tags=['Widget'],
    summary='Get Widget Data',
    description="""
    Get public widget data for display on third-party websites.
    
    This endpoint provides all the necessary data for rendering a business review widget,
    including approved reviews, business information, and widget configuration settings.
    
    This is a public endpoint that doesn't require authentication.
    """,
    parameters=[
        OpenApiParameter(
            name='user_id',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
            description='User ID of the business owner',
            required=True
        )
    ],
    examples=[
        OpenApiExample(
            'Widget Data Response',
            value={
                'business': {
                    'id': 12,
                    'name': 'Pizza Palace',
                    'description': 'Best pizza in town with fresh ingredients',
                    'website': 'https://pizzapalace.com',
                    'phone': '+1-555-0123',
                    'address': '123 Main St, City, State 12345'
                },
                'reviews': [
                    {
                        'id': 45,
                        'overall_rating': 5,
                        'comment': 'Amazing food and excellent service!',
                        'reviewer_name': 'John D.',
                        'created_at': '2025-01-20T18:30:00Z',
                        'business_response': 'Thank you for your wonderful feedback!'
                    },
                    {
                        'id': 44,
                        'overall_rating': 4,
                        'comment': 'Great pizza, fast delivery!',
                        'reviewer_name': 'Sarah M.',
                        'created_at': '2025-01-19T20:15:00Z'
                    }
                ],
                'stats': {
                    'total_reviews': 45,
                    'average_rating': 4.6,
                    'rating_distribution': {
                        '5': 25,
                        '4': 12,
                        '3': 6,
                        '2': 1,
                        '1': 1
                    }
                },
                'widget_settings': {
                    'theme': 'light',
                    'show_logo': True,
                    'max_reviews_display': 5,
                    'auto_scroll': True
                }
            },
            response_only=True
        )
    ],
    responses={
        200: 'Widget data retrieved successfully',
        404: OpenApiExample(
            'Business Not Found',
            value={'error': 'Business not found'},
            response_only=True
        )
    }
)
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


# Public review submission
@extend_schema(
    operation_id='get_public_review_form',
    tags=['Public'],
    summary='Get Public Review Form',
    description="""
    Get review form data for public review submission using a review token.
    This endpoint is public and doesn't require authentication.
    
    Customers receive review tokens via email after completing orders.
    The token allows them to submit a review without creating an account.
    """,
    parameters=[
        OpenApiParameter(
            name='token',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.PATH,
            description='Unique review token sent to customer via email',
            required=True
        )
    ],
    examples=[
        OpenApiExample(
            'Review Form Data Response',
            value={
                'order': {
                    'id': 123,
                    'order_number': 'ORD-2025-001234',
                    'customer_name': 'John Doe',
                    'product_service_name': 'Deluxe Pizza Combo',
                    'purchase_date': '2025-01-20'
                },
                'business': {
                    'id': 1,
                    'name': 'My Awesome Restaurant',
                    'address': '123 Main St, City, State 12345'
                },
                'review_criteria': [
                    {
                        'id': 1,
                        'name': 'Food Quality',
                        'is_active': True,
                        'order': 1
                    },
                    {
                        'id': 2,
                        'name': 'Service',
                        'is_active': True,
                        'order': 2
                    }
                ]
            },
            response_only=True
        )
    ],
    responses={
        200: 'Review form data retrieved successfully',
        400: OpenApiExample(
            'Invalid Token',
            value={'error': 'Review link is no longer valid'},
            response_only=True
        ),
        404: OpenApiExample(
            'Token Not Found',
            value={'error': 'Invalid review token'},
            response_only=True
        )
    }
)
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


@extend_schema(
    operation_id='submit_public_review',
    tags=['Public'],
    summary='Submit Public Review',
    description="""
    Submit a customer review using a review token. This endpoint is public and doesn't require authentication.
    
    Customers use this endpoint to submit their review after receiving a review token via email.
    Once submitted, the review will be pending approval by the business owner.
    """,
    parameters=[
        OpenApiParameter(
            name='token',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.PATH,
            description='Unique review token sent to customer via email',
            required=True
        )
    ],
    examples=[
        OpenApiExample(
            'Submit Review Request',
            value={
                'overall_rating': 5,
                'service_rating': 5,
                'quality_rating': 4,
                'value_rating': 5,
                'comment': 'Amazing food and excellent service! The pizza was delicious and arrived hot. Staff was very friendly and accommodating. Highly recommended!',
                'would_recommend': True
            },
            request_only=True
        ),
        OpenApiExample(
            'Review Submitted Response',
            value={
                'message': 'Review submitted successfully',
                'review': {
                    'id': 45,
                    'overall_rating': 5,
                    'service_rating': 5,
                    'quality_rating': 4,
                    'value_rating': 5,
                    'comment': 'Amazing food and excellent service!',
                    'would_recommend': True,
                    'reviewer_name': 'John Doe',
                    'reviewer_email': 'john.doe@example.com',
                    'status': 'pending',
                    'created_at': '2025-01-20T18:30:00Z'
                }
            },
            response_only=True
        )
    ],
    responses={
        201: 'Review submitted successfully',
        400: OpenApiExample(
            'Validation or Business Rule Error',
            value={'error': 'Review already submitted for this order'},
            response_only=True
        ),
        404: OpenApiExample(
            'Invalid Token',
            value={'error': 'Invalid review token'},
            response_only=True
        )
    }
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


# ===== PAYMENT VIEWS =====

from .models import Payment, Plan
from .serializers import PaymentSerializer
from .paypal import create_paypal_order, capture_paypal_order

PLAN_PRICING = {
    'basic': {'amount': 29.99, 'review_limit': 100},
    'standard': {'amount': 99.99, 'review_limit': 1000},
    'premium': {'amount': 199.99, 'review_limit': 10000},
}

@extend_schema(
    operation_id='payment_operations',
    tags=['Payment'],
    summary='Payment Operations',
    description="""
    Handle all payment-related operations through a single endpoint.
    
    **GET Operations (via ?action= parameter):**
    - `action=pricing`: Get available subscription plans and pricing
    - `action=user-plan`: Get current user's subscription plan
    - No action (default): List user's payment history
    
    **POST Operations (via action field in request body):**
    - `action=create-order`: Create a new PayPal payment order
    - `action=capture`: Capture and complete a PayPal payment
    """,
    parameters=[
        OpenApiParameter(
            name='action',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Action to perform for GET requests',
            enum=['pricing', 'user-plan'],
            required=False
        )
    ],
    examples=[
        OpenApiExample(
            'Create PayPal Order Request',
            value={
                'action': 'create-order',
                'plan_type': 'standard'
            },
            request_only=True
        ),
        OpenApiExample(
            'Capture Payment Request',
            value={
                'action': 'capture',
                'paypal_order_id': '8XY12345ABC678DEF'
            },
            request_only=True
        ),
        OpenApiExample(
            'Plan Pricing Response',
            value={
                'basic': {'amount': 29.99, 'review_limit': 100},
                'standard': {'amount': 99.99, 'review_limit': 1000},
                'premium': {'amount': 199.99, 'review_limit': 10000}
            },
            response_only=True
        ),
        OpenApiExample(
            'User Plan Response',
            value={
                'plan_type': 'standard',
                'review_limit': 1000,
                'created_at': '2025-01-15T10:30:00Z'
            },
            response_only=True
        ),
        OpenApiExample(
            'PayPal Order Created Response',
            value={
                'order_id': '8XY12345ABC678DEF',
                'payment_id': 42,
                'approval_url': 'https://www.paypal.com/checkoutnow?token=8XY12345ABC678DEF'
            },
            response_only=True
        ),
        OpenApiExample(
            'Payment Captured Response',
            value={
                'message': 'Payment successful and plan upgraded',
                'plan': {
                    'type': 'standard',
                    'review_limit': 1000
                }
            },
            response_only=True
        ),
        OpenApiExample(
            'Payment History Response',
            value=[
                {
                    'id': 42,
                    'plan_type': 'standard',
                    'amount': 99.99,
                    'currency': 'USD',
                    'status': 'completed',
                    'paypal_order_id': '8XY12345ABC678DEF',
                    'created_at': '2025-01-15T10:30:00Z'
                }
            ],
            response_only=True
        )
    ],
    responses={
        200: 'Success - varies by action',
        400: OpenApiExample(
            'Validation Error',
            value={'error': 'Invalid plan type'},
            response_only=True
        ),
        403: OpenApiExample(
            'Permission Denied',
            value={'error': 'Permission denied'},
            response_only=True
        ),
        404: OpenApiExample(
            'Payment Not Found',
            value={'error': 'Payment not found'},
            response_only=True
        ),
        500: OpenApiExample(
            'PayPal API Error',
            value={'error': 'PayPal API temporarily unavailable'},
            response_only=True
        )
    }
)
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def payment_view(request):
    """Handle all payment operations"""
    if request.method == 'GET':
        action = request.GET.get('action', 'list')
        
        if action == 'pricing':
            return Response(PLAN_PRICING)
        
        elif action == 'user-plan':
            try:
                plan = Plan.objects.get(user=request.user)
                return Response({
                    'plan_type': plan.plan_type,
                    'review_limit': plan.review_limit,
                    'created_at': plan.created_at
                })
            except Plan.DoesNotExist:
                return Response({
                    'plan_type': 'basic',
                    'review_limit': 50,
                    'created_at': None
                })
        
        else:  # list payments
            if request.user.is_staff:
                queryset = Payment.objects.all()
            else:
                queryset = Payment.objects.filter(user=request.user)
            serializer = PaymentSerializer(queryset, many=True)
            return Response(serializer.data)
    
    elif request.method == 'POST':
        action = request.data.get('action')
        
        if action == 'create-order':
            plan_type = request.data.get('plan_type')
            if plan_type not in PLAN_PRICING:
                return Response({'error': 'Invalid plan type'}, status=400)
            
            amount = PLAN_PRICING[plan_type]['amount']
            try:
                order_data = create_paypal_order(amount, 'USD')
                payment = Payment.objects.create(
                    user=request.user,
                    plan_type=plan_type,
                    paypal_order_id=order_data['id'],
                    amount=amount,
                    status='created',
                    raw_response=order_data
                )
                return Response({
                    'order_id': order_data['id'],
                    'payment_id': payment.id,
                    'approval_url': next(
                        link['href'] for link in order_data['links'] 
                        if link['rel'] == 'approve'
                    )
                })
            except Exception as e:
                return Response({'error': str(e)}, status=500)
        
        elif action == 'capture':
            paypal_order_id = request.data.get('paypal_order_id')
            if not paypal_order_id:
                return Response({'error': 'PayPal order ID required'}, status=400)
            
            try:
                payment = get_object_or_404(Payment, paypal_order_id=paypal_order_id)
                if payment.user != request.user and not request.user.is_staff:
                    return Response({'error': 'Permission denied'}, status=403)
                
                capture_result = capture_paypal_order(paypal_order_id)
                if capture_result['status'] == 'COMPLETED':
                    payment.status = 'completed'
                    payment.raw_response = capture_result
                    payment.save()
                    
                    plan, created = Plan.objects.get_or_create(
                        user=request.user,
                        defaults={'plan_type': payment.plan_type}
                    )
                    if not created:
                        plan.plan_type = payment.plan_type
                        plan.review_limit = PLAN_PRICING[payment.plan_type]['review_limit']
                        plan.save()
                    
                    return Response({
                        'message': 'Payment successful and plan upgraded',
                        'plan': {
                            'type': plan.plan_type,
                            'review_limit': plan.review_limit
                        }
                    })
                else:
                    payment.status = 'failed'
                    payment.raw_response = capture_result
                    payment.save()
                    return Response({'error': 'Payment failed'}, status=400)
            except Exception as e:
                return Response({'error': str(e)}, status=500)


# ===== WIDGET VIEWS =====

from django.http import HttpResponse
from django.template.loader import render_to_string

@extend_schema(
    operation_id='widget_operations',
    tags=['Widget'],
    summary='Review Widget Operations',
    description="""
    Handle all widget-related operations for embedding business reviews on external websites.
    This endpoint is public and doesn't require authentication.
    
    **Available Actions (via ?action= parameter):**
    - `embed` (default): Returns HTML widget for embedding
    - `data`: Returns JSON data for custom widget implementations
    - `script`: Returns JavaScript code for dynamic widget loading
    
    The widget displays business information, average rating, review count, and recent reviews.
    """,
    parameters=[
        OpenApiParameter(
            name='user_id',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
            description='ID of the business owner user',
            required=True
        ),
        OpenApiParameter(
            name='action',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Widget action to perform',
            enum=['embed', 'data', 'script'],
            required=False
        )
    ],
    examples=[
        OpenApiExample(
            'Widget Data Response',
            value={
                'business': {
                    'id': 1,
                    'name': 'My Awesome Restaurant',
                    'address': '123 Main St, City, State 12345',
                    'website': 'https://myrestaurant.com'
                },
                'stats': {
                    'avg_rating': 4.5,
                    'total_reviews': 128,
                    'recommend_percent': 87,
                    'trust_badge': 'Gold',
                    'rating_distribution': {
                        '1': 2,
                        '2': 5,
                        '3': 15,
                        '4': 45,
                        '5': 61
                    }
                },
                'recent_reviews': [
                    {
                        'id': 45,
                        'rating': 5,
                        'comment': 'Amazing food and service!',
                        'reviewer_name': 'John D.',
                        'created_at': '2025-01-20T18:30:00Z'
                    },
                    {
                        'id': 44,
                        'rating': 4,
                        'comment': 'Great experience, will come back!',
                        'reviewer_name': 'Sarah M.',
                        'created_at': '2025-01-19T15:45:00Z'
                    }
                ]
            },
            response_only=True
        )
    ],
    responses={
        200: 'Success - format varies by action (HTML, JSON, or JavaScript)',
        404: OpenApiExample(
            'Business Not Found',
            value={'error': 'Business not found'},
            response_only=True
        )
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def widget_view(request, user_id):
    """Handle all widget operations"""
    action = request.GET.get('action', 'embed')
    
    try:
        user = get_object_or_404(User, id=user_id)
        business = get_object_or_404(Business, owner=user)
        
        # Get reviews for this business
        reviews_qs = Review.objects.filter(order__business=business, status='published')
        
        # Calculate stats
        avg_rating = reviews_qs.aggregate(avg=Avg('overall_rating'))['avg']
        if avg_rating is None:
            avg_rating = 4.5
        avg_rating = round(avg_rating, 1)
        
        total_reviews = reviews_qs.count()
        if total_reviews > 0:
            recommend_count = reviews_qs.filter(overall_rating__gte=4).count()
            recommend_percent = round((recommend_count / total_reviews) * 100)
        else:
            recommend_percent = 92
        
        # Trust badge
        trust_badge = "Bronze"
        if total_reviews >= 50 and avg_rating >= 4.5:
            trust_badge = "Gold"
        elif total_reviews >= 20 and avg_rating >= 4.0:
            trust_badge = "Silver"
        
        if action == 'data':
            # Return JSON data
            reviews = []
            for r in reviews_qs.order_by('-created_at')[:10]:
                reviews.append({
                    "id": r.id,
                    "rating": r.overall_rating,
                    "comment": r.comment,
                    "reviewer_name": r.reviewer_name,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                })
            
            rating_distribution = {}
            for i in range(1, 6):
                rating_distribution[str(i)] = reviews_qs.filter(overall_rating=i).count()
            
            return Response({
                "business": {
                    "id": business.id,
                    "name": business.name,
                    "address": business.address,
                    "website": business.website
                },
                "stats": {
                    "avg_rating": avg_rating,
                    "total_reviews": total_reviews,
                    "recommend_percent": recommend_percent,
                    "trust_badge": trust_badge,
                    "rating_distribution": rating_distribution
                },
                "recent_reviews": reviews
            })
        
        elif action == 'script':
            # Return JavaScript
            api_url = request.build_absolute_uri(f"/api/widget/{user_id}/?action=data")
            script_content = f"""
(function() {{
    var widgetContainer = document.getElementById('rcs-widget-{user_id}');
    if (!widgetContainer) return;
    
    fetch('{api_url}')
        .then(response => response.json())
        .then(data => {{
            widgetContainer.innerHTML = `
                <div class="rcs-widget">
                    <h3>${{data.business.name}}</h3>
                    <div>${{'★'.repeat(Math.round(data.stats.avg_rating))}} ${{data.stats.avg_rating}}/5</div>
                    <div>(${{data.stats.total_reviews}} reviews)</div>
                    <div>${{data.stats.trust_badge}} Trusted</div>
                </div>
            `;
        }})
        .catch(() => widgetContainer.innerHTML = '<div>Unable to load reviews</div>');
}})();
            """
            return HttpResponse(script_content, content_type='application/javascript')
        
        else:  # embed HTML
            reviews = []
            for r in reviews_qs.order_by('-created_at')[:3]:
                reviews.append({
                    "rating": r.overall_rating,
                    "text": r.comment,
                    "user": r.reviewer_name
                })
            
            context = {
                "business": business,
                "avg_rating": avg_rating,
                "recommend_percent": recommend_percent,
                "trust_badge": trust_badge,
                "reviews": reviews,
                "total_reviews": total_reviews
            }
            
            html = render_to_string("widget_embed.html", context)
            return HttpResponse(html)
            
    except (User.DoesNotExist, Business.DoesNotExist):
        if action == 'data':
            return Response({"error": "Business not found"}, status=404)
        elif action == 'script':
            return HttpResponse("console.error('RCS Widget: Business not found');", 
                              content_type='application/javascript', status=404)
        else:
            return HttpResponse("<div>Widget not available</div>", status=404)
