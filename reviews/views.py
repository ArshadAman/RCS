from rest_framework import status, permissions, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import ValidationError, PermissionDenied
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Avg, Count
from django.utils import timezone
from django.http import JsonResponse
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
import uuid
import qrcode
from io import BytesIO
import base64

from .models import (
    Business, Review, ReviewImage, ReviewLike, Category, Company, Order, 
    SurveyQuestion, Plan, Badge, QRFeedback, ReviewAnswer, ReviewCriteria,
    ReviewCriteriaRating, EmailTemplate, WidgetSettings
)
from .serializers import (
    BusinessSerializer, BusinessCreateSerializer, ReviewSerializer,
    ReviewCreateSerializer, ReviewLikeSerializer, CategorySerializer,
    CompanySerializer, OrderSerializer, SurveyQuestionSerializer,
    PlanSerializer, BadgeSerializer, QRFeedbackSerializer,
    ReviewAnswerSerializer, ReviewCriteriaSerializer, ReviewCriteriaRatingSerializer,
    EmailTemplateSerializer, WidgetSettingsSerializer, PublicReviewSerializer
)
from .permissions import IsCompanyOwnerOrReadOnly, IsBusinessOwnerOrReadOnly
from .filters import ReviewFilter, OrderFilter


# Helper functions
def _calculate_recommendation_percentage(reviews):
    """Calculate recommendation percentage from reviews"""
    published_reviews = reviews.filter(status='published')
    if published_reviews.exists():
        recommended = published_reviews.filter(would_recommend=True).count()
        return round((recommended / published_reviews.count()) * 100, 1)
    return 0

def _get_rating_distribution(reviews):
    """Get rating distribution from reviews"""
    published_reviews = reviews.filter(status='published')
    distribution = {}
    for i in range(1, 6):
        distribution[str(i)] = published_reviews.filter(overall_rating=i).count()
    return distribution

