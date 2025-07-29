from django.urls import path
from . import views

urlpatterns = [
    # Unified endpoint for user sync and status
    path('sync/', views.user_sync_and_status, name='user_sync_and_status'),
    
    # Unified endpoint for user preferences
    path('preferences/', views.user_preferences, name='user_preferences'),
] 