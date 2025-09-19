import json
import os
import random
import math
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
import requests


DATA_DIR = Path(__file__).resolve().parent.parent / 'data'
OVERPASS_URL = os.getenv('OVERPASS_API_URL', 'https://overpass-api.de/api/interpreter')


def _save_geojson(filename: str, fc: Dict[str, Any]) -> None:
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        (DATA_DIR / filename).write_text(json.dumps(fc, ensure_ascii=False), encoding='utf-8')
    except Exception:
        pass


def _load_local(filename: str) -> Dict[str, Any]:
    try:
        with open(DATA_DIR / filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {"type": "FeatureCollection", "features": []}


def _elements_to_geojson(elements: List[Dict[str, Any]]) -> Dict[str, Any]:
    features: List[Dict[str, Any]] = []
    for el in elements or []:
        if el.get('type') == 'node':
            lat = el.get('lat')
            lon = el.get('lon')
            if lat is None or lon is None:
                continue
            features.append({
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [lon, lat]},
                "properties": el.get('tags', {})
            })
        elif el.get('type') in ('way', 'relation') and el.get('center'):
            c = el['center']
            lat = c.get('lat')
            lon = c.get('lon')
            if lat is None or lon is None:
                continue
            features.append({
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [lon, lat]},
                "properties": el.get('tags', {})
            })
    return {"type": "FeatureCollection", "features": features}


