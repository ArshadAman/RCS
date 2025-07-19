"""
PayPal integration utilities for subscription payments and vaulting.
Based on PayPal REST API for SaaS subscription payments.
"""
import requests
import uuid
from django.conf import settings

PAYPAL_API_BASE = getattr(settings, 'PAYPAL_API_BASE', 'https://api-m.sandbox.paypal.com')


def get_paypal_access_token():
    """Get PayPal access token for API calls."""
    client_id = settings.PAYPAL_CLIENT_ID
    client_secret = settings.PAYPAL_CLIENT_SECRET
    auth = (client_id, client_secret)
    data = {'grant_type': 'client_credentials'}
    resp = requests.post(f"{PAYPAL_API_BASE}/v1/oauth2/token", data=data, auth=auth)
    resp.raise_for_status()
    return resp.json()['access_token']


def create_vault_setup_token(plan_type, company_name, return_url, cancel_url):
    """Create a setup token for vaulting payment method."""
    access_token = get_paypal_access_token()
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {access_token}',
        'PayPal-Request-Id': str(uuid.uuid4()),
    }
    
    # Plan pricing based on plan type
    pricing = {
        'basic': {'amount': '29.99', 'description': 'Basic Plan - 100 reviews/month'},
        'standard': {'amount': '99.99', 'description': 'Standard Plan - 1000 reviews/month'},
        'premium': {'amount': '199.99', 'description': 'Premium Plan - 10000 reviews/month'},
    }
    
    plan_info = pricing.get(plan_type, pricing['basic'])
    
    data = {
        "payment_source": {
            "paypal": {
                "usage_type": "MERCHANT",
                "usage_pattern": "SUBSCRIPTION_PREPAID",
                "experience_context": {
                    "return_url": return_url,
                    "cancel_url": cancel_url,
                },
            },
        },
    }
    
    resp = requests.post(f"{PAYPAL_API_BASE}/v3/vault/setup-tokens", json=data, headers=headers)
    resp.raise_for_status()
    return resp.json()


def create_payment_token(setup_token_id):
    """Create a payment token from setup token."""
    access_token = get_paypal_access_token()
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {access_token}',
        'PayPal-Request-Id': str(uuid.uuid4()),
    }
    
    data = {
        "payment_source": {
            "token": {
                "id": setup_token_id,
                "type": "SETUP_TOKEN"
            }
        }
    }
    
    resp = requests.post(f"{PAYPAL_API_BASE}/v3/vault/payment-tokens", json=data, headers=headers)
    resp.raise_for_status()
    return resp.json()


def create_paypal_order(amount, currency, plan_type, company_name, return_url, cancel_url, payment_token_id=None):
    """Create a PayPal order for payment (with optional vault token)."""
    access_token = get_paypal_access_token()
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {access_token}',
        'PayPal-Request-Id': str(uuid.uuid4()),  # Idempotency
    }
    data = {
        "intent": "CAPTURE",
        "purchase_units": [
            {
                "amount": {
                    "currency_code": currency,
                    "value": str(amount)
                },
                "description": f"{plan_type.title()} Plan for {company_name}",
                "custom_id": f"plan_{plan_type}_{company_name}"
            }
        ],
        "application_context": {
            "return_url": return_url,
            "cancel_url": cancel_url,
            "brand_name": "Review Collection System",
            "landing_page": "BILLING",
            "user_action": "PAY_NOW"
        }
    }
    
    # If using vaulted payment method
    if payment_token_id:
        data["payment_source"] = {
            "paypal": {
                "vault_id": payment_token_id,
                "stored_credential": {
                    "payment_initiator": "MERCHANT",
                    "usage": "SUBSEQUENT",
                    "usage_pattern": "RECURRING_POSTPAID",
                },
            },
        }
    
    resp = requests.post(f"{PAYPAL_API_BASE}/v2/checkout/orders", json=data, headers=headers)
    resp.raise_for_status()
    return resp.json()


def capture_paypal_order(order_id):
    """Capture a PayPal order to complete payment."""
    access_token = get_paypal_access_token()
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {access_token}',
    }
    resp = requests.post(f"{PAYPAL_API_BASE}/v2/checkout/orders/{order_id}/capture", headers=headers)
    resp.raise_for_status()
    return resp.json()


def create_subscription_plan(plan_name, plan_description, amount, currency):
    """Create a PayPal subscription plan for recurring payments (optional future feature)."""
    access_token = get_paypal_access_token()
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {access_token}',
        'PayPal-Request-Id': str(uuid.uuid4()),
    }
    
    # First create a product
    product_data = {
        "name": f"Review System {plan_name}",
        "description": plan_description,
        "type": "SERVICE",
        "category": "SOFTWARE"
    }
    product_resp = requests.post(f"{PAYPAL_API_BASE}/v1/catalogs/products", json=product_data, headers=headers)
    product_resp.raise_for_status()
    product_id = product_resp.json()['id']
    
    # Then create the plan
    plan_data = {
        "product_id": product_id,
        "name": f"{plan_name} Plan",
        "description": plan_description,
        "billing_cycles": [
            {
                "frequency": {
                    "interval_unit": "MONTH",
                    "interval_count": 1
                },
                "tenure_type": "REGULAR",
                "sequence": 1,
                "total_cycles": 0,  # Infinite
                "pricing_scheme": {
                    "fixed_price": {
                        "value": str(amount),
                        "currency_code": currency
                    }
                }
            }
        ],
        "payment_preferences": {
            "auto_bill_outstanding": True,
            "setup_fee_failure_action": "CONTINUE",
            "payment_failure_threshold": 3
        }
    }
    plan_resp = requests.post(f"{PAYPAL_API_BASE}/v1/billing/plans", json=plan_data, headers=headers)
    plan_resp.raise_for_status()
    return plan_resp.json()


def verify_webhook_signature(headers, body):
    """Verify PayPal webhook signature (implement if needed for security)."""
    # For production, implement webhook signature verification
    # https://developer.paypal.com/docs/api/webhooks/v1/#verify-webhook-signature
    pass
