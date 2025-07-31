from celery import shared_task
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from .models import Review
from .email_utils import send_review_notification_email
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 60})
def schedule_auto_publish_review(self, review_id):
    """
    Task to automatically publish a negative review after 7 days
    if the business owner hasn't responded.
    """
    try:
        review = Review.objects.get(id=review_id)
        
        # Check if review is still pending moderation
        if review.status != 'pending_moderation':
            logger.info(f"Review {review_id} status is {review.status}, not auto-publishing")
            return f"Review {review_id} status is {review.status}, not auto-publishing"
        
        # Check if auto-publish date has arrived
        if review.auto_publish_date and timezone.now() >= review.auto_publish_date:
            # Auto-publish the review
            review.status = 'published'
            review.auto_published = True
            review.auto_published_at = timezone.now()
            review.save()
            
            logger.info(f"Auto-published review {review_id}")
            
            # Send notification to business owner about auto-publication
            send_review_notification_email(
                review, 
                email_type='business_auto_published'
            )
            
            # Send notification to customer that their review is now published
            send_review_notification_email(
                review, 
                email_type='customer_review_published'
            )
            
            return f"Successfully auto-published review {review_id}"
        else:
            logger.info(f"Review {review_id} auto-publish date not yet reached")
            return f"Review {review_id} auto-publish date not yet reached"
            
    except Review.DoesNotExist:
        logger.error(f"Review {review_id} not found")
        return f"Review {review_id} not found"
    
    except Exception as e:
        logger.error(f"Error auto-publishing review {review_id}: {str(e)}")
        raise


@shared_task
def check_pending_reviews_for_auto_publish():
    """
    Periodic task to check for reviews that need to be auto-published.
    This task should run daily to catch any reviews that might have been missed.
    """
    try:
        now = timezone.now()
        
        # Find reviews that should be auto-published
        reviews_to_publish = Review.objects.filter(
            status='pending_moderation',
            auto_publish_date__lte=now,
            auto_published=False
        )
        
        published_count = 0
        for review in reviews_to_publish:
            try:
                # Auto-publish the review
                review.status = 'published'
                review.auto_published = True
                review.auto_published_at = now
                review.save()
                
                # Send notifications
                send_review_notification_email(
                    review, 
                    email_type='business_auto_published'
                )
                
                send_review_notification_email(
                    review, 
                    email_type='customer_review_published'
                )
                
                published_count += 1
                logger.info(f"Auto-published review {review.id}")
                
            except Exception as e:
                logger.error(f"Error auto-publishing review {review.id}: {str(e)}")
        
        logger.info(f"Auto-published {published_count} reviews")
        return f"Auto-published {published_count} reviews"
        
    except Exception as e:
        logger.error(f"Error in check_pending_reviews_for_auto_publish: {str(e)}")
        raise


@shared_task
def send_reminder_to_business_owner(review_id, days_remaining):
    """
    Send reminder to business owner about pending negative review
    """
    try:
        review = Review.objects.get(id=review_id)
        
        if review.status != 'pending_moderation':
            return f"Review {review_id} is no longer pending moderation"
        
        # Send reminder email
        send_review_notification_email(
            review, 
            email_type='business_reminder',
            extra_context={'days_remaining': days_remaining}
        )
        
        logger.info(f"Sent reminder for review {review_id}, {days_remaining} days remaining")
        return f"Sent reminder for review {review_id}"
        
    except Review.DoesNotExist:
        logger.error(f"Review {review_id} not found")
        return f"Review {review_id} not found"
    
    except Exception as e:
        logger.error(f"Error sending reminder for review {review_id}: {str(e)}")
        raise


@shared_task
def schedule_review_reminders(review_id):
    """
    Schedule reminder emails for business owners about pending negative reviews
    - Send reminder at day 3 (4 days remaining)
    - Send reminder at day 5 (2 days remaining)
    - Send final reminder at day 6 (1 day remaining)
    """
    from datetime import timedelta
    from django_celery_beat.models import PeriodicTask, CrontabSchedule
    import json
    
    try:
        review = Review.objects.get(id=review_id)
        
        if review.status != 'pending_moderation' or not review.auto_publish_date:
            return f"Review {review_id} not eligible for reminders"
        
        # Calculate reminder dates
        created_date = review.created_at
        reminder_dates = [
            (created_date + timedelta(days=3), 4),  # Day 3, 4 days remaining
            (created_date + timedelta(days=5), 2),  # Day 5, 2 days remaining
            (created_date + timedelta(days=6), 1),  # Day 6, 1 day remaining
        ]
        
        for reminder_date, days_remaining in reminder_dates:
            if reminder_date > timezone.now():  # Only schedule future reminders
                send_reminder_to_business_owner.apply_async(
                    args=[review_id, days_remaining],
                    eta=reminder_date
                )
        
        logger.info(f"Scheduled reminders for review {review_id}")
        return f"Scheduled reminders for review {review_id}"
        
    except Review.DoesNotExist:
        logger.error(f"Review {review_id} not found")
        return f"Review {review_id} not found"
    
    except Exception as e:
        logger.error(f"Error scheduling reminders for review {review_id}: {str(e)}")
        raise


@shared_task
def cleanup_expired_review_requests():
    """
    Cleanup expired review requests (older than 30 days)
    """
    from .models import ReviewRequest
    from datetime import timedelta
    
    try:
        thirty_days_ago = timezone.now() - timedelta(days=30)
        
        expired_requests = ReviewRequest.objects.filter(
            status='pending',
            created_at__lt=thirty_days_ago
        )
        
        count = expired_requests.count()
        expired_requests.update(status='expired')
        
        logger.info(f"Marked {count} review requests as expired")
        return f"Marked {count} review requests as expired"
        
    except Exception as e:
        logger.error(f"Error cleaning up expired review requests: {str(e)}")
        raise