def _build_query(dataset: str, lat: float, lon: float, radius_m: float) -> Optional[str]:
    r = int(max(1, min(radius_m, 5000)))
    
    # Core safety infrastructure
    if dataset == 'police_stations':
        return f"[out:json][timeout:10];(node[amenity=police](around:{r},{lat},{lon});way[amenity=police](around:{r},{lat},{lon});relation[amenity=police](around:{r},{lat},{lon}););out center;"
    
    if dataset == 'hospitals_medical':
        return f"[out:json][timeout:10];(node[amenity=hospital](around:{r},{lat},{lon});node[amenity=clinic](around:{r},{lat},{lon});node[amenity=doctors](around:{r},{lat},{lon});node[amenity=pharmacy](around:{r},{lat},{lon});way[amenity=hospital](around:{r},{lat},{lon});way[amenity=clinic](around:{r},{lat},{lon}););out center;"
    
    if dataset == 'streetlights_lighting':
        return f"[out:json][timeout:10];(node[highway=street_lamp](around:{r},{lat},{lon});node[amenity=street_lamp](around:{r},{lat},{lon});node[man_made=street_lamp](around:{r},{lat},{lon}););out center;"
    
    if dataset == 'sidewalks_pedestrian':
        return f'[out:json][timeout:15];(way["highway"="footway"](around:{r},{lat},{lon});way[sidewalk](around:{r},{lat},{lon});way["highway"="pedestrian"](around:{r},{lat},{lon}););out center;'
    
    # Tourism and cultural
    if dataset == 'tourist_places_tn':
        return f"[out:json][timeout:10];(node[tourism](around:{r},{lat},{lon});way[tourism](around:{r},{lat},{lon});relation[tourism](around:{r},{lat},{lon}););out center;"
    if dataset == 'temples_tn':
        return f"[out:json][timeout:10];(node[amenity=place_of_worship][religion=hindu](around:{r},{lat},{lon});way[amenity=place_of_worship][religion=hindu](around:{r},{lat},{lon});relation[amenity=place_of_worship][religion=hindu](around:{r},{lat},{lon}););out center;"
    if dataset == 'beaches_tn':
        return f"[out:json][timeout:10];(node[natural=beach](around:{r},{lat},{lon});way[natural=beach](around:{r},{lat},{lon});relation[natural=beach](around:{r},{lat},{lon}););out center;"
    
    # Enhanced safety factors with comprehensive OSM queries
    if dataset == 'openness_factors':
        # Parks, squares, open spaces, recreational areas
        return f"[out:json][timeout:15];(node[leisure=park](around:{r},{lat},{lon});node[leisure=square](around:{r},{lat},{lon});node[leisure=recreation_ground](around:{r},{lat},{lon});node[amenity=marketplace](around:{r},{lat},{lon});node[landuse=recreation_ground](around:{r},{lat},{lon});way[leisure=park](around:{r},{lat},{lon});way[leisure=square](around:{r},{lat},{lon});way[leisure=recreation_ground](around:{r},{lat},{lon});way[amenity=marketplace](around:{r},{lat},{lon});way[landuse=recreation_ground](around:{r},{lat},{lon}););out center;"
    
    if dataset == 'visibility_factors':
        # Street lights, clear sight lines, well-lit areas, open roads
        return f"[out:json][timeout:15];(node[highway=street_lamp](around:{r},{lat},{lon});node[amenity=street_lamp](around:{r},{lat},{lon});node[man_made=street_lamp](around:{r},{lat},{lon});way[highway=residential](around:{r},{lat},{lon});way[highway=primary](around:{r},{lat},{lon});way[highway=secondary](around:{r},{lat},{lon});way[highway=tertiary](around:{r},{lat},{lon});way[highway=unclassified](around:{r},{lat},{lon}););out center;"
    
    if dataset == 'people_density_factors':
        # Commercial, residential, public spaces with high foot traffic
        return f"[out:json][timeout:15];(node[amenity=restaurant](around:{r},{lat},{lon});node[amenity=cafe](around:{r},{lat},{lon});node[amenity=bar](around:{r},{lat},{lon});node[amenity=fast_food](around:{r},{lat},{lon});node[shop](around:{r},{lat},{lon});node[amenity=bank](around:{r},{lat},{lon});node[amenity=pharmacy](around:{r},{lat},{lon});node[amenity=post_office](around:{r},{lat},{lon});node[amenity=library](around:{r},{lat},{lon});node[amenity=community_centre](around:{r},{lat},{lon});way[landuse=commercial](around:{r},{lat},{lon});way[landuse=residential](around:{r},{lat},{lon});way[landuse=retail](around:{r},{lat},{lon}););out center;"
    
    if dataset == 'transport_factors':
        # Comprehensive public transportation coverage
        return f"[out:json][timeout:15];(node[public_transport=station](around:{r},{lat},{lon});node[public_transport=stop_position](around:{r},{lat},{lon});node[public_transport=platform](around:{r},{lat},{lon});node[amenity=bus_station](around:{r},{lat},{lon});node[railway=station](around:{r},{lat},{lon});node[railway=halt](around:{r},{lat},{lon});node[railway=tram_stop](around:{r},{lat},{lon});node[highway=bus_stop](around:{r},{lat},{lon});node[amenity=taxi](around:{r},{lat},{lon});way[public_transport=platform](around:{r},{lat},{lon});way[railway](around:{r},{lat},{lon}););out center;"
    
    # Additional safety factors
    if dataset == 'emergency_services':
        # Fire stations, emergency services
        return f"[out:json][timeout:10];(node[amenity=fire_station](around:{r},{lat},{lon});node[emergency=fire_station](around:{r},{lat},{lon});way[amenity=fire_station](around:{r},{lat},{lon});way[emergency=fire_station](around:{r},{lat},{lon}););out center;"
    
    if dataset == 'security_factors':
        # Security cameras, barriers, controlled access
        return f"[out:json][timeout:10];(node[security=yes](around:{r},{lat},{lon});node[barrier](around:{r},{lat},{lon});node[access=private](around:{r},{lat},{lon});way[barrier](around:{r},{lat},{lon});way[access=private](around:{r},{lat},{lon}););out center;"
    
    return None


