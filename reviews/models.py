from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import uuid


# ...existing code...

# Place Plan and Payment models after Company definition

# ...existing code...

class Plan(models.Model):
    """Subscription plan for companies"""
    PLAN_CHOICES = [
        ('basic', 'Basic'),
        ('standard', 'Standard'),
        ('premium', 'Premium'),
    ]
    company = models.OneToOneField('Company', on_delete=models.CASCADE, related_name='plan')
    plan_type = models.CharField(max_length=20, choices=PLAN_CHOICES)
    review_limit = models.PositiveIntegerField(default=50)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.company.name} - {self.get_plan_type_display()}"

class Payment(models.Model):
    """Tracks PayPal payments for plan upgrades"""
    PAYMENT_STATUS_CHOICES = [
        ('created', 'Created'),
        ('approved', 'Approved'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    company = models.ForeignKey('Company', on_delete=models.CASCADE, related_name='payments')
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
        return f"{self.company.name} - {self.plan_type} - {self.status}"
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import uuid

User = get_user_model()


class Company(models.Model):
    """Multi-tenant company/brand model"""
    name = models.CharField(max_length=200, unique=True)
    unique_id = models.CharField(max_length=32, unique=True, default=uuid.uuid4)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='companies')
    logo = models.ImageField(upload_to='company_logos/', blank=True, null=True)
    website = models.URLField(blank=True)
    email = models.EmailField(blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = 'Companies'
    
    def __str__(self):
        """String representation of the company (for admin and debugging)."""
        return self.name


class ReviewCriteria(models.Model):
    """Customizable review criteria per company"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='review_criteria')
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order']
        unique_together = ('company', 'name')
        verbose_name_plural = 'Review Criteria'
    
    def __str__(self):
        return f"{self.company.name} - {self.name}"


class Business(models.Model):
    """Model representing a business that can receive reviews"""
    
    name = models.CharField(max_length=200)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='businesses')
    description = models.TextField(blank=True)
    category = models.CharField(max_length=100)
    address = models.TextField()
    phone_number = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)
    logo = models.ImageField(upload_to='business_logos/', blank=True, null=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_businesses')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Business'
        verbose_name_plural = 'Businesses'
        unique_together = ('company', 'name')
    
    def __str__(self):
        return f"{self.company.name} - {self.name}"
    
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
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='orders')
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
        unique_together = ('company', 'order_number')
        ordering = ['-created_at']

    def __str__(self):
        return f"Order {self.order_number} for {self.customer_email}"
    
    @property
    def review_url(self):
        return f"https://yourdomain.com/leave-review/{self.review_link_token}"


class Review(models.Model):
    """Model representing a customer review with customizable criteria"""
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending Approval'),
        ('published', 'Published'),
        ('appealed', 'Appealed'),
        ('archived', 'Archived'),
    ]
    
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='review')
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='reviews')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='reviews')
    reviewer_name = models.CharField(max_length=100, help_text="Public display name")
    reviewer_email = models.EmailField()
    
    # Main question: Would you recommend?
    would_recommend = models.BooleanField()
    
    # Overall rating (calculated from criteria or default 5 if recommended without rating)
    overall_rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        default=5
    )
    
    # Comment (required for negative feedback or low ratings)
    comment = models.TextField(blank=True)
    
    # Review status and moderation
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    is_anonymous = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=True)  # Email-based reviews are verified
    
    # Business response
    business_response = models.TextField(blank=True, help_text="Business response to review")
    response_date = models.DateTimeField(blank=True, null=True)
    responded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='review_responses')
    
    # Metadata
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company', 'status']),
            models.Index(fields=['business', 'status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.overall_rating}★ - {self.business.name} by {self.reviewer_name}"
    
    def save(self, *args, **kwargs):
        if self.business_response and not self.response_date:
            self.response_date = timezone.now()
        super().save(*args, **kwargs)


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


class Plan(models.Model):
    """Subscription plan for companies"""
    PLAN_CHOICES = [
        ('basic', 'Basic'),
        ('standard', 'Standard'),
        ('premium', 'Premium'),
    ]
    company = models.OneToOneField(Company, on_delete=models.CASCADE, related_name='plan')
    plan_type = models.CharField(max_length=20, choices=PLAN_CHOICES)
    review_limit = models.PositiveIntegerField(default=50)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.company.name} - {self.get_plan_type_display()}"


class Badge(models.Model):
    """Certification badge for companies"""
    BADGE_CHOICES = [
        ('bronze', 'Bronze'),
        ('silver', 'Silver'),
        ('gold', 'Gold'),
    ]
    company = models.OneToOneField(Company, on_delete=models.CASCADE, related_name='badge')
    badge_type = models.CharField(max_length=20, choices=BADGE_CHOICES)
    percentage = models.FloatField(default=0)
    assigned_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.company.name} - {self.get_badge_type_display()}"


class QRFeedback(models.Model):
    """QR-based offline feedback"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='qr_feedbacks')
    branch_id = models.CharField(max_length=100)
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField()
    submitted_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"QR Feedback {self.branch_id} - {self.rating}★"


class EmailTemplate(models.Model):
    """Email templates for review requests"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='email_templates')
    name = models.CharField(max_length=100)
    subject = models.CharField(max_length=200)
    body_html = models.TextField()
    body_text = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.company.name} - {self.name}"


class WidgetSettings(models.Model):
    """Widget display settings per company"""
    company = models.OneToOneField(Company, on_delete=models.CASCADE, related_name='widget_settings')
    is_enabled = models.BooleanField(default=True)
    position = models.CharField(max_length=20, choices=[('right', 'Right'), ('left', 'Left')], default='right')
    theme_color = models.CharField(max_length=7, default='#4F46E5')  # Hex color
    show_company_logo = models.BooleanField(default=True)
    show_review_count = models.BooleanField(default=True)
    show_criteria_breakdown = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Widget settings for {self.company.name}"


class SurveyQuestion(models.Model):
    """Custom survey questions for companies"""
    QUESTION_TYPES = [
        ('text', 'Text'),
        ('textarea', 'Textarea'),
        ('rating', 'Rating'),
        ('choice', 'Multiple Choice'),
        ('boolean', 'Yes/No'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='survey_questions')
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
        unique_together = ('company', 'question_text')
    
    def __str__(self):
        return f"{self.company.name} - {self.question_text[:50]}"


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
