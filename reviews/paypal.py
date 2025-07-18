"""
PayPal integration utilities for order creation and webhook verification.
"""
import requests
from django.conf import settings

PAYPAL_API_BASE = getattr(settings, 'PAYPAL_API_BASE', 'https://api-m.sandbox.paypal.com')


def get_paypal_access_token():
    client_id = settings.PAYPAL_CLIENT_ID
    client_secret = settings.PAYPAL_CLIENT_SECRET
    auth = (client_id, client_secret)
    data = {'grant_type': 'client_credentials'}
    resp = requests.post(f"{PAYPAL_API_BASE}/v1/oauth2/token", data=data, auth=auth)
    resp.raise_for_status()
    return resp.json()['access_token']


def create_paypal_order(amount, currency, plan_type, company_name, return_url, cancel_url):
    access_token = get_paypal_access_token()
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {access_token}',
    }
    data = {
        "intent": "CAPTURE",
        "purchase_units": [
            {
                "amount": {
                    "currency_code": currency,
                    "value": str(amount)
                },
                "description": f"{plan_type.title()} Plan for {company_name}"
            }
        ],
        "application_context": {
            "return_url": return_url,
            "cancel_url": cancel_url
        }
    }
    resp = requests.post(f"{PAYPAL_API_BASE}/v2/checkout/orders", json=data, headers=headers)
    resp.raise_for_status()
    return resp.json()


def capture_paypal_order(order_id):
    access_token = get_paypal_access_token()
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {access_token}',
    }
    resp = requests.post(f"{PAYPAL_API_BASE}/v2/checkout/orders/{order_id}/capture", headers=headers)
    resp.raise_for_status()
    return resp.json()


def verify_webhook_signature(headers, body):
    # Implement PayPal webhook signature verification if needed
    pass
