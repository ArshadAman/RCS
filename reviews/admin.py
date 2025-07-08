from django.contrib import admin
from .models import Business, Review, ReviewImage, ReviewLike, Category, Company, Order, SurveyQuestion, Plan, Badge, QRFeedback, ReviewAnswer


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('name',)


@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'owner', 'average_rating', 'total_reviews', 'is_active', 'created_at')
    list_filter = ('category', 'is_active', 'created_at')
    search_fields = ('name', 'description', 'category', 'owner__email')
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
    list_display = ('title', 'business', 'reviewer_name', 'rating', 'is_approved', 'is_featured', 'created_at')
    list_filter = ('rating', 'is_approved', 'is_featured', 'is_anonymous', 'created_at')
    search_fields = ('title', 'content', 'business__name', 'reviewer__email', 'reviewer_name')
    readonly_fields = ('created_at', 'updated_at', 'response_date')
    ordering = ('-created_at',)
    inlines = [ReviewImageInline]
    
    fieldsets = (
        ('Review Information', {
            'fields': ('business', 'reviewer', 'rating', 'title', 'content')
        }),
        ('Reviewer Information', {
            'fields': ('reviewer_name', 'reviewer_email', 'is_anonymous')
        }),
        ('Management', {
            'fields': ('is_approved', 'is_featured')
        }),
        ('Business Response', {
            'fields': ('response', 'response_date'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_reviews', 'feature_reviews', 'unfeature_reviews']
    
    def approve_reviews(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f'{updated} reviews approved successfully.')
    approve_reviews.short_description = "Approve selected reviews"
    
    def feature_reviews(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, f'{updated} reviews featured successfully.')
    feature_reviews.short_description = "Feature selected reviews"
    
    def unfeature_reviews(self, request, queryset):
        updated = queryset.update(is_featured=False)
        self.message_user(request, f'{updated} reviews unfeatured successfully.')
    unfeature_reviews.short_description = "Unfeature selected reviews"


@admin.register(ReviewImage)
class ReviewImageAdmin(admin.ModelAdmin):
    list_display = ('review', 'caption', 'uploaded_at')
    list_filter = ('uploaded_at',)
    search_fields = ('review__title', 'caption')
    ordering = ('-uploaded_at',)


@admin.register(ReviewLike)
class ReviewLikeAdmin(admin.ModelAdmin):
    list_display = ('review', 'user', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('review__title', 'user__email')
    ordering = ('-created_at',)


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'unique_id', 'owner', 'is_active', 'created_at')
    search_fields = ('name', 'unique_id', 'owner__email')
    list_filter = ('is_active', 'created_at')
    ordering = ('-created_at',)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'company', 'customer_email', 'product_name', 'purchase_date', 'created_at')
    search_fields = ('order_id', 'customer_email', 'product_name')
    list_filter = ('company', 'purchase_date', 'created_at')
    ordering = ('-created_at',)


@admin.register(SurveyQuestion)
class SurveyQuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'company', 'is_active', 'is_required', 'order', 'created_at')
    search_fields = ('text',)
    list_filter = ('company', 'is_active', 'is_required')
    ordering = ('company', 'order')


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ('company', 'plan_type', 'review_limit', 'created_at')
    list_filter = ('plan_type',)
    search_fields = ('company__name',)
    ordering = ('-created_at',)


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ('company', 'badge_type', 'percentage', 'assigned_at')
    list_filter = ('badge_type',)
    search_fields = ('company__name',)
    ordering = ('-assigned_at',)


@admin.register(QRFeedback)
class QRFeedbackAdmin(admin.ModelAdmin):
    list_display = ('company', 'branch_id', 'rating', 'ip_address', 'submitted_at')
    search_fields = ('branch_id', 'company__name')
    list_filter = ('company', 'rating', 'submitted_at')
    ordering = ('-submitted_at',)


@admin.register(ReviewAnswer)
class ReviewAnswerAdmin(admin.ModelAdmin):
    list_display = ('review', 'question', 'value', 'created_at')
    search_fields = ('review__title', 'question__text', 'value')
    list_filter = ('question', 'created_at')
    ordering = ('-created_at',)
