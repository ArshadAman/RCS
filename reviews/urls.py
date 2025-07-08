from django.urls import path
from .views import (
    CategoryListView,
    BusinessListCreateView,
    BusinessDetailView,
    BusinessReviewsView,
    ReviewListCreateView,
    ReviewDetailView,
    ReviewResponseView,
    toggle_review_like,
    approve_review,
    business_stats,
    OrderIntakeWebhook,
    SurveyQuestionListCreateView,
    SurveyQuestionDetailView,
    ReviewAnswerListCreateView,
    ReviewAnswerDetailView,
    company_widget_data,
    qr_feedback_submit,
    generate_qr_code,
    CompanyListView,
)

app_name = 'reviews'

urlpatterns = [
    # Categories
    path('categories/', CategoryListView.as_view(), name='category_list'),
    
    # Businesses
    path('businesses/', BusinessListCreateView.as_view(), name='business_list_create'),
    path('businesses/<int:pk>/', BusinessDetailView.as_view(), name='business_detail'),
    path('businesses/<int:business_id>/reviews/', BusinessReviewsView.as_view(), name='business_reviews'),
    path('businesses/<int:business_id>/stats/', business_stats, name='business_stats'),
    
    # Reviews
    path('reviews/', ReviewListCreateView.as_view(), name='review_list_create'),
    path('reviews/<int:pk>/', ReviewDetailView.as_view(), name='review_detail'),
    path('reviews/<int:pk>/response/', ReviewResponseView.as_view(), name='review_response'),
    path('reviews/<int:review_id>/like/', toggle_review_like, name='toggle_review_like'),
    path('reviews/<int:review_id>/approve/', approve_review, name='approve_review'),
    
    # Order Intake Webhook
    path('orders/webhook/', OrderIntakeWebhook.as_view(), name='order_intake_webhook'),
    
    # Survey Questions
    path('survey-questions/', SurveyQuestionListCreateView.as_view(), name='surveyquestion_list_create'),
    path('survey-questions/<int:pk>/', SurveyQuestionDetailView.as_view(), name='surveyquestion_detail'),
    
    # Review Answers
    path('review-answers/', ReviewAnswerListCreateView.as_view(), name='reviewanswer_list_create'),
    path('review-answers/<int:pk>/', ReviewAnswerDetailView.as_view(), name='reviewanswer_detail'),
    
    # Widget API
    path('widget/<str:company_id>/', company_widget_data, name='company_widget_data'),
    
    # QR Feedback
    path('qr-feedback/<str:branch_id>/', qr_feedback_submit, name='qr_feedback_submit'),
    path('qr-code/<str:company_id>/<str:branch_id>/', generate_qr_code, name='generate_qr_code'),
    
    # Companies
    path('companies/', CompanyListView.as_view(), name='company_list'),
]
