import json
from pathlib import Path
from typing import Dict, List, Any
from .geo import haversine_distance_meters


def load_geojson(filename: str) -> Dict[str, Any]:
    """
    Load a GeoJSON file from `backend/api/data/`. Returns {} on failure.
    """
    data_dir = Path(__file__).resolve().parent.parent / 'data'
    file_path = data_dir / filename
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def filter_points_in_radius(lat: float, lon: float, radius_m: float, features: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filter GeoJSON Point features within radius (meters) using precise Haversine.
    Adds 'distance_m' into feature['properties'].
    """
    results: List[Dict[str, Any]] = []
    for feature in features or []:
        geom = feature.get('geometry') or {}
        if geom.get('type') != 'Point':
            continue
        coords = geom.get('coordinates') or []
        if len(coords) != 2:
            continue
        f_lon, f_lat = coords[0], coords[1]
        d = haversine_distance_meters(lat, lon, f_lat, f_lon)
        if d <= radius_m:
            fcopy = dict(feature)
            props = dict(fcopy.get('properties') or {})
            props['distance_m'] = d
            fcopy['properties'] = props
            results.append(fcopy)
    results.sort(key=lambda f: f.get('properties', {}).get('distance_m', 1e12))
    return results


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    return haversine_distance_meters(lat1, lon1, lat2, lon2)


def get_feature_safety_score(feature: Dict[str, Any], default: float = 0.5) -> float:
    """
    Heuristic per-feature safety score in 0..1 based on type/properties.
    """
    props = (feature or {}).get('properties') or {}
    name = (props.get('name') or '').lower()
    kind = (props.get('type') or props.get('amenity') or props.get('category') or '').lower()

    score = default
    if 'police' in kind or 'police' in name:
        score = max(score, 0.9)
    elif 'hospital' in kind or 'hospital' in name:
        score = max(score, 0.8)
    elif 'park' in kind or 'park' in name:
        score = max(score, 0.7)

    status = (props.get('status') or '').lower()
    if status == 'working':
        score += 0.1
    elif status == 'broken':
        score -= 0.2
    return max(0.0, min(1.0, score))