from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CompanyViewSet,
    BusinessViewSet,
    OrderViewSet,
    ReviewViewSet,
    ReviewCriteriaViewSet,
    EmailTemplateViewSet,
    WidgetSettingsViewSet,
    CategoryListView,
    QRFeedbackViewSet,
    public_review_form,
    submit_public_review,
    widget_data,
    generate_qr_code,
    submit_qr_feedback,
    export_reviews,
    bulk_approve_reviews,
    bulk_reject_reviews,
)

app_name = 'reviews'

# Create a router and register our ViewSets
router = DefaultRouter()
router.register(r'companies', CompanyViewSet, basename='company')
router.register(r'businesses', BusinessViewSet, basename='business')
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'reviews', ReviewViewSet, basename='review')
router.register(r'review-criteria', ReviewCriteriaViewSet, basename='reviewcriteria')
router.register(r'email-templates', EmailTemplateViewSet, basename='emailtemplate')
router.register(r'widget-settings', WidgetSettingsViewSet, basename='widgetsettings')
router.register(r'categories', CategoryListView, basename='category')
router.register(r'qr-feedback', QRFeedbackViewSet, basename='qrfeedback')

urlpatterns = [
    # Include the router URLs
    path('', include(router.urls)),
    
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
    
    # Legacy endpoints (for backward compatibility)
    path('businesses/<int:business_id>/public-reviews/', 
         BusinessViewSet.as_view({'get': 'public_reviews'}), 
         name='business_public_reviews'),
    path('companies/<int:pk>/dashboard/', 
         CompanyViewSet.as_view({'get': 'dashboard_stats'}), 
         name='company_dashboard'),
    path('orders/<int:pk>/send-review-request/', 
         OrderViewSet.as_view({'post': 'send_review_request'}), 
         name='send_review_request'),
]
