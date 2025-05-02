from django.contrib.auth.models import User
from django.conf import settings
from rest_framework import authentication
from rest_framework.exceptions import AuthenticationFailed
import jwt
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError

class JWTAuthentication(authentication.BaseAuthentication):
    """
    Custom authentication class for DRF to authenticate users via JWT token from NextAuth.
    """
    def authenticate(self, request):
        # Get the token from the authorization header
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
            return (user, token)
            
        except (InvalidTokenError, ExpiredSignatureError) as e:
            raise AuthenticationFailed(f'Invalid or expired token: {str(e)}')
        except User.DoesNotExist:
            raise AuthenticationFailed('User not found') 