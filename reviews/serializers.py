from rest_framework import serializers
from .models import Business, Review, ReviewImage, ReviewLike, Category, Company, Order, SurveyQuestion, Plan, Badge, QRFeedback, ReviewAnswer
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
            'rating', 'title', 'content', 'reviewer_name',
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


class ReviewResponseSerializer(serializers.ModelSerializer):
    """Serializer for business response to review"""
    
    class Meta:
        model = Review
        fields = ('response',)
    
    def update(self, instance, validated_data):
        instance.response = validated_data.get('response', instance.response)
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
        fields = '__all__'


class OrderSerializer(serializers.ModelSerializer):
    """Serializer for Order model"""
    
    class Meta:
        model = Order
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
