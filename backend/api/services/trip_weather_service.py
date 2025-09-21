"""
Trip Weather and Climate Analysis Service

This service analyzes weather and climate conditions for trip planning,
considering factors like temperature, precipitation, humidity, and extreme weather events.
"""

import requests
import json
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class WeatherCondition:
    """Data class for weather conditions."""
    temperature: float
    feels_like: float
    humidity: float
    precipitation: float
    wind_speed: float
    description: str
    date: str


@dataclass
class ClimateAnalysis:
    """Data class for climate analysis results."""
    average_temperature: float
    temperature_range: Tuple[float, float]
    average_humidity: float
    total_precipitation: float
    rainy_days: int
    extreme_weather_risk: str
    daylight_hours: float
    comfort_score: float  # 0-1 scale
    recommendation: str


class TripWeatherService:
    """
    Service for analyzing weather and climate conditions for trip planning.
    """
    
    def __init__(self):
        self.openweather_api_key = None  # Will be set from environment
        self.base_url = "http://api.openweathermap.org/data/2.5"
        
    def analyze_trip_weather(self, locations: List[Dict], start_date: str, end_date: str) -> Dict:
        """
        Analyze weather conditions for a trip across multiple locations.
        
        Args:
            locations: List of location dictionaries with 'latitude', 'longitude', 'name'
            start_date: Trip start date in YYYY-MM-DD format
            end_date: Trip end date in YYYY-MM-DD format
            
        Returns:
            Dictionary containing weather analysis for each location
        """
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            trip_duration = (end_dt - start_dt).days + 1
            
            weather_analysis = {
                "trip_dates": {
                    "start_date": start_date,
                    "end_date": end_date,
                    "duration_days": trip_duration
                },
                "locations": {},
                "overall_weather_score": 0.0,
                "weather_recommendations": [],
                "extreme_weather_warnings": []
            }
            
            total_score = 0
            location_count = 0
            
            for location in locations:
                location_name = location.get('name', f"Location {location_count + 1}")
                lat = location.get('latitude')
                lon = location.get('longitude')
                
                if not lat or not lon:
                    logger.warning(f"Missing coordinates for location: {location_name}")
                    continue
                
                # Get weather forecast for this location
                location_weather = self._get_location_weather_analysis(
                    lat, lon, location_name, start_date, end_date
                )
                
                if location_weather:
                    weather_analysis["locations"][location_name] = location_weather
                    total_score += location_weather.get("climate_analysis", {}).get("comfort_score", 0.5)
                    location_count += 1
                    
                    # Collect recommendations and warnings
                    if location_weather.get("climate_analysis", {}).get("recommendation"):
                        weather_analysis["weather_recommendations"].append({
                            "location": location_name,
                            "recommendation": location_weather["climate_analysis"]["recommendation"]
                        })
                    
                    if location_weather.get("climate_analysis", {}).get("extreme_weather_risk") != "low":
                        weather_analysis["extreme_weather_warnings"].append({
                            "location": location_name,
                            "risk_level": location_weather["climate_analysis"]["extreme_weather_risk"],
                            "details": location_weather["climate_analysis"].get("recommendation", "")
                        })
            
            # Calculate overall weather score
            if location_count > 0:
                weather_analysis["overall_weather_score"] = total_score / location_count
            
            # Generate overall recommendations
            weather_analysis["overall_recommendations"] = self._generate_overall_weather_recommendations(
                weather_analysis
            )
            
            return weather_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing trip weather: {e}")
            return {
                "error": str(e),
                "trip_dates": {"start_date": start_date, "end_date": end_date},
                "locations": {},
                "overall_weather_score": 0.5,
                "weather_recommendations": [],
                "extreme_weather_warnings": []
            }
    
    def _get_location_weather_analysis(self, latitude: float, longitude: float, 
                                     location_name: str, start_date: str, end_date: str) -> Optional[Dict]:
        """Get weather analysis for a specific location."""
        try:
            # Get current weather
            current_weather = self._get_current_weather(latitude, longitude)
            
            # Get forecast (if API key available)
            forecast_weather = self._get_weather_forecast(latitude, longitude, start_date, end_date)
            
            # Analyze climate conditions
            climate_analysis = self._analyze_climate_conditions(
                current_weather, forecast_weather, start_date, end_date
            )
            
            return {
                "location": {
                    "name": location_name,
                    "latitude": latitude,
                    "longitude": longitude
                },
                "current_weather": current_weather,
                "forecast_weather": forecast_weather,
                "climate_analysis": climate_analysis
            }
            
        except Exception as e:
            logger.error(f"Error getting weather analysis for {location_name}: {e}")
            return None
    
    def _get_current_weather(self, latitude: float, longitude: float) -> Optional[Dict]:
        """Get current weather conditions."""
        try:
            # For now, return mock data. In production, integrate with OpenWeatherMap API
            return {
                "temperature": 28.5,
                "feels_like": 32.1,
                "humidity": 75,
                "precipitation": 0.0,
                "wind_speed": 12.5,
                "description": "Partly cloudy",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "data_source": "mock"  # Will be "openweathermap" when integrated
            }
        except Exception as e:
            logger.error(f"Error getting current weather: {e}")
            return None
    
    def _get_weather_forecast(self, latitude: float, longitude: float, 
                            start_date: str, end_date: str) -> List[Dict]:
        """Get weather forecast for the trip period."""
        try:
            # For now, return mock forecast data
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            
            forecast = []
            current_date = start_dt
            
            while current_date <= end_dt:
                # Mock weather data - in production, use OpenWeatherMap API
                forecast.append({
                    "date": current_date.strftime("%Y-%m-%d"),
                    "temperature": 28.5 + (current_date.day % 7) * 2,  # Vary temperature
                    "feels_like": 32.1 + (current_date.day % 7) * 2,
                    "humidity": 70 + (current_date.day % 5) * 5,
                    "precipitation": 0.0 if current_date.day % 3 != 0 else 5.2,
                    "wind_speed": 10.0 + (current_date.day % 4) * 3,
                    "description": "Sunny" if current_date.day % 3 != 0 else "Light rain",
                    "data_source": "mock"
                })
                current_date += timedelta(days=1)
            
            return forecast
            
        except Exception as e:
            logger.error(f"Error getting weather forecast: {e}")
            return []
    
    def _analyze_climate_conditions(self, current_weather: Optional[Dict], 
                                  forecast_weather: List[Dict], 
                                  start_date: str, end_date: str) -> Dict:
        """Analyze climate conditions and provide recommendations."""
        try:
            if not forecast_weather:
                return self._get_default_climate_analysis()
            
            # Calculate statistics
            temperatures = [day["temperature"] for day in forecast_weather]
            humidities = [day["humidity"] for day in forecast_weather]
            precipitations = [day["precipitation"] for day in forecast_weather]
            
            avg_temp = sum(temperatures) / len(temperatures)
            temp_range = (min(temperatures), max(temperatures))
            avg_humidity = sum(humidities) / len(humidities)
            total_precipitation = sum(precipitations)
            rainy_days = sum(1 for p in precipitations if p > 0)
            
            # Calculate daylight hours (approximate)
            daylight_hours = self._calculate_daylight_hours(start_date, end_date)
            
            # Assess extreme weather risk
            extreme_weather_risk = self._assess_extreme_weather_risk(
                avg_temp, avg_humidity, total_precipitation, rainy_days
            )
            
            # Calculate comfort score
            comfort_score = self._calculate_comfort_score(
                avg_temp, avg_humidity, total_precipitation, rainy_days
            )
            
            # Generate recommendation
            recommendation = self._generate_weather_recommendation(
                avg_temp, avg_humidity, total_precipitation, rainy_days, 
                extreme_weather_risk, comfort_score
            )
            
            return {
                "average_temperature": round(avg_temp, 1),
                "temperature_range": (round(temp_range[0], 1), round(temp_range[1], 1)),
                "average_humidity": round(avg_humidity, 1),
                "total_precipitation": round(total_precipitation, 1),
                "rainy_days": rainy_days,
                "extreme_weather_risk": extreme_weather_risk,
                "daylight_hours": round(daylight_hours, 1),
                "comfort_score": round(comfort_score, 2),
                "recommendation": recommendation
            }
            
        except Exception as e:
            logger.error(f"Error analyzing climate conditions: {e}")
            return self._get_default_climate_analysis()
    
    def _calculate_daylight_hours(self, start_date: str, end_date: str) -> float:
        """Calculate average daylight hours for the trip period."""
        try:
            # Simplified calculation - in production, use more accurate astronomical calculations
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            
            # Approximate daylight hours based on month (for Northern Hemisphere)
            month = start_dt.month
            if month in [12, 1, 2]:  # Winter
                return 10.0
            elif month in [3, 4, 5]:  # Spring
                return 12.0
            elif month in [6, 7, 8]:  # Summer
                return 14.0
            else:  # Fall
                return 11.0
                
        except Exception:
            return 12.0  # Default value
    
    def _assess_extreme_weather_risk(self, avg_temp: float, avg_humidity: float, 
                                   total_precipitation: float, rainy_days: int) -> str:
        """Assess the risk of extreme weather conditions."""
        risk_score = 0
        
        # Temperature risk
        if avg_temp > 35 or avg_temp < 0:
            risk_score += 2
        elif avg_temp > 30 or avg_temp < 5:
            risk_score += 1
        
        # Humidity risk
        if avg_humidity > 80:
            risk_score += 1
        
        # Precipitation risk
        if total_precipitation > 50:  # High precipitation
            risk_score += 2
        elif total_precipitation > 20:
            risk_score += 1
        
        # Rainy days risk
        if rainy_days > 5:
            risk_score += 1
        
        if risk_score >= 4:
            return "high"
        elif risk_score >= 2:
            return "medium"
        else:
            return "low"
    
    def _calculate_comfort_score(self, avg_temp: float, avg_humidity: float, 
                               total_precipitation: float, rainy_days: int) -> float:
        """Calculate comfort score (0-1, higher is better)."""
        score = 1.0
        
        # Temperature comfort (optimal range: 20-25°C)
        if 20 <= avg_temp <= 25:
            temp_score = 1.0
        elif 15 <= avg_temp <= 30:
            temp_score = 0.8
        elif 10 <= avg_temp <= 35:
            temp_score = 0.6
        else:
            temp_score = 0.3
        
        # Humidity comfort (optimal: 40-60%)
        if 40 <= avg_humidity <= 60:
            humidity_score = 1.0
        elif 30 <= avg_humidity <= 70:
            humidity_score = 0.8
        elif 20 <= avg_humidity <= 80:
            humidity_score = 0.6
        else:
            humidity_score = 0.4
        
        # Precipitation comfort
        if total_precipitation < 10:
            precip_score = 1.0
        elif total_precipitation < 25:
            precip_score = 0.8
        elif total_precipitation < 50:
            precip_score = 0.6
        else:
            precip_score = 0.3
        
        # Rainy days comfort
        if rainy_days <= 2:
            rainy_score = 1.0
        elif rainy_days <= 4:
            rainy_score = 0.8
        elif rainy_days <= 6:
            rainy_score = 0.6
        else:
            rainy_score = 0.4
        
        # Weighted average
        final_score = (temp_score * 0.4 + humidity_score * 0.3 + 
                      precip_score * 0.2 + rainy_score * 0.1)
        
        return max(0.0, min(1.0, final_score))
    
    def _generate_weather_recommendation(self, avg_temp: float, avg_humidity: float, 
                                       total_precipitation: float, rainy_days: int,
                                       extreme_weather_risk: str, comfort_score: float) -> str:
        """Generate weather-based recommendation."""
        recommendations = []
        
        # Temperature recommendations
        if avg_temp > 35:
            recommendations.append("Extremely hot weather - bring sun protection and stay hydrated")
        elif avg_temp > 30:
            recommendations.append("Hot weather - light clothing and sun protection recommended")
        elif avg_temp < 5:
            recommendations.append("Cold weather - warm clothing essential")
        elif avg_temp < 10:
            recommendations.append("Cool weather - bring layers and warm clothing")
        
        # Humidity recommendations
        if avg_humidity > 80:
            recommendations.append("High humidity - expect muggy conditions")
        elif avg_humidity < 30:
            recommendations.append("Low humidity - stay hydrated and use moisturizer")
        
        # Precipitation recommendations
        if total_precipitation > 50:
            recommendations.append("Heavy rainfall expected - bring rain gear and waterproof items")
        elif total_precipitation > 20:
            recommendations.append("Moderate rainfall - pack umbrella and rain jacket")
        elif rainy_days > 5:
            recommendations.append("Frequent rain - waterproof gear recommended")
        
        # Overall comfort recommendation
        if comfort_score >= 0.8:
            recommendations.append("Excellent weather conditions for tourism")
        elif comfort_score >= 0.6:
            recommendations.append("Good weather conditions with minor considerations")
        elif comfort_score >= 0.4:
            recommendations.append("Moderate weather conditions - plan accordingly")
        else:
            recommendations.append("Challenging weather conditions - consider rescheduling")
        
        # Extreme weather warning
        if extreme_weather_risk == "high":
            recommendations.append("⚠️ HIGH RISK: Extreme weather conditions expected")
        elif extreme_weather_risk == "medium":
            recommendations.append("⚠️ MODERATE RISK: Monitor weather conditions closely")
        
        return "; ".join(recommendations) if recommendations else "Weather conditions are generally suitable for travel"
    
    def _generate_overall_weather_recommendations(self, weather_analysis: Dict) -> List[str]:
        """Generate overall weather recommendations for the entire trip."""
        recommendations = []
        
        overall_score = weather_analysis.get("overall_weather_score", 0.5)
        warnings = weather_analysis.get("extreme_weather_warnings", [])
        
        # Overall score recommendation
        if overall_score >= 0.8:
            recommendations.append("🌤️ Excellent weather conditions across all destinations")
        elif overall_score >= 0.6:
            recommendations.append("🌤️ Good weather conditions with minor considerations")
        elif overall_score >= 0.4:
            recommendations.append("🌤️ Moderate weather conditions - plan accordingly")
        else:
            recommendations.append("🌤️ Challenging weather conditions - consider rescheduling")
        
        # Extreme weather warnings
        if warnings:
            high_risk_locations = [w["location"] for w in warnings if w["risk_level"] == "high"]
            if high_risk_locations:
                recommendations.append(f"⚠️ HIGH WEATHER RISK in: {', '.join(high_risk_locations)}")
            
            medium_risk_locations = [w["location"] for w in warnings if w["risk_level"] == "medium"]
            if medium_risk_locations:
                recommendations.append(f"⚠️ MODERATE WEATHER RISK in: {', '.join(medium_risk_locations)}")
        
        return recommendations
    
    def _get_default_climate_analysis(self) -> Dict:
        """Get default climate analysis when weather data is unavailable."""
        return {
            "average_temperature": 25.0,
            "temperature_range": (20.0, 30.0),
            "average_humidity": 60.0,
            "total_precipitation": 10.0,
            "rainy_days": 2,
            "extreme_weather_risk": "low",
            "daylight_hours": 12.0,
            "comfort_score": 0.7,
            "recommendation": "Weather data unavailable - check local forecasts before travel"
        }


# Global instance
trip_weather_service = TripWeatherService()
