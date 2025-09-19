from django.contrib import admin
from .models import Feedback


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ("id", "location_name", "location_id", "rating", "region", "place_type", "created_at")
    search_fields = ("location_name", "location_id", "region", "place_type", "comment")
    list_filter = ("region", "place_type", "rating")

# Register your models here.
