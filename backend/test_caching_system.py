#!/usr/bin/env python3
"""
Test script to demonstrate the caching system for safety factors
"""

import os
import sys
import django

# Add the backend directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'safetyscore.settings')
django.setup()

from api.services.osm_service import get_location_safety_summary, fetch_osm_or_local

def test_caching_system():
    """Test the caching system for safety factors"""
    
    print("🧪 Testing Safety Factors Caching System")
    print("=" * 50)
    
    # Test locations
    test_locations = [
        (12.9716, 77.5946, 1000, "Bangalore"),  # Bangalore
        (13.0827, 80.2707, 1000, "Chennai"),    # Chennai
        (28.7041, 77.1025, 1000, "Delhi"),      # Delhi
    ]
    
    for lat, lon, radius, city in test_locations:
        print(f"\n📍 Testing {city} ({lat}, {lon}) with radius {radius}m")
        print("-" * 40)
        
        # Test individual dataset caching
        print("🔍 Testing individual dataset caching...")
        datasets = ['police_stations', 'openness_factors', 'transport_factors']
        
        for dataset in datasets:
            print(f"  📊 Fetching {dataset}...")
            data = fetch_osm_or_local(dataset, lat, lon, radius)
            features = data.get('features', [])
            print(f"    ✅ Found {len(features)} features")
        
        # Test comprehensive safety summary
        print("📋 Testing comprehensive safety summary...")
        summary = get_location_safety_summary(lat, lon, radius)
        
        print(f"  📊 Safety Summary for {city}:")
        for factor, data in summary['safety_factors'].items():
            count = data.get('count', 0)
            source = data.get('data_source', 'unknown')
            print(f"    {factor}: {count} features ({source})")
        
        print(f"  ⏰ Summary timestamp: {summary['timestamp']}")
    
    print("\n🎯 Caching System Test Complete!")
    print("\n💡 Benefits:")
    print("  • Faster response times for repeated locations")
    print("  • Offline access to previously fetched data")
    print("  • Reduced API calls and costs")
    print("  • 24-hour cache validity")
    print("  • Automatic cache cleanup (keeps last 100 entries per dataset)")

if __name__ == "__main__":
    test_caching_system()
