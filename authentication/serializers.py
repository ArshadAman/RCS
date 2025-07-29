from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from .models import User


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration with company and plan creation"""
    
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)
    
    # Business/Company fields
    business_name = serializers.CharField(max_length=200, write_only=True)
    website_url = serializers.URLField(required=False, allow_blank=True, write_only=True)
    contact_number = serializers.CharField(max_length=20, write_only=True)
    country = serializers.CharField(max_length=100, write_only=True)
    
    # Plan selection
    plan_type = serializers.ChoiceField(
        choices=[('basic', 'Basic'), ('standard', 'Standard'), ('premium', 'Premium')],
        write_only=True
    )
    
    class Meta:
        model = User
        fields = (
            'username', 'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'phone_number', 'date_of_birth',
            'business_name', 'website_url', 'contact_number', 'country', 'plan_type'
        )
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        
        # Check if business name is already taken
        from reviews.models import Business
        business_name = attrs.get('business_name')
        if Business.objects.filter(name=business_name).exists():
            raise serializers.ValidationError({
                'business_name': 'A business with this name already exists'
            })
        
        return attrs
    
    def create(self, validated_data):
        # Extract business and plan data
        business_name = validated_data.pop('business_name')
        website_url = validated_data.pop('website_url', '')
        contact_number = validated_data.pop('contact_number')
        country = validated_data.pop('country')
        plan_type = validated_data.pop('plan_type')
        validated_data.pop('password_confirm')
        
        # Create user
        user = User.objects.create_user(**validated_data)
        user.is_verified = True
        user.save()
        
        # Create business with the business information
        from reviews.models import Business, Plan
        business = Business.objects.create(
            name=business_name,
            owner=user,
            website=website_url,
            email=user.email,
            phone_number=contact_number,
            category='General',  # Default category
            address='',  # Can be updated later
            description='',  # Can be updated later
        )
        
        # Create plan based on selection
        plan_limits = {
            'basic': 50,
            'standard': 150, 
            'premium': 400
        }
        
        Plan.objects.create(
            user=user,
            plan_type=plan_type,
            review_limit=plan_limits[plan_type]
        )
        
        return user


class EmailVerificationSerializer(serializers.Serializer):
    """Serializer for email verification"""
    
    uid = serializers.CharField()
    token = serializers.CharField()
    
    def validate(self, attrs):
        try:
            uid = force_str(urlsafe_base64_decode(attrs['uid']))
            user = User.objects.get(pk=uid)
            
            if not default_token_generator.check_token(user, attrs['token']):
                raise serializers.ValidationError('Invalid verification token')
            
            if user.is_verified:
                raise serializers.ValidationError('Email already verified')
            
            attrs['user'] = user
            return attrs
            
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError('Invalid verification link')


class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializer for password reset request"""
    
    email = serializers.EmailField()
    
    def validate_email(self, value):
        try:
            user = User.objects.get(email=value)
            self.context['user'] = user
            return value
        except User.DoesNotExist:
            # Don't reveal if email exists for security
            return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer for password reset confirmation"""
    
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField()  # Remove validators
    new_password_confirm = serializers.CharField()
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        
        try:
            uid = force_str(urlsafe_base64_decode(attrs['uid']))
            user = User.objects.get(pk=uid)
            
            if not default_token_generator.check_token(user, attrs['token']):
                raise serializers.ValidationError('Invalid reset token')
            
            attrs['user'] = user
            return attrs
            
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError('Invalid reset link')


class UserLoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    
    email = serializers.EmailField()
    password = serializers.CharField()
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            user = authenticate(
                request=self.context.get('request'),
                username=email,
                password=password
            )
            
            if not user:
                raise serializers.ValidationError('Invalid credentials')
            
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled')
            
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError('Must include email and password')


class UserProfileSerializer(serializers.ModelSerializer):
    """Comprehensive serializer for user profile with business and plan details"""
    
    full_name = serializers.CharField(read_only=True)
    
    # Business information
    business_name = serializers.CharField(source='business.name', read_only=True)
    business_website = serializers.URLField(source='business.website', read_only=True)
    business_email = serializers.EmailField(source='business.email', read_only=True)
    business_phone = serializers.CharField(source='business.phone_number', read_only=True)
    business_address = serializers.CharField(source='business.address', read_only=True)
    business_category = serializers.CharField(source='business.category', read_only=True)
    business_logo = serializers.ImageField(source='business.logo', read_only=True)
    business_description = serializers.CharField(source='business.description', read_only=True)
    business_average_rating = serializers.ReadOnlyField(source='business.average_rating')
    business_total_reviews = serializers.ReadOnlyField(source='business.total_reviews')
    business_recommendation_percentage = serializers.ReadOnlyField(source='business.recommendation_percentage')
    
    # Plan information
    plan_type = serializers.CharField(source='plan.plan_type', read_only=True)
    plan_display_name = serializers.CharField(source='plan.get_plan_type_display', read_only=True)
    review_limit = serializers.IntegerField(source='plan.review_limit', read_only=True)
    plan_created_at = serializers.DateTimeField(source='plan.created_at', read_only=True)
    
    # Plan features based on plan type
    plan_features = serializers.SerializerMethodField()
    
    # Badge information if exists
    badge_type = serializers.CharField(source='badge.badge_type', read_only=True)
    badge_percentage = serializers.FloatField(source='badge.percentage', read_only=True)
    badge_display_name = serializers.CharField(source='badge.get_badge_type_display', read_only=True)
    
    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'avatar', 'phone_number', 'date_of_birth', 'is_verified',
            'date_joined', 'last_login',
            # Business fields
            'business_name', 'business_website', 'business_email', 'business_phone',
            'business_address', 'business_category', 'business_logo', 'business_description',
            'business_average_rating', 'business_total_reviews', 'business_recommendation_percentage',
            # Plan fields
            'plan_type', 'plan_display_name', 'review_limit', 'plan_created_at', 'plan_features',
            # Badge fields
            'badge_type', 'badge_percentage', 'badge_display_name'
        )
        read_only_fields = ('id', 'username', 'email', 'is_verified', 'date_joined', 'last_login')
    
    def get_plan_features(self, obj):
        """Return plan-specific features and limits with pricing info"""
        from reviews.plan_data import get_plan_data
        
        if not hasattr(obj, 'plan') or not obj.plan:
            return get_plan_data('basic')
        
        plan_type = obj.plan.plan_type
        plan_data = get_plan_data(plan_type)
        
        # Override review_limit with actual user's limit
        plan_data['review_limit'] = obj.plan.review_limit
        plan_data['plan_created_at'] = obj.plan.created_at.isoformat() if obj.plan.created_at else None
        
        return plan_data


class PasswordChangeSerializer(serializers.Serializer):
    """Serializer for password change"""
    
    old_password = serializers.CharField()
    new_password = serializers.CharField()  # Remove validators
    new_password_confirm = serializers.CharField()
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("New passwords don't match")
        return attrs
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Old password is incorrect')
        return value
    
    def save(self):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user
