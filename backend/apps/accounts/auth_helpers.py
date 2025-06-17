from django.contrib.auth.models import User
from django.conf import settings
import jwt
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError
import logging
from utils.http import create_cors_response
import time

logger = logging.getLogger(__name__)

def create_jwt_token(user):
    """
    Creates a JWT token for the given user
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