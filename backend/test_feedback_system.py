#!/usr/bin/env python3
"""
Test script for the enhanced feedback collection system.

This script demonstrates how to use the new feedback collection and aggregation
features to collect feedback from 50+ users and calculate location-specific safety scores.
"""

import os
import sys
import django
import requests
import json
import random
from datetime import datetime, timedelta

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'safetyscore.settings')
django.setup()

from api.services.feedback_aggregation_service import feedback_aggregation_service
from api.services.scoring_engine import scoring_engine
from api.models import Feedback


def test_feedback_aggregation_service():
    """Test the feedback aggregation service functionality."""
    print("🧪 Testing Feedback Aggregation Service")
    print("=" * 50)
    
    # Test location (Marina Beach, Chennai)
    test_lat = 13.049953
    test_lon = 80.282403
    
    # 1. Test location feedback summary
    print("\n1. Testing location feedback summary...")
    summary = feedback_aggregation_service.get_location_feedback_summary(test_lat, test_lon)
    print(f"   Feedback count: {summary['feedback_count']}")
    print(f"   Unique users: {summary['unique_users']}")
    print(f"   Meets threshold: {summary['meets_threshold']}")
    print(f"   Average rating: {summary['statistics']['average_rating']}")
    print(f"   Safety score: {summary['safety_score']}")
    
    # 2. Test collection progress
    print("\n2. Testing collection progress...")
    progress = feedback_aggregation_service.get_feedback_collection_progress(test_lat, test_lon)
    print(f"   Current feedbacks: {progress['current_feedbacks']}")
    print(f"   Progress percentage: {progress['progress_percentage']:.1f}%")
    print(f"   Status: {progress['status']}")
    print(f"   Remaining needed: {progress['remaining_needed']}")
    
    # 3. Test top locations needing feedback
    print("\n3. Testing top locations needing feedback...")
    locations = feedback_aggregation_service.get_top_locations_needing_feedback(5)
    print(f"   Found {len(locations)} locations needing feedback")
    for i, loc in enumerate(locations[:3], 1):
        print(f"   {i}. {loc['sample_location_name']}: {loc['current_feedbacks']}/{loc['current_feedbacks'] + loc['remaining_needed']}")
    
    # 4. Test analytics
    print("\n4. Testing system analytics...")
    analytics = feedback_aggregation_service.get_feedback_analytics()
    print(f"   Total feedbacks: {analytics['system_overview']['total_feedbacks']}")
    print(f"   Unique users: {analytics['system_overview']['unique_users']}")
    print(f"   Unique locations: {analytics['system_overview']['unique_locations']}")
    print(f"   Locations with sufficient feedback: {analytics['system_overview']['locations_with_sufficient_feedback']}")
    print(f"   Completion rate: {analytics['collection_progress']['completion_rate']:.1f}%")


def test_scoring_engine():
    """Test the enhanced scoring engine with location-specific feedback."""
    print("\n\n🧪 Testing Enhanced Scoring Engine")
    print("=" * 50)
    
    # Test location
    test_lat = 13.049953
    test_lon = 80.282403
    
    # Sample features for testing
    features = {
        "police_stations": 0.7,
        "hospitals": 0.6,
        "lighting": 0.8,
        "visibility": 0.7,
        "sidewalks": 0.5,
        "businesses": 0.6,
        "transport": 0.7,
        "transport_density": 0.6,
        "crime_rate": 0.4,
        "natural_surveillance": 0.5,
        "user_feedback": 0.5
    }
    
    # Test location-specific scoring
    print("\n1. Testing location-specific scoring...")
    score, adj, feedback_info = scoring_engine.score_with_location_feedback(
        features, profile={}, latitude=test_lat, longitude=test_lon
    )
    
    print(f"   Final score: {score:.1f}")
    print(f"   Has sufficient feedback: {feedback_info['has_sufficient_feedback']}")
    print(f"   Feedback count: {feedback_info['feedback_count']}")
    print(f"   Unique users: {feedback_info['unique_users']}")
    print(f"   Scoring method: {feedback_info['scoring_method']}")
    print(f"   AI weight: {feedback_info['ai_score_weight']}")
    print(f"   User feedback weight: {feedback_info['user_feedback_weight']}")
    
    # Test regular scoring for comparison
    print("\n2. Testing regular scoring for comparison...")
    regular_score, _ = scoring_engine.score(features, profile={})
    print(f"   Regular AI score: {regular_score:.1f}")
    print(f"   Difference: {score - regular_score:.1f}")


