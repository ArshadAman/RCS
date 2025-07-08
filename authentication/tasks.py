from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.urls import reverse
from celery import shared_task
import logging

logger = logging.getLogger(__name__)


@shared_task
def send_verification_email(user_id):
    """Send email verification to user"""
    from authentication.models import User
    
    try:
        user = User.objects.get(id=user_id)
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        
        verification_link = f"{settings.FRONTEND_URL}/verify-email/{uid}/{token}/"
        
        subject = 'Verify your email address'
        message = f"""
        Hi {user.first_name or user.username},
        
        Thank you for registering with our Review Collection System!
        
        Please click the link below to verify your email address:
        {verification_link}
        
        If you didn't create this account, please ignore this email.
        
        Best regards,
        Review Collection System Team
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        
        logger.info(f"Verification email sent to {user.email}")
        
    except User.DoesNotExist:
        logger.error(f"User with id {user_id} not found")
    except Exception as e:
        logger.error(f"Failed to send verification email: {str(e)}")


@shared_task
def send_password_reset_email(user_id):
    """Send password reset email to user"""
    from authentication.models import User
    
    try:
        user = User.objects.get(id=user_id)
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        
        reset_link = f"{settings.FRONTEND_URL}/reset-password/{uid}/{token}/"
        
        subject = 'Reset your password'
        message = f"""
        Hi {user.first_name or user.username},
        
        You requested a password reset for your account.
        
        Please click the link below to reset your password:
        {reset_link}
        
        If you didn't request this, please ignore this email.
        
        Best regards,
        Review Collection System Team
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        
        logger.info(f"Password reset email sent to {user.email}")
        
    except User.DoesNotExist:
        logger.error(f"User with id {user_id} not found")
    except Exception as e:
        logger.error(f"Failed to send password reset email: {str(e)}")


@shared_task
def send_review_notification(review_id):
    """Send notification when new review is submitted"""
    from reviews.models import Review
    
    try:
        review = Review.objects.get(id=review_id)
        business_owner = review.business.owner
        
        subject = f'New review for {review.business.name}'
        message = f"""
        Hi {business_owner.first_name or business_owner.username},
        
        You have received a new review for {review.business.name}:
        
        Rating: {review.rating}/5 stars
        Title: {review.title}
        Reviewer: {review.reviewer_name}
        
        You can view and respond to this review in your admin panel.
        
        Best regards,
        Review Collection System Team
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[business_owner.email],
            fail_silently=False,
        )
        
        logger.info(f"Review notification sent to {business_owner.email}")
        
    except Review.DoesNotExist:
        logger.error(f"Review with id {review_id} not found")
    except Exception as e:
        logger.error(f"Failed to send review notification: {str(e)}")


@shared_task
def send_feedback_email(customer_email, customer_name, product_name, feedback_url, company_name):
    """Send personalized feedback request email"""
    try:
        subject = f'How was your experience with {product_name}?'
        message = f"""
        Hi {customer_name},
        
        Thank you for your recent purchase of {product_name} from {company_name}!
        
        We'd love to hear about your experience. Would you recommend us to others?
        
        Please share your feedback by clicking the link below:
        {feedback_url}
        
        Your feedback helps us improve and helps other customers make informed decisions.
        
        Thank you for your time!
        
        Best regards,
        {company_name} Team
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[customer_email],
            fail_silently=False,
        )
        
        logger.info(f'Feedback email sent to {customer_email}')
        return True
        
    except Exception as e:
        logger.error(f'Failed to send feedback email to {customer_email}: {str(e)}')
        return False
