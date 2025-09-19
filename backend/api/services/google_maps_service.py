import requests
import os
import json
from typing import Dict, List, Optional
import time
from ..utils.geo import haversine_distance_meters

class GoogleMapsService:
    """
    A service to interact with various Google Maps APIs.
    """
    
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_MAPS_API_KEY")
        self.base_url = "https://maps.googleapis.com/maps/api"
        self.cache = {}
        self.cache_duration = 3600 # 1 hour
    
    def _make_request(self, endpoint: str, params: Dict) -> Optional[Dict]:
        """
        Internal function to make a GET request to a Google Maps API endpoint.
        """
        if not self.api_key:
            print("Warning: GOOGLE_MAPS_API_KEY not set. Cannot make API calls.")
            return None
            
        params['key'] = self.api_key
        
        url = f"{self.base_url}/{endpoint}"
        
        # Check cache
        cache_key = json.dumps({ 'url': url, 'params': params }, sort_keys=True)
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.cache_duration:
                print("Cache hit for Google Maps API.")
                return cached_data
                
        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'OK' or data.get('status') == 'ZERO_RESULTS':
                    self.cache[cache_key] = (data, time.time())
                    return data
                else:
                    error_msg = data.get('error_message', 'Unknown error')
                    error_status = data.get('status', 'Unknown status')
                    print(f"Google Maps API error: {error_status} - {error_msg}")
                    print(f"Full API response: {data}")
                    return None
            else:
                print(f"HTTP Error: {response.status_code} - {response.text}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"Request Error: {e}")
            return None
    
    def reverse_geocode(self, lat: float, lon: float) -> Optional[Dict]:
        """
        Reverse geocoding to get a readable address from coordinates.
        """
        params = {
            'latlng': f"{lat},{lon}",
        }
        
        response = self._make_request('geocode/json', params)
        if response and response.get('results'):
            return response['results'][0]
        return None

    def geocode(self, address: str) -> Optional[Dict]:
        """
        Forward geocoding to get coordinates from an address/location string.
        Enhanced to be more precise for landmarks and specific locations.
        Returns the first result dict from Google API or None.
        """
        params = {
            'address': address,
            'region': 'in',  # Bias towards India
            'components': 'country:IN',  # Restrict to India
        }
        response = self._make_request('geocode/json', params)
        if response and response.get('results'):
            # Prefer results with more specific location types
            results = response['results']
            for result in results:
                types = result.get('types', [])
                # Prefer specific location types over administrative areas
                if any(t in types for t in ['establishment', 'point_of_interest', 'tourist_attraction', 'park', 'hospital', 'school']):
                    return result
            # Fall back to first result if no specific type found
            return results[0]
        return None

    def search_places_detailed(self, query: str, location: str = "Chennai, India") -> Optional[Dict]:
        """
        Search for places using Google Places API for more accurate results.
        """
        params = {
            'query': f"{query} {location}",
            'fields': 'place_id,name,geometry,formatted_address,types',
        }
        response = self._make_request('place/textsearch/json', params)
        if response and response.get('results'):
            results = response['results']
            # Prefer results with specific location types
            for result in results:
                types = result.get('types', [])
                if any(t in types for t in ['establishment', 'point_of_interest', 'tourist_attraction', 'park', 'hospital', 'school']):
                    return result
            return results[0]
        return None
        
    def search_places(self, query: str, location: Optional[str] = None, radius: int = 1000) -> List[Dict]:
        """
        Text Search for places.
        """
        params = {
            'query': query,
        }
        if location:
            params['location'] = location
            params['radius'] = radius
        
        response = self._make_request('place/textsearch/json', params)
        if response and response.get('results'):
            return response['results']
        return []
    
    def get_place_details(self, place_id: str, fields: str = None) -> Optional[Dict]:
        """
        Get detailed information about a place with customizable fields.
        
        Args:
            place_id: Google Place ID
            fields: Comma-separated list of fields to return (e.g., 'name,rating,formatted_phone_number,opening_hours')
        """
        if not fields:
            # Default fields for safety scoring
            fields = 'place_id,name,rating,user_ratings_total,formatted_address,geometry,types,opening_hours,formatted_phone_number,website,photos'
        
        params = {
            'place_id': place_id,
            'fields': fields
        }
        
        response = self._make_request('place/details/json', params)
        if response and response.get('result'):
            return response['result']
        return None

    def get_enhanced_nearby_places_with_details(self, lat: float, lon: float, radius: int, 
                                              place_type: str, max_results: int = 5) -> List[Dict]:
        """
        Get nearby places with enhanced details including ratings, photos, and opening hours.
        More efficient than separate calls for each place.
        """
        # First get basic nearby places
        places = self.get_nearby_places(lat, lon, radius, place_type, rankby='distance')
        
        if not places:
            return []
        
        # Limit results to avoid too many API calls
        places = places[:max_results]
        
        # Get detailed information for each place
        enhanced_places = []
        for place in places:
            place_id = place.get('place_id')
            if place_id:
                details = self.get_place_details(place_id)
                if details:
                    # Merge basic info with detailed info
                    enhanced_place = {**place, **details}
                    enhanced_places.append(enhanced_place)
                else:
                    enhanced_places.append(place)
        
        return enhanced_places

    def search_multiple_place_types(self, lat: float, lon: float, radius: int, 
                                   place_types: List[str], keyword: str = None) -> Dict[str, List[Dict]]:
        """
        Search for multiple place types efficiently using parallel requests.
        Returns a dictionary with place_type as key and list of places as value.
        """
        import concurrent.futures
        import threading
        
        results = {}
        
        def search_place_type(place_type):
            places = self.get_nearby_places(
                lat, lon, radius, place_type, 
                keyword=keyword, rankby='distance'
            )
            return place_type, places
        
        # Use ThreadPoolExecutor for parallel requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_type = {
                executor.submit(search_place_type, place_type): place_type 
                for place_type in place_types
            }
            
            for future in concurrent.futures.as_completed(future_to_type):
                place_type, places = future.result()
                results[place_type] = places
        
        return results
        
    def get_nearby_places(self, lat: float, lon: float, radius: int, place_type: str, 
                         keyword: str = None, rankby: str = 'distance', 
                         min_price: int = None, max_price: int = None) -> List[Dict]:
        """
        Finds nearby places of a specific type with advanced Google Maps features.
        
        Args:
            lat: Latitude
            lon: Longitude  
            radius: Search radius in meters (max 50000)
            place_type: Type of place to search for
            keyword: Additional keyword to refine search
            rankby: 'distance' or 'prominence' for result ranking
            min_price: Minimum price level (0-4)
            max_price: Maximum price level (0-4)
        """
        params = {
            'location': f"{lat},{lon}",
            'radius': min(radius, 50000),  # Google's max radius
            'type': place_type,
        }
        
        # Add optional parameters
        if keyword:
            params['keyword'] = keyword
        if rankby:
            params['rankby'] = rankby
        if min_price is not None:
            params['minprice'] = min_price
        if max_price is not None:
            params['maxprice'] = max_price
            
        response = self._make_request('place/nearbysearch/json', params)
        if response and response.get('results'):
            return response['results']
        return []

    def get_comprehensive_nearby_places(self, lat: float, lon: float, radius: int = 1000) -> Dict:
        """
        Gets comprehensive nearby places data for safety scoring using multiple place types.
        Uses Google Maps' advanced features and parallel processing for better efficiency.
        """
        # Define place types for safety scoring
        safety_place_types = {
            'emergency_services': ['police', 'hospital', 'fire_station'],
            'transportation': ['bus_station', 'train_station', 'transit_station', 'subway_station'],
            'public_amenities': ['park', 'library', 'school', 'university'],
            'commercial': ['shopping_mall', 'store', 'restaurant', 'gas_station'],
            'recreation': ['tourist_attraction', 'museum', 'zoo', 'amusement_park']
        }
        
        results = {}
        
        # Use parallel search for better efficiency
        all_place_types = []
        for place_types in safety_place_types.values():
            all_place_types.extend(place_types)
        
        # Search all place types in parallel
        search_results = self.search_multiple_place_types(lat, lon, radius, all_place_types)
        
        # Organize results by category
        for category, place_types in safety_place_types.items():
            category_places = []
            for place_type in place_types:
                if place_type in search_results:
                    category_places.extend(search_results[place_type])
            
            # Remove duplicates based on place_id
            unique_places = {}
            for place in category_places:
                place_id = place.get('place_id')
                if place_id and place_id not in unique_places:
                    unique_places[place_id] = place
            
            results[category] = {
                'count': len(unique_places),
                'places': list(unique_places.values())
            }
        
        return results

    def get_transport_data(self, lat: float, lon: float, radius: int) -> Dict:
        """
        Gets a count of bus, train, and transit stations within a radius.
        Enhanced with better filtering and ranking.
        """
        bus_stops = self.get_nearby_places(lat, lon, radius, 'bus_station', rankby='distance')
        train_stations = self.get_nearby_places(lat, lon, radius, 'train_station', rankby='distance')
        transit_stations = self.get_nearby_places(lat, lon, radius, 'transit_station', rankby='distance')
        subway_stations = self.get_nearby_places(lat, lon, radius, 'subway_station', rankby='distance')
        
        return {
            "bus_stops": len(bus_stops),
            "train_stations": len(train_stations),
            "transit_stations": len(transit_stations),
            "subway_stations": len(subway_stations),
            "total_transport": len(bus_stops) + len(train_stations) + len(transit_stations) + len(subway_stations)
        }
        
    def get_location_safety_indicators(self, lat: float, lon: float, radius: int) -> Dict:
        """
        Gets comprehensive safety-related indicators using Google Maps advanced features.
        """
        # Get emergency services with better filtering
        police_stations = self.get_nearby_places(lat, lon, radius, 'police', rankby='distance')
        hospitals = self.get_nearby_places(lat, lon, radius, 'hospital', rankby='distance')
        fire_stations = self.get_nearby_places(lat, lon, radius, 'fire_station', rankby='distance')
        
        # Get public safety indicators
        parks = self.get_nearby_places(lat, lon, radius, 'park', rankby='distance')
        schools = self.get_nearby_places(lat, lon, radius, 'school', rankby='distance')
        libraries = self.get_nearby_places(lat, lon, radius, 'library', rankby='distance')
        
        # Get commercial activity indicators
        shopping_areas = self.get_nearby_places(lat, lon, radius, 'shopping_mall', rankby='distance')
        restaurants = self.get_nearby_places(lat, lon, radius, 'restaurant', rankby='distance')
        
        # Calculate enhanced safety scores
        emergency_score = (len(police_stations) * 3 + len(hospitals) * 2 + len(fire_stations) * 2) / 10
        public_space_score = (len(parks) * 1.5 + len(schools) * 1 + len(libraries) * 1) / 10
        activity_score = (len(shopping_areas) * 1 + len(restaurants) * 0.5) / 10
        
        # Overall safety score (0-1 scale)
        overall_safety_score = min(1.0, (emergency_score + public_space_score + activity_score) / 3)
        
        return {
            "emergency_services": {
                "police_stations": len(police_stations),
                "hospitals": len(hospitals),
                "fire_stations": len(fire_stations),
                "total_emergency": len(police_stations) + len(hospitals) + len(fire_stations)
            },
            "public_spaces": {
                "parks": len(parks),
                "schools": len(schools),
                "libraries": len(libraries),
                "total_public": len(parks) + len(schools) + len(libraries)
            },
            "commercial_activity": {
                "shopping_areas": len(shopping_areas),
                "restaurants": len(restaurants),
                "total_commercial": len(shopping_areas) + len(restaurants)
            },
            "safety_scores": {
                "emergency_score": round(emergency_score, 2),
                "public_space_score": round(public_space_score, 2),
                "activity_score": round(activity_score, 2),
                "overall_safety_score": round(overall_safety_score, 2)
            }
        }

google_maps_service = GoogleMapsService()
