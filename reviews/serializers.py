from rest_framework import serializers
from django.db import transaction
from .models import (
    Business, Review, ReviewImage, ReviewLike, Category, Company, Order, 
    SurveyQuestion, Plan, Badge, QRFeedback, ReviewAnswer, ReviewCriteria,
    ReviewCriteriaRating, EmailTemplate, WidgetSettings, Payment
)
from authentication.serializers import UserProfileSerializer


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for Category model"""
    
    class Meta:
        model = Category
        fields = '__all__'


class BusinessSerializer(serializers.ModelSerializer):
    """Serializer for Business model"""
    
    owner = UserProfileSerializer(read_only=True)
    average_rating = serializers.ReadOnlyField()
    total_reviews = serializers.ReadOnlyField()
    
    class Meta:
        model = Business
        fields = '__all__'
        read_only_fields = ('owner', 'created_at', 'updated_at')


class BusinessCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a business"""
    
    class Meta:
        model = Business
        exclude = ('owner', 'created_at', 'updated_at')


class ReviewImageSerializer(serializers.ModelSerializer):
    """Serializer for Review Images"""
    
    class Meta:
        model = ReviewImage
        fields = '__all__'
        read_only_fields = ('uploaded_at',)


class ReviewSerializer(serializers.ModelSerializer):
    """Serializer for Review model"""
    
    reviewer = UserProfileSerializer(read_only=True)
    business = BusinessSerializer(read_only=True)
    images = ReviewImageSerializer(many=True, read_only=True)
    likes_count = serializers.SerializerMethodField()
    user_has_liked = serializers.SerializerMethodField()
    
    class Meta:
        model = Review
        fields = '__all__'
        read_only_fields = (
            'reviewer', 'business', 'is_approved', 'is_featured',
            'response', 'response_date', 'created_at', 'updated_at'
        )
    
    def get_likes_count(self, obj):
        return obj.likes.count()
    
    def get_user_has_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.likes.filter(user=request.user).exists()
        return False


class ReviewAnswerSerializer(serializers.ModelSerializer):
    """Serializer for dynamic survey answers"""
    
    class Meta:
        model = ReviewAnswer
        fields = '__all__'


class ReviewCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a review with dynamic survey answers"""
    images = serializers.ListField(
        child=serializers.ImageField(),
        required=False,
        allow_empty=True,
        max_length=5
    )
    answers = ReviewAnswerSerializer(many=True, required=False)

    class Meta:
        model = Review
        fields = (
            'overall_rating', 'comment', 'reviewer_name',
            'reviewer_email', 'is_anonymous', 'images', 'answers'
        )

    def create(self, validated_data):
        images_data = validated_data.pop('images', [])
        answers_data = validated_data.pop('answers', [])
        review = Review.objects.create(**validated_data)
        # Create review images
        for image_data in images_data:
            ReviewImage.objects.create(review=review, image=image_data)
        # Create dynamic survey answers
        for answer in answers_data:
            ReviewAnswer.objects.create(review=review, **answer)
        return review


class ReviewCriteriaRatingSerializer(serializers.ModelSerializer):
    """Serializer for individual criteria ratings"""
    
    criteria_name = serializers.CharField(source='criteria.name', read_only=True)
    
    class Meta:
        model = ReviewCriteriaRating
        fields = ['criteria', 'criteria_name', 'rating']


class PublicReviewSerializer(serializers.ModelSerializer):
    """Serializer for public review submission and display"""
    
    criteria_ratings = ReviewCriteriaRatingSerializer(many=True, required=False)
    
    class Meta:
        model = Review
        fields = [
            'id', 'overall_rating', 'would_recommend', 'comment',
            'customer_name', 'customer_email', 'criteria_ratings',
            'status', 'created_at'
        ]
        read_only_fields = ['id', 'status', 'created_at']
    
    @transaction.atomic
    def create(self, validated_data):
        criteria_ratings_data = validated_data.pop('criteria_ratings', [])
        
        # Set default values for required fields
        if not validated_data.get('overall_rating'):
            validated_data['overall_rating'] = 3
        
        # Create review
        review = Review.objects.create(**validated_data)
        
        # Create criteria ratings
        for rating_data in criteria_ratings_data:
            ReviewCriteriaRating.objects.create(
                review=review,
                **rating_data
            )
        
        return review


class ReviewResponseSerializer(serializers.ModelSerializer):
    """Serializer for business response to review"""
    
    class Meta:
        model = Review
        fields = ('business_response',)
    
    def update(self, instance, validated_data):
        instance.business_response = validated_data.get('business_response', instance.business_response)
        instance.save()
        return instance


class ReviewLikeSerializer(serializers.ModelSerializer):
    """Serializer for Review Likes"""
    
    class Meta:
        model = ReviewLike
        fields = '__all__'
        read_only_fields = ('user', 'created_at')


class BusinessSummarySerializer(serializers.ModelSerializer):
    """Lightweight serializer for business summary"""
    
    average_rating = serializers.ReadOnlyField()
    total_reviews = serializers.ReadOnlyField()
    
    class Meta:
        model = Business
        fields = (
            'id', 'name', 'category', 'logo', 'average_rating', 'total_reviews'
        )


class CompanySerializer(serializers.ModelSerializer):
    """Serializer for Company model"""
    
    class Meta:
        model = Company
        fields = [
            'id', 'name', 'unique_id', 'logo', 'website', 'email', 
            'phone_number', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['unique_id', 'created_at', 'updated_at']


class ReviewCriteriaSerializer(serializers.ModelSerializer):
    """Serializer for ReviewCriteria model"""
    
    class Meta:
        model = ReviewCriteria
        fields = ['id', 'name', 'is_active', 'order', 'created_at']
        read_only_fields = ['created_at']


class OrderSerializer(serializers.ModelSerializer):
    """Serializer for Order model with review link generation"""
    
    review_url = serializers.ReadOnlyField()
    
    class Meta:
        model = Order
        fields = [
            'id', 'business', 'order_number', 'customer_email', 'customer_name',
            'product_service_name', 'purchase_date', 'status', 'review_url',
            'email_sent_at', 'created_at'
        ]
        read_only_fields = ['review_link_token', 'review_url', 'email_sent_at', 'created_at']


class EmailTemplateSerializer(serializers.ModelSerializer):
    """Serializer for EmailTemplate model"""
    
    class Meta:
        model = EmailTemplate
        fields = '__all__'


class WidgetSettingsSerializer(serializers.ModelSerializer):
    """Serializer for WidgetSettings model"""
    
    class Meta:
        model = WidgetSettings
        fields = '__all__'


class SurveyQuestionSerializer(serializers.ModelSerializer):
    """Serializer for SurveyQuestion model"""
    
    class Meta:
        model = SurveyQuestion
        fields = '__all__'


class PlanSerializer(serializers.ModelSerializer):
    """Serializer for Plan model"""
    
    class Meta:
        model = Plan
        fields = '__all__'


class BadgeSerializer(serializers.ModelSerializer):
    """Serializer for Badge model"""
    
    class Meta:
        model = Badge
        fields = '__all__'


class QRFeedbackSerializer(serializers.ModelSerializer):
    """Serializer for QRFeedback model"""
    
    class Meta:
        model = QRFeedback
        fields = '__all__'
        read_only_fields = ['created_at', 'ip_address']


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer for Payment model"""
    
    class Meta:
        model = Payment
        fields = '__all__'
