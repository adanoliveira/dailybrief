from django.contrib.auth.models import User
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from django.utils.functional import SimpleLazyObject
from rest_framework.exceptions import AuthenticationFailed
import jwt
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError

def get_user_from_token(request):
    """
    Extract user from token and attach to request.
    """
    auth_header = request.headers.get('Authorization', '')
    
    if not auth_header.startswith('Bearer '):
        return None
    
    token = auth_header[7:]  # Remove 'Bearer ' prefix
    
    try:
        # Decode JWT token
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        
        # Get user from payload
        user_id = payload.get('django_user_id')
        if not user_id:
            return None
            
        # Get user from database
        user = User.objects.get(id=user_id)
        return user
        
    except (InvalidTokenError, ExpiredSignatureError, User.DoesNotExist) as e:
        return None


class JWTAuthenticationMiddleware(MiddlewareMixin):
    """
    Middleware to authenticate users via JWT token from NextAuth.
    """
    def process_request(self, request):
        # Skip authentication for paths that should be public
        if request.path.startswith('/admin/') or request.path == '/api/auth/sync/':
            return None
            
        # Attach user to request if authenticated
        request.user = SimpleLazyObject(lambda: get_user_from_token(request) or request.user) 