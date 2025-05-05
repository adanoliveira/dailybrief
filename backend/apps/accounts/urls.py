from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from . import views

urlpatterns = [
    # Unified endpoint for user sync and status
    path('sync/', csrf_exempt(views.user_sync_and_status), name='user_sync_and_status'),
    
    # Unified endpoint for user preferences
    path('preferences/', csrf_exempt(views.user_preferences), name='user_preferences'),
] 