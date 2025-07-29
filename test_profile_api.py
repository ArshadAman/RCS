#!/usr/bin/env python3
"""
Test script to check profile API functionality
"""
import requests
import json
import sys

def test_profile_api():
    base_url = "http://127.0.0.1:8000/api"
    
    # Test login first
    login_data = {
        "email": "admin@test.com",
        "password": "admin123"
    }
    
    print("Testing login...")
    login_response = requests.post(f"{base_url}/auth/login/", json=login_data)
    
    if login_response.status_code == 200:
        login_result = login_response.json()
        print("Login response:", json.dumps(login_result, indent=2))
        
        # Get access token
        access_token = None
        if 'tokens' in login_result and 'access' in login_result['tokens']:
            access_token = login_result['tokens']['access']
        elif 'access' in login_result:
            access_token = login_result['access']
        elif 'access_token' in login_result:
            access_token = login_result['access_token']
            
        if not access_token:
            print("❌ No access token found in login response")
            return
            
        print("✅ Login successful")
        
        # Test profile endpoint
        print("\nTesting profile endpoint...")
        headers = {"Authorization": f"Bearer {access_token}"}
        profile_response = requests.get(f"{base_url}/auth/profile/", headers=headers)
        
        if profile_response.status_code == 200:
            profile_data = profile_response.json()
            print("✅ Profile API successful")
            print("\n📋 Profile Data:")
            print(json.dumps(profile_data, indent=2))
        else:
            print(f"❌ Profile API failed: {profile_response.status_code}")
            print(profile_response.text)
    else:
        print(f"❌ Login failed: {login_response.status_code}")
        print(login_response.text)
    
    # Test plans endpoint (no auth required)
    print("\n\nTesting plans endpoint...")
    plans_response = requests.get(f"{base_url}/auth/plans/")
    if plans_response.status_code == 200:
        plans_data = plans_response.json()
        print("✅ Plans API successful")
        print("\n📋 Available Plans:")
        for plan_type, plan_info in plans_data.items():
            print(f"  {plan_type.upper()}: {plan_info['name']} - ${plan_info['price']}/{plan_info['billing_period']}")
    else:
        print(f"❌ Plans API failed: {plans_response.status_code}")

if __name__ == "__main__":
    test_profile_api()
