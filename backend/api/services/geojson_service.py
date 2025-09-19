import json
import os
import math
import time
import requests
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from ..utils.geo import haversine_distance_meters
from ..utils.geojson_utils import load_geojson, filter_points_in_radius, get_feature_safety_score

class GeoJSONService:
    """Enhanced service for processing and serving GeoJSON data."""
    
    def __init__(self):
        self.data_dir = Path(__file__).resolve().parent.parent / "data"
        self.cache = {}
        # Set a longer cache duration for remote API calls to avoid rate limits
        self.cache_duration = 3600  # 1 hour cache
        # Add a placeholder for your government API base URL
        self.crime_api_base_url = os.getenv("CRIME_API_URL")
        self.data_files = {
            'parks': 'parks.geojson',
            'police_stations': 'police_stations.geojson',
            'streetlights': 'streetlights.geojson',
            'sidewalks': 'sidewalks.geojson',
            'bus_stops': 'bus_stops.geojson',
            'train_stations': 'train_stations.geojson',
            'hospitals': 'hospitals.geojson',
            'businesses': 'businesses.geojson'
        }
        
    def load_geojson(self, data_type: str, api_key: Optional[str] = None) -> Optional[Dict]:
        """
        Load GeoJSON data with caching.
        Can load from a local file or a remote URL, with an optional API key.
        """
        if data_type in self.cache:
            cached_data, timestamp = self.cache[data_type]
            if time.time() - timestamp < self.cache_duration:
                return cached_data
        
        data = None
        # Check if we should use the API key to form the URL
        if data_type == 'crime_api' and self.crime_api_base_url and api_key:
            url = f"{self.crime_api_base_url}?api_key={api_key}"
            try:
                print(f"Fetching GeoJSON from crime API: {url}")
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                else:
                    print(f"Failed to fetch crime data from API. Status code: {response.status_code}")
                    return None
            except requests.exceptions.RequestException as e:
                print(f"Error fetching from crime API: {e}")
                return None
        elif data_type in self.data_files:
            # Fallback to loading from a local file
            file_path = self.data_dir / self.data_files[data_type]
            if not file_path.exists():
                print(f"Local GeoJSON file not found: {file_path}")
                return None
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading {self.data_files[data_type]}: {e}")
                return None
        else:
            print(f"Unknown data type: {data_type}")
            return None

        if data:
            self.cache[data_type] = (data, time.time())
        return data
    
    def get_features_within_radius(self, data_type: str, lat: float, lon: float, 
                                 radius_m: float = 250) -> List[Dict]:
        """Get features within a specified radius of a point."""
        geojson_data = self.load_geojson(data_type)
        if not geojson_data or 'features' not in geojson_data:
            return []
        
        features_within_radius = []
        
        for feature in geojson_data['features']:
            if 'geometry' not in feature or 'coordinates' not in feature['geometry']:
                continue
            
            coords = feature['geometry']['coordinates']
            
            if feature['geometry']['type'] == 'Point':
                f_lon, f_lat = coords[0], coords[1]
                distance = haversine_distance_meters(lat, lon, f_lat, f_lon)
                
                if distance <= radius_m:
                    feature_with_distance = feature.copy()
                    feature_with_distance['properties'] = feature_with_distance.get('properties', {}).copy()
                    feature_with_distance['properties']['distance_m'] = distance
                    features_within_radius.append(feature_with_distance)
                    
            elif feature['geometry']['type'] == 'Polygon':
                polygon_coords = coords[0]
                center_lon = sum(coord[0] for coord in polygon_coords) / len(polygon_coords)
                center_lat = sum(coord[1] for coord in polygon_coords) / len(polygon_coords)
                
                distance = haversine_distance_meters(lat, lon, center_lat, center_lon)
                
                if distance <= radius_m:
                    feature_with_distance = feature.copy()
                    feature_with_distance['properties'] = feature_with_distance.get('properties', {}).copy()
                    feature_with_distance['properties']['distance_m'] = distance
                    feature_with_distance['properties']['center_lat'] = center_lat
                    feature_with_distance['properties']['center_lon'] = center_lon
                    features_within_radius.append(feature_with_distance)
        
        features_within_radius.sort(key=lambda x: x['properties'].get('distance_m', float('inf')))
        return features_within_radius
    
    def get_feature_statistics(self, data_type: str, lat: float, lon: float, 
                             radius_m: float = 250) -> Dict:
        """Get statistics about features within radius."""
        features = self.get_features_within_radius(data_type, lat, lon, radius_m)
        
        if not features:
            return {
                'count': 0,
                'total_area': 0,
                'average_distance': 0,
                'closest_distance': 0,
                'feature_types': {},
                'properties_summary': {}
            }
        
        total_area = 0
        distances = []
        feature_types = {}
        properties_summary = {}
        
        for feature in features:
            distance = feature['properties'].get('distance_m', 0)
            distances.append(distance)
            
            if feature['geometry']['type'] == 'Polygon':
                area = self._calculate_polygon_area(feature['geometry']['coordinates'][0])
                total_area += area
                feature['properties']['area_sqm'] = area
            
            feature_type = feature['geometry']['type']
            feature_types[feature_type] = feature_types.get(feature_type, 0) + 1
            
            props = feature.get('properties', {})
            for key, value in props.items():
                if value is not None and value != '':
                    if key not in properties_summary:
                        properties_summary[key] = []
                    properties_summary[key].append(value)
        
        return {
            'count': len(features),
            'total_area': total_area,
            'average_distance': sum(distances) / len(distances) if distances else 0,
            'closest_distance': min(distances) if distances else 0,
            'feature_types': feature_types,
            'properties_summary': {k: list(set(v)) for k, v in properties_summary.items()},
            'features': features[:10]
        }
    
    def _calculate_polygon_area(self, coordinates: List[List[float]]) -> float:
        """Calculate area of a polygon using the shoelace formula."""
        if len(coordinates) < 3:
            return 0.0
        
        area = 0.0
        n = len(coordinates)
        
        for i in range(n):
            j = (i + 1) % n
            lat1, lon1 = coordinates[i][1], coordinates[i][0]
            lat2, lon2 = coordinates[j][1], coordinates[j][0]
            
            area += (lon1 * lat2 - lon2 * lat1)
        
        return abs(area) * 111000 * 111000 / 2
    
    def get_enhanced_features(self, data_type: str, lat: float, lon: float, 
                            radius_m: float = 250) -> Dict:
        """Get enhanced feature data with additional processing."""
        features = self.get_features_within_radius(data_type, lat, lon, radius_m)
        statistics = self.get_feature_statistics(data_type, lat, lon, radius_m)
        
        enhanced_features = []
        for feature in features:
            enhanced_feature = feature.copy()
            enhanced_feature['properties'] = feature['properties'].copy()
            
            safety_score = self._calculate_feature_safety_score(feature, data_type)
            enhanced_feature['properties']['safety_score'] = safety_score
            
            quality_score = self._calculate_feature_quality_score(feature)
            enhanced_feature['properties']['quality_score'] = quality_score
            
            enhanced_features.append(enhanced_feature)
        
        return {
            'data_type': data_type,
            'center_lat': lat,
            'center_lon': lon,
            'radius_m': radius_m,
            'statistics': statistics,
            'enhanced_features': enhanced_features,
            'safety_analysis': self._analyze_safety_impact(enhanced_features, data_type)
        }
    
    def _calculate_feature_safety_score(self, feature: Dict, data_type: str) -> float:
        """Calculate safety score for a feature based on its properties."""
        props = feature.get('properties', {})
        base_score = 0.5
        
        if data_type == 'parks':
            base_score = 0.7
            if props.get('opening_hours'):
                base_score += 0.1
            if props.get('operator') and 'corporation' in props.get('operator', '').lower():
                base_score += 0.1
            if props.get('dog') == 'yes':
                base_score += 0.05
        
        elif data_type == 'police_stations':
            base_score = 0.9
            if props.get('amenity') == 'police':
                base_score += 0.05
        
        elif data_type == 'streetlights':
            base_score = 0.8
            if props.get('status') == 'working':
                base_score += 0.1
            elif props.get('status') == 'broken':
                base_score -= 0.2
        
        elif data_type == 'sidewalks':
            base_score = 0.6
            if props.get('quality') == 'good':
                base_score += 0.2
            elif props.get('quality') == 'poor':
                base_score -= 0.2
        
        return max(0.0, min(1.0, base_score))
    
    def _calculate_feature_quality_score(self, feature: Dict) -> float:
        """Calculate quality score based on feature completeness and properties."""
        props = feature.get('properties', {})
        quality_score = 0.5
        
        essential_props = ['name', 'operator', 'opening_hours']
        for prop in essential_props:
            if props.get(prop):
                quality_score += 0.1
        
        if props.get('website') or props.get('phone'):
            quality_score += 0.1
        
        if props.get('description'):
            quality_score += 0.05
        
        return max(0.0, min(1.0, quality_score))
    
    def _analyze_safety_impact(self, features: List[Dict], data_type: str) -> Dict:
        """Analyze the overall safety impact of features in the area."""
        if not features:
            return {
                'overall_safety_score': 0.5,
                'safety_factors': [],
                'recommendations': ['No data available for this area']
            }
        
        total_weight = 0
        weighted_score = 0
        
        for feature in features:
            distance = feature['properties'].get('distance_m', 250)
            safety_score = feature['properties'].get('safety_score', 0.5)
            
            weight = max(0.1, 1.0 - (distance / 250))
            weighted_score += safety_score * weight
            total_weight += weight
        
        overall_safety_score = weighted_score / total_weight if total_weight > 0 else 0.5
        
        safety_factors = []
        if data_type == 'parks':
            if overall_safety_score > 0.7:
                safety_factors.append('Good park coverage improves area safety')
            elif overall_safety_score < 0.4:
                safety_factors.append('Limited park access may reduce safety')
        
        elif data_type == 'police_stations':
            if overall_safety_score > 0.8:
                safety_factors.append('Strong police presence in area')
            elif overall_safety_score < 0.3:
                safety_factors.append('Limited police presence')
        
        elif data_type == 'streetlights':
            if overall_safety_score > 0.7:
                safety_factors.append('Good street lighting coverage')
            elif overall_safety_score < 0.4:
                safety_factors.append('Poor street lighting may affect safety')
        
        elif data_type == 'sidewalks':
            if overall_safety_score > 0.6:
                safety_factors.append('Good pedestrian infrastructure')
            elif overall_safety_score < 0.4:
                safety_factors.append('Limited pedestrian infrastructure')
        
        recommendations = []
        if overall_safety_score < 0.4:
            recommendations.append(f'Consider improving {data_type} in this area')
        elif overall_safety_score > 0.8:
            recommendations.append(f'Excellent {data_type} coverage in this area')
        
        return {
            'overall_safety_score': overall_safety_score,
            'safety_factors': safety_factors,
            'recommendations': recommendations
        }
    
    def get_all_data_types(self) -> List[str]:
        """Get list of available GeoJSON data types."""
        available_types = []
        for file_path in self.data_dir.glob("*.geojson"):
            available_types.append(file_path.stem)
        return available_types
    
    def get_data_summary(self) -> Dict:
        """Get summary of all available GeoJSON data."""
        summary = {}
        
        for data_type in self.get_all_data_types():
            geojson_data = self.load_geojson(data_type)
            if geojson_data and 'features' in geojson_data:
                features = geojson_data['features']
                summary[data_type] = {
                    'total_features': len(features),
                    'geometry_types': list(set(f.get('geometry', {}).get('type', 'unknown') for f in features)),
                    'has_properties': any(f.get('properties') for f in features),
                    'sample_properties': list(features[0].get('properties', {}).keys()) if features else []
                }
        
        return summary


# Global GeoJSON service instance
geojson_service = GeoJSONService()
