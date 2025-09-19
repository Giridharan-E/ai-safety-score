import os
import json
from typing import Dict, Any, List
from .geojson_service import geojson_service
from .google_maps_service import google_maps_service
from ..utils.geojson_utils import load_geojson, filter_points_in_radius, haversine_m

class HybridDataService:
    """
    A service to combine and enhance data from multiple sources (GeoJSON and Google Maps).
    """

    def __init__(self):
        # Data types to be fetched from local GeoJSON files
        self.geojson_types = ['parks', 'police_stations', 'streetlights', 'sidewalks']
        # Data types to be fetched from Google Maps
        self.google_maps_types = {
            'businesses': 'establishment',
            'hospitals': 'hospital',
            'transport_facilities': 'bus_station,train_station,transit_station'
        }

    def get_enhanced_location_data(self, lat: float, lon: float, radius: float) -> Dict[str, Any]:
        """
        Combines location data from GeoJSON files and Google Maps.
        """
        enhanced_data = {}
        total_features = 0
        data_sources = {'geojson': False, 'google_maps': False}

        # Fetch from GeoJSON files
        for data_type in self.geojson_types:
            geojson_features = load_geojson(f"{data_type}.geojson").get("features", [])
            nearby_features = filter_points_in_radius(lat, lon, radius, geojson_features)
            
            # GeoJSON coordinates are [lon, lat], convert to [lat, lon] for consistency
            for f in nearby_features:
                if f.get('geometry', {}).get('type') == 'Point':
                    f['coordinates'] = {'lat': f['geometry']['coordinates'][1], 'lng': f['geometry']['coordinates'][0]}
                f['source'] = 'geojson'

            enhanced_data[data_type] = nearby_features
            total_features += len(nearby_features)
            if nearby_features:
                data_sources['geojson'] = True

        # Fetch from Google Maps
        for data_type, google_type in self.google_maps_types.items():
            places = google_maps_service.get_nearby_places(lat, lon, int(radius), google_type)
            if places:
                data_sources['google_maps'] = True
            
            # Extract and format relevant information
            formatted_places = []
            for place in places:
                geom = place.get('geometry', {}).get('location', {})
                if geom:
                    formatted_places.append({
                        'name': place.get('name', 'Unnamed'),
                        'coordinates': {'lat': geom.get('lat'), 'lng': geom.get('lng')},
                        'properties': place,
                        'source': 'google_maps'
                    })
            enhanced_data[data_type] = formatted_places
            total_features += len(formatted_places)

        return {
            "total_features": total_features,
            "data_sources": data_sources,
            **enhanced_data
        }
        
    def get_enhanced_transport_data(self, lat: float, lon: float, radius: float) -> Dict[str, Any]:
        """
        Combines and scores transport data.
        """
        data = self.get_enhanced_location_data(lat, lon, radius)
        
        bus_stops_count = len(data.get('bus_stops', []))
        train_stations_count = len(data.get('train_stations', []))
        transit_stations_count = bus_stops_count + train_stations_count
        
        # Simple heuristic for accessibility score
        accessibility_score = min(transit_stations_count / 10, 1.0) * 10
        transport_density = transit_stations_count / (math.pi * (radius / 1000)**2) if radius > 0 else 0

        data_sources = {'geojson': False, 'google_maps': False}
        if bus_stops_count > 0 or train_stations_count > 0:
            data_sources['google_maps'] = True # Assuming bus/train data comes from Google

        return {
            'bus_stops': bus_stops_count,
            'train_stations': train_stations_count,
            'transit_stations': transit_stations_count,
            'accessibility_score': accessibility_score,
            'transport_density': transport_density,
            'data_sources': data_sources
        }

    def get_enhanced_natural_surveillance(self, lat: float, lon: float, radius: float) -> Dict[str, Any]:
        """
        Combines and scores natural surveillance data.
        """
        data = self.get_enhanced_location_data(lat, lon, radius)
        
        streetlights_count = len(data.get('streetlights', []))
        sidewalks_count = len(data.get('sidewalks', []))
        businesses_count = len(data.get('businesses', []))
        
        # Heuristics for scoring
        lighting_score = min(streetlights_count / 20, 1.0) * 10
        sidewalk_score = min(sidewalks_count / 10, 1.0) * 10
        businesses_score = min(businesses_count / 50, 1.0) * 10
        
        natural_surveillance_score = (lighting_score + sidewalk_score + businesses_score) / 3
        visibility_score = (lighting_score + sidewalk_score) / 2
        
        data_sources = {'geojson': False, 'google_maps': False}
        if streetlights_count > 0 or sidewalks_count > 0:
            data_sources['geojson'] = True
        if businesses_count > 0:
            data_sources['google_maps'] = True

        return {
            'streetlights_count': streetlights_count,
            'working_lights_count': streetlights_count, # Simplified, as we don't have working status in generic data
            'sidewalks_count': sidewalks_count,
            'businesses_count': businesses_count,
            'natural_surveillance_score': natural_surveillance_score,
            'visibility_score': visibility_score,
            'data_sources': data_sources
        }

hybrid_data_service = HybridDataService()