def _send_review_email(order):
    """Send personalized review request email"""
    try:
        # Get email template
        template = EmailTemplate.objects.filter(
            company=order.business.company,
            template_type='review_request'
        ).first()
        
        if not template:
            # Use default template
            subject = f"How was your experience with {order.business.name}?"
            message = f"Hi {order.customer_name},\n\nWe'd love to hear about your recent experience with {order.business.name}.\n\nPlease click the link below to leave a review:\n{settings.FRONTEND_URL}/review/{order.review_token}\n\nThank you!"
        else:
            subject = template.subject.format(
                customer_name=order.customer_name,
                business_name=order.business.name
            )
            message = template.body.format(
                customer_name=order.customer_name,
                business_name=order.business.name,
                review_link=f"{settings.FRONTEND_URL}/review/{order.review_token}"
            )
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[order.customer_email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Email sending failed: {e}")
        return False


# Company CRUD views
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def company_list_create_view(request):
    """List companies or create a new company"""
    
    if request.method == 'GET':
        if request.user.is_staff:
            queryset = Company.objects.all()
        else:
            queryset = Company.objects.filter(owner=request.user)
        
        # Apply search filtering
        search = request.GET.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(email__icontains=search)
            )
        
        serializer = CompanySerializer(queryset, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = CompanySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(owner=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def company_detail_view(request, pk):
    """Retrieve, update or delete a specific company"""
    
    try:
        if request.user.is_staff:
            company = Company.objects.get(pk=pk)
        else:
            company = Company.objects.get(pk=pk, owner=request.user)
    except Company.DoesNotExist:
        return Response({'error': 'Company not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Check permissions
    if not request.user.is_staff and company.owner != request.user:
        raise PermissionDenied("You can only access your own companies")
    
    if request.method == 'GET':
        serializer = CompanySerializer(company)
        return Response(serializer.data)
    
    elif request.method in ['PUT', 'PATCH']:
        partial = request.method == 'PATCH'
        serializer = CompanySerializer(company, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    
    elif request.method == 'DELETE':
        company.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def company_dashboard_stats_view(request, pk):
    """Get dashboard statistics for a company"""
    
    try:
        if request.user.is_staff:
            company = Company.objects.get(pk=pk)
        else:
            company = Company.objects.get(pk=pk, owner=request.user)
    except Company.DoesNotExist:
        return Response({'error': 'Company not found'}, status=status.HTTP_404_NOT_FOUND)
    
    reviews = Review.objects.filter(business__company=company)
    
    stats = {
        'total_businesses': company.businesses.count(),
        'total_reviews': reviews.filter(status='published').count(),
        'pending_reviews': reviews.filter(status='pending').count(),
        'average_rating': reviews.filter(status='published').aggregate(
            avg=Avg('overall_rating')
        )['avg'] or 0,
        'recommendation_percentage': _calculate_recommendation_percentage(reviews),
        'recent_reviews': ReviewSerializer(
            reviews.filter(status='published').order_by('-created_at')[:10],
            many=True
        ).data,
        'rating_distribution': _get_rating_distribution(reviews),
    }
    return Response(stats)


# Business CRUD views
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def business_list_create_view(request):
    """List businesses or create a new business"""
    
    if request.method == 'GET':
        if request.user.is_staff:
            queryset = Business.objects.all()
        else:
            queryset = Business.objects.filter(
                Q(company__owner=request.user) | Q(owner=request.user)
            )
        
        # Apply filters
        category = request.GET.get('category')
        company_id = request.GET.get('company')
        is_active = request.GET.get('is_active')
        search = request.GET.get('search', '')
        
        if category:
            queryset = queryset.filter(category=category)
        if company_id:
            queryset = queryset.filter(company=company_id)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | 
                Q(description__icontains=search) |
                Q(category__icontains=search)
            )
        
        # Apply ordering
        ordering = request.GET.get('ordering', '-created_at')
        queryset = queryset.order_by(ordering)
        
        serializer = BusinessSerializer(queryset, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = BusinessCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Ensure the business is created under a company owned by the user
        company = serializer.validated_data.get('company')
        if company.owner != request.user:
            raise PermissionDenied("You can only create businesses under your own companies")
        
        serializer.save(owner=request.user)
        return Response(BusinessSerializer(serializer.instance).data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def business_detail_view(request, pk):
    """Retrieve, update or delete a specific business"""
    
    try:
        if request.user.is_staff:
            business = Business.objects.get(pk=pk)
        else:
            business = Business.objects.filter(
                pk=pk
            ).filter(
                Q(company__owner=request.user) | Q(owner=request.user)
            ).first()
            if not business:
                raise Business.DoesNotExist
    except Business.DoesNotExist:
        return Response({'error': 'Business not found'}, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        serializer = BusinessSerializer(business)
        return Response(serializer.data)
    
    elif request.method in ['PUT', 'PATCH']:
        # Check permissions
        if not request.user.is_staff and business.owner != request.user:
            raise PermissionDenied("You can only modify your own businesses")
        
        partial = request.method == 'PATCH'
        serializer = BusinessSerializer(business, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    
    elif request.method == 'DELETE':
        # Check permissions
        if not request.user.is_staff and business.owner != request.user:
            raise PermissionDenied("You can only delete your own businesses")
        
        business.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def business_reviews_view(request, pk):
    """Get all reviews for a business"""
    
    try:
        if request.user.is_staff:
            business = Business.objects.get(pk=pk)
        else:
            business = Business.objects.filter(
                pk=pk
            ).filter(
                Q(company__owner=request.user) | Q(owner=request.user)
            ).first()
            if not business:
                raise Business.DoesNotExist
    except Business.DoesNotExist:
        return Response({'error': 'Business not found'}, status=status.HTTP_404_NOT_FOUND)
    
    reviews = Review.objects.filter(business=business)
    
    # Filter by status if not owner
    if business.owner != request.user and not request.user.is_staff:
        reviews = reviews.filter(status='published')
    
    serializer = ReviewSerializer(reviews, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def business_public_reviews_view(request, pk):
    """Get public reviews for a business (for widget)"""
    
    try:
        business = Business.objects.get(pk=pk)
    except Business.DoesNotExist:
        return Response({'error': 'Business not found'}, status=status.HTTP_404_NOT_FOUND)
    
    reviews = Review.objects.filter(
        business=business,
        status='published'
    ).order_by('-created_at')[:20]
    
    serializer = PublicReviewSerializer(reviews, many=True)
    return Response(serializer.data)


# Order CRUD views
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def order_list_create_view(request):
    """List orders or create a new order"""
    
    if request.method == 'GET':
        if request.user.is_staff:
            queryset = Order.objects.all()
        else:
            queryset = Order.objects.filter(business__company__owner=request.user)
        
        # Apply ordering
        ordering = request.GET.get('ordering', '-created_at')
        queryset = queryset.order_by(ordering)
        
        serializer = OrderSerializer(queryset, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = OrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        business = serializer.validated_data.get('business')
        if business.company.owner != request.user:
            raise PermissionDenied("You can only create orders for your own businesses")
        
        # Automatically set the company based on the business
        serializer.save(company=business.company)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def order_detail_view(request, pk):
    """Retrieve, update or delete a specific order"""
    
    try:
        if request.user.is_staff:
            order = Order.objects.get(pk=pk)
        else:
            order = Order.objects.get(pk=pk, business__company__owner=request.user)
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
        if request.user.is_staff:
            order = Order.objects.get(pk=pk)
        else:
            order = Order.objects.get(pk=pk, business__company__owner=request.user)
    except Order.DoesNotExist:
        return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
    
    if order.status != 'pending':
        return Response(
            {'error': 'Order is not in pending status'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Generate review token if not exists
    if not order.review_token:
        order.review_token = str(uuid.uuid4())
        order.save()
    
    # Send email
    success = _send_review_email(order)
    
    if success:
        order.status = 'review_sent'
        order.review_sent_at = timezone.now()
        order.save()
        return Response({'message': 'Review request sent successfully'})
    else:
        return Response(
            {'error': 'Failed to send review request'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Review CRUD views
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def review_list_create_view(request):
    """List reviews or create a new review"""
    
    if request.method == 'GET':
        if request.user.is_staff:
            queryset = Review.objects.all()
        else:
            # Return reviews for businesses owned by the user
            queryset = Review.objects.filter(business__company__owner=request.user)
        
        # Apply ordering
        ordering = request.GET.get('ordering', '-created_at')
        queryset = queryset.order_by(ordering)
        
        serializer = ReviewSerializer(queryset, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = ReviewCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Enforce plan review limit
        business = serializer.validated_data.get('business')
        company = business.company
        plan = getattr(company, 'plan', None)
        if plan is not None:
            review_limit = plan.review_limit
            current_review_count = Review.objects.filter(business__company=company).count()
            if current_review_count >= review_limit:
                raise ValidationError(f"Review limit reached for your current plan ({plan.get_plan_type_display()}). Please upgrade your plan to add more reviews.")
        
        review = serializer.save()
        return Response(ReviewSerializer(review).data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def review_detail_view(request, pk):
    """Retrieve, update or delete a specific review"""
    
    try:
        if request.user.is_staff:
            review = Review.objects.get(pk=pk)
        else:
            review = Review.objects.get(pk=pk, business__company__owner=request.user)
    except Review.DoesNotExist:
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
        if request.user.is_staff:
            review = Review.objects.get(pk=pk)
        else:
            review = Review.objects.get(pk=pk, business__company__owner=request.user)
    except Review.DoesNotExist:
        return Response({'error': 'Review not found'}, status=status.HTTP_404_NOT_FOUND)
    
    if review.business.company.owner != request.user and not request.user.is_staff:
        raise PermissionDenied("You can only approve reviews for your own businesses")
    
    review.status = 'published'
    review.save()
    
    return Response({'message': 'Review approved successfully'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def review_reject_view(request, pk):
    """Reject a review"""
    
    try:
        if request.user.is_staff:
            review = Review.objects.get(pk=pk)
        else:
            review = Review.objects.get(pk=pk, business__company__owner=request.user)
    except Review.DoesNotExist:
        return Response({'error': 'Review not found'}, status=status.HTTP_404_NOT_FOUND)
    
    if review.business.company.owner != request.user and not request.user.is_staff:
        raise PermissionDenied("You can only reject reviews for your own businesses")
    
    review.status = 'rejected'
    review.save()
    
    return Response({'message': 'Review rejected successfully'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def review_respond_view(request, pk):
    """Add business response to review"""
    
    try:
        if request.user.is_staff:
            review = Review.objects.get(pk=pk)
        else:
            review = Review.objects.get(pk=pk, business__company__owner=request.user)
    except Review.DoesNotExist:
        return Response({'error': 'Review not found'}, status=status.HTTP_404_NOT_FOUND)
    
    if review.business.company.owner != request.user and not request.user.is_staff:
        raise PermissionDenied("You can only respond to reviews for your own businesses")
    
    response_text = request.data.get('response')
    if not response_text:
        return Response(
            {'error': 'Response text is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    review.business_response = response_text
    review.response_date = timezone.now()
    review.save()
    
    return Response({'message': 'Response added successfully'})


# Review Criteria CRUD views
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def review_criteria_list_create_view(request):
    """List review criteria or create a new review criteria"""
    
    if request.method == 'GET':
        if request.user.is_staff:
            queryset = ReviewCriteria.objects.all()
        else:
            queryset = ReviewCriteria.objects.filter(company__owner=request.user)
        
        # Apply filters
        company = request.GET.get('company')
        is_active = request.GET.get('is_active')
        
        if company:
            queryset = queryset.filter(company=company)
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
        
        company = serializer.validated_data.get('company')
        if company.owner != request.user:
            raise PermissionDenied("You can only create criteria for your own companies")
        
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def review_criteria_detail_view(request, pk):
    """Retrieve, update or delete a specific review criteria"""
    
    try:
        if request.user.is_staff:
            criteria = ReviewCriteria.objects.get(pk=pk)
        else:
            criteria = ReviewCriteria.objects.get(pk=pk, company__owner=request.user)
    except ReviewCriteria.DoesNotExist:
        return Response({'error': 'Review criteria not found'}, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        serializer = ReviewCriteriaSerializer(criteria)
        return Response(serializer.data)
    
    elif request.method in ['PUT', 'PATCH']:
        # Check permissions
        if not request.user.is_staff and criteria.company.owner != request.user:
            raise PermissionDenied("You can only modify your own criteria")
        
        partial = request.method == 'PATCH'
        serializer = ReviewCriteriaSerializer(criteria, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    
    elif request.method == 'DELETE':
        # Check permissions
        if not request.user.is_staff and criteria.company.owner != request.user:
            raise PermissionDenied("You can only delete your own criteria")
        
        criteria.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# Email Template CRUD views
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def email_template_list_create_view(request):
    """List email templates or create a new email template"""
    
    if request.method == 'GET':
        if request.user.is_staff:
            queryset = EmailTemplate.objects.all()
        else:
            queryset = EmailTemplate.objects.filter(company__owner=request.user)
        
        # Apply filters
        company = request.GET.get('company')
        template_type = request.GET.get('template_type')
        
        if company:
            queryset = queryset.filter(company=company)
        if template_type:
            queryset = queryset.filter(template_type=template_type)
        
        serializer = EmailTemplateSerializer(queryset, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = EmailTemplateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        company = serializer.validated_data.get('company')
        if company.owner != request.user:
            raise PermissionDenied("You can only create templates for your own companies")
        
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def email_template_detail_view(request, pk):
    """Retrieve, update or delete a specific email template"""
    
    try:
        if request.user.is_staff:
            template = EmailTemplate.objects.get(pk=pk)
        else:
            template = EmailTemplate.objects.get(pk=pk, company__owner=request.user)
    except EmailTemplate.DoesNotExist:
        return Response({'error': 'Email template not found'}, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        serializer = EmailTemplateSerializer(template)
        return Response(serializer.data)
    
    elif request.method in ['PUT', 'PATCH']:
        # Check permissions
        if not request.user.is_staff and template.company.owner != request.user:
            raise PermissionDenied("You can only modify your own templates")
        
        partial = request.method == 'PATCH'
        serializer = EmailTemplateSerializer(template, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    
    elif request.method == 'DELETE':
        # Check permissions
        if not request.user.is_staff and template.company.owner != request.user:
            raise PermissionDenied("You can only delete your own templates")
        
        template.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# Widget Settings CRUD views
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def widget_settings_list_create_view(request):
    """List widget settings or create new widget settings"""
    
    if request.method == 'GET':
        if request.user.is_staff:
            queryset = WidgetSettings.objects.all()
        else:
            queryset = WidgetSettings.objects.filter(company__owner=request.user)
        
        # Apply filters
        company = request.GET.get('company')
        if company:
            queryset = queryset.filter(company=company)
        
        serializer = WidgetSettingsSerializer(queryset, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = WidgetSettingsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        company = serializer.validated_data.get('company')
        if company.owner != request.user:
            raise PermissionDenied("You can only create widget settings for your own companies")
        
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def widget_settings_detail_view(request, pk):
    """Retrieve, update or delete specific widget settings"""
    
    try:
        if request.user.is_staff:
            settings = WidgetSettings.objects.get(pk=pk)
        else:
            settings = WidgetSettings.objects.get(pk=pk, company__owner=request.user)
    except WidgetSettings.DoesNotExist:
        return Response({'error': 'Widget settings not found'}, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        serializer = WidgetSettingsSerializer(settings)
        return Response(serializer.data)
    
    elif request.method in ['PUT', 'PATCH']:
        # Check permissions
        if not request.user.is_staff and settings.company.owner != request.user:
            raise PermissionDenied("You can only modify your own widget settings")
        
        partial = request.method == 'PATCH'
        serializer = WidgetSettingsSerializer(settings, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    
    elif request.method == 'DELETE':
        # Check permissions
        if not request.user.is_staff and settings.company.owner != request.user:
            raise PermissionDenied("You can only delete your own widget settings")
        
        settings.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# Public APIs (no authentication required)

@api_view(['GET'])
@permission_classes([AllowAny])
def public_review_form(request, token):
    """Get review form data for public review submission"""
    try:
        order = Order.objects.get(review_token=token)
        
        # Check if order is still valid
        if order.status not in ['pending', 'review_sent']:
            return Response(
                {'error': 'Review link is no longer valid'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get review criteria for the company
        criteria = ReviewCriteria.objects.filter(
            company=order.business.company,
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
        order = Order.objects.get(review_token=token)
        
        # Check if order is still valid
        if order.status not in ['pending', 'review_sent']:
            return Response(
                {'error': 'Review link is no longer valid'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if review already exists
        if Review.objects.filter(order=order).exists():
            return Response(
                {'error': 'Review has already been submitted for this order'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create review
        review_data = request.data.copy()
        review_data['business'] = order.business.id
        review_data['order'] = order.id
        review_data['customer_name'] = order.customer_name
        review_data['customer_email'] = order.customer_email
        
        serializer = PublicReviewSerializer(data=review_data)
        if serializer.is_valid():
            # Business logic validation
            overall_rating = serializer.validated_data.get('overall_rating', 0)
            comment = serializer.validated_data.get('comment', '')
            
            # Enforce required comments for low ratings
            if overall_rating <= 3 and not comment.strip():
                return Response(
                    {'error': 'Comment is required for ratings of 3 or below'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            review = serializer.save()
            
            # Update order status
            order.status = 'completed'
            order.save()
            
            return Response({
                'message': 'Review submitted successfully',
                'review': ReviewSerializer(review).data
            })
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    except Order.DoesNotExist:
        return Response(
            {'error': 'Invalid review token'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def widget_data(request, company_id):
    """Get widget data for public display"""
    try:
        company = Company.objects.get(unique_id=company_id)
        
        # Get widget settings
        widget_settings = WidgetSettings.objects.filter(company=company).first()
        
        # Get reviews for all businesses under this company
        reviews = Review.objects.filter(
            business__company=company,
            status='published'
        ).order_by('-created_at')
        
        # Get statistics
        total_reviews = reviews.count()
        avg_rating = reviews.aggregate(avg=Avg('overall_rating'))['avg'] or 0
        recommendation_percentage = 0
        
        if total_reviews > 0:
            recommended_count = reviews.filter(would_recommend=True).count()
            recommendation_percentage = round((recommended_count / total_reviews) * 100, 1)
        
        # Get recent reviews based on widget settings
        display_count = widget_settings.display_count if widget_settings else 5
        recent_reviews = reviews[:display_count]
        
        data = {
            'company': CompanySerializer(company).data,
            'widget_settings': WidgetSettingsSerializer(widget_settings).data if widget_settings else None,
            'statistics': {
                'total_reviews': total_reviews,
                'average_rating': round(avg_rating, 1),
                'recommendation_percentage': recommendation_percentage,
            },
            'recent_reviews': PublicReviewSerializer(recent_reviews, many=True).data,
        }
        
        return Response(data)
    
    except Company.DoesNotExist:
        return Response(
            {'error': 'Company not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def generate_qr_code(request, company_id, branch_id):
    """Generate QR code for feedback collection"""
    try:
        company = Company.objects.get(unique_id=company_id)
        
        # Create QR code
        feedback_url = f"{settings.FRONTEND_URL}/qr-feedback/{company_id}/{branch_id}"
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(feedback_url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        qr_image = base64.b64encode(buffer.getvalue()).decode()
        
        return Response({
            'qr_code': f"data:image/png;base64,{qr_image}",
            'feedback_url': feedback_url,
            'company': CompanySerializer(company).data,
        })
    
    except Company.DoesNotExist:
        return Response(
            {'error': 'Company not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def submit_qr_feedback(request, company_id, branch_id):
    """Submit QR-based feedback"""
    try:
        company = Company.objects.get(unique_id=company_id)
        
        # Create feedback data
        feedback_data = request.data.copy()
        feedback_data['company'] = company.id
        feedback_data['branch_id'] = branch_id
        feedback_data['ip_address'] = request.META.get('REMOTE_ADDR', '127.0.0.1')
        
        serializer = QRFeedbackSerializer(data=feedback_data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Feedback submitted successfully',
                'feedback': serializer.data
            })
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    except Company.DoesNotExist:
        return Response(
            {'error': 'Company not found'},
            status=status.HTTP_404_NOT_FOUND
        )


# Additional API endpoints

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_reviews(request, company_id):
    """Export reviews for a company"""
    try:
        company = Company.objects.get(id=company_id)
        
        if company.owner != request.user and not request.user.is_staff:
            raise PermissionDenied("You can only export reviews for your own companies")
        
        reviews = Review.objects.filter(
            business__company=company,
            status='published'
        ).select_related('business', 'order')
        
        # Format data for export
        export_data = []
        for review in reviews:
            export_data.append({
                'business': review.business.name,
                'customer_name': review.customer_name,
                'customer_email': review.customer_email,
                'overall_rating': review.overall_rating,
                'would_recommend': review.would_recommend,
                'comment': review.comment,
                'created_at': review.created_at.isoformat(),
                'order_id': review.order.order_id if review.order else None,
            })
        
        return Response({
            'company': company.name,
            'total_reviews': len(export_data),
            'reviews': export_data
        })
    
    except Company.DoesNotExist:
        return Response(
            {'error': 'Company not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bulk_approve_reviews(request):
    """Bulk approve reviews"""
    review_ids = request.data.get('review_ids', [])
    
    if not review_ids:
        return Response(
            {'error': 'No review IDs provided'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    reviews = Review.objects.filter(
        id__in=review_ids,
        business__company__owner=request.user
    )
    
    updated_count = reviews.update(status='published')
    
    return Response({
        'message': f'{updated_count} reviews approved successfully'
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bulk_reject_reviews(request):
    """Bulk reject reviews"""
    review_ids = request.data.get('review_ids', [])
    
    if not review_ids:
        return Response(
            {'error': 'No review IDs provided'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    reviews = Review.objects.filter(
        id__in=review_ids,
        business__company__owner=request.user
    )
    
    updated_count = reviews.update(status='rejected')
    
    return Response({
        'message': f'{updated_count} reviews rejected successfully'
    })


# Category views  
@api_view(['GET'])
@permission_classes([AllowAny])
def category_list_view(request):
    """List all active categories"""
    queryset = Category.objects.filter(is_active=True)
    serializer = CategorySerializer(queryset, many=True)
    return Response(serializer.data)


# QR Feedback CRUD views
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def qr_feedback_list_create_view(request):
    """List QR feedback or create new QR feedback"""
    
    if request.method == 'GET':
        if request.user.is_staff:
            queryset = QRFeedback.objects.all()
        else:
            queryset = QRFeedback.objects.filter(company__owner=request.user)
        
        # Apply filters
        company = request.GET.get('company')
        branch_id = request.GET.get('branch_id')
        rating = request.GET.get('rating')
        
        if company:
            queryset = queryset.filter(company=company)
        if branch_id:
            queryset = queryset.filter(branch_id=branch_id)
        if rating:
            queryset = queryset.filter(rating=rating)
        
        # Apply ordering
        ordering = request.GET.get('ordering', '-submitted_at')
        queryset = queryset.order_by(ordering)
        
        serializer = QRFeedbackSerializer(queryset, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = QRFeedbackSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        company = serializer.validated_data.get('company')
        if company.owner != request.user:
            raise PermissionDenied("You can only create QR feedback for your own companies")
        
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def qr_feedback_detail_view(request, pk):
    """Retrieve, update or delete specific QR feedback"""
    
    try:
        if request.user.is_staff:
            feedback = QRFeedback.objects.get(pk=pk)
        else:
            feedback = QRFeedback.objects.get(pk=pk, company__owner=request.user)
    except QRFeedback.DoesNotExist:
        return Response({'error': 'QR feedback not found'}, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        serializer = QRFeedbackSerializer(feedback)
        return Response(serializer.data)
    
    elif request.method in ['PUT', 'PATCH']:
        # Check permissions
        if not request.user.is_staff and feedback.company.owner != request.user:
            raise PermissionDenied("You can only modify your own QR feedback")
        
        partial = request.method == 'PATCH'
        serializer = QRFeedbackSerializer(feedback, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    
    elif request.method == 'DELETE':
        # Check permissions
        if not request.user.is_staff and feedback.company.owner != request.user:
            raise PermissionDenied("You can only delete your own QR feedback")
        
        feedback.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
