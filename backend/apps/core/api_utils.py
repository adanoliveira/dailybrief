"""
API utility functions for standardized JSON responses.
"""
from django.http import JsonResponse
import json
import traceback
import logging

logger = logging.getLogger(__name__)

def create_response(data, status=200):
    """
    Create a standardized JSON response with CORS headers.
    
    Args:
        data: The data to return in the response
        status: HTTP status code (default: 200)
        
    Returns:
        JsonResponse with CORS headers
    """
    response = JsonResponse(data, safe=False, status=status)
    response["Access-Control-Allow-Origin"] = "*"
    response["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response

def create_error_response(message, status=400, error_code=None, details=None):
    """
    Create a standardized error response.
    
    Args:
        message: Error message
        status: HTTP status code (default: 400)
        error_code: Application-specific error code (optional)
        details: Additional error details (optional)
        
    Returns:
        JsonResponse with error information and CORS headers
    """
    error_data = {
        "error": message
    }
    
    if error_code:
        error_data["error_code"] = error_code
        
    if details:
        error_data["details"] = details
        
    return create_response(error_data, status=status)

def handle_options_request():
    """
    Handle OPTIONS requests for CORS preflight.
    
    Returns:
        JsonResponse with appropriate CORS headers
    """
    response = JsonResponse({})
    response["Access-Control-Allow-Origin"] = "*"
    response["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response

def parse_request_body(request):
    """
    Parse JSON request body.
    
    Args:
        request: Django HttpRequest object
        
    Returns:
        tuple: (data, error_response)
        If successful, data will contain the parsed JSON and error_response will be None.
        If parsing fails, data will be None and error_response will be a JsonResponse.
    """
    try:
        data = json.loads(request.body)
        return data, None
    except json.JSONDecodeError:
        error = create_error_response("Invalid JSON in request body", status=400)
        return None, error

def api_view(allowed_methods=None, authenticate=True, skip_auth_dev=False):
    """
    Decorator for API views.
    
    Args:
        allowed_methods: List of allowed HTTP methods (default: ["GET"])
        authenticate: Whether to authenticate the request (default: True)
        skip_auth_dev: Whether to skip authentication in development (default: False)
        
    Returns:
        Decorated view function
    """
    if allowed_methods is None:
        allowed_methods = ["GET"]
        
    # Convert to uppercase
    allowed_methods = [m.upper() for m in allowed_methods]
    
    def decorator(view_func):
        from functools import wraps
        from apps.accounts.auth_helpers import authenticate_request, get_auth_response
        
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Handle OPTIONS requests
            if request.method == "OPTIONS":
                return handle_options_request()
                
            # Check if method is allowed
            if request.method.upper() not in allowed_methods:
                return create_error_response(
                    f"Method {request.method} not allowed. Use {', '.join(allowed_methods)}",
                    status=405
                )
                
            # Authenticate if required
            if authenticate:
                do_auth = not (skip_auth_dev and hasattr(request, 'is_dev_environment') and request.is_dev_environment)
                
                if do_auth:
                    authenticated, user, error = authenticate_request(request)
                    if not authenticated:
                        return get_auth_response(error)
                    # Add user to request
                    request.user = user
            
            # Call the view function
            try:
                return view_func(request, *args, **kwargs)
            except Exception as e:
                logger.error(f"Error in {view_func.__name__}: {e}")
                logger.error(traceback.format_exc())
                return create_error_response(
                    f"Internal server error: {str(e)}",
                    status=500
                )
                
        return wrapper
    
    return decorator 