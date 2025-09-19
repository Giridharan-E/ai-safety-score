#!/usr/bin/env python3
"""
Test script to check API endpoints
"""
import os
import sys
import django
import requests
import json

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'safetyscore.settings')
django.setup()

def test_api_endpoints():
    """Test the API endpoints to see what's happening"""
    
    print("🧪 Testing API Endpoints")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    
    # Test endpoints
    endpoints = [
        "/api/combined_data/?latitude=13.0827&longitude=80.2707&radius=800",
        "/api/feedback/list/",
        "/api/tester/"
    ]
    
    for endpoint in endpoints:
        print(f"\n🔍 Testing: {endpoint}")
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            print(f"   Status Code: {response.status_code}")
            print(f"   Content-Type: {response.headers.get('content-type', 'Unknown')}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"   ✅ JSON Response: {type(data)}")
                    if isinstance(data, dict):
                        print(f"   Keys: {list(data.keys())}")
                except json.JSONDecodeError:
                    print(f"   ❌ Not JSON - First 200 chars:")
                    print(f"   {response.text[:200]}...")
            else:
                print(f"   ❌ Error - First 200 chars:")
                print(f"   {response.text[:200]}...")
                
        except requests.exceptions.ConnectionError:
            print(f"   ❌ Connection Error - Is Django server running?")
        except requests.exceptions.Timeout:
            print(f"   ❌ Timeout Error")
        except Exception as e:
            print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    test_api_endpoints()
