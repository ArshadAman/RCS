from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

User = get_user_model()


class Business(models.Model):
    """Model representing a business that can receive reviews"""
    
    name = models.CharField(max_length=200)
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
    
    def __str__(self):
        return self.name
    
    @property
    def average_rating(self):
        reviews = self.reviews.filter(is_approved=True)
        if reviews.exists():
            return round(reviews.aggregate(models.Avg('rating'))['rating__avg'], 1)
        return 0
    
    @property
    def total_reviews(self):
        return self.reviews.filter(is_approved=True).count()


class Review(models.Model):
    """Model representing a customer review"""
    
    RATING_CHOICES = [(i, i) for i in range(1, 6)]
    
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='reviews')
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        choices=RATING_CHOICES
    )
    title = models.CharField(max_length=200)
    content = models.TextField()
    reviewer_name = models.CharField(max_length=100, help_text="Public display name")
    reviewer_email = models.EmailField(blank=True)
    is_anonymous = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    response = models.TextField(blank=True, help_text="Business response to review")
    response_date = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('business', 'reviewer')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.rating}★ - {self.title} by {self.reviewer_name}"
    
    def save(self, *args, **kwargs):
        if self.response and not self.response_date:
            self.response_date = timezone.now()
        super().save(*args, **kwargs)


class ReviewImage(models.Model):
    """Model for storing review images"""
    
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='review_images/')
    caption = models.CharField(max_length=200, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Image for review: {self.review.title}"


class ReviewLike(models.Model):
    """Model for tracking review likes/helpful votes"""
    
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('review', 'user')
    
    def __str__(self):
        return f"{self.user.username} liked {self.review.title}"


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


class Company(models.Model):
    """Multi-tenant company/brand model"""
    name = models.CharField(max_length=200, unique=True)
    unique_id = models.CharField(max_length=32, unique=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='companies')
    logo = models.ImageField(upload_to='company_logos/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name


class Order(models.Model):
    """Order intake for feedback requests"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='orders')
    order_id = models.CharField(max_length=100)
    customer_email = models.EmailField()
    customer_name = models.CharField(max_length=100)
    product_name = models.CharField(max_length=200)
    purchase_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('company', 'order_id')

    def __str__(self):
        return f"Order {self.order_id} for {self.customer_email}"


class SurveyQuestion(models.Model):
    """Admin-editable survey/rating fields"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='survey_questions')
    text = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)
    is_required = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.text


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


class ReviewAnswer(models.Model):
    """Stores answers to dynamic survey questions for each review"""
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(SurveyQuestion, on_delete=models.CASCADE)
    value = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('review', 'question')

    def __str__(self):
        return f"{self.review} - {self.question.text}: {self.value}"
