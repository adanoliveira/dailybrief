"""
Enhanced API utility functions for standardized JSON responses across DailyBrief.

This module provides a unified approach to:
- Authentication handling (JWT via NextAuth)
- CORS management (development/production)
- Response formatting (success/error standardization)
- HTTP method validation
- Exception handling

Usage:
    @api_view(['GET', 'POST'])
    def my_view(request):
        user = request.user  # Automatically authenticated
        return create_response({'data': 'success'})
"""
from django.http import JsonResponse, HttpRequest, HttpResponseBase
from django.conf import settings
from django.contrib.auth.models import User
import json
import traceback
import logging
import jwt
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError
import time
from typing import Dict, Any, Optional, Union, List
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# ============================================================================
# AUTHENTICATION UTILITIES (Consolidated from auth_helpers.py)
# ============================================================================

def create_jwt_token(user):
    """
    Creates a JWT token for the given user.
    
    Args:
        user: Django User instance
        
    Returns:
        str: JWT token string
        
    Raises:
        ValueError: If token generation fails
    """
    payload = {
        'user_id': user.id,
        'django_user_id': user.id,  # Add this for compatibility
        'email': user.email,
        'exp': int(time.time()) + 60 * 60 * 24 * 30,  # 30 days expiration
    }
    
    # Generate the token
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
    
    # Validate the token format
    try:
        # Ensure the token is a string (PyJWT sometimes returns bytes)
        if isinstance(token, bytes):
            token = token.decode('utf-8')
            
        # Basic format validation
        if not token or token.count('.') != 2:
            logger.error(f"Generated invalid JWT token format: {token[:10]}...")
            raise ValueError("Generated token has invalid format")
            
        # Verify the token can be decoded
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        if decoded['user_id'] != user.id:
            logger.error("Generated token has incorrect user_id")
            raise ValueError("Generated token has incorrect payload")
            
        logger.info(f"Successfully generated JWT token for user {user.id}")
        return token
    except Exception as e:
        logger.error(f"Error validating generated token: {str(e)}")
        raise

def authenticate_request(request):
    """
    Authenticate a request using JWT token from NextAuth.
    
    Args:
        request: Django HttpRequest object
        
    Returns:
        tuple: (is_authenticated, user, error_message)
    """
    # Get the token from the authorization header
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    
    # Check if we have an auth header
    if not auth_header:
        logger.warning("No Authorization header found")
        return False, None, "No Authorization header"
    
    # Check for Bearer token
    if auth_header.startswith('Bearer '):
        token = auth_header[7:].strip()  # Remove 'Bearer ' prefix and trim whitespace
        
        # Validate token format before attempting to decode
        if not token:
            logger.warning("Empty token provided")
            return False, None, "Empty token provided"
            
        # Basic JWT format validation (should have 3 segments separated by dots)
        if token.count('.') != 2:
            logger.warning(f"JWT token error: Not enough segments (found {token.count('.')+1}, expected 3)")
            return False, None, f"Invalid token format: expected 3 segments, got {token.count('.')+1}"
        
        try:
            # Decode JWT token
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            
            # Get user from payload - check both keys for backwards compatibility
            user_id = payload.get('django_user_id') or payload.get('user_id')
            if not user_id:
                logger.warning("No user_id or django_user_id in JWT payload")
                return False, None, "Invalid token payload"
                
            # Get user from database
            try:
                user = User.objects.get(id=user_id)
                logger.debug(f"Authenticated user ID: {user.id}")
                return True, user, None
            except User.DoesNotExist:
                logger.warning(f"User with ID {user_id} not found")
                return False, None, "User not found"
                
        except (InvalidTokenError, ExpiredSignatureError) as e:
            logger.warning(f"JWT token error: {str(e)}")
            return False, None, f"Token error: {str(e)}"
    else:
        # Unrecognized authorization format
        logger.warning(f"Unrecognized Authorization header format: {auth_header[:10]}...")
        return False, None, "Invalid authorization format"

def _get_allowed_origins() -> List[str]:
    """Return normalized CORS origins from settings."""
    origins = getattr(settings, "CORS_ALLOWED_ORIGINS", [])
    valid_origins: list[str] = []

    for origin in origins:
        if not origin:
            continue

        parsed = urlparse(origin)
        if parsed.scheme in {"http", "https"} and parsed.netloc:
            valid_origins.append(origin)
        else:
            logger.warning("Ignoring malformed CORS origin in settings: %s", origin)

    return valid_origins


def _resolve_cors_origin(request: Optional[HttpRequest] = None) -> str:
    """
    Resolve which CORS origin should be set on responses.

    Prefers the incoming Origin header when it is explicitly allowlisted.
    Falls back to the first configured allowlisted origin.
    """
    allowed_origins = _get_allowed_origins()
    if not allowed_origins:
        return ""

    if request is not None:
        request_origin = request.META.get("HTTP_ORIGIN", "").strip()
        if request_origin in allowed_origins:
            return request_origin

    return allowed_origins[0]


