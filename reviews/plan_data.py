"""
Plan data configuration for the review collection system
"""

PLAN_DATA = {
    'basic': {
        'name': 'Basic Plan',
        'price': 0,
        'currency': 'USD',
        'billing_period': 'month',
        'review_limit': 50,
        'features': [
            'Up to 50 reviews per month',
            'Basic email templates',
            'Standard widget',
            'Email notifications',
            'Basic analytics',
            'Community support'
        ],
        'limitations': [
            'Limited customization',
            'Basic reporting only',
            'No API access'
        ]
    },
    'standard': {
        'name': 'Standard Plan',
        'price': 29,
        'currency': 'USD',
        'billing_period': 'month',
        'review_limit': 200,
        'features': [
            'Up to 200 reviews per month',
            'Custom email templates',
            'Advanced widget customization',
            'Priority email notifications',
            'Advanced analytics & reporting',
            'Custom survey questions',
            'Review response management',
            'Email support'
        ],
        'limitations': [
            'No white-label options',
            'Limited API access'
        ]
    },
    'premium': {
        'name': 'Premium Plan',
        'price': 99,
        'currency': 'USD',
        'billing_period': 'month',
        'review_limit': -1,  # -1 means unlimited
        'features': [
            'Unlimited reviews',
            'Full template customization',
            'White-label widget',
            'Real-time notifications',
            'Advanced analytics & insights',
            'Custom survey questions',
            'Review response management',
            'Full API access',
            'Priority support',
            'Custom integrations',
            'Advanced reporting & exports',
            'Multi-user accounts'
        ],
        'limitations': []
    }
}


def get_plan_data(plan_type='basic'):
    """Get plan data for a specific plan type"""
    return PLAN_DATA.get(plan_type, PLAN_DATA['basic'])


def get_all_plans():
    """Get all available plans"""
    return PLAN_DATA


def get_plan_comparison():
    """Get plan comparison data"""
    return {
        'features': [
            {
                'name': 'Monthly Reviews',
                'basic': '50',
                'standard': '200',
                'premium': 'Unlimited'
            },
            {
                'name': 'Email Templates',
                'basic': 'Basic',
                'standard': 'Custom',
                'premium': 'Full Customization'
            },
            {
                'name': 'Widget Customization',
                'basic': 'Standard',
                'standard': 'Advanced',
                'premium': 'White-label'
            },
            {
                'name': 'Analytics',
                'basic': 'Basic',
                'standard': 'Advanced',
                'premium': 'Advanced + Insights'
            },
            {
                'name': 'Survey Questions',
                'basic': '❌',
                'standard': '✅',
                'premium': '✅'
            },
            {
                'name': 'API Access',
                'basic': '❌',
                'standard': 'Limited',
                'premium': 'Full'
            },
            {
                'name': 'Support',
                'basic': 'Community',
                'standard': 'Email',
                'premium': 'Priority'
            }
        ],
        'plans': PLAN_DATA
    }
