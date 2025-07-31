from django.urls import path
from .views import (
    # Core views
    business_view,
    business_dashboard_view,
    order_list_create_view,
    order_detail_view,
    order_send_review_request_view,
    review_list_create_view,
    review_detail_view,
    review_approve_view,
    review_reject_view,
    review_respond_view,
    review_criteria_list_create_view,
    review_criteria_detail_view,
    public_review_form,
    submit_public_review,
    widget_data,
    # Consolidated views
    payment_view,
    widget_view,
)

# Daily Sales Report views
from .daily_sales_views import (
    upload_sales_report,
    get_sales_reports,
    submit_feedback,
    get_feedback_requests,
    get_customer_reviews,
    respond_to_review,
    dashboard_stats,
)

urlpatterns = [
    # Business (single per user)
    path('business/', business_view, name='business'),
    path('business/dashboard/', business_dashboard_view, name='business-dashboard'),
    
    # Orders
    path('orders/', order_list_create_view, name='orders'),
    path('orders/<int:pk>/', order_detail_view, name='order-detail'),
    path('orders/<int:pk>/send-review-request/', order_send_review_request_view, name='send-review-request'),
    
    # Reviews
    path('reviews/', review_list_create_view, name='reviews'),
    path('reviews/<int:pk>/', review_detail_view, name='review-detail'),
    path('reviews/<int:pk>/approve/', review_approve_view, name='review-approve'),
    path('reviews/<int:pk>/reject/', review_reject_view, name='review-reject'),
    path('reviews/<int:pk>/respond/', review_respond_view, name='review-respond'),
    
    # Review Criteria
    path('review-criteria/', review_criteria_list_create_view, name='review-criteria'),
    path('review-criteria/<int:pk>/', review_criteria_detail_view, name='review-criteria-detail'),
    
    # Public
    path('review-form/<str:token>/', public_review_form, name='review-form'),
    path('submit-review/<str:token>/', submit_public_review, name='submit-review'),
    path('widget-data/<int:user_id>/', widget_data, name='widget-data'),
    
    # Daily Sales Reports & Review System
    path('sales-report/upload/', upload_sales_report, name='upload-sales-report'),
    path('sales-reports/', get_sales_reports, name='sales-reports'),
    path('feedback/<uuid:token>/', submit_feedback, name='submit-feedback'),
    path('review-requests/', get_feedback_requests, name='review-requests'),
    path('customer-reviews/', get_customer_reviews, name='customer-reviews'),
    path('review/<int:review_id>/respond/', respond_to_review, name='respond-review'),
    path('dashboard/stats/', dashboard_stats, name='dashboard-stats'),
    
    # Consolidated endpoints
    path('payment/', payment_view, name='payment'),  # Handles all payment actions via ?action= or POST action
    path('widget/<int:user_id>/', widget_view, name='widget'),  # Handles embed, data, script via ?action=
]
