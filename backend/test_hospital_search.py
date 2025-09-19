#!/usr/bin/env python3
"""
Test script to debug hospital search issues
"""

import os
import sys
import django

# Add the backend directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'safetyscore.settings')
django.setup()

from api.services.google_maps_service import google_maps_service

def test_hospital_search():
    """Test hospital search with different coordinates"""
    
    # Test coordinates (Chennai, India)
    test_locations = [
        (12.9716, 77.5946, 1000),  # Bangalore
        (13.0827, 80.2707, 1000),  # Chennai
        (28.7041, 77.1025, 1000),  # Delhi
    ]
    
    print("🔍 Testing Hospital Search")
    print("=" * 50)
    
    # Check API key
    print(f"🔑 Google Maps API Key available: {bool(google_maps_service.api_key)}")
    if not google_maps_service.api_key:
        print("❌ No Google Maps API key found!")
        return
    
    for lat, lon, radius in test_locations:
        print(f"\n📍 Testing location: ({lat}, {lon}) with radius {radius}m")
        
        try:
            # Test hospital search
            hospitals = google_maps_service.get_nearby_places(lat, lon, radius, 'hospital')
            print(f"🏥 Hospitals found: {len(hospitals) if isinstance(hospitals, list) else 'Not a list'}")
            
            if isinstance(hospitals, list) and len(hospitals) > 0:
                print("🏥 Hospital details:")
                for i, hospital in enumerate(hospitals[:3]):  # Show first 3
                    print(f"  {i+1}. {hospital.get('name', 'Unknown')} - {hospital.get('vicinity', 'Unknown location')}")
                    print(f"     Types: {hospital.get('types', [])}")
            else:
                print("🏥 No hospitals found, trying alternative searches...")
                
                # Try alternative searches
                alternatives = ['health', 'doctor', 'clinic', 'medical_center']
                for alt_type in alternatives:
                    alt_results = google_maps_service.get_nearby_places(lat, lon, radius, alt_type)
                    if isinstance(alt_results, list) and len(alt_results) > 0:
                        print(f"🏥 Found {len(alt_results)} {alt_type} facilities")
                        break
                else:
                    print("🏥 No health facilities found with any search term")
                    
        except Exception as e:
            print(f"❌ Error searching for hospitals: {e}")

if __name__ == "__main__":
    test_hospital_search()
