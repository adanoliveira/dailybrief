"""
URL configuration for digest API endpoints.
"""

from django.urls import path, include
from . import views

app_name = 'digest'

urlpatterns = [
    # Latest digest
    path('latest/', views.get_latest_digest, name='latest_digest'),
    
    # Digest by date
    path('date/<str:date_str>/', views.get_digest_by_date, name='digest_by_date'),
    
    # List user's digests
    path('list/', views.list_user_digests, name='list_digests'),
    
    # Generate digest on-demand
    path('generate/', views.generate_digest_on_demand, name='generate_digest'),
    
    # Digest status and content
    path('<str:digest_id>/status/', views.get_digest_status, name='digest_status'),
    path('<str:digest_id>/html/', views.get_digest_html, name='digest_html'),
] 