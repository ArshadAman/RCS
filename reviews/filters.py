import django_filters
from django.db.models import Q
from .models import Review, Order, Business, Company, QRFeedback


class ReviewFilter(django_filters.FilterSet):
    """Filter class for Review model"""
    
    business = django_filters.CharFilter(field_name='business__id')
    company = django_filters.CharFilter(field_name='business__company__id')
    rating_min = django_filters.NumberFilter(field_name='overall_rating', lookup_expr='gte')
    rating_max = django_filters.NumberFilter(field_name='overall_rating', lookup_expr='lte')
    date_from = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    date_to = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    status = django_filters.ChoiceFilter(
        field_name='status',
        choices=Review.STATUS_CHOICES
    )
    would_recommend = django_filters.BooleanFilter(field_name='would_recommend')
    has_comment = django_filters.BooleanFilter(method='filter_has_comment')
    search = django_filters.CharFilter(method='filter_search')
    
    class Meta:
        model = Review
        fields = [
            'business', 'company', 'rating_min', 'rating_max',
            'date_from', 'date_to', 'status', 'would_recommend',
            'has_comment', 'search'
        ]
    
    def filter_has_comment(self, queryset, name, value):
        if value:
            return queryset.exclude(comment__isnull=True).exclude(comment__exact='')
        else:
            return queryset.filter(Q(comment__isnull=True) | Q(comment__exact=''))
    
    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(comment__icontains=value) |
            Q(customer_name__icontains=value) |
            Q(customer_email__icontains=value) |
            Q(business__name__icontains=value)
        )


class OrderFilter(django_filters.FilterSet):
    """Filter class for Order model"""
    
    business = django_filters.CharFilter(field_name='business__id')
    company = django_filters.CharFilter(field_name='business__company__id')
    status = django_filters.ChoiceFilter(
        field_name='status',
        choices=Order.STATUS_CHOICES
    )
    date_from = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    date_to = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    customer_search = django_filters.CharFilter(method='filter_customer_search')
    order_id = django_filters.CharFilter(field_name='order_id', lookup_expr='icontains')
    
    class Meta:
        model = Order
        fields = [
            'business', 'company', 'status', 'date_from', 'date_to',
            'customer_search', 'order_id'
        ]
    
    def filter_customer_search(self, queryset, name, value):
        return queryset.filter(
            Q(customer_name__icontains=value) |
            Q(customer_email__icontains=value) |
            Q(customer_phone__icontains=value)
        )


class BusinessFilter(django_filters.FilterSet):
    """Filter class for Business model"""
    
    company = django_filters.CharFilter(field_name='company__id')
    category = django_filters.CharFilter(field_name='category', lookup_expr='icontains')
    is_active = django_filters.BooleanFilter(field_name='is_active')
    search = django_filters.CharFilter(method='filter_search')
    
    class Meta:
        model = Business
        fields = ['company', 'category', 'is_active', 'search']
    
    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(name__icontains=value) |
            Q(description__icontains=value) |
            Q(category__icontains=value) |
            Q(address__icontains=value)
        )


class CompanyFilter(django_filters.FilterSet):
    """Filter class for Company model"""
    
    is_active = django_filters.BooleanFilter(field_name='is_active')
    search = django_filters.CharFilter(method='filter_search')
    
    class Meta:
        model = Company
        fields = ['is_active', 'search']
    
    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(name__icontains=value) |
            Q(email__icontains=value) |
            Q(website__icontains=value)
        )


class QRFeedbackFilter(django_filters.FilterSet):
    """Filter class for QRFeedback model"""
    
    company = django_filters.CharFilter(field_name='company__id')
    branch_id = django_filters.CharFilter(field_name='branch_id')
    rating_min = django_filters.NumberFilter(field_name='rating', lookup_expr='gte')
    rating_max = django_filters.NumberFilter(field_name='rating', lookup_expr='lte')
    date_from = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    date_to = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    
    class Meta:
        model = QRFeedback
        fields = ['company', 'branch_id', 'rating_min', 'rating_max', 'date_from', 'date_to']
