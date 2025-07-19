from django.http import HttpResponse
from django.template.loader import render_to_string
from django.views import View
from django.db.models import Avg
from .models import Company, Review

class WidgetEmbedView(View):
    def get(self, request, company_id):
        company = Company.objects.get(id=company_id)
        # Example: calculate average rating, recommend percent, trust badge, and recent reviews
        reviews_qs = Review.objects.filter(order__business__company=company, status='published')
        reviews = [
            {"rating": r.overall_rating, "text": r.comment, "user": r.reviewer_name}
            for r in reviews_qs.order_by('-created_at')[:3]
        ]
        avg_rating = reviews_qs.aggregate(avg=Avg('overall_rating'))['avg']
        if avg_rating is None:
            avg_rating = 4.5
        avg_rating = round(avg_rating, 1)
        recommend_percent = 92  # Replace with actual calculation
        trust_badge = "Gold"   # Replace with actual logic
        context = {
            "company": company,
            "avg_rating": avg_rating,
            "recommend_percent": recommend_percent,
            "trust_badge": trust_badge,
            "reviews": reviews
        }
        html = render_to_string("widget_embed.html", context)
        return HttpResponse(html)
