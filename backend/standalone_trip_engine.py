#!/usr/bin/env python3
"""
Standalone Trip Recommendation Engine

This version can be run independently without Django imports.
It uses mock data and simplified logic for testing purposes.
"""

import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class TripRecommendation:
    """Data class for trip recommendation results."""
    overall_score: float
    recommendation: str
    confidence: float
    key_factors: List[str]
    suggestions: List[str]
    warnings: List[str]
    weather_analysis: Dict
    tourist_analysis: Dict
    safety_analysis: Dict
    cost_analysis: Dict


class StandaloneTripWeatherService:
    """Standalone weather service with mock data."""
    
    def analyze_trip_weather(self, locations: List[Dict], start_date: str, end_date: str) -> Dict:
        """Analyze weather conditions for trip locations."""
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            duration_days = (end_dt - start_dt).days + 1
            
            weather_analysis = {
                "overall_weather_score": 0.0,
                "locations": {},
                "weather_recommendations": [],
                "extreme_weather_warnings": [],
                "trip_duration_days": duration_days,
                "analysis_date": datetime.now().isoformat()
            }
            
            total_score = 0
            location_count = 0
            
            for location in locations:
                location_name = location.get('name', f"Location {location_count + 1}")
                lat = location.get('latitude', 0)
                lon = location.get('longitude', 0)
                
                # Mock weather data based on location and season
                weather_score = self._calculate_weather_score(lat, lon, start_dt)
                
                weather_analysis["locations"][location_name] = {
                    "weather_score": round(weather_score, 2),
                    "temperature_range": self._get_temperature_range(lat, lon, start_dt),
                    "precipitation_risk": self._get_precipitation_risk(lat, lon, start_dt),
                    "humidity_level": self._get_humidity_level(lat, lon, start_dt),
                    "wind_conditions": self._get_wind_conditions(lat, lon, start_dt),
                    "visibility": self._get_visibility(lat, lon, start_dt),
                    "uv_index": self._get_uv_index(lat, lon, start_dt),
                    "air_quality": self._get_air_quality(lat, lon, start_dt)
                }
                
                total_score += weather_score
                location_count += 1
                
                # Add weather recommendations
                if weather_score >= 0.8:
                    weather_analysis["weather_recommendations"].append(
                        f"Excellent weather conditions in {location_name}"
                    )
                elif weather_score <= 0.3:
                    weather_analysis["weather_recommendations"].append(
                        f"Challenging weather conditions in {location_name}"
                    )
                
                # Add extreme weather warnings
                if weather_score <= 0.2:
                    weather_analysis["extreme_weather_warnings"].append({
                        "location": location_name,
                        "risk_level": "high",
                        "details": "Extreme weather conditions expected"
                    })
            
            # Calculate overall weather score
            if location_count > 0:
                weather_analysis["overall_weather_score"] = total_score / location_count
            
            return weather_analysis
            
        except Exception as e:
            return {
                "overall_weather_score": 0.5,
                "locations": {},
                "weather_recommendations": ["Weather analysis unavailable"],
                "extreme_weather_warnings": [],
                "error": str(e)
            }
    
    def _calculate_weather_score(self, lat: float, lon: float, date: datetime) -> float:
        """Calculate weather score based on location and date."""
        # Mock calculation based on location and season
        base_score = 0.7
        
        # Adjust for season
        month = date.month
        if month in [12, 1, 2]:  # Winter
            base_score += 0.1
        elif month in [6, 7, 8]:  # Summer
            base_score -= 0.1
        
        # Adjust for location (tropical vs temperate)
        if abs(lat) < 30:  # Tropical
            base_score -= 0.1
        
        return max(0.0, min(1.0, base_score + random.uniform(-0.2, 0.2)))
    
    def _get_temperature_range(self, lat: float, lon: float, date: datetime) -> str:
        """Get temperature range for location and date."""
        if abs(lat) < 30:  # Tropical
            return "25-35°C (Warm to Hot)"
        else:  # Temperate
            return "15-25°C (Mild to Warm)"
    
    def _get_precipitation_risk(self, lat: float, lon: float, date: datetime) -> str:
        """Get precipitation risk."""
        risks = ["Low", "Moderate", "High"]
        return random.choice(risks)
    
    def _get_humidity_level(self, lat: float, lon: float, date: datetime) -> str:
        """Get humidity level."""
        if abs(lat) < 30:  # Tropical
            return "High (70-90%)"
        else:
            return "Moderate (50-70%)"
    
    def _get_wind_conditions(self, lat: float, lon: float, date: datetime) -> str:
        """Get wind conditions."""
        return "Light to Moderate"
    
    def _get_visibility(self, lat: float, lon: float, date: datetime) -> str:
        """Get visibility conditions."""
        return "Good to Excellent"
    
    def _get_uv_index(self, lat: float, lon: float, date: datetime) -> str:
        """Get UV index."""
        if abs(lat) < 30:  # Tropical
            return "High (7-10)"
        else:
            return "Moderate (3-6)"
    
    def _get_air_quality(self, lat: float, lon: float, date: datetime) -> str:
        """Get air quality."""
        return "Good"


