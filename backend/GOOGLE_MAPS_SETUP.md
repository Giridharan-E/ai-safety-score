# 🗺️ Google Maps API Setup Guide

## 📋 **Overview**

The Enhanced Interactive Trip Planner uses Google Maps Geocoding API to automatically convert location names to coordinates. This makes trip planning much more user-friendly!

## 🔑 **Getting a Google Maps API Key**

### **Step 1: Create a Google Cloud Project**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Sign in with your Google account
3. Click "Select a project" → "New Project"
4. Enter project name (e.g., "AI Safety Score Trip Planner")
5. Click "Create"

### **Step 2: Enable Geocoding API**
1. In the Google Cloud Console, go to "APIs & Services" → "Library"
2. Search for "Geocoding API"
3. Click on "Geocoding API"
4. Click "Enable"

### **Step 3: Create API Key**
1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "API Key"
3. Copy the generated API key
4. (Optional) Click "Restrict Key" to add restrictions for security

### **Step 4: Set Up Billing (Required)**
1. Go to "Billing" in the Google Cloud Console
2. Link a billing account to your project
3. **Note**: Geocoding API has a free tier (40,000 requests/month)

## 🔧 **Setting Up the API Key**

### **Option 1: Environment Variable (Recommended)**
```bash
# Windows (PowerShell)
$env:GOOGLE_MAPS_API_KEY="YOUR_API_KEY_HERE"

# Windows (Command Prompt)
set GOOGLE_MAPS_API_KEY=YOUR_API_KEY_HERE

# Linux/Mac
export GOOGLE_MAPS_API_KEY="YOUR_API_KEY_HERE"
```

### **Option 2: .env File**
Create a `.env` file in the backend directory:
```
GOOGLE_MAPS_API_KEY=YOUR_API_KEY_HERE
```

### **Option 3: Direct in Code (Not Recommended)**
```python
geocoding = GeocodingService(api_key="YOUR_API_KEY_HERE")
```

## 🚀 **Using the Enhanced Trip Planner**

### **Run with API Key:**
```bash
cd backend
python enhanced_interactive_trip_planner.py
```

### **Example Session:**
```
🌍 ENHANCED INTERACTIVE TRIP PLANNER
==================================================
Let's plan your trip! Please provide the following details:

📅 Start date (YYYY-MM-DD): 2024-03-15
📅 End date (YYYY-MM-DD): 2024-03-22
📍 Number of locations to visit: 2

📍 Location 1:
   Location name (e.g., 'Marina Beach Chennai'): Marina Beach Chennai
   🔍 Looking up coordinates for 'Marina Beach Chennai'...
   ✅ Found: Marina Beach, Chennai, Tamil Nadu, India
   📍 Coordinates: 13.049953, 80.282403
   🤔 Use this location? (y/n): y

📍 Location 2:
   Location name (e.g., 'Marina Beach Chennai'): Taj Mahal Agra
   🔍 Looking up coordinates for 'Taj Mahal Agra'...
   ✅ Found: Taj Mahal, Agra, Uttar Pradesh, India
   📍 Coordinates: 27.175015, 78.042155
   🤔 Use this location? (y/n): y
```

## 💰 **Pricing Information**

### **Geocoding API Pricing (as of 2024):**
- **Free Tier**: 40,000 requests/month
- **Paid Tier**: $5.00 per 1,000 requests after free tier
- **Typical Usage**: 1 request per location lookup

### **Cost Examples:**
- **10 trips with 3 locations each**: 30 requests (Free)
- **100 trips with 5 locations each**: 500 requests (Free)
- **1,000 trips with 10 locations each**: 10,000 requests (Free)

## 🔒 **Security Best Practices**

### **API Key Restrictions:**
1. **HTTP Referrers**: Restrict to your domain
2. **IP Addresses**: Restrict to your server IPs
3. **APIs**: Restrict to only Geocoding API
4. **Usage Quotas**: Set daily/monthly limits

### **Example Restrictions:**
```
Application restrictions:
- HTTP referrers: yourdomain.com/*

API restrictions:
- Geocoding API only

Quotas:
- Requests per day: 1,000
- Requests per 100 seconds: 100
```

## 🧪 **Testing Without API Key**

If you don't have an API key, the planner will:
1. **Ask if you want to use mock geocoding** (for testing)
2. **Allow manual coordinate entry**
3. **Continue with the trip planning process**

### **Mock Geocoding Example:**
```
⚠️ Google Maps API key not found.
   You can:
   1. Set GOOGLE_MAPS_API_KEY environment variable
   2. Enter coordinates manually
   3. Continue with mock geocoding (for testing)

🤔 Use mock geocoding for testing? (y/n): y

📍 Location 1:
   Location name (e.g., 'Marina Beach Chennai'): Marina Beach
   🔍 Looking up coordinates for 'Marina Beach'...
   ✅ Found: Marina Beach, India
   📍 Coordinates: 13.049953, 80.282403
   🤔 Use this location? (y/n): y
```

## 🔧 **Troubleshooting**

### **Common Issues:**

1. **"API key not found"**
   - Check if environment variable is set correctly
   - Verify the API key is valid

2. **"Geocoding API error: REQUEST_DENIED"**
   - Check if Geocoding API is enabled
   - Verify API key restrictions

3. **"No results found"**
   - Try more specific location names
   - Add country name for better results

4. **"Network error"**
   - Check internet connection
   - Verify firewall settings

### **Debug Mode:**
Add this to see detailed error messages:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📚 **Additional Resources**

- [Google Maps Geocoding API Documentation](https://developers.google.com/maps/documentation/geocoding)
- [Google Cloud Console](https://console.cloud.google.com/)
- [API Key Best Practices](https://developers.google.com/maps/api-key-best-practices)

## 🎯 **Benefits of Using Geocoding**

1. **User-Friendly**: No need to know exact coordinates
2. **Accurate**: Google's comprehensive location database
3. **Fast**: Automatic coordinate lookup
4. **Reliable**: Handles various location name formats
5. **Detailed**: Provides formatted addresses and country info

The enhanced trip planner makes it much easier for users to plan their trips by simply entering location names! 🚀
