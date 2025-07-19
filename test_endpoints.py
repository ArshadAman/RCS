#!/usr/bin/env python3
"""
Comprehensive API endpoint testing script for Review Collection System
Tests all endpoints including authentication, companies, businesses, orders, reviews, and payments
"""

import requests
import json
from datetime import datetime
import uuid

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api"

class APITester:
    def __init__(self):
        self.access_token = None
        self.refresh_token = None
        self.user_id = None
        self.company_id = None
        self.business_id = None
        self.order_id = None
        self.review_id = None
        self.headers = {'Content-Type': 'application/json'}
        
    def log(self, message, status="INFO"):
        print(f"[{status}] {message}")
        
    def test_endpoint(self, method, endpoint, data=None, expected_status=200, description=""):
        """Generic endpoint tester"""
        url = f"{API_BASE}{endpoint}"
        
        self.log(f"Testing {method} {endpoint} - {description}")
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=self.headers)
            elif method.upper() == 'POST':
                response = requests.post(url, json=data, headers=self.headers)
            elif method.upper() == 'PUT':
                response = requests.put(url, json=data, headers=self.headers)
            elif method.upper() == 'PATCH':
                response = requests.patch(url, json=data, headers=self.headers)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=self.headers)
            
            self.log(f"Response Status: {response.status_code}")
            
            if response.status_code == expected_status:
                self.log("✅ Test PASSED", "SUCCESS")
                return response.json() if response.content else None
            else:
                self.log(f"❌ Test FAILED - Expected {expected_status}, got {response.status_code}", "ERROR")
                if response.content:
                    self.log(f"Response: {response.text}")
                return None
                
        except Exception as e:
            self.log(f"❌ Test ERROR: {str(e)}", "ERROR")
            return None
    
    def register_user(self):
        """Test user registration"""
        user_data = {
            "username": f"testuser_{uuid.uuid4().hex[:8]}",
            "email": f"test_{uuid.uuid4().hex[:8]}@example.com",
            "password": "testpass123",
            "password_confirm": "testpass123",
            "first_name": "Test",
            "last_name": "User"
        }
        
        result = self.test_endpoint(
            "POST", "/auth/register/", 
            user_data, 
            201, 
            "User Registration"
        )
        
        if result:
            self.user_id = result.get('user', {}).get('id')
            return user_data
        return None
    
    def login_user(self, user_data):
        """Test user login"""
        login_data = {
            "username": user_data["username"],
            "password": user_data["password"]
        }
        
        result = self.test_endpoint(
            "POST", "/auth/login/", 
            login_data, 
            200, 
            "User Login"
        )
        
        if result:
            self.access_token = result.get('access')
            self.refresh_token = result.get('refresh')
            self.headers['Authorization'] = f'Bearer {self.access_token}'
            return True
        return False
    
    def test_authentication_endpoints(self):
        """Test all authentication endpoints"""
        self.log("=== TESTING AUTHENTICATION ENDPOINTS ===", "INFO")
        
        # Register user
        user_data = self.register_user()
        if not user_data:
            self.log("❌ Registration failed, skipping auth tests", "ERROR")
            return False
            
        # Login user
        if not self.login_user(user_data):
            self.log("❌ Login failed, skipping auth tests", "ERROR")
            return False
            
        # Test token refresh
        if self.refresh_token:
            refresh_result = self.test_endpoint(
                "POST", "/auth/token/refresh/",
                {"refresh": self.refresh_token},
                200,
                "Token Refresh"
            )
            
            if refresh_result:
                new_access = refresh_result.get('access')
                if new_access:
                    self.access_token = new_access
                    self.headers['Authorization'] = f'Bearer {self.access_token}'
        
        # Test user profile
        self.test_endpoint("GET", "/auth/profile/", None, 200, "Get User Profile")
        
        return True
    
    def test_company_endpoints(self):
        """Test company management endpoints"""
        self.log("=== TESTING COMPANY ENDPOINTS ===", "INFO")
        
        # Create company
        company_data = {
            "name": f"Test Company {uuid.uuid4().hex[:8]}",
            "website": "https://testcompany.com",
            "email": "info@testcompany.com",
            "phone_number": "+1234567890"
        }
        
        result = self.test_endpoint(
            "POST", "/companies/",
            company_data,
            201,
            "Create Company"
        )
        
        if result:
            self.company_id = result.get('id')
            
            # Test company list
            self.test_endpoint("GET", "/companies/", None, 200, "List Companies")
            
            # Test company detail
            self.test_endpoint("GET", f"/companies/{self.company_id}/", None, 200, "Get Company Detail")
            
            # Test company dashboard stats
            self.test_endpoint("GET", f"/companies/{self.company_id}/dashboard_stats/", None, 200, "Company Dashboard Stats")
            
            # Update company
            update_data = {"website": "https://updated-testcompany.com"}
            self.test_endpoint("PATCH", f"/companies/{self.company_id}/", update_data, 200, "Update Company")
            
            return True
        return False
    
    def test_business_endpoints(self):
        """Test business management endpoints"""
        self.log("=== TESTING BUSINESS ENDPOINTS ===", "INFO")
        
        if not self.company_id:
            self.log("❌ No company ID available, skipping business tests", "ERROR")
            return False
            
        # Create business
        business_data = {
            "name": f"Test Business {uuid.uuid4().hex[:8]}",
            "company": self.company_id,
            "description": "A test business for API testing",
            "category": "Technology",
            "address": "123 Test Street, Test City, TC 12345",
            "phone_number": "+1234567890",
            "email": "business@testcompany.com"
        }
        
        result = self.test_endpoint(
            "POST", "/businesses/",
            business_data,
            201,
            "Create Business"
        )
        
        if result:
            self.business_id = result.get('id')
            
            # Test business list
            self.test_endpoint("GET", "/businesses/", None, 200, "List Businesses")
            
            # Test business detail
            self.test_endpoint("GET", f"/businesses/{self.business_id}/", None, 200, "Get Business Detail")
            
            # Test business reviews
            self.test_endpoint("GET", f"/businesses/{self.business_id}/reviews/", None, 200, "Get Business Reviews")
            
            # Test public reviews
            self.test_endpoint("GET", f"/businesses/{self.business_id}/public_reviews/", None, 200, "Get Public Reviews")
            
            return True
        return False
    
    def test_order_endpoints(self):
        """Test order management endpoints"""
        self.log("=== TESTING ORDER ENDPOINTS ===", "INFO")
        
        if not self.business_id:
            self.log("❌ No business ID available, skipping order tests", "ERROR")
            return False
            
        # Create order
        order_data = {
            "business": self.business_id,
            "order_number": f"ORD-{uuid.uuid4().hex[:8]}",
            "customer_email": "customer@example.com",
            "customer_name": "John Doe",
            "product_service_name": "Test Product",
            "purchase_date": datetime.now().isoformat()
        }
        
        result = self.test_endpoint(
            "POST", "/orders/",
            order_data,
            201,
            "Create Order"
        )
        
        if result:
            self.order_id = result.get('id')
            
            # Test order list
            self.test_endpoint("GET", "/orders/", None, 200, "List Orders")
            
            # Test order detail
            self.test_endpoint("GET", f"/orders/{self.order_id}/", None, 200, "Get Order Detail")
            
            # Test send review request
            self.test_endpoint("POST", f"/orders/{self.order_id}/send_review_request/", {}, 200, "Send Review Request")
            
            return True
        return False
    
    def test_review_endpoints(self):
        """Test review management endpoints"""
        self.log("=== TESTING REVIEW ENDPOINTS ===", "INFO")
        
        # Test review list
        self.test_endpoint("GET", "/reviews/", None, 200, "List Reviews")
        
        # Test review criteria
        self.test_endpoint("GET", "/review-criteria/", None, 200, "List Review Criteria")
        
        if self.company_id:
            # Create review criteria
            criteria_data = {
                "company": self.company_id,
                "name": "Service Quality",
                "is_active": True,
                "order": 1
            }
            
            self.test_endpoint(
                "POST", "/review-criteria/",
                criteria_data,
                201,
                "Create Review Criteria"
            )
    
    def test_payment_endpoints(self):
        """Test payment and plan management endpoints"""
        self.log("=== TESTING PAYMENT ENDPOINTS ===", "INFO")
        
        # Test pricing endpoint
        self.test_endpoint("GET", "/payments/pricing/", None, 200, "Get Plan Pricing")
        
        # Test company plan
        if self.company_id:
            self.test_endpoint("GET", f"/payments/company_plan/?company_id={self.company_id}", None, 200, "Get Company Plan")
        
        # Test payment list
        self.test_endpoint("GET", "/payments/", None, 200, "List Payments")
    
    def test_public_endpoints(self):
        """Test public API endpoints (no auth required)"""
        self.log("=== TESTING PUBLIC ENDPOINTS ===", "INFO")
        
        # Temporarily remove auth header for public endpoints
        original_headers = self.headers.copy()
        self.headers = {'Content-Type': 'application/json'}
        
        # Test categories
        self.test_endpoint("GET", "/categories/", None, 200, "List Categories")
        
        # Test widget data (requires company unique_id)
        # We'll use a placeholder since we need actual data
        # self.test_endpoint("GET", "/widget-data/test-company-id/", None, 200, "Get Widget Data")
        
        # Restore auth headers
        self.headers = original_headers
    
    def test_admin_endpoints(self):
        """Test admin-specific endpoints"""
        self.log("=== TESTING ADMIN/MANAGEMENT ENDPOINTS ===", "INFO")
        
        # Test bulk operations (requires review IDs)
        # self.test_endpoint("POST", "/bulk-approve-reviews/", {"review_ids": []}, 200, "Bulk Approve Reviews")
        
        # Test email templates
        self.test_endpoint("GET", "/email-templates/", None, 200, "List Email Templates")
        
        # Test widget settings
        self.test_endpoint("GET", "/widget-settings/", None, 200, "List Widget Settings")
        
        # Test QR feedback
        self.test_endpoint("GET", "/qr-feedback/", None, 200, "List QR Feedback")
    
    def run_all_tests(self):
        """Run comprehensive test suite"""
        self.log("🚀 STARTING COMPREHENSIVE API ENDPOINT TESTING", "INFO")
        self.log("=" * 60, "INFO")
        
        # Test authentication first
        if not self.test_authentication_endpoints():
            self.log("❌ Authentication tests failed, stopping", "ERROR")
            return
        
        # Test core endpoints
        self.test_company_endpoints()
        self.test_business_endpoints() 
        self.test_order_endpoints()
        self.test_review_endpoints()
        self.test_payment_endpoints()
        self.test_public_endpoints()
        self.test_admin_endpoints()
        
        self.log("=" * 60, "INFO")
        self.log("🎉 API ENDPOINT TESTING COMPLETED", "INFO")

if __name__ == "__main__":
    tester = APITester()
    tester.run_all_tests()
