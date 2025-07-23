from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
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


@method_decorator(ratelimit(key='ip', rate='5/m', method='POST'), name='post')
class UserRegistrationView(generics.CreateAPIView):
    """View for user registration"""
    
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Get the created company
        from reviews.models import Company
        company = Company.objects.filter(owner=user).first()
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        response_data = {
            'message': 'Registration successful! Your account and company have been created.',
            'user': UserProfileSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }
        
        # Include company information if created
        if company:
            from reviews.serializers import CompanySerializer
            response_data['company'] = CompanySerializer(company).data
            
            # Include plan information
            if hasattr(company, 'plan'):
                from reviews.serializers import PlanSerializer
                response_data['plan'] = PlanSerializer(company.plan).data
        
        return Response(response_data, status=status.HTTP_201_CREATED)


@method_decorator(ratelimit(key='ip', rate='10/m', method='POST'), name='post')
class UserLoginView(generics.GenericAPIView):
    """View for user login"""
    
    serializer_class = UserLoginSerializer
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
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


class UserProfileView(generics.RetrieveUpdateAPIView):
    """View for retrieving and updating user profile"""
    
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user


class PasswordChangeView(generics.GenericAPIView):
    """View for changing user password"""
    
    serializer_class = PasswordChangeSerializer
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response({
            'message': 'Password changed successfully'
        }, status=status.HTTP_200_OK)


class EmailVerificationView(generics.GenericAPIView):
    """View for email verification"""
    
    serializer_class = EmailVerificationSerializer
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.validated_data['user']
        user.is_verified = True
        user.save()
        
        return Response({
            'message': 'Email verified successfully'
        }, status=status.HTTP_200_OK)


@method_decorator(ratelimit(key='ip', rate='3/m', method='POST'), name='post')
class PasswordResetRequestView(generics.GenericAPIView):
    """View for password reset request"""
    
    serializer_class = PasswordResetRequestSerializer
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
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


class PasswordResetConfirmView(generics.GenericAPIView):
    """View for password reset confirmation"""
    
    serializer_class = PasswordResetConfirmSerializer
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
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


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_profile_view(request):
    """Simple view to get current user profile"""
    serializer = UserProfileSerializer(request.user)
    return Response(serializer.data)