class StandaloneTripTouristFactorsService:
    """Standalone tourist factors service with mock data."""
    
    def analyze_tourist_factors(self, locations: List[Dict], start_date: str, end_date: str) -> Dict:
        """Analyze tourist-related factors for trip locations."""
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            duration_days = (end_dt - start_dt).days + 1
            
            tourist_analysis = {
                "overall_tourist_score": 0.0,
                "locations": {},
                "tourist_recommendations": [],
                "safety_warnings": [],
                "trip_duration_days": duration_days,
                "analysis_date": datetime.now().isoformat()
            }
            
            total_score = 0
            location_count = 0
            
            for location in locations:
                location_name = location.get('name', f"Location {location_count + 1}")
                country = location.get('country', 'Unknown')
                
                # Mock tourist factors analysis
                tourist_score = self._calculate_tourist_score(country, start_dt)
                
                tourist_analysis["locations"][location_name] = {
                    "tourist_score": round(tourist_score, 2),
                    "peak_season": self._get_peak_season(country, start_dt),
                    "local_events": self._get_local_events(country, start_dt),
                    "cultural_factors": self._get_cultural_factors(country),
                    "transport_availability": self._get_transport_availability(country),
                    "safety_advisories": self._get_safety_advisories(country),
                    "health_requirements": self._get_health_requirements(country),
                    "language_barrier": self._get_language_barrier(country)
                }
                
                total_score += tourist_score
                location_count += 1
                
                # Add tourist recommendations
                if tourist_score >= 0.8:
                    tourist_analysis["tourist_recommendations"].append(
                        f"Excellent tourist conditions in {location_name}"
                    )
                elif tourist_score <= 0.3:
                    tourist_analysis["tourist_recommendations"].append(
                        f"Limited tourist amenities in {location_name}"
                    )
                
                # Add safety warnings
                if tourist_score <= 0.2:
                    tourist_analysis["safety_warnings"].append({
                        "location": location_name,
                        "level": "high",
                        "details": "Significant tourist safety concerns"
                    })
            
            # Calculate overall tourist score
            if location_count > 0:
                tourist_analysis["overall_tourist_score"] = total_score / location_count
            
            return tourist_analysis
            
        except Exception as e:
            return {
                "overall_tourist_score": 0.5,
                "locations": {},
                "tourist_recommendations": ["Tourist analysis unavailable"],
                "safety_warnings": [],
                "error": str(e)
            }
    
    def _calculate_tourist_score(self, country: str, date: datetime) -> float:
        """Calculate tourist score based on country and date."""
        base_score = 0.7
        
        # Adjust for country
        if country.lower() in ['india', 'thailand', 'singapore']:
            base_score += 0.1
        elif country.lower() in ['afghanistan', 'syria', 'yemen']:
            base_score -= 0.3
        
        # Adjust for season
        month = date.month
        if month in [12, 1, 2, 3]:  # Peak tourist season
            base_score += 0.1
        
        return max(0.0, min(1.0, base_score + random.uniform(-0.2, 0.2)))
    
    def _get_peak_season(self, country: str, date: datetime) -> str:
        """Get peak season information."""
        month = date.month
        if month in [12, 1, 2, 3]:
            return "Peak Season - Higher prices, more crowds"
        else:
            return "Off Season - Better prices, fewer crowds"
    
    def _get_local_events(self, country: str, date: datetime) -> str:
        """Get local events information."""
        events = ["No major events", "Local festival", "Cultural celebration", "Sports event"]
        return random.choice(events)
    
    def _get_cultural_factors(self, country: str) -> str:
        """Get cultural factors."""
        if country.lower() == 'india':
            return "Tourist-friendly with some cultural considerations"
        else:
            return "Generally tourist-friendly"
    
    def _get_transport_availability(self, country: str) -> str:
        """Get transport availability."""
        if country.lower() in ['india', 'thailand', 'singapore']:
            return "Good - Multiple options available"
        else:
            return "Moderate - Limited options"
    
    def _get_safety_advisories(self, country: str) -> str:
        """Get safety advisories."""
        if country.lower() in ['afghanistan', 'syria', 'yemen']:
            return "High risk - Travel not recommended"
        else:
            return "No major safety concerns"
    
    def _get_health_requirements(self, country: str) -> str:
        """Get health requirements."""
        return "Standard vaccinations recommended"
    
    def _get_language_barrier(self, country: str) -> str:
        """Get language barrier information."""
        if country.lower() in ['india', 'singapore']:
            return "English widely spoken"
        else:
            return "Limited English, learn basic phrases"


