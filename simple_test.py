#!/usr/bin/env python3
"""
Simple API endpoint testing script
"""

import requests
import json
import uuid

BASE_URL = "http://localhost:8000/api"

def test_endpoint(method, endpoint, data=None, headers=None):
    """Test a single endpoint"""
    url = f"{BASE_URL}{endpoint}"
    print(f"\n🔍 Testing {method} {endpoint}")
    
    if headers is None:
        headers = {'Content-Type': 'application/json'}
    
    try:
        if method.upper() == 'GET':
            response = requests.get(url, headers=headers)
        elif method.upper() == 'POST':
            response = requests.post(url, json=data, headers=headers)
        elif method.upper() == 'PUT':
            response = requests.put(url, json=data, headers=headers)
        elif method.upper() == 'PATCH':
            response = requests.patch(url, json=data, headers=headers)
        elif method.upper() == 'DELETE':
            response = requests.delete(url, headers=headers)
        
        print(f"Status Code: {response.status_code}")
        
        if response.content:
            try:
                json_response = response.json()
                print(f"Response: {json.dumps(json_response, indent=2)[:500]}...")
                return json_response
            except:
                print(f"Response: {response.text[:500]}...")
                return response.text
        else:
            print("Empty response")
            return None
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

def main():
    print("🚀 Starting API endpoint tests")
    
    # Test authentication endpoints
    print("\n" + "="*50)
    print("TESTING AUTHENTICATION")
    print("="*50)
    
    # 1. Test user registration
    user_data = {
        "username": f"testuser_{uuid.uuid4().hex[:8]}",
        "email": f"test_{uuid.uuid4().hex[:8]}@example.com",
        "password": "testpass123",
        "password_confirm": "testpass123",
        "first_name": "Test",
        "last_name": "User"
    }
    
    register_result = test_endpoint("POST", "/auth/register/", user_data)
    
    if register_result and 'tokens' in register_result:
        print("✅ Registration successful!")
        
        # 2. Test login
        login_data = {
            "email": user_data["email"],  # Use email instead of username
            "password": user_data["password"]
        }
        
        login_result = test_endpoint("POST", "/auth/login/", login_data)
        
        if login_result and 'tokens' in login_result and 'access' in login_result['tokens']:
            access_token = login_result['tokens']['access']
            auth_headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {access_token}'
            }
            print("✅ Login successful!")
            
            # Test authenticated endpoints
            print("\n" + "="*50)
            print("TESTING CORE ENDPOINTS")
            print("="*50)
            
            # 3. Test companies endpoint
            test_endpoint("GET", "/companies/", headers=auth_headers)
            
            # 4. Create a company
            company_data = {
                "name": f"Test Company {uuid.uuid4().hex[:8]}",
                "website": "https://testcompany.com",
                "email": "info@testcompany.com"
            }
            company_result = test_endpoint("POST", "/companies/", company_data, auth_headers)
            
            if company_result and 'id' in company_result:
                company_id = company_result['id']
                print(f"✅ Company created with ID: {company_id}")
                
                # 5. Test businesses endpoint
                test_endpoint("GET", "/businesses/", headers=auth_headers)
                
                # 6. Create a business
                business_data = {
                    "name": f"Test Business {uuid.uuid4().hex[:8]}",
                    "company": company_id,
                    "description": "A test business",
                    "category": "Technology",
                    "address": "123 Test Street"
                }
                business_result = test_endpoint("POST", "/businesses/", business_data, auth_headers)
                
                if business_result and 'id' in business_result:
                    business_id = business_result['id']
                    print(f"✅ Business created with ID: {business_id}")
                    
                    # 7. Test orders endpoint
                    test_endpoint("GET", "/orders/", headers=auth_headers)
                    
                    # 8. Create an order
                    order_data = {
                        "business": business_id,
                        "order_number": f"ORD-{uuid.uuid4().hex[:8]}",
                        "customer_email": "customer@example.com",
                        "customer_name": "John Doe",
                        "product_service_name": "Test Product",
                        "purchase_date": "2025-07-18T12:00:00Z"
                    }
                    order_result = test_endpoint("POST", "/orders/", order_data, auth_headers)
                    
                    if order_result and isinstance(order_result, dict) and 'id' in order_result:
                        print(f"✅ Order created with ID: {order_result['id']}")
                        
                        # 9. Test reviews endpoint
                        test_endpoint("GET", "/reviews/", headers=auth_headers)
                        
                        # 10. Test payment endpoints
                        test_endpoint("GET", "/payments/pricing/", headers=auth_headers)
                        test_endpoint("GET", "/payments/", headers=auth_headers)
                        
                        # 11. Test company plan
                        test_endpoint("GET", f"/payments/company_plan/?company_id={company_id}", headers=auth_headers)
                    else:
                        print("❌ Order creation failed, but continuing with other tests...")
                        
                        # Still test other endpoints even if order creation failed
                        test_endpoint("GET", "/reviews/", headers=auth_headers)
                        test_endpoint("GET", "/payments/pricing/", headers=auth_headers)
                        test_endpoint("GET", "/payments/", headers=auth_headers)
                        test_endpoint("GET", f"/payments/company_plan/?company_id={company_id}", headers=auth_headers)
            
            # Test public endpoints
            print("\n" + "="*50)
            print("TESTING PUBLIC ENDPOINTS")
            print("="*50)
            
            # 12. Test categories (public)
            test_endpoint("GET", "/categories/")
            
            # 13. Test QR feedback (public)
            test_endpoint("GET", "/qr-feedback/", headers=auth_headers)
            
            # 14. Test review criteria
            test_endpoint("GET", "/review-criteria/", headers=auth_headers)
            
            # 15. Test email templates
            test_endpoint("GET", "/email-templates/", headers=auth_headers)
            
            # 16. Test widget settings
            test_endpoint("GET", "/widget-settings/", headers=auth_headers)
            
        else:
            print("❌ Login failed")
    else:
        print("❌ Registration failed")
    
    print("\n🎉 Testing completed!")

if __name__ == "__main__":
    main()
