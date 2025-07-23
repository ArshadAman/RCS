#!/usr/bin/env python
"""
Test script for the new registration flow with business information and plan selection
"""
import os
import sys
import django
import json
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'review_collection_system.settings')
django.setup()

from django.test import Client
from django.urls import reverse
from authentication.models import User
from reviews.models import Company, Plan

def test_registration_flow():
    """Test the new registration flow"""
    client = Client()
    
    # Registration data matching the new requirements
    registration_data = {
        'username': f'testuser_{int(datetime.now().timestamp())}',
        'email': f'test_{int(datetime.now().timestamp())}@example.com',
        'password': 'testpass123',
        'password_confirm': 'testpass123',
        'first_name': 'John',
        'last_name': 'Doe',
        'phone_number': '+1234567890',
        'business_name': f'Test Business {int(datetime.now().timestamp())}',
        'website_url': 'https://testbusiness.com',
        'contact_number': '+1987654321',
        'country': 'United States',
        'plan_type': 'basic'
    }
    
    print("🧪 Testing New Registration Flow")
    print("=" * 50)
    print(f"📝 Registration Data:")
    for key, value in registration_data.items():
        if key == 'password':
            print(f"  {key}: [HIDDEN]")
        else:
            print(f"  {key}: {value}")
    
    # Test the registration endpoint
    try:
        response = client.post(
            '/api/auth/register/',
            data=json.dumps(registration_data),
            content_type='application/json'
        )
        
        print(f"\n📡 Response Status: {response.status_code}")
        
        if response.status_code == 201:
            response_data = response.json()
            print("✅ Registration successful!")
            print(f"📄 Response:")
            print(json.dumps(response_data, indent=2))
            
            # Verify user creation
            user = User.objects.get(email=registration_data['email'])
            print(f"👤 User created: {user.username} ({user.email})")
            
            # Verify company creation
            company = Company.objects.get(owner=user)
            print(f"🏢 Company created: {company.name}")
            print(f"   - Website: {company.website}")
            print(f"   - Phone: {company.phone_number}")
            print(f"   - Country: {company.country}")
            
            # Verify plan creation
            plan = Plan.objects.get(company=company)
            print(f"📋 Plan created: {plan.get_plan_type_display()}")
            print(f"   - Review Limit: {plan.review_limit}")
            
            return True
            
        else:
            print("❌ Registration failed!")
            try:
                error_data = response.json()
                print(f"📄 Error Response:")
                print(json.dumps(error_data, indent=2))
            except:
                print(f"Raw Response: {response.content}")
            return False
            
    except Exception as e:
        print(f"❌ Exception during test: {str(e)}")
        return False

def test_plan_types():
    """Test different plan types"""
    print("\n🔄 Testing Different Plan Types")
    print("=" * 50)
    
    plan_tests = [
        ('basic', 50),
        ('standard', 150),
        ('premium', 400)
    ]
    
    for plan_type, expected_limit in plan_tests:
        client = Client()
        timestamp = int(datetime.now().timestamp())
        
        registration_data = {
            'username': f'plantest_{plan_type}_{timestamp}',
            'email': f'plantest_{plan_type}_{timestamp}@example.com',
            'password': 'testpass123',
            'password_confirm': 'testpass123',
            'first_name': 'Plan',
            'last_name': 'Tester',
            'phone_number': '+1111111111',
            'business_name': f'Plan Test {plan_type.title()} {timestamp}',
            'website_url': f'https://{plan_type}test.com',
            'contact_number': '+2222222222',
            'country': 'Canada',
            'plan_type': plan_type
        }
        
        response = client.post(
            '/api/auth/register/',
            data=json.dumps(registration_data),
            content_type='application/json'
        )
        
        if response.status_code == 201:
            user = User.objects.get(email=registration_data['email'])
            company = Company.objects.get(owner=user)
            plan = Plan.objects.get(company=company)
            
            if plan.plan_type == plan_type and plan.review_limit == expected_limit:
                print(f"✅ {plan_type.title()} Plan: {plan.review_limit} reviews")
            else:
                print(f"❌ {plan_type.title()} Plan: Expected {expected_limit}, got {plan.review_limit}")
        else:
            print(f"❌ {plan_type.title()} Plan: Registration failed")

if __name__ == '__main__':
    print("🚀 Starting Registration Flow Tests")
    print("=" * 50)
    
    # Test basic registration
    success = test_registration_flow()
    
    if success:
        # Test different plan types
        test_plan_types()
        print("\n🎉 All tests completed!")
    else:
        print("\n❌ Basic registration test failed, skipping plan tests")
