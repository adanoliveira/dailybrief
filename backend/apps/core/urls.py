"""
URL patterns for the core app - API Examples and Testing.

This file demonstrates URL patterns for the enhanced API utilities,
providing working examples of all available features:
- Public endpoints (no authentication)
- Authenticated user endpoints 
- Staff-only administrative endpoints
- Pagination examples
- Error handling demonstrations

Use these endpoints to test the API utilities and as reference
for implementing similar patterns in other apps.
"""
from django.urls import path
# from . import example_view  # Temporarily commented out due to syntax error

# API Examples - organized by category
urlpatterns = [
    # =========================================================================
    # PUBLIC ENDPOINTS (No Authentication Required)
    # =========================================================================
    
    # Basic public endpoints
    # path('examples/public/hello/', 
    #      example_view.hello_world, 
    #      name='example_hello'),
    
    # path('examples/public/echo/', 
    #      example_view.echo_data, 
    #      name='example_echo'),
    
    # =========================================================================
    # AUTHENTICATED USER ENDPOINTS
    # =========================================================================
    
    # User information and settings
    # path('examples/user/info/', 
    #      example_view.get_user_info, 
    #      name='example_user_info'),
    
    # path('examples/user/settings/', 
    #      example_view.manage_user_settings, 
    #      name='example_user_settings'),
    
    # Pagination example
    # path('examples/user/activities/', 
    #      example_view.list_user_activities, 
    #      name='example_user_activities'),
    
    # =========================================================================
    # STAFF-ONLY ADMINISTRATIVE ENDPOINTS
    # =========================================================================
    
    # Administrative dashboard and actions
    # path('examples/admin/stats/', 
    #      example_view.admin_dashboard_stats, 
    #      name='example_admin_stats'),
    
    # path('examples/admin/action/', 
    #      example_view.admin_system_action, 
    #      name='example_admin_action'),
    
    # =========================================================================
    # TESTING AND ERROR DEMONSTRATION
    # =========================================================================
    
    # Error response testing
    # path('examples/test/errors/', 
    #      example_view.test_error_responses, 
    #      name='example_test_errors'),
]

# Alternative URL patterns with more semantic naming
# Uncomment these if you prefer more descriptive URLs:

"""
urlpatterns += [
    # Public API testing
    path('test/public/greeting/', 
         example_view.hello_world, 
         name='test_public_greeting'),
    
    path('test/public/validation/', 
         example_view.echo_data, 
         name='test_public_validation'),
    
    # User API testing  
    path('test/user/profile/', 
         example_view.get_user_info, 
         name='test_user_profile'),
    
    path('test/user/preferences/', 
         example_view.manage_user_settings, 
         name='test_user_preferences'),
    
    path('test/user/activity-log/', 
         example_view.list_user_activities, 
         name='test_user_activity_log'),
    
    # Admin API testing
    path('test/admin/dashboard/', 
         example_view.admin_dashboard_stats, 
         name='test_admin_dashboard'),
    
    path('test/admin/execute/', 
         example_view.admin_system_action, 
         name='test_admin_execute'),
    
    # Error testing
    path('test/errors/simulate/', 
         example_view.test_error_responses, 
         name='test_error_simulation'),
]
""" 