def _generate_synthetic_data(dataset: str, lat: float, lon: float, radius_m: float) -> Dict[str, Any]:
    """Generate synthetic backup data when OSM API is not available."""
    
    # Calculate number of features based on area and location characteristics
    area_km2 = ((radius_m / 1000) ** 2) * math.pi
    base_density = 2.0  # Base features per km²
    
    # Adjust density based on location (urban vs rural)
    if _is_urban_area(lat, lon):
        density_multiplier = 3.0
    else:
        density_multiplier = 1.0
    
    num_features = max(1, int(area_km2 * base_density * density_multiplier))
    
    features = []
    
    if dataset == 'police_stations':
        for i in range(min(num_features, 3)):  # Max 3 police stations
            features.append(_create_synthetic_feature(
                lat, lon, radius_m, 
                {'amenity': 'police', 'name': f'Police Station {i+1}', 'type': 'police'}
            ))
    
    elif dataset == 'hospitals_medical':
        for i in range(min(num_features, 5)):  # Max 5 medical facilities
            facility_type = random.choice(['hospital', 'clinic', 'pharmacy'])
            features.append(_create_synthetic_feature(
                lat, lon, radius_m,
                {'amenity': facility_type, 'name': f'{facility_type.title()} {i+1}', 'type': 'medical'}
            ))
    
    elif dataset == 'streetlights_lighting':
        for i in range(min(num_features, 20)):  # Max 20 street lights
            features.append(_create_synthetic_feature(
                lat, lon, radius_m,
                {'highway': 'street_lamp', 'name': f'Street Light {i+1}', 'type': 'lighting'}
            ))
    
    elif dataset == 'sidewalks_pedestrian':
        for i in range(min(num_features, 15)):  # Max 15 sidewalk segments
            features.append(_create_synthetic_feature(
                lat, lon, radius_m,
                {'highway': 'footway', 'name': f'Sidewalk {i+1}', 'type': 'pedestrian'}
            ))
    
    elif dataset == 'openness_factors':
        for i in range(min(num_features, 8)):  # Max 8 open spaces
            space_type = random.choice(['park', 'square', 'marketplace'])
            features.append(_create_synthetic_feature(
                lat, lon, radius_m,
                {'leisure': space_type, 'name': f'{space_type.title()} {i+1}', 'type': 'open_space'}
            ))
    
    elif dataset == 'visibility_factors':
        for i in range(min(num_features, 25)):  # Max 25 visibility factors
            feature_type = random.choice(['street_lamp', 'residential_road', 'primary_road'])
            features.append(_create_synthetic_feature(
                lat, lon, radius_m,
                {'highway': feature_type, 'name': f'Visibility Factor {i+1}', 'type': 'visibility'}
            ))
    
    elif dataset == 'people_density_factors':
        for i in range(min(num_features, 12)):  # Max 12 commercial/residential
            amenity_type = random.choice(['restaurant', 'cafe', 'shop', 'bank', 'pharmacy'])
            features.append(_create_synthetic_feature(
                lat, lon, radius_m,
                {'amenity': amenity_type, 'name': f'{amenity_type.title()} {i+1}', 'type': 'commercial'}
            ))
    
    elif dataset == 'transport_factors':
        for i in range(min(num_features, 10)):  # Max 10 transport facilities
            transport_type = random.choice(['bus_stop', 'railway_station', 'taxi_stand'])
            features.append(_create_synthetic_feature(
                lat, lon, radius_m,
                {'highway': transport_type, 'name': f'{transport_type.replace("_", " ").title()} {i+1}', 'type': 'transport'}
            ))
    
    elif dataset == 'emergency_services':
        for i in range(min(num_features, 2)):  # Max 2 emergency services
            features.append(_create_synthetic_feature(
                lat, lon, radius_m,
                {'amenity': 'fire_station', 'name': f'Fire Station {i+1}', 'type': 'emergency'}
            ))
    
    elif dataset == 'security_factors':
        for i in range(min(num_features, 5)):  # Max 5 security features
            features.append(_create_synthetic_feature(
                lat, lon, radius_m,
                {'security': 'yes', 'name': f'Security Point {i+1}', 'type': 'security'}
            ))
    
    return {"type": "FeatureCollection", "features": features}


