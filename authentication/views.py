from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django_ratelimit.decorators import ratelimit
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from .models import User
from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserProfileSerializer,
    PasswordChangeSerializer,
    EmailVerificationSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer
)


@api_view(['POST'])
@permission_classes([AllowAny])
@ratelimit(key='ip', rate='5/m', method='POST')
def user_registration_view(request):
    """Function-based view for user registration"""
    
    serializer = UserRegistrationSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()
    
    # Get the created business
    from reviews.models import Business
    business = Business.objects.filter(owner=user).first()
    
    # Generate JWT tokens
    refresh = RefreshToken.for_user(user)
    
    response_data = {
        'message': 'Registration successful! Your account and business have been created.',
        'user': UserProfileSerializer(user).data,
        'tokens': {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
    }
    
    # Include business information if created
    if business:
        from reviews.serializers import BusinessSerializer
        response_data['business'] = BusinessSerializer(business).data
        
        # Include plan information
        if hasattr(user, 'plan'):
            from reviews.serializers import PlanSerializer
            response_data['plan'] = PlanSerializer(user.plan).data
    
    return Response(response_data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([AllowAny])
@ratelimit(key='ip', rate='10/m', method='POST')
def user_login_view(request):
    """Function-based view for user login"""
    
    serializer = UserLoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.validated_data['user']
    
    # Generate JWT tokens
    refresh = RefreshToken.for_user(user)
    
    return Response({
        'message': 'Login successful',
        'user': UserProfileSerializer(user).data,
        'tokens': {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
    }, status=status.HTTP_200_OK)


@extend_schema(
    summary="User Profile Management",
    description="""
    **GET:** Retrieve comprehensive user profile information including:
    - Personal user information (name, email, phone, etc.)
    - Business details (company name, website, address, ratings, etc.)
    - Current subscription plan details with features and limitations
    - Badge information (if assigned)
    
    **PUT/PATCH:** Update user profile and business information.
    - Use PATCH for partial updates
    - Use PUT for complete updates
    - Business fields should be prefixed with `business_` in the request
    
    Example business fields:
    - `business_name` → updates business name
    - `business_website` → updates business website
    - `business_email` → updates business contact email
    """,
    responses={
        200: OpenApiExample(
            'Profile Retrieved/Updated Successfully',
            value={
                "id": 2,
                "username": "admin@test.com",
                "email": "admin@test.com",
                "first_name": "John",
                "last_name": "Doe",
                "full_name": "John Doe",
                "avatar": None,
                "phone_number": "+1234567890",
                "date_of_birth": "1990-01-01",
                "is_verified": False,
                "date_joined": "2025-07-29T09:34:54.090566Z",
                "last_login": None,
                "business_name": "Test Company",
                "business_website": "https://testcompany.com",
                "business_email": "contact@testcompany.com",
                "business_phone": "+1234567890",
                "business_address": "123 Test Street, Test City",
                "business_category": "Technology",
                "business_logo": None,
                "business_description": "Test company description",
                "business_average_rating": 4.5,
                "business_total_reviews": 15,
                "business_recommendation_percentage": 85.0,
                "plan_type": "standard",
                "plan_display_name": "Standard",
                "review_limit": 200,
                "plan_created_at": "2025-07-29T09:35:47.231281Z",
                "plan_features": {
                    "name": "Standard Plan",
                    "price": 29,
                    "currency": "USD",
                    "billing_period": "month",
                    "review_limit": 200,
                    "features": [
                        "Up to 200 reviews per month",
                        "Custom email templates",
                        "Advanced widget customization",
                        "Priority email notifications",
                        "Advanced analytics & reporting",
                        "Custom survey questions",
                        "Review response management",
                        "Email support"
                    ],
                    "limitations": [
                        "No white-label options",
                        "Limited API access"
                    ],
                    "plan_created_at": "2025-07-29T09:35:47.231281+00:00"
                },
                "badge_type": "silver",
                "badge_percentage": 75.5,
                "badge_display_name": "Silver"
            },
            response_only=True
        ),
        400: OpenApiExample(
            'Validation Error',
            value={
                "business_email": ["Enter a valid email address."],
                "date_of_birth": ["Date has wrong format. Use one of these formats instead: YYYY-MM-DD."]
            },
            response_only=True
        ),
        401: OpenApiExample(
            'Authentication Required',
            value={
                "detail": "Authentication credentials were not provided."
            },
            response_only=True
        )
    },
    examples=[
        OpenApiExample(
            'Update User Information',
            value={
                "first_name": "John",
                "last_name": "Doe",
                "phone_number": "+1234567890",
                "date_of_birth": "1990-01-01"
            },
            request_only=True
        ),
        OpenApiExample(
            'Update Business Information',
            value={
                "business_name": "Updated Company Name",
                "business_website": "https://newwebsite.com",
                "business_email": "contact@newcompany.com",
                "business_phone": "+1987654321",
                "business_address": "456 New Street, New City",
                "business_category": "E-commerce",
                "business_description": "Updated company description"
            },
            request_only=True
        ),
        OpenApiExample(
            'Update Both User and Business',
            value={
                "first_name": "John",
                "last_name": "Doe",
                "phone_number": "+1234567890",
                "business_name": "My Updated Company",
                "business_website": "https://mycompany.com",
                "business_description": "We provide excellent services"
            },
            request_only=True
        )
    ],
    tags=['Profile Management']
)
@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def user_profile_update_view(request):
    """Function-based view for retrieving and updating user profile with business info"""
    
    user = request.user
    
    if request.method == 'GET':
        serializer = UserProfileSerializer(user)
        return Response(serializer.data)
    
    elif request.method in ['PUT', 'PATCH']:
        partial = request.method == 'PATCH'
        
        # Separate user data from business data
        user_data = {}
        business_data = {}
        
        for key, value in request.data.items():
            if key.startswith('business_'):
                # Map business_ prefixed fields to actual business model fields
                business_field = key.replace('business_', '')
                if business_field == 'phone':
                    business_field = 'phone_number'
                business_data[business_field] = value
            else:
                user_data[key] = value
        
        # Update user data
        if user_data:
            user_serializer = UserProfileSerializer(user, data=user_data, partial=True)
            user_serializer.is_valid(raise_exception=True)
            user_serializer.save()
        
        # Update business data if exists
        if business_data and hasattr(user, 'business'):
            from reviews.serializers import BusinessSerializer
            business_serializer = BusinessSerializer(user.business, data=business_data, partial=True)
            business_serializer.is_valid(raise_exception=True)
            business_serializer.save()
        
        # Return updated profile
        serializer = UserProfileSerializer(user)
        return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def password_change_view(request):
    """Function-based view for changing user password"""
    
    serializer = PasswordChangeSerializer(data=request.data, context={'request': request})
    serializer.is_valid(raise_exception=True)
    serializer.save()
    
    return Response({
        'message': 'Password changed successfully'
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def email_verification_view(request):
    """Function-based view for email verification"""
    
    serializer = EmailVerificationSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    user = serializer.validated_data['user']
    user.is_verified = True
    user.save()
    
    return Response({
        'message': 'Email verified successfully'
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
@ratelimit(key='ip', rate='3/m', method='POST')
def password_reset_request_view(request):
    """Function-based view for password reset request"""
    
    serializer = PasswordResetRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    # Send reset email if user exists
    user = serializer.context.get('user')
    if user:
        from .tasks import send_password_reset_email
        send_password_reset_email.delay(user.id)
    
    # Always return success message for security
    return Response({
        'message': 'If an account with this email exists, you will receive password reset instructions.'
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_confirm_view(request):
    """Function-based view for password reset confirmation"""
    
    serializer = PasswordResetConfirmSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    user = serializer.validated_data['user']
    user.set_password(serializer.validated_data['new_password'])
    user.save()
    
    return Response({
        'message': 'Password reset successful'
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """View for user logout"""
    try:
        refresh_token = request.data.get('refresh_token')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
        
        return Response({
            'message': 'Logout successful'
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'error': 'Invalid token'
        }, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    summary="Get Simple User Profile",
    description="""
    Retrieves the same comprehensive user profile information as the main profile endpoint.
    This is a read-only endpoint that returns complete profile data including:
    - Personal information
    - Business details
    - Plan information with features
    - Badge status
    """,
    responses={
        200: OpenApiExample(
            'Profile Retrieved Successfully',
            value={
                "id": 2,
                "username": "admin@test.com",
                "email": "admin@test.com",
                "full_name": "Admin User",
                "business_name": "Test Company",
                "business_website": "https://testcompany.com",
                "plan_type": "standard",
                "plan_display_name": "Standard",
                "review_limit": 200,
                "plan_features": {
                    "name": "Standard Plan",
                    "price": 29,
                    "features": ["Up to 200 reviews per month", "Custom email templates"]
                }
            },
            response_only=True
        ),
        401: OpenApiExample(
            'Authentication Required',
            value={
                "detail": "Authentication credentials were not provided."
            },
            response_only=True
        )
    },
    tags=['Profile Management']
)
@api_view(['GET'])
@permission_classes([AllowAny])
def user_profile_view(request):
    """Simple view to get current user profile"""
    if request.user.is_authenticated:
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)
    else:
        return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)


@extend_schema(
    summary="Get Subscription Plans",
    description="""
    Retrieves all available subscription plans with detailed pricing and features.
    
    **Query Parameters:**
    - `comparison=true`: Returns plan comparison matrix with side-by-side feature comparison
    - No parameters: Returns standard plan listing with full details
    
    **Plans Available:**
    - **Basic Plan**: Free tier with limited features (50 reviews/month)
    - **Standard Plan**: $29/month with advanced features (200 reviews/month)
    - **Premium Plan**: $99/month with unlimited features (unlimited reviews)
    
    Each plan includes:
    - Pricing information (price, currency, billing period)
    - Review limits and quotas
    - Feature list with detailed capabilities
    - Limitations and restrictions
    """,
    parameters=[
        OpenApiParameter(
            name='comparison',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Set to "true" to get plan comparison data with feature matrix',
            required=False,
            enum=['true', 'false']
        )
    ],
    responses={
        200: OpenApiExample(
            'Standard Plans Response',
            value={
                "basic": {
                    "name": "Basic Plan",
                    "price": 0,
                    "currency": "USD",
                    "billing_period": "month",
                    "review_limit": 50,
                    "features": [
                        "Up to 50 reviews per month",
                        "Basic email templates",
                        "Standard widget",
                        "Email notifications",
                        "Basic analytics",
                        "Community support"
                    ],
                    "limitations": [
                        "Limited customization",
                        "Basic reporting only",
                        "No API access"
                    ]
                },
                "standard": {
                    "name": "Standard Plan",
                    "price": 29,
                    "currency": "USD",
                    "billing_period": "month",
                    "review_limit": 200,
                    "features": [
                        "Up to 200 reviews per month",
                        "Custom email templates",
                        "Advanced widget customization",
                        "Priority email notifications",
                        "Advanced analytics & reporting",
                        "Custom survey questions",
                        "Review response management",
                        "Email support"
                    ],
                    "limitations": [
                        "No white-label options",
                        "Limited API access"
                    ]
                },
                "premium": {
                    "name": "Premium Plan",
                    "price": 99,
                    "currency": "USD",
                    "billing_period": "month",
                    "review_limit": -1,
                    "features": [
                        "Unlimited reviews",
                        "Full template customization",
                        "White-label widget",
                        "Real-time notifications",
                        "Advanced analytics & insights",
                        "Custom survey questions",
                        "Review response management",
                        "Full API access",
                        "Priority support",
                        "Custom integrations",
                        "Advanced reporting & exports",
                        "Multi-user accounts"
                    ],
                    "limitations": []
                }
            },
            response_only=True
        )
    },
    examples=[
        OpenApiExample(
            'Plan Comparison Response (with ?comparison=true)',
            value={
                "features": [
                    {
                        "name": "Monthly Reviews",
                        "basic": "50",
                        "standard": "200",
                        "premium": "Unlimited"
                    },
                    {
                        "name": "Email Templates",
                        "basic": "Basic",
                        "standard": "Custom",
                        "premium": "Full Customization"
                    },
                    {
                        "name": "Widget Customization",
                        "basic": "Standard",
                        "standard": "Advanced",
                        "premium": "White-label"
                    },
                    {
                        "name": "Analytics",
                        "basic": "Basic",
                        "standard": "Advanced",
                        "premium": "Advanced + Insights"
                    },
                    {
                        "name": "Survey Questions",
                        "basic": "❌",
                        "standard": "✅",
                        "premium": "✅"
                    },
                    {
                        "name": "API Access",
                        "basic": "❌",
                        "standard": "Limited",
                        "premium": "Full"
                    },
                    {
                        "name": "Support",
                        "basic": "Community",
                        "standard": "Email",
                        "premium": "Priority"
                    }
                ],
                "plans": {
                    "basic": {"name": "Basic Plan", "price": 0},
                    "standard": {"name": "Standard Plan", "price": 29},
                    "premium": {"name": "Premium Plan", "price": 99}
                }
            },
            response_only=True
        )
    ],
    tags=['Subscription Plans']
)
@api_view(['GET'])
@permission_classes([AllowAny])
def plans_view(request):
    """Get all available plans with features and pricing"""
    from reviews.plan_data import get_all_plans, get_plan_comparison
    
    if request.GET.get('comparison') == 'true':
        data = get_plan_comparison()
    else:
        data = get_all_plans()
    
    return Response(data)
