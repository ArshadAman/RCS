from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    UserRegistrationView,
    UserLoginView,
    UserProfileView,
    PasswordChangeView,
    EmailVerificationView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    logout_view,
    user_profile_view
)

app_name = 'authentication'

urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('logout/', logout_view, name='logout'),
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('profile/simple/', user_profile_view, name='profile_simple'),
    path('password/change/', PasswordChangeView.as_view(), name='password_change'),
    path('password/reset/', PasswordResetRequestView.as_view(), name='password_reset'),
    path('password/reset/confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('email/verify/', EmailVerificationView.as_view(), name='email_verify'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