def get_auth_response(message, status=401, request: Optional[HttpRequest] = None):
    """
    Create a standard authentication error response.
    
    Args:
        message: Error message
        status: HTTP status code (default: 401)
        
    Returns:
        JsonResponse with authentication error
    """
    response = JsonResponse({
        "error": "Authentication failed",
        "detail": message
    }, status=status)
    
    _add_cors_headers(response, request=request, allowed_methods="GET, OPTIONS")
    
    return response

# ============================================================================
# RESPONSE UTILITIES
# ============================================================================

def create_response(
    data: Dict[str, Any],
    status: int = 200,
    request: Optional[HttpRequest] = None
) -> JsonResponse:
    """
    Create a standardized JSON response with CORS headers.
    
    Args:
        data: The data to return in the response
        status: HTTP status code (default: 200)
        
    Returns:
        JsonResponse with CORS headers and standardized format
    """
    response = JsonResponse(data, safe=False, status=status)
    _add_cors_headers(response, request=request)
    return response

def create_error_response(
    message: str, 
    status: int = 400, 
    error_code: Optional[str] = None, 
    details: Optional[Dict[str, Any]] = None,
    request: Optional[HttpRequest] = None
) -> JsonResponse:
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
        "error": message,
        "success": False
    }
    
    if error_code:
        error_data["error_code"] = error_code
        
    if details:
        error_data["details"] = details
        
    return create_response(error_data, status=status, request=request)

def create_success_response(
    data: Dict[str, Any], 
    message: Optional[str] = None,
    status: int = 200,
    request: Optional[HttpRequest] = None
) -> JsonResponse:
    """
    Create a standardized success response.
    
    Args:
        data: The data to return
        message: Optional success message
        status: HTTP status code (default: 200)
        
    Returns:
        JsonResponse with success format and CORS headers
    """
    response_data = {
        "data": data,
        "success": True
    }
    
    if message:
        response_data["message"] = message
        
    return create_response(response_data, status=status, request=request)

def handle_options_request(
    allowed_methods: str = "GET, POST, PUT, DELETE, OPTIONS",
    request: Optional[HttpRequest] = None
) -> JsonResponse:
    """
    Handle OPTIONS requests for CORS preflight.
    
    Args:
        allowed_methods: Comma-separated list of allowed HTTP methods
        
    Returns:
        JsonResponse with appropriate CORS headers
    """
    response = JsonResponse({})
    _add_cors_headers(response, request=request, allowed_methods=allowed_methods)
    response["Access-Control-Max-Age"] = "86400"  # 24 hours
    return response

def parse_request_body(request) -> tuple[Optional[Dict[str, Any]], Optional[JsonResponse]]:
    """
    Parse JSON request body with error handling.
    
    Args:
        request: Django HttpRequest object
        
    Returns:
        tuple: (data, error_response)
        If successful, data will contain the parsed JSON and error_response will be None.
        If parsing fails, data will be None and error_response will be a JsonResponse.
    """
    try:
        if not request.body:
            return {}, None
        data = json.loads(request.body)
        return data, None
    except json.JSONDecodeError as e:
        error = create_error_response(
            "Invalid JSON in request body", 
            status=400,
            details={"json_error": str(e)}
        )
        return None, error

