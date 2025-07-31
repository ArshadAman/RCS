from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
import uuid

User = get_user_model()


def generate_unique_id():
    return str(uuid.uuid4()).replace('-', '')[:32]


class Plan(models.Model):
    """Subscription plan for users"""
    PLAN_CHOICES = [
        ('basic', 'Basic'),
        ('standard', 'Standard'),
        ('premium', 'Premium'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='plan', null=True)
    plan_type = models.CharField(max_length=20, choices=PLAN_CHOICES)
    review_limit = models.PositiveIntegerField(default=50)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.get_plan_type_display()}"


class Payment(models.Model):
    """Tracks PayPal payments for plan upgrades"""
    PAYMENT_STATUS_CHOICES = [
        ('created', 'Created'),
        ('approved', 'Approved'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments', null=True)
    plan_type = models.CharField(max_length=20, choices=Plan.PLAN_CHOICES)
    paypal_order_id = models.CharField(max_length=100, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default='USD')
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    raw_response = models.JSONField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'

    def __str__(self):
        return f"{self.user.username} - {self.plan_type} - {self.status}"


class ReviewCriteria(models.Model):
    """Customizable review criteria per user/business"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='review_criteria', null=True)
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order']
        unique_together = ('user', 'name')
        verbose_name_plural = 'Review Criteria'
    
    def __str__(self):
        return f"{self.user.username} - {self.name}"


class Business(models.Model):
    """Model representing a user's business that can receive reviews"""
    
    name = models.CharField(max_length=200)
    owner = models.OneToOneField(User, on_delete=models.CASCADE, related_name='business')
    description = models.TextField(blank=True)
    category = models.CharField(max_length=100)
    address = models.TextField()
    phone_number = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)
    logo = models.ImageField(upload_to='business_logos/', blank=True, null=True)
    unique_id = models.CharField(max_length=32, default=generate_unique_id)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Business'
        verbose_name_plural = 'Businesses'
    
    def __str__(self):
        return self.name
    
    @property
    def average_rating(self):
        reviews = self.reviews.filter(status='published')
        if reviews.exists():
            return round(reviews.aggregate(models.Avg('overall_rating'))['overall_rating__avg'], 1)
        return 0
    
    @property
    def total_reviews(self):
        return self.reviews.filter(status='published').count()
    
    @property
    def recommendation_percentage(self):
        reviews = self.reviews.filter(status='published')
        if reviews.exists():
            recommended_count = reviews.filter(would_recommend=True).count()
            return round((recommended_count / reviews.count()) * 100, 1)
        return 0


class Order(models.Model):
    """Order intake for feedback requests"""
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('review_sent', 'Review Request Sent'),
        ('completed', 'Review Completed'),
        ('expired', 'Expired'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders', null=True)
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='orders')
    order_number = models.CharField(max_length=100)
    customer_email = models.EmailField()
    customer_name = models.CharField(max_length=100)
    product_service_name = models.CharField(max_length=200)
    purchase_date = models.DateTimeField()
    review_link_token = models.UUIDField(default=uuid.uuid4, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    email_sent_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'order_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"Order {self.order_number} for {self.customer_email}"
    
    @property
    def review_url(self):
        return f"https://yourdomain.com/leave-review/{self.review_link_token}"


class Review(models.Model):
    """Model representing a customer review with customizable criteria and daily sales integration"""
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending_moderation', 'Pending Moderation'),
        ('published', 'Published'),
        ('disputed', 'Under Dispute'),
        ('auto_published', 'Auto Published (7 days)'),
        ('hidden', 'Hidden by Store'),
        ('appealed', 'Appealed'),
        ('archived', 'Archived'),
    ]
    
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]
    
    # Can be linked to either Order (widget reviews) or ReviewRequest (daily sales reviews)
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='review', blank=True, null=True)
    review_request = models.OneToOneField('ReviewRequest', on_delete=models.CASCADE, related_name='review', blank=True, null=True)
    
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='reviews')
    reviewer_name = models.CharField(max_length=100, help_text="Public display name")
    reviewer_email = models.EmailField()
    
    # Main question: Would you recommend this store?
    would_recommend = models.BooleanField()
    
    # If YES (positive feedback) - detailed ratings
    logistics_rating = models.IntegerField(choices=RATING_CHOICES, blank=True, null=True, help_text="Shipping, delivery, packaging")
    communication_rating = models.IntegerField(choices=RATING_CHOICES, blank=True, null=True, help_text="Customer service, responsiveness")
    website_usability_rating = models.IntegerField(choices=RATING_CHOICES, blank=True, null=True, help_text="Website experience, ease of ordering")
    positive_comment = models.TextField(blank=True, help_text="Additional positive feedback")
    
    # If NO (negative feedback)
    negative_comment = models.TextField(blank=True, help_text="Detailed explanation for negative feedback")
    
    # Overall rating (calculated from criteria or default based on recommendation)
    overall_rating = models.IntegerField(
        choices=RATING_CHOICES,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        default=5
    )
    
    # General comment (for widget reviews or additional feedback)
    comment = models.TextField(blank=True, help_text="General review comment")
    
    # Review status and moderation
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending_moderation')
    is_anonymous = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=True)  # Email-based reviews are verified
    
    # Store response
    store_response = models.TextField(blank=True, help_text="Store response to review")
    response_date = models.DateTimeField(blank=True, null=True)
    responded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='review_responses')
    
    # Auto-publish tracking (for negative reviews from daily sales)
    auto_publish_date = models.DateTimeField(blank=True, null=True)
    is_auto_published = models.BooleanField(default=False)
    
    # Moderation
    moderation_notes = models.TextField(blank=True)
    moderated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='moderated_reviews')
    moderated_at = models.DateTimeField(blank=True, null=True)
    
    # Metadata
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['business', 'status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        recommend_text = "YES" if self.would_recommend else "NO"
        if self.review_request:
            return f"{self.review_request.order_id} - {recommend_text} ({self.overall_rating}★)"
        return f"{self.overall_rating}★ - {self.business.name} by {self.reviewer_name}"
    
    def save(self, *args, **kwargs):
        # Calculate overall rating based on recommendation and sub-ratings
        if self.would_recommend:
            # Positive feedback: 5 stars or average of sub-ratings
            if self.logistics_rating or self.communication_rating or self.website_usability_rating:
                ratings = []
                if self.logistics_rating:
                    ratings.append(self.logistics_rating)
                if self.communication_rating:
                    ratings.append(self.communication_rating)
                if self.website_usability_rating:
                    ratings.append(self.website_usability_rating)
                
                if ratings:
                    self.overall_rating = round(sum(ratings) / len(ratings))
                else:
                    self.overall_rating = 5
            else:
                self.overall_rating = 5
            
            # Positive feedback gets published immediately
            if self.status == 'pending_moderation':
                self.status = 'published'
        else:
            # Negative feedback: Must have detailed comment for daily sales reviews
            if self.review_request and (not self.negative_comment or len(self.negative_comment.strip()) < 50):
                from django.core.exceptions import ValidationError
                raise ValidationError("Negative feedback must include a detailed comment (minimum 50 characters)")
            
            # Calculate based on sub-ratings or default to 2 for negative feedback
            if self.logistics_rating or self.communication_rating or self.website_usability_rating:
                ratings = []
                if self.logistics_rating:
                    ratings.append(self.logistics_rating)
                if self.communication_rating:
                    ratings.append(self.communication_rating)
                if self.website_usability_rating:
                    ratings.append(self.website_usability_rating)
                
                if ratings:
                    self.overall_rating = round(sum(ratings) / len(ratings))
                else:
                    self.overall_rating = 2
            else:
                self.overall_rating = 2
            
            # Set auto-publish date for negative feedback from daily sales (7 days from creation)
            if self.review_request and not self.auto_publish_date:
                self.auto_publish_date = timezone.now() + timezone.timedelta(days=7)
        
        # Handle store response timing
        if self.store_response and not self.response_date:
            self.response_date = timezone.now()
        
        # Check if owner responded to negative feedback within 7 days - publish it
        if (not self.would_recommend and 
            self.store_response and 
            self.status == 'pending_moderation' and
            self.auto_publish_date and 
            timezone.now() <= self.auto_publish_date):
            self.status = 'published'  # Publish with response
        
        # Auto-publish negative feedback after 7 days (without response)
        elif (not self.would_recommend and 
              self.status == 'pending_moderation' and 
              self.auto_publish_date and 
              timezone.now() >= self.auto_publish_date and 
              not self.store_response):
            self.status = 'auto_published'
            self.is_auto_published = True
        
        super().save(*args, **kwargs)
    
    @property
    def is_positive(self):
        return self.would_recommend
    
    @property
    def should_auto_publish(self):
        if self.would_recommend:
            return False
        return timezone.now() >= self.auto_publish_date if self.auto_publish_date else False
    
    @property
    def display_color(self):
        return 'green' if self.would_recommend else 'red'
    
    @property
    def is_daily_sales_review(self):
        """Check if this review came from daily sales report"""
        return self.review_request is not None


class ReviewCriteriaRating(models.Model):
    """Individual ratings for each criteria in a review"""
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='criteria_ratings')
    criteria = models.ForeignKey(ReviewCriteria, on_delete=models.CASCADE)
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    
    class Meta:
        unique_together = ('review', 'criteria')
    
    def __str__(self):
        return f"{self.review} - {self.criteria.name}: {self.rating}★"


