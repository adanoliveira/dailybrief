from django.shortcuts import render
from django.contrib.auth.models import User
from django.conf import settings
from django.http import JsonResponse
import json
import traceback
from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
import jwt
import uuid
from .models import UserProfile
from .serializers import OnboardingDataSerializer
from django.db import transaction
from apps.accounts.auth_helpers import authenticate_request, get_auth_response

# Create your views here.

def sync_user(request):
    """
    Direct Django view (no DRF) for NextAuth to sync user data with Django.
    Creates or updates a Django user based on the NextAuth user data.
    """
    try:
        # For OPTIONS requests (preflight CORS)
        if request.method == 'OPTIONS':
            response = JsonResponse({})
            response["Access-Control-Allow-Origin"] = "*"
            response["Access-Control-Allow-Methods"] = "POST, OPTIONS"
            response["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
            return response
            
        # Only allow POST method
        if request.method != 'POST':
            error_response = JsonResponse(
                {"error": "Method not allowed, use POST"},
                status=405
            )
            error_response["Access-Control-Allow-Origin"] = "*"
            return error_response
        
        # Parse request body
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            error_response = JsonResponse(
                {"error": "Invalid JSON in request body"},
                status=400
            )
            error_response["Access-Control-Allow-Origin"] = "*"
            return error_response

        # Validate request data
        required_fields = ['email', 'name', 'provider', 'nextauth_id']
        for field in required_fields:
            if field not in data:
                error_response = JsonResponse(
                    {"error": f"Missing required field: {field}"},
                    status=400
                )
                error_response["Access-Control-Allow-Origin"] = "*"
                return error_response
        
        email = data['email']
        name = data['name']
        provider = data['provider']
        nextauth_id = data['nextauth_id']
        image = data.get('image', '')
        
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
        
        # Check if user has completed onboarding
        from apps.feeds.models import UserTopic
        has_completed_onboarding = UserTopic.objects.filter(user=user).exists()
        
        # If the user has completed onboarding, update the profile
        if has_completed_onboarding and not profile.onboarding_completed:
            profile.onboarding_completed = True
            profile.save()
        
        # Return user data and token
        response = JsonResponse({
            'id': user.id,
            'public_id': str(profile.public_id),
            'email': user.email,
            'name': user.first_name,
            'django_token': token,
            'has_completed_onboarding': has_completed_onboarding,
        })
        
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        return response
        
    except Exception as e:
        print(f"Error in sync_user: {e}")
        print(traceback.format_exc())
        error_response = JsonResponse(
            {"error": f"User sync failed: {str(e)}"},
            status=500
        )
        error_response["Access-Control-Allow-Origin"] = "*"
        return error_response

def check_user_status(request):
    """
    Consolidated endpoint to check user status, including:
    - Onboarding completion status
    - Basic user information
    """
    try:
        # For OPTIONS requests (preflight CORS)
        if request.method == 'OPTIONS':
            response = JsonResponse({})
            response["Access-Control-Allow-Origin"] = "*"
            response["Access-Control-Allow-Methods"] = "GET, OPTIONS"
            response["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
            return response
            
        # Only allow GET method
        if request.method != 'GET':
            error_response = JsonResponse(
                {"error": "Method not allowed, use GET"},
                status=405
            )
            error_response["Access-Control-Allow-Origin"] = "*"
            return error_response
            
        # Authenticate the request
        authenticated, user, error = authenticate_request(request)
        if not authenticated:
            return get_auth_response(error)
        
        # Get the profile which has the onboarding_completed field
        profile = UserProfile.objects.get(user=user)
        
        # Return the user status with essential information
        response = JsonResponse({
            'user_id': user.id,
            'public_id': str(profile.public_id),
            'email': user.email,
            'name': user.first_name,
            'has_completed_onboarding': profile.onboarding_completed,
        })
        
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        return response
        
    except Exception as e:
        print(f"Error in check_user_status: {e}")
        print(traceback.format_exc())
        error_response = JsonResponse(
            {"error": f"Failed to check user status: {str(e)}"},
            status=500
        )
        error_response["Access-Control-Allow-Origin"] = "*"
        return error_response

@api_view(['POST'])
def save_onboarding(request):
    """
    Save the user's onboarding preferences and mark onboarding as completed.
    """
    try:
        user = request.user
        
        # Ensure user is authenticated
        if not user.is_authenticated:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Validate request data
        serializer = OnboardingDataSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get validated data
        topics_ids = serializer.validated_data.get('topics', [])
        regions_codes = serializer.validated_data.get('regions', [])
        languages_codes = serializer.validated_data.get('languages', [])
        publications_ids = serializer.validated_data.get('publications', [])
        
        # Import models from feeds app
        from apps.feeds.models import (
            Topic, Region, Language, Publication,
            UserTopic, UserRegion, UserLanguage, UserPublication
        )
        
        # Process the data in a transaction to ensure atomic operations
        with transaction.atomic():
            # Clear existing preferences
            UserTopic.objects.filter(user=user).delete()
            UserRegion.objects.filter(user=user).delete()
            UserLanguage.objects.filter(user=user).delete()
            UserPublication.objects.filter(user=user).delete()
            
            # Add topics
            for topic_id in topics_ids:
                try:
                    topic = Topic.objects.get(id=topic_id)
                    UserTopic.objects.create(user=user, topic=topic)
                except Topic.DoesNotExist:
                    pass  # Skip invalid topic
            
            # Add regions
            for region_code in regions_codes:
                try:
                    region = Region.objects.get(code=region_code)
                    UserRegion.objects.create(user=user, region=region)
                except Region.DoesNotExist:
                    pass  # Skip invalid region
            
            # Add languages
            for language_code in languages_codes:
                try:
                    language = Language.objects.get(iso_code=language_code)
                    UserLanguage.objects.create(user=user, language=language)
                except Language.DoesNotExist:
                    pass  # Skip invalid language
            
            # Add publications (optional)
            for pub_id in publications_ids:
                try:
                    publication = Publication.objects.get(id=pub_id)
                    UserPublication.objects.create(user=user, publication=publication)
                except Publication.DoesNotExist:
                    pass  # Skip invalid publication
            
            # Mark onboarding as completed
            profile = UserProfile.objects.get(user=user)
            profile.onboarding_completed = True
            profile.save()
        
        # Return success response
        return Response({
            'message': 'Onboarding preferences saved successfully',
            'has_completed_onboarding': True,
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': f'Failed to save onboarding preferences: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# Non-DRF direct view for preferences
def save_preferences_direct(request):
    """
    Save user preferences using direct Django view (no DRF)
    to avoid recursion issues.
    """
    try:
        # For OPTIONS requests (preflight CORS)
        if request.method == 'OPTIONS':
            response = JsonResponse({})
            response["Access-Control-Allow-Origin"] = "*"
            response["Access-Control-Allow-Methods"] = "POST, OPTIONS"
            response["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
            return response
            
        # Only allow POST method
        if request.method != 'POST':
            error_response = JsonResponse(
                {"error": "Method not allowed, use POST"},
                status=405
            )
            error_response["Access-Control-Allow-Origin"] = "*"
            return error_response
            
        # Authenticate the request
        authenticated, user, error = authenticate_request(request)
        if not authenticated:
            return get_auth_response(error)
            
        # Parse request body
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            error_response = JsonResponse(
                {"error": "Invalid JSON in request body"},
                status=400
            )
            error_response["Access-Control-Allow-Origin"] = "*"
            return error_response
            
        # Validate required data
        required_fields = ['topics']
        for field in required_fields:
            if field not in data:
                error_response = JsonResponse(
                    {"error": f"Missing required field: {field}"},
                    status=400
                )
                error_response["Access-Control-Allow-Origin"] = "*"
                return error_response
                
        # Get validated data
        topics_ids = data.get('topics', [])
        regions_codes = data.get('regions', [])
        languages_codes = data.get('languages', [])
        publications_ids = data.get('publications', [])
        
        # Validate data types
        if not isinstance(topics_ids, list):
            error_response = JsonResponse(
                {"error": "topics must be a list"},
                status=400
            )
            error_response["Access-Control-Allow-Origin"] = "*"
            return error_response
        
        # Import models from feeds app
        from apps.feeds.models import (
            Topic, Region, Language, Publication,
            UserTopic, UserRegion, UserLanguage, UserPublication
        )
        
        # Process the data in a transaction to ensure atomic operations
        with transaction.atomic():
            # Clear existing preferences
            UserTopic.objects.filter(user=user).delete()
            UserRegion.objects.filter(user=user).delete()
            UserLanguage.objects.filter(user=user).delete()
            UserPublication.objects.filter(user=user).delete()
            
            # Add topics
            for topic_id in topics_ids:
                try:
                    topic = Topic.objects.get(id=topic_id)
                    UserTopic.objects.create(user=user, topic=topic)
                except Topic.DoesNotExist:
                    pass  # Skip invalid topic
            
            # Add regions
            for region_code in regions_codes:
                try:
                    region = Region.objects.get(code=region_code)
                    UserRegion.objects.create(user=user, region=region)
                except Region.DoesNotExist:
                    pass  # Skip invalid region
            
            # Add languages
            for language_code in languages_codes:
                try:
                    language = Language.objects.get(iso_code=language_code)
                    UserLanguage.objects.create(user=user, language=language)
                except Language.DoesNotExist:
                    pass  # Skip invalid language
            
            # Add publications (optional)
            for pub_id in publications_ids:
                try:
                    publication = Publication.objects.get(id=pub_id)
                    UserPublication.objects.create(user=user, publication=publication)
                except Publication.DoesNotExist:
                    pass  # Skip invalid publication
            
            # Mark onboarding as completed
            profile = UserProfile.objects.get(user=user)
            profile.onboarding_completed = True
            profile.save()
        
        # Return success response
        response = JsonResponse({
            'message': 'Preferences saved successfully',
            'has_completed_onboarding': True,
        })
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        return response
        
    except Exception as e:
        print(f"Error in save_preferences_direct: {e}")
        print(traceback.format_exc())
        error_response = JsonResponse(
            {"error": f"Failed to save preferences: {str(e)}"},
            status=500
        )
        error_response["Access-Control-Allow-Origin"] = "*"
        return error_response

def get_preferences_direct(request):
    """
    Get user preferences using direct Django view (no DRF)
    to avoid recursion issues.
    """
    try:
        # For OPTIONS requests (preflight CORS)
        if request.method == 'OPTIONS':
            response = JsonResponse({})
            response["Access-Control-Allow-Origin"] = "*"
            response["Access-Control-Allow-Methods"] = "GET, OPTIONS"
            response["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
            return response
            
        # Only allow GET method
        if request.method != 'GET':
            error_response = JsonResponse(
                {"error": "Method not allowed, use GET"},
                status=405
            )
            error_response["Access-Control-Allow-Origin"] = "*"
            return error_response
            
        # Authenticate the request
        authenticated, user, error = authenticate_request(request)
        if not authenticated:
            return get_auth_response(error)
            
        # Import models from feeds app
        from apps.feeds.models import (
            UserTopic, UserRegion, UserLanguage, UserPublication
        )
        
        # Get user preferences
        user_topics = list(UserTopic.objects.filter(user=user).values_list('topic_id', flat=True))
        user_regions = list(UserRegion.objects.filter(user=user).values_list('region_id', flat=True))
        user_languages = list(UserLanguage.objects.filter(user=user).values_list('language_id', flat=True))
        user_publications = list(UserPublication.objects.filter(user=user).values_list('publication_id', flat=True))
        
        # Get profile
        profile = UserProfile.objects.get(user=user)
        
        # Return preferences
        response = JsonResponse({
            'topics': user_topics,
            'regions': user_regions,
            'languages': user_languages,
            'publications': user_publications,
            'has_completed_onboarding': profile.onboarding_completed,
            'user_id': user.id,
            'public_id': str(profile.public_id),
            'email': user.email,
            'name': user.first_name,
        })
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        return response
        
    except Exception as e:
        print(f"Error in get_preferences_direct: {e}")
        print(traceback.format_exc())
        error_response = JsonResponse(
            {"error": f"Failed to get preferences: {str(e)}"},
            status=500
        )
        error_response["Access-Control-Allow-Origin"] = "*"
        return error_response
