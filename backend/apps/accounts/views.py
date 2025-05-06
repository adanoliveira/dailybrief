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
from utils.http import create_cors_response, handle_options_request

# Unified endpoint for user sync and status
def user_sync_and_status(request):
    """
    Unified endpoint to handle user synchronization and status checking.
    - POST: Syncs user data from NextAuth, creates/updates Django user
    - GET: Returns current authenticated user status
    """
    try:
        # Handle OPTIONS requests (preflight CORS)
        if request.method == 'OPTIONS':
            return handle_options_request("GET, POST, OPTIONS")
            
        # Handle GET method (status)
        if request.method == 'GET':
            # Authenticate the request
            authenticated, user, error = authenticate_request(request)
            if not authenticated:
                return create_cors_response(
                    {}, 
                    status=401, 
                    error=error
                )
            
            # Get the profile which has the onboarding_completed field
            profile = UserProfile.objects.get(user=user)
            
            # Return the user status with essential information
            return create_cors_response({
                'user_id': user.id,
                'public_id': str(profile.public_id),
                'email': user.email,
                'name': user.first_name,
                'has_completed_onboarding': profile.onboarding_completed,
            })
            
        # Handle POST method (sync)
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

            # Validate request data
            required_fields = ['email', 'name', 'provider', 'nextauth_id']
            for field in required_fields:
                if field not in data:
                    return create_cors_response(
                        {}, 
                        status=400, 
                        error=f"Missing required field: {field}"
                    )
            
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
            return create_cors_response({
                'id': user.id,
                'public_id': str(profile.public_id),
                'email': user.email,
                'name': user.first_name,
                'django_token': token,
                'has_completed_onboarding': has_completed_onboarding,
            })
            
        # Reject other methods
        else:
            return create_cors_response(
                {}, 
                status=405, 
                error="Method not allowed, use GET or POST"
            )
            
    except Exception as e:
        print(f"Error in user_sync_and_status: {e}")
        print(traceback.format_exc())
        return create_cors_response(
            {}, 
            status=500, 
            error=f"Operation failed: {str(e)}"
        )

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