class ReviewImage(models.Model):
    """Model for storing review images"""
    
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='review_images/')
    caption = models.CharField(max_length=200, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Image for review: {self.review}"


class ReviewLike(models.Model):
    """Model for tracking review likes/helpful votes"""
    
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('review', 'user')
    
    def __str__(self):
        return f"{self.user.username} liked review by {self.review.reviewer_name}"


class Category(models.Model):
    """Model for business categories"""
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text="CSS class for icon")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Badge(models.Model):
    """Certification badge for users/businesses"""
    BADGE_CHOICES = [
        ('bronze', 'Bronze'),
        ('silver', 'Silver'),
        ('gold', 'Gold'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='badge', null=True)
    badge_type = models.CharField(max_length=20, choices=BADGE_CHOICES)
    percentage = models.FloatField(default=0)
    assigned_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.get_badge_type_display()}"


class QRFeedback(models.Model):
    """QR-based offline feedback"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='qr_feedbacks', null=True)
    branch_id = models.CharField(max_length=100)
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField()
    submitted_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"QR Feedback {self.branch_id} - {self.rating}★"


class EmailTemplate(models.Model):
    """Email templates for review requests"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_templates', null=True)
    name = models.CharField(max_length=100)
    subject = models.CharField(max_length=200)
    body_html = models.TextField()
    body_text = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.name}"