class StandaloneTripRecommendationEngine:
    """Standalone trip recommendation engine."""
    
    def __init__(self):
        self.weights = {
            "weather": 0.25,
            "tourist_factors": 0.20,
            "safety_score": 0.30,
            "user_feedback": 0.15,
            "cost_effectiveness": 0.10
        }
        
        self.recommendation_thresholds = {
            "proceed": 0.8,
            "proceed_with_caution": 0.6,
            "reconsider": 0.4
        }
        
        self.weather_service = StandaloneTripWeatherService()
        self.tourist_service = StandaloneTripTouristFactorsService()
    
    def generate_trip_recommendation(self, trip_details: Dict) -> Dict:
        """Generate comprehensive trip recommendation."""
        try:
            # Extract trip details
            start_date = trip_details.get("start_date")
            end_date = trip_details.get("end_date")
            locations = trip_details.get("locations", [])
            budget = trip_details.get("budget", {})
            traveler_profile = trip_details.get("traveler_profile", {})
            
            if not start_date or not end_date or not locations:
                return {
                    "error": "Missing required trip details (start_date, end_date, locations)"
                }
            
            # Analyze weather conditions
            weather_analysis = self.weather_service.analyze_trip_weather(
                locations, start_date, end_date
            )
            
            # Analyze tourist factors
            tourist_analysis = self.tourist_service.analyze_tourist_factors(
                locations, start_date, end_date
            )
            
            # Analyze safety scores (mock)
            safety_analysis = self._analyze_safety_scores(locations)
            
            # Analyze user feedback (mock)
            feedback_analysis = self._analyze_user_feedback(locations)
            
            # Analyze cost effectiveness
            cost_analysis = self._analyze_cost_effectiveness(budget, locations)
            
            # Calculate overall score
            weather_score = weather_analysis.get("overall_weather_score", 0.5)
            tourist_score = tourist_analysis.get("overall_tourist_score", 0.5)
            safety_score = safety_analysis.get("overall_safety_score", 0.5)
            feedback_score = feedback_analysis.get("overall_feedback_score", 0.5)
            cost_score = cost_analysis.get("cost_effectiveness_score", 0.5)
            
            overall_score = (
                weather_score * self.weights["weather"] +
                tourist_score * self.weights["tourist_factors"] +
                safety_score * self.weights["safety_score"] +
                feedback_score * self.weights["user_feedback"] +
                cost_score * self.weights["cost_effectiveness"]
            )
            
            # Determine recommendation
            if overall_score >= self.recommendation_thresholds["proceed"]:
                recommendation = "proceed"
                confidence = min(0.95, overall_score + 0.1)
            elif overall_score >= self.recommendation_thresholds["proceed_with_caution"]:
                recommendation = "proceed_with_caution"
                confidence = overall_score
            elif overall_score >= self.recommendation_thresholds["reconsider"]:
                recommendation = "reconsider"
                confidence = overall_score
            else:
                recommendation = "not_recommended"
                confidence = 1.0 - overall_score
            
            # Generate key factors and suggestions
            key_factors = self._generate_key_factors(
                weather_score, tourist_score, safety_score, feedback_score, cost_score
            )
            
            suggestions = self._generate_suggestions(recommendation, weather_analysis, safety_analysis)
            warnings = self._generate_warnings(weather_analysis, tourist_analysis, safety_analysis)
            
            return {
                "success": True,
                "data": {
                    "recommendation": {
                        "overall_score": round(overall_score, 2),
                        "recommendation": recommendation,
                        "confidence": round(confidence, 2),
                        "key_factors": key_factors,
                        "suggestions": suggestions,
                        "warnings": warnings
                    },
                    "weather_analysis": weather_analysis,
                    "tourist_analysis": tourist_analysis,
                    "safety_analysis": safety_analysis,
                    "feedback_analysis": feedback_analysis,
                    "cost_analysis": cost_analysis
                }
            }
            
        except Exception as e:
            return {
                "error": f"Error generating trip recommendation: {str(e)}"
            }
    
    def _analyze_safety_scores(self, locations: List[Dict]) -> Dict:
        """Analyze safety scores for locations (mock)."""
        safety_analysis = {
            "locations": {},
            "overall_safety_score": 0.0,
            "safety_recommendations": [],
            "high_risk_locations": []
        }
        
        total_score = 0
        location_count = 0
        
        for location in locations:
            location_name = location.get('name', f"Location {location_count + 1}")
            # Mock safety score
            safety_score = random.uniform(0.4, 0.9)
            
            safety_analysis["locations"][location_name] = {
                "safety_score": round(safety_score, 2),
                "normalized_score": round(safety_score, 2),
                "has_sufficient_feedback": False,
                "feedback_count": 0,
                "scoring_method": "ai_only"
            }
            
            total_score += safety_score
            location_count += 1
            
            if safety_score < 0.4:
                safety_analysis["high_risk_locations"].append({
                    "location": location_name,
                    "safety_score": safety_score,
                    "risk_level": "high"
                })
        
        if location_count > 0:
            safety_analysis["overall_safety_score"] = total_score / location_count
        
        return safety_analysis
    
    def _analyze_user_feedback(self, locations: List[Dict]) -> Dict:
        """Analyze user feedback for locations (mock)."""
        return {
            "locations": {},
            "overall_feedback_score": 0.5,
            "feedback_recommendations": [],
            "locations_needing_feedback": []
        }
    
    def _analyze_cost_effectiveness(self, budget: Dict, locations: List[Dict]) -> Dict:
        """Analyze cost effectiveness (mock)."""
        return {
            "cost_effectiveness_score": 0.7,
            "budget_compatibility": "good",
            "cost_recommendations": []
        }
    
    def _generate_key_factors(self, weather_score: float, tourist_score: float, 
                            safety_score: float, feedback_score: float, cost_score: float) -> List[str]:
        """Generate key factors based on scores."""
        factors = []
        
        if weather_score >= 0.8:
            factors.append("Excellent weather conditions")
        elif weather_score <= 0.3:
            factors.append("Challenging weather conditions")
        
        if tourist_score >= 0.8:
            factors.append("Great tourist conditions")
        elif tourist_score <= 0.3:
            factors.append("Limited tourist amenities")
        
        if safety_score >= 0.8:
            factors.append("High safety rating")
        elif safety_score <= 0.3:
            factors.append("Safety concerns")
        
        if feedback_score >= 0.8:
            factors.append("Positive user feedback")
        elif feedback_score <= 0.3:
            factors.append("Limited user feedback")
        
        if cost_score >= 0.8:
            factors.append("Excellent value for money")
        elif cost_score <= 0.3:
            factors.append("High costs")
        
        return factors
    
    def _generate_suggestions(self, recommendation: str, weather_analysis: Dict, safety_analysis: Dict) -> List[str]:
        """Generate suggestions based on recommendation."""
        suggestions = []
        
        if recommendation == "proceed":
            suggestions.append("✅ Trip is highly recommended - proceed with confidence")
            suggestions.append("📋 Book accommodations and attractions in advance")
            suggestions.append("🎒 Pack according to weather conditions")
        elif recommendation == "proceed_with_caution":
            suggestions.append("⚠️ Trip is recommended with some precautions")
            suggestions.append("📋 Research specific locations and plan accordingly")
            suggestions.append("🎒 Pack for variable conditions")
        elif recommendation == "reconsider":
            suggestions.append("🤔 Consider alternative dates or destinations")
            suggestions.append("📋 Review all concerns before booking")
            suggestions.append("🎒 Prepare for challenging conditions")
        else:
            suggestions.append("❌ Trip is not recommended at this time")
            suggestions.append("📋 Consider alternative destinations or dates")
            suggestions.append("🎒 Wait for better conditions")
        
        return suggestions
    
    def _generate_warnings(self, weather_analysis: Dict, tourist_analysis: Dict, safety_analysis: Dict) -> List[str]:
        """Generate warnings based on analysis."""
        warnings = []
        
        # Weather warnings
        weather_warnings = weather_analysis.get("extreme_weather_warnings", [])
        for warning in weather_warnings:
            if warning.get("risk_level") == "high":
                warnings.append(f"⚠️ HIGH WEATHER RISK in {warning['location']}: {warning['details']}")
        
        # Safety warnings
        safety_warnings = safety_analysis.get("high_risk_locations", [])
        for warning in safety_warnings:
            warnings.append(f"⚠️ HIGH SAFETY RISK in {warning['location']} (Score: {warning['safety_score']:.1f})")
        
        # Tourist warnings
        tourist_warnings = tourist_analysis.get("safety_warnings", [])
        for warning in tourist_warnings:
            warnings.append(f"⚠️ Tourist safety concern in {warning['location']}")
        
        return warnings


