#!/usr/bin/env python3
"""
Test script to demonstrate address-to-coordinates conversion flow
"""
import os
import sys
import django

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'safetyscore.settings')
django.setup()

from api.services.google_maps_service import google_maps_service

def test_address_conversion():
    """Test the address to coordinates conversion process"""
    
    print("🧪 Testing Address-to-Coordinates Conversion Flow")
    print("=" * 60)
    
    # Test addresses
    test_addresses = [
        "Marina Beach Chennai",
        "Taj Mahal Agra", 
        "Red Fort Delhi",
        "Gateway of India Mumbai"
    ]
    
    for address in test_addresses:
        print(f"\n🔍 Testing address: '{address}'")
        print("-" * 40)
        
        # Step 1: Try detailed place search
        print("1️⃣ Trying detailed place search...")
        geo = google_maps_service.search_places_detailed(address)
        
        if not geo:
            print("   ❌ Detailed search failed, trying regular geocoding...")
            # Step 2: Fallback to regular geocoding
            geo = google_maps_service.geocode(address)
        else:
            print("   ✅ Detailed search successful!")
        
        if geo:
            # Extract coordinates
            loc = geo.get('geometry', {}).get('location', {})
            if loc and 'lat' in loc and 'lng' in loc:
                lat = float(loc.get('lat'))
                lon = float(loc.get('lng'))
                resolved_address = geo.get('formatted_address', address)
                
                print(f"   📍 Coordinates: ({lat}, {lon})")
                print(f"   🏷️ Resolved address: '{resolved_address}'")
                
                # Step 3: Test reverse geocoding
                print("2️⃣ Testing reverse geocoding...")
                reverse_geo = google_maps_service.reverse_geocode(lat, lon)
                if reverse_geo:
                    reverse_address = reverse_geo.get('formatted_address', 'N/A')
                    print(f"   🔄 Reverse geocoded: '{reverse_address}'")
                
                # Step 4: Test nearby places search
                print("3️⃣ Testing nearby places search...")
                police_places = google_maps_service.get_nearby_places(lat, lon, 1000, 'police')
                hospital_places = google_maps_service.get_nearby_places(lat, lon, 1000, 'hospital')
                
                print(f"   🚔 Police stations nearby: {len(police_places)}")
                print(f"   🏥 Hospitals nearby: {len(hospital_places)}")
                
                if police_places:
                    print(f"   📍 Nearest police: {police_places[0].get('name', 'Unknown')}")
                if hospital_places:
                    print(f"   📍 Nearest hospital: {hospital_places[0].get('name', 'Unknown')}")
                
            else:
                print("   ❌ Invalid coordinates returned")
        else:
            print("   ❌ Geocoding failed completely")
        
        print("   " + "="*40)

if __name__ == "__main__":
    test_address_conversion()