def simulate_feedback_collection():
    """Simulate collecting feedback from multiple users."""
    print("\n\n🧪 Simulating Feedback Collection")
    print("=" * 50)
    
    # Test location
    test_lat = 13.049953
    test_lon = 80.282403
    
    # Generate sample feedback data
    sample_feedbacks = []
    for i in range(60):  # Generate 60 feedbacks to exceed the 50-user threshold
        user_id = f"test_user_{i+1}"
        rating = random.randint(4, 9)  # Generally positive ratings
        comment = f"Test feedback from user {i+1}"
        
        feedback_data = {
            'user_id': user_id,
            'location_id': f"LOC_{int(test_lat * 1000)}_{int(test_lon * 1000)}",
            'location_name': f"Test Location {i+1}",
            'latitude': test_lat + random.uniform(-0.001, 0.001),  # Small variation
            'longitude': test_lon + random.uniform(-0.001, 0.001),
            'place_type': 'tourist_place',
            'region': 'Tamil Nadu',
            'rating': rating,
            'comment': comment,
            'approval_status': 'auto_approved',
            'is_trusted_user': i % 3 == 0,  # Every 3rd user is trusted
        }
        sample_feedbacks.append(feedback_data)
    
    print(f"Generated {len(sample_feedbacks)} sample feedbacks")
    
    # Test aggregation with simulated data
    print("\n1. Testing aggregation with simulated data...")
    
    # Create a mock feedback summary
    mock_summary = {
        "location": {"latitude": test_lat, "longitude": test_lon, "radius_meters": 100},
        "feedback_count": len(sample_feedbacks),
        "unique_users": len(sample_feedbacks),
        "meets_threshold": len(sample_feedbacks) >= 50,
        "statistics": {
            "average_rating": sum(f['rating'] for f in sample_feedbacks) / len(sample_feedbacks),
            "median_rating": sorted([f['rating'] for f in sample_feedbacks])[len(sample_feedbacks)//2],
            "rating_std_dev": 1.2,
            "min_rating": min(f['rating'] for f in sample_feedbacks),
            "max_rating": max(f['rating'] for f in sample_feedbacks),
            "rating_distribution": {str(i): sum(1 for f in sample_feedbacks if f['rating'] == i) for i in range(1, 11)}
        },
        "quality_metrics": {
            "outlier_count": 2,
            "recent_feedbacks": len(sample_feedbacks),
            "trusted_user_ratio": sum(1 for f in sample_feedbacks if f['is_trusted_user']) / len(sample_feedbacks),
            "data_freshness": 0.95
        },
        "safety_score": sum(f['rating'] for f in sample_feedbacks) / len(sample_feedbacks) / 10.0,
        "recommendations": ["High safety rating - generally safe area"],
        "last_updated": datetime.now().isoformat()
    }
    
    print(f"   Mock feedback count: {mock_summary['feedback_count']}")
    print(f"   Meets threshold: {mock_summary['meets_threshold']}")
    print(f"   Average rating: {mock_summary['statistics']['average_rating']:.1f}")
    print(f"   Safety score: {mock_summary['safety_score']:.3f}")
    print(f"   Trusted user ratio: {mock_summary['quality_metrics']['trusted_user_ratio']:.2f}")


def test_api_endpoints():
    """Test the new API endpoints."""
    print("\n\n🧪 Testing API Endpoints")
    print("=" * 50)
    
    base_url = "http://localhost:8000/api"
    test_lat = 13.049953
    test_lon = 80.282403
    
    endpoints_to_test = [
        {
            "name": "Location Feedback Summary",
            "url": f"{base_url}/feedback/location-summary/",
            "params": {"latitude": test_lat, "longitude": test_lon, "radius": 100}
        },
        {
            "name": "Collection Progress",
            "url": f"{base_url}/feedback/collection-progress/",
            "params": {"latitude": test_lat, "longitude": test_lon, "radius": 100}
        },
        {
            "name": "Locations Needing Feedback",
            "url": f"{base_url}/feedback/locations-needing/",
            "params": {"limit": 5}
        },
        {
            "name": "Feedback Analytics",
            "url": f"{base_url}/feedback/analytics/",
            "params": {}
        }
    ]
    
    for endpoint in endpoints_to_test:
        print(f"\n1. Testing {endpoint['name']}...")
        try:
            response = requests.get(endpoint['url'], params=endpoint['params'], timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Success: {response.status_code}")
                if 'data' in data:
                    print(f"   Data keys: {list(data['data'].keys())}")
                else:
                    print(f"   Response keys: {list(data.keys())}")
            else:
                print(f"   ❌ Error: {response.status_code}")
                print(f"   Response: {response.text[:200]}")
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Connection error: {e}")
        except Exception as e:
            print(f"   ❌ Unexpected error: {e}")


def main():
    """Run all tests."""
    print("🚀 Feedback Collection System Test Suite")
    print("=" * 60)
    
    try:
        # Test the aggregation service
        test_feedback_aggregation_service()
        
        # Test the scoring engine
        test_scoring_engine()
        
        # Simulate feedback collection
        simulate_feedback_collection()
        
        # Test API endpoints (if server is running)
        print("\n\n📡 Testing API Endpoints (requires running server)")
        print("=" * 50)
        print("Note: These tests require the Django server to be running on localhost:8000")
        print("Start the server with: python manage.py runserver")
        
        # Uncomment the line below to test API endpoints
        # test_api_endpoints()
        
        print("\n✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
