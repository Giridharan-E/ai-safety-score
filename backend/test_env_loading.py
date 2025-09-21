#!/usr/bin/env python3
"""
Test script to verify .env file loading and Google Maps API key access.
"""

import os

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Successfully loaded .env file")
except ImportError:
    print("❌ python-dotenv not installed")
    print("   Install with: pip install python-dotenv")
    exit(1)

# Check if Google Maps API key is available
api_key = os.getenv('GOOGLE_MAPS_API_KEY')

if api_key:
    print(f"✅ Google Maps API key found!")
    print(f"   Key starts with: {api_key[:10]}...")
    print(f"   Key length: {len(api_key)} characters")
    
    # Test if the key looks valid (basic validation)
    if len(api_key) > 20 and api_key.startswith('AIza'):
        print("✅ API key format looks correct")
    else:
        print("⚠️ API key format might be incorrect")
        print("   Google Maps API keys usually start with 'AIza' and are longer than 20 characters")
else:
    print("❌ Google Maps API key not found in .env file")
    print("   Make sure your .env file contains:")
    print("   GOOGLE_MAPS_API_KEY=your_actual_api_key_here")

# Show all environment variables that start with GOOGLE
print(f"\n🔍 Environment variables starting with 'GOOGLE':")
google_vars = {k: v for k, v in os.environ.items() if k.startswith('GOOGLE')}
if google_vars:
    for key, value in google_vars.items():
        if 'KEY' in key.upper():
            print(f"   {key}: {value[:10]}...")
        else:
            print(f"   {key}: {value}")
else:
    print("   No Google-related environment variables found")

print(f"\n📁 Current working directory: {os.getcwd()}")
print(f"📄 Looking for .env file in: {os.path.join(os.getcwd(), '.env')}")

if os.path.exists('.env'):
    print("✅ .env file exists in current directory")
    try:
        with open('.env', 'r') as f:
            lines = f.readlines()
        print(f"   .env file has {len(lines)} lines")
        
        # Check if GOOGLE_MAPS_API_KEY is in the file
        has_google_key = any('GOOGLE_MAPS_API_KEY' in line for line in lines)
        if has_google_key:
            print("✅ GOOGLE_MAPS_API_KEY found in .env file")
        else:
            print("❌ GOOGLE_MAPS_API_KEY not found in .env file")
            print("   Add this line to your .env file:")
            print("   GOOGLE_MAPS_API_KEY=your_actual_api_key_here")
    except Exception as e:
        print(f"❌ Error reading .env file: {e}")
else:
    print("❌ .env file not found in current directory")
    print("   Create a .env file with:")
    print("   GOOGLE_MAPS_API_KEY=your_actual_api_key_here")
