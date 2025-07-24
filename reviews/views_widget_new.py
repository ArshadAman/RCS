from django.http import HttpResponse
from django.template.loader import render_to_string
from django.db.models import Avg
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Business, Review, User


@api_view(['GET'])
def widget_embed_view(request, user_id):
    """Function-based view for widget embed"""
    try:
        user = get_object_or_404(User, id=user_id)
        business = get_object_or_404(Business, user=user)
        
        # Get reviews for this business
        reviews_qs = Review.objects.filter(order__business=business, status='published')
        reviews = [
            {
                "rating": r.overall_rating, 
                "text": r.comment, 
                "user": r.reviewer_name
            }
            for r in reviews_qs.order_by('-created_at')[:3]
        ]
        
        # Calculate average rating
        avg_rating = reviews_qs.aggregate(avg=Avg('overall_rating'))['avg']
        if avg_rating is None:
            avg_rating = 4.5
        avg_rating = round(avg_rating, 1)
        
        # Calculate recommend percentage (reviews with rating >= 4)
        total_reviews = reviews_qs.count()
        if total_reviews > 0:
            recommend_count = reviews_qs.filter(overall_rating__gte=4).count()
            recommend_percent = round((recommend_count / total_reviews) * 100)
        else:
            recommend_percent = 92  # Default value
        
        # Determine trust badge based on review count and average rating
        trust_badge = "Bronze"  # Default
        if total_reviews >= 50 and avg_rating >= 4.5:
            trust_badge = "Gold"
        elif total_reviews >= 20 and avg_rating >= 4.0:
            trust_badge = "Silver"
        
        context = {
            "business": business,
            "user": user,
            "avg_rating": avg_rating,
            "recommend_percent": recommend_percent,
            "trust_badge": trust_badge,
            "reviews": reviews,
            "total_reviews": total_reviews
        }
        
        html = render_to_string("widget_embed.html", context)
        return HttpResponse(html)
        
    except (User.DoesNotExist, Business.DoesNotExist):
        return HttpResponse(
            "<div>Widget not available - Business not found</div>", 
            status=404
        )


@api_view(['GET'])
def widget_data_view(request, user_id):
    """API endpoint to get widget data as JSON"""
    try:
        user = get_object_or_404(User, id=user_id)
        business = get_object_or_404(Business, user=user)
        
        # Get reviews for this business
        reviews_qs = Review.objects.filter(order__business=business, status='published')
        reviews = []
        
        for r in reviews_qs.order_by('-created_at')[:10]:  # Get more for API
            reviews.append({
                "id": r.id,
                "rating": r.overall_rating,
                "comment": r.comment,
                "reviewer_name": r.reviewer_name,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "service_rating": r.service_rating,
                "quality_rating": r.quality_rating,
                "value_rating": r.value_rating
            })
        
        # Calculate average rating
        avg_rating = reviews_qs.aggregate(avg=Avg('overall_rating'))['avg']
        if avg_rating is None:
            avg_rating = 4.5
        avg_rating = round(avg_rating, 1)
        
        # Calculate recommend percentage
        total_reviews = reviews_qs.count()
        if total_reviews > 0:
            recommend_count = reviews_qs.filter(overall_rating__gte=4).count()
            recommend_percent = round((recommend_count / total_reviews) * 100)
        else:
            recommend_percent = 92
        
        # Trust badge
        trust_badge = "Bronze"
        if total_reviews >= 50 and avg_rating >= 4.5:
            trust_badge = "Gold"
        elif total_reviews >= 20 and avg_rating >= 4.0:
            trust_badge = "Silver"
        
        # Rating distribution
        rating_distribution = {}
        for i in range(1, 6):
            count = reviews_qs.filter(overall_rating=i).count()
            rating_distribution[str(i)] = count
        
        return Response({
            "business": {
                "id": business.id,
                "name": business.name,
                "industry": business.industry,
                "website": business.website
            },
            "stats": {
                "avg_rating": avg_rating,
                "total_reviews": total_reviews,
                "recommend_percent": recommend_percent,
                "trust_badge": trust_badge,
                "rating_distribution": rating_distribution
            },
            "recent_reviews": reviews
        })
        
    except (User.DoesNotExist, Business.DoesNotExist):
        return Response(
            {"error": "Business not found"}, 
            status=404
        )


@api_view(['GET'])
def widget_script_view(request, user_id):
    """Generate JavaScript widget script"""
    try:
        user = get_object_or_404(User, id=user_id)
        business = get_object_or_404(Business, user=user)
        
        # Generate JavaScript that can be embedded on external sites
        api_url = request.build_absolute_uri(f"/api/widget/{user_id}/data/")
        script_content = f"""
(function() {{
    var widgetContainer = document.getElementById('rcs-widget-{user_id}');
    if (!widgetContainer) {{
        console.error('RCS Widget container not found');
        return;
    }}
    
    fetch('{api_url}')
        .then(response => response.json())
        .then(data => {{
            var html = `
                <div class="rcs-widget">
                    <div class="rcs-header">
                        <h3>${{data.business.name}}</h3>
                        <div class="rcs-rating">
                            <span class="stars">${{'★'.repeat(Math.round(data.stats.avg_rating))}}</span>
                            <span class="rating-value">${{data.stats.avg_rating}}/5</span>
                            <span class="review-count">(${{data.stats.total_reviews}} reviews)</span>
                        </div>
                        <div class="rcs-badge trust-${{data.stats.trust_badge.toLowerCase()}}">
                            ${{data.stats.trust_badge}} Trusted
                        </div>
                    </div>
                    <div class="rcs-reviews">
                        ${{data.recent_reviews.slice(0, 3).map(review => `
                            <div class="rcs-review">
                                <div class="review-rating">${{'★'.repeat(review.rating)}}</div>
                                <div class="review-text">${{review.comment}}</div>
                                <div class="review-author">- ${{review.reviewer_name}}</div>
                            </div>
                        `).join('')}}
                    </div>
                    <div class="rcs-footer">
                        <a href="#" onclick="window.open('/widget/{user_id}/', 'reviews', 'width=600,height=400')">
                            View All Reviews
                        </a>
                    </div>
                </div>
            `;
            widgetContainer.innerHTML = html;
        }})
        .catch(error => {{
            console.error('Error loading widget:', error);
            widgetContainer.innerHTML = '<div>Unable to load reviews</div>';
        }});
}})();
        """
        
        return HttpResponse(script_content, content_type='application/javascript')
        
    except (User.DoesNotExist, Business.DoesNotExist):
        return HttpResponse(
            "console.error('RCS Widget: Business not found');", 
            content_type='application/javascript',
            status=404
        )
