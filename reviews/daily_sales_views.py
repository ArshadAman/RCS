from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import transaction, models
from django.core.mail import send_mail
from django.conf import settings
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
import csv
import io
import json
from datetime import timedelta

from .models import (
    Business, DailySalesReport, ReviewRequest, Review
)
from .serializers import (
    DailySalesReportSerializer, SalesReportUploadSerializer,
    ReviewRequestSerializer, ReviewSerializer,
    ReviewSubmissionSerializer, ReviewResponseSerializer,
    DashboardStatsSerializer
)


@extend_schema(
    summary="Upload Daily Sales Report",
    description="""
    Upload daily sales report to trigger feedback requests.
    
    **Supported Methods:**
    - **Manual Upload**: Upload CSV file through dashboard
    - **API Integration**: Send JSON data directly
    
    **CSV Format:**
    ```
    Order ID,Customer Name,Email,Phone Number
    ORD001,Ramesh Kumar,ramesh@example.com,+91 9876543210
    ORD002,Anita Sharma,anita@example.com,+91 9123456789
    ```
    
    **JSON Format:**
    ```json
    {
      "report_date": "2025-07-30",
      "orders": [
        {
          "order_id": "ORD001",
          "customer_name": "Ramesh Kumar",
          "email": "ramesh@example.com",
          "phone": "+91 9876543210"
        }
      ]
    }
    ```
    
    **Process:**
    1. Validates customer data
    2. Creates feedback requests
    3. Sends feedback emails
    4. Returns processing summary
    """,
    request=SalesReportUploadSerializer,
    responses={
        201: OpenApiExample(
            'Report Processed Successfully',
            value={
                "message": "Sales report processed successfully",
                "report": {
                    "id": 1,
                    "business_name": "Test Company",
                    "report_date": "2025-07-30",
                    "file_name": "daily_sales_2025-07-30.json",
                    "upload_method": "api",
                    "total_orders": 3,
                    "processed_orders": 3,
                    "emails_sent": 3,
                    "status": "completed",
                    "success_rate": 100.0
                }
            },
            response_only=True
        ),
        400: OpenApiExample(
            'Validation Error',
            value={
                "orders": ["Order 1: 'email' is required and cannot be empty"],
                "report_date": ["Date already exists for today"]
            },
            response_only=True
        )
    },
    examples=[
        OpenApiExample(
            'API Upload Request',
            value={
                "report_date": "2025-07-30",
                "orders": [
                    {
                        "order_id": "ORD001",
                        "customer_name": "Ramesh Kumar",
                        "email": "ramesh@example.com",
                        "phone": "+91 9876543210"
                    },
                    {
                        "order_id": "ORD002",
                        "customer_name": "Anita Sharma",
                        "email": "anita@example.com",
                        "phone": "+91 9123456789"
                    }
                ]
            },
            request_only=True
        )
    ],
    tags=['Daily Sales Reports']
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_sales_report(request):
    """Upload daily sales report and trigger feedback requests"""
    
    # Get user's business
    try:
        business = request.user.business
    except Business.DoesNotExist:
        return Response(
            {'error': 'You must have a business to upload sales reports'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    serializer = SalesReportUploadSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    report_date = serializer.validated_data['report_date']
    orders = serializer.validated_data['orders']
    
    # Check if report already exists for this date
    if DailySalesReport.objects.filter(
        user=request.user,
        business=business,
        report_date=report_date
    ).exists():
        return Response(
            {'error': f'Sales report for {report_date} already exists'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Process the sales report
    with transaction.atomic():
        # Create the sales report
        sales_report = DailySalesReport.objects.create(
            user=request.user,
            business=business,
            report_date=report_date,
            file_name=f"daily_sales_{report_date}.json",
            upload_method='api',
            total_orders=len(orders),
            status='processing'
        )
        
        processed_orders = 0
        emails_sent = 0
        errors = []
        
        for order_data in orders:
            try:
                # Create review request
                review_request = ReviewRequest.objects.create(
                    daily_report=sales_report,
                    business=business,
                    order_id=order_data['order_id'],
                    customer_name=order_data['customer_name'],
                    customer_email=order_data['email'],
                    customer_phone=order_data.get('phone', ''),
                    expires_at=timezone.now() + timedelta(days=7)
                )
                
                # Send review email
                if send_review_email(review_request):
                    emails_sent += 1
                
                processed_orders += 1
                
            except Exception as e:
                errors.append(f"Order {order_data['order_id']}: {str(e)}")
        
        # Update sales report
        sales_report.processed_orders = processed_orders
        sales_report.emails_sent = emails_sent
        sales_report.status = 'completed' if processed_orders == len(orders) else 'partial'
        sales_report.error_log = '\n'.join(errors) if errors else ''
        sales_report.save()
        
        # Serialize and return
        report_serializer = DailySalesReportSerializer(sales_report)
        
        return Response({
            'message': f'Sales report processed successfully. {emails_sent} feedback emails sent.',
            'report': report_serializer.data
        }, status=status.HTTP_201_CREATED)


@extend_schema(
    summary="Get Sales Reports",
    description="Retrieve all sales reports for the authenticated user's business",
    responses={
        200: DailySalesReportSerializer(many=True)
    },
    tags=['Daily Sales Reports']
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_sales_reports(request):
    """Get all sales reports for user's business"""
    
    try:
        business = request.user.business
    except Business.DoesNotExist:
        return Response(
            {'error': 'Business not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    reports = DailySalesReport.objects.filter(business=business)
    serializer = DailySalesReportSerializer(reports, many=True)
    
    return Response(serializer.data)


@extend_schema(
    summary="Submit Customer Feedback",
    description="""
    Submit customer feedback via email link.
    
    **Main Question**: "Would you recommend this store to your friends or family?"
    
    **If YES (Positive Feedback):**
    - Auto 5-star main rating
    - Optional sub-questions for Logistics, Communication, Website Usability
    - Optional comment (no limit)
    - If no sub-ratings given, system assigns 5 stars to all
    - Appears in store's admin panel for response
    
    **If NO (Negative Feedback):**
    - Sub-ratings and detailed comment (min 50 characters) required
    - Review not valid or published until complete
    - Review shown in red in dashboard
    - Auto-publish after 7 days if no action taken
    """,
    request=ReviewSubmissionSerializer,
    responses={
        200: OpenApiExample(
            'Feedback Submitted Successfully',
            value={
                "message": "Thank you for your feedback!",
                "feedback": {
                    "would_recommend": True,
                    "overall_rating": 5,
                    "status": "published",
                    "display_color": "green"
                }
            },
            response_only=True
        ),
        400: OpenApiExample(
            'Validation Error',
            value={
                "negative_comment": ["For negative feedback, please provide a detailed comment (minimum 50 characters) to help us improve."]
            },
            response_only=True
        ),
        404: OpenApiExample(
            'Invalid or Expired Link',
            value={
                "error": "Feedback request not found or has expired"
            },
            response_only=True
        )
    },
    examples=[
        OpenApiExample(
            'Positive Feedback',
            value={
                "would_recommend": True,
                "logistics_rating": 5,
                "communication_rating": 4,
                "website_usability_rating": 5,
                "positive_comment": "Great service and fast delivery!"
            },
            request_only=True
        ),
        OpenApiExample(
            'Negative Feedback',
            value={
                "would_recommend": False,
                "logistics_rating": 2,
                "communication_rating": 1,
                "website_usability_rating": 3,
                "negative_comment": "The delivery was very late and the customer service was unhelpful. The website was confusing to navigate and the checkout process took too long. I expected better service for the price I paid."
            },
            request_only=True
        )
    ],
    tags=['Customer Feedback']
)
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def submit_feedback(request, token):
    """Submit customer feedback via email link"""
    
    # Get feedback request by token
    try:
        feedback_request = ReviewRequest.objects.get(
            email_token=token,
            status='pending'
        )
    except ReviewRequest.DoesNotExist:
        return Response(
            {'error': 'Feedback request not found or has expired'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Check if expired
    if feedback_request.is_expired:
        feedback_request.status = 'expired'
        feedback_request.save()
        return Response(
            {'error': 'This feedback request has expired'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validate review data
    serializer = ReviewSubmissionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    # Create customer review
    with transaction.atomic():
        review = Review.objects.create(
            review_request=feedback_request,
            business=feedback_request.business,
            reviewer_name=feedback_request.customer_name,
            reviewer_email=feedback_request.customer_email,
            would_recommend=serializer.validated_data['would_recommend'],
            comment=serializer.validated_data.get('comment', ''),
            # Map the comment to appropriate fields based on recommendation
            negative_comment=serializer.validated_data.get('comment', '') if not serializer.validated_data['would_recommend'] else '',
            positive_comment=serializer.validated_data.get('comment', '') if serializer.validated_data['would_recommend'] else '',
            overall_rating=serializer.validated_data.get('overall_rating', 5),
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            # NEW: Status logic based on rating (>=3 = positive, <3 = negative)
            status='published' if serializer.validated_data.get('overall_rating', 5) >= 3 else 'pending_moderation',
            # NEW: Auto-publish date for negative reviews (7 days from now)
            auto_publish_date=timezone.now() + timedelta(days=7) if serializer.validated_data.get('overall_rating', 5) < 3 else None
        )
        
        # Update feedback request
        feedback_request.status = 'responded'
        feedback_request.responded_at = timezone.now()
        feedback_request.save()
        
        # NEW: Send email notifications using SendGrid
        from .email_utils import send_review_notification_email
        from .tasks import schedule_auto_publish_review, schedule_review_reminders
        
        if review.overall_rating >= 3:
            # Positive review - thank the customer
            send_review_notification_email(
                review, 
                email_type='customer_thank_you'
            )
        else:
            # Negative review - notify business owner and schedule auto-publish
            send_review_notification_email(
                review, 
                email_type='business_negative_review'
            )
            
            # Schedule auto-publish task
            schedule_auto_publish_review.apply_async(
                args=[review.id],
                eta=review.auto_publish_date
            )
            
            # Schedule reminder emails
            schedule_review_reminders.delay(review.id)
        
        review_data = ReviewSerializer(review).data
        
        return Response({
            'message': 'Thank you for your positive review! It has been published.' if review.overall_rating >= 3 
                      else 'Thank you for your feedback. We have forwarded your concerns to our team. They will have 7 days to respond before your review is automatically published.',
            'review': review_data
        })


@extend_schema(
    summary="Get Feedback Requests",
    description="Get all feedback requests for the authenticated user's business",
    parameters=[
        OpenApiParameter('status', OpenApiTypes.STR, description='Filter by status'),
        OpenApiParameter('days', OpenApiTypes.INT, description='Filter by days (e.g., last 30 days)')
    ],
    responses={
        200: ReviewRequestSerializer(many=True)
    },
    tags=['Customer Feedback']
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_feedback_requests(request):
    """Get feedback requests for user's business"""
    
    try:
        business = request.user.business
    except Business.DoesNotExist:
        return Response(
            {'error': 'Business not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    feedback_requests = ReviewRequest.objects.filter(business=business)
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        feedback_requests = feedback_requests.filter(status=status_filter)
    
    # Filter by days
    days = request.GET.get('days')
    if days:
        try:
            days_int = int(days)
            since_date = timezone.now() - timedelta(days=days_int)
            feedback_requests = feedback_requests.filter(created_at__gte=since_date)
        except ValueError:
            pass
    
    serializer = ReviewRequestSerializer(feedback_requests, many=True)
    return Response(serializer.data)


@extend_schema(
    summary="Get Customer Reviews",
    description="Get all customer reviews for the authenticated user's business",
    parameters=[
        OpenApiParameter('status', OpenApiTypes.STR, description='Filter by status'),
        OpenApiParameter('recommendation', OpenApiTypes.BOOL, description='Filter by recommendation (true/false)'),
        OpenApiParameter('auto_publish_pending', OpenApiTypes.BOOL, description='Show reviews pending auto-publish')
    ],
    responses={
        200: ReviewSerializer(many=True)
    },
    tags=['Customer Reviews']
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_customer_reviews(request):
    """Get customer reviews for user's business"""
    
    try:
        business = request.user.business
    except Business.DoesNotExist:
        return Response(
            {'error': 'Business not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Get reviews from daily sales reports (those with review_request)
    reviews = Review.objects.filter(business=business, review_request__isnull=False)
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        reviews = reviews.filter(status=status_filter)
    
    # Filter by recommendation
    recommendation = request.GET.get('recommendation')
    if recommendation is not None:
        is_positive = recommendation.lower() == 'true'
        reviews = reviews.filter(would_recommend=is_positive)
    
    # Filter by auto-publish pending
    auto_publish_pending = request.GET.get('auto_publish_pending')
    if auto_publish_pending and auto_publish_pending.lower() == 'true':
        reviews = reviews.filter(
            would_recommend=False,
            status='pending_moderation',
            auto_publish_date__lte=timezone.now()
        )
    
    serializer = ReviewSerializer(reviews, many=True)
    return Response(serializer.data)


@extend_schema(
    summary="Respond to Customer Review",
    description="Store owner responds to customer review",
    request=ReviewResponseSerializer,
    responses={
        200: ReviewSerializer
    },
    tags=['Customer Reviews']
)
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def respond_to_review(request, review_id):
    """Store owner responds to customer review"""
    
    try:
        business = request.user.business
    except Business.DoesNotExist:
        return Response(
            {'error': 'Business not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    review = get_object_or_404(Review, id=review_id, business=business, review_request__isnull=False)
    
    serializer = ReviewResponseSerializer(review, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    
    review.store_response = serializer.validated_data['store_response']
    review.responded_by = request.user
    review.response_date = timezone.now()
    review.save()
    
    response_serializer = ReviewSerializer(review)
    return Response(response_serializer.data)


@extend_schema(
    summary="Dashboard Statistics",
    description="Get dashboard statistics for feedback tracking",
    responses={
        200: DashboardStatsSerializer
    },
    tags=['Dashboard']
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    """Get dashboard statistics"""
    
    try:
        business = request.user.business
    except Business.DoesNotExist:
        return Response(
            {'error': 'Business not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Calculate statistics
    review_requests = ReviewRequest.objects.filter(business=business)
    reviews = Review.objects.filter(business=business)
    
    total_review_requests = review_requests.count()
    pending_responses = review_requests.filter(status='pending').count()
    positive_reviews = reviews.filter(overall_rating__gte=4).count()
    negative_reviews = reviews.filter(overall_rating__lt=4).count()
    
    # Auto-publish pending count (negative reviews with no response that's ready to auto-publish)
    auto_publish_pending = reviews.filter(
        overall_rating__lt=4,
        status='pending',
        auto_publish_date__lte=timezone.now(),
        store_response__exact=''  # No response from store
    ).count()
    
    # Average rating
    if reviews.exists():
        avg_rating = reviews.aggregate(avg_rating=models.Avg('overall_rating'))['avg_rating'] or 0
    else:
        avg_rating = 0
    
    # Response rate
    response_rate = 0
    if total_review_requests > 0:
        responded = review_requests.filter(status='responded').count()
        response_rate = (responded / total_review_requests) * 100
    
    # Recent data
    recent_reports = DailySalesReport.objects.filter(business=business)[:5]
    recent_reviews = reviews.order_by('-created_at')[:10]
    pending_moderation = reviews.filter(status='pending')[:5]
    
    stats_data = {
        'total_review_requests': total_review_requests,
        'pending_responses': pending_responses,
        'positive_reviews': positive_reviews,
        'negative_reviews': negative_reviews,
        'auto_publish_pending': auto_publish_pending,
        'average_rating': round(avg_rating, 1),
        'response_rate': round(response_rate, 1),
        'recent_reports': DailySalesReportSerializer(recent_reports, many=True).data,
        'recent_reviews': ReviewSerializer(recent_reviews, many=True).data,
        'pending_moderation': ReviewSerializer(pending_moderation, many=True).data
    }
    
    return Response(stats_data)


# Helper functions
def send_review_email(review_request):
    """Send review request email to customer using SendGrid"""
    from .email_utils import send_review_request_email
    
    try:
        return send_review_request_email(review_request)
    except Exception as e:
        print(f"Email sending failed: {e}")
        return False


def notify_moderation_team(review):
    """Notify moderation team about negative review using SendGrid"""
    from .email_utils import send_review_notification_email
    
    try:
        # Send notification to business owner
        return send_review_notification_email(
            review, 
            email_type='business_negative_review'
        )
    except Exception as e:
        print(f"Moderation notification failed: {e}")
        return False


def get_client_ip(request):
    """Get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
