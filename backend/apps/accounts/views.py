from django.shortcuts import render
from django.contrib.auth.models import User
from django.conf import settings
from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
import jwt
import uuid
from .models import UserProfile

# Create your views here.

@api_view(['POST'])
@permission_classes([AllowAny])
def sync_user(request):
    """
    Endpoint for NextAuth to sync user data with Django.
    Creates or updates a Django user based on the NextAuth user data.
    """
    try:
        # Validate request data
        required_fields = ['email', 'name', 'provider', 'nextauth_id']
        for field in required_fields:
            if field not in request.data:
                return Response(
                    {'error': f'Missing required field: {field}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        email = request.data['email']
        name = request.data['name']
        provider = request.data['provider']
        nextauth_id = request.data['nextauth_id']
        image = request.data.get('image', '')
        
        # Try to find existing user by email
        try:
            user = User.objects.get(email=email)
            # Update user data if needed
            if user.first_name != name:
                user.first_name = name
                user.save()
        except User.DoesNotExist:
            # Create new user
            username = f"{email.split('@')[0]}_{uuid.uuid4().hex[:8]}"
            user = User.objects.create_user(
                username=username,
                email=email,
                first_name=name,
                # No password for social/magic link users
                password=None
            )
        
        # Get or create user profile
        try:
            profile = UserProfile.objects.get(user=user)
        except UserProfile.DoesNotExist:
            profile = UserProfile.objects.create(
                user=user,
                # Use default timezone, can be updated later
            )
        
        # Generate JWT token with Django user ID
        payload = {
            'user_id': user.id,
            'email': user.email,
            'django_user_id': user.id,
            'nextauth_id': nextauth_id,
            'profile_id': str(profile.public_id)
        }
        
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
        
        # Return user data and token
        return Response({
            'id': user.id,
            'public_id': str(profile.public_id),
            'email': user.email,
            'name': user.first_name,
            'django_token': token,
            'has_completed_onboarding': False,  # We'll implement this later
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': f'User sync failed: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
def check_onboarding_status(request):
    """
    Check if the authenticated user has completed onboarding.
    Uses the frontend auth token to identify the user.
    """
    # This will be implemented in the next step
    try:
        user = request.user
        # For now, we'll return a placeholder
        # Later we'll check user preferences in the feeds app
        return Response({
            'has_completed_onboarding': False
        })
    except Exception as e:
        return Response(
            {'error': f'Failed to check onboarding status: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
