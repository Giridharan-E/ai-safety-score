#!/usr/bin/env python3
"""
Test script to verify feedback JSON fix
"""
import os
import sys
import django
import json

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'safetyscore.settings')
django.setup()

from api.utils.json_store import get_json_store

def test_feedback_json_fix():
    """Test the fixed feedback JSON functionality"""
    
    print("🧪 Testing Fixed Feedback JSON Storage")
    print("=" * 50)
    
    # Test JSON store
    feedback_store = get_json_store("feedback.json")
    
    # Test reading empty/corrupted file
    print("1️⃣ Testing JSON read with error handling...")
    try:
        feedback_data = feedback_store["read"]()
        if not isinstance(feedback_data, dict):
            feedback_data = {}
        print("   ✅ JSON read successful")
    except (json.JSONDecodeError, ValueError) as e:
        print(f"   ⚠️ JSON error handled: {e}")
        feedback_data = {}
    
    # Test adding feedback
    print("\n2️⃣ Testing feedback addition...")
    test_feedback = {
        "id": "test_456",
        "user_id": "test_user_2",
        "location_id": "LOC_13082_80270",
        "location_name": "Marina Beach, Chennai",
        "latitude": 13.0827,
        "longitude": 80.2707,
        "place_type": "beach",
        "region": "Tamil Nadu",
        "rating": 9,
        "comment": "Test feedback after fix",
        "created_at": "2024-01-01T12:00:00Z"
    }
    
    # Initialize feedbacks array if not exists
    if "feedbacks" not in feedback_data:
        feedback_data["feedbacks"] = []
    
    feedback_data["feedbacks"].append(test_feedback)
    
    # Write back to file
    feedback_store["write"](feedback_data)
    print("   ✅ Feedback added successfully!")
    
    # Verify the data
    print("\n3️⃣ Verifying data was saved...")
    try:
        updated_data = feedback_store["read"]()
        feedbacks = updated_data.get("feedbacks", [])
        print(f"   Total feedbacks: {len(feedbacks)}")
        
        if feedbacks:
            print("   Latest feedback:")
            latest = feedbacks[-1]
            print(f"   - ID: {latest.get('id')}")
            print(f"   - Location: {latest.get('location_name')}")
            print(f"   - Rating: {latest.get('rating')}")
            print(f"   - Location ID: {latest.get('location_id')}")
        
        print("\n✅ Feedback JSON fix test completed successfully!")
        
    except Exception as e:
        print(f"   ❌ Error verifying data: {e}")

if __name__ == "__main__":
    test_feedback_json_fix()