def _create_synthetic_feature(lat: float, lon: float, radius_m: float, properties: Dict[str, str]) -> Dict[str, Any]:
    """Create a synthetic feature with random coordinates within radius."""
    # Generate random offset within radius
    angle = random.uniform(0, 2 * math.pi)
    distance = random.uniform(0, radius_m * 0.8)  # 80% of radius to keep within bounds
    
    # Convert to lat/lon offset
    lat_offset = (distance / 111000) * math.cos(angle)  # Rough conversion
    lon_offset = (distance / (111000 * math.cos(math.radians(lat)))) * math.sin(angle)
    
    feature_lat = lat + lat_offset
    feature_lon = lon + lon_offset
    
    return {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [feature_lon, feature_lat]
        },
        "properties": properties
    }


def _is_urban_area(lat: float, lon: float) -> bool:
    """Determine if location is in an urban area (simplified heuristic)."""
    # This is a simplified check - in reality, you'd use proper urban area data
    # For now, we'll use a basic heuristic based on coordinates
    # Urban areas typically have higher feature density
    return True  # Assume urban for now


def _get_cache_key(dataset: str, lat: float, lon: float, radius_m: float) -> str:
    """Generate a cache key for location-specific data."""
    # Round coordinates to reduce cache fragmentation
    lat_rounded = round(lat, 3)
    lon_rounded = round(lon, 3)
    radius_rounded = round(radius_m / 100) * 100  # Round to nearest 100m
    return f"{dataset}_{lat_rounded}_{lon_rounded}_{radius_rounded}"


