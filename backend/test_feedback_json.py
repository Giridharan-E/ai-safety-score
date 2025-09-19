#!/usr/bin/env python3
"""
Test script to verify feedback JSON functionality
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

def test_feedback_json():
    """Test the feedback JSON storage functionality"""
    
    print("🧪 Testing Feedback JSON Storage")
    print("=" * 50)
    
    # Test JSON store
    feedback_store = get_json_store("feedback.json")
    
    # Read current data
    print("1️⃣ Reading current feedback data...")
    current_data = feedback_store["read"]()
    print(f"   Current data: {json.dumps(current_data, indent=2)}")
    
    # Add a test feedback
    print("\n2️⃣ Adding test feedback...")
    test_feedback = {
        "id": "test_123",
        "user_id": "test_user",
        "location_id": "TEST_LOC_001",
        "location_name": "Test Location",
        "latitude": 13.0827,
        "longitude": 80.2707,
        "place_type": "test_place",
        "region": "Tamil Nadu",
        "rating": 8,
        "comment": "Test feedback from script",
        "created_at": "2024-01-01T12:00:00Z"
    }
    
    # Initialize feedbacks array if not exists
    if "feedbacks" not in current_data:
        current_data["feedbacks"] = []
    
    # Add test feedback
    current_data["feedbacks"].append(test_feedback)
    
    # Write back to file
    feedback_store["write"](current_data)
    print("   ✅ Test feedback added successfully!")
    
    # Read back to verify
    print("\n3️⃣ Verifying data was saved...")
    updated_data = feedback_store["read"]()
    feedbacks = updated_data.get("feedbacks", [])
    print(f"   Total feedbacks: {len(feedbacks)}")
    
    if feedbacks:
        print("   Latest feedback:")
        latest = feedbacks[-1]
        print(f"   - ID: {latest.get('id')}")
        print(f"   - Location: {latest.get('location_name')}")
        print(f"   - Rating: {latest.get('rating')}")
        print(f"   - Coordinates: ({latest.get('latitude')}, {latest.get('longitude')})")
    
    print("\n✅ Feedback JSON storage test completed!")

if __name__ == "__main__":
    test_feedback_json()
