from django.urls import path
from . import views

urlpatterns = [
    path('status/', views.sync_status, name='sync_status'),
    path('trigger/', views.trigger_sync, name='trigger_sync'),
] 