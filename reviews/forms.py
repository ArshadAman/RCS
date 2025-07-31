from django import forms
from django.core.validators import MinLengthValidator, EmailValidator
from .models import Review


class ReviewSubmissionForm(forms.Form):
    """Form for submitting reviews via template views"""
    
    customer_name = forms.CharField(
        max_length=100,
        validators=[MinLengthValidator(2)],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your full name',
            'required': True
        }),
        label='Your Name'
    )
    
    customer_email = forms.EmailField(
        validators=[EmailValidator()],
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address',
            'required': True
        }),
        label='Your Email'
    )
    
    product_name = forms.CharField(
        max_length=200,
        validators=[MinLengthValidator(2)],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Product or service name',
            'required': True
        }),
        label='Product/Service'
    )
    
    rating = forms.IntegerField(
        min_value=1,
        max_value=5,
        widget=forms.HiddenInput(),
        label='Rating'
    )
    
    review_text = forms.CharField(
        max_length=1000,
        validators=[MinLengthValidator(10)],
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Share your experience with us...',
            'rows': 4,
            'required': True
        }),
        label='Your Review'
    )
    
    def clean_rating(self):
        rating = self.cleaned_data.get('rating')
        if not rating or rating < 1 or rating > 5:
            raise forms.ValidationError('Please select a rating between 1 and 5 stars.')
        return rating
    
    def clean_review_text(self):
        review_text = self.cleaned_data.get('review_text', '').strip()
        if len(review_text) < 10:
            raise forms.ValidationError('Please provide a more detailed review (at least 10 characters).')
        
        # Check for inappropriate content (basic filtering)
        inappropriate_words = ['spam', 'fake', 'test', 'ignore']
        if any(word in review_text.lower() for word in inappropriate_words):
            raise forms.ValidationError('Please provide a genuine review.')
        
        return review_text


class ReviewResponseForm(forms.Form):
    """Form for business owners to respond to reviews"""
    
    response_text = forms.CharField(
        max_length=500,
        validators=[MinLengthValidator(10)],
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Write your response to this review...',
            'rows': 3,
            'required': True
        }),
        label='Your Response'
    )
    
    def clean_response_text(self):
        response_text = self.cleaned_data.get('response_text', '').strip()
        if len(response_text) < 10:
            raise forms.ValidationError('Please provide a meaningful response (at least 10 characters).')
        return response_text
