"""
Comprehensive examples demonstrating the enhanced API utilities.

This file showcases all features of the standardized API approach:
- Basic authenticated endpoints
- Public endpoints (no auth)
- Staff-only administrative endpoints  
- Pagination utilities
- Request validation with detailed error responses
- Multi-method endpoints
- Success responses with messages

Use these as reference patterns when building new API endpoints.
"""
from django.utils import timezone
from datetime import datetime, timedelta

from .api_utils import (
    api_view, create_response, create_error_response, 
    create_success_response, parse_request_body, paginate_response
)

# ============================================================================
# BASIC EXAMPLES
# ============================================================================

@api_view(['GET'], authenticate=False)
def hello_world(request):
    """
    Simple public endpoint that returns a greeting.
    
    Features demonstrated:
    - Public endpoint (no authentication)
    - Query parameter handling
    - Basic response format
    
    Query Parameters:
        name (str, optional): Name to include in greeting
    """
    # Get query parameters
    name = request.GET.get('name')
    language = request.GET.get('language', 'en')
    
    # Create localized greetings
    greetings = {
        'en': 'Hello',
        'es': 'Hola', 
        'fr': 'Bonjour',
        'de': 'Hallo'
    }
    
    greeting = greetings.get(language, greetings['en'])
    
    # Build response data
    data = {
        'message': f'{greeting}, {name}!' if name else f'{greeting}, world!',
        'status': 'ok',
        'version': '1.0',
        'timestamp': timezone.now().isoformat(),
        'language': language
    }
    
    return create_response(data)

@api_view(['POST'], authenticate=False)
def echo_data(request):
    """
    Echo endpoint that validates and returns posted data.
    
    Features demonstrated:
    - Request body parsing with error handling
    - Input validation
    - Error responses with details
    - Success responses
    
    Request Body:
        {
            "message": "string (required)",
            "metadata": "object (optional)"
        }
    """
    # Parse request body
    data, error = parse_request_body(request)
    if error:
        return error
    
    # Validate required fields
    if not data:
        return create_error_response(
            "Request body cannot be empty",
            status=400,
            error_code="EMPTY_REQUEST_BODY"
        )
    
    if 'message' not in data:
        return create_error_response(
            "Missing required field: message",
            status=400,
            error_code="MISSING_REQUIRED_FIELD",
            details={
                "field": "message",
                "required_fields": ["message"],
                "optional_fields": ["metadata"]
            }
        )
    
    # Validate message length
    message = data['message']
    if len(message) > 500:
        return create_error_response(
            "Message too long",
            status=400,
            error_code="MESSAGE_TOO_LONG",
            details={
                "max_length": 500,
                "current_length": len(message)
            }
        )
    
    # Return success response
    return create_success_response(
        {
            'received_message': message,
            'message_length': len(message),
            'metadata': data.get('metadata'),
            'processed_at': timezone.now().isoformat()
        },
        message="Data received and validated successfully"
    )

# ============================================================================
# AUTHENTICATED EXAMPLES
# ============================================================================

@api_view(['GET'])
def get_user_info(request):
    """
    Get current authenticated user's information.
    
    Features demonstrated:
    - Automatic JWT authentication
    - User object access
    - Standard response format
    
    Returns user profile data including preferences count.
    """
    user = request.user  # Automatically authenticated
    
    # Get additional user data (mock for example)
    user_data = {
        'user_id': user.id,
        'email': user.email,
        'name': user.first_name or user.username,
        'is_staff': user.is_staff,
        'date_joined': user.date_joined.isoformat(),
        'last_login': user.last_login.isoformat() if user.last_login else None,
        # Mock data for demonstration
        'preferences_count': 5,
        'articles_read': 42,
        'last_activity': (timezone.now() - timedelta(hours=2)).isoformat()
    }
    
    return create_response(user_data)

