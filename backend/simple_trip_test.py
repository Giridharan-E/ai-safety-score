#!/usr/bin/env python3
"""
Simple standalone test for trip recommendation system.

This script tests the API endpoints without requiring Django setup.
"""

import requests
import json
import time


def test_server_connection():
    """Test if the server is running."""
    print("🔍 Testing server connection...")
    try:
        response = requests.get("http://localhost:8000/api/feedback/analytics/", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running and accessible!")
            return True
        else:
            print(f"❌ Server responded with status: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to server: {e}")
        print("Please start the Django server with: python manage.py runserver")
        return False


def test_trip_recommendation():
    """Test the main trip recommendation endpoint."""
    print("\n🎯 Testing Trip Recommendation API")
    print("=" * 50)
    
    trip_data = {
        "start_date": "2024-03-15",
        "end_date": "2024-03-22",
        "locations": [
            {
                "latitude": 13.049953,
                "longitude": 80.282403,
                "name": "Marina Beach, Chennai",
                "country": "India"
            }
        ],
        "budget": {
            "total": 1500,
            "per_day": 200,
            "currency": "USD"
        },
        "traveler_profile": {
            "experience_level": "beginner",
            "preferences": ["beaches", "cultural_sites"],
            "group_size": 2
        }
    }
    
    try:
        print("📤 Sending trip recommendation request...")
        response = requests.post(
            "http://localhost:8000/api/trip/recommendation/",
            json=trip_data,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                rec = data["data"]["recommendation"]
                print("✅ Trip recommendation received!")
                print(f"Overall Score: {rec.get('overall_score', 0):.2f}")
                print(f"Recommendation: {rec.get('recommendation', 'unknown').upper()}")
                print(f"Confidence: {rec.get('confidence', 0):.2f}")
                
                if rec.get('key_factors'):
                    print("\n🔑 Key Factors:")
                    for factor in rec['key_factors'][:3]:
                        print(f"  • {factor}")
                
                if rec.get('suggestions'):
                    print("\n💡 Suggestions:")
                    for suggestion in rec['suggestions'][:3]:
                        print(f"  • {suggestion}")
                
                return True
            else:
                print(f"❌ API returned error: {data}")
                return False
        else:
            print(f"❌ HTTP error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Request error: {e}")
        return False


def test_weather_analysis():
    """Test the weather analysis endpoint."""
    print("\n🌤️ Testing Weather Analysis API")
    print("=" * 50)
    
    locations = json.dumps([{
        "latitude": 13.049953,
        "longitude": 80.282403,
        "name": "Marina Beach, Chennai"
    }])
    
    try:
        print("📤 Sending weather analysis request...")
        response = requests.get(
            "http://localhost:8000/api/trip/weather-analysis/",
            params={
                "start_date": "2024-03-15",
                "end_date": "2024-03-22",
                "locations": locations
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                weather = data["data"]
                print("✅ Weather analysis received!")
                print(f"Weather Score: {weather.get('overall_weather_score', 0):.2f}")
                print(f"Locations analyzed: {len(weather.get('locations', {}))}")
                
                if weather.get('weather_recommendations'):
                    print("\n🌤️ Weather Recommendations:")
                    for rec in weather['weather_recommendations'][:3]:
                        print(f"  • {rec}")
                
                return True
            else:
                print(f"❌ API returned error: {data}")
                return False
        else:
            print(f"❌ HTTP error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Request error: {e}")
        return False


def test_tourist_factors():
    """Test the tourist factors endpoint."""
    print("\n🏛️ Testing Tourist Factors API")
    print("=" * 50)
    
    locations = json.dumps([{
        "latitude": 13.049953,
        "longitude": 80.282403,
        "name": "Marina Beach, Chennai",
        "country": "India"
    }])
    
    try:
        print("📤 Sending tourist factors request...")
        response = requests.get(
            "http://localhost:8000/api/trip/tourist-factors/",
            params={
                "start_date": "2024-03-15",
                "end_date": "2024-03-22",
                "locations": locations
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                tourist = data["data"]
                print("✅ Tourist factors analysis received!")
                print(f"Tourist Score: {tourist.get('overall_tourist_score', 0):.2f}")
                print(f"Locations analyzed: {len(tourist.get('locations', {}))}")
                
                if tourist.get('tourist_recommendations'):
                    print("\n🏛️ Tourist Recommendations:")
                    for rec in tourist['tourist_recommendations'][:3]:
                        print(f"  • {rec}")
                
                return True
            else:
                print(f"❌ API returned error: {data}")
                return False
        else:
            print(f"❌ HTTP error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Request error: {e}")
        return False


def test_safety_score():
    """Test the existing safety score endpoint."""
    print("\n🛡️ Testing Safety Score API")
    print("=" * 50)
    
    try:
        print("📤 Sending safety score request...")
        response = requests.get(
            "http://localhost:8000/api/combined_data/",
            params={
                "latitude": 13.049953,
                "longitude": 80.282403,
                "radius": 800
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Safety score received!")
            print(f"Safety Score: {data.get('overall_safety_score', 0)}")
            print(f"Safety Color: {data.get('safety_color', 'unknown')}")
            
            if data.get('user_feedback'):
                feedback = data['user_feedback']
                print(f"User Feedback Count: {feedback.get('total_feedbacks', 0)}")
                print(f"Average Rating: {feedback.get('average_rating', 0)}")
            
            return True
        else:
            print(f"❌ HTTP error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Request error: {e}")
        return False


def main():
    """Run all API tests."""
    print("🧪 TRIP RECOMMENDATION API TESTS")
    print("=" * 60)
    print("This script tests the API endpoints without requiring Django setup.")
    print("Make sure the Django server is running: python manage.py runserver")
    
    # Test server connection
    if not test_server_connection():
        return
    
    # Run tests
    tests_passed = 0
    total_tests = 5
    
    if test_trip_recommendation():
        tests_passed += 1
    
    if test_weather_analysis():
        tests_passed += 1
    
    if test_tourist_factors():
        tests_passed += 1
    
    if test_safety_score():
        tests_passed += 1
    
    # Summary
    print(f"\n📊 TEST RESULTS")
    print("=" * 50)
    print(f"Tests passed: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("✅ All API tests passed! The system is working correctly.")
    else:
        print("⚠️ Some tests failed. Check the errors above.")
    
    print(f"\n💡 Available endpoints:")
    print("• POST /api/trip/recommendation/ - Main trip recommendation")
    print("• GET /api/trip/weather-analysis/ - Weather analysis")
    print("• GET /api/trip/tourist-factors/ - Tourist factors analysis")
    print("• GET /api/combined_data/ - Safety score")
    print("• GET /api/feedback/ - Submit feedback")
    print("• GET /api/tester/ - HTML test page")


if __name__ == "__main__":
    main()
