from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.template.loader import render_to_string
from reviews.models import Order
from authentication.tasks import send_feedback_email


class Command(BaseCommand):
    help = 'Send feedback request emails for pending orders'

    def add_arguments(self, parser):
        parser.add_argument('--order-id', type=str, help='Send email for specific order')
        parser.add_argument('--company-id', type=str, help='Send emails for specific company')

    def handle(self, *args, **options):
        orders = Order.objects.all()
        
        if options['order_id']:
            orders = orders.filter(order_id=options['order_id'])
        elif options['company_id']:
            orders = orders.filter(company__unique_id=options['company_id'])
        
        count = 0
        for order in orders:
            # Generate unique feedback link
            feedback_url = f"https://domain.com/feedback?order_id={order.order_id}&customer_id={order.customer_email}"
            
            # Send email via Celery task
            send_feedback_email.delay(
                customer_email=order.customer_email,
                customer_name=order.customer_name,
                product_name=order.product_name,
                feedback_url=feedback_url,
                company_name=order.company.name
            )
            count += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'Sent {count} feedback request emails')
        )
