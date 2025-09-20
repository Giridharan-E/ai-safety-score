"""
Feedback Aggregation Service

This service handles the collection, validation, and aggregation of user feedback
for safety score calculation. It ensures that feedback from 50+ different users
is properly collected and processed before being used in safety score calculations.
"""

import json
import logging
from typing import Dict, List, Optional, Tuple, Any
from django.db.models import Q, Count, Avg, StdDev
from django.utils import timezone
from datetime import timedelta
from collections import defaultdict
import statistics

from ..models import Feedback
from ..utils.json_store import get_json_store

logger = logging.getLogger(__name__)


class FeedbackAggregationService:
    """
    Service for aggregating user feedback and calculating location-specific safety scores.
    """
    
    def __init__(self):
        self.min_feedback_threshold = 50  # Minimum feedbacks required for location scoring
        self.max_feedback_age_days = 365  # Maximum age of feedback to consider (1 year)
        self.location_radius_meters = 100  # Radius to group nearby feedbacks
        self.outlier_threshold = 2.0  # Standard deviations for outlier detection
        
    def get_location_feedback_summary(self, latitude: float, longitude: float, 
                                    radius: float = None) -> Dict[str, Any]:
        """
        Get comprehensive feedback summary for a specific location.
        
        Args:
            latitude: Location latitude
            longitude: Location longitude  
            radius: Search radius in meters (defaults to self.location_radius_meters)
            
        Returns:
            Dictionary containing feedback statistics and analysis
        """
        if radius is None:
            radius = self.location_radius_meters
            
        try:
            # Get approved feedback within radius
            feedbacks = self._get_feedbacks_in_radius(latitude, longitude, radius)
            
            if not feedbacks:
                return self._empty_feedback_summary()
            
            # Calculate statistics
            ratings = [f.rating for f in feedbacks]
            unique_users = len(set(f.user_id for f in feedbacks if f.user_id))
            
            summary = {
                "location": {
                    "latitude": latitude,
                    "longitude": longitude,
                    "radius_meters": radius
                },
                "feedback_count": len(feedbacks),
                "unique_users": unique_users,
                "meets_threshold": len(feedbacks) >= self.min_feedback_threshold,
                "statistics": {
                    "average_rating": round(statistics.mean(ratings), 2),
                    "median_rating": statistics.median(ratings),
                    "rating_std_dev": round(statistics.stdev(ratings) if len(ratings) > 1 else 0, 2),
                    "min_rating": min(ratings),
                    "max_rating": max(ratings),
                    "rating_distribution": self._calculate_rating_distribution(ratings)
                },
                "quality_metrics": {
                    "outlier_count": self._count_outliers(ratings),
                    "recent_feedbacks": self._count_recent_feedbacks(feedbacks),
                    "trusted_user_ratio": self._calculate_trusted_user_ratio(feedbacks),
                    "data_freshness": self._calculate_data_freshness(feedbacks)
                },
                "safety_score": self._calculate_location_safety_score(feedbacks, ratings),
                "recommendations": self._generate_recommendations(feedbacks, ratings),
                "last_updated": timezone.now().isoformat()
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting location feedback summary: {e}")
            return self._empty_feedback_summary()
    
    def get_feedback_collection_progress(self, latitude: float, longitude: float,
                                       radius: float = None) -> Dict[str, Any]:
        """
        Get progress towards the 50-user feedback threshold for a location.
        
        Args:
            latitude: Location latitude
            longitude: Location longitude
            radius: Search radius in meters
            
        Returns:
            Dictionary containing collection progress information
        """
        if radius is None:
            radius = self.location_radius_meters
            
        try:
            feedbacks = self._get_feedbacks_in_radius(latitude, longitude, radius)
            unique_users = len(set(f.user_id for f in feedbacks if f.user_id))
            
            progress = {
                "location": {
                    "latitude": latitude,
                    "longitude": longitude,
                    "radius_meters": radius
                },
                "current_feedbacks": len(feedbacks),
                "unique_users": unique_users,
                "target_feedbacks": self.min_feedback_threshold,
                "progress_percentage": min(100, (len(feedbacks) / self.min_feedback_threshold) * 100),
                "remaining_needed": max(0, self.min_feedback_threshold - len(feedbacks)),
                "status": self._get_collection_status(len(feedbacks), unique_users),
                "recent_activity": self._get_recent_activity(feedbacks),
                "user_engagement": self._analyze_user_engagement(feedbacks),
                "last_updated": timezone.now().isoformat()
            }
            
            return progress
            
        except Exception as e:
            logger.error(f"Error getting feedback collection progress: {e}")
            return {
                "error": str(e),
                "current_feedbacks": 0,
                "unique_users": 0,
                "target_feedbacks": self.min_feedback_threshold,
                "progress_percentage": 0,
                "remaining_needed": self.min_feedback_threshold,
                "status": "error"
            }
    
    def get_top_locations_needing_feedback(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get locations that need more feedback to reach the 50-user threshold.
        
        Args:
            limit: Maximum number of locations to return
            
        Returns:
            List of locations with feedback collection status
        """
        try:
            # Get all approved feedback
            feedbacks = Feedback.objects.filter(
                approval_status__in=['approved', 'auto_approved']
            ).order_by('-created_at')
            
            # Group by location (using a simple grid-based approach)
            location_groups = defaultdict(list)
            
            for feedback in feedbacks:
                # Create location key based on rounded coordinates
                lat_key = round(feedback.latitude, 3)  # ~100m precision
                lon_key = round(feedback.longitude, 3)
                location_key = f"{lat_key}_{lon_key}"
                
                location_groups[location_key].append(feedback)
            
            # Analyze each location group
            locations_needing_feedback = []
            
            for location_key, group_feedbacks in location_groups.items():
                if len(group_feedbacks) < self.min_feedback_threshold:
                    # Calculate location center
                    avg_lat = sum(f.latitude for f in group_feedbacks) / len(group_feedbacks)
                    avg_lon = sum(f.longitude for f in group_feedbacks) / len(group_feedbacks)
                    
                    unique_users = len(set(f.user_id for f in group_feedbacks if f.user_id))
                    
                    locations_needing_feedback.append({
                        "location_key": location_key,
                        "latitude": avg_lat,
                        "longitude": avg_lon,
                        "current_feedbacks": len(group_feedbacks),
                        "unique_users": unique_users,
                        "remaining_needed": self.min_feedback_threshold - len(group_feedbacks),
                        "progress_percentage": (len(group_feedbacks) / self.min_feedback_threshold) * 100,
                        "recent_activity": self._get_recent_activity(group_feedbacks),
                        "sample_location_name": group_feedbacks[0].location_name if group_feedbacks else "Unknown"
                    })
            
            # Sort by remaining needed (ascending) and return top locations
            locations_needing_feedback.sort(key=lambda x: x['remaining_needed'])
            return locations_needing_feedback[:limit]
            
        except Exception as e:
            logger.error(f"Error getting top locations needing feedback: {e}")
            return []
    
    def get_feedback_analytics(self) -> Dict[str, Any]:
        """
        Get comprehensive analytics about the feedback collection system.
        
        Returns:
            Dictionary containing system-wide analytics
        """
        try:
            # Get all approved feedback
            all_feedbacks = Feedback.objects.filter(
                approval_status__in=['approved', 'auto_approved']
            )
            
            # Basic statistics
            total_feedbacks = all_feedbacks.count()
            unique_users = all_feedbacks.values('user_id').distinct().count()
            unique_locations = all_feedbacks.values('latitude', 'longitude').distinct().count()
            
            # Location analysis
            location_groups = defaultdict(list)
            for feedback in all_feedbacks:
                lat_key = round(feedback.latitude, 3)
                lon_key = round(feedback.longitude, 3)
                location_key = f"{lat_key}_{lon_key}"
                location_groups[location_key].append(feedback)
            
            locations_with_sufficient_feedback = sum(
                1 for group in location_groups.values() 
                if len(group) >= self.min_feedback_threshold
            )
            
            # Recent activity
            recent_feedbacks = all_feedbacks.filter(
                created_at__gte=timezone.now() - timedelta(days=7)
            ).count()
            
            # Rating distribution
            ratings = [f.rating for f in all_feedbacks]
            rating_distribution = self._calculate_rating_distribution(ratings)
            
            analytics = {
                "system_overview": {
                    "total_feedbacks": total_feedbacks,
                    "unique_users": unique_users,
                    "unique_locations": unique_locations,
                    "locations_with_sufficient_feedback": locations_with_sufficient_feedback,
                    "feedback_threshold": self.min_feedback_threshold
                },
                "recent_activity": {
                    "feedbacks_last_7_days": recent_feedbacks,
                    "average_daily_feedbacks": round(recent_feedbacks / 7, 1)
                },
                "rating_analysis": {
                    "average_rating": round(statistics.mean(ratings) if ratings else 0, 2),
                    "rating_distribution": rating_distribution,
                    "rating_std_dev": round(statistics.stdev(ratings) if len(ratings) > 1 else 0, 2)
                },
                "collection_progress": {
                    "locations_needing_feedback": len(location_groups) - locations_with_sufficient_feedback,
                    "completion_rate": round((locations_with_sufficient_feedback / len(location_groups)) * 100, 1) if location_groups else 0
                },
                "quality_metrics": {
                    "trusted_user_ratio": self._calculate_trusted_user_ratio(all_feedbacks),
                    "average_feedback_age_days": self._calculate_average_feedback_age(all_feedbacks)
                },
                "last_updated": timezone.now().isoformat()
            }
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error getting feedback analytics: {e}")
            return {"error": str(e)}
    
    def _get_feedbacks_in_radius(self, latitude: float, longitude: float, 
                                radius: float) -> List[Feedback]:
        """Get approved feedback within the specified radius."""
        # Convert radius from meters to approximate degrees
        # 1 degree latitude ≈ 111,000 meters
        lat_delta = radius / 111000.0
        lon_delta = radius / (111000.0 * abs(latitude / 90.0))  # Adjust for longitude
        
        return Feedback.objects.filter(
            approval_status__in=['approved', 'auto_approved'],
            latitude__range=(latitude - lat_delta, latitude + lat_delta),
            longitude__range=(longitude - lon_delta, longitude + lon_delta),
            created_at__gte=timezone.now() - timedelta(days=self.max_feedback_age_days)
        ).order_by('-created_at')
    
    def _empty_feedback_summary(self) -> Dict[str, Any]:
        """Return empty feedback summary for locations with no feedback."""
        return {
            "location": {"latitude": 0, "longitude": 0, "radius_meters": 0},
            "feedback_count": 0,
            "unique_users": 0,
            "meets_threshold": False,
            "statistics": {
                "average_rating": 0,
                "median_rating": 0,
                "rating_std_dev": 0,
                "min_rating": 0,
                "max_rating": 0,
                "rating_distribution": {}
            },
            "quality_metrics": {
                "outlier_count": 0,
                "recent_feedbacks": 0,
                "trusted_user_ratio": 0,
                "data_freshness": 0
            },
            "safety_score": 0.5,  # Neutral score
            "recommendations": [],
            "last_updated": timezone.now().isoformat()
        }
    
    def _calculate_rating_distribution(self, ratings: List[int]) -> Dict[str, int]:
        """Calculate distribution of ratings."""
        distribution = {}
        for rating in range(1, 11):
            distribution[str(rating)] = ratings.count(rating)
        return distribution
    
    def _count_outliers(self, ratings: List[int]) -> int:
        """Count outliers in ratings using standard deviation."""
        if len(ratings) < 3:
            return 0
        
        mean_rating = statistics.mean(ratings)
        std_dev = statistics.stdev(ratings)
        
        outliers = 0
        for rating in ratings:
            if abs(rating - mean_rating) > self.outlier_threshold * std_dev:
                outliers += 1
        
        return outliers
    
    def _count_recent_feedbacks(self, feedbacks: List[Feedback]) -> int:
        """Count feedbacks from the last 30 days."""
        thirty_days_ago = timezone.now() - timedelta(days=30)
        return sum(1 for f in feedbacks if f.created_at >= thirty_days_ago)
    
    def _calculate_trusted_user_ratio(self, feedbacks: List[Feedback]) -> float:
        """Calculate ratio of feedbacks from trusted users."""
        if not feedbacks:
            return 0.0
        
        trusted_count = sum(1 for f in feedbacks if f.is_trusted_user)
        return round(trusted_count / len(feedbacks), 2)
    
    def _calculate_data_freshness(self, feedbacks: List[Feedback]) -> float:
        """Calculate data freshness score (0-1, higher is fresher)."""
        if not feedbacks:
            return 0.0
        
        now = timezone.now()
        total_age_days = sum((now - f.created_at).days for f in feedbacks)
        avg_age_days = total_age_days / len(feedbacks)
        
        # Convert to freshness score (0-1, where 1 is very fresh)
        freshness = max(0, 1 - (avg_age_days / 365))  # 1 year = 0 freshness
        return round(freshness, 2)
    
    def _calculate_location_safety_score(self, feedbacks: List[Feedback], 
                                       ratings: List[int]) -> float:
        """Calculate safety score for a location based on feedback."""
        if not ratings:
            return 0.5  # Neutral score
        
        # Use weighted average considering recency and user trust
        weighted_sum = 0
        total_weight = 0
        
        for feedback in feedbacks:
            # Weight based on recency (newer = higher weight)
            days_old = (timezone.now() - feedback.created_at).days
            recency_weight = max(0.1, 1 - (days_old / 365))  # 1 year = 0.1 weight
            
            # Weight based on user trust
            trust_weight = 1.5 if feedback.is_trusted_user else 1.0
            
            # Combined weight
            weight = recency_weight * trust_weight
            
            weighted_sum += feedback.rating * weight
            total_weight += weight
        
        if total_weight == 0:
            return 0.5
        
        # Convert to 0-1 scale (ratings are 1-10)
        safety_score = (weighted_sum / total_weight) / 10.0
        return round(max(0, min(1, safety_score)), 3)
    
    def _generate_recommendations(self, feedbacks: List[Feedback], 
                                ratings: List[int]) -> List[str]:
        """Generate recommendations based on feedback analysis."""
        recommendations = []
        
        if not ratings:
            return ["No feedback available for this location"]
        
        avg_rating = statistics.mean(ratings)
        
        if avg_rating < 4:
            recommendations.append("Low safety rating - consider avoiding this area")
        elif avg_rating < 6:
            recommendations.append("Moderate safety rating - exercise caution")
        elif avg_rating >= 8:
            recommendations.append("High safety rating - generally safe area")
        
        # Check for recent negative feedback
        recent_negative = sum(1 for f in feedbacks 
                            if f.rating <= 3 and 
                            f.created_at >= timezone.now() - timedelta(days=30))
        
        if recent_negative > 0:
            recommendations.append(f"Recent negative feedback ({recent_negative} reports in last 30 days)")
        
        # Check data quality
        if len(feedbacks) < 10:
            recommendations.append("Limited feedback data - more user input needed")
        
        return recommendations
    
    def _get_collection_status(self, feedback_count: int, unique_users: int) -> str:
        """Get collection status based on feedback count and unique users."""
        if feedback_count >= self.min_feedback_threshold:
            return "complete"
        elif feedback_count >= self.min_feedback_threshold * 0.8:
            return "nearly_complete"
        elif feedback_count >= self.min_feedback_threshold * 0.5:
            return "in_progress"
        elif feedback_count > 0:
            return "started"
        else:
            return "not_started"
    
    def _get_recent_activity(self, feedbacks: List[Feedback]) -> Dict[str, int]:
        """Get recent activity statistics."""
        now = timezone.now()
        
        return {
            "last_24_hours": sum(1 for f in feedbacks if f.created_at >= now - timedelta(hours=24)),
            "last_7_days": sum(1 for f in feedbacks if f.created_at >= now - timedelta(days=7)),
            "last_30_days": sum(1 for f in feedbacks if f.created_at >= now - timedelta(days=30))
        }
    
    def _analyze_user_engagement(self, feedbacks: List[Feedback]) -> Dict[str, Any]:
        """Analyze user engagement patterns."""
        if not feedbacks:
            return {"average_feedbacks_per_user": 0, "most_active_user": None}
        
        user_feedback_counts = defaultdict(int)
        for feedback in feedbacks:
            if feedback.user_id:
                user_feedback_counts[feedback.user_id] += 1
        
        if not user_feedback_counts:
            return {"average_feedbacks_per_user": 0, "most_active_user": None}
        
        avg_feedbacks_per_user = sum(user_feedback_counts.values()) / len(user_feedback_counts)
        most_active_user = max(user_feedback_counts.items(), key=lambda x: x[1])
        
        return {
            "average_feedbacks_per_user": round(avg_feedbacks_per_user, 1),
            "most_active_user": {
                "user_id": most_active_user[0],
                "feedback_count": most_active_user[1]
            }
        }
    
    def _calculate_average_feedback_age(self, feedbacks) -> float:
        """Calculate average age of feedbacks in days."""
        if not feedbacks:
            return 0.0
        
        now = timezone.now()
        total_age_days = sum((now - f.created_at).days for f in feedbacks)
        return round(total_age_days / len(feedbacks), 1)


# Global instance
feedback_aggregation_service = FeedbackAggregationService()
