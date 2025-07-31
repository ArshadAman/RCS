import os
import logging
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
from python_http_client.exceptions import HTTPError
import json

logger = logging.getLogger(__name__)


class SendGridEmailService:
    """SendGrid email service for sending review-related emails"""
    
    def __init__(self):
        self.api_key = getattr(settings, 'SENDGRID_API_KEY', os.environ.get('SENDGRID_API_KEY'))
        self.from_email = getattr(settings, 'SENDGRID_FROM_EMAIL', 'noreply@yourdomain.com')
        self.from_name = getattr(settings, 'SENDGRID_FROM_NAME', 'Review Collection System')
        
        if not self.api_key:
            raise ValueError("SendGrid API key not found. Please set SENDGRID_API_KEY in settings or environment.")
        
        self.sg = SendGridAPIClient(api_key=self.api_key)
    
    def send_email(self, to_email, subject, html_content, plain_content=None):
        """Send email using SendGrid"""
        try:
            from_email = Email(self.from_email, self.from_name)
            to_email = To(to_email)
            
            # If no plain content provided, strip HTML
            if not plain_content:
                plain_content = strip_tags(html_content)
            
            # Create mail object
            mail = Mail(
                from_email=from_email,
                to_emails=to_email,
                subject=subject,
                html_content=html_content,
                plain_text_content=plain_content
            )
            
            # Send email
            response = self.sg.send(mail)
            
            logger.info(f"Email sent successfully to {to_email}. Status: {response.status_code}")
            return True
            
        except HTTPError as e:
            logger.error(f"SendGrid HTTP error: {e.body}")
            return False
        except Exception as e:
            logger.error(f"Email sending failed: {str(e)}")
            return False


def send_review_notification_email(review, email_type, extra_context=None):
    """
    Send review-related notification emails
    
    Email types:
    - customer_thank_you: Thank customer for positive review
    - customer_review_published: Notify customer their review is published
    - business_negative_review: Notify business owner of negative review
    - business_auto_published: Notify business owner of auto-published review
    - business_reminder: Remind business owner about pending review
    - review_request: Send review request to customer
    """
    
    email_service = SendGridEmailService()
    
    # Base context for all emails
    context = {
        'review': review,
        'business': review.business,
        'site_name': getattr(settings, 'SITE_NAME', 'Review Collection System'),
        'site_url': getattr(settings, 'SITE_URL', 'https://yourdomain.com'),
    }
    
    # Add extra context if provided
    if extra_context:
        context.update(extra_context)
    
    # Email configurations
    email_configs = {
        'customer_thank_you': {
            'to_email': review.reviewer_email,
            'subject': f'Thank you for your review - {review.business.name}',
            'template': 'emails/customer_thank_you.html'
        },
        'customer_review_published': {
            'to_email': review.reviewer_email,
            'subject': f'Your review has been published - {review.business.name}',
            'template': 'emails/customer_review_published.html'
        },
        'business_negative_review': {
            'to_email': review.business.owner.email,
            'subject': f'New review requiring attention - {review.business.name}',
            'template': 'emails/business_negative_review.html'
        },
        'business_auto_published': {
            'to_email': review.business.owner.email,
            'subject': f'Review auto-published - {review.business.name}',
            'template': 'emails/business_auto_published.html'
        },
        'business_reminder': {
            'to_email': review.business.owner.email,
            'subject': f'Reminder: Review pending response - {review.business.name}',
            'template': 'emails/business_reminder.html'
        }
    }
    
    # Get email configuration
    if email_type not in email_configs:
        logger.error(f"Unknown email type: {email_type}")
        return False
    
    config = email_configs[email_type]
    
    try:
        # Render email template
        html_content = render_to_string(config['template'], context)
        
        # Send email
        success = email_service.send_email(
            to_email=config['to_email'],
            subject=config['subject'],
            html_content=html_content
        )
        
        if success:
            logger.info(f"Sent {email_type} email for review {review.id}")
        else:
            logger.error(f"Failed to send {email_type} email for review {review.id}")
        
        return success
        
    except Exception as e:
        logger.error(f"Error sending {email_type} email for review {review.id}: {str(e)}")
        return False


def send_review_request_email(review_request):
    """Send review request email to customer"""
    
    email_service = SendGridEmailService()
    
    # Create review link
    site_url = getattr(settings, 'SITE_URL', 'https://yourdomain.com')
    review_link = f"{site_url}/reviews/submit/{review_request.email_token}/"
    
    context = {
        'review_request': review_request,
        'business': review_request.business,
        'review_link': review_link,
        'customer_name': review_request.customer_name,
        'site_name': getattr(settings, 'SITE_NAME', 'Review Collection System'),
        'site_url': site_url,
    }
    
    try:
        # Render email template
        html_content = render_to_string('emails/review_request.html', context)
        
        # Send email
        success = email_service.send_email(
            to_email=review_request.customer_email,
            subject=f'Please share your experience with {review_request.business.name}',
            html_content=html_content
        )
        
        if success:
            # Update review request
            review_request.email_sent_at = timezone.now()
            review_request.save()
            logger.info(f"Sent review request email to {review_request.customer_email}")
        else:
            logger.error(f"Failed to send review request email to {review_request.customer_email}")
        
        return success
        
    except Exception as e:
        logger.error(f"Error sending review request email: {str(e)}")
        return False


def send_bulk_review_requests(review_requests):
    """Send multiple review request emails efficiently"""
    
    success_count = 0
    failed_count = 0
    
    for review_request in review_requests:
        try:
            if send_review_request_email(review_request):
                success_count += 1
            else:
                failed_count += 1
        except Exception as e:
            logger.error(f"Error sending bulk review request to {review_request.customer_email}: {str(e)}")
            failed_count += 1
    
    logger.info(f"Bulk email sending completed. Success: {success_count}, Failed: {failed_count}")
    
    return {
        'success_count': success_count,
        'failed_count': failed_count,
        'total_count': success_count + failed_count
    }