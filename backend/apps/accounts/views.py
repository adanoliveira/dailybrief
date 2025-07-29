from django.shortcuts import render
from django.contrib.auth.models import User
from django.conf import settings
from django.http import JsonResponse
from django.db import transaction
import json
import traceback
import jwt
import uuid
from .models import UserProfile
from .serializers import OnboardingDataSerializer

# Import from consolidated API utilities
from apps.core.api_utils import (
    api_view, create_response, create_error_response, 
    create_success_response, parse_request_body, create_jwt_token,
    authenticate_request, get_auth_response
)

# Unified endpoint for user sync and status
@api_view(['GET', 'POST'], authenticate=False)  # Handle auth manually for POST
def user_sync_and_status(request):
    """
    Sync user status and get onboarding status.
    Used by frontend to check user state on app start.
    
    GET: Retrieve current user status (requires auth)
    POST: Sync user from NextAuth (no auth required)
    """
    if request.method == 'GET':
        # For GET requests, we need authentication
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
            return create_response({
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
            return create_error_response(f'Failed to get user status: {str(e)}', status=500)
            
    # Handle POST method (sync) - no auth required
    elif request.method == 'POST':
        # Parse request body
        data, error = parse_request_body(request)
        if error:
            return error

        if not data.get('email'):
            return create_error_response('Email is required', status=400)
        
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
        return create_response({
            'id': user.id,
            'public_id': str(profile.public_id),
            'email': user.email,
            'name': user.first_name,
            'django_token': token,
            'has_completed_onboarding': has_completed_onboarding,
        })

# Consolidated preferences handling
@api_view(['GET', 'POST'])
def user_preferences(request):
    """
    Unified endpoint for managing user preferences:
    - GET: Retrieves current user preferences
    - POST: Saves user preferences and marks onboarding as complete
    """
    user = request.user  # Automatically authenticated by @api_view
            
    # Handle GET request
    if request.method == 'GET':
        # Import models from feeds app
        from apps.feeds.models import (
            UserTopic, UserRegion, UserLanguage, UserPublication
        )
        
        # Get user preferences
        user_topics = list(UserTopic.objects.filter(user=user).values_list('topic_id', flat=True))
        user_regions = list(UserRegion.objects.filter(user=user).values_list('region__code', flat=True))
        user_languages = list(UserLanguage.objects.filter(user=user).values_list('language__iso_code', flat=True))
        user_publications = list(UserPublication.objects.filter(user=user).values_list('publication_id', flat=True))
        
        # Get topic details for the frontend
        from apps.feeds.models import Topic
        user_topics_details = list(
            Topic.objects.filter(id__in=user_topics).values('id', 'name', 'slug')
        )
        
        # Get profile
        profile = UserProfile.objects.get(user=user)
        
        # Return preferences
        return create_response({
            'topics': user_topics,
            'topics_details': user_topics_details,
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
        data, error = parse_request_body(request)
        if error:
            return error
            
        # Validate required data
        if 'topics' not in data:
            return create_error_response(
                "Missing required field: topics", 
                status=400,
                error_code="MISSING_REQUIRED_FIELD"
            )
            
        # Get validated data
        topics_ids = data.get('topics', [])
        regions_codes = data.get('regions', [])
        languages_codes = data.get('languages', [])
        publications_ids = data.get('publications', [])
        
        # Validate data types
        if not isinstance(topics_ids, list):
            return create_error_response(
                "topics must be a list", 
                status=400,
                error_code="INVALID_DATA_TYPE"
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
        return create_success_response(
            {'has_completed_onboarding': True},
            message='Preferences saved successfully'
        )
