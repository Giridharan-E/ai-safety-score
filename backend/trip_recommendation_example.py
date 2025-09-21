#!/usr/bin/env python3
"""
Trip Recommendation System Example

This script demonstrates how to use the trip recommendation system
to get comprehensive trip recommendations for tourists.
"""

import requests
import json
import time
from datetime import datetime, timedelta

# Configuration
BASE_URL = "http://localhost:8000/api"

# Sample trip scenarios
SAMPLE_TRIPS = [
    {
        "name": "Chennai Beach Vacation",
        "description": "A week-long beach vacation in Chennai",
        "trip_data": {
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
                "preferences": ["beaches", "cultural_sites", "food"],
                "group_size": 2
            }
        }
    },
    {
        "name": "Golden Triangle Tour",
        "description": "Classic India tour covering Delhi, Agra, and Jaipur",
        "trip_data": {
            "start_date": "2024-06-01",
            "end_date": "2024-06-15",
            "locations": [
                {
                    "latitude": 28.6139,
                    "longitude": 77.2090,
                    "name": "Red Fort, Delhi",
                    "country": "India"
                },
                {
                    "latitude": 27.1751,
                    "longitude": 78.0421,
                    "name": "Taj Mahal, Agra",
                    "country": "India"
                },
                {
                    "latitude": 26.9124,
                    "longitude": 75.7873,
                    "name": "Hawa Mahal, Jaipur",
                    "country": "India"
                }
            ],
            "budget": {
                "total": 3000,
                "per_day": 200,
                "currency": "USD"
            },
            "traveler_profile": {
                "experience_level": "intermediate",
                "preferences": ["cultural_sites", "historical_monuments", "photography"],
                "group_size": 4
            }
        }
    },
    {
        "name": "Monsoon Season Trip",
        "description": "Trip during monsoon season (not recommended)",
        "trip_data": {
            "start_date": "2024-07-15",
            "end_date": "2024-07-22",
            "locations": [
                {
                    "latitude": 12.9716,
                    "longitude": 77.5946,
                    "name": "Bangalore Palace",
                    "country": "India"
                },
                {
                    "latitude": 13.0827,
                    "longitude": 80.2707,
                    "name": "Chennai Central",
                    "country": "India"
                }
            ],
            "budget": {
                "total": 2000,
                "per_day": 250,
                "currency": "USD"
            },
            "traveler_profile": {
                "experience_level": "beginner",
                "preferences": ["cultural_sites", "shopping"],
                "group_size": 2
            }
        }
    }
]


def test_server_connection():
    """Test if the server is running and accessible."""
    print("🔍 Testing server connection...")
    try:
        response = requests.get(f"{BASE_URL}/feedback/analytics/", timeout=5)
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