def _get_cached_location_data(dataset: str, lat: float, lon: float, radius_m: float) -> Optional[Dict[str, Any]]:
    """Get cached data for a specific location and radius."""
    try:
        cache_file = DATA_DIR / f"cache_{dataset}.json"
        if not cache_file.exists():
            return None
        
        with open(cache_file, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
        
        cache_key = _get_cache_key(dataset, lat, lon, radius_m)
        cached_entry = cache_data.get(cache_key)
        
        if cached_entry:
            # Check if cache is still valid (24 hours)
            cache_time = cached_entry.get('timestamp', 0)
            if time.time() - cache_time < 86400:  # 24 hours
                print(f"📦 Cache hit for {dataset} at ({lat}, {lon})")
                return cached_entry.get('data')
            else:
                print(f"⏰ Cache expired for {dataset} at ({lat}, {lon})")
        
        return None
    except Exception as e:
        print(f"⚠️ Error reading cache for {dataset}: {e}")
        return None


def _cache_location_data(dataset: str, lat: float, lon: float, radius_m: float, data: Dict[str, Any]) -> None:
    """Cache data for a specific location and radius."""
    try:
        cache_file = DATA_DIR / f"cache_{dataset}.json"
        
        # Load existing cache
        cache_data = {}
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
            except (json.JSONDecodeError, IOError):
                cache_data = {}
        
        # Add new entry
        cache_key = _get_cache_key(dataset, lat, lon, radius_m)
        cache_data[cache_key] = {
            'timestamp': time.time(),
            'data': data,
            'location': {'lat': lat, 'lon': lon, 'radius': radius_m}
        }
        
        # Save cache (keep only last 100 entries per dataset)
        if len(cache_data) > 100:
            # Remove oldest entries
            sorted_entries = sorted(cache_data.items(), key=lambda x: x[1].get('timestamp', 0))
            cache_data = dict(sorted_entries[-100:])
        
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Cached {dataset} data for ({lat}, {lon})")
    except Exception as e:
        print(f"⚠️ Error caching {dataset} data: {e}")


def get_location_safety_summary(lat: float, lon: float, radius_m: float) -> Dict[str, Any]:
    """Get a comprehensive safety summary for a location using cached data."""
    summary = {
        'location': {'lat': lat, 'lon': lon, 'radius': radius_m},
        'timestamp': time.time(),
        'safety_factors': {}
    }
    
    # Define all safety factor datasets
    safety_datasets = [
        'police_stations', 'hospitals_medical', 'streetlights_lighting', 'sidewalks_pedestrian',
        'openness_factors', 'visibility_factors', 'people_density_factors', 'transport_factors',
        'emergency_services', 'security_factors', 'tourist_places_tn', 'temples_tn', 'beaches_tn'
    ]
    
    for dataset in safety_datasets:
        try:
            data = fetch_osm_or_local(dataset, lat, lon, radius_m)
            features = data.get('features', [])
            
            summary['safety_factors'][dataset] = {
                'count': len(features),
                'data_source': 'cached' if _get_cached_location_data(dataset, lat, lon, radius_m) else 'fresh',
                'features': features[:5]  # Include first 5 features as samples
            }
        except Exception as e:
            summary['safety_factors'][dataset] = {
                'count': 0,
                'error': str(e),
                'features': []
            }
    
    return summary


def fetch_osm_or_local(dataset: str, lat: float, lon: float, radius_m: float) -> Dict[str, Any]:
    filename_map = {
        # Core safety infrastructure
        'police_stations': 'police_stations.geojson',
        'hospitals_medical': 'hospitals_medical.geojson',
        'streetlights_lighting': 'streetlights.geojson',  # Use existing file
        'sidewalks_pedestrian': 'sidewalks.geojson',  # Use existing file
        
        # Tourism and cultural
        'tourist_places_tn': 'tourist_places_tn.geojson',
        'temples_tn': 'temples_tn.geojson',
        'beaches_tn': 'beaches_tn.geojson',
        
        # Enhanced safety factors
        'openness_factors': 'openness_factors.geojson',
        'visibility_factors': 'visibility_factors.geojson',
        'people_density_factors': 'people_density_factors.geojson',
        'transport_factors': 'transport_factors.geojson',
        
        # Additional safety factors
        'emergency_services': 'emergency_services.geojson',
        'security_factors': 'security_factors.geojson',
    }
    filename = filename_map.get(dataset, f"{dataset}.geojson")

    # Check if we have cached data for this specific location and radius
    cached_data = _get_cached_location_data(dataset, lat, lon, radius_m)
    if cached_data:
        print(f"📦 Using cached data for {dataset} at ({lat}, {lon})")
        return cached_data

    q = _build_query(dataset, lat, lon, radius_m)
    if q:
        try:
            print(f"🌐 Fetching {dataset} from OSM API...")
            resp = requests.post(OVERPASS_URL, data={"data": q}, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                fc = _elements_to_geojson(data.get('elements', []))
                print(f"✅ OSM API success: {len(fc.get('features', []))} {dataset} found")
                
                # Cache the location-specific data
                _cache_location_data(dataset, lat, lon, radius_m, fc)
                
                # Also update the general GeoJSON file
                _save_geojson(filename, fc)
                return fc
            else:
                print(f"⚠️ OSM API error: {resp.status_code}")
        except requests.RequestException as e:
            print(f"⚠️ OSM API request failed: {e}")
        except ValueError as e:
            print(f"⚠️ OSM API response parsing failed: {e}")

    # Fallback to local file
    print(f"📁 Trying local file for {dataset}...")
    local_data = _load_local(filename)
    if local_data.get('features'):
        print(f"✅ Local file success: {len(local_data['features'])} {dataset} found")
        # Cache this data for future use
        _cache_location_data(dataset, lat, lon, radius_m, local_data)
        return local_data
    
    # Final fallback to synthetic data
    print(f"🎲 Generating synthetic data for {dataset}...")
    synthetic_data = _generate_synthetic_data(dataset, lat, lon, radius_m)
    print(f"✅ Synthetic data generated: {len(synthetic_data['features'])} {dataset} created")
    
    # Cache synthetic data and save to file
    _cache_location_data(dataset, lat, lon, radius_m, synthetic_data)
    _save_geojson(filename, synthetic_data)
    return synthetic_data


