import os
import requests
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import time

class CrimeDataService:
    """Service for fetching and processing crime data from various sources."""
    
    def __init__(self):
        self.crime_api_url = os.getenv("CRIME_API_URL")
        self.crime_api_key = os.getenv("CRIME_API_KEY")
        self.cache = {}
        self.cache_duration = 3600  # 1 hour cache
        
    def get_crime_data(self, lat: float, lon: float, radius: float = 1000) -> Dict:
        """
        Get crime data for a specific location and radius.
        Returns crime statistics and safety score.
        """
        cache_key = f"crime_{lat}_{lon}_{radius}"
        
        # Check cache first
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.cache_duration:
                return cached_data
        
        crime_data = self._fetch_crime_data(lat, lon, radius)
        
        # Cache the result
        self.cache[cache_key] = (crime_data, time.time())
        
        return crime_data
    
    def _fetch_crime_data(self, lat: float, lon: float, radius: float) -> Dict:
        """Fetch crime data from external APIs or use mock data."""
        
        # Try to fetch from external crime API if available
        if self.crime_api_url and self.crime_api_key:
            try:
                return self._fetch_from_crime_api(lat, lon, radius)
            except Exception as e:
                print(f"⚠️ Error fetching from crime API: {e}")
        
        # Fallback to mock data based on location characteristics
        return self._generate_mock_crime_data(lat, lon, radius)
    
    def _fetch_from_crime_api(self, lat: float, lon: float, radius: float) -> Dict:
        """Fetch crime data from external crime API."""
        url = f"{self.crime_api_url}"
        params = {
            'lat': lat,
            'lon': lon,
            'radius': radius,
            'api_key': self.crime_api_key
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        return self._process_crime_api_response(data, lat, lon, radius)
    
    def _process_crime_api_response(self, data: Dict, lat: float, lon: float, radius: float) -> Dict:
        """Process crime API response into standardized format."""
        crimes = data.get('crimes', [])
        
        # Categorize crimes by type
        crime_categories = {
            'violent': 0,
            'property': 0,
            'theft': 0,
            'assault': 0,
            'other': 0
        }
        
        recent_crimes = []
        total_crimes = len(crimes)
        
        for crime in crimes:
            crime_type = crime.get('type', '').lower()
            crime_date = crime.get('date', '')
            
            # Categorize crime
            if any(keyword in crime_type for keyword in ['assault', 'violence', 'murder', 'rape']):
                crime_categories['violent'] += 1
            elif any(keyword in crime_type for keyword in ['theft', 'burglary', 'robbery']):
                crime_categories['theft'] += 1
            elif any(keyword in crime_type for keyword in ['property', 'vandalism', 'damage']):
                crime_categories['property'] += 1
            else:
                crime_categories['other'] += 1
            
            # Check if crime is recent (within last 30 days)
            if crime_date:
                try:
                    crime_datetime = datetime.fromisoformat(crime_date.replace('Z', '+00:00'))
                    if crime_datetime > datetime.now() - timedelta(days=30):
                        recent_crimes.append(crime)
                except:
                    pass
        
        # Calculate safety score based on crime data
        safety_score = self._calculate_crime_safety_score(total_crimes, crime_categories, recent_crimes, radius)
        
        return {
            'total_crimes': total_crimes,
            'recent_crimes': len(recent_crimes),
            'crime_categories': crime_categories,
            'safety_score': safety_score,
            'crime_rate_per_km2': (total_crimes / ((radius/1000) ** 2 * 3.14159)) if radius > 0 else 0,
            'recent_crime_rate': len(recent_crimes) / max(1, total_crimes) if total_crimes > 0 else 0,
            'location': {'lat': lat, 'lon': lon, 'radius': radius},
            'data_source': 'crime_api',
            'last_updated': datetime.now().isoformat()
        }
    
    def _generate_mock_crime_data(self, lat: float, lon: float, radius: float) -> Dict:
        """Generate mock crime data based on location characteristics."""
        
        # Simulate crime data based on location (this is a simplified model)
        # In a real implementation, this would use historical data, demographics, etc.
        
        # Base crime rate (crimes per km² per month)
        base_crime_rate = 2.5
        
        # Adjust based on location characteristics
        # Urban areas typically have higher crime rates
        if self._is_urban_area(lat, lon):
            base_crime_rate *= 1.5
        
        # Tourist areas might have different crime patterns
        if self._is_tourist_area(lat, lon):
            base_crime_rate *= 0.8  # Tourist areas often have better security
        
        # Calculate crimes in the given radius
        area_km2 = ((radius/1000) ** 2) * 3.14159
        total_crimes = int(base_crime_rate * area_km2)
        
        # Generate crime categories
        crime_categories = {
            'violent': int(total_crimes * 0.15),
            'property': int(total_crimes * 0.25),
            'theft': int(total_crimes * 0.35),
            'assault': int(total_crimes * 0.15),
            'other': int(total_crimes * 0.10)
        }
        
        # Recent crimes (last 30 days)
        recent_crimes_count = max(0, int(total_crimes * 0.3))
        
        # Calculate safety score
        safety_score = self._calculate_crime_safety_score(total_crimes, crime_categories, [], radius)
        
        return {
            'total_crimes': total_crimes,
            'recent_crimes': recent_crimes_count,
            'crime_categories': crime_categories,
            'safety_score': safety_score,
            'crime_rate_per_km2': base_crime_rate,
            'recent_crime_rate': recent_crimes_count / max(1, total_crimes) if total_crimes > 0 else 0,
            'location': {'lat': lat, 'lon': lon, 'radius': radius},
            'data_source': 'mock_data',
            'last_updated': datetime.now().isoformat()
        }
    
    def _is_urban_area(self, lat: float, lon: float) -> bool:
        """Determine if location is in an urban area (simplified)."""
        # This is a simplified check - in reality, you'd use proper urban area data
        # For now, we'll use a basic heuristic based on coordinates
        return True  # Assume urban for now
    
    def _is_tourist_area(self, lat: float, lon: float) -> bool:
        """Determine if location is in a tourist area (simplified)."""
        # This is a simplified check - in reality, you'd use tourist attraction data
        return False  # Assume not tourist area for now
    
    def _calculate_crime_safety_score(self, total_crimes: int, crime_categories: Dict, 
                                    recent_crimes: List, radius: float) -> float:
        """Calculate safety score based on crime data (0-1 scale, higher is safer)."""
        
        if total_crimes == 0:
            return 0.9  # Very safe if no crimes
        
        # Base score starts high and decreases with crime
        base_score = 0.9
        
        # Penalize based on total crimes (normalized by area)
        area_km2 = ((radius/1000) ** 2) * 3.14159
        crime_density = total_crimes / max(area_km2, 0.1)
        
        # Reduce score based on crime density
        if crime_density > 10:
            base_score -= 0.4
        elif crime_density > 5:
            base_score -= 0.3
        elif crime_density > 2:
            base_score -= 0.2
        elif crime_density > 1:
            base_score -= 0.1
        
        # Penalize violent crimes more heavily
        violent_ratio = crime_categories.get('violent', 0) / max(total_crimes, 1)
        if violent_ratio > 0.3:
            base_score -= 0.3
        elif violent_ratio > 0.2:
            base_score -= 0.2
        elif violent_ratio > 0.1:
            base_score -= 0.1
        
        # Penalize recent crimes
        recent_ratio = len(recent_crimes) / max(total_crimes, 1)
        if recent_ratio > 0.5:
            base_score -= 0.2
        elif recent_ratio > 0.3:
            base_score -= 0.1
        
        return max(0.0, min(1.0, base_score))
    
    def get_crime_statistics_summary(self, lat: float, lon: float, radius: float = 1000) -> Dict:
        """Get a summary of crime statistics for display."""
        crime_data = self.get_crime_data(lat, lon, radius)
        
        return {
            'total_crimes': crime_data['total_crimes'],
            'recent_crimes': crime_data['recent_crimes'],
            'crime_rate_per_km2': round(crime_data['crime_rate_per_km2'], 2),
            'safety_score': round(crime_data['safety_score'], 2),
            'safety_level': self._get_safety_level(crime_data['safety_score']),
            'top_crime_type': max(crime_data['crime_categories'].items(), key=lambda x: x[1])[0] if crime_data['crime_categories'] else 'none',
            'data_source': crime_data['data_source'],
            'last_updated': crime_data['last_updated']
        }
    
    def _get_safety_level(self, safety_score: float) -> str:
        """Convert safety score to human-readable level."""
        if safety_score >= 0.8:
            return "Very Safe"
        elif safety_score >= 0.6:
            return "Safe"
        elif safety_score >= 0.4:
            return "Moderate"
        elif safety_score >= 0.2:
            return "Caution"
        else:
            return "High Risk"


# Global crime service instance
crime_service = CrimeDataService()
