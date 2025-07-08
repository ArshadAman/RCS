#!/usr/bin/env python3
"""
Simple script to test the Review Collection System API endpoints
"""

import requests
import json

BASE_URL = "http://127.0.0.1:8001"

def test_api():
    print("Testing Review Collection System API...")
    print("=" * 50)
    
    # Test 1: Get categories (public endpoint)
    print("\n1. Testing categories endpoint...")
    response = requests.get(f"{BASE_URL}/api/categories/")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        if 'results' in data:
            categories = data['results']
        else:
            categories = data
        print(f"Found {len(categories)} categories")
        for i, cat in enumerate(categories):
            if i >= 3:  # Show first 3
                break
            print(f"  - {cat['name']}: {cat['description']}")
    
    # Test 2: Login with sample user
    print("\n2. Testing user login...")
    login_data = {
        "email": "john@example.com",
        "password": "user123"
    }
    response = requests.post(f"{BASE_URL}/api/auth/login/", json=login_data)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        tokens = response.json()
        access_token = tokens['tokens']['access']
        print("Login successful!")
        
        # Test 3: Get user profile
        print("\n3. Testing user profile...")
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(f"{BASE_URL}/api/auth/profile/", headers=headers)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            profile = response.json()
            print(f"User: {profile['full_name']} ({profile['email']})")
        
        # Test 4: Get businesses
        print("\n4. Testing businesses endpoint...")
        response = requests.get(f"{BASE_URL}/api/businesses/")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            businesses = response.json()
            if 'results' in businesses:
                businesses = businesses['results']
            print(f"Found {len(businesses)} businesses")
            for biz in businesses:
                print(f"  - {biz['name']} ({biz['category']}) - {biz['average_rating']}★")
        
        # Test 5: Get reviews
        print("\n5. Testing reviews endpoint...")
        response = requests.get(f"{BASE_URL}/api/reviews/")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            reviews = response.json()
            if 'results' in reviews:
                reviews = reviews['results']
            print(f"Found {len(reviews)} reviews")
            for i, review in enumerate(reviews):
                if i >= 3:  # Show first 3
                    break
                print(f"  - {review['rating']}★ {review['title']} by {review['reviewer_name']}")
    
    else:
        print("Login failed, skipping authenticated tests")
    
    print("\n" + "=" * 50)
    print("API testing completed!")

if __name__ == "__main__":
    try:
        test_api()
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the server.")
        print("Make sure the Django server is running on http://127.0.0.1:8001")
    except Exception as e:
        print(f"Error: {e}")
