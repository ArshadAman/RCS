from rest_framework import viewsets, status, permissions, filters
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



class CompanyViewSet(viewsets.ModelViewSet):
    """ViewSet for Company CRUD operations"""
    serializer_class = CompanySerializer
    permission_classes = [IsAuthenticated, IsCompanyOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['name', 'email']
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return Company.objects.all()
        return Company.objects.filter(owner=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
    
    @action(detail=True, methods=['get'])
    def dashboard_stats(self, request, pk=None):
        """Get dashboard statistics for a company"""
        company = self.get_object()
        reviews = Review.objects.filter(business__company=company)
        
        stats = {
            'total_businesses': company.businesses.count(),
            'total_reviews': reviews.filter(status='published').count(),
            'pending_reviews': reviews.filter(status='pending').count(),
            'average_rating': reviews.filter(status='published').aggregate(
                avg=Avg('overall_rating')
            )['avg'] or 0,
            'recommendation_percentage': self._calculate_recommendation_percentage(reviews),
            'recent_reviews': ReviewSerializer(
                reviews.filter(status='published').order_by('-created_at')[:10],
                many=True
            ).data,
            'rating_distribution': self._get_rating_distribution(reviews),
        }
        return Response(stats)
    
    def _calculate_recommendation_percentage(self, reviews):
        published_reviews = reviews.filter(status='published')
        if published_reviews.exists():
            recommended = published_reviews.filter(would_recommend=True).count()
            return round((recommended / published_reviews.count()) * 100, 1)
        return 0
    
    def _get_rating_distribution(self, reviews):
        published_reviews = reviews.filter(status='published')
        distribution = {}
        for i in range(1, 6):
            distribution[str(i)] = published_reviews.filter(overall_rating=i).count()
        return distribution


class BusinessViewSet(viewsets.ModelViewSet):
    """ViewSet for Business CRUD operations"""
    serializer_class = BusinessSerializer
    permission_classes = [IsAuthenticated, IsBusinessOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'company', 'is_active']
    search_fields = ['name', 'description', 'category']
    ordering_fields = ['name', 'created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return Business.objects.all()
        return Business.objects.filter(
            Q(company__owner=self.request.user) | Q(owner=self.request.user)
        )
    
    def get_serializer_class(self):
        if self.action == 'create':
            return BusinessCreateSerializer
        return BusinessSerializer
    
    def perform_create(self, serializer):
        # Ensure the business is created under a company owned by the user
        company = serializer.validated_data.get('company')
        if company.owner != self.request.user:
            raise PermissionDenied("You can only create businesses under your own companies")
        serializer.save(owner=self.request.user)
    
    @action(detail=True, methods=['get'])
    def reviews(self, request, pk=None):
        """Get all reviews for a business"""
        business = self.get_object()
        reviews = Review.objects.filter(business=business)
        
        # Filter by status if not owner
        if business.owner != request.user and not request.user.is_staff:
            reviews = reviews.filter(status='published')
        
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def public_reviews(self, request, pk=None):
        """Get public reviews for a business (for widget)"""
        business = self.get_object()
        reviews = Review.objects.filter(
            business=business,
            status='published'
        ).order_by('-created_at')[:20]
        
        serializer = PublicReviewSerializer(reviews, many=True)
        return Response(serializer.data)


class OrderViewSet(viewsets.ModelViewSet):
    """ViewSet for Order management"""
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = OrderFilter
    ordering = ['-created_at']
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return Order.objects.all()
        return Order.objects.filter(business__company__owner=self.request.user)
    
    def perform_create(self, serializer):
        business = serializer.validated_data.get('business')
        if business.company.owner != self.request.user:
            raise PermissionDenied("You can only create orders for your own businesses")
        serializer.save()
    
    @action(detail=True, methods=['post'])
    def send_review_request(self, request, pk=None):
        """Send review request email to customer"""
        order = self.get_object()
        
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
        success = self._send_review_email(order)
        
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
    
    def _send_review_email(self, order):
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


class ReviewViewSet(viewsets.ModelViewSet):
    """ViewSet for Review management"""
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = ReviewFilter
    ordering = ['-created_at']
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return Review.objects.all()
        # Return reviews for businesses owned by the user
        return Review.objects.filter(business__company__owner=self.request.user)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ReviewCreateSerializer
        return ReviewSerializer
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a review"""
        review = self.get_object()
        
        if review.business.company.owner != request.user and not request.user.is_staff:
            raise PermissionDenied("You can only approve reviews for your own businesses")
        
        review.status = 'published'
        review.save()
        
        return Response({'message': 'Review approved successfully'})
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a review"""
        review = self.get_object()
        
        if review.business.company.owner != request.user and not request.user.is_staff:
            raise PermissionDenied("You can only reject reviews for your own businesses")
        
        review.status = 'rejected'
        review.save()
        
        return Response({'message': 'Review rejected successfully'})
    
    @action(detail=True, methods=['post'])
    def respond(self, request, pk=None):
        """Add business response to review"""
        review = self.get_object()
        
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


class ReviewCriteriaViewSet(viewsets.ModelViewSet):
    """ViewSet for Review Criteria management"""
    serializer_class = ReviewCriteriaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['company', 'is_active']
    ordering = ['order']
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return ReviewCriteria.objects.all()
        return ReviewCriteria.objects.filter(company__owner=self.request.user)
    
    def perform_create(self, serializer):
        company = serializer.validated_data.get('company')
        if company.owner != self.request.user:
            raise PermissionDenied("You can only create criteria for your own companies")
        serializer.save()


class EmailTemplateViewSet(viewsets.ModelViewSet):
    """ViewSet for Email Template management"""
    serializer_class = EmailTemplateSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['company', 'template_type']
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return EmailTemplate.objects.all()
        return EmailTemplate.objects.filter(company__owner=self.request.user)
    
    def perform_create(self, serializer):
        company = serializer.validated_data.get('company')
        if company.owner != self.request.user:
            raise PermissionDenied("You can only create templates for your own companies")
        serializer.save()


class WidgetSettingsViewSet(viewsets.ModelViewSet):
    """ViewSet for Widget Settings management"""
    serializer_class = WidgetSettingsSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['company']
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return WidgetSettings.objects.all()
        return WidgetSettings.objects.filter(company__owner=self.request.user)
    
    def perform_create(self, serializer):
        company = serializer.validated_data.get('company')
        if company.owner != self.request.user:
            raise PermissionDenied("You can only create widget settings for your own companies")
        serializer.save()


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


# Legacy views for backward compatibility

class CategoryListView(viewsets.ReadOnlyModelViewSet):
    """Read-only ViewSet for Categories"""
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]


class QRFeedbackViewSet(viewsets.ModelViewSet):
    """ViewSet for QR Feedback management"""
    serializer_class = QRFeedbackSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['company', 'branch_id', 'rating']
    ordering = ['-created_at']
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return QRFeedback.objects.all()
        return QRFeedback.objects.filter(company__owner=self.request.user)