class WidgetSettings(models.Model):
    """Widget display settings per user/business"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='widget_settings', null=True)
    is_enabled = models.BooleanField(default=True)
    position = models.CharField(max_length=20, choices=[('right', 'Right'), ('left', 'Left')], default='right')
    theme_color = models.CharField(max_length=7, default='#4F46E5')  # Hex color
    show_business_logo = models.BooleanField(default=True)
    show_review_count = models.BooleanField(default=True)
    show_criteria_breakdown = models.BooleanField(default=True)
    display_count = models.PositiveIntegerField(default=5)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Widget settings for {self.user.username}"


class SurveyQuestion(models.Model):
    """Custom survey questions for users/businesses"""
    QUESTION_TYPES = [
        ('text', 'Text'),
        ('textarea', 'Textarea'),
        ('rating', 'Rating'),
        ('choice', 'Multiple Choice'),
        ('boolean', 'Yes/No'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='survey_questions', null=True)
    question_text = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES, default='text')
    is_required = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    choices = models.JSONField(blank=True, null=True)  # For multiple choice questions
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order']
        unique_together = ('user', 'question_text')
    
    def __str__(self):
        return f"{self.user.username} - {self.question_text[:50]}"


class ReviewAnswer(models.Model):
    """Answers to custom survey questions"""
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(SurveyQuestion, on_delete=models.CASCADE)
    answer_text = models.TextField(blank=True)
    answer_rating = models.IntegerField(
        blank=True, 
        null=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    answer_boolean = models.BooleanField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('review', 'question')
    
    def __str__(self):
        return f"{self.review.id} - {self.question.question_text[:30]}"


class DailySalesReport(models.Model):
    """Daily sales report uploaded by stores"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sales_reports')
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='sales_reports')
    report_date = models.DateField()
    file_name = models.CharField(max_length=255)
    upload_method = models.CharField(max_length=20, choices=[('manual', 'Manual Upload'), ('api', 'API Integration')], default='manual')
    total_orders = models.PositiveIntegerField(default=0)
    processed_orders = models.PositiveIntegerField(default=0)
    emails_sent = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=[
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('partial', 'Partially Processed')
    ], default='processing')
    error_log = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('user', 'business', 'report_date')
        ordering = ['-report_date', '-created_at']
    
    def __str__(self):
        return f"{self.business.name} - {self.report_date} ({self.total_orders} orders)"


class ReviewRequest(models.Model):
    """Tracks review requests sent to customers"""
    STATUS_CHOICES = [
        ('pending', 'Pending Response'),
        ('responded', 'Response Received'),
        ('expired', 'Expired (7 days)'),
        ('invalid', 'Invalid Email/Customer'),
    ]
    
    daily_report = models.ForeignKey(DailySalesReport, on_delete=models.CASCADE, related_name='review_requests')
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='review_requests')
    order_id = models.CharField(max_length=100)
    customer_name = models.CharField(max_length=100)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=20, blank=True)
    
    # Tracking
    email_token = models.UUIDField(default=uuid.uuid4, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    email_sent_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(blank=True, null=True)
    expires_at = models.DateTimeField()
    
    # Metadata
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('business', 'order_id', 'customer_email')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.order_id} - {self.customer_email} ({self.status})"
    
    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(days=7)
        super().save(*args, **kwargs)
    
    @property
    def review_url(self):
        return f"https://yourdomain.com/review/{self.email_token}"
    
    @property
    def is_expired(self):
        return timezone.now() > self.expires_at



