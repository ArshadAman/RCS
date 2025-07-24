from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    user_registration_view,
    user_login_view,
    user_profile_update_view,
    password_change_view,
    email_verification_view,
    password_reset_request_view,
    password_reset_confirm_view,
    logout_view,
    user_profile_view
)

app_name = 'authentication'

urlpatterns = [
    path('register/', user_registration_view, name='register'),
    path('login/', user_login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('profile/', user_profile_update_view, name='profile'),
    path('profile/simple/', user_profile_view, name='profile_simple'),
    path('password/change/', password_change_view, name='password_change'),
    path('password/reset/', password_reset_request_view, name='password_reset'),
    path('password/reset/confirm/', password_reset_confirm_view, name='password_reset_confirm'),
    path('email/verify/', email_verification_view, name='email_verify'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
