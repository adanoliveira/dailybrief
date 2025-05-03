from django.contrib.auth.models import User
from django.conf import settings
import jwt
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError
import logging

logger = logging.getLogger(__name__)

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
        token = auth_header[7:]  # Remove 'Bearer ' prefix
        try:
            # Decode JWT token
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            
            # Get user from payload
            user_id = payload.get('django_user_id')
            if not user_id:
                logger.warning("No django_user_id in JWT payload")
                return False, None, "Invalid token payload"
                
            # Get user from database
            try:
                user = User.objects.get(id=user_id)
                logger.info(f"Authenticated user: {user.username} (ID: {user.id})")
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

def get_auth_response(message, status=401):
    """
    Create a standard authentication error response
    """
    from django.http import JsonResponse
    
    response = JsonResponse({
        "error": "Authentication failed",
        "detail": message
    }, status=status)
    
    # Add CORS headers
    response["Access-Control-Allow-Origin"] = "*"
    response["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    response["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    
    return response 