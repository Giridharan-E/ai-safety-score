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
    # Google Maps API key endpoint
    path('google-maps-key/', views.google_maps_key_view, name='google-maps-key'),
    # Cached safety data endpoint
    path('cached-safety-data/', views.cached_safety_data_view, name='cached-safety-data'),
    # Simple test page
    path('tester/', views.test_page_view, name='tester'),
]
