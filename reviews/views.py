from rest_framework import generics, status, permissions, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import ValidationError
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Avg
from .models import Business, Review, ReviewImage, ReviewLike, Category, Company, Order, SurveyQuestion, Plan, Badge, QRFeedback, ReviewAnswer
from .serializers import (
    BusinessSerializer,
    BusinessCreateSerializer,
    BusinessSummarySerializer,
    ReviewSerializer,
    ReviewCreateSerializer,
    ReviewResponseSerializer,
    ReviewLikeSerializer,
    CategorySerializer,
    CompanySerializer,
    OrderSerializer,
    SurveyQuestionSerializer,
    PlanSerializer,
    BadgeSerializer,
    QRFeedbackSerializer,
    ReviewAnswerSerializer
)


class CategoryListView(generics.ListAPIView):
    """View to list all categories"""
    
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]


class BusinessListCreateView(generics.ListCreateAPIView):
    """View to list and create businesses"""
    
    queryset = Business.objects.filter(is_active=True)
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'owner']
    search_fields = ['name', 'description', 'category']
    ordering_fields = ['name', 'created_at', 'average_rating']
    ordering = ['-created_at']
    
    def get_permissions(self):
        if self.request.method == 'GET':
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return BusinessCreateSerializer
        return BusinessSerializer
    
    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class BusinessDetailView(generics.RetrieveUpdateDestroyAPIView):
    """View to retrieve, update, and delete a business"""
    
    queryset = Business.objects.filter(is_active=True)
    serializer_class = BusinessSerializer
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        if self.request.method == 'GET':
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_object(self):
        obj = super().get_object()
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            if obj.owner != self.request.user:
                self.permission_denied(self.request)
        return obj


class BusinessReviewsView(generics.ListAPIView):
    """View to list reviews for a specific business"""
    
    serializer_class = ReviewSerializer
    permission_classes = [AllowAny]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at', 'rating']
    ordering = ['-created_at']
    
    def get_queryset(self):
        business_id = self.kwargs['business_id']
        return Review.objects.filter(
            business_id=business_id,
            is_approved=True
        ).select_related('reviewer', 'business').prefetch_related('images', 'likes')


class ReviewListCreateView(generics.ListCreateAPIView):
    """View to list and create reviews"""
    
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['business', 'rating', 'is_approved']
    ordering_fields = ['created_at', 'rating']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ReviewCreateSerializer
        return ReviewSerializer
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return Review.objects.all().select_related('reviewer', 'business')
        return Review.objects.filter(is_approved=True).select_related('reviewer', 'business')
    
    def perform_create(self, serializer):
        business_id = self.request.data.get('business_id')
        business = Business.objects.get(id=business_id)
        
        # Check if user already reviewed this business
        if Review.objects.filter(business=business, reviewer=self.request.user).exists():
            raise ValidationError("You have already reviewed this business")
        
        # PLAN LIMIT ENFORCEMENT
        company = getattr(business, 'company', None)
        if company and hasattr(company, 'plan'):
            plan = company.plan
            review_count = Review.objects.filter(business__company=company).count()
            if review_count >= plan.review_limit:
                raise ValidationError(f"Review limit reached for this company's plan.")
        
        serializer.save(reviewer=self.request.user, business=business)


class ReviewDetailView(generics.RetrieveUpdateDestroyAPIView):
    """View to retrieve, update, and delete a review"""
    
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        obj = super().get_object()
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            if obj.reviewer != self.request.user and not self.request.user.is_staff:
                self.permission_denied(self.request)
        return obj


