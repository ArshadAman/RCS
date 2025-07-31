from django.contrib import admin
from .models import (
    Business, Review, ReviewImage, ReviewLike, Order, SurveyQuestion, 
    Plan, Badge, QRFeedback, ReviewAnswer, Payment, ReviewCriteria,
    DailySalesReport, FeedbackRequest, CustomerFeedback
)


@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'owner', 'average_rating', 'total_reviews', 'is_active', 'created_at')
    list_filter = ('category', 'is_active', 'created_at')
    search_fields = ('name', 'description', 'category', 'owner__email', 'owner__username')
    readonly_fields = ('average_rating', 'total_reviews', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'category', 'logo')
        }),
        ('Contact Information', {
            'fields': ('address', 'phone_number', 'email', 'website')
        }),
        ('Management', {
            'fields': ('owner', 'is_active')
        }),
        ('Statistics', {
            'fields': ('average_rating', 'total_reviews'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


class ReviewImageInline(admin.TabularInline):
    model = ReviewImage
    extra = 0
    readonly_fields = ('uploaded_at',)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('reviewer_name', 'business', 'overall_rating', 'status', 'created_at')
    list_filter = ('overall_rating', 'status', 'would_recommend', 'created_at')
    search_fields = ('comment', 'business__name', 'reviewer_name', 'reviewer_email')
    readonly_fields = ('created_at', 'updated_at', 'response_date')
    ordering = ('-created_at',)
    inlines = [ReviewImageInline]
    
    fieldsets = (
        ('Review Information', {
            'fields': ('business', 'order', 'overall_rating', 'would_recommend', 'comment')
        }),
        ('Customer Information', {
            'fields': ('reviewer_name', 'reviewer_email')
        }),
        ('Management', {
            'fields': ('status',)
        }),
        ('Business Response', {
            'fields': ('business_response', 'response_date'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_reviews', 'reject_reviews', 'publish_reviews']
    
    def approve_reviews(self, request, queryset):
        updated = queryset.update(status='published')
        self.message_user(request, f'{updated} reviews approved successfully.')
    approve_reviews.short_description = "Approve selected reviews"
    
    def reject_reviews(self, request, queryset):
        updated = queryset.update(status='rejected')
        self.message_user(request, f'{updated} reviews rejected successfully.')
    reject_reviews.short_description = "Reject selected reviews"
    
    def publish_reviews(self, request, queryset):
        updated = queryset.update(status='published')
        self.message_user(request, f'{updated} reviews published successfully.')
    publish_reviews.short_description = "Publish selected reviews"


@admin.register(ReviewImage)
class ReviewImageAdmin(admin.ModelAdmin):
    list_display = ('review', 'caption', 'uploaded_at')
    list_filter = ('uploaded_at',)
    search_fields = ('review__reviewer_name', 'caption')
    ordering = ('-uploaded_at',)


@admin.register(ReviewLike)
class ReviewLikeAdmin(admin.ModelAdmin):
    list_display = ('review', 'user', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('review__reviewer_name', 'user__email')
    ordering = ('-created_at',)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'business', 'customer_email', 'product_service_name', 'purchase_date', 'status', 'created_at')
    search_fields = ('order_number', 'customer_email', 'product_service_name', 'customer_name')
    list_filter = ('business__owner', 'status', 'purchase_date', 'created_at')
    ordering = ('-created_at',)


@admin.register(SurveyQuestion)
class SurveyQuestionAdmin(admin.ModelAdmin):
    list_display = ('question_text', 'user', 'question_type', 'is_active', 'is_required', 'order', 'created_at')
    search_fields = ('question_text',)
    list_filter = ('user', 'question_type', 'is_active', 'is_required')
    ordering = ('user', 'order')


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan_type', 'review_limit', 'created_at')
    list_filter = ('plan_type',)
    search_fields = ('user__username', 'user__email')
    ordering = ('-created_at',)


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ('user', 'badge_type', 'percentage', 'assigned_at')
    list_filter = ('badge_type',)
    search_fields = ('user__username', 'user__email')
    ordering = ('-assigned_at',)


@admin.register(QRFeedback)
class QRFeedbackAdmin(admin.ModelAdmin):
    list_display = ('user', 'branch_id', 'rating', 'ip_address', 'submitted_at')
    search_fields = ('branch_id', 'user__username', 'comment')
    list_filter = ('user', 'rating', 'submitted_at')
    ordering = ('-submitted_at',)


@admin.register(ReviewAnswer)
class ReviewAnswerAdmin(admin.ModelAdmin):
    list_display = ('review', 'question', 'answer_text', 'answer_rating', 'created_at')
    search_fields = ('review__reviewer_name', 'question__question_text', 'answer_text')
    list_filter = ('question', 'created_at')
    ordering = ('-created_at',)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan_type', 'amount', 'currency', 'status', 'paypal_order_id', 'created_at')
    list_filter = ('status', 'plan_type', 'currency', 'created_at')
    search_fields = ('user__username', 'user__email', 'paypal_order_id')
    readonly_fields = ('raw_response',)


@admin.register(ReviewCriteria)
class ReviewCriteriaAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('user__username', 'user__email', 'name')
    ordering = ('-created_at',)


@admin.register(DailySalesReport)
class DailySalesReportAdmin(admin.ModelAdmin):
    list_display = ('business', 'report_date', 'upload_method', 'total_orders', 'processed_orders', 'emails_sent', 'status', 'created_at')
    list_filter = ('status', 'upload_method', 'report_date', 'created_at')
    search_fields = ('business__name', 'file_name', 'user__email')
    readonly_fields = ('created_at', 'updated_at', 'error_log')
    ordering = ('-report_date', '-created_at')
    
    fieldsets = (
        ('Report Information', {
            'fields': ('user', 'business', 'report_date', 'file_name', 'upload_method')
        }),
        ('Processing Results', {
            'fields': ('total_orders', 'processed_orders', 'emails_sent', 'status')
        }),
        ('Errors', {
            'fields': ('error_log',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(FeedbackRequest)
class FeedbackRequestAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'business', 'customer_name', 'customer_email', 'status', 'email_sent_at', 'expires_at')
    list_filter = ('status', 'business', 'email_sent_at', 'expires_at')
    search_fields = ('order_id', 'customer_name', 'customer_email', 'business__name')
    readonly_fields = ('email_token', 'created_at', 'responded_at', 'feedback_url')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Customer Information', {
            'fields': ('order_id', 'customer_name', 'customer_email', 'customer_phone')
        }),
        ('Business & Report', {
            'fields': ('business', 'daily_report')
        }),
        ('Status & Tracking', {
            'fields': ('status', 'email_token', 'feedback_url', 'email_sent_at', 'responded_at', 'expires_at')
        }),
        ('Metadata', {
            'fields': ('ip_address', 'user_agent', 'created_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(CustomerFeedback)
class CustomerFeedbackAdmin(admin.ModelAdmin):
    list_display = ('get_order_id', 'business', 'get_customer_name', 'would_recommend', 'overall_rating', 'status', 'display_color', 'created_at')
    list_filter = ('would_recommend', 'status', 'overall_rating', 'business', 'is_auto_published', 'created_at')
    search_fields = ('feedback_request__order_id', 'feedback_request__customer_name', 'feedback_request__customer_email', 'business__name')
    readonly_fields = ('overall_rating', 'display_color', 'is_positive', 'should_auto_publish', 'created_at', 'updated_at', 'response_date', 'auto_publish_date')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Feedback Information', {
            'fields': ('feedback_request', 'business', 'would_recommend', 'overall_rating', 'status')
        }),
        ('Positive Feedback', {
            'fields': ('logistics_rating', 'communication_rating', 'website_usability_rating', 'positive_comment'),
            'classes': ('collapse',)
        }),
        ('Negative Feedback', {
            'fields': ('negative_comment',),
            'classes': ('collapse',)
        }),
        ('Store Response', {
            'fields': ('store_response', 'responded_by', 'response_date'),
            'classes': ('collapse',)
        }),
        ('Auto-Publishing', {
            'fields': ('auto_publish_date', 'is_auto_published'),
            'classes': ('collapse',)
        }),
        ('Moderation', {
            'fields': ('moderation_notes', 'moderated_by', 'moderated_at'),
            'classes': ('collapse',)
        }),
        ('Display Properties', {
            'fields': ('display_color', 'is_positive', 'should_auto_publish'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('ip_address', 'user_agent', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_feedback', 'reject_feedback', 'mark_auto_published']
    
    def get_order_id(self, obj):
        return obj.feedback_request.order_id
    get_order_id.short_description = 'Order ID'
    get_order_id.admin_order_field = 'feedback_request__order_id'
    
    def get_customer_name(self, obj):
        return obj.feedback_request.customer_name
    get_customer_name.short_description = 'Customer Name'
    get_customer_name.admin_order_field = 'feedback_request__customer_name'
    
    def approve_feedback(self, request, queryset):
        updated = queryset.update(status='published')
        self.message_user(request, f'{updated} feedback approved and published.')
    approve_feedback.short_description = "Approve and publish selected feedback"
    
    def reject_feedback(self, request, queryset):
        updated = queryset.update(status='hidden')
        self.message_user(request, f'{updated} feedback hidden.')
    reject_feedback.short_description = "Hide selected feedback"
    
    def mark_auto_published(self, request, queryset):
        updated = queryset.update(status='auto_published', is_auto_published=True)
        self.message_user(request, f'{updated} feedback marked as auto-published.')
    mark_auto_published.short_description = "Mark as auto-published"
