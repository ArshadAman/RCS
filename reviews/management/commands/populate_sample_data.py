from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
import random
import uuid

from reviews.models import (
    Company, Business, Order, Review, ReviewCriteria, 
    EmailTemplate, WidgetSettings, Category, QRFeedback
)

User = get_user_model()


class Command(BaseCommand):
    help = 'Create sample data for the review collection system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--users',
            type=int,
            default=5,
            help='Number of users to create',
        )
        parser.add_argument(
            '--companies',
            type=int,
            default=3,
            help='Number of companies to create',
        )
        parser.add_argument(
            '--businesses',
            type=int,
            default=8,
            help='Number of businesses to create',
        )
        parser.add_argument(
            '--orders',
            type=int,
            default=50,
            help='Number of orders to create',
        )
        parser.add_argument(
            '--reviews',
            type=int,
            default=100,
            help='Number of reviews to create',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting sample data creation...'))
        
        # Create sample users
        users = self.create_users(options['users'])
        self.stdout.write(self.style.SUCCESS(f'Created {len(users)} users'))
        
        # Create categories
        categories = self.create_categories()
        self.stdout.write(self.style.SUCCESS(f'Created {len(categories)} categories'))
        
        # Create companies
        companies = self.create_companies(users, options['companies'])
        self.stdout.write(self.style.SUCCESS(f'Created {len(companies)} companies'))
        
        # Create review criteria
        self.create_review_criteria(companies)
        self.stdout.write(self.style.SUCCESS('Created review criteria'))
        
        # Create email templates
        self.create_email_templates(companies)
        self.stdout.write(self.style.SUCCESS('Created email templates'))
        
        # Create widget settings
        self.create_widget_settings(companies)
        self.stdout.write(self.style.SUCCESS('Created widget settings'))
        
        # Create businesses
        businesses = self.create_businesses(companies, categories, options['businesses'])
        self.stdout.write(self.style.SUCCESS(f'Created {len(businesses)} businesses'))
        
        # Create orders
        orders = self.create_orders(businesses, options['orders'])
        self.stdout.write(self.style.SUCCESS(f'Created {len(orders)} orders'))
        
        # Create reviews
        reviews = self.create_reviews(orders, options['reviews'])
        self.stdout.write(self.style.SUCCESS(f'Created {len(reviews)} reviews'))
        
        # Create QR feedback
        qr_feedback = self.create_qr_feedback(companies, 20)
        self.stdout.write(self.style.SUCCESS(f'Created {len(qr_feedback)} QR feedback entries'))
        
        self.stdout.write(self.style.SUCCESS('Sample data creation completed!'))

    def create_users(self, count):
        users = []
        for i in range(count):
            username = f'user_{i+1}'
            email = f'user{i+1}@example.com'
            
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'first_name': f'User {i+1}',
                    'last_name': 'Test',
                    'is_active': True,
                }
            )
            if created:
                user.set_password('testpass123')
                user.save()
            users.append(user)
        return users

    def create_categories(self):
        categories = [
            'Restaurant',
            'Hotel',
            'Retail',
            'Healthcare',
            'Automotive',
            'Beauty & Spa',
            'Technology',
            'Education',
            'Real Estate',
            'Financial Services',
        ]
        
        created_categories = []
        for category_name in categories:
            category, created = Category.objects.get_or_create(
                name=category_name,
                defaults={
                    'description': f'Businesses in the {category_name} category',
                    'is_active': True,
                }
            )
            created_categories.append(category)
        
        return created_categories

    def create_companies(self, users, count):
        companies = []
        company_names = [
            'TechCorp Solutions',
            'Green Valley Restaurants',
            'Urban Retail Group',
            'Healthcare Plus',
            'AutoMotive Excellence',
            'Beauty & Wellness Co',
            'EduTech Academy',
            'Prime Real Estate',
            'Financial Advisors Inc',
            'Service Excellence Ltd',
        ]
        
        for i in range(count):
            name = company_names[i % len(company_names)]
            owner = users[i % len(users)]
            
            company, created = Company.objects.get_or_create(
                name=f'{name} {i+1}',
                defaults={
                    'owner': owner,
                    'unique_id': str(uuid.uuid4())[:8],
                    'email': f'contact@{name.lower().replace(" ", "")}{i+1}.com',
                    'website': f'https://www.{name.lower().replace(" ", "")}{i+1}.com',
                    'phone_number': f'+1-555-{random.randint(100, 999)}-{random.randint(1000, 9999)}',
                    'is_active': True,
                }
            )
            companies.append(company)
        
        return companies

    def create_review_criteria(self, companies):
        criteria_sets = [
            ['Service Quality', 'Food Quality', 'Atmosphere', 'Value for Money'],
            ['Staff Friendliness', 'Product Quality', 'Store Cleanliness', 'Price'],
            ['Professionalism', 'Timeliness', 'Communication', 'Results'],
            ['Ease of Use', 'Features', 'Support', 'Performance'],
        ]
        
        for company in companies:
            criteria_set = random.choice(criteria_sets)
            for i, criterion in enumerate(criteria_set):
                ReviewCriteria.objects.get_or_create(
                    company=company,
                    name=criterion,
                    defaults={
                        'is_active': True,
                        'order': i + 1,
                    }
                )

    def create_email_templates(self, companies):
        templates = [
            {
                'name': 'Review Request',
                'subject': 'How was your experience with {business_name}?',
                'body_html': '''
                <html>
                <body>
                    <h2>How was your experience?</h2>
                    <p>Hi {customer_name},</p>
                    <p>We hope you enjoyed your recent experience with {business_name}. We would love to hear your feedback!</p>
                    <p><a href="{review_link}" style="background-color: #4F46E5; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Leave a Review</a></p>
                    <p>Thank you for your time!</p>
                    <p>Best regards,<br>The {business_name} Team</p>
                </body>
                </html>
                ''',
                'body_text': 'Hi {customer_name},\n\nWe hope you enjoyed your recent experience with {business_name}. We would love to hear your feedback!\n\nPlease take a moment to leave a review by clicking the link below:\n{review_link}\n\nThank you for your time!\n\nBest regards,\nThe {business_name} Team',
            },
            {
                'name': 'Review Reminder',
                'subject': 'Reminder: Share your experience with {business_name}',
                'body_html': '''
                <html>
                <body>
                    <h2>We'd love to hear from you!</h2>
                    <p>Hi {customer_name},</p>
                    <p>We sent you a review request a few days ago and wanted to follow up. Your feedback is very important to us!</p>
                    <p><a href="{review_link}" style="background-color: #4F46E5; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Leave a Review</a></p>
                    <p>Thank you!</p>
                    <p>Best regards,<br>The {business_name} Team</p>
                </body>
                </html>
                ''',
                'body_text': 'Hi {customer_name},\n\nWe sent you a review request a few days ago and wanted to follow up. Your feedback is very important to us!\n\nPlease click the link below to leave your review:\n{review_link}\n\nThank you!\n\nBest regards,\nThe {business_name} Team',
            },
            {
                'name': 'Thank You',
                'subject': 'Thank you for your review!',
                'body_html': '''
                <html>
                <body>
                    <h2>Thank you for your feedback!</h2>
                    <p>Hi {customer_name},</p>
                    <p>Thank you for taking the time to leave a review for {business_name}. Your feedback helps us improve our service!</p>
                    <p>Best regards,<br>The {business_name} Team</p>
                </body>
                </html>
                ''',
                'body_text': 'Hi {customer_name},\n\nThank you for taking the time to leave a review for {business_name}. Your feedback helps us improve our service!\n\nBest regards,\nThe {business_name} Team',
            },
        ]
        
        for company in companies:
            for template_data in templates:
                EmailTemplate.objects.get_or_create(
                    company=company,
                    name=template_data['name'],
                    defaults={
                        'subject': template_data['subject'],
                        'body_html': template_data['body_html'],
                        'body_text': template_data['body_text'],
                    }
                )

    def create_widget_settings(self, companies):
        for company in companies:
            WidgetSettings.objects.get_or_create(
                company=company,
                defaults={
                    'is_enabled': True,
                    'position': random.choice(['right', 'left']),
                    'theme_color': random.choice(['#007bff', '#28a745', '#dc3545', '#ffc107', '#6f42c1']),
                    'show_company_logo': True,
                    'show_review_count': True,
                    'show_criteria_breakdown': random.choice([True, False]),
                }
            )

    def create_businesses(self, companies, categories, count):
        businesses = []
        business_names = [
            'Downtown Bistro',
            'The Corner Cafe',
            'Elite Salon & Spa',
            'TechRepair Pro',
            'Green Valley Hotel',
            'Urban Fitness Center',
            'Family Medical Clinic',
            'Auto Service Plus',
            'The Book Nook',
            'Creative Design Studio',
            'Fresh Market',
            'Cozy Coffee House',
            'Professional Dental Care',
            'Fashion Boutique',
            'Home Improvement Store',
        ]
        
        for i in range(count):
            name = business_names[i % len(business_names)]
            company = companies[i % len(companies)]
            category = categories[i % len(categories)]
            
            business, created = Business.objects.get_or_create(
                name=f'{name} {i+1}',
                company=company,
                defaults={
                    'owner': company.owner,
                    'category': category.name,
                    'description': f'A premier {category.name.lower()} business offering excellent service and quality.',
                    'address': f'{random.randint(100, 9999)} {random.choice(["Main", "Oak", "Elm", "Pine", "Cedar"])} Street, City, State {random.randint(10000, 99999)}',
                    'phone_number': f'+1-555-{random.randint(100, 999)}-{random.randint(1000, 9999)}',
                    'email': f'info@{name.lower().replace(" ", "")}{i+1}.com',
                    'website': f'https://www.{name.lower().replace(" ", "")}{i+1}.com',
                    'is_active': True,
                }
            )
            businesses.append(business)
        
        return businesses

    def create_orders(self, businesses, count):
        orders = []
        first_names = ['John', 'Jane', 'Mike', 'Sarah', 'David', 'Emma', 'Chris', 'Lisa', 'Tom', 'Amy']
        last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez']
        
        for i in range(count):
            business = random.choice(businesses)
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            
            order = Order.objects.create(
                company=business.company,
                business=business,
                order_number=f'ORD-{random.randint(100000, 999999)}',
                customer_name=f'{first_name} {last_name}',
                customer_email=f'{first_name.lower()}.{last_name.lower()}@example.com',
                product_service_name=f'{business.category} Service',
                purchase_date=timezone.now() - timedelta(days=random.randint(1, 30)),
                status=random.choice(['pending', 'review_sent', 'completed', 'expired']),
            )
            orders.append(order)
        
        return orders

    def create_reviews(self, orders, count):
        reviews = []
        comments = [
            'Great experience! Highly recommend.',
            'Service was excellent and staff was very friendly.',
            'Good value for money and quality service.',
            'Could be better. Service was slow.',
            'Outstanding! Will definitely come back.',
            'Average experience. Nothing special.',
            'Terrible service. Would not recommend.',
            'Exceeded my expectations in every way.',
            'Decent service but room for improvement.',
            'Professional and efficient service.',
            'Very satisfied with the quality.',
            'Not worth the price paid.',
            'Excellent attention to detail.',
            'Staff was helpful and knowledgeable.',
            'Clean and well-maintained facility.',
        ]
        
        for i in range(min(count, len(orders))):
            order = orders[i]
            rating = random.randint(1, 5)
            
            # Create review
            review = Review.objects.create(
                order=order,
                business=order.business,
                company=order.business.company,
                reviewer_name=order.customer_name,
                reviewer_email=order.customer_email,
                overall_rating=rating,
                would_recommend=rating >= 4,
                comment=random.choice(comments) if rating != 3 else random.choice(comments[:5]),
                status=random.choice(['pending', 'published', 'rejected']),
            )
            
            # Create criteria ratings
            criteria = ReviewCriteria.objects.filter(company=order.business.company, is_active=True)
            for criterion in criteria:
                from reviews.models import ReviewCriteriaRating
                ReviewCriteriaRating.objects.create(
                    review=review,
                    criteria=criterion,
                    rating=random.randint(max(1, rating-1), min(5, rating+1)),
                )
            
            reviews.append(review)
        
        return reviews

    def create_qr_feedback(self, companies, count):
        feedback_entries = []
        comments = [
            'Great service today!',
            'Staff was very helpful.',
            'Clean and organized.',
            'Could be faster.',
            'Excellent experience.',
            'Good quality.',
            'Needs improvement.',
            'Very professional.',
            'Satisfied with service.',
            'Would recommend.',
        ]
        
        for i in range(count):
            company = random.choice(companies)
            
            feedback = QRFeedback.objects.create(
                company=company,
                branch_id=f'BRANCH-{random.randint(100, 999)}',
                rating=random.randint(1, 5),
                comment=random.choice(comments),
                ip_address=f'192.168.1.{random.randint(1, 255)}',
            )
            feedback_entries.append(feedback)
        
        return feedback_entries
