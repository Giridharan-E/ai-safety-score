#!/usr/bin/env python3
"""
Interactive Trip Planner

This script allows users to manually input their trip details and get recommendations.
"""

import json
from datetime import datetime, timedelta
from standalone_trip_engine import StandaloneTripRecommendationEngine


def get_user_input():
    """Get trip details from user input."""
    print("🌍 INTERACTIVE TRIP PLANNER")
    print("=" * 50)
    print("Let's plan your trip! Please provide the following details:\n")
    
    # Get trip dates
    while True:
        try:
            start_date = input("📅 Start date (YYYY-MM-DD): ").strip()
            datetime.strptime(start_date, "%Y-%m-%d")
            break
        except ValueError:
            print("❌ Invalid date format. Please use YYYY-MM-DD")
    
    while True:
        try:
            end_date = input("📅 End date (YYYY-MM-DD): ").strip()
            datetime.strptime(end_date, "%Y-%m-%d")
            if end_date <= start_date:
                print("❌ End date must be after start date")
                continue
            break
        except ValueError:
            print("❌ Invalid date format. Please use YYYY-MM-DD")
    
    # Get number of locations
    while True:
        try:
            num_locations = int(input("📍 Number of locations to visit: "))
            if num_locations < 1:
                print("❌ Please enter at least 1 location")
                continue
            break
        except ValueError:
            print("❌ Please enter a valid number")
    
    # Get location details
    locations = []
    for i in range(num_locations):
        print(f"\n📍 Location {i+1}:")
        name = input(f"   Name: ").strip()
        
        while True:
            try:
                latitude = float(input(f"   Latitude: "))
                if not -90 <= latitude <= 90:
                    print("❌ Latitude must be between -90 and 90")
                    continue
                break
            except ValueError:
                print("❌ Please enter a valid latitude")
        
        while True:
            try:
                longitude = float(input(f"   Longitude: "))
                if not -180 <= longitude <= 180:
                    print("❌ Longitude must be between -180 and 180")
                    continue
                break
            except ValueError:
                print("❌ Please enter a valid longitude")
        
        country = input(f"   Country: ").strip()
        
        locations.append({
            "name": name,
            "latitude": latitude,
            "longitude": longitude,
            "country": country
        })
    
    # Get budget information
    print(f"\n💰 Budget Information:")
    while True:
        try:
            total_budget = float(input("   Total budget (USD): "))
            if total_budget < 0:
                print("❌ Budget must be positive")
                continue
            break
        except ValueError:
            print("❌ Please enter a valid budget amount")
    
    while True:
        try:
            per_day_budget = float(input("   Budget per day (USD): "))
            if per_day_budget < 0:
                print("❌ Daily budget must be positive")
                continue
            break
        except ValueError:
            print("❌ Please enter a valid daily budget")
    
    currency = input("   Currency (default: USD): ").strip() or "USD"
    
    # Get traveler profile
    print(f"\n👤 Traveler Profile:")
    experience_levels = ["beginner", "intermediate", "advanced"]
    print("   Experience levels: beginner, intermediate, advanced")
    while True:
        experience = input("   Your experience level: ").strip().lower()
        if experience in experience_levels:
            break
        print("❌ Please choose from: beginner, intermediate, advanced")
    
    preferences = input("   Preferences (comma-separated, e.g., beaches, cultural_sites, adventure): ").strip()
    if preferences:
        preferences_list = [p.strip() for p in preferences.split(",")]
    else:
        preferences_list = []
    
    while True:
        try:
            group_size = int(input("   Group size: "))
            if group_size < 1:
                print("❌ Group size must be at least 1")
                continue
            break
        except ValueError:
            print("❌ Please enter a valid group size")
    
    # Compile trip details
    trip_details = {
        "start_date": start_date,
        "end_date": end_date,
        "locations": locations,
        "budget": {
            "total": total_budget,
            "per_day": per_day_budget,
            "currency": currency
        },
        "traveler_profile": {
            "experience_level": experience,
            "preferences": preferences_list,
            "group_size": group_size
        }
    }
    
    return trip_details


def display_recommendation(result):
    """Display the trip recommendation in a user-friendly format."""
    if result.get("error"):
        print(f"\n❌ Error: {result['error']}")
        return
    
    if not result.get("success"):
        print(f"\n❌ Failed to generate recommendation")
        return
    
    data = result["data"]
    rec = data["recommendation"]
    
    print("\n" + "=" * 60)
    print("🎯 TRIP RECOMMENDATION")
    print("=" * 60)
    
    # Overall recommendation
    score = rec['overall_score']
    recommendation = rec['recommendation']
    confidence = rec['confidence']
    
    print(f"📊 Overall Score: {score:.2f}/1.0")
    
    # Recommendation with emoji
    if recommendation == "proceed":
        print(f"✅ Recommendation: PROCEED - Trip is highly recommended!")
    elif recommendation == "proceed_with_caution":
        print(f"⚠️ Recommendation: PROCEED WITH CAUTION - Trip is recommended with precautions")
    elif recommendation == "reconsider":
        print(f"🤔 Recommendation: RECONSIDER - Consider alternative dates or destinations")
    else:
        print(f"❌ Recommendation: NOT RECOMMENDED - Trip is not recommended at this time")
    
    print(f"🎯 Confidence: {confidence:.1%}")
    
    # Key factors
    if rec['key_factors']:
        print(f"\n🔑 Key Factors:")
        for factor in rec['key_factors']:
            print(f"   • {factor}")
    
    # Suggestions
    if rec['suggestions']:
        print(f"\n💡 Suggestions:")
        for suggestion in rec['suggestions']:
            print(f"   {suggestion}")
    
    # Warnings
    if rec['warnings']:
        print(f"\n⚠️ Warnings:")
        for warning in rec['warnings']:
            print(f"   {warning}")
    
    # Detailed analysis
    print(f"\n📊 Detailed Analysis:")
    print(f"   🌤️ Weather Score: {data['weather_analysis']['overall_weather_score']:.2f}/1.0")
    print(f"   🏛️ Tourist Score: {data['tourist_analysis']['overall_tourist_score']:.2f}/1.0")
    print(f"   🔒 Safety Score: {data['safety_analysis']['overall_safety_score']:.2f}/1.0")
    print(f"   📝 Feedback Score: {data['feedback_analysis']['overall_feedback_score']:.2f}/1.0")
    print(f"   💰 Cost Score: {data['cost_analysis']['cost_effectiveness_score']:.2f}/1.0")
    
    # Location-specific details
    print(f"\n📍 Location Details:")
    for location_name, location_data in data['weather_analysis']['locations'].items():
        print(f"   {location_name}:")
        print(f"     Weather: {location_data['weather_score']:.2f}/1.0")
        print(f"     Temperature: {location_data['temperature_range']}")
        print(f"     Precipitation: {location_data['precipitation_risk']}")
        print(f"     Humidity: {location_data['humidity_level']}")


def save_recommendation(result, trip_details):
    """Save the recommendation to a file."""
    try:
        filename = f"trip_recommendation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        save_data = {
            "trip_details": trip_details,
            "recommendation": result,
            "generated_at": datetime.now().isoformat()
        }
        
        with open(filename, 'w') as f:
            json.dump(save_data, f, indent=2)
        
        print(f"\n💾 Recommendation saved to: {filename}")
        
    except Exception as e:
        print(f"\n❌ Error saving recommendation: {e}")


def main():
    """Main interactive function."""
    try:
        # Get user input
        trip_details = get_user_input()
        
        # Display summary
        print(f"\n📋 Trip Summary:")
        print(f"   Dates: {trip_details['start_date']} to {trip_details['end_date']}")
        print(f"   Locations: {len(trip_details['locations'])}")
        print(f"   Budget: {trip_details['budget']['total']} {trip_details['budget']['currency']}")
        print(f"   Group Size: {trip_details['traveler_profile']['group_size']}")
        
        # Confirm with user
        confirm = input(f"\n🤔 Generate recommendation? (y/n): ").strip().lower()
        if confirm != 'y':
            print("👋 Trip planning cancelled. Goodbye!")
            return
        
        # Generate recommendation
        print(f"\n🔄 Generating recommendation...")
        engine = StandaloneTripRecommendationEngine()
        result = engine.generate_trip_recommendation(trip_details)
        
        # Display results
        display_recommendation(result)
        
        # Ask if user wants to save
        save = input(f"\n💾 Save recommendation to file? (y/n): ").strip().lower()
        if save == 'y':
            save_recommendation(result, trip_details)
        
        # Ask if user wants to plan another trip
        another = input(f"\n🔄 Plan another trip? (y/n): ").strip().lower()
        if another == 'y':
            main()
        else:
            print("👋 Happy travels! Goodbye!")
    
    except KeyboardInterrupt:
        print(f"\n\n👋 Trip planning cancelled. Goodbye!")
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")


if __name__ == "__main__":
    main()