def get_trip_recommendation(trip_data):
    """Get trip recommendation from the API."""
    print(f"📋 Getting trip recommendation...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/trip/recommendation/",
            json=trip_data,
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ API error: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {e}")
        return None


def display_recommendation_summary(recommendation_data):
    """Display a summary of the trip recommendation."""
    if not recommendation_data or not recommendation_data.get("success"):
        print("❌ No recommendation data available")
        return
    
    data = recommendation_data["data"]
    rec = data["recommendation"]
    
    print(f"\n🎯 TRIP RECOMMENDATION SUMMARY")
    print("=" * 50)
    
    # Overall recommendation
    recommendation_level = rec["recommendation"]
    overall_score = rec["overall_score"]
    confidence = rec["confidence"]
    
    print(f"Overall Score: {overall_score:.2f}/1.0")
    print(f"Recommendation: {recommendation_level.upper().replace('_', ' ')}")
    print(f"Confidence: {confidence:.2f}/1.0")
    
    # Recommendation emoji
    if recommendation_level == "proceed":
        emoji = "✅"
    elif recommendation_level == "proceed_with_caution":
        emoji = "⚠️"
    elif recommendation_level == "reconsider":
        emoji = "🤔"
    else:
        emoji = "❌"
    
    print(f"Status: {emoji} {recommendation_level.upper().replace('_', ' ')}")
    
    # Key factors
    if rec.get("key_factors"):
        print(f"\n🔑 Key Factors:")
        for factor in rec["key_factors"]:
            print(f"  • {factor}")
    
    # Warnings
    if rec.get("warnings"):
        print(f"\n⚠️ Warnings:")
        for warning in rec["warnings"]:
            print(f"  • {warning}")
    
    # Suggestions
    if rec.get("suggestions"):
        print(f"\n💡 Suggestions:")
        for suggestion in rec["suggestions"]:
            print(f"  • {suggestion}")
    
    # Score breakdown
    if rec.get("score_breakdown"):
        print(f"\n📊 Score Breakdown:")
        breakdown = rec["score_breakdown"]
        for factor, score in breakdown.items():
            print(f"  • {factor.replace('_', ' ').title()}: {score:.2f}")


def display_detailed_analysis(recommendation_data):
    """Display detailed analysis of each factor."""
    if not recommendation_data or not recommendation_data.get("success"):
        return
    
    data = recommendation_data["data"]
    analysis = data["analysis"]
    
    print(f"\n📈 DETAILED ANALYSIS")
    print("=" * 50)
    
    # Weather Analysis
    weather = analysis.get("weather", {})
    if weather:
        print(f"\n🌤️ Weather Analysis:")
        print(f"  Overall Score: {weather.get('overall_weather_score', 0):.2f}")
        if weather.get("weather_recommendations"):
            print(f"  Recommendations:")
            for rec in weather["weather_recommendations"][:3]:  # Show top 3
                print(f"    • {rec}")
    
    # Tourist Factors
    tourist = analysis.get("tourist_factors", {})
    if tourist:
        print(f"\n🏛️ Tourist Factors:")
        print(f"  Overall Score: {tourist.get('overall_tourist_score', 0):.2f}")
        if tourist.get("cost_estimates"):
            print(f"  Cost Estimates:")
            for location, costs in list(tourist["cost_estimates"].items())[:2]:  # Show top 2
                daily_cost = costs.get("total_per_day", 0)
                print(f"    • {location}: ${daily_cost:.2f}/day")
    
    # Safety Analysis
    safety = analysis.get("safety", {})
    if safety:
        print(f"\n🛡️ Safety Analysis:")
        print(f"  Overall Score: {safety.get('overall_safety_score', 0):.2f}")
        if safety.get("high_risk_locations"):
            print(f"  High Risk Locations:")
            for risk in safety["high_risk_locations"]:
                print(f"    • {risk['location']}: Score {risk['safety_score']:.1f}")
    
    # User Feedback
    feedback = analysis.get("user_feedback", {})
    if feedback:
        print(f"\n👥 User Feedback:")
        print(f"  Overall Score: {feedback.get('overall_feedback_score', 0):.2f}")
        if feedback.get("locations_needing_feedback"):
            print(f"  Locations Needing More Feedback:")
            for loc in feedback["locations_needing_feedback"][:3]:  # Show top 3
                print(f"    • {loc['location']}: {loc['current_feedbacks']}/50 feedbacks")
    
    # Cost Analysis
    cost = analysis.get("cost", {})
    if cost:
        print(f"\n💰 Cost Analysis:")
        print(f"  Cost Effectiveness: {cost.get('cost_effectiveness_score', 0):.2f}")
        print(f"  Budget Compatibility: {cost.get('budget_compatibility', 'unknown')}")
        if cost.get("average_daily_cost"):
            print(f"  Average Daily Cost: ${cost['average_daily_cost']:.2f}")


def run_trip_scenario(scenario):
    """Run a complete trip scenario and display results."""
    print(f"\n🚀 RUNNING TRIP SCENARIO: {scenario['name']}")
    print("=" * 60)
    print(f"Description: {scenario['description']}")
    
    # Display trip details
    trip_data = scenario["trip_data"]
    print(f"\n📅 Trip Details:")
    print(f"  Dates: {trip_data['start_date']} to {trip_data['end_date']}")
    print(f"  Locations: {len(trip_data['locations'])} destinations")
    for i, loc in enumerate(trip_data['locations'], 1):
        print(f"    {i}. {loc['name']}")
    
    if trip_data.get('budget'):
        budget = trip_data['budget']
        print(f"  Budget: ${budget.get('total', 0)} total, ${budget.get('per_day', 0)}/day")
    
    # Get recommendation
    recommendation = get_trip_recommendation(trip_data)
    
    if recommendation:
        # Display summary
        display_recommendation_summary(recommendation)
        
        # Display detailed analysis
        display_detailed_analysis(recommendation)
        
        # Save to file for reference
        filename = f"trip_recommendation_{scenario['name'].lower().replace(' ', '_')}.json"
        with open(filename, 'w') as f:
            json.dump(recommendation, f, indent=2)
        print(f"\n💾 Recommendation saved to: {filename}")
        
    else:
        print("❌ Failed to get recommendation")
    
    print("\n" + "="*60)


def demonstrate_individual_services():
    """Demonstrate individual service endpoints."""
    print(f"\n🔧 TESTING INDIVIDUAL SERVICES")
    print("=" * 50)
    
    # Test weather analysis
    print(f"\n🌤️ Testing Weather Analysis...")
    try:
        locations = json.dumps([{
            "latitude": 13.049953,
            "longitude": 80.282403,
            "name": "Marina Beach, Chennai"
        }])
        
        response = requests.get(
            f"{BASE_URL}/trip/weather-analysis/",
            params={
                "start_date": "2024-03-15",
                "end_date": "2024-03-22",
                "locations": locations
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            weather_score = data["data"].get("overall_weather_score", 0)
            print(f"  ✅ Weather Analysis: Score {weather_score:.2f}")
        else:
            print(f"  ❌ Weather Analysis failed: {response.status_code}")
            
    except Exception as e:
        print(f"  ❌ Weather Analysis error: {e}")
    
    # Test tourist factors
    print(f"\n🏛️ Testing Tourist Factors...")
    try:
        locations = json.dumps([{
            "latitude": 13.049953,
            "longitude": 80.282403,
            "name": "Marina Beach, Chennai",
            "country": "India"
        }])
        
        response = requests.get(
            f"{BASE_URL}/trip/tourist-factors/",
            params={
                "start_date": "2024-03-15",
                "end_date": "2024-03-22",
                "locations": locations
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            tourist_score = data["data"].get("overall_tourist_score", 0)
            print(f"  ✅ Tourist Factors: Score {tourist_score:.2f}")
        else:
            print(f"  ❌ Tourist Factors failed: {response.status_code}")
            
    except Exception as e:
        print(f"  ❌ Tourist Factors error: {e}")


def main():
    """Main demonstration function."""
    print("🌟 TRIP RECOMMENDATION SYSTEM DEMO")
    print("=" * 60)
    print("This demo shows how the trip recommendation system works")
    print("by analyzing multiple factors to provide comprehensive")
    print("trip recommendations for tourists.")
    
    # Test server connection
    if not test_server_connection():
        return
    
    # Run trip scenarios
    print(f"\n🎯 RUNNING TRIP SCENARIOS")
    print("=" * 50)
    
    for scenario in SAMPLE_TRIPS:
        run_trip_scenario(scenario)
        time.sleep(1)  # Small delay between requests
    
    # Test individual services
    demonstrate_individual_services()
    
    print(f"\n✅ DEMO COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    print("Key Takeaways:")
    print("• The system analyzes weather, tourist factors, safety, and costs")
    print("• Recommendations range from 'proceed' to 'not_recommended'")
    print("• Each recommendation includes detailed analysis and suggestions")
    print("• The system provides actionable insights for trip planning")
    print("• All analysis is saved to JSON files for reference")
    
    print(f"\n📁 Generated Files:")
    for scenario in SAMPLE_TRIPS:
        filename = f"trip_recommendation_{scenario['name'].lower().replace(' ', '_')}.json"
        print(f"  • {filename}")


if __name__ == "__main__":
    main()
