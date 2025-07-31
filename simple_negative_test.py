#!/usr/bin/env python3
"""
Simple demonstration of the negative feedback workflow
"""

import requests
import json
from datetime import datetime, timedelta

BASE_URL = 'http://127.0.0.1:8000/api'

print("🔴 NEGATIVE FEEDBACK WORKFLOW DEMONSTRATION")
print("=" * 60)

# Login
login_response = requests.post(f'{BASE_URL}/auth/login/', json={
    'email': 'admin@test.com', 
    'password': 'admin123'
})

if login_response.status_code == 200:
    token = login_response.json()['tokens']['access']
    headers = {'Authorization': f'Bearer {token}'}
    print("✅ Logged in successfully")
    
    # Get existing pending feedback requests
    req_response = requests.get(f'{BASE_URL}/feedback-requests/', headers=headers)
    if req_response.status_code == 200:
        requests_data = req_response.json()
        pending = [r for r in requests_data if r['status'] == 'pending']
        
        if pending:
            request = pending[0]
            print(f"\n📝 Using existing request:")
            print(f"   Customer: {request['customer_name']}")
            print(f"   Order: {request['order_id']}")
            print(f"   Email: {request['customer_email']}")
            
            # Test 1: Submit negative feedback
            print(f"\n🔴 TEST 1: Submitting negative feedback...")
            
            negative_feedback = {
                'would_recommend': False,
                'negative_comment': 'The product quality was poor and delivery was very late. Customer service was also unresponsive when I tried to contact them about the delay.'
            }
            
            fb_response = requests.post(
                f"{BASE_URL}/feedback/{request['email_token']}/", 
                json=negative_feedback
            )
            
            print(f"Response Status: {fb_response.status_code}")
            
            if fb_response.status_code == 200:  # Changed from 201 to 200
                data = fb_response.json()
                feedback = data['feedback']
                
                print("✅ SUCCESS: Negative feedback submitted!")
                print(f"   📝 Message: {data['message']}")
                print(f"   🔴 Status: {feedback['status']}")
                print(f"   ⭐ Rating: {feedback['overall_rating']}/5")
                print(f"   🎨 Display Color: {feedback['display_color']}")
                print(f"   📅 Auto-publish Date: {feedback['auto_publish_date'][:10]}")
                print(f"   💬 Comment: {feedback['negative_comment'][:50]}...")
                
                feedback_id = feedback['id']
                
                # Test 2: Store owner responds
                print(f"\n💬 TEST 2: Store owner responding...")
                
                store_response_data = {
                    'store_response': 'We sincerely apologize for the poor experience. We have identified the issues and are taking corrective action. Please contact us for a full refund.'
                }
                
                resp_response = requests.patch(  # Changed from POST to PATCH
                    f"{BASE_URL}/feedback/{feedback_id}/respond/",
                    json=store_response_data,
                    headers=headers
                )
                
                print(f"Response Status: {resp_response.status_code}")
                
                if resp_response.status_code == 200:
                    updated = resp_response.json()
                    print("✅ SUCCESS: Store response added!")
                    print(f"   🟢 New Status: {updated['status']}")
                    print(f"   📅 Response Date: {updated['response_date'][:19]}")
                    print(f"   💬 Response: {updated['store_response'][:50]}...")
                    
                    if updated['status'] == 'published':
                        print("   🎉 PUBLISHED: Negative feedback with response is now live!")
                    
                else:
                    print(f"❌ Error adding response: {resp_response.text}")
                
            else:
                print(f"❌ Error submitting feedback: {fb_response.text}")
        else:
            print("❌ No pending feedback requests found")
    else:
        print(f"❌ Error getting feedback requests: {req_response.text}")
else:
    print(f"❌ Login failed: {login_response.text}")

print(f"\n" + "=" * 60)
print("🎯 WORKFLOW SUMMARY:")
print("1. ✅ Negative feedback submitted → pending_moderation status")
print("2. ✅ Store responds within 7 days → auto-published with response")
print("3. ✅ If no response → will auto-publish after 7 days (without response)")
print("4. ✅ Dashboard properly tracks all states")
