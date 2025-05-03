"""
URL patterns for the core app.
"""
from django.urls import path
from . import example_view

# URLs for example views
urlpatterns = [
    # Example views for testing and reference
    path('examples/hello/', example_view.hello_world, name='example_hello'),
    path('examples/echo/', example_view.echo_data, name='example_echo'),
] 