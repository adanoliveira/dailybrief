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
from apps.accounts.auth_helpers import authenticate_request, get_auth_response, create_jwt_token
from utils.http import create_cors_response, handle_options_request
from django.views.decorators.csrf import csrf_exempt

# Unified endpoint for user sync and status
@csrf_exempt
def user_sync_and_status(request):
    """
    Sync user status and get onboarding status.
    Used by frontend to check user state on app start.
    """
    # Handle OPTIONS requests (preflight CORS)
    if request.method == 'OPTIONS':
        return handle_options_request("GET, POST, OPTIONS")
        
    if request.method == 'GET':
        # Validate authentication - unpack 3 values, not 2
        is_authenticated, user, error_message = authenticate_request(request)
        if not is_authenticated:
            return get_auth_response(error_message)

        try:
            # Get user profile 
            profile = UserProfile.objects.get(user=user)
            
            # Create a new token for the user
            token = create_jwt_token(user)
            
            from apps.feeds.models import UserTopic, Topic
            # Check if user has completed onboarding
            has_completed_onboarding = UserTopic.objects.filter(user=user).exists()
            
            # Get user topics with details
            user_topic_ids = UserTopic.objects.filter(user=user).values_list('topic_id', flat=True)
            
            # Get the topic details (name and slug)
            topics_details = []
            if user_topic_ids:
                topics_details = list(Topic.objects.filter(id__in=user_topic_ids).values('id', 'name', 'slug'))
            
            # Return user data and token
            return create_cors_response({
                'id': user.id,
                'public_id': str(profile.public_id),
                'email': user.email,
                'name': user.first_name,
                'django_token': token,
                'has_completed_onboarding': has_completed_onboarding,
                'topics': list(user_topic_ids),
                'topics_details': topics_details,
            })
            
        except Exception as e:
            return create_cors_response({'error': str(e)}, status=500)
    
    # Handle POST method (sync)
    elif request.method == 'POST':
        # Get the data from the request body
        try:
            data = json.loads(request.body.decode('utf-8'))
        except json.JSONDecodeError:
            return create_cors_response({'error': 'Invalid JSON'}, status=400)
        
        if not data.get('email'):
            return create_cors_response({'error': 'Email is required'}, status=400)
        
        # Find or create the user by email
        email = data.get('email')
        name = data.get('name', '')
        
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'username': email,  # Use email as username
                'first_name': name,
            }
        )
        
        # If user exists but no name, update it
        if not created and name and not user.first_name:
            user.first_name = name
            user.save()
        
        # Create or get user profile with a public_id
        profile, _ = UserProfile.objects.get_or_create(
            user=user,
            defaults={
                'public_id': uuid.uuid4(),
            }
        )
        
        # Create a new token for the user
        token = create_jwt_token(user)
        
        # Check if user has completed onboarding
        from apps.feeds.models import UserTopic
        has_completed_onboarding = UserTopic.objects.filter(user=user).exists()
        
        # Return user data and token
        return create_cors_response({
            'id': user.id,
            'public_id': str(profile.public_id),
            'email': user.email,
            'name': user.first_name,
            'django_token': token,
            'has_completed_onboarding': has_completed_onboarding,
        })
    
    # If method not allowed
    return create_cors_response({'error': 'Method not allowed'}, status=405)

# Consolidated preferences handling
def user_preferences(request):
    """
    Unified endpoint for managing user preferences:
    - GET: Retrieves current user preferences
    - POST: Saves user preferences and marks onboarding as complete
    """
    try:
        # Handle OPTIONS requests (preflight CORS)
        if request.method == 'OPTIONS':
            return handle_options_request("GET, POST, OPTIONS")
            
        # Authenticate for both methods
        authenticated, user, error = authenticate_request(request)
        if not authenticated:
            return create_cors_response({}, status=401, error=error)
            
        # Handle GET request
        if request.method == 'GET':
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
            return create_cors_response({
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
                
        # Handle POST request
        elif request.method == 'POST':
            # Parse request body
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                return create_cors_response(
                    {}, 
                    status=400, 
                    error="Invalid JSON in request body"
                )
                
            # Validate required data
            if 'topics' not in data:
                return create_cors_response(
                    {}, 
                    status=400, 
                    error="Missing required field: topics"
                )
                
            # Get validated data
            topics_ids = data.get('topics', [])
            regions_codes = data.get('regions', [])
            languages_codes = data.get('languages', [])
            publications_ids = data.get('publications', [])
            
            # Validate data types
            if not isinstance(topics_ids, list):
                return create_cors_response(
                    {}, 
                    status=400, 
                    error="topics must be a list"
                )
            
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
            return create_cors_response({
                'message': 'Preferences saved successfully',
                'has_completed_onboarding': True,
            })
        
        # Reject other methods
        else:
            return create_cors_response(
                {}, 
                status=405, 
                error="Method not allowed, use GET or POST"
            )
            
    except Exception as e:
        print(f"Error in user_preferences: {e}")
        print(traceback.format_exc())
        return create_cors_response(
            {}, 
            status=500, 
            error=f"Failed to process preferences: {str(e)}"
        )
