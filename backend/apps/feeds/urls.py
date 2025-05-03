from django.urls import path
from . import views

urlpatterns = [
    path('topics/', views.get_topics, name='topics'),
    path('regions/', views.get_regions, name='regions'),
    path('languages/', views.get_languages, name='languages'),
    path('publications/', views.get_publications, name='publications'),
    path('reference-data/', views.get_reference_data, name='reference_data'),
    path('debug/', views.debug_endpoint, name='debug_endpoint'),
    path('basic-data/', views.basic_data, name='basic_data'),
] 