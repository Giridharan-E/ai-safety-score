#!/usr/bin/env python3
"""
Enhanced Interactive Trip Planner with Google Maps Geocoding

This script allows users to input location names and automatically gets coordinates
using Google Maps Geocoding API.
"""

import json
import requests
import os
from datetime import datetime, timedelta
from standalone_trip_engine import StandaloneTripRecommendationEngine

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Loaded environment variables from .env file")
except ImportError:
    print("⚠️ python-dotenv not installed. Install with: pip install python-dotenv")
    print("   Or set GOOGLE_MAPS_API_KEY environment variable manually")


class GeocodingService:
    """Service for geocoding location names to coordinates."""
    
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv('GOOGLE_MAPS_API_KEY')
        self.base_url = "https://maps.googleapis.com/maps/api/geocode/json"
        
        # Fallback coordinates for common locations when API is not available
        self.fallback_locations = {
            'bangalore': {'lat': 12.9716, 'lon': 77.5946, 'country': 'India', 'address': 'Bangalore, Karnataka, India'},
            'chennai': {'lat': 13.0827, 'lon': 80.2707, 'country': 'India', 'address': 'Chennai, Tamil Nadu, India'},
            'mumbai': {'lat': 19.0760, 'lon': 72.8777, 'country': 'India', 'address': 'Mumbai, Maharashtra, India'},
            'delhi': {'lat': 28.7041, 'lon': 77.1025, 'country': 'India', 'address': 'Delhi, India'},
            'kolkata': {'lat': 22.5726, 'lon': 88.3639, 'country': 'India', 'address': 'Kolkata, West Bengal, India'},
            'hyderabad': {'lat': 17.3850, 'lon': 78.4867, 'country': 'India', 'address': 'Hyderabad, Telangana, India'},
            'pune': {'lat': 18.5204, 'lon': 73.8567, 'country': 'India', 'address': 'Pune, Maharashtra, India'},
            'agra': {'lat': 27.1767, 'lon': 78.0081, 'country': 'India', 'address': 'Agra, Uttar Pradesh, India'},
            'jaipur': {'lat': 26.9124, 'lon': 75.7873, 'country': 'India', 'address': 'Jaipur, Rajasthan, India'},
            'goa': {'lat': 15.2993, 'lon': 74.1240, 'country': 'India', 'address': 'Goa, India'},
            'kerala': {'lat': 10.8505, 'lon': 76.2711, 'country': 'India', 'address': 'Kerala, India'},
            'rajasthan': {'lat': 27.0238, 'lon': 74.2179, 'country': 'India', 'address': 'Rajasthan, India'},
            'taj mahal': {'lat': 27.1751, 'lon': 78.0421, 'country': 'India', 'address': 'Taj Mahal, Agra, Uttar Pradesh, India'},
            'marina beach': {'lat': 13.0499, 'lon': 80.2824, 'country': 'India', 'address': 'Marina Beach, Chennai, Tamil Nadu, India'},
            'golden temple': {'lat': 31.6204, 'lon': 74.8765, 'country': 'India', 'address': 'Golden Temple, Amritsar, Punjab, India'},
            'red fort': {'lat': 28.6562, 'lon': 77.2410, 'country': 'India', 'address': 'Red Fort, Delhi, India'},
            'gateway of india': {'lat': 18.9220, 'lon': 72.8347, 'country': 'India', 'address': 'Gateway of India, Mumbai, Maharashtra, India'},
            'hawa mahal': {'lat': 26.9239, 'lon': 75.8267, 'country': 'India', 'address': 'Hawa Mahal, Jaipur, Rajasthan, India'},
            'mysore palace': {'lat': 12.3051, 'lon': 76.6552, 'country': 'India', 'address': 'Mysore Palace, Mysuru, Karnataka, India'},
            'charminar': {'lat': 17.3616, 'lon': 78.4747, 'country': 'India', 'address': 'Charminar, Hyderabad, Telangana, India'},
        }
    
    def geocode_location(self, location_name, country=None):
        """
        Get coordinates for a location name using Google Maps Geocoding API.
        
        Args:
            location_name (str): Name of the location
            country (str): Optional country to narrow down results
            
        Returns:
            dict: Contains success, latitude, longitude, formatted_address, country
        """
        if not self.api_key:
            return {
                "success": False,
                "error": "Google Maps API key not found. Please set GOOGLE_MAPS_API_KEY environment variable or provide api_key parameter."
            }
        
        try:
            # Prepare the address
            address = location_name
            if country:
                address += f", {country}"
            
            # Make API request with better error handling
            params = {
                'address': address,
                'key': self.api_key
            }
            
            # Try with different timeout and retry settings
            try:
                response = requests.get(self.base_url, params=params, timeout=15)
                response.raise_for_status()
            except requests.exceptions.ConnectTimeout:
                return {
                    "success": False,
                    "error": "Connection timeout. Please check your internet connection and try again."
                }
            except requests.exceptions.ConnectionError as e:
                return {
                    "success": False,
                    "error": f"Network connection error. Please check your internet connection, firewall settings, or proxy configuration. Error: {str(e)}"
                }
            except requests.exceptions.Timeout:
                return {
                    "success": False,
                    "error": "Request timeout. The server took too long to respond."
                }
            except requests.exceptions.RequestException as e:
                return {
                    "success": False,
                    "error": f"Network error: {str(e)}"
                }
            
            data = response.json()
            
            if data['status'] == 'OK' and data['results']:
                result = data['results'][0]  # Get the first (most relevant) result
                location = result['geometry']['location']
                
                # Extract country from address components
                country_from_result = None
                for component in result['address_components']:
                    if 'country' in component['types']:
                        country_from_result = component['long_name']
                        break
                
                return {
                    "success": True,
                    "latitude": location['lat'],
                    "longitude": location['lng'],
                    "formatted_address": result['formatted_address'],
                    "country": country_from_result,
                    "place_id": result['place_id']
                }
            elif data['status'] == 'ZERO_RESULTS':
                return {
                    "success": False,
                    "error": f"No results found for '{location_name}'"
                }
            elif data['status'] == 'REQUEST_DENIED':
                return {
                    "success": False,
                    "error": "API request denied. Please check your API key and ensure Geocoding API is enabled."
                }
            elif data['status'] == 'OVER_QUERY_LIMIT':
                return {
                    "success": False,
                    "error": "API quota exceeded. Please try again later or check your billing."
                }
            else:
                return {
                    "success": False,
                    "error": f"Geocoding API error: {data['status']}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}"
            }
    
    def geocode_with_fallback(self, location_name, country=None):
        """
        Try Google Maps API first, then fallback to predefined locations.
        
        Args:
            location_name (str): Name of the location
            country (str): Optional country to narrow down results
            
        Returns:
            dict: Contains success, latitude, longitude, formatted_address, country
        """
        # First try the Google Maps API
        if self.api_key and self.api_key != "mock_key":
            result = self.geocode_location(location_name, country)
            if result["success"]:
                return result
        
        # If API fails, try fallback locations
        location_lower = location_name.lower().strip()
        
        # Check for exact matches first
        if location_lower in self.fallback_locations:
            fallback = self.fallback_locations[location_lower]
            return {
                "success": True,
                "latitude": fallback['lat'],
                "longitude": fallback['lon'],
                "formatted_address": fallback['address'],
                "country": fallback['country'],
                "source": "fallback_database"
            }
        
        # Check for partial matches
        for key, fallback in self.fallback_locations.items():
            if key in location_lower or location_lower in key:
                return {
                    "success": True,
                    "latitude": fallback['lat'],
                    "longitude": fallback['lon'],
                    "formatted_address": fallback['address'],
                    "country": fallback['country'],
                    "source": "fallback_database"
                }
        
        # If no fallback found, return the original API error or a generic error
        if self.api_key and self.api_key != "mock_key":
            return self.geocode_location(location_name, country)
        else:
            return {
                "success": False,
                "error": f"No fallback location found for '{location_name}'. Please enter coordinates manually or try a different location name."
            }
    
    def reverse_geocode(self, latitude, longitude):
        """
        Get location name from coordinates using reverse geocoding.
        
        Args:
            latitude (float): Latitude coordinate
            longitude (float): Longitude coordinate
            
        Returns:
            dict: Contains success, formatted_address, country
        """
        if not self.api_key:
            return {
                "success": False,
                "error": "Google Maps API key not found"
            }
        
        try:
            params = {
                'latlng': f"{latitude},{longitude}",
                'key': self.api_key
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data['status'] == 'OK' and data['results']:
                result = data['results'][0]
                
                # Extract country from address components
                country = None
                for component in result['address_components']:
                    if 'country' in component['types']:
                        country = component['long_name']
                        break
                
                return {
                    "success": True,
                    "formatted_address": result['formatted_address'],
                    "country": country,
                    "place_id": result['place_id']
                }
            else:
                return {
                    "success": False,
                    "error": f"Reverse geocoding error: {data['status']}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Error: {str(e)}"
            }


def get_user_input_with_geocoding():
    """Get trip details from user input with geocoding support."""
    print("🌍 ENHANCED INTERACTIVE TRIP PLANNER")
    print("=" * 50)
    print("Let's plan your trip! Please provide the following details:\n")
    
    # Initialize geocoding service
    geocoding = GeocodingService()
    
    # Check if API key is available
    if not geocoding.api_key:
        print("⚠️ Google Maps API key not found in .env file.")
        print("   You can:")
        print("   1. Add GOOGLE_MAPS_API_KEY=your_key_here to .env file")
        print("   2. Set GOOGLE_MAPS_API_KEY environment variable")
        print("   3. Enter coordinates manually")
        print("   4. Continue with mock geocoding (for testing)\n")
        
        use_mock = input("🤔 Use mock geocoding for testing? (y/n): ").strip().lower()
        if use_mock == 'y':
            geocoding.api_key = "mock_key"  # Enable mock mode
        else:
            print("📝 You'll need to enter coordinates manually.\n")
    else:
        print("✅ Google Maps API key found! Geocoding is available.\n")
    
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
    
    # Get location details with geocoding
    locations = []
    for i in range(num_locations):
        print(f"\n📍 Location {i+1}:")
        
        while True:
            location_name = input(f"   Location name (e.g., 'Marina Beach Chennai'): ").strip()
            if location_name:
                break
            print("❌ Please enter a location name")
        
        # Try geocoding with fallback
        if geocoding.api_key:
            print(f"   🔍 Looking up coordinates for '{location_name}'...")
            
            if geocoding.api_key == "mock_key":
                # Mock geocoding for testing
                geocode_result = {
                    "success": True,
                    "latitude": 13.049953 + (i * 0.1),
                    "longitude": 80.282403 + (i * 0.1),
                    "formatted_address": f"{location_name}, India",
                    "country": "India"
                }
            else:
                # Try geocoding with fallback
                geocode_result = geocoding.geocode_with_fallback(location_name)
            
            if geocode_result["success"]:
                source_info = ""
                if geocode_result.get("source") == "fallback_database":
                    source_info = " (from fallback database)"
                
                print(f"   ✅ Found: {geocode_result['formatted_address']}{source_info}")
                print(f"   📍 Coordinates: {geocode_result['latitude']:.6f}, {geocode_result['longitude']:.6f}")
                
                # Ask user to confirm
                confirm = input(f"   🤔 Use this location? (y/n): ").strip().lower()
                if confirm == 'y':
                    locations.append({
                        "name": location_name,
                        "latitude": geocode_result['latitude'],
                        "longitude": geocode_result['longitude'],
                        "country": geocode_result['country'],
                        "formatted_address": geocode_result['formatted_address']
                    })
                    continue
                else:
                    print("   📝 Please try a different location name or enter coordinates manually")
                    continue
            else:
                print(f"   ❌ {geocode_result['error']}")
                print("   📝 You can enter coordinates manually or try a different location name")
        
        # Manual coordinate entry
        print(f"   📍 Enter coordinates manually:")
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
            "name": location_name,
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
        # Get user input with geocoding
        trip_details = get_user_input_with_geocoding()
        
        # Display summary
        print(f"\n📋 Trip Summary:")
        print(f"   Dates: {trip_details['start_date']} to {trip_details['end_date']}")
        print(f"   Locations: {len(trip_details['locations'])}")
        for i, loc in enumerate(trip_details['locations'], 1):
            if 'formatted_address' in loc:
                print(f"     {i}. {loc['formatted_address']}")
            else:
                print(f"     {i}. {loc['name']} ({loc['latitude']:.4f}, {loc['longitude']:.4f})")
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
