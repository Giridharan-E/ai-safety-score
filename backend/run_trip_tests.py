#!/usr/bin/env python3
"""
Interactive test runner for the trip recommendation system.

This script provides an easy way to test different parts of the system.
"""

import os
import sys
import requests
import json
from datetime import datetime, timedelta


def check_server():
    """Check if the Django server is running."""
    try:
        response = requests.get("http://localhost:8000/api/feedback/analytics/", timeout=5)
        return response.status_code == 200
    except:
        return False


def test_safety_score():
    """Test the safety score endpoint."""
    print("🔒 Testing Safety Score API")
    print("=" * 40)
    
    try:
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
            print(f"✅ Safety Score: {data.get('overall_safety_score', 0)}")
            print(f"✅ Safety Color: {data.get('safety_color', 'unknown')}")
            print(f"✅ User Feedback: {data.get('user_feedback', {}).get('total_feedbacks', 0)} ratings")
            return True
        else:
            print(f"❌ Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_weather_analysis():
    """Test the weather analysis endpoint."""
    print("\n🌤️ Testing Weather Analysis API")
    print("=" * 40)
    
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
                print(f"✅ Weather Score: {weather.get('overall_weather_score', 0):.2f}")
                print(f"✅ Locations Analyzed: {len(weather.get('locations', {}))}")
                if weather.get('weather_recommendations'):
                    print("✅ Recommendations:")
                    for rec in weather['weather_recommendations'][:2]:
                        print(f"   • {rec}")
                return True
            else:
                print(f"❌ API Error: {data}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_tourist_factors():
    """Test the tourist factors endpoint."""
    print("\n🏛️ Testing Tourist Factors API")
    print("=" * 40)
    
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
                print(f"✅ Tourist Score: {tourist.get('overall_tourist_score', 0):.2f}")
                print(f"✅ Locations Analyzed: {len(tourist.get('locations', {}))}")
                if tourist.get('tourist_recommendations'):
                    print("✅ Recommendations:")
                    for rec in tourist['tourist_recommendations'][:2]:
                        print(f"   • {rec}")
                return True
            else:
                print(f"❌ API Error: {data}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_trip_recommendation():
    """Test the trip recommendation endpoint."""
    print("\n🎯 Testing Trip Recommendation API")
    print("=" * 40)
    
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
                print(f"✅ Overall Score: {rec_data.get('overall_score', 0):.2f}")
                print(f"✅ Recommendation: {rec_data.get('recommendation', 'unknown')}")
                print(f"✅ Confidence: {rec_data.get('confidence', 0):.2f}")
                
                if rec_data.get('key_factors'):
                    print("✅ Key Factors:")
                    for factor in rec_data['key_factors'][:2]:
                        print(f"   • {factor}")
                
                if rec_data.get('suggestions'):
                    print("✅ Suggestions:")
                    for suggestion in rec_data['suggestions'][:2]:
                        print(f"   • {suggestion}")
                
                return True
            else:
                print(f"❌ API Error: {data}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_feedback_system():
    """Test the feedback system."""
    print("\n📝 Testing Feedback System")
    print("=" * 40)
    
    try:
        # Test feedback analytics
        response = requests.get("http://localhost:8000/api/feedback/analytics/", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                analytics = data["data"]
                print(f"✅ Total Feedbacks: {analytics.get('total_feedbacks', 0)}")
                print(f"✅ Unique Users: {analytics.get('unique_users', 0)}")
                print(f"✅ Average Rating: {analytics.get('average_rating', 0):.2f}")
                print(f"✅ Locations with Feedback: {analytics.get('locations_with_feedback', 0)}")
                return True
            else:
                print(f"❌ API Error: {data}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """Main interactive test runner."""
    print("🧪 TRIP RECOMMENDATION SYSTEM TEST RUNNER")
    print("=" * 50)
    
    # Check if server is running
    if not check_server():
        print("❌ Django server is not running!")
        print("Please start it with: python manage.py runserver")
        return
    
    print("✅ Django server is running")
    
    # Test menu
    while True:
        print("\n" + "=" * 50)
        print("Choose a test to run:")
        print("1. 🔒 Safety Score Test")
        print("2. 🌤️ Weather Analysis Test")
        print("3. 🏛️ Tourist Factors Test")
        print("4. 🎯 Trip Recommendation Test")
        print("5. 📝 Feedback System Test")
        print("6. 🚀 Run All Tests")
        print("0. ❌ Exit")
        
        choice = input("\nEnter your choice (0-6): ").strip()
        
        if choice == "0":
            print("👋 Goodbye!")
            break
        elif choice == "1":
            test_safety_score()
        elif choice == "2":
            test_weather_analysis()
        elif choice == "3":
            test_tourist_factors()
        elif choice == "4":
            test_trip_recommendation()
        elif choice == "5":
            test_feedback_system()
        elif choice == "6":
            print("\n🚀 Running All Tests...")
            print("=" * 50)
            
            tests = [
                ("Safety Score", test_safety_score),
                ("Weather Analysis", test_weather_analysis),
                ("Tourist Factors", test_tourist_factors),
                ("Trip Recommendation", test_trip_recommendation),
                ("Feedback System", test_feedback_system)
            ]
            
            passed = 0
            total = len(tests)
            
            for test_name, test_func in tests:
                print(f"\n🧪 Running {test_name} Test...")
                if test_func():
                    passed += 1
                    print(f"✅ {test_name} Test PASSED")
                else:
                    print(f"❌ {test_name} Test FAILED")
            
            print(f"\n📊 FINAL RESULTS: {passed}/{total} tests passed")
            if passed == total:
                print("🎉 All tests passed! System is working perfectly!")
            else:
                print("⚠️ Some tests failed. Check the output above.")
        else:
            print("❌ Invalid choice. Please try again.")


if __name__ == "__main__":
    main()