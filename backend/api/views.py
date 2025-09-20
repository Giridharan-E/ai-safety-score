import asyncio
import json
from typing import Any, Dict, Optional
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.db import IntegrityError
from api.services.weather_service import fetch_weather
from api.services.google_maps_service import google_maps_service
from api.services.hybrid_data_service import hybrid_data_service
from api.services.scoring_engine import scoring_engine
from api.services.crime_service import crime_service
from api.utils.geojson_utils import load_geojson, filter_points_in_radius, get_feature_safety_score, haversine_m
from api.utils.json_store import get_json_store
from api.models import Feedback
from api.services.osm_service import fetch_osm_or_local


# ----- Error/response helpers -----
def _error_response(code: str, message: str, http_status: int, details: Optional[Dict[str, Any]] = None):
    payload = {"error": {"code": code, "message": message}}
    if details:
        payload["error"]["details"] = details
    return Response(payload, status=http_status)


def _parse_params(request) -> Dict[str, Any]:
    try:
        # Support either lat/lon or address query
        address = request.GET.get('address') or request.GET.get('q')
        lat_param = request.GET.get('latitude')
        lon_param = request.GET.get('longitude')
        lat = None
        lon = None
        resolved_address = ""  # Initialize with empty string
        
        if address and (not lat_param or not lon_param):
            print(f"🔍 Geocoding address: '{address}'")
            # Try detailed place search first for better accuracy
            geo = google_maps_service.search_places_detailed(address)
            if not geo:
                print("📍 Detailed search failed, trying regular geocoding...")
                # Fallback to regular geocoding
                geo = google_maps_service.geocode(address)
            if not geo:
                raise ValueError(f"Failed to geocode address: '{address}'. Check if GOOGLE_MAPS_API_KEY is set.")
            loc = geo.get('geometry', {}).get('location', {})
            if not loc or 'lat' not in loc or 'lng' not in loc:
                raise ValueError(f"Invalid coordinates returned for address: '{address}'")
            lat = float(loc.get('lat'))
            lon = float(loc.get('lng'))
            resolved_address = geo.get('formatted_address', address)
            print(f"✅ Address converted: '{address}' → ({lat}, {lon}) → '{resolved_address}'")
        else:
            if not lat_param or not lon_param:
                raise ValueError("Either address or both latitude and longitude must be provided")
            lat = float(lat_param)
            lon = float(lon_param)
            # Try to get resolved address for coordinates
            try:
                reverse_geo = google_maps_service.reverse_geocode(lat, lon)
                if reverse_geo:
                    resolved_address = reverse_geo.get('formatted_address', f"{lat}, {lon}")
                else:
                    resolved_address = f"{lat}, {lon}"
            except:
                resolved_address = f"{lat}, {lon}"
                
        radius = float(request.GET.get('radius', 800))
        if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
            raise ValueError("Latitude/longitude out of bounds")
        if radius <= 0 or radius > 5000:
            radius = 800.0
        return {"lat": lat, "lon": lon, "radius": radius, "resolved_address": resolved_address}
    except Exception as e:
        raise ValueError(f"Invalid or missing latitude/longitude: {str(e)}")


@api_view(["GET"])
def combined_data_view(request):
    try:
        params = _parse_params(request)
    except ValueError as e:
        return _error_response("invalid_parameters", str(e), status.HTTP_400_BAD_REQUEST)

    lat, lon, radius = params["lat"], params["lon"], params["radius"]
    resolved_address = params.get("resolved_address", "")
    
    # Get original request parameters for processing info
    address = request.GET.get('address') or request.GET.get('q')
    lat_param = request.GET.get('latitude')
    lon_param = request.GET.get('longitude')
    
    print(f"🎯 Processing safety score for coordinates: ({lat}, {lon}) with radius: {radius}m")
    print(f"📍 Resolved address: '{resolved_address}'")

    # Concurrent external fetches using asyncio.to_thread
    async def gather_external():
        print(f"🌤️ Fetching weather data for ({lat}, {lon})")
        weather_task = asyncio.to_thread(fetch_weather, lat, lon)
        
        print(f"🚔 Searching for police stations near ({lat}, {lon}) within {radius}m")
        g_police_task = asyncio.to_thread(google_maps_service.get_nearby_places, lat, lon, int(radius), 'police')
        
        print(f"🏥 Searching for hospitals near ({lat}, {lon}) within {radius}m")
        print(f"🔑 Google Maps API Key available: {bool(google_maps_service.api_key)}")
        g_hosp_task = asyncio.to_thread(google_maps_service.get_nearby_places, lat, lon, int(radius), 'hospital')
        
        print(f"🚨 Fetching crime data for ({lat}, {lon}) within {radius}m")
        crime_task = asyncio.to_thread(crime_service.get_crime_data, lat, lon, radius)
        
        results = await asyncio.gather(weather_task, g_police_task, g_hosp_task, crime_task, return_exceptions=True)
        safe_results = []
        for r in results:
            safe_results.append(None if isinstance(r, BaseException) else r)
        return safe_results

    # Fetch comprehensive OSM datasets with API-first approach and synthetic fallback
    print(f"🗺️ Fetching comprehensive OSM data for coordinates ({lat}, {lon}) within {radius}m radius")
    
    # Core safety infrastructure (OSM API + synthetic backup)
    osm_police = fetch_osm_or_local('police_stations', lat, lon, radius)
    osm_hospitals = fetch_osm_or_local('hospitals_medical', lat, lon, radius)
    osm_streetlights = fetch_osm_or_local('streetlights_lighting', lat, lon, radius)
    osm_sidewalks = fetch_osm_or_local('sidewalks_pedestrian', lat, lon, radius)
    
    # Tourism and cultural (OSM API + synthetic backup)
    osm_tourist = fetch_osm_or_local('tourist_places_tn', lat, lon, radius)
    osm_temples = fetch_osm_or_local('temples_tn', lat, lon, radius)
    osm_beaches = fetch_osm_or_local('beaches_tn', lat, lon, radius)
    
    # Enhanced safety factors (OSM API + synthetic backup)
    osm_openness = fetch_osm_or_local('openness_factors', lat, lon, radius)
    osm_visibility = fetch_osm_or_local('visibility_factors', lat, lon, radius)
    osm_transport = fetch_osm_or_local('transport_factors', lat, lon, radius)
    
    # Additional safety factors (OSM API + synthetic backup)
    osm_emergency = fetch_osm_or_local('emergency_services', lat, lon, radius)
    osm_security = fetch_osm_or_local('security_factors', lat, lon, radius)

    # Process all OSM datasets
    police_loc = osm_police.get('features', [])
    hospital_loc = osm_hospitals.get('features', [])
    streetlights_osm = osm_streetlights.get('features', [])
    sidewalks = osm_sidewalks.get('features', [])
    tourist_places = osm_tourist.get('features', [])
    temples = osm_temples.get('features', [])
    beaches = osm_beaches.get('features', [])
    
    # Process enhanced safety factors
    openness_features = osm_openness.get('features', [])
    visibility_features = osm_visibility.get('features', [])
    transport_features = osm_transport.get('features', [])
    emergency_features = osm_emergency.get('features', [])
    security_features = osm_security.get('features', [])
    
    # Fallback to local streetlights if OSM data is insufficient
    streetlights_local = load_geojson('streetlights.geojson').get('features', [])
    streetlights = streetlights_osm if streetlights_osm else streetlights_local

    # Filter all safety factors within radius
    police_near = filter_points_in_radius(lat, lon, radius, police_loc)
    hospital_near = filter_points_in_radius(lat, lon, radius, hospital_loc)
    sidewalks_near = filter_points_in_radius(lat, lon, radius, sidewalks)
    streetlights_near = filter_points_in_radius(lat, lon, radius, streetlights)
    tourist_near = filter_points_in_radius(lat, lon, radius, tourist_places)
    temples_near = filter_points_in_radius(lat, lon, radius, temples)
    beaches_near = filter_points_in_radius(lat, lon, radius, beaches)
    
    # Filter enhanced safety factors
    openness_near = filter_points_in_radius(lat, lon, radius, openness_features)
    visibility_near = filter_points_in_radius(lat, lon, radius, visibility_features)
    transport_near = filter_points_in_radius(lat, lon, radius, transport_features)
    emergency_near = filter_points_in_radius(lat, lon, radius, emergency_features)
    security_near = filter_points_in_radius(lat, lon, radius, security_features)

    # Feature-level scores
    def to_nearby_list(items, typ: str):
        result = []
        for it in items[:20]:
            name = (it.get('properties', {}).get('name') or 'Unknown')
            score = get_feature_safety_score(it)
            dist = it.get('properties', {}).get('distance_m', None)
            result.append({"name": name, "type": typ, "score": round(score * 10, 1), "distance": round(dist or 0)})
        return result

    # Create safety recommendations for temples and beaches
    def create_safety_recommendations(temples, beaches, lat, lon, radius):
        recommendations = []
        
        # Add temples as safe places
        for temple in temples[:5]:  # Limit to 5 closest
            name = temple.get('properties', {}).get('name', 'Temple')
            dist = temple.get('properties', {}).get('distance_m', 0)
            if dist <= radius:
                recommendations.append({
                    "name": name,
                    "type": "temple",
                    "safety_level": "high",  # Temples are generally safe
                    "distance_m": round(dist),
                    "description": "Sacred place with community presence",
                    "recommendation": "Safe place to visit during day hours"
                })
        
        # Add beaches as safe places
        for beach in beaches[:3]:  # Limit to 3 closest
            name = beach.get('properties', {}).get('name', 'Beach')
            dist = beach.get('properties', {}).get('distance_m', 0)
            if dist <= radius:
                recommendations.append({
                    "name": name,
                    "type": "beach",
                    "safety_level": "medium",  # Beaches can be less safe at night
                    "distance_m": round(dist),
                    "description": "Public recreational area",
                    "recommendation": "Safe during day, avoid at night"
                })
        
        # Sort by distance
        recommendations.sort(key=lambda x: x['distance_m'])
        return recommendations

    # Analyze user feedback for the location
    def analyze_user_feedback(lat, lon, radius):
        """Analyze user feedback data for the given location and radius"""
        try:
            feedback_store = get_json_store("feedback.json")
            
            # Read feedback data with error handling
            try:
                feedback_data = feedback_store["read"]()
                if not isinstance(feedback_data, dict):
                    feedback_data = {}
            except (json.JSONDecodeError, ValueError):
                return {
                    "user_ratings": [],
                    "average_rating": 0,
                    "total_feedbacks": 0,
                    "feedback_score": 0.5,  # Neutral score if no feedback
                    "nearby_feedbacks": 0
                }
            
            feedbacks = feedback_data.get("feedbacks", [])
            nearby_feedbacks = []
            
            # Find feedbacks within radius
            for feedback in feedbacks:
                try:
                    fb_lat = float(feedback.get('latitude', 0))
                    fb_lon = float(feedback.get('longitude', 0))
                    rating = int(feedback.get('rating', 0))
                    
                    # Calculate distance using haversine formula
                    try:
                        distance = haversine_m(lat, lon, fb_lat, fb_lon)
                    except Exception as e:
                        print(f"⚠️ Error calculating distance: {e}")
                        continue
                    
                    if distance <= radius:
                        nearby_feedbacks.append({
                            "location_name": feedback.get('location_name', 'Unknown'),
                            "rating": rating,
                            "distance_m": round(distance),
                            "place_type": feedback.get('place_type', 'general'),
                            "comment": feedback.get('comment', ''),
                            "created_at": feedback.get('created_at', '')
                        })
                except (ValueError, TypeError):
                    continue  # Skip invalid feedback entries
            
            # Calculate statistics
            if nearby_feedbacks:
                ratings = [fb['rating'] for fb in nearby_feedbacks]
                average_rating = sum(ratings) / len(ratings)
                
                # Convert rating to safety score (1-10 scale to 0-1 scale)
                feedback_score = min(average_rating / 10.0, 1.0)
                
                print(f"📊 Found {len(nearby_feedbacks)} user feedbacks nearby")
                print(f"⭐ Average user rating: {average_rating:.1f}/10")
                print(f"🛡️ Feedback safety score: {feedback_score:.2f}")
            else:
                average_rating = 0
                feedback_score = 0.5  # Neutral if no feedback
                print(f"📊 No user feedback found within {radius}m radius")
            
            return {
                "user_ratings": nearby_feedbacks[:10],  # Limit to 10 most recent
                "average_rating": round(average_rating, 1),
                "total_feedbacks": len(nearby_feedbacks),
                "feedback_score": round(feedback_score, 2),
                "nearby_feedbacks": len(nearby_feedbacks)
            }
            
        except Exception as e:
            print(f"⚠️ Error analyzing user feedback: {e}")
            return {
                "user_ratings": [],
                "average_rating": 0,
                "total_feedbacks": 0,
                "feedback_score": 0.5,
                "nearby_feedbacks": 0
            }

    # We no longer include full lists in the response; only counts are returned.

    # Analyze user feedback for this location (before creating features)
    try:
        user_feedback_data = analyze_user_feedback(lat, lon, radius)
    except Exception as e:
        print(f"⚠️ Error analyzing user feedback: {e}")
        user_feedback_data = {
            "user_ratings": [],
            "average_rating": 0,
            "total_feedbacks": 0,
            "feedback_score": 0.5,
            "nearby_feedbacks": 0
        }

    # External concurrent fetches
    try:
        weather, g_police, g_hosp, crime_data = asyncio.run(gather_external())
        print(f"🏥 Async hospital search result: {len(g_hosp) if isinstance(g_hosp, list) else 'Not a list'} hospitals found")
        
        # If no hospitals found via Google Maps, use local hospital data as fallback
        if not g_hosp or len(g_hosp) == 0:
            print("🏥 No hospitals found via Google Maps, using local hospital data...")
            try:
                local_hospitals = load_geojson('hospitals.geojson').get('features', [])
                g_hosp = filter_points_in_radius(lat, lon, radius, local_hospitals)
                print(f"🏥 Local hospital data: {len(g_hosp)} hospitals found")
            except Exception as local_e:
                print(f"⚠️ Error loading local hospital data: {local_e}")
                g_hosp = []
        
        if isinstance(g_hosp, list) and len(g_hosp) > 0:
            print(f"🏥 First hospital: {g_hosp[0].get('name', 'Unknown')} at {g_hosp[0].get('vicinity', 'Unknown location')}")
    except RuntimeError:
        # If event loop is already running (e.g., ASGI), fall back to sequential threads
        try:
            weather = fetch_weather(lat, lon)
        except Exception:
            weather = None
        try:
            g_police = google_maps_service.get_nearby_places(lat, lon, int(radius), 'police')
        except Exception:
            g_police = []
        try:
            # Try multiple hospital search terms
            g_hosp = google_maps_service.get_nearby_places(lat, lon, int(radius), 'hospital')
            print(f"🏥 Hospital search result: {len(g_hosp) if isinstance(g_hosp, list) else 'Not a list'} hospitals found")
            
            # If no hospitals found, try alternative search terms
            if not g_hosp or len(g_hosp) == 0:
                print("🏥 No hospitals found with 'hospital' type, trying 'health'...")
                g_hosp = google_maps_service.get_nearby_places(lat, lon, int(radius), 'health')
                print(f"🏥 Health search result: {len(g_hosp) if isinstance(g_hosp, list) else 'Not a list'} health facilities found")
            
            # If still no hospitals found, use local hospital data as fallback
            if not g_hosp or len(g_hosp) == 0:
                print("🏥 No hospitals found via Google Maps, using local hospital data...")
                try:
                    local_hospitals = load_geojson('hospitals.geojson').get('features', [])
                    g_hosp = filter_points_in_radius(lat, lon, radius, local_hospitals)
                    print(f"🏥 Local hospital data: {len(g_hosp)} hospitals found")
                except Exception as local_e:
                    print(f"⚠️ Error loading local hospital data: {local_e}")
            g_hosp = []

            if isinstance(g_hosp, list) and len(g_hosp) > 0:
                print(f"🏥 First hospital: {g_hosp[0].get('name', 'Unknown')} at {g_hosp[0].get('vicinity', 'Unknown location')}")
        except Exception as e:
            print(f"⚠️ Error fetching hospitals: {e}")
            g_hosp = []
        try:
            crime_data = crime_service.get_crime_data(lat, lon, radius)
        except Exception:
            crime_data = None

    # Get crime safety score from crime data
    crime_safety_score = 0.5  # Default safe score
    if crime_data and isinstance(crime_data, dict):
        crime_safety_score = crime_data.get('safety_score', 0.5)
        print(f"🚨 Crime data: {crime_data.get('total_crimes', 0)} total crimes, safety score: {crime_safety_score:.2f}")
    else:
        print("⚠️ No crime data available, using default safety score")

    # Calculate comprehensive safety factor scores
    openness_score = min(len(openness_near) / 10, 1.0)  # Parks, squares, open spaces
    visibility_score = min((len(visibility_near) + len(streetlights_near)) / 25, 1.0)  # Street lights + clear sight lines
    transport_score = min(len(transport_near) / 8, 1.0)  # Public transport facilities
    security_score = min(len(security_near) / 5, 1.0)  # Security features
    
    # Combine OSM hospitals with Google Maps hospitals
    total_hospitals = len(hospital_near) + (len(g_hosp) if isinstance(g_hosp, list) else 0)
    
    print(f"🌳 Openness score: {openness_score:.2f} ({len(openness_near)} open spaces)")
    print(f"💡 Visibility score: {visibility_score:.2f} ({len(visibility_near)} visibility factors)")
    print(f"🚌 Transport score: {transport_score:.2f} ({len(transport_near)} transport facilities)")
    print(f"🔒 Security score: {security_score:.2f} ({len(security_near)} security features)")
    print(f"🏥 Total hospitals: {total_hospitals}")

    # Comprehensive features for scoring engine (0..1)
    features = {
        "police_stations": min(len(police_near) / 5, 1.0),
        "hospitals": min(total_hospitals / 5, 1.0),  # Combined OSM + Google Maps
        "lighting": min(len(streetlights_near) / 20, 1.0),
        "visibility": visibility_score,  # Enhanced visibility calculation
        "sidewalks": min(len(sidewalks_near) / 10, 1.0),
        "businesses": 0.5,  # Default business indicator score
        "transport": transport_score,  # Use actual transport data
        "transport_density": transport_score,  # Same as transport for now
        "openness": openness_score,  # New openness factor
        "security_features": security_score,  # Security features factor
        "crime_rate": crime_safety_score,  # Use actual crime data
        "natural_surveillance": 0.5,
        "user_feedback": user_feedback_data["feedback_score"],  # Include user feedback score
    }

    # Adjust weights using feedback trends
    scoring_engine.update_weights_from_feedback(lat, lon, radius)
    ai_safety_score, _adj = scoring_engine.score(features, profile={})
    
    # Calculate enhanced safety score using the formula:
    # (AI safety score + user feedback avg) / 2
    user_feedback_count = user_feedback_data["total_feedbacks"]
    user_feedback_avg = user_feedback_data["average_rating"]
    
    if user_feedback_count > 0:
        # Apply the formula: (AI score + user avg) / 2
        score = (ai_safety_score + user_feedback_avg) / 2
        
        print(f"🧮 Enhanced scoring: AI={ai_safety_score:.1f}, User avg={user_feedback_avg:.1f}, Count={user_feedback_count}")
        print(f"📊 Formula: ({ai_safety_score:.1f} + {user_feedback_avg:.1f}) / 2 = {score:.1f}")
    else:
        # No user feedback, use AI score only
        score = ai_safety_score
        print(f"🤖 No user feedback, using AI score only: {score:.1f}")

    # Weather formatting
    weather_payload = None
    if isinstance(weather, dict):
        weather_payload = {
            "temperature": weather.get('temperature'),
            "condition": weather.get('weather_main')
        }

    # Create safety recommendations
    safety_recommendations = create_safety_recommendations(temples_near, beaches_near, lat, lon, radius)
    print(f"🏛️ Found {len(temples_near)} temples and {len(beaches_near)} beaches for recommendations")
    print(f"💡 Created {len(safety_recommendations)} safety recommendations")

    resp = {
        "overall_safety_score": round(score, 1),
        "safety_color": "green" if score >= 7.5 else ("yellow" if score >= 5 else "red"),
        "location_info": {
            "coordinates": {"latitude": round(lat, 6), "longitude": round(lon, 6)},
        "resolved_address": resolved_address,
            "search_radius_meters": radius
        },
        "weather": weather_payload or {},
        "safety_indicators": {
            "police_nearby": len(police_near),
            "hospitals_nearby": total_hospitals,
            "streetlights": len(streetlights_near),
            "sidewalks": len(sidewalks_near),
            "tourist_places": len(tourist_near),
            "open_spaces": len(openness_near),
            "visibility_factors": len(visibility_near),
            "transport_facilities": len(transport_near),
            "security_factors": len(security_near),
        },
        "crime_statistics": crime_service.get_crime_statistics_summary(lat, lon, radius) if crime_data else {
            "total_crimes": 0,
            "recent_crimes": 0,
            "crime_rate_per_km2": 0.0,
            "safety_score": 0.5,
            "safety_level": "Unknown",
            "top_crime_type": "none",
            "data_source": "no_data",
            "last_updated": "N/A"
        },
        "user_feedback": {
            "average_rating": user_feedback_data["average_rating"],
            "total_feedbacks": user_feedback_data["total_feedbacks"],
            "feedback_score": user_feedback_data["feedback_score"],
            "recent_ratings": user_feedback_data["user_ratings"][:5],  # Show top 5 recent ratings
            "calculation": {
                "ai_safety_score": round(ai_safety_score, 1),
                "user_feedback_avg": user_feedback_data["average_rating"],
                "feedback_count": user_feedback_data["total_feedbacks"],
                "formula": f"({ai_safety_score:.1f} + {user_feedback_data['average_rating']:.1f}) / 2" if user_feedback_data["total_feedbacks"] > 0 else "AI score only (no user feedback)",
                "enhanced_score": round(score, 1)
            }
        },
        "safety_factors_breakdown": {
            "openness": {
                "score": round(openness_score, 2),
                "count": len(openness_near),
                "description": "Parks, squares, and open spaces that improve visibility and safety",
                "data_source": "OSM API + Synthetic Backup"
            },
            "visibility": {
                "score": round(visibility_score, 2),
                "count": len(visibility_near) + len(streetlights_near),
                "description": "Street lights and clear sight lines for better visibility",
                "data_source": "OSM API + Synthetic Backup"
            },
            "transport": {
                "score": round(transport_score, 2),
                "count": len(transport_near),
                "description": "Public transportation facilities for easy access and escape routes",
                "data_source": "OSM API + Synthetic Backup"
            },
            "security_features": {
                "score": round(security_score, 2),
                "count": len(security_near),
                "description": "Security cameras, barriers, and controlled access points",
                "data_source": "OSM API + Synthetic Backup"
            }
        },
        "safety_recommendations": {
            "nearby_safe_places": safety_recommendations,
            "total_recommendations": len(safety_recommendations)
        },
        "processing_info": {
            "geocoding_used": bool(address and not lat_param and not lon_param),
            "coordinate_source": "address_geocoded" if (address and not lat_param and not lon_param) else "direct_coordinates",
            "total_places_found": len(police_near) + len(g_hosp) + len(streetlights_near) + len(sidewalks_near) + len(tourist_near) + len(openness_near) + len(visibility_near) + len(transport_near),
            "user_feedbacks_analyzed": user_feedback_data["nearby_feedbacks"],
            "data_sources": {
                "osm_api": "Used for real-time data fetching",
                "local_cache": "Used for offline access and faster response",
                "synthetic_data": "Used when APIs are unavailable"
            },
            "cache_status": "Data cached for 24 hours for faster subsequent requests"
        }
    }
    return Response(resp)


@api_view(["GET"])
def simple_data_view(request):
    """Simple endpoint that only requires lat/lon - no geocoding"""
    try:
        lat = float(request.GET.get('latitude'))
        lon = float(request.GET.get('longitude'))
        radius = float(request.GET.get('radius', 800))
        if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
            return _error_response("invalid_coordinates", "Latitude/longitude out of bounds", status.HTTP_400_BAD_REQUEST)
        if radius <= 0 or radius > 5000:
            radius = 800.0
    except (ValueError, TypeError):
        return _error_response("invalid_parameters", "Missing or invalid latitude/longitude parameters", status.HTTP_400_BAD_REQUEST)

    # Use local GeoJSON only (no OSM or Google Maps)
    police_loc = load_geojson('police_stations.geojson').get('features', [])
    streetlights = load_geojson('streetlights.geojson').get('features', [])
    sidewalks = load_geojson('sidewalks.geojson').get('features', [])
    parks = load_geojson('parks.geojson').get('features', [])

    police_near = filter_points_in_radius(lat, lon, radius, police_loc)
    streetlights_near = filter_points_in_radius(lat, lon, radius, streetlights)
    sidewalks_near = filter_points_in_radius(lat, lon, radius, sidewalks)
    parks_near = filter_points_in_radius(lat, lon, radius, parks)

    # Simple scoring
    features = {
        "police_stations": min(len(police_near) / 5, 1.0),
        "hospitals": 0.5,  # Default
        "lighting": min(len(streetlights_near) / 20, 1.0),
        "visibility": min((len(streetlights_near) + len(sidewalks_near)) / 30, 1.0),
        "sidewalks": min(len(sidewalks_near) / 10, 1.0),
        "businesses": 0.5,
        "transport": 0.5,
        "transport_density": 0.5,
        "crime_rate": 0.6,
        "natural_surveillance": 0.5,
    }

    score, _adj = scoring_engine.score(features, profile={})

    resp = {
        "overall_safety_score": round(score, 1),
        "safety_color": "green" if score >= 7.5 else ("yellow" if score >= 5 else "red"),
        "center": {"latitude": round(lat, 6), "longitude": round(lon, 6)},
        "other_safety_indicators": {
            "police_nearby": len(police_near),
            "hospitals_nearby": 0,
            "streetlights": len(streetlights_near),
            "sidewalks": len(sidewalks_near),
            "parks": len(parks_near),
        },
    }
    return Response(resp)


@api_view(["POST"])
@csrf_exempt
def feedback_view(request):
    data = request.data or {}
    
    # Import feedback validator
    from .services.feedback_validator import feedback_validator
    
    # Validate feedback using the validator
    is_valid, validation_errors, approval_status = feedback_validator.validate_feedback(data)
    
    if not is_valid:
        return _error_response(
            "validation_failed", 
            f"Validation failed: {'; '.join(validation_errors)}", 
            status.HTTP_400_BAD_REQUEST
        )

    try:
        # Extract validated values
        lat_val = float(data.get("latitude"))
        lon_val = float(data.get("longitude"))
        rating_val = int(data.get("rating"))

        # Auto-generate location ID based on coordinates
        location_id = f"LOC_{int(lat_val * 1000)}_{int(lon_val * 1000)}"
        print(f"🆔 Auto-generated location ID: {location_id}")
        
        # Try to get location name from reverse geocoding if not provided
        location_name = data.get("location_name", "")
        if not location_name:
            print(f"🌍 Auto-detecting location name for ({lat_val}, {lon_val})")
            try:
                reverse_geo = google_maps_service.reverse_geocode(lat_val, lon_val)
                if reverse_geo:
                    location_name = reverse_geo.get('formatted_address', f"Location at {lat_val}, {lon_val}")
                    print(f"📍 Detected location: {location_name}")
                else:
                    location_name = f"Location at {lat_val}, {lon_val}"
            except:
                location_name = f"Location at {lat_val}, {lon_val}"
        else:
            print(f"📍 Using provided location name: {location_name}")

        # Create feedback with approval status and validation metadata
        # Handle case where new fields don't exist yet (before migration)
        try:
            fb = Feedback.objects.create(
                user_id=str(data.get("user_id", ""))[:64],
                location_id=location_id[:128],
                location_name=location_name[:256],
                latitude=lat_val,
                longitude=lon_val,
                place_type=str(data.get("place_type", "general"))[:64],
                region=str(data.get("region", "Unknown"))[:64],
                rating=rating_val,
                comment=str(data.get("comment", "")),
                approval_status=approval_status,
                validation_errors=validation_errors,
                is_trusted_user=feedback_validator._is_trusted_user(data.get("user_id", "")),
            )
        except Exception as db_error:
            # Fallback: create feedback without new fields (before migration)
            print(f"⚠️ Using fallback feedback creation: {db_error}")
            fb = Feedback.objects.create(
                user_id=str(data.get("user_id", ""))[:64],
                location_id=location_id[:128],
                location_name=location_name[:256],
                latitude=lat_val,
                longitude=lon_val,
                place_type=str(data.get("place_type", "general"))[:64],
                region=str(data.get("region", "Unknown"))[:64],
                rating=rating_val,
                comment=str(data.get("comment", "")),
            )
            # Override approval status for fallback
            approval_status = 'auto_approved'  # Assume auto-approved for fallback
        
        # Also save to JSON file
        try:
            feedback_store = get_json_store("feedback.json")
            
            # Read existing data with error handling
            try:
                feedback_data = feedback_store["read"]()
                if not isinstance(feedback_data, dict):
                    feedback_data = {}
            except (json.JSONDecodeError, ValueError):
                print("⚠️ feedback.json is corrupted or empty, initializing new structure")
                feedback_data = {}
            
            # Create feedback entry for JSON (only include approved feedback)
            if approval_status in ['approved', 'auto_approved']:
                feedback_entry = {
                    "id": str(fb.id),
                    "user_id": str(data.get("user_id", "")),
                    "location_id": location_id,
                    "location_name": location_name,
                    "latitude": lat_val,
                    "longitude": lon_val,
                    "place_type": str(data.get("place_type", "general")),
                    "region": str(data.get("region", "Unknown")),
                    "rating": rating_val,
                    "comment": str(data.get("comment", "")),
                    "created_at": fb.created_at.isoformat(),
                    "approval_status": approval_status
                }
            
                # Initialize feedbacks array if not exists
                if "feedbacks" not in feedback_data:
                    feedback_data["feedbacks"] = []
                
                feedback_data["feedbacks"].append(feedback_entry)
                feedback_store["write"](feedback_data)
                print(f"✅ Feedback saved to JSON: {location_id}")
            
        except Exception as e:
            print(f"❌ Warning: Could not save feedback to JSON: {e}")
            # Don't fail the entire request if JSON save fails
        
    except (ValueError, IntegrityError) as e:
        return _error_response("invalid_input", f"Invalid input: {e}", status.HTTP_400_BAD_REQUEST)

    # Only trigger weight refresh for approved feedback
    if approval_status in ['approved', 'auto_approved']:
        try:
            scoring_engine.update_weights_from_feedback(fb.latitude, fb.longitude)
        except Exception:
            pass

    # Return response with approval status
    response_data = {
        "id": fb.id, 
        "created_at": fb.created_at,
        "approval_status": approval_status,
        "message": "Feedback submitted successfully"
    }
    
    if approval_status == 'auto_approved':
        response_data["message"] += " and auto-approved"
    elif approval_status == 'pending':
        response_data["message"] += " and pending review"
    
    return Response(response_data, status=status.HTTP_201_CREATED)


@api_view(["GET"])
def feedback_list_view(request):
    """
    Get all feedback data from JSON file
    """
    try:
        feedback_store = get_json_store("feedback.json")
        
        # Read with error handling
        try:
            feedback_data = feedback_store["read"]()
            if not isinstance(feedback_data, dict):
                feedback_data = {}
        except (json.JSONDecodeError, ValueError):
            print("⚠️ feedback.json is corrupted or empty, returning empty list")
            feedback_data = {}
        
        # Return feedbacks array or empty array if none
        feedbacks = feedback_data.get("feedbacks", [])
        
        return Response({
            "count": len(feedbacks),
            "feedbacks": feedbacks
        })
        
    except Exception as e:
        return _error_response("json_read_error", f"Could not read feedback data: {str(e)}", status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
def pending_feedback_view(request):
    """Get feedback pending manual review."""
    try:
        from .services.feedback_validator import feedback_validator
        pending = feedback_validator.get_pending_feedback()
        return Response({
            "count": len(pending),
            "pending_feedback": pending
        })
    except Exception as e:
        print(f"❌ Error in pending_feedback_view: {e}")
        return _error_response("fetch_error", f"Could not fetch pending feedback: {str(e)}", status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@csrf_exempt
def approve_feedback_view(request):
    """Approve a feedback."""
    try:
        from .services.feedback_validator import feedback_validator
        
        data = request.data or {}
        feedback_id = data.get('feedback_id')
        admin_user = data.get('admin_user', 'admin')
        
        if not feedback_id:
            return _error_response("missing_fields", "feedback_id required", status.HTTP_400_BAD_REQUEST)
        
        success = feedback_validator.approve_feedback(feedback_id, admin_user)
        
        if success:
            return Response({"message": "Feedback approved successfully"})
        else:
            return _error_response("approval_failed", "Failed to approve feedback", status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        print(f"❌ Error in approve_feedback_view: {e}")
        return _error_response("approval_error", f"Error approving feedback: {str(e)}", status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@csrf_exempt
def reject_feedback_view(request):
    """Reject a feedback."""
    try:
        from .services.feedback_validator import feedback_validator
        
        data = request.data or {}
        feedback_id = data.get('feedback_id')
        admin_user = data.get('admin_user', 'admin')
        reason = data.get('reason', 'No reason provided')
        
        if not feedback_id:
            return _error_response("missing_fields", "feedback_id required", status.HTTP_400_BAD_REQUEST)
        
        success = feedback_validator.reject_feedback(feedback_id, admin_user, reason)
        
        if success:
            return Response({"message": "Feedback rejected successfully"})
        else:
            return _error_response("rejection_failed", "Failed to reject feedback", status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        print(f"❌ Error in reject_feedback_view: {e}")
        return _error_response("rejection_error", f"Error rejecting feedback: {str(e)}", status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
def feedback_statistics_view(request):
    """Get feedback validation statistics."""
    try:
        from .services.feedback_validator import feedback_validator
        stats = feedback_validator.get_feedback_statistics()
        return Response(stats)
    except Exception as e:
        print(f"❌ Error in feedback_statistics_view: {e}")
        return _error_response("stats_error", f"Could not fetch statistics: {str(e)}", status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
def google_maps_key_view(request):
    """Get Google Maps API key for frontend autocomplete"""
    try:
        import os
        api_key = os.getenv("GOOGLE_MAPS_API_KEY")
        return Response({
            "api_key": api_key if api_key else None,
            "available": bool(api_key)
        })
    except Exception as e:
        return Response({
            "api_key": None,
            "available": False,
            "error": str(e)
        })


@api_view(["GET"])
def cached_safety_data_view(request):
    """Get cached safety data for a location"""
    try:
        lat = float(request.GET.get('latitude'))
        lon = float(request.GET.get('longitude'))
        radius = float(request.GET.get('radius', 800))
        
        if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
            return _error_response("invalid_coordinates", "Latitude/longitude out of bounds", status.HTTP_400_BAD_REQUEST)
        
        from api.services.osm_service import get_location_safety_summary
        summary = get_location_safety_summary(lat, lon, radius)
        
        return Response({
            "success": True,
            "location": summary['location'],
            "timestamp": summary['timestamp'],
            "safety_factors": summary['safety_factors'],
            "cache_info": {
                "cached_factors": sum(1 for factor in summary['safety_factors'].values() if factor.get('data_source') == 'cached'),
                "fresh_factors": sum(1 for factor in summary['safety_factors'].values() if factor.get('data_source') == 'fresh'),
                "total_factors": len(summary['safety_factors'])
            }
        })
    except (ValueError, TypeError):
        return _error_response("invalid_parameters", "Missing or invalid latitude/longitude parameters", status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return _error_response("data_error", f"Failed to get cached safety data: {str(e)}", status.HTTP_500_INTERNAL_SERVER_ERROR)


def test_page_view(_request):
    html = (
        """
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>SafetyScore API Tester - Enhanced</title>
  <style>
    body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 20px; background: #f5f5f5; }
    .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
    input, button, select { padding: 10px; margin: 5px 0; border: 1px solid #ddd; border-radius: 5px; font-size: 14px; }
    input:focus, select:focus { outline: none; border-color: #4CAF50; box-shadow: 0 0 5px rgba(76, 175, 80, 0.3); }
    .row { display: flex; gap: 15px; flex-wrap: wrap; margin: 10px 0; }
    .col { display: flex; flex-direction: column; min-width: 200px; flex: 1; }
    .col-2 { flex: 2; }
    .col-3 { flex: 3; }
    pre { background: #f8f9fa; padding: 15px; border: 1px solid #e9ecef; border-radius: 5px; max-height: 400px; overflow: auto; font-size: 12px; }
    .card { border: 1px solid #e0e0e0; padding: 15px; border-radius: 8px; margin: 15px 0; background: #fafafa; }
    .status { padding: 10px; margin: 10px 0; border-radius: 5px; }
    .status.loading { background: #e3f2fd; color: #1976d2; border: 1px solid #bbdefb; }
    .status.success { background: #e8f5e8; color: #2e7d32; border: 1px solid #c8e6c9; }
    .status.error { background: #ffebee; color: #c62828; border: 1px solid #ffcdd2; }
    button { background: #4CAF50; color: white; border: none; cursor: pointer; font-weight: bold; }
    button:hover { background: #45a049; }
    button:disabled { background: #cccccc; cursor: not-allowed; }
    .autocomplete { position: relative; }
    .autocomplete-items { position: absolute; border: 1px solid #d4d4d4; border-bottom: none; border-top: none; z-index: 99; top: 100%; left: 0; right: 0; max-height: 200px; overflow-y: auto; background: white; }
    .autocomplete-items div { padding: 10px; cursor: pointer; border-bottom: 1px solid #d4d4d4; }
    .autocomplete-items div:hover { background-color: #e9e9e9; }
    .autocomplete-active { background-color: DodgerBlue !important; color: #ffffff; }
    .coords-display { background: #e8f5e8; padding: 10px; border-radius: 5px; margin: 10px 0; font-family: monospace; }
    .loading-spinner { display: inline-block; width: 20px; height: 20px; border: 3px solid #f3f3f3; border-top: 3px solid #3498db; border-radius: 50%; animation: spin 1s linear infinite; }
    @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    .hidden { display: none; }
  </style>
</head>
<body>
  <div class="container">
    <h1>🛡️ SafetyScore API Tester - Enhanced</h1>
    
    <div class="card">
      <h3>📍 Location Input</h3>
  <div class="row">
        <div class="col-2">
          <label>Search Address or Landmark</label>
          <div class="autocomplete">
            <input id="addr" type="text" placeholder="e.g., Marina Beach Chennai, Taj Mahal, Red Fort Delhi" 
                   autocomplete="on" oninput="handleAddressInput()" onkeypress="handleAddressKeyPress(event)" />
            <div id="autocomplete-list" class="autocomplete-items"></div>
          </div>
        </div>
    <div class="col">
          <label>Radius (meters)</label>
          <select id="radius" onchange="updateRadius()">
            <option value="500">500m</option>
            <option value="800" selected>800m</option>
            <option value="1000">1000m</option>
            <option value="1500">1500m</option>
            <option value="2000">2000m</option>
          </select>
    </div>
    <div class="col">
          <label>&nbsp;</label>
          <button onclick="searchAddress()" id="searchAddressBtn" style="width: 100%;">
            <span id="searchAddressText">🔍 Search</span>
            <span id="searchAddressSpinner" class="loading-spinner hidden"></span>
          </button>
    </div>
    <div class="col">
          <label>&nbsp;</label>
          <button onclick="callCombined()" id="searchBtn" style="width: 100%;">
            <span id="searchText">🛡️ Get Safety Score</span>
            <span id="searchSpinner" class="loading-spinner hidden"></span>
          </button>
    </div>
  </div>

  <div class="row">
        <div class="col-2">
          <label>Manual Coordinates (if needed)</label>
          <div class="row">
            <div class="col">
              <input id="lat" type="number" step="any" placeholder="Latitude" onchange="updateFromCoords()" />
    </div>
            <div class="col">
              <input id="lon" type="number" step="any" placeholder="Longitude" onchange="updateFromCoords()" />
            </div>
          </div>
        </div>
        <div class="col">
          <label>Current Location</label>
          <button onclick="getCurrentLocation()" id="currentLocBtn">📍 Use My Location</button>
        </div>
  </div>
      
      <div id="coordsDisplay" class="coords-display hidden">
        <strong>📍 Resolved Coordinates:</strong> <span id="resolvedCoords"></span><br>
        <strong>🏷️ Address:</strong> <span id="resolvedAddress"></span>
      </div>
    </div>

    <div id="statusDiv" class="status hidden"></div>

  <div class="card">
      <h3>📊 Safety Score Response</h3>
      <pre id="output">Click "Get Safety Score" to see results...</pre>
  </div>

    <div class="card">
      <h3>💬 Submit Feedback</h3>
  <div class="row">
    <div class="col">
          <label>Location Name (optional)</label>
          <input id="fname" placeholder="Will auto-detect from coordinates" />
    </div>
    <div class="col">
      <label>Type</label>
          <select id="ftype">
            <option value="tourist_place">Tourist Place</option>
            <option value="restaurant">Restaurant</option>
            <option value="park">Park</option>
            <option value="shopping_mall">Shopping Mall</option>
            <option value="hospital">Hospital</option>
            <option value="police_station">Police Station</option>
          </select>
    </div>
    <div class="col">
      <label>Region</label>
      <input id="fregion" value="Tamil Nadu" />
    </div>
    <div class="col">
      <label>Rating (1-10)</label>
      <input id="frating" type="number" min="1" max="10" value="9" />
    </div>
  </div>
  <div class="row">
        <button onclick="sendFeedback()">💾 Submit Feedback</button>
        <button onclick="loadFeedbacks()" style="background: #2196F3;">📋 View Feedbacks</button>
      </div>
    </div>

    <div class="card" id="feedbackCard" style="display: none;">
      <h3>📋 Feedback Data</h3>
      <div class="row">
        <div class="col">
          <button onclick="loadFeedbacks()" style="background: #4CAF50;">🔄 Refresh</button>
        </div>
        <div class="col">
          <button onclick="clearFeedbacks()" style="background: #f44336;">🗑️ Clear Display</button>
        </div>
      </div>
      <pre id="feedbackOutput">Click "View Feedbacks" to see data...</pre>
    </div>
  </div>

  <script>
    let currentTimeout;
    let autocompleteData = [];
    let googleMapsLoaded = false;
    
    // Initialize Google Maps Places API
    function initGoogleMaps() {
      if (googleMapsLoaded) return;
      
      // Get Google Maps API key from backend
      fetch('/api/google-maps-key/')
        .then(response => response.json())
        .then(data => {
          if (data.api_key) {
            // Load Google Maps Places API
            const script = document.createElement('script');
            script.src = `https://maps.googleapis.com/maps/api/js?key=${data.api_key}&libraries=places&callback=initAutocomplete`;
            script.async = true;
            script.defer = true;
            document.head.appendChild(script);
          } else {
            console.log('Google Maps API key not available, using fallback autocomplete');
          }
        })
        .catch(error => {
          console.log('Error loading Google Maps API key, using fallback autocomplete:', error);
        });
      
      googleMapsLoaded = true;
    }
    
    // Initialize autocomplete when Google Maps loads
    function initAutocomplete() {
      const input = document.getElementById('addr');
      if (input && window.google && window.google.maps && window.google.maps.places) {
        const autocomplete = new google.maps.places.Autocomplete(input, {
          types: ['establishment', 'geocode'],
          componentRestrictions: { country: 'in' } // Focus on India, remove for global
        });
        
        autocomplete.addListener('place_changed', function() {
          const place = autocomplete.getPlace();
          if (place.geometry && place.geometry.location) {
            const lat = place.geometry.location.lat();
            const lng = place.geometry.location.lng();
            document.getElementById('lat').value = lat.toFixed(6);
            document.getElementById('lon').value = lng.toFixed(6);
            updateCoordsDisplay(lat, lng, place.formatted_address);
            closeAutocomplete();
          }
        });
      }
    }
    
    // Sample addresses for autocomplete (fallback)
    const sampleAddresses = [
      "Marina Beach Chennai",
      "Taj Mahal Agra",
      "Red Fort Delhi", 
      "Gateway of India Mumbai",
      "Golden Temple Amritsar",
      "Charminar Hyderabad",
      "India Gate Delhi",
      "Lotus Temple Delhi",
      "Hawa Mahal Jaipur",
      "Victoria Memorial Kolkata",
      "Meenakshi Temple Madurai",
      "Konark Sun Temple Odisha",
      "Ajanta Caves Maharashtra",
      "Ellora Caves Maharashtra",
      "Khajuraho Temples MP"
    ];

    function showStatus(message, type = 'loading') {
      const statusDiv = document.getElementById('statusDiv');
      statusDiv.className = `status ${type}`;
      statusDiv.textContent = message;
      statusDiv.classList.remove('hidden');
    }

    function hideStatus() {
      document.getElementById('statusDiv').classList.add('hidden');
    }

    function show(obj) {
      document.getElementById('output').textContent = JSON.stringify(obj, null, 2);
    }

    function updateCoordsDisplay(lat, lon, address) {
      document.getElementById('resolvedCoords').textContent = `${lat}, ${lon}`;
      document.getElementById('resolvedAddress').textContent = address || 'N/A';
      document.getElementById('coordsDisplay').classList.remove('hidden');
    }

    function handleAddressInput() {
      const input = document.getElementById('addr');
      const value = input.value.trim();
      
      if (value.length < 2) {
        closeAutocomplete();
        return;
      }

      // Try to use Google Maps Places API if available
      if (window.google && window.google.maps && window.google.maps.places) {
        // Google Maps autocomplete is already initialized
        return;
      }

      // Fallback to sample addresses
      autocompleteData = sampleAddresses.filter(addr => 
        addr.toLowerCase().includes(value.toLowerCase())
      );

      showAutocomplete(autocompleteData);
    }

    function handleAddressKeyPress(event) {
      if (event.key === 'Enter') {
        event.preventDefault();
        searchAddress();
      }
    }

    async function searchAddress() {
      const addr = document.getElementById('addr').value.trim();
      if (!addr) {
        showStatus('❌ Please enter an address to search', 'error');
        return;
      }

      const searchBtn = document.getElementById('searchAddressBtn');
      const searchText = document.getElementById('searchAddressText');
      const searchSpinner = document.getElementById('searchAddressSpinner');
      
      // Show loading state
      searchBtn.disabled = true;
      searchText.classList.add('hidden');
      searchSpinner.classList.remove('hidden');
      showStatus(`🔍 Geocoding address: "${addr}"`, 'loading');

      try {
        // Use the geocoding endpoint to get coordinates
        const url = `/api/combined_data/?address=${encodeURIComponent(addr)}&radius=800`;
        const res = await fetch(url);
        const data = await res.json();
        
        if (data.error) {
          showStatus(`❌ Geocoding error: ${data.error.message}`, 'error');
        } else if (data.location_info) {
          const coords = data.location_info.coordinates;
          const address = data.location_info.resolved_address;
          
          // Update coordinate inputs
          document.getElementById('lat').value = coords.latitude;
          document.getElementById('lon').value = coords.longitude;
          
          // Update display
          updateCoordsDisplay(coords.latitude, coords.longitude, address);
          
          showStatus(`✅ Address geocoded successfully!`, 'success');
          
          // Auto-hide status after 2 seconds
          setTimeout(() => hideStatus(), 2000);
        } else {
          showStatus('❌ No location data received', 'error');
        }
        
      } catch (e) { 
        showStatus(`❌ Network error: ${e.message}`, 'error');
      } finally {
        searchBtn.disabled = false;
        searchText.classList.remove('hidden');
        searchSpinner.classList.add('hidden');
      }
    }

    function showAutocomplete(items) {
      const list = document.getElementById('autocomplete-list');
      list.innerHTML = '';
      
      items.forEach((item, index) => {
        const div = document.createElement('div');
        div.innerHTML = item.replace(new RegExp(document.getElementById('addr').value, 'gi'), '<strong>$&</strong>');
        div.addEventListener('click', () => {
          document.getElementById('addr').value = item;
          closeAutocomplete();
          // Auto-geocode when address is selected
          setTimeout(() => searchAddress(), 300);
        });
        list.appendChild(div);
      });
    }

    function closeAutocomplete() {
      document.getElementById('autocomplete-list').innerHTML = '';
    }

    function updateRadius() {
      const radius = document.getElementById('radius').value;
      console.log('Radius updated to:', radius);
    }

    function updateFromCoords() {
      const lat = document.getElementById('lat').value;
      const lon = document.getElementById('lon').value;
      if (lat && lon) {
        updateCoordsDisplay(lat, lon, 'Manual coordinates');
        // Clear address input
        document.getElementById('addr').value = '';
      }
    }

    function getCurrentLocation() {
      const btn = document.getElementById('currentLocBtn');
      const originalText = btn.textContent;
      btn.textContent = '📍 Getting Location...';
      btn.disabled = true;

      if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
          (position) => {
            const lat = position.coords.latitude;
            const lon = position.coords.longitude;
            document.getElementById('lat').value = lat;
            document.getElementById('lon').value = lon;
            updateCoordsDisplay(lat, lon, 'Current location');
            document.getElementById('addr').value = '';
            btn.textContent = originalText;
            btn.disabled = false;
            // Auto-search with current location
            setTimeout(() => callCombined(), 500);
          },
          (error) => {
            showStatus('Error getting location: ' + error.message, 'error');
            btn.textContent = originalText;
            btn.disabled = false;
          }
        );
      } else {
        showStatus('Geolocation not supported by this browser', 'error');
        btn.textContent = originalText;
        btn.disabled = false;
      }
    }

    async function callCombined() {
      const lat = document.getElementById('lat').value;
      const lon = document.getElementById('lon').value;
      const radius = document.getElementById('radius').value;
      const addr = document.getElementById('addr').value.trim();
      
      const searchBtn = document.getElementById('searchBtn');
      const searchText = document.getElementById('searchText');
      const searchSpinner = document.getElementById('searchSpinner');
      
      // Show loading state
      searchBtn.disabled = true;
      searchText.classList.add('hidden');
      searchSpinner.classList.remove('hidden');
      showStatus('🔍 Searching for safety data...', 'loading');

      let url = `/api/combined_data/?radius=${encodeURIComponent(radius)}`;
      
      if (addr && (!lat || !lon)) {
        url += `&address=${encodeURIComponent(addr)}`;
        showStatus(`🔍 Geocoding address: "${addr}"`, 'loading');
      } else if (lat && lon) {
        url += `&latitude=${encodeURIComponent(lat)}&longitude=${encodeURIComponent(lon)}`;
        showStatus(`🎯 Using coordinates: (${lat}, ${lon})`, 'loading');
      } else {
        showStatus('❌ Please enter an address and click "Search" first, or enter coordinates manually', 'error');
        searchBtn.disabled = false;
        searchText.classList.remove('hidden');
        searchSpinner.classList.add('hidden');
        return;
      }

      try {
        const res = await fetch(url);
        const data = await res.json();
        
        if (data.error) {
          showStatus(`❌ Error: ${data.error.message}`, 'error');
        } else {
          showStatus(`✅ Safety score calculated successfully!`, 'success');
          
          // Update coordinates display if we geocoded an address
          if (addr && data.location_info) {
            const coords = data.location_info.coordinates;
            const address = data.location_info.resolved_address;
            updateCoordsDisplay(coords.latitude, coords.longitude, address);
            
            // Update manual coordinate inputs
            document.getElementById('lat').value = coords.latitude;
            document.getElementById('lon').value = coords.longitude;
          }
        }
        
        show(data);
        
        // Hide status after 3 seconds
        setTimeout(() => hideStatus(), 3000);
        
      } catch (e) { 
        showStatus(`❌ Network error: ${e.message}`, 'error');
        show({ error: String(e) }); 
      } finally {
        searchBtn.disabled = false;
        searchText.classList.remove('hidden');
        searchSpinner.classList.add('hidden');
      }
    }

    async function sendFeedback() {
      const lat = parseFloat(document.getElementById('lat').value);
      const lon = parseFloat(document.getElementById('lon').value);
      const payload = {
        location_name: document.getElementById('fname').value || '', // Optional, will auto-detect if empty
        place_type: document.getElementById('ftype').value,
        region: document.getElementById('fregion').value,
        latitude: lat,
        longitude: lon,
        rating: parseInt(document.getElementById('frating').value) || 5,
        comment: 'Quick test from enhanced tester page'
      };
      
      showStatus('💾 Submitting feedback...', 'loading');
      
      try {
        const res = await fetch('/api/feedback/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        const data = await res.json();
        showStatus('✅ Feedback submitted successfully!', 'success');
        show(data);
        setTimeout(() => hideStatus(), 3000);
      } catch (e) { 
        showStatus(`❌ Error submitting feedback: ${e.message}`, 'error');
        show({ error: String(e) }); 
      }
    }

    async function loadFeedbacks() {
      showStatus('📋 Loading feedback data...', 'loading');
      
      try {
        const res = await fetch('/api/feedback/list/');
        const data = await res.json();
        
        if (data.error) {
          showStatus(`❌ Error loading feedbacks: ${data.error.message}`, 'error');
        } else {
          showStatus(`✅ Loaded ${data.count} feedback entries`, 'success');
          document.getElementById('feedbackOutput').textContent = JSON.stringify(data, null, 2);
          document.getElementById('feedbackCard').style.display = 'block';
        }
        
        setTimeout(() => hideStatus(), 3000);
      } catch (e) { 
        showStatus(`❌ Network error: ${e.message}`, 'error');
      }
    }

    function clearFeedbacks() {
      document.getElementById('feedbackOutput').textContent = 'Click "View Feedbacks" to see data...';
      document.getElementById('feedbackCard').style.display = 'none';
    }

    // Close autocomplete when clicking outside
    document.addEventListener('click', (e) => {
      if (!e.target.closest('.autocomplete')) {
        closeAutocomplete();
      }
    });

    // Initialize with empty values - no default coordinates
    document.getElementById('lat').value = '';
    document.getElementById('lon').value = '';
    // Don't show coordinates display initially
    document.getElementById('coordsDisplay').classList.add('hidden');
    
    // Initialize Google Maps autocomplete when page loads
    initGoogleMaps();
  </script>
</body>
</html>
"""
    )
    from django.http import HttpResponse
    return HttpResponse(html, content_type="text/html")
