from django.http import JsonResponse
from typing import Dict, Any, Optional, Union


def create_cors_response(
    data: Dict[str, Any], 
    status: int = 200, 
    error: Optional[str] = None,
    allowed_methods: str = "GET, POST, OPTIONS"
) -> JsonResponse:
    """
    Create a consistent API response with CORS headers.
    
    Args:
        data: The data to return in the response
        status: HTTP status code
        error: Optional error message
        allowed_methods: Comma-separated list of allowed HTTP methods
        
    Returns:
        JsonResponse with appropriate headers and data
    """
    # If error is provided, create an error response
    if error is not None:
        response_data = {"error": error}
        response = JsonResponse(response_data, status=status)
    else:
        response = JsonResponse(data, status=status)
    
    # Add CORS headers
    response["Access-Control-Allow-Origin"] = "*"
    response["Access-Control-Allow-Methods"] = allowed_methods
    response["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    
    return response


def handle_options_request(allowed_methods: str = "GET, POST, OPTIONS") -> JsonResponse:
    """
    Handle OPTIONS requests for CORS preflight.
    
    Args:
        allowed_methods: Comma-separated list of allowed HTTP methods
        
    Returns:
        JsonResponse with appropriate CORS headers
    """
    return create_cors_response({}, allowed_methods=allowed_methods) 