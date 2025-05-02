from django.urls import path
from . import views

urlpatterns = [
    path('sync/', views.sync_user, name='sync_user'),
    path('onboarding-status/', views.check_onboarding_status, name='check_onboarding_status'),
] 