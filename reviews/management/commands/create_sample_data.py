from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from reviews.models import Category, Business, Review

User = get_user_model()


class Command(BaseCommand):
    help = 'Create sample data for the Review Collection System'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creating sample data...'))
        
        # Create superuser if it doesn't exist
        if not User.objects.filter(is_superuser=True).exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin123',
                first_name='Admin',
                last_name='User'
            )
            self.stdout.write(self.style.SUCCESS('Created superuser: admin@example.com (password: admin123)'))
        
        # Create sample users
        sample_users = [
            {
                'username': 'john_doe',
                'email': 'john@example.com',
                'password': 'user123',
                'first_name': 'John',
                'last_name': 'Doe'
            },
            {
                'username': 'jane_smith',
                'email': 'jane@example.com',
                'password': 'user123',
                'first_name': 'Jane',
                'last_name': 'Smith'
            },
            {
                'username': 'business_owner',
                'email': 'owner@example.com',
                'password': 'user123',
                'first_name': 'Business',
                'last_name': 'Owner'
            }
        ]
        
        created_users = []
        for user_data in sample_users:
            user, created = User.objects.get_or_create(
                email=user_data['email'],
                defaults=user_data
            )
            if created:
                user.set_password(user_data['password'])
                user.save()
                created_users.append(user)
        
        self.stdout.write(self.style.SUCCESS(f'Created {len(created_users)} sample users'))
        
        # Create categories
        categories = [
            {'name': 'Restaurant', 'description': 'Food and dining establishments', 'icon': 'restaurant'},
            {'name': 'Hotel', 'description': 'Accommodation and lodging', 'icon': 'hotel'},
            {'name': 'Retail', 'description': 'Shopping and retail stores', 'icon': 'shopping_cart'},
            {'name': 'Healthcare', 'description': 'Medical and healthcare services', 'icon': 'local_hospital'},
            {'name': 'Education', 'description': 'Educational institutions', 'icon': 'school'},
            {'name': 'Technology', 'description': 'Tech companies and services', 'icon': 'computer'},
        ]
        
        created_categories = []
        for cat_data in categories:
            category, created = Category.objects.get_or_create(
                name=cat_data['name'],
                defaults=cat_data
            )
            if created:
                created_categories.append(category)
        
        self.stdout.write(self.style.SUCCESS(f'Created {len(created_categories)} categories'))
        
        # Create sample businesses
        business_owner = User.objects.get(email='owner@example.com')
        admin_user = User.objects.filter(is_superuser=True).first()
        
        businesses = [
            {
                'name': 'The Great Restaurant',
                'description': 'A fantastic dining experience with great food and atmosphere.',
                'category': 'Restaurant',
                'address': '123 Main St, Downtown, City',
                'phone_number': '+1-555-0123',
                'email': 'info@greatrestaurant.com',
                'website': 'https://greatrestaurant.com',
                'owner': business_owner
            },
            {
                'name': 'Grand Hotel',
                'description': 'Luxury accommodation in the heart of the city.',
                'category': 'Hotel',
                'address': '456 Hotel Ave, City Center',
                'phone_number': '+1-555-0456',
                'email': 'reservations@grandhotel.com',
                'website': 'https://grandhotel.com',
                'owner': admin_user
            },
            {
                'name': 'Tech Solutions Inc',
                'description': 'Innovative technology solutions for modern businesses.',
                'category': 'Technology',
                'address': '789 Tech Park, Innovation District',
                'phone_number': '+1-555-0789',
                'email': 'contact@techsolutions.com',
                'website': 'https://techsolutions.com',
                'owner': business_owner
            }
        ]
        
        created_businesses = []
        for biz_data in businesses:
            business, created = Business.objects.get_or_create(
                name=biz_data['name'],
                defaults=biz_data
            )
            if created:
                created_businesses.append(business)
        
        self.stdout.write(self.style.SUCCESS(f'Created {len(created_businesses)} businesses'))
        
        # Create sample reviews
        john = User.objects.get(email='john@example.com')
        jane = User.objects.get(email='jane@example.com')
        
        reviews = [
            {
                'business': Business.objects.get(name='The Great Restaurant'),
                'reviewer': john,
                'rating': 5,
                'title': 'Amazing food and service!',
                'content': 'Had a wonderful dinner here. The food was exceptional and the staff was very friendly. Highly recommended!',
                'reviewer_name': 'John D.',
                'is_approved': True
            },
            {
                'business': Business.objects.get(name='The Great Restaurant'),
                'reviewer': jane,
                'rating': 4,
                'title': 'Great atmosphere',
                'content': 'The restaurant has a lovely atmosphere and the food was good. Service could be a bit faster but overall a nice experience.',
                'reviewer_name': 'Jane S.',
                'is_approved': True
            },
            {
                'business': Business.objects.get(name='Grand Hotel'),
                'reviewer': john,
                'rating': 5,
                'title': 'Perfect stay',
                'content': 'Everything was perfect! Clean rooms, great service, and excellent location. Will definitely stay here again.',
                'reviewer_name': 'John D.',
                'is_approved': True
            },
            {
                'business': Business.objects.get(name='Tech Solutions Inc'),
                'reviewer': jane,
                'rating': 4,
                'title': 'Good service',
                'content': 'They provided good technical support and solved our problems efficiently. Professional team.',
                'reviewer_name': 'Jane S.',
                'is_approved': True
            }
        ]
        
        created_reviews = []
        for review_data in reviews:
            review, created = Review.objects.get_or_create(
                business=review_data['business'],
                reviewer=review_data['reviewer'],
                defaults=review_data
            )
            if created:
                created_reviews.append(review)
        
        self.stdout.write(self.style.SUCCESS(f'Created {len(created_reviews)} reviews'))
        
        self.stdout.write(
            self.style.SUCCESS(
                '\nSample data created successfully!\n'
                'You can now:\n'
                '1. Login to admin panel with admin@example.com / admin123\n'
                '2. Test API endpoints with sample users\n'
                '3. View sample businesses and reviews\n'
            )
        )
