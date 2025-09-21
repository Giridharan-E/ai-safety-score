#!/usr/bin/env python3
"""
Standalone test script for the trip recommendation system.

This script tests the API endpoints without importing the services directly.
"""

import os
import sys
import requests
import json
from datetime import datetime, timedelta


def test_trip_weather_service():
    """Test the trip weather service via API."""
    print("🌤️ Testing Trip Weather Service")
    print("=" * 50)
    
    locations = json.dumps([{
        "latitude": 13.049953,
        "longitude": 80.282403,
        "name": "Marina Beach, Chennai"
    }])
    
    try:
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
                print(f"✅ Weather analysis completed")
                print(f"Overall weather score: {weather.get('overall_weather_score', 0):.2f}")
                print(f"Locations analyzed: {len(weather.get('locations', {}))}")
                
                if weather.get('weather_recommendations'):
                    print("Weather recommendations:")
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
        print(f"❌ Weather service error: {e}")
        return False


def test_trip_tourist_factors_service():
    """Test the trip tourist factors service via API."""
    print("\n🏛️ Testing Trip Tourist Factors Service")
    print("=" * 50)
    
    locations = json.dumps([{
        "latitude": 13.049953,
        "longitude": 80.282403,
        "name": "Marina Beach, Chennai",
        "country": "India"
    }])
    
    try:
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
                print(f"✅ Tourist factors analysis completed")
                print(f"Overall tourist score: {tourist.get('overall_tourist_score', 0):.2f}")
                print(f"Locations analyzed: {len(tourist.get('locations', {}))}")
                
                if tourist.get('tourist_recommendations'):
                    print("Tourist recommendations:")
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
        print(f"❌ Tourist factors service error: {e}")
        return False


def test_trip_recommendation_engine():
    """Test the trip recommendation engine via API."""
    print("\n🎯 Testing Trip Recommendation Engine")
    print("=" * 50)
    
    trip_details = {
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
        response = requests.post(
            "http://localhost:8000/api/trip/recommendation/",
            json=trip_details,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                rec_data = data["data"]["recommendation"]
                print(f"✅ Trip recommendation completed")
                print(f"Overall score: {rec_data.get('overall_score', 0):.2f}")
                print(f"Recommendation: {rec_data.get('recommendation', 'unknown')}")
                print(f"Confidence: {rec_data.get('confidence', 0):.2f}")
                
                if rec_data.get('key_factors'):
                    print("Key factors:")
                    for factor in rec_data['key_factors'][:3]:
                        print(f"  • {factor}")
                
                if rec_data.get('suggestions'):
                    print("Suggestions:")
                    for suggestion in rec_data['suggestions'][:3]:
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
        print(f"❌ Recommendation engine error: {e}")
        return False


def test_api_endpoints():
    """Test the API endpoints."""
    print("\n🌐 Testing API Endpoints")
    print("=" * 50)
    
    base_url = "http://localhost:8000/api"
    
    # Test if server is running
    try:
        response = requests.get(f"{base_url}/feedback/analytics/", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running")
        else:
            print(f"❌ Server error: {response.status_code}")
            return False
    except requests.exceptions.RequestException:
        print("❌ Server not running. Start with: python manage.py runserver")
        return False
    
    # Test safety score endpoint
    try:
        response = requests.get(
            f"{base_url}/combined_data/",
            params={
                "latitude": 13.049953,
                "longitude": 80.282403,
                "radius": 800
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Safety score API working")
            print(f"  Safety Score: {data.get('overall_safety_score', 0)}")
            print(f"  Safety Color: {data.get('safety_color', 'unknown')}")
        else:
            print(f"❌ Safety API error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Safety API test error: {e}")
        return False
    
    return True


def main():
    """Run all tests."""
    print("🧪 TRIP RECOMMENDATION SYSTEM TESTS")
    print("=" * 60)
    
    tests_passed = 0
    total_tests = 4
    
    # Test individual services
    if test_trip_weather_service():
        tests_passed += 1
    
    if test_trip_tourist_factors_service():
        tests_passed += 1
    
    if test_trip_recommendation_engine():
        tests_passed += 1
    
    if test_api_endpoints():
        tests_passed += 1
    
    # Summary
    print(f"\n📊 TEST RESULTS")
    print("=" * 50)
    print(f"Tests passed: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("✅ All tests passed! System is working correctly.")
    else:
        print("⚠️ Some tests failed. Check the errors above.")
    
    print(f"\n💡 Next steps:")
    print("1. Start the Django server: python manage.py runserver")
    print("2. Test the API endpoints with curl or Postman")
    print("3. Run the example script: python trip_recommendation_example.py")


if __name__ == "__main__":
    main()
