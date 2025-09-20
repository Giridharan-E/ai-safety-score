#!/usr/bin/env python3
"""
Example usage of the enhanced feedback collection system.

This script demonstrates how to:
1. Check feedback collection progress for a location
2. Submit feedback from multiple users
3. Monitor progress towards the 50-user threshold
4. Get location-specific safety scores
"""

import requests
import json
import time
import random

# Configuration
BASE_URL = "http://localhost:8000/api"
TEST_LOCATION = {
    "latitude": 13.049953,  # Marina Beach, Chennai
    "longitude": 80.282403,
    "name": "Marina Beach, Chennai"
}


def check_feedback_progress(lat, lon):
    """Check the current feedback collection progress for a location."""
    print(f"📊 Checking feedback progress for {TEST_LOCATION['name']}...")
    
    try:
        response = requests.get(
            f"{BASE_URL}/feedback/collection-progress/",
            params={
                "latitude": lat,
                "longitude": lon,
                "radius": 100
            }
        )
        
        if response.status_code == 200:
            data = response.json()["data"]
            print(f"   Current feedbacks: {data['current_feedbacks']}")
            print(f"   Unique users: {data['unique_users']}")
            print(f"   Progress: {data['progress_percentage']:.1f}%")
            print(f"   Status: {data['status']}")
            print(f"   Remaining needed: {data['remaining_needed']}")
            
            if data['status'] == 'complete':
                print("   ✅ Location has sufficient feedback for enhanced scoring!")
            else:
                print(f"   ⏳ Need {data['remaining_needed']} more feedbacks to reach threshold")
                
            return data
        else:
            print(f"   ❌ Error: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"   ❌ Error checking progress: {e}")
        return None


def submit_feedback(lat, lon, user_id, rating, comment=""):
    """Submit feedback for a location."""
    print(f"📝 Submitting feedback from user {user_id}...")
    
    feedback_data = {
        "latitude": lat,
        "longitude": lon,
        "rating": rating,
        "comment": comment,
        "place_type": "tourist_place",
        "region": "Tamil Nadu",
        "user_id": user_id
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/feedback/",
            json=feedback_data
        )
        
        if response.status_code == 201:
            result = response.json()
            print(f"   ✅ Feedback submitted successfully!")
            print(f"   Approval status: {result['approval_status']}")
            print(f"   Message: {result['message']}")
            return True
        else:
            print(f"   ❌ Error: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error submitting feedback: {e}")
        return False


def get_location_summary(lat, lon):
    """Get comprehensive feedback summary for a location."""
    print(f"📋 Getting location summary for {TEST_LOCATION['name']}...")
    
    try:
        response = requests.get(
            f"{BASE_URL}/feedback/location-summary/",
            params={
                "latitude": lat,
                "longitude": lon,
                "radius": 100
            }
        )
        
        if response.status_code == 200:
            data = response.json()["data"]
            print(f"   Feedback count: {data['feedback_count']}")
            print(f"   Unique users: {data['unique_users']}")
            print(f"   Meets threshold: {data['meets_threshold']}")
            print(f"   Average rating: {data['statistics']['average_rating']:.1f}")
            print(f"   Safety score: {data['safety_score']:.3f}")
            
            if data['recommendations']:
                print("   Recommendations:")
                for rec in data['recommendations']:
                    print(f"     - {rec}")
                    
            return data
        else:
            print(f"   ❌ Error: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"   ❌ Error getting summary: {e}")
        return None


def get_safety_score(lat, lon):
    """Get the enhanced safety score for a location."""
    print(f"🛡️ Getting enhanced safety score for {TEST_LOCATION['name']}...")
    
    try:
        response = requests.get(
            f"{BASE_URL}/combined_data/",
            params={
                "latitude": lat,
                "longitude": lon,
                "radius": 800
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            score = data["overall_safety_score"]
            feedback_info = data["user_feedback"]["location_specific_analysis"]
            
            print(f"   Overall safety score: {score}")
            print(f"   Scoring method: {feedback_info['scoring_method']}")
            print(f"   Has sufficient feedback: {feedback_info['has_sufficient_feedback']}")
            print(f"   AI weight: {feedback_info['ai_score_weight']}")
            print(f"   User feedback weight: {feedback_info['user_feedback_weight']}")
            
            if feedback_info['has_sufficient_feedback']:
                print("   ✅ Using enhanced scoring with user feedback!")
            else:
                print("   ⚠️ Using AI-only scoring (insufficient user feedback)")
                
            return data
        else:
            print(f"   ❌ Error: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"   ❌ Error getting safety score: {e}")
        return None


def simulate_user_feedback_collection():
    """Simulate collecting feedback from multiple users."""
    print("\n🎭 Simulating feedback collection from multiple users...")
    print("=" * 60)
    
    lat, lon = TEST_LOCATION["latitude"], TEST_LOCATION["longitude"]
    
    # Check initial progress
    initial_progress = check_feedback_progress(lat, lon)
    if not initial_progress:
        return
    
    # Simulate feedback from 10 users
    print(f"\n📝 Simulating feedback from 10 users...")
    successful_submissions = 0
    
    for i in range(1, 11):
        user_id = f"demo_user_{i}"
        rating = random.randint(5, 9)  # Generally positive ratings
        comment = f"Demo feedback from user {i} - generally safe area"
        
        if submit_feedback(lat, lon, user_id, rating, comment):
            successful_submissions += 1
        
        # Small delay between submissions
        time.sleep(0.5)
    
    print(f"\n✅ Successfully submitted {successful_submissions}/10 feedbacks")
    
    # Check progress after submissions
    print(f"\n📊 Checking progress after submissions...")
    final_progress = check_feedback_progress(lat, lon)
    
    if final_progress:
        improvement = final_progress['current_feedbacks'] - initial_progress['current_feedbacks']
        print(f"   Improvement: +{improvement} feedbacks")
        print(f"   Progress change: {initial_progress['progress_percentage']:.1f}% → {final_progress['progress_percentage']:.1f}%")


def demonstrate_enhanced_scoring():
    """Demonstrate the enhanced scoring system."""
    print("\n🧮 Demonstrating Enhanced Scoring System")
    print("=" * 60)
    
    lat, lon = TEST_LOCATION["latitude"], TEST_LOCATION["longitude"]
    
    # Get location summary
    summary = get_location_summary(lat, lon)
    if not summary:
        return
    
    # Get enhanced safety score
    safety_data = get_safety_score(lat, lon)
    if not safety_data:
        return
    
    # Show the difference between AI-only and enhanced scoring
    ai_score = safety_data["user_feedback"]["calculation"]["ai_safety_score"]
    enhanced_score = safety_data["user_feedback"]["calculation"]["enhanced_score"]
    
    print(f"\n📊 Scoring Comparison:")
    print(f"   AI-only score: {ai_score}")
    print(f"   Enhanced score: {enhanced_score}")
    print(f"   Difference: {enhanced_score - ai_score:+.1f}")
    
    if summary['meets_threshold']:
        print("   ✅ Enhanced scoring is active (50+ user feedbacks)")
    else:
        print("   ⚠️ AI-only scoring (insufficient user feedback)")


def show_system_analytics():
    """Show system-wide analytics."""
    print("\n📈 System Analytics")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/feedback/analytics/")
        
        if response.status_code == 200:
            data = response.json()["data"]
            overview = data["system_overview"]
            progress = data["collection_progress"]
            
            print(f"System Overview:")
            print(f"   Total feedbacks: {overview['total_feedbacks']}")
            print(f"   Unique users: {overview['unique_users']}")
            print(f"   Unique locations: {overview['unique_locations']}")
            print(f"   Locations with sufficient feedback: {overview['locations_with_sufficient_feedback']}")
            print(f"   Completion rate: {progress['completion_rate']:.1f}%")
            
            print(f"\nRecent Activity:")
            recent = data["recent_activity"]
            print(f"   Feedbacks last 7 days: {recent['feedbacks_last_7_days']}")
            print(f"   Average daily feedbacks: {recent['average_daily_feedbacks']}")
            
        else:
            print(f"❌ Error getting analytics: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error getting analytics: {e}")


def main():
    """Main demonstration function."""
    print("🚀 Enhanced Feedback Collection System Demo")
    print("=" * 60)
    print(f"Testing location: {TEST_LOCATION['name']}")
    print(f"Coordinates: {TEST_LOCATION['latitude']}, {TEST_LOCATION['longitude']}")
    print(f"Base URL: {BASE_URL}")
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/feedback/analytics/", timeout=5)
        if response.status_code != 200:
            print(f"\n❌ Server not responding properly. Status: {response.status_code}")
            print("Please ensure the Django server is running on localhost:8000")
            return
    except requests.exceptions.RequestException:
        print(f"\n❌ Cannot connect to server at {BASE_URL}")
        print("Please start the Django server with: python manage.py runserver")
        return
    
    print("✅ Server is running!")
    
    # Run demonstrations
    try:
        # 1. Check initial progress
        check_feedback_progress(TEST_LOCATION["latitude"], TEST_LOCATION["longitude"])
        
        # 2. Simulate user feedback collection
        simulate_user_feedback_collection()
        
        # 3. Demonstrate enhanced scoring
        demonstrate_enhanced_scoring()
        
        # 4. Show system analytics
        show_system_analytics()
        
        print("\n✅ Demo completed successfully!")
        print("\n💡 Key Takeaways:")
        print("   - The system tracks progress towards 50-user threshold")
        print("   - Enhanced scoring activates when sufficient feedback is collected")
        print("   - User feedback is weighted alongside AI analysis")
        print("   - System provides comprehensive analytics and monitoring")
        
    except KeyboardInterrupt:
        print("\n\n⏹️ Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
