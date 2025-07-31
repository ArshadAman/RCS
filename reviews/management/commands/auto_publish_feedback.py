from django.core.management.base import BaseCommand
from django.utils import timezone
from reviews.models import CustomerFeedback


class Command(BaseCommand):
    help = 'Auto-publish negative feedback after 7 days if no store response'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be auto-published without actually doing it',
        )

    def handle(self, *args, **options):
        now = timezone.now()
        
        # Find negative feedback that should be auto-published
        feedback_to_publish = CustomerFeedback.objects.filter(
            would_recommend=False,
            status='pending_moderation',
            auto_publish_date__lte=now,
            store_response__exact=''  # No response from store
        )
        
        count = feedback_to_publish.count()
        
        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING(f'DRY RUN: Would auto-publish {count} negative feedback entries')
            )
            for feedback in feedback_to_publish:
                order_id = feedback.feedback_request.order_id
                business_name = feedback.business.name
                customer_name = feedback.feedback_request.customer_name
                days_elapsed = (now - feedback.created_at).days
                
                self.stdout.write(
                    f'  - {business_name}: Order {order_id} by {customer_name} '
                    f'({days_elapsed} days old, auto-publish date: {feedback.auto_publish_date})'
                )
        else:
            # Actually auto-publish the feedback
            updated = feedback_to_publish.update(
                status='auto_published',
                is_auto_published=True
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully auto-published {updated} negative feedback entries')
            )
            
            # Log details for each published feedback
            for feedback in CustomerFeedback.objects.filter(
                would_recommend=False,
                status='auto_published',
                is_auto_published=True,
                auto_publish_date__lte=now
            ):
                order_id = feedback.feedback_request.order_id
                business_name = feedback.business.name
                customer_name = feedback.feedback_request.customer_name
                
                self.stdout.write(
                    f'  ✓ Published: {business_name} - Order {order_id} by {customer_name}'
                )
        
        if count == 0:
            self.stdout.write(
                self.style.SUCCESS('No negative feedback ready for auto-publishing')
            )
