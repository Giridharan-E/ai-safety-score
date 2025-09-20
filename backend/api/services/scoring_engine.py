from typing import Dict, Tuple, List
from django.db.models import Avg
from ..models import Feedback

class ScoringEngine:
    """
    Core scoring engine for calculating the final safety score.
    This class can be expanded with more sophisticated scoring algorithms.
    """

    def __init__(self):
        # Default weights for each factor. These can be tuned based on data analysis.
        self.weights = {
            "transport": 0.10,
            "transport_density": 0.05,
            "lighting": 0.15,
            "visibility": 0.10,
            "natural_surveillance": 0.10,
            "sidewalks": 0.05,
            "businesses": 0.05,
            "police_stations": 0.15,
            "hospitals": 0.10,
            "crime_rate": 0.15,
            "user_feedback": 0.20,  # Increased weight for user feedback when available
        }
        # Factors that can be adjusted based on the user profile or time of day
        self.adjustments = {
            "gender_usage": {"male": 1.0, "female": 1.2, "other": 1.1},
            "time_of_day": {"day": 1.0, "night": 0.8},
            "weather": {"clear": 1.0, "rain": 0.9, "storm": 0.7},
        }

    def score(self, features: Dict, profile: Dict, weather_mul: float = 1.0, incident_mul: float = 1.0) -> Tuple[float, float]:
        """
        Calculates a comprehensive safety score based on a dictionary of features.
        
        Args:
            features (Dict): A dictionary of normalized safety features (0-1).
            profile (Dict): A dictionary of user profile information (e.g., gender, age).
            weather_mul (float): A multiplier for weather impact (0-1).
            incident_mul (float): A multiplier for recent incident impact (0-1).
            
        Returns:
            Tuple[float, float]: A tuple containing the final safety score (1-10) and an adjustment index.
        """
        total_score = 0
        total_weight = 0
        adjustment_index = 1.0

        for factor, weight in self.weights.items():
            if factor in features:
                # Ensure feature value is within a reasonable range (e.g., 0-1)
                value = max(0.0, min(1.0, features[factor]))
                
                # Apply multipliers
                final_value = value
                if factor in ["lighting", "visibility"]:
                    final_value *= weather_mul
                if factor == "crime_rate":
                    final_value *= incident_mul
                
                total_score += final_value * weight
                total_weight += weight
        
        # Normalize the score to be out of 10
        final_score = (total_score / total_weight) * 10 if total_weight > 0 else 5.0
        
        # Apply profile-based adjustments (if any)
        # For example, if a user has a 'female' profile, certain factors might be weighted differently
        # We can implement this in a more detailed version of the engine.
        
        final_score = max(1.0, min(10.0, final_score))

        return (final_score, adjustment_index)

    def update_weights_from_feedback(self, latitude: float, longitude: float, radius_m: float = 1000.0) -> None:
        """
        Adjust weights based on approved feedback trends, prioritizing tourist places in Tamil Nadu.
        Only uses approved and auto-approved feedback to prevent manipulation.
        Simple heuristic: if avg rating in region/type is low (<5), increase weight on police/lighting; if high (>8), boost businesses/parks.
        """
        try:
            # Only use approved feedback
            qs = Feedback.objects.filter(
                approval_status__in=['approved', 'auto_approved']
            )
            tn_tourism = qs.filter(region__iexact="tamil nadu", place_type__icontains="tourist")
            avg_tn = tn_tourism.aggregate(avg=Avg("rating")).get("avg")
        except Exception:
            avg_tn = None

        if avg_tn is not None:
            if avg_tn < 5:
                self.weights["police_stations"] = min(0.25, self.weights["police_stations"] + 0.03)
                self.weights["lighting"] = min(0.25, self.weights["lighting"] + 0.02)
                self.weights["visibility"] = min(0.20, self.weights["visibility"] + 0.02)
            elif avg_tn > 8:
                self.weights["businesses"] = min(0.15, self.weights["businesses"] + 0.02)
                self.weights["transport"] = min(0.20, self.weights["transport"] + 0.02)

        # Normalize weights to sum to 1
        total = sum(self.weights.values())
        if total > 0:
            for k in list(self.weights.keys()):
                self.weights[k] = self.weights[k] / total

    def score_with_location_feedback(self, features: Dict, profile: Dict, 
                                   latitude: float, longitude: float,
                                   weather_mul: float = 1.0, incident_mul: float = 1.0) -> Tuple[float, float, Dict]:
        """
        Calculate safety score with location-specific user feedback integration.
        
        Args:
            features: Dictionary of normalized safety features (0-1)
            profile: User profile information
            latitude: Location latitude
            longitude: Location longitude
            weather_mul: Weather impact multiplier
            incident_mul: Incident impact multiplier
            
        Returns:
            Tuple of (final_score, adjustment_index, feedback_info)
        """
        from .feedback_aggregation_service import feedback_aggregation_service
        
        # Get location-specific feedback summary
        feedback_summary = feedback_aggregation_service.get_location_feedback_summary(
            latitude, longitude
        )
        
        feedback_info = {
            "has_sufficient_feedback": feedback_summary["meets_threshold"],
            "feedback_count": feedback_summary["feedback_count"],
            "unique_users": feedback_summary["unique_users"],
            "average_rating": feedback_summary["statistics"]["average_rating"],
            "safety_score_from_feedback": feedback_summary["safety_score"]
        }
        
        # Calculate base AI score
        base_score, adjustment_index = self.score(features, profile, weather_mul, incident_mul)
        
        # If we have sufficient feedback (50+ users), blend AI score with user feedback
        if feedback_summary["meets_threshold"]:
            user_feedback_score = feedback_summary["safety_score"]
            
            # Weighted combination: 60% AI score, 40% user feedback
            # This gives more weight to AI analysis while incorporating user experience
            final_score = (base_score * 0.6) + (user_feedback_score * 10 * 0.4)  # Convert feedback score to 1-10 scale
            
            feedback_info["scoring_method"] = "blended_ai_user_feedback"
            feedback_info["ai_score_weight"] = 0.6
            feedback_info["user_feedback_weight"] = 0.4
        else:
            # Use AI score only when insufficient feedback
            final_score = base_score
            feedback_info["scoring_method"] = "ai_only_insufficient_feedback"
            feedback_info["ai_score_weight"] = 1.0
            feedback_info["user_feedback_weight"] = 0.0
        
        # Ensure score is within bounds
        final_score = max(1.0, min(10.0, final_score))
        
        return final_score, adjustment_index, feedback_info


# Global instance
scoring_engine = ScoringEngine()
