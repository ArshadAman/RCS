from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    # Company views
    company_list_create_view,
    company_detail_view,
    company_dashboard_stats_view,
    # Business views
    business_list_create_view,
    business_detail_view,
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
    # Email Template views
    email_template_list_create_view,
    email_template_detail_view,
    # Widget Settings views
    widget_settings_list_create_view,
    widget_settings_detail_view,
    # Category views
    category_list_view,
    # QR Feedback views
    qr_feedback_list_create_view,
    qr_feedback_detail_view,
    # Public views
    public_review_form,
    submit_public_review,
    widget_data,
    generate_qr_code,
    submit_qr_feedback,
    # Additional views
    export_reviews,
    bulk_approve_reviews,
    bulk_reject_reviews,
)
from .views_payment import (
    payment_list_create_view,
    payment_detail_view,
    payment_pricing_view,
    payment_setup_vault_view,
    payment_create_token_view,
    payment_create_order_view,
    payment_capture_view,
    payment_company_plan_view,
)
from .webhooks import paypal_webhook
from .views_widget import widget_embed_view

app_name = 'reviews'

urlpatterns = [
    # Company URLs
    path('companies/', company_list_create_view, name='company-list'),
    path('companies/<int:pk>/', company_detail_view, name='company-detail'),
    path('companies/<int:pk>/dashboard/', company_dashboard_stats_view, name='company-dashboard'),
    
    # Business URLs
    path('businesses/', business_list_create_view, name='business-list'),
    path('businesses/<int:pk>/', business_detail_view, name='business-detail'),
    path('businesses/<int:pk>/reviews/', business_reviews_view, name='business-reviews'),
    path('businesses/<int:pk>/public-reviews/', business_public_reviews_view, name='business-public-reviews'),
    
    # Order URLs
    path('orders/', order_list_create_view, name='order-list'),
    path('orders/<int:pk>/', order_detail_view, name='order-detail'),
    path('orders/<int:pk>/send-review-request/', order_send_review_request_view, name='order-send-review-request'),
    
    # Review URLs
    path('reviews/', review_list_create_view, name='review-list'),
    path('reviews/<int:pk>/', review_detail_view, name='review-detail'),
    path('reviews/<int:pk>/approve/', review_approve_view, name='review-approve'),
    path('reviews/<int:pk>/reject/', review_reject_view, name='review-reject'),
    path('reviews/<int:pk>/respond/', review_respond_view, name='review-respond'),
    
    # Review Criteria URLs
    path('review-criteria/', review_criteria_list_create_view, name='reviewcriteria-list'),
    path('review-criteria/<int:pk>/', review_criteria_detail_view, name='reviewcriteria-detail'),
    
    # Email Template URLs
    path('email-templates/', email_template_list_create_view, name='emailtemplate-list'),
    path('email-templates/<int:pk>/', email_template_detail_view, name='emailtemplate-detail'),
    
    # Widget Settings URLs
    path('widget-settings/', widget_settings_list_create_view, name='widgetsettings-list'),
    path('widget-settings/<int:pk>/', widget_settings_detail_view, name='widgetsettings-detail'),
    
    # Category URLs
    path('categories/', category_list_view, name='category-list'),
    
    # QR Feedback URLs
    path('qr-feedback/', qr_feedback_list_create_view, name='qrfeedback-list'),
    path('qr-feedback/<int:pk>/', qr_feedback_detail_view, name='qrfeedback-detail'),
    
    # Payment URLs
    path('payments/', payment_list_create_view, name='payment-list'),
    path('payments/<int:pk>/', payment_detail_view, name='payment-detail'),
    path('payments/pricing/', payment_pricing_view, name='payment-pricing'),
    path('payments/setup-vault/', payment_setup_vault_view, name='payment-setup-vault'),
    path('payments/create-token/', payment_create_token_view, name='payment-create-token'),
    path('payments/create-order/', payment_create_order_view, name='payment-create-order'),
    path('payments/capture/', payment_capture_view, name='payment-capture'),
    path('payments/company-plan/', payment_company_plan_view, name='payment-company-plan'),
    
    # Public APIs (no authentication required)
    path('public/review-form/<str:token>/', public_review_form, name='public_review_form'),
    path('public/submit-review/<str:token>/', submit_public_review, name='submit_public_review'),
    path('public/widget/<str:company_id>/', widget_data, name='widget_data'),
    path('public/qr-code/<str:company_id>/<str:branch_id>/', generate_qr_code, name='generate_qr_code'),
    path('public/qr-feedback/<str:company_id>/<str:branch_id>/', submit_qr_feedback, name='submit_qr_feedback'),
    
    # Additional endpoints
    path('export/<int:company_id>/', export_reviews, name='export_reviews'),
    path('bulk-approve/', bulk_approve_reviews, name='bulk_approve_reviews'),
    path('bulk-reject/', bulk_reject_reviews, name='bulk_reject_reviews'),
    
    # Webhook endpoints
    path('paypal/webhook/', paypal_webhook, name='paypal-webhook'),
    
    # Widget embed endpoint
    path('widget/<int:company_id>/embed/', widget_embed_view, name='widget-embed'),
]
