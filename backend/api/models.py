from django.db import models


class Feedback(models.Model):
    """
    Stores user feedback for locations/features to improve scoring over time.
    Prioritize tourist places in Tamil Nadu via place_type and region tags.
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    user_id = models.CharField(max_length=64, blank=True, default="")
    location_id = models.CharField(max_length=128)
    location_name = models.CharField(max_length=256, blank=True, default="")
    latitude = models.FloatField()
    longitude = models.FloatField()
    place_type = models.CharField(max_length=64, blank=True, default="")  # e.g., tourist_place
    region = models.CharField(max_length=64, blank=True, default="")      # e.g., Tamil Nadu

    rating = models.PositiveSmallIntegerField()  # 1..10
    comment = models.TextField(blank=True, default="")
    
    # Approval and validation fields
    APPROVAL_STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('auto_approved', 'Auto Approved'),
    ]
    
    approval_status = models.CharField(
        max_length=20, 
        choices=APPROVAL_STATUS_CHOICES, 
        default='pending'
    )
    approved_by = models.CharField(max_length=64, blank=True, default="")
    approved_at = models.DateTimeField(null=True, blank=True)
    rejected_by = models.CharField(max_length=64, blank=True, default="")
    rejected_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, default="")
    
    # Validation metadata
    validation_errors = models.JSONField(default=list, blank=True)
    is_trusted_user = models.BooleanField(default=False)
    validation_score = models.FloatField(default=0.0)  # 0-1 confidence score

    class Meta:
        indexes = [
            models.Index(fields=["location_id"]),
            models.Index(fields=["region", "place_type"]),
            models.Index(fields=["approval_status"]),
            models.Index(fields=["user_id", "approval_status"]),
        ]

    def __str__(self) -> str:
        return f"{self.location_name or self.location_id} ({self.rating}) - {self.approval_status}"

