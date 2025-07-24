from django.urls import path
from .views import (
    # Business views
    business_view,
    business_dashboard_view,
    business_reviews_view,
    business_public_reviews_view,
    # Order views
    order_list_create_view,
    order_detail_view,
    order_send_review_request_view,
    # Review views
    review_list_create_view,
    review_detail_view,
    review_approve_view,
    review_reject_view,
    review_respond_view,
    # Review Criteria views
    review_criteria_list_create_view,
    review_criteria_detail_view,
    # Dashboard stats
    dashboard_stats_view,
)
from .views_payment import (
    payment_list_create_view,
    payment_detail_view,
    payment_pricing_view,
    payment_create_order_view,
    payment_capture_view,
    payment_user_plan_view,
)
from .views_widget import (
    widget_embed_view,
    widget_data_view,
    widget_script_view,
)

urlpatterns = [
    # Business endpoints (single business per user)
    path('business/', business_view, name='business'),
    path('business/dashboard/', business_dashboard_view, name='business-dashboard'),
    path('business/reviews/', business_reviews_view, name='business-reviews'),
    path('business/public-reviews/', business_public_reviews_view, name='business-public-reviews'),
    
    # Dashboard stats
    path('dashboard/stats/', dashboard_stats_view, name='dashboard-stats'),
    
    # Order management
    path('orders/', order_list_create_view, name='order-list-create'),
    path('orders/<int:pk>/', order_detail_view, name='order-detail'),
    path('orders/<int:pk>/send-review-request/', order_send_review_request_view, name='order-send-review-request'),
    
    # Review management
    path('reviews/', review_list_create_view, name='review-list-create'),
    path('reviews/<int:pk>/', review_detail_view, name='review-detail'),
    path('reviews/<int:pk>/approve/', review_approve_view, name='review-approve'),
    path('reviews/<int:pk>/reject/', review_reject_view, name='review-reject'),
    path('reviews/<int:pk>/respond/', review_respond_view, name='review-respond'),
    
    # Review criteria
    path('review-criteria/', review_criteria_list_create_view, name='review-criteria-list-create'),
    path('review-criteria/<int:pk>/', review_criteria_detail_view, name='review-criteria-detail'),
    
    # Payment endpoints
    path('payments/', payment_list_create_view, name='payment-list-create'),
    path('payments/<int:pk>/', payment_detail_view, name='payment-detail'),
    path('payments/pricing/', payment_pricing_view, name='payment-pricing'),
    path('payments/create-order/', payment_create_order_view, name='payment-create-order'),
    path('payments/capture/', payment_capture_view, name='payment-capture'),
    path('payments/user-plan/', payment_user_plan_view, name='payment-user-plan'),
    
    # Widget endpoints
    path('widget/<int:user_id>/', widget_embed_view, name='widget-embed'),
    path('widget/<int:user_id>/data/', widget_data_view, name='widget-data'),
    path('widget/<int:user_id>/script.js', widget_script_view, name='widget-script'),
]
