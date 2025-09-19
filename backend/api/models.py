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

    class Meta:
        indexes = [
            models.Index(fields=["location_id"]),
            models.Index(fields=["region", "place_type"]),
        ]

    def __str__(self) -> str:
        return f"{self.location_name or self.location_id} ({self.rating})"

