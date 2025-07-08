import uuid
from django.core.management.base import BaseCommand
from reviews.models import Company, Plan, Badge


class Command(BaseCommand):
    help = 'Calculate and assign badges to companies based on recommendation percentage'

    def handle(self, *args, **options):
        companies = Company.objects.all()
        
        for company in companies:
            # Create plan if not exists
            if not hasattr(company, 'plan'):
                Plan.objects.create(
                    company=company,
                    plan_type='basic',
                    review_limit=50
                )
            
            # Calculate recommendation percentage
            from reviews.models import Review
            reviews = Review.objects.filter(business__owner=company.owner, is_approved=True)
            
            if reviews.count() > 0:
                recommend_count = reviews.filter(rating__gte=4).count()
                percentage = (recommend_count / reviews.count()) * 100
                
                # Assign badge based on percentage
                badge_type = None
                if percentage >= 98:
                    badge_type = 'gold'
                elif percentage >= 95:
                    badge_type = 'silver'
                elif percentage >= 90:
                    badge_type = 'bronze'
                
                if badge_type:
                    badge, created = Badge.objects.get_or_create(
                        company=company,
                        defaults={'badge_type': badge_type, 'percentage': percentage}
                    )
                    if not created:
                        badge.badge_type = badge_type
                        badge.percentage = percentage
                        badge.save()
                    
                    self.stdout.write(
                        self.style.SUCCESS(f'Assigned {badge_type} badge to {company.name} ({percentage:.1f}%)')
                    )
        
        self.stdout.write(self.style.SUCCESS('Badge assignment completed'))
