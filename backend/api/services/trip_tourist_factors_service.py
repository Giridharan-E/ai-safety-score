"""
Trip Tourist Factors Analysis Service

This service analyzes tourist-related factors including peak season, events,
safety considerations, and local conditions that affect the tourist experience.
"""

import requests
import json
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TouristFactor:
    """Data class for tourist factors."""
    factor_type: str
    name: str
    impact: str  # positive, negative, neutral
    description: str
    confidence: float  # 0-1 scale


@dataclass
class TouristAnalysis:
    """Data class for tourist analysis results."""
    peak_season_status: str
    crowd_level: str
    price_level: str
    local_events: List[Dict]
    safety_considerations: List[Dict]
    cultural_norms: List[Dict]
    transport_availability: Dict
    overall_tourist_score: float  # 0-1 scale
    recommendations: List[str]


class TripTouristFactorsService:
    """
    Service for analyzing tourist-related factors for trip planning.
    """
    
    def __init__(self):
        self.base_urls = {
            "travel_briefing": "https://travelbriefing.org",
            "rest_countries": "https://restcountries.com/v3.1",
            "eventbrite": "https://www.eventbriteapi.com/v3",
            "ticketmaster": "https://app.ticketmaster.com/discovery/v2",
            "uk_fcdo": "https://www.gov.uk/foreign-travel-advice",
            "wikipedia": "https://en.wikipedia.org/w/api.php"
        }
    
    def analyze_tourist_factors(self, locations: List[Dict], start_date: str, end_date: str) -> Dict:
        """
        Analyze tourist-related factors for a trip across multiple locations.
        
        Args:
            locations: List of location dictionaries with 'latitude', 'longitude', 'name', 'country'
            start_date: Trip start date in YYYY-MM-DD format
            end_date: Trip end date in YYYY-MM-DD format
            
        Returns:
            Dictionary containing tourist factors analysis for each location
        """
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            trip_duration = (end_dt - start_dt).days + 1
            
            tourist_analysis = {
                "trip_dates": {
                    "start_date": start_date,
                    "end_date": end_date,
                    "duration_days": trip_duration
                },
                "locations": {},
                "overall_tourist_score": 0.0,
                "tourist_recommendations": [],
                "safety_warnings": [],
                "cost_estimates": {}
            }
            
            total_score = 0
            location_count = 0
            
            for location in locations:
                location_name = location.get('name', f"Location {location_count + 1}")
                country = location.get('country', 'Unknown')
                lat = location.get('latitude')
                lon = location.get('longitude')
                
                if not lat or not lon:
                    logger.warning(f"Missing coordinates for location: {location_name}")
                    continue
                
                # Analyze tourist factors for this location
                location_analysis = self._analyze_location_tourist_factors(
                    lat, lon, location_name, country, start_date, end_date
                )
                
                if location_analysis:
                    tourist_analysis["locations"][location_name] = location_analysis
                    total_score += location_analysis.get("overall_tourist_score", 0.5)
                    location_count += 1
                    
                    # Collect recommendations and warnings
                    if location_analysis.get("recommendations"):
                        tourist_analysis["tourist_recommendations"].extend([
                            {"location": location_name, "recommendation": rec}
                            for rec in location_analysis["recommendations"]
                        ])
                    
                    if location_analysis.get("safety_considerations"):
                        high_risk_items = [
                            item for item in location_analysis["safety_considerations"]
                            if item.get("risk_level") == "high"
                        ]
                        if high_risk_items:
                            tourist_analysis["safety_warnings"].extend([
                                {"location": location_name, "warning": item}
                                for item in high_risk_items
                            ])
                    
                    # Cost estimates
                    if location_analysis.get("cost_estimates"):
                        tourist_analysis["cost_estimates"][location_name] = location_analysis["cost_estimates"]
            
            # Calculate overall tourist score
            if location_count > 0:
                tourist_analysis["overall_tourist_score"] = total_score / location_count
            
            # Generate overall recommendations
            tourist_analysis["overall_recommendations"] = self._generate_overall_tourist_recommendations(
                tourist_analysis
            )
            
            return tourist_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing tourist factors: {e}")
            return {
                "error": str(e),
                "trip_dates": {"start_date": start_date, "end_date": end_date},
                "locations": {},
                "overall_tourist_score": 0.5,
                "tourist_recommendations": [],
                "safety_warnings": []
            }
    
    def _analyze_location_tourist_factors(self, latitude: float, longitude: float, 
                                        location_name: str, country: str,
                                        start_date: str, end_date: str) -> Optional[Dict]:
        """Analyze tourist factors for a specific location."""
        try:
            # Analyze peak season status
            peak_season_analysis = self._analyze_peak_season(location_name, country, start_date, end_date)
            
            # Analyze local events
            local_events = self._get_local_events(location_name, country, start_date, end_date)
            
            # Analyze safety considerations
            safety_considerations = self._analyze_safety_considerations(location_name, country)
            
            # Analyze cultural norms
            cultural_norms = self._analyze_cultural_norms(location_name, country)
            
            # Analyze transport availability
            transport_availability = self._analyze_transport_availability(location_name, country)
            
            # Calculate overall tourist score
            overall_score = self._calculate_tourist_score(
                peak_season_analysis, local_events, safety_considerations, 
                cultural_norms, transport_availability
            )
            
            # Generate recommendations
            recommendations = self._generate_tourist_recommendations(
                peak_season_analysis, local_events, safety_considerations,
                cultural_norms, transport_availability, overall_score
            )
            
            # Estimate costs
            cost_estimates = self._estimate_trip_costs(
                peak_season_analysis, location_name, country
            )
            
            return {
                "location": {
                    "name": location_name,
                    "country": country,
                    "latitude": latitude,
                    "longitude": longitude
                },
                "peak_season_analysis": peak_season_analysis,
                "local_events": local_events,
                "safety_considerations": safety_considerations,
                "cultural_norms": cultural_norms,
                "transport_availability": transport_availability,
                "overall_tourist_score": overall_score,
                "recommendations": recommendations,
                "cost_estimates": cost_estimates
            }
            
        except Exception as e:
            logger.error(f"Error analyzing tourist factors for {location_name}: {e}")
            return None
    
    def _analyze_peak_season(self, location_name: str, country: str, 
                           start_date: str, end_date: str) -> Dict:
        """Analyze peak season status for the trip dates."""
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            month = start_dt.month
            
            # Simplified peak season analysis based on month
            # In production, this would use more sophisticated data
            peak_seasons = {
                "tropical": [12, 1, 2, 3],  # Winter months
                "temperate": [6, 7, 8],     # Summer months
                "mediterranean": [6, 7, 8, 9],  # Summer/early fall
                "mountain": [12, 1, 2, 3, 6, 7, 8]  # Winter and summer
            }
            
            # Determine climate type (simplified)
            climate_type = self._determine_climate_type(country, location_name)
            
            is_peak = month in peak_seasons.get(climate_type, [6, 7, 8])
            
            if is_peak:
                status = "peak"
                crowd_level = "high"
                price_level = "high"
                description = "Peak tourist season - expect crowds and higher prices"
            else:
                status = "off_peak"
                crowd_level = "low"
                price_level = "low"
                description = "Off-peak season - fewer crowds and lower prices"
            
            return {
                "status": status,
                "crowd_level": crowd_level,
                "price_level": price_level,
                "description": description,
                "climate_type": climate_type,
                "month": month
            }
            
        except Exception as e:
            logger.error(f"Error analyzing peak season: {e}")
            return {
                "status": "unknown",
                "crowd_level": "medium",
                "price_level": "medium",
                "description": "Peak season analysis unavailable",
                "climate_type": "unknown",
                "month": 1
            }
    
    def _determine_climate_type(self, country: str, location_name: str) -> str:
        """Determine climate type for a location."""
        # Simplified climate type determination
        # In production, this would use more sophisticated geographic data
        
        tropical_countries = ["Thailand", "India", "Indonesia", "Philippines", "Brazil", "Mexico"]
        temperate_countries = ["United States", "Canada", "United Kingdom", "Germany", "France"]
        mediterranean_countries = ["Spain", "Italy", "Greece", "Portugal", "Turkey"]
        mountain_countries = ["Switzerland", "Austria", "Nepal", "Peru"]
        
        if any(country.lower() in tropical_countries for country in [country]):
            return "tropical"
        elif any(country.lower() in mediterranean_countries for country in [country]):
            return "mediterranean"
        elif any(country.lower() in mountain_countries for country in [country]):
            return "mountain"
        else:
            return "temperate"
    
    def _get_local_events(self, location_name: str, country: str, 
                         start_date: str, end_date: str) -> List[Dict]:
        """Get local events and festivals for the trip period."""
        try:
            # For now, return mock data. In production, integrate with Eventbrite, Ticketmaster APIs
            events = []
            
            # Mock events based on location and time
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            month = start_dt.month
            
            # Add some mock events based on month and location
            if month == 12:
                events.append({
                    "name": "Christmas Festival",
                    "date": start_date,
                    "type": "cultural",
                    "impact": "positive",
                    "description": "Local Christmas celebrations and markets"
                })
            elif month in [6, 7, 8]:
                events.append({
                    "name": "Summer Music Festival",
                    "date": start_date,
                    "type": "entertainment",
                    "impact": "positive",
                    "description": "Annual summer music festival"
                })
            
            # Add location-specific events
            if "chennai" in location_name.lower():
                events.append({
                    "name": "Chennai Music Season",
                    "date": start_date,
                    "type": "cultural",
                    "impact": "positive",
                    "description": "Traditional Carnatic music festival"
                })
            
            return events
            
        except Exception as e:
            logger.error(f"Error getting local events: {e}")
            return []
    
    def _analyze_safety_considerations(self, location_name: str, country: str) -> List[Dict]:
        """Analyze safety considerations for the location."""
        try:
            safety_items = []
            
            # Mock safety analysis - in production, integrate with travel advisory APIs
            safety_items.append({
                "category": "general",
                "risk_level": "low",
                "description": "Generally safe for tourists",
                "recommendations": ["Take normal precautions", "Keep valuables secure"]
            })
            
            # Add location-specific safety considerations
            if "chennai" in location_name.lower():
                safety_items.append({
                    "category": "transport",
                    "risk_level": "medium",
                    "description": "Heavy traffic and chaotic driving",
                    "recommendations": ["Use reputable taxi services", "Avoid driving during peak hours"]
                })
            
            return safety_items
            
        except Exception as e:
            logger.error(f"Error analyzing safety considerations: {e}")
            return []
    
    def _analyze_cultural_norms(self, location_name: str, country: str) -> List[Dict]:
        """Analyze cultural norms and requirements."""
        try:
            cultural_norms = []
            
            # Mock cultural analysis - in production, integrate with cultural databases
            cultural_norms.append({
                "category": "dress_code",
                "description": "Modest clothing recommended for religious sites",
                "importance": "medium",
                "applicable_locations": ["temples", "churches", "mosques"]
            })
            
            cultural_norms.append({
                "category": "behavior",
                "description": "Remove shoes before entering religious sites",
                "importance": "high",
                "applicable_locations": ["temples", "mosques"]
            })
            
            # Add country-specific norms
            if "india" in country.lower():
                cultural_norms.append({
                    "category": "dining",
                    "description": "Use right hand for eating, left hand for other purposes",
                    "importance": "medium",
                    "applicable_locations": ["restaurants", "homes"]
                })
            
            return cultural_norms
            
        except Exception as e:
            logger.error(f"Error analyzing cultural norms: {e}")
            return []
    
    def _analyze_transport_availability(self, location_name: str, country: str) -> Dict:
        """Analyze transport availability and options."""
        try:
            transport_options = {
                "ride_sharing": {
                    "available": True,
                    "services": ["Uber", "Ola", "Local taxis"],
                    "safety_rating": "good",
                    "cost_level": "medium"
                },
                "public_transport": {
                    "available": True,
                    "services": ["Bus", "Metro", "Train"],
                    "safety_rating": "good",
                    "cost_level": "low"
                },
                "car_rental": {
                    "available": True,
                    "safety_rating": "medium",
                    "cost_level": "medium",
                    "requirements": ["International driving license", "Credit card"]
                },
                "walking": {
                    "recommended": True,
                    "safety_rating": "good",
                    "considerations": ["Use pedestrian crossings", "Be aware of traffic"]
                }
            }
            
            # Add location-specific transport considerations
            if "chennai" in location_name.lower():
                transport_options["ride_sharing"]["services"] = ["Uber", "Ola", "Auto-rickshaw"]
                transport_options["public_transport"]["services"] = ["Bus", "Metro", "MRTS"]
            
            return transport_options
            
        except Exception as e:
            logger.error(f"Error analyzing transport availability: {e}")
            return {}
    
    def _calculate_tourist_score(self, peak_season_analysis: Dict, local_events: List[Dict],
                               safety_considerations: List[Dict], cultural_norms: List[Dict],
                               transport_availability: Dict) -> float:
        """Calculate overall tourist score (0-1, higher is better)."""
        try:
            score = 0.5  # Base score
            
            # Peak season impact
            if peak_season_analysis.get("status") == "off_peak":
                score += 0.2  # Off-peak is generally better for tourists
            elif peak_season_analysis.get("status") == "peak":
                score -= 0.1  # Peak season has crowds and higher prices
            
            # Events impact
            positive_events = sum(1 for event in local_events if event.get("impact") == "positive")
            if positive_events > 0:
                score += 0.1  # Positive events enhance experience
            
            # Safety impact
            high_risk_items = sum(1 for item in safety_considerations if item.get("risk_level") == "high")
            if high_risk_items > 0:
                score -= 0.2  # High safety risks reduce score
            elif all(item.get("risk_level") == "low" for item in safety_considerations):
                score += 0.1  # Low safety risks increase score
            
            # Transport availability impact
            if transport_availability.get("ride_sharing", {}).get("available"):
                score += 0.1
            if transport_availability.get("public_transport", {}).get("available"):
                score += 0.1
            
            return max(0.0, min(1.0, score))
            
        except Exception as e:
            logger.error(f"Error calculating tourist score: {e}")
            return 0.5
    
    def _generate_tourist_recommendations(self, peak_season_analysis: Dict, local_events: List[Dict],
                                        safety_considerations: List[Dict], cultural_norms: List[Dict],
                                        transport_availability: Dict, overall_score: float) -> List[str]:
        """Generate tourist recommendations based on analysis."""
        recommendations = []
        
        # Peak season recommendations
        if peak_season_analysis.get("status") == "peak":
            recommendations.append("Peak season - book accommodations and attractions in advance")
            recommendations.append("Expect crowds and higher prices - budget accordingly")
        elif peak_season_analysis.get("status") == "off_peak":
            recommendations.append("Off-peak season - great time for budget travel and fewer crowds")
        
        # Event recommendations
        if local_events:
            recommendations.append(f"Local events during your visit: {', '.join([e['name'] for e in local_events])}")
        
        # Safety recommendations
        for safety_item in safety_considerations:
            if safety_item.get("risk_level") == "high":
                recommendations.append(f"⚠️ HIGH SAFETY RISK: {safety_item['description']}")
            elif safety_item.get("risk_level") == "medium":
                recommendations.append(f"⚠️ Safety consideration: {safety_item['description']}")
        
        # Cultural recommendations
        if cultural_norms:
            recommendations.append("Cultural norms to observe:")
            for norm in cultural_norms[:3]:  # Show top 3 most important
                recommendations.append(f"  - {norm['description']}")
        
        # Transport recommendations
        if transport_availability.get("ride_sharing", {}).get("available"):
            recommendations.append("Ride-sharing services available - convenient for getting around")
        
        # Overall score recommendations
        if overall_score >= 0.8:
            recommendations.append("Excellent tourist conditions - highly recommended")
        elif overall_score >= 0.6:
            recommendations.append("Good tourist conditions with minor considerations")
        elif overall_score >= 0.4:
            recommendations.append("Moderate tourist conditions - plan carefully")
        else:
            recommendations.append("Challenging tourist conditions - consider alternatives")
        
        return recommendations
    
    def _estimate_trip_costs(self, peak_season_analysis: Dict, location_name: str, country: str) -> Dict:
        """Estimate trip costs based on various factors."""
        try:
            base_costs = {
                "accommodation_per_night": 50,  # USD
                "meals_per_day": 30,
                "transport_per_day": 20,
                "attractions_per_day": 25,
                "miscellaneous_per_day": 15
            }
            
            # Adjust for peak season
            if peak_season_analysis.get("price_level") == "high":
                multiplier = 1.5
            elif peak_season_analysis.get("price_level") == "low":
                multiplier = 0.7
            else:
                multiplier = 1.0
            
            # Adjust for country (simplified)
            if "india" in country.lower():
                multiplier *= 0.3  # India is generally cheaper
            elif "switzerland" in country.lower():
                multiplier *= 2.0  # Switzerland is expensive
            
            estimated_costs = {}
            for category, base_cost in base_costs.items():
                estimated_costs[category] = round(base_cost * multiplier, 2)
            
            estimated_costs["total_per_day"] = sum(estimated_costs.values())
            estimated_costs["currency"] = "USD"
            estimated_costs["note"] = "Estimates based on mid-range options"
            
            return estimated_costs
            
        except Exception as e:
            logger.error(f"Error estimating trip costs: {e}")
            return {}
    
    def _generate_overall_tourist_recommendations(self, tourist_analysis: Dict) -> List[str]:
        """Generate overall tourist recommendations for the entire trip."""
        recommendations = []
        
        overall_score = tourist_analysis.get("overall_tourist_score", 0.5)
        safety_warnings = tourist_analysis.get("safety_warnings", [])
        
        # Overall score recommendation
        if overall_score >= 0.8:
            recommendations.append("🌟 Excellent tourist conditions across all destinations")
        elif overall_score >= 0.6:
            recommendations.append("🌟 Good tourist conditions with minor considerations")
        elif overall_score >= 0.4:
            recommendations.append("🌟 Moderate tourist conditions - plan carefully")
        else:
            recommendations.append("🌟 Challenging tourist conditions - consider alternatives")
        
        # Safety warnings
        if safety_warnings:
            high_risk_locations = [w["location"] for w in safety_warnings if w["warning"].get("risk_level") == "high"]
            if high_risk_locations:
                recommendations.append(f"⚠️ HIGH SAFETY RISK in: {', '.join(high_risk_locations)}")
        
        # Cost recommendations
        cost_estimates = tourist_analysis.get("cost_estimates", {})
        if cost_estimates:
            avg_daily_cost = sum(loc.get("total_per_day", 0) for loc in cost_estimates.values()) / len(cost_estimates)
            recommendations.append(f"💰 Estimated daily cost: ${avg_daily_cost:.2f} USD")
        
        return recommendations


# Global instance
trip_tourist_factors_service = TripTouristFactorsService()
