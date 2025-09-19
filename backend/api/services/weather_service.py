import requests
import os
import json
import time
from typing import Dict, Any, Optional

# Caching for weather data
weather_cache: Dict[str, Any] = {}
CACHE_DURATION = 900  # 15 minutes

def fetch_weather(lat: float, lon: float) -> Optional[Dict]:
    """
    Fetches weather data from OpenWeatherMap API with caching.
    """
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        print("Warning: OPENWEATHER_API_KEY not set. Cannot fetch weather.")
        return None
        
    cache_key = f"{lat:.2f},{lon:.2f}"
    if cache_key in weather_cache and time.time() - weather_cache[cache_key]['timestamp'] < CACHE_DURATION:
        print("Cache hit for weather data.")
        return weather_cache[cache_key]['data']
        
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        'lat': lat,
        'lon': lon,
        'appid': api_key,
        'units': 'metric',  # For Celsius
    }
    
    try:
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            weather_data = {
                'weather_main': data['weather'][0]['main'],
                'weather_desc': data['weather'][0]['description'],
                'temperature': data['main']['temp'],
                'humidity': data['main']['humidity'],
                'wind_speed': data['wind']['speed'],
                'timestamp': time.time(),
            }
            weather_cache[cache_key] = {'data': weather_data, 'timestamp': time.time()}
            return weather_data
        else:
            print(f"Failed to fetch weather data. Status: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching weather data: {e}")
        return None
