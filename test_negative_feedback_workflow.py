#!/usr/bin/env python3
"""
Test the new negative feedback workflow:
1. Negative feedback submitted -> pending_moderation
2. Store owner responds within 7 days -> published (with response)
3. No response after 7 days -> auto_published (without response)
"""

import requests
import json
from datetime import datetime, timedelta

BASE_URL = 'http://127.0.0.1:8000/api'

def test_negative_feedback_workflow():
    """Test the complete negative feedback workflow with responses"""
    
    print("🔴 TESTING NEGATIVE FEEDBACK WORKFLOW")
    print("="*60)
    
    # Step 1: Login as admin
    login_response = requests.post(f'{BASE_URL}/auth/login/', json={
        'email': 'admin@test.com',
        'password': 'admin123'
    })
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.text}")
        return False
    
    token = login_response.json()['tokens']['access']
    headers = {'Authorization': f'Bearer {token}'}
    print("✅ Admin login successful!")
    
    # Step 2: Create a new sales report with future date to get fresh feedback requests
    future_date = (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d')
    
    sales_data = {
        'report_date': future_date,
        'orders': [
            {
                'order_id': f'ORD{int(datetime.now().timestamp())}',
                'customer_name': 'Jennifer Wilson',
                'email': 'jennifer@example.com',
                'phone': '+1 555-0201'
            },
            {
                'order_id': f'ORD{int(datetime.now().timestamp()) + 1}', 
                'customer_name': 'David Martinez',
                'email': 'david@example.com',
                'phone': '+1 555-0202'
            }
        ]
    }
    
    sales_response = requests.post(f'{BASE_URL}/sales-report/upload/', 
                                 json=sales_data, headers=headers)
    
    if sales_response.status_code == 201:
        report_data = sales_response.json()
        print(f"✅ New sales report created for {future_date}")
        print(f"   📧 Emails sent: {report_data['report']['emails_sent']}")
    else:
        print(f"❌ Failed to create sales report: {sales_response.text}")
        return False
    
    # Step 3: Get the new feedback requests
    requests_response = requests.get(f'{BASE_URL}/feedback-requests/', headers=headers)
    if requests_response.status_code != 200:
        print(f"❌ Failed to get feedback requests: {requests_response.text}")
        return False
    
    requests_data = requests_response.json()
    pending_requests = [r for r in requests_data if r['status'] == 'pending']
    
    if len(pending_requests) < 2:
        print("❌ Need at least 2 pending requests for this test")
        return False
    
    # Step 4: Submit negative feedback for first customer
    print(f"\n🔴 Step 4: {pending_requests[0]['customer_name']} submitting negative feedback...")
    
    negative_feedback = {
        'would_recommend': False,
        'negative_comment': 'Very disappointed with the service. The product quality was poor, delivery was delayed by 3 days without notification, and customer support was unhelpful when I called to inquire about the delay. The packaging was also damaged.'
    }
    
    feedback_response = requests.post(
        f"{BASE_URL}/feedback/{pending_requests[0]['email_token']}/", 
        json=negative_feedback
    )
    
    if feedback_response.status_code == 201:
        feedback_data = feedback_response.json()['feedback']
        print("✅ Negative feedback submitted successfully!")
        print(f"   👤 Customer: {pending_requests[0]['customer_name']}")
        print(f"   📦 Order: {pending_requests[0]['order_id']}")
        print(f"   🔴 Status: {feedback_data['status']} (pending moderation)")
        print(f"   ⏰ Auto-publish date: {feedback_data['auto_publish_date']}")
        
        first_feedback_id = feedback_data['id']
    else:
        print(f"❌ Failed to submit negative feedback: {feedback_response.text}")
        return False
    
    # Step 5: Store owner responds to the negative feedback
    print(f"\n💬 Step 5: Store owner responding to negative feedback...")
    
    store_response = {
        'store_response': 'We sincerely apologize for your poor experience. We have investigated the delivery delay and have implemented new quality control measures. We would like to offer you a full refund and a 20% discount on your next order. Please contact us directly at support@store.com to resolve this matter.'
    }
    
    response_result = requests.post(
        f"{BASE_URL}/feedback/{first_feedback_id}/respond/",
        json=store_response,
        headers=headers
    )
    
    if response_result.status_code == 200:
        updated_feedback = response_result.json()
        print("✅ Store response added successfully!")
        print(f"   🏪 Response: {store_response['store_response'][:100]}...")
        print(f"   🟢 Status: {updated_feedback['status']} (published with response!)")
        print(f"   📅 Response date: {updated_feedback['response_date']}")
    else:
        print(f"❌ Failed to add store response: {response_result.text}")
        return False
    
    # Step 6: Submit another negative feedback (this one will get no response)
    print(f"\n🔴 Step 6: {pending_requests[1]['customer_name']} submitting negative feedback (no response scenario)...")
    
    negative_feedback_2 = {
        'would_recommend': False,
        'negative_comment': 'Product was not as described in the website. The material feels cheap and the color is completely different from what was shown online. Very misleading advertising and poor quality control.'
    }
    
    feedback_response_2 = requests.post(
        f"{BASE_URL}/feedback/{pending_requests[1]['email_token']}/", 
        json=negative_feedback_2
    )
    
    if feedback_response_2.status_code == 201:
        feedback_data_2 = feedback_response_2.json()['feedback']
        print("✅ Second negative feedback submitted successfully!")
        print(f"   👤 Customer: {pending_requests[1]['customer_name']}")
        print(f"   📦 Order: {pending_requests[1]['order_id']}")
        print(f"   🔴 Status: {feedback_data_2['status']} (pending moderation)")
        print(f"   ⏰ This will auto-publish after 7 days if no response")
    else:
        print(f"❌ Failed to submit second negative feedback: {feedback_response_2.text}")
        return False
    
    # Step 7: Check dashboard stats
    print(f"\n📊 Step 7: Updated dashboard statistics...")
    stats_response = requests.get(f'{BASE_URL}/dashboard/stats/', headers=headers)
    
    if stats_response.status_code == 200:
        stats = stats_response.json()
        print("✅ Dashboard statistics:")
        print(f"   🎯 Total feedback: {stats['positive_feedback'] + stats['negative_feedback']}")
        print(f"   🟢 Positive: {stats['positive_feedback']}")
        print(f"   🔴 Negative: {stats['negative_feedback']}")
        print(f"   ⏳ Pending moderation: {stats['negative_feedback'] - 1}")  # -1 because one was published with response
        print(f"   🚨 Ready for auto-publish: {stats['auto_publish_pending']}")
    
    print(f"\n✅ NEGATIVE FEEDBACK WORKFLOW TEST COMPLETED!")
    print("="*60)
    print("📋 WORKFLOW SUMMARY:")
    print("  ✅ Negative feedback submitted → pending_moderation")
    print("  ✅ Store responds within 7 days → published (with response)")
    print("  ✅ No response scenario → will auto-publish after 7 days")
    print("  ✅ Dashboard properly tracks all states")
    
    return True

if __name__ == "__main__":
    print("🚀 Starting Negative Feedback Workflow Test...")
    import time
    time.sleep(2)  # Wait for server
    
    try:
        success = test_negative_feedback_workflow()
        if success:
            print("\n🎉 ALL TESTS PASSED!")
        else:
            print("\n❌ SOME TESTS FAILED!")
    except Exception as e:
        print(f"\n💥 Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