def api_view(
    allowed_methods: Optional[List[str]] = None, 
    authenticate: bool = True, 
    staff_required: bool = False,
    skip_auth_dev: bool = False
):
    """
    Enhanced decorator for API views with comprehensive feature set.
    
    Features:
    - Automatic OPTIONS handling for CORS
    - HTTP method validation
    - JWT authentication via NextAuth integration
    - Staff-only access control
    - Standardized error responses
    - Development mode auth skipping
    - Exception handling with logging
    
    Args:
        allowed_methods: List of allowed HTTP methods (default: ["GET"])
        authenticate: Whether to authenticate the request (default: True)
        staff_required: Whether staff permissions are required (default: False)
        skip_auth_dev: Whether to skip authentication in development (default: False)
        
    Usage:
        @api_view(['GET', 'POST'])
        def my_view(request):
            user = request.user  # Available after authentication
            return create_response({'data': 'success'})
            
        @api_view(['POST'], staff_required=True)
        def admin_view(request):
            # Only staff users can access
            return create_response({'admin': 'data'})
        
    Returns:
        Decorated view function with automatic handling
    """
    if allowed_methods is None:
        allowed_methods = ["GET"]
        
    # Convert to uppercase for consistency
    allowed_methods = [m.upper() for m in allowed_methods]
    
    def decorator(view_func):
        from functools import wraps
        from django.views.decorators.csrf import csrf_exempt
        
        @csrf_exempt  # API endpoints use JWT auth, not CSRF tokens
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Handle OPTIONS requests for CORS preflight
            if request.method == "OPTIONS":
                return handle_options_request(", ".join(allowed_methods + ["OPTIONS"]), request=request)
                
            # Validate HTTP method
            if request.method.upper() not in allowed_methods:
                return create_error_response(
                    f"Method {request.method} not allowed",
                    status=405,
                    details={
                        "allowed_methods": allowed_methods,
                        "received_method": request.method
                    },
                    request=request
                )
                
            # Handle authentication if required
            if authenticate:
                # Skip auth in development if specified
                should_skip_auth = (
                    skip_auth_dev and 
                    getattr(settings, 'DEBUG', False) and
                    hasattr(request, 'skip_auth_for_dev')
                )
                
                if not should_skip_auth:
                    authenticated, user, error = authenticate_request(request)
                    if not authenticated:
                        return get_auth_response(error, request=request)
                    
                    # Staff requirement check
                    if staff_required and not user.is_staff:
                        return create_error_response(
                            "Staff permissions required",
                            status=403,
                            error_code="INSUFFICIENT_PERMISSIONS",
                            request=request
                        )
                    
                    # Add authenticated user to request
                    request.user = user
            
            # Execute the view with comprehensive error handling
            try:
                response = view_func(request, *args, **kwargs)
                if isinstance(response, HttpResponseBase):
                    # Enforce request-aware CORS headers even when callers
                    # build responses without passing request=request.
                    _add_cors_headers(response, request=request)
                return response
            except Exception as e:
                # Log the full exception for debugging
                logger.error(f"Error in {view_func.__name__}: {e}")
                logger.error(f"Request path: {request.path}")
                logger.error(f"Request method: {request.method}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                
                # Return user-friendly error response
                if settings.DEBUG:
                    # Include more details in debug mode
                    return create_error_response(
                        f"Internal server error: {str(e)}",
                        status=500,
                        error_code="INTERNAL_ERROR",
                        details={
                            "exception_type": type(e).__name__,
                            "view_function": view_func.__name__
                        },
                        request=request
                    )
                else:
                    # Generic error in production
                    return create_error_response(
                        "An internal error occurred. Please try again.",
                        status=500,
                        error_code="INTERNAL_ERROR",
                        request=request
                    )
                
        return wrapper
    
    return decorator

def _add_cors_headers(
    response: JsonResponse,
    request: Optional[HttpRequest] = None,
    allowed_methods: str = "GET, POST, PUT, DELETE, OPTIONS"
) -> None:
    """
    Add CORS headers to a response object.
    
    Args:
        response: JsonResponse object to modify
    """
    allow_origin = _resolve_cors_origin(request)
    if allow_origin:
        response["Access-Control-Allow-Origin"] = allow_origin
        response["Vary"] = "Origin"
    response["Access-Control-Allow-Methods"] = allowed_methods
    response["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With"

# ============================================================================
# LEGACY COMPATIBILITY FUNCTIONS
# ============================================================================

def create_cors_response(
    data: Dict[str, Any], 
    status: int = 200, 
    error: Optional[str] = None
) -> JsonResponse:
    """
    Legacy compatibility function for existing views.
    
    Provides backward compatibility with utils/http.py pattern.
    New views should use create_response() or create_success_response().
    
    Args:
        data: Response data
        status: HTTP status code
        error: Error message (if any)
        
    Returns:
        JsonResponse with CORS headers
    """
    if error:
        return create_error_response(error, status=status)
    return create_response(data, status=status)

# ============================================================================
# PAGINATION UTILITIES
# ============================================================================

def paginate_response(
    queryset, 
    page: int = 1, 
    page_size: int = 10, 
    max_page_size: int = 100
) -> Dict[str, Any]:
    """
    Create pagination metadata for list responses.
    
    Args:
        queryset: Django QuerySet or list to paginate
        page: Current page number
        page_size: Items per page
        max_page_size: Maximum allowed page size
        
    Returns:
        Dictionary with pagination data and items
    """
    from django.core.paginator import Paginator
    
    # Limit page size
    page_size = min(page_size, max_page_size)
    
    # Create paginator
    paginator = Paginator(queryset, page_size)
    
    # Handle invalid page numbers
    if page > paginator.num_pages:
        page = paginator.num_pages
    if page < 1:
        page = 1
        
    page_obj = paginator.get_page(page)
    
    return {
        'items': list(page_obj.object_list),
        'pagination': {
            'page': page,
            'page_size': page_size,
            'total_pages': paginator.num_pages,
            'total_count': paginator.count,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
            'next_page': page + 1 if page_obj.has_next() else None,
            'previous_page': page - 1 if page_obj.has_previous() else None
        }
    } 