@api_view(['GET', 'POST', 'PUT'])
def manage_user_settings(request):
    """
    Multi-method endpoint for user settings management.
    
    Features demonstrated:
    - Multiple HTTP methods in one view
    - Method-specific logic
    - Request validation per method
    - Success responses with messages
    
    GET: Retrieve current settings
    POST: Create new settings
    PUT: Update existing settings
    """
    user = request.user
    
    if request.method == 'GET':
        # Mock user settings for demonstration
        settings = {
            'notifications_enabled': True,
            'email_frequency': 'daily',
            'preferred_topics': ['technology', 'business'],
            'reading_time_preference': 'short',
            'last_updated': (timezone.now() - timedelta(days=3)).isoformat()
        }
        
        return create_response({
            'settings': settings,
            'user_id': user.id
        })
    
    elif request.method in ['POST', 'PUT']:
        # Parse and validate request body
        data, error = parse_request_body(request)
        if error:
            return error
        
        # Validate settings structure
        valid_settings = {
            'notifications_enabled': bool,
            'email_frequency': ['daily', 'weekly', 'never'],
            'preferred_topics': list,
            'reading_time_preference': ['short', 'medium', 'long']
        }
        
        for field, expected_type in valid_settings.items():
            if field in data:
                if isinstance(expected_type, list):
                    # Choice field validation
                    if data[field] not in expected_type:
                        return create_error_response(
                            f"Invalid value for {field}",
                            status=400,
                            error_code="INVALID_CHOICE",
                            details={
                                "field": field,
                                "value": data[field],
                                "valid_choices": expected_type
                            }
                        )
                elif not isinstance(data[field], expected_type):
                    # Type validation
                    return create_error_response(
                        f"Invalid type for {field}",
                        status=400,
                        error_code="INVALID_TYPE",
                        details={
                            "field": field,
                            "expected_type": expected_type.__name__,
                            "received_type": type(data[field]).__name__
                        }
                    )
        
        # Mock saving the settings
        action = "created" if request.method == 'POST' else "updated"
        
        return create_success_response(
            {
                'settings': data,
                'user_id': user.id,
                'updated_at': timezone.now().isoformat()
            },
            message=f"Settings {action} successfully"
        )

# ============================================================================
# PAGINATION EXAMPLE
# ============================================================================

@api_view(['GET'])
def list_user_activities(request):
    """
    Paginated list of user activities (mock data).
    
    Features demonstrated:
    - Built-in pagination utility
    - Query parameter validation
    - Filtering options
    - Comprehensive pagination metadata
    
    Query Parameters:
        page (int): Page number (default: 1)
        page_size (int): Items per page (default: 10, max: 50)
        activity_type (str): Filter by activity type
        days (int): Activities from last N days (default: 30)
    """
    user = request.user
    
    # Get and validate query parameters
    try:
        page = int(request.GET.get('page', 1))
        page_size = min(int(request.GET.get('page_size', 10)), 50)
        days = int(request.GET.get('days', 30))
    except ValueError:
        return create_error_response(
            "Invalid query parameters",
            status=400,
            error_code="INVALID_QUERY_PARAMS",
            details={
                "page": "Must be integer",
                "page_size": "Must be integer (max 50)",
                "days": "Must be integer"
            }
        )
    
    activity_type = request.GET.get('activity_type')
    
    # Mock activity data (in real app, this would be a QuerySet)
    base_time = timezone.now()
    mock_activities = []
    
    for i in range(100):  # Mock 100 activities
        activity = {
            'id': i + 1,
            'type': ['read', 'liked', 'shared', 'commented'][i % 4],
            'title': f'Article {i + 1}: Sample Title',
            'timestamp': (base_time - timedelta(hours=i * 2)).isoformat(),
            'duration_minutes': (i % 10) + 1
        }
        
        # Apply activity type filter
        if activity_type and activity['type'] != activity_type:
            continue
        
        # Apply days filter
        activity_time = base_time - timedelta(hours=i * 2)
        if activity_time < base_time - timedelta(days=days):
            continue
            
        mock_activities.append(activity)
    
    # Use pagination utility
    result = paginate_response(mock_activities, page, page_size, max_page_size=50)
    
    # Add filter information to response
    result['filters_applied'] = {
        'activity_type': activity_type,
        'days': days,
        'user_id': user.id
    }
    
    return create_response(result)

# ============================================================================
# STAFF-ONLY ADMINISTRATIVE EXAMPLES
# ============================================================================

@api_view(['GET'], staff_required=True)
def admin_dashboard_stats(request):
    """
    Administrative dashboard statistics.
    
    Features demonstrated:
    - Staff-only access control
    - Administrative data aggregation
    - System-wide statistics
    
    Only accessible to staff users.
    """
    user = request.user  # Guaranteed to be staff
    
    # Mock admin statistics
    stats = {
        'total_users': 1250,
        'active_users_today': 89,
        'new_users_this_week': 24,
        'total_articles': 15678,
        'articles_processed_today': 234,
        'api_requests_last_hour': 1456,
        'error_rate_percentage': 0.3,
        'generated_at': timezone.now().isoformat(),
        'requested_by': user.email
    }
    
    return create_response(stats)

@api_view(['POST'], staff_required=True)
def admin_system_action(request):
    """
    Administrative system action endpoint.
    
    Features demonstrated:
    - Staff-only administrative actions
    - Action validation and logging
    - Comprehensive error handling for admin actions
    
    Request Body:
        {
            "action": "string (required)",
            "parameters": "object (optional)"
        }
    """
    user = request.user  # Guaranteed to be staff
    
    # Parse request body
    data, error = parse_request_body(request)
    if error:
        return error
    
    # Validate action
    if 'action' not in data:
        return create_error_response(
            "Missing required field: action",
            status=400,
            error_code="MISSING_ACTION"
        )
    
    action = data['action']
    parameters = data.get('parameters', {})
    
    # Validate allowed actions
    allowed_actions = [
        'clear_cache',
        'rebuild_index', 
        'send_notification',
        'generate_report'
    ]
    
    if action not in allowed_actions:
        return create_error_response(
            "Invalid action",
            status=400,
            error_code="INVALID_ACTION",
            details={
                "action": action,
                "allowed_actions": allowed_actions
            }
        )
    
    # Mock action execution
    execution_time = timezone.now()
    
    # Simulate different action results
    if action == 'clear_cache':
        result = {
            'cache_entries_cleared': 1234,
            'cache_size_freed_mb': 45.7
        }
    elif action == 'rebuild_index':
        result = {
            'documents_indexed': 15678,
            'index_build_time_seconds': 23.4
        }
    elif action == 'send_notification':
        result = {
            'notifications_sent': 567,
            'delivery_rate_percentage': 98.2
        }
    else:  # generate_report
        result = {
            'report_id': f'RPT-{execution_time.strftime("%Y%m%d%H%M%S")}',
            'report_size_kb': 234.5
        }
    
    return create_success_response(
        {
            'action': action,
            'parameters': parameters,
            'result': result,
            'executed_at': execution_time.isoformat(),
            'executed_by': user.email,
            'execution_id': f'EXE-{execution_time.strftime("%Y%m%d%H%M%S")}'
        },
        message=f"Administrative action '{action}' completed successfully"
    )

# ============================================================================
# ERROR HANDLING EXAMPLES
# ============================================================================

@api_view(['GET'])
def test_error_responses(request):
    """
    Test endpoint to demonstrate various error response formats.
    
    Features demonstrated:
    - Different error types and status codes
    - Error codes and details
    - Comprehensive error information
    
    Query Parameters:
        error_type (str): Type of error to simulate
    """
    user = request.user
    
    error_type = request.GET.get('error_type', 'none')
    
    if error_type == 'validation':
        return create_error_response(
            "Validation failed for multiple fields",
            status=400,
            error_code="VALIDATION_ERROR",
            details={
                "errors": [
                    {"field": "email", "message": "Invalid email format"},
                    {"field": "age", "message": "Must be between 18 and 120"}
                ],
                "input_received": {"email": "invalid-email", "age": 150}
            }
        )
    
    elif error_type == 'not_found':
        return create_error_response(
            "Requested resource not found",
            status=404,
            error_code="RESOURCE_NOT_FOUND",
            details={
                "resource_type": "article",
                "resource_id": "123",
                "available_resources": ["articles", "users", "topics"]
            }
        )
    
    elif error_type == 'permission':
        return create_error_response(
            "Insufficient permissions for this action",
            status=403,
            error_code="INSUFFICIENT_PERMISSIONS",
            details={
                "required_permission": "admin",
                "user_permissions": ["read", "write"],
                "action_attempted": "delete_user"
            }
        )
    
    elif error_type == 'rate_limit':
        return create_error_response(
            "Rate limit exceeded",
            status=429,
            error_code="RATE_LIMIT_EXCEEDED",
            details={
                "limit": 100,
                "requests_made": 100,
                "reset_time": (timezone.now() + timedelta(minutes=15)).isoformat(),
                "retry_after_seconds": 900
            }
        )
    
    else:
        # No error - return success
        return create_response({
            'message': 'No error requested',
            'available_error_types': [
                'validation', 'not_found', 'permission', 'rate_limit'
            ],
            'user_id': user.id
        }) 