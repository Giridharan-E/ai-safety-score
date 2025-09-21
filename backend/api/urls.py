from django.urls import path
from api import views

urlpatterns = [
    # Combined data endpoint
    path('combined_data/', views.combined_data_view, name='combined-data'),
    # Simple data endpoint (no geocoding)
    path('simple_data/', views.simple_data_view, name='simple-data'),
    # Feedback endpoints
    path('feedback/', views.feedback_view, name='feedback'),
    path('feedback/list/', views.feedback_list_view, name='feedback-list'),
    # Admin feedback management endpoints
    path('admin/feedback/pending/', views.pending_feedback_view, name='pending-feedback'),
    path('admin/feedback/approve/', views.approve_feedback_view, name='approve-feedback'),
    path('admin/feedback/reject/', views.reject_feedback_view, name='reject-feedback'),
    path('admin/feedback/statistics/', views.feedback_statistics_view, name='feedback-statistics'),
    # Feedback aggregation and collection endpoints
    path('feedback/location-summary/', views.location_feedback_summary_view, name='location-feedback-summary'),
    path('feedback/collection-progress/', views.feedback_collection_progress_view, name='feedback-collection-progress'),
    path('feedback/locations-needing/', views.locations_needing_feedback_view, name='locations-needing-feedback'),
    path('feedback/analytics/', views.feedback_analytics_view, name='feedback-analytics'),
    # Trip recommendation endpoints
    path('trip/recommendation/', views.trip_recommendation_view, name='trip-recommendation'),
    path('trip/weather-analysis/', views.trip_weather_analysis_view, name='trip-weather-analysis'),
    path('trip/tourist-factors/', views.trip_tourist_factors_view, name='trip-tourist-factors'),
    # Google Maps API key endpoint
    path('google-maps-key/', views.google_maps_key_view, name='google-maps-key'),
    # Cached safety data endpoint
    path('cached-safety-data/', views.cached_safety_data_view, name='cached-safety-data'),
    # Simple test page
    path('tester/', views.test_page_view, name='tester'),
]
