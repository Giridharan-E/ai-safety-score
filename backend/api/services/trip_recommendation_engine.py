"""
Trip Recommendation Engine

This service combines weather analysis, tourist factors, safety scores, and other
factors to provide comprehensive trip recommendations for tourists.
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

from .trip_weather_service import trip_weather_service
from .trip_tourist_factors_service import trip_tourist_factors_service
from .scoring_engine import scoring_engine
from .feedback_aggregation_service import feedback_aggregation_service

logger = logging.getLogger(__name__)


@dataclass
class TripRecommendation:
    """Data class for trip recommendations."""
    overall_score: float  # 0-1 scale
    recommendation: str  # proceed, proceed_with_caution, reconsider, not_recommended
    confidence: float  # 0-1 scale
    key_factors: List[str]
    warnings: List[str]
    suggestions: List[str]


class TripRecommendationEngine:
    """
    Main engine for generating comprehensive trip recommendations.
    """
    
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
            "reconsider": 0.4,
            "not_recommended": 0.0
        }
    
    def generate_trip_recommendation(self, trip_details: Dict) -> Dict:
        """
        Generate comprehensive trip recommendation based on multiple factors.
        
        Args:
            trip_details: Dictionary containing:
                - start_date: Trip start date (YYYY-MM-DD)
                - end_date: Trip end date (YYYY-MM-DD)
                - locations: List of location dictionaries with lat/lon/name/country
                - budget: Optional budget information
                - traveler_profile: Optional traveler preferences
                
        Returns:
            Dictionary containing comprehensive trip recommendation
        """
        try:
            start_date = trip_details.get("start_date")
            end_date = trip_details.get("end_date")
            locations = trip_details.get("locations", [])
            budget = trip_details.get("budget")
            traveler_profile = trip_details.get("traveler_profile", {})
            
            if not start_date or not end_date or not locations:
                return {
                    "error": "Missing required trip details (start_date, end_date, locations)",
                    "recommendation": "not_recommended"
                }
            
            # Validate trip dates
            try:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                if start_dt >= end_dt:
                    return {
                        "error": "End date must be after start date",
                        "recommendation": "not_recommended"
                    }
            except ValueError:
                return {
                    "error": "Invalid date format. Use YYYY-MM-DD",
                    "recommendation": "not_recommended"
                }
            
            # Analyze weather conditions
            weather_analysis = trip_weather_service.analyze_trip_weather(
                locations, start_date, end_date
            )
            
            # Analyze tourist factors
            tourist_analysis = trip_tourist_factors_service.analyze_tourist_factors(
                locations, start_date, end_date
            )
            
            # Analyze safety scores for each location
            safety_analysis = self._analyze_safety_scores(locations)
            
            # Analyze user feedback for locations
            feedback_analysis = self._analyze_user_feedback(locations)
            
            # Calculate cost effectiveness
            cost_analysis = self._analyze_cost_effectiveness(
                locations, budget, tourist_analysis
            )
            
            # Generate overall recommendation
            recommendation = self._generate_overall_recommendation(
                weather_analysis, tourist_analysis, safety_analysis,
                feedback_analysis, cost_analysis, traveler_profile
            )
            
            # Compile comprehensive response
            trip_recommendation = {
                "trip_details": {
                    "start_date": start_date,
                    "end_date": end_date,
                    "duration_days": (end_dt - start_dt).days + 1,
                    "locations": locations,
                    "budget": budget,
                    "traveler_profile": traveler_profile
                },
                "analysis": {
                    "weather": weather_analysis,
                    "tourist_factors": tourist_analysis,
                    "safety": safety_analysis,
                    "user_feedback": feedback_analysis,
                    "cost": cost_analysis
                },
                "recommendation": recommendation,
                "generated_at": datetime.now().isoformat()
            }
            
            return trip_recommendation
            
        except Exception as e:
            logger.error(f"Error generating trip recommendation: {e}")
            return {
                "error": str(e),
                "recommendation": "not_recommended",
                "generated_at": datetime.now().isoformat()
            }
    
    def _analyze_safety_scores(self, locations: List[Dict]) -> Dict:
        """Analyze safety scores for all locations."""
        try:
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
                lat = location.get('latitude')
                lon = location.get('longitude')
                
                if not lat or not lon:
                    continue
                
                # Get safety score using existing scoring engine
                try:
                    # Use a simplified feature set for safety scoring
                    features = {
                        "police_stations": 0.5,
                        "hospitals": 0.5,
                        "lighting": 0.5,
                        "visibility": 0.5,
                        "sidewalks": 0.5,
                        "businesses": 0.5,
                        "transport": 0.5,
                        "transport_density": 0.5,
                        "crime_rate": 0.5,
                        "natural_surveillance": 0.5,
                        "user_feedback": 0.5
                    }
                    
                    # Get location-specific safety score
                    safety_score, _, feedback_info = scoring_engine.score_with_location_feedback(
                        features, profile={}, latitude=lat, longitude=lon
                    )
                    
                    # Normalize to 0-1 scale
                    normalized_score = safety_score / 10.0
                    
                    safety_analysis["locations"][location_name] = {
                        "safety_score": round(safety_score, 1),
                        "normalized_score": round(normalized_score, 2),
                        "has_sufficient_feedback": feedback_info.get("has_sufficient_feedback", False),
                        "feedback_count": feedback_info.get("feedback_count", 0),
                        "scoring_method": feedback_info.get("scoring_method", "ai_only")
                    }
                    
                    total_score += normalized_score
                    location_count += 1
                    
                    # Identify high-risk locations
                    if normalized_score < 0.4:
                        safety_analysis["high_risk_locations"].append({
                            "location": location_name,
                            "safety_score": safety_score,
                            "risk_level": "high"
                        })
                    elif normalized_score < 0.6:
                        safety_analysis["safety_recommendations"].append({
                            "location": location_name,
                            "recommendation": f"Moderate safety concerns (Score: {safety_score:.1f})"
                        })
                    
                except Exception as e:
                    logger.error(f"Error getting safety score for {location_name}: {e}")
                    # Use default safety score
                    safety_analysis["locations"][location_name] = {
                        "safety_score": 5.0,
                        "normalized_score": 0.5,
                        "has_sufficient_feedback": False,
                        "feedback_count": 0,
                        "scoring_method": "default"
                    }
                    total_score += 0.5
                    location_count += 1
            
            # Calculate overall safety score
            if location_count > 0:
                safety_analysis["overall_safety_score"] = total_score / location_count
            
            return safety_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing safety scores: {e}")
            return {
                "locations": {},
                "overall_safety_score": 0.5,
                "safety_recommendations": [],
                "high_risk_locations": []
            }
    
    def _analyze_user_feedback(self, locations: List[Dict]) -> Dict:
        """Analyze user feedback for all locations."""
        try:
            feedback_analysis = {
                "locations": {},
                "overall_feedback_score": 0.0,
                "feedback_recommendations": [],
                "locations_needing_feedback": []
            }
            
            total_score = 0
            location_count = 0
            
            for location in locations:
                location_name = location.get('name', f"Location {location_count + 1}")
                lat = location.get('latitude')
                lon = location.get('longitude')
                
                if not lat or not lon:
                    continue
                
                # Get feedback summary for this location
                feedback_summary = feedback_aggregation_service.get_location_feedback_summary(
                    lat, lon, radius=100
                )
                
                feedback_analysis["locations"][location_name] = {
                    "feedback_count": feedback_summary.get("feedback_count", 0),
                    "unique_users": feedback_summary.get("unique_users", 0),
                    "meets_threshold": feedback_summary.get("meets_threshold", False),
                    "average_rating": feedback_summary.get("statistics", {}).get("average_rating", 0),
                    "safety_score": feedback_summary.get("safety_score", 0.5),
                    "recommendations": feedback_summary.get("recommendations", [])
                }
                
                # Add to overall score
                total_score += feedback_summary.get("safety_score", 0.5)
                location_count += 1
                
                # Check if location needs more feedback
                if not feedback_summary.get("meets_threshold", False):
                    feedback_analysis["locations_needing_feedback"].append({
                        "location": location_name,
                        "current_feedbacks": feedback_summary.get("feedback_count", 0),
                        "needed": 50 - feedback_summary.get("feedback_count", 0)
                    })
                
                # Add recommendations
                if feedback_summary.get("recommendations"):
                    feedback_analysis["feedback_recommendations"].extend([
                        {"location": location_name, "recommendation": rec}
                        for rec in feedback_summary["recommendations"]
                    ])
            
            # Calculate overall feedback score
            if location_count > 0:
                feedback_analysis["overall_feedback_score"] = total_score / location_count
            
            return feedback_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing user feedback: {e}")
            return {
                "locations": {},
                "overall_feedback_score": 0.5,
                "feedback_recommendations": [],
                "locations_needing_feedback": []
            }
    
    def _analyze_cost_effectiveness(self, locations: List[Dict], budget: Optional[Dict], 
                                  tourist_analysis: Dict) -> Dict:
        """Analyze cost effectiveness of the trip."""
        try:
            cost_analysis = {
                "estimated_costs": {},
                "budget_compatibility": "unknown",
                "cost_effectiveness_score": 0.5,
                "cost_recommendations": []
            }
            
            # Get cost estimates from tourist analysis
            cost_estimates = tourist_analysis.get("cost_estimates", {})
            
            if cost_estimates:
                total_estimated_cost = 0
                location_count = 0
                
                for location_name, costs in cost_estimates.items():
                    daily_cost = costs.get("total_per_day", 0)
                    cost_analysis["estimated_costs"][location_name] = costs
                    total_estimated_cost += daily_cost
                    location_count += 1
                
                if location_count > 0:
                    avg_daily_cost = total_estimated_cost / location_count
                    cost_analysis["average_daily_cost"] = round(avg_daily_cost, 2)
                    
                    # Calculate cost effectiveness score
                    if avg_daily_cost < 50:
                        cost_analysis["cost_effectiveness_score"] = 0.9  # Very cost-effective
                    elif avg_daily_cost < 100:
                        cost_analysis["cost_effectiveness_score"] = 0.7  # Cost-effective
                    elif avg_daily_cost < 200:
                        cost_analysis["cost_effectiveness_score"] = 0.5  # Moderate
                    else:
                        cost_analysis["cost_effectiveness_score"] = 0.3  # Expensive
                    
                    # Budget compatibility
                    if budget:
                        budget_per_day = budget.get("per_day", 0)
                        if budget_per_day > 0:
                            if avg_daily_cost <= budget_per_day * 0.8:
                                cost_analysis["budget_compatibility"] = "excellent"
                            elif avg_daily_cost <= budget_per_day:
                                cost_analysis["budget_compatibility"] = "good"
                            elif avg_daily_cost <= budget_per_day * 1.2:
                                cost_analysis["budget_compatibility"] = "moderate"
                            else:
                                cost_analysis["budget_compatibility"] = "poor"
                    
                    # Generate cost recommendations
                    if cost_analysis["cost_effectiveness_score"] >= 0.7:
                        cost_analysis["cost_recommendations"].append("Excellent value for money")
                    elif cost_analysis["cost_effectiveness_score"] >= 0.5:
                        cost_analysis["cost_recommendations"].append("Good value for money")
                    else:
                        cost_analysis["cost_recommendations"].append("Consider budget alternatives")
            
            return cost_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing cost effectiveness: {e}")
            return {
                "estimated_costs": {},
                "budget_compatibility": "unknown",
                "cost_effectiveness_score": 0.5,
                "cost_recommendations": []
            }
    
    def _generate_overall_recommendation(self, weather_analysis: Dict, tourist_analysis: Dict,
                                       safety_analysis: Dict, feedback_analysis: Dict,
                                       cost_analysis: Dict, traveler_profile: Dict) -> Dict:
        """Generate overall trip recommendation based on all factors."""
        try:
            # Calculate weighted overall score
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
            
            # Determine recommendation level
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
            
            # Generate key factors
            key_factors = []
            if weather_score >= 0.8:
                key_factors.append("Excellent weather conditions")
            elif weather_score <= 0.3:
                key_factors.append("Challenging weather conditions")
            
            if tourist_score >= 0.8:
                key_factors.append("Great tourist conditions")
            elif tourist_score <= 0.3:
                key_factors.append("Limited tourist amenities")
            
            if safety_score >= 0.8:
                key_factors.append("High safety rating")
            elif safety_score <= 0.3:
                key_factors.append("Safety concerns")
            
            if feedback_score >= 0.8:
                key_factors.append("Positive user feedback")
            elif feedback_score <= 0.3:
                key_factors.append("Limited user feedback")
            
            if cost_score >= 0.8:
                key_factors.append("Excellent value for money")
            elif cost_score <= 0.3:
                key_factors.append("High costs")
            
            # Generate warnings
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
            
            # Generate suggestions
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
            
            # Add specific suggestions based on analysis
            if weather_analysis.get("overall_weather_score", 0.5) < 0.4:
                suggestions.append("🌤️ Consider rescheduling for better weather")
            
            if safety_analysis.get("overall_safety_score", 0.5) < 0.4:
                suggestions.append("🛡️ Research safety measures and travel advisories")
            
            if cost_analysis.get("budget_compatibility") == "poor":
                suggestions.append("💰 Consider budget alternatives or saving more")
            
            return {
                "overall_score": round(overall_score, 2),
                "recommendation": recommendation,
                "confidence": round(confidence, 2),
                "key_factors": key_factors,
                "warnings": warnings,
                "suggestions": suggestions,
                "score_breakdown": {
                    "weather": round(weather_score, 2),
                    "tourist_factors": round(tourist_score, 2),
                    "safety": round(safety_score, 2),
                    "user_feedback": round(feedback_score, 2),
                    "cost_effectiveness": round(cost_score, 2)
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating overall recommendation: {e}")
            return {
                "overall_score": 0.5,
                "recommendation": "not_recommended",
                "confidence": 0.5,
                "key_factors": ["Analysis error"],
                "warnings": ["Unable to complete analysis"],
                "suggestions": ["Contact support for assistance"],
                "score_breakdown": {}
            }


# Global instance
trip_recommendation_engine = TripRecommendationEngine()