def main():
    """Test the standalone trip recommendation engine."""
    print("🧪 Testing Standalone Trip Recommendation Engine")
    print("=" * 60)
    
    # Create engine instance
    engine = StandaloneTripRecommendationEngine()
    
    # Test trip details
    trip_details = {
        "start_date": "2024-03-15",
        "end_date": "2024-03-22",
        "locations": [
            {
                "latitude": 13.049953,
                "longitude": 80.282403,
                "name": "Marina Beach, Chennai",
                "country": "India"
            }
        ],
        "budget": {
            "total": 1500,
            "per_day": 200,
            "currency": "USD"
        },
        "traveler_profile": {
            "experience_level": "beginner",
            "preferences": ["beaches", "cultural_sites"],
            "group_size": 2
        }
    }
    
    # Generate recommendation
    result = engine.generate_trip_recommendation(trip_details)
    
    if result.get("error"):
        print(f"❌ Error: {result['error']}")
        return
    
    if result.get("success"):
        data = result["data"]
        rec = data["recommendation"]
        
        print(f"✅ Trip Recommendation Generated")
        print(f"Overall Score: {rec['overall_score']:.2f}/1.0")
        print(f"Recommendation: {rec['recommendation']}")
        print(f"Confidence: {rec['confidence']:.2f}")
        
        print(f"\n🎯 Key Factors:")
        for factor in rec['key_factors']:
            print(f"  • {factor}")
        
        print(f"\n💡 Suggestions:")
        for suggestion in rec['suggestions']:
            print(f"  • {suggestion}")
        
        if rec['warnings']:
            print(f"\n⚠️ Warnings:")
            for warning in rec['warnings']:
                print(f"  • {warning}")
        
        print(f"\n📊 Detailed Analysis:")
        print(f"  Weather Score: {data['weather_analysis']['overall_weather_score']:.2f}")
        print(f"  Tourist Score: {data['tourist_analysis']['overall_tourist_score']:.2f}")
        print(f"  Safety Score: {data['safety_analysis']['overall_safety_score']:.2f}")
        print(f"  Feedback Score: {data['feedback_analysis']['overall_feedback_score']:.2f}")
        print(f"  Cost Score: {data['cost_analysis']['cost_effectiveness_score']:.2f}")
        
        print(f"\n🎉 Standalone engine working perfectly!")
    else:
        print(f"❌ Failed to generate recommendation")


if __name__ == "__main__":
    main()