class ReviewResponseView(generics.UpdateAPIView):
    """View for business owners to respond to reviews"""
    
    queryset = Review.objects.all()
    serializer_class = ReviewResponseSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        obj = super().get_object()
        if obj.business.owner != self.request.user:
            self.permission_denied(self.request)
        return obj


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_review_like(request, review_id):
    """Toggle like/unlike for a review"""
    try:
        review = Review.objects.get(id=review_id)
        like, created = ReviewLike.objects.get_or_create(
            review=review,
            user=request.user
        )
        
        if not created:
            like.delete()
            return Response({
                'message': 'Like removed',
                'liked': False,
                'likes_count': review.likes.count()
            })
        else:
            return Response({
                'message': 'Like added',
                'liked': True,
                'likes_count': review.likes.count()
            })
    
    except Review.DoesNotExist:
        return Response({
            'error': 'Review not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def approve_review(request, review_id):
    """Approve a review (admin/business owner only)"""
    try:
        review = Review.objects.get(id=review_id)
        
        # Check if user is staff or business owner
        if not (request.user.is_staff or review.business.owner == request.user):
            return Response({
                'error': 'Permission denied'
            }, status=status.HTTP_403_FORBIDDEN)
        
        review.is_approved = True
        review.save()
        
        return Response({
            'message': 'Review approved successfully'
        })
    
    except Review.DoesNotExist:
        return Response({
            'error': 'Review not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([AllowAny])
def business_stats(request, business_id):
    """Get statistics for a business"""
    try:
        business = Business.objects.get(id=business_id)
        reviews = Review.objects.filter(business=business, is_approved=True)
        
        stats = {
            'total_reviews': reviews.count(),
            'average_rating': business.average_rating,
            'rating_distribution': {
                '5': reviews.filter(rating=5).count(),
                '4': reviews.filter(rating=4).count(),
                '3': reviews.filter(rating=3).count(),
                '2': reviews.filter(rating=2).count(),
                '1': reviews.filter(rating=1).count(),
            }
        }
        
        return Response(stats)
    
    except Business.DoesNotExist:
        return Response({
            'error': 'Business not found'
        }, status=status.HTTP_404_NOT_FOUND)


from rest_framework.views import APIView

class OrderIntakeWebhook(APIView):
    """Webhook endpoint to receive order data from external B2C platforms"""
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = OrderSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SurveyQuestionListCreateView(generics.ListCreateAPIView):
    """View to list and create survey questions"""
    
    queryset = SurveyQuestion.objects.all()
    serializer_class = SurveyQuestionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['company', 'is_active']
    ordering_fields = ['order', 'created_at']
    ordering = ['order']


class SurveyQuestionDetailView(generics.RetrieveUpdateDestroyAPIView):
    """View to retrieve, update, and delete a survey question"""
    
    queryset = SurveyQuestion.objects.all()
    serializer_class = SurveyQuestionSerializer
    permission_classes = [permissions.IsAuthenticated]


class ReviewAnswerListCreateView(generics.ListCreateAPIView):
    """View to list and create review answers"""
    
    queryset = ReviewAnswer.objects.all()
    serializer_class = ReviewAnswerSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['review', 'question']


class ReviewAnswerDetailView(generics.RetrieveUpdateDestroyAPIView):
    """View to retrieve, update, and delete a review answer"""
    
    queryset = ReviewAnswer.objects.all()
    serializer_class = ReviewAnswerSerializer
    permission_classes = [permissions.IsAuthenticated]


@api_view(['GET'])
@permission_classes([AllowAny])
def company_widget_data(request, company_id):
    """Widget API: Returns company rating, badge, and review summary"""
    try:
        company = Company.objects.get(unique_id=company_id)
        businesses = Business.objects.filter(owner=company.owner)
        reviews = Review.objects.filter(business__in=businesses, is_approved=True)
        badge = getattr(company, 'badge', None)
        data = {
            'company': CompanySerializer(company).data,
            'badge': BadgeSerializer(badge).data if badge else None,
            'average_rating': round(reviews.aggregate(Avg('rating'))['rating__avg'] or 0, 2),
            'total_reviews': reviews.count(),
            'recommend_percent': int(100 * reviews.filter(rating__gte=4).count() / reviews.count()) if reviews.count() else 0,
            'recent_reviews': ReviewSerializer(reviews.order_by('-created_at')[:5], many=True).data,
        }
        return Response(data)
    except Company.DoesNotExist:
        return Response({'error': 'Company not found'}, status=404)


@api_view(['POST'])
@permission_classes([AllowAny])
def qr_feedback_submit(request, branch_id):
    """QR-based feedback submission endpoint"""
    try:
        company = Company.objects.get(qr_feedbacks__branch_id=branch_id)
        # Check plan limits
        if hasattr(company, 'plan'):
            feedback_count = QRFeedback.objects.filter(company=company).count()
            if feedback_count >= company.plan.review_limit:
                return Response({'error': 'Feedback limit reached'}, status=400)
        
        data = request.data.copy()
        data['company'] = company.id
        data['branch_id'] = branch_id
        data['ip_address'] = request.META.get('REMOTE_ADDR', '127.0.0.1')
        
        serializer = QRFeedbackSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)
    except Company.DoesNotExist:
        return Response({'error': 'Invalid QR code'}, status=404)

@api_view(['GET'])
@permission_classes([AllowAny])
def generate_qr_code(request, company_id, branch_id):
    """Generate QR code for branch feedback"""
    import qrcode
    from io import BytesIO
    import base64
    
    feedback_url = f"{request.build_absolute_uri('/')[:-1]}/qr-feedback?id={branch_id}"
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
        'feedback_url': feedback_url
    })


from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .serializers import CompanySerializer

class CompanyListView(APIView):
    """List companies accessible to the current user (owner or staff)"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # For now, return all companies if staff, else only companies user owns
        if request.user.is_staff:
            companies = Company.objects.all()
        else:
            companies = Company.objects.filter(owner=request.user)
        serializer = CompanySerializer(companies, many=True)
        return Response(serializer.data)
