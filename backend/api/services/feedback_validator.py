"""
Feedback Validation and Authorization Service

This service provides comprehensive validation and authorization for user feedback
before it affects safety score calculations. It includes multiple validation layers
and approval workflows.
"""

import re
import time
from typing import Dict, List, Optional, Tuple
from django.db.models import Q, Count, Avg
from django.utils import timezone
from datetime import timedelta
import logging

from ..models import Feedback

logger = logging.getLogger(__name__)


class FeedbackValidator:
    """
    Comprehensive feedback validation and authorization service.
    """
    
    def __init__(self):
        # Validation thresholds
        self.max_feedback_per_user_per_day = 10
        self.max_feedback_per_location_per_hour = 5
        self.min_rating = 1
        self.max_rating = 10
        
        # Auto-approval rules (more lenient)
        self.auto_approve_rating_range = (2, 9)  # Ratings 2-9 auto-approved (expanded range)
        self.trusted_user_threshold = 3  # Users with 3+ approved feedbacks (lowered threshold)
        self.auto_approve_trusted_users = True
        
        # Suspicious patterns for content validation (more specific and less aggressive)
        self.suspicious_patterns = [
            r'\b(this\s+is\s+spam|fake\s+review|dummy\s+data)\b',  # More specific spam patterns
            r'\b(very\s+){4,}',  # Increased threshold for repetition
            r'[!]{8,}',  # Increased threshold for exclamation marks
            r'[?]{8,}',  # Increased threshold for question marks
            r'\b(click\s+here|buy\s+now|free\s+money)\b',  # Common spam phrases
        ]

    def validate_feedback(self, feedback_data: Dict) -> Tuple[bool, List[str], str]:
        """
        Comprehensive feedback validation.
        
        Args:
            feedback_data: Dictionary containing feedback information
            
        Returns:
            Tuple of (is_valid, validation_errors, approval_status)
            approval_status: 'auto_approved', 'pending', 'rejected'
        """
        validation_errors = []
        approval_status = 'pending'
        
        # Run all validation checks
        if not self._validate_basic_fields(feedback_data, validation_errors):
            return False, validation_errors, 'rejected'
        
        if not self._validate_coordinates(feedback_data, validation_errors):
            return False, validation_errors, 'rejected'
        
        if not self._validate_rating(feedback_data, validation_errors):
            return False, validation_errors, 'rejected'
        
        if not self._validate_content(feedback_data, validation_errors):
            return False, validation_errors, 'rejected'
        
        if not self._validate_rate_limits(feedback_data, validation_errors):
            return False, validation_errors, 'rejected'
        
        # Determine approval status
        approval_status = self._determine_approval_status(feedback_data, validation_errors)
        
        is_valid = len(validation_errors) == 0 or approval_status != 'rejected'
        return is_valid, validation_errors, approval_status

    def _validate_basic_fields(self, data: Dict, errors: List[str]) -> bool:
        """Validate basic required fields."""
        required_fields = ['latitude', 'longitude', 'rating']
        missing_fields = [field for field in required_fields if field not in data or data[field] is None]
        
        if missing_fields:
            errors.append(f"Missing required fields: {', '.join(missing_fields)}")
            return False
        return True

    def _validate_coordinates(self, data: Dict, errors: List[str]) -> bool:
        """Validate coordinate values."""
        try:
            lat = float(data['latitude'])
            lon = float(data['longitude'])
            
            if not (-90.0 <= lat <= 90.0):
                errors.append("Latitude must be between -90 and 90 degrees")
                return False
            
            if not (-180.0 <= lon <= 180.0):
                errors.append("Longitude must be between -180 and 180 degrees")
                return False
                
        except (ValueError, TypeError):
            errors.append("Invalid coordinate format")
            return False
        
        return True

    def _validate_rating(self, data: Dict, errors: List[str]) -> bool:
        """Validate rating value."""
        try:
            rating = int(data['rating'])
            if not (self.min_rating <= rating <= self.max_rating):
                errors.append(f"Rating must be between {self.min_rating} and {self.max_rating}")
                return False
        except (ValueError, TypeError):
            errors.append("Invalid rating format")
            return False
        
        return True

    def _validate_content(self, data: Dict, errors: List[str]) -> bool:
        """Validate comment content for suspicious patterns."""
        comment = data.get('comment', '').lower()
        
        if not comment:
            return True  # Empty comments are fine
        
        # Check for suspicious patterns
        for pattern in self.suspicious_patterns:
            if re.search(pattern, comment, re.IGNORECASE):
                errors.append("Comment contains suspicious content")
                return False
        
        # Check for excessive length
        if len(comment) > 1000:
            errors.append("Comment is too long (max 1000 characters)")
            return False
        
        return True

    def _validate_rate_limits(self, data: Dict, errors: List[str]) -> bool:
        """Validate rate limiting rules."""
        user_id = data.get('user_id', '')
        lat = float(data['latitude'])
        lon = float(data['longitude'])
        
        # Check user daily limit
        if user_id:
            today = timezone.now().date()
            user_feedback_count = Feedback.objects.filter(
                user_id=user_id,
                created_at__date=today
            ).count()
            
            if user_feedback_count >= self.max_feedback_per_user_per_day:
                errors.append(f"Daily feedback limit exceeded ({self.max_feedback_per_user_per_day})")
                return False
        
        # Check location hourly limit
        one_hour_ago = timezone.now() - timedelta(hours=1)
        location_feedback_count = Feedback.objects.filter(
            latitude__range=(lat - 0.001, lat + 0.001),
            longitude__range=(lon - 0.001, lon + 0.001),
            created_at__gte=one_hour_ago
        ).count()
        
        if location_feedback_count >= self.max_feedback_per_location_per_hour:
            errors.append(f"Location feedback limit exceeded ({self.max_feedback_per_location_per_hour} per hour)")
            return False
        
        return True

    def _determine_approval_status(self, data: Dict, errors: List[str]) -> str:
        """Determine approval status based on validation results."""
        rating = int(data['rating'])
        user_id = data.get('user_id', '')
        
        # Check for suspicious content first (most restrictive)
        if any('suspicious' in error.lower() for error in errors):
            return 'pending'
        
        # Check if user is trusted (trusted users get more lenient treatment)
        if user_id and self._is_trusted_user(user_id):
            if self.auto_approve_trusted_users:
                return 'auto_approved'
        
        # Check if rating is in auto-approve range (expanded range)
        if 2 <= rating <= 9:
            return 'auto_approved'
        
        # Only extreme ratings (1 and 10) need manual review
        if rating in [1, 10]:
            return 'pending'
        
        # Check for new user (but be more lenient)
        if user_id and self._is_new_user(user_id):
            # New users with moderate ratings can be auto-approved
            if 3 <= rating <= 8:
                return 'auto_approved'
            return 'pending'
        
        # Default to auto-approved for safety (more lenient)
        return 'auto_approved'

    def _is_trusted_user(self, user_id: str) -> bool:
        """Check if user is trusted based on feedback history."""
        if not user_id:
            return False
            
        approved_count = Feedback.objects.filter(
            user_id=user_id,
            approval_status__in=['approved', 'auto_approved']
        ).count()
        
        return approved_count >= self.trusted_user_threshold

    def _is_new_user(self, user_id: str) -> bool:
        """Check if user is new (less than 3 feedbacks)."""
        if not user_id:
            return True
        
        feedback_count = Feedback.objects.filter(user_id=user_id).count()
        return feedback_count < 3

    def get_pending_feedback(self, limit: int = 50) -> List[Dict]:
        """Get feedback pending manual review."""
        pending_feedback = []
        
        # Get recent feedback with extreme ratings
        extreme_ratings = Feedback.objects.filter(
            rating__in=[1, 2, 9, 10],
            approval_status='pending',
            created_at__gte=timezone.now() - timedelta(days=7)
        ).order_by('-created_at')[:limit]
        
        for feedback in extreme_ratings:
            pending_feedback.append({
                'id': feedback.id,
                'user_id': feedback.user_id,
                'location_name': feedback.location_name,
                'rating': feedback.rating,
                'comment': feedback.comment,
                'created_at': feedback.created_at,
                'review_reason': 'extreme_rating'
            })
        
        return pending_feedback

    def approve_feedback(self, feedback_id: int, admin_user: str) -> bool:
        """Approve a feedback for inclusion in scoring."""
        try:
            feedback = Feedback.objects.get(id=feedback_id)
            feedback.approval_status = 'approved'
            feedback.approved_by = admin_user
            feedback.approved_at = timezone.now()
            feedback.save()
            
            logger.info(f"Feedback {feedback_id} approved by {admin_user}")
            return True
        except Feedback.DoesNotExist:
            logger.error(f"Feedback {feedback_id} not found for approval")
            return False

    def reject_feedback(self, feedback_id: int, admin_user: str, reason: str) -> bool:
        """Reject a feedback and exclude it from scoring."""
        try:
            feedback = Feedback.objects.get(id=feedback_id)
            feedback.approval_status = 'rejected'
            feedback.rejected_by = admin_user
            feedback.rejected_at = timezone.now()
            feedback.rejection_reason = reason
            feedback.save()
            
            logger.info(f"Feedback {feedback_id} rejected by {admin_user}: {reason}")
            return True
        except Feedback.DoesNotExist:
            logger.error(f"Feedback {feedback_id} not found for rejection")
            return False

    def get_feedback_statistics(self) -> Dict:
        """Get feedback validation statistics."""
        total_feedback = Feedback.objects.count()
        
        # Get counts by approval status
        approved_feedback = Feedback.objects.filter(approval_status__in=['approved', 'auto_approved']).count()
        pending_feedback = Feedback.objects.filter(approval_status='pending').count()
        rejected_feedback = Feedback.objects.filter(approval_status='rejected').count()
        
        return {
            'total_feedback': total_feedback,
            'approved_feedback': approved_feedback,
            'pending_feedback': pending_feedback,
            'rejected_feedback': rejected_feedback,
            'validation_rules': {
                'max_feedback_per_user_per_day': self.max_feedback_per_user_per_day,
                'max_feedback_per_location_per_hour': self.max_feedback_per_location_per_hour,
                'auto_approve_rating_range': self.auto_approve_rating_range,
                'trusted_user_threshold': self.trusted_user_threshold,
            }
        }


# Global instance
feedback_validator = FeedbackValidator()
