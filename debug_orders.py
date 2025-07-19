#!/usr/bin/env python3
import requests
import json

# Test just the orders endpoint to see the exact error
base_url = "http://localhost:8000/api"

# First login to get a token
login_data = {
    "email": "admin@example.com",
    "password": "admin123"
}

try:
    login_response = requests.post(f"{base_url}/auth/login/", json=login_data)
    print(f"Login Status: {login_response.status_code}")
    
    if login_response.status_code == 200:
        token = login_response.json()['tokens']['access']
        headers = {'Authorization': f'Bearer {token}'}
        
        # Test GET orders first
        get_response = requests.get(f"{base_url}/orders/", headers=headers)
        print(f"GET Orders Status: {get_response.status_code}")
        
        # Test POST orders
        order_data = {
            "business": 1,  # Use existing business ID
            "order_number": "TEST-123",
            "customer_email": "test@example.com",
            "customer_name": "Test Customer",
            "product_service_name": "Test Product",
            "purchase_date": "2025-07-18T12:00:00Z"
        }
        
        post_response = requests.post(f"{base_url}/orders/", json=order_data, headers=headers)
        print(f"POST Orders Status: {post_response.status_code}")
        print(f"Response: {post_response.text[:1000]}")
        
    else:
        print(f"Login failed: {login_response.text}")
        
except Exception as e:
    print(f"Error: {e}")
