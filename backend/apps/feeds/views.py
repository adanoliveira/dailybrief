from django.shortcuts import render
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from .models import Topic, Region, Language, Publication
from .serializers import TopicSerializer, RegionSerializer, LanguageSerializer, PublicationSerializer
import json
import logging
import traceback
from rest_framework.permissions import AllowAny
from apps.accounts.auth_helpers import authenticate_request, get_auth_response

logger = logging.getLogger(__name__)

# Create your views here.

@api_view(['GET'])
def get_topics(request):
    """
    Get all available topics/categories.
    """
    topics = Topic.objects.all().order_by('name')
    serializer = TopicSerializer(topics, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def get_regions(request):
    """
    Get all available regions.
    """
    regions = Region.objects.all().order_by('name')
    serializer = RegionSerializer(regions, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def get_languages(request):
    """
    Get all available languages.
    """
    languages = Language.objects.all().order_by('name')
    serializer = LanguageSerializer(languages, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def get_publications(request):
    """
    Get all available publications.
    Optionally filter by topic_id, region_code, or language_code.
    """
    publications = Publication.objects.all().order_by('name')
    
    # Filter by topic if provided
    topic_id = request.query_params.get('topic_id')
    if topic_id:
        publications = publications.filter(topics__id=topic_id)
    
    # Filter by region if provided
    region_code = request.query_params.get('region_code')
    if region_code:
        publications = publications.filter(regions__code=region_code)
    
    # Filter by language if provided
    language_code = request.query_params.get('language_code')
    if language_code:
        publications = publications.filter(languages__iso_code=language_code)
    
    serializer = PublicationSerializer(publications, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([AllowAny])  # Allow any user (no authentication required)
def debug_endpoint(request):
    """
    Debug endpoint to help isolate issues - returns hardcoded data
    """
    try:
        # Return hardcoded data without touching DB
        result = {
            "status": "ok",
            "message": "Debug endpoint working",
            "timestamp": "2025-05-02T22:30:00Z",
            "sample_data": {
                "name": "Test Item",
                "value": 42,
                "is_active": True
            }
        }
        logger.info("Debug endpoint success")
        return Response(result)
    except Exception as e:
        logger.error(f"Error in debug endpoint: {e}")
        return Response({"error": str(e)}, status=500)

def basic_data(request):
    """
    Get all reference data for onboarding in a single request.
    Uses Django's JsonResponse directly instead of DRF to avoid recursion issues.
    """
    try:
        # For OPTIONS requests (preflight CORS)
        if request.method == 'OPTIONS':
            response = JsonResponse({})
            response["Access-Control-Allow-Origin"] = "*"
            response["Access-Control-Allow-Methods"] = "GET, OPTIONS"
            response["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
            return response
            
        # Authenticate the request
        skip_auth = True  # Set to False in production for strict auth
        
        if not skip_auth:
            authenticated, user, error = authenticate_request(request)
            if not authenticated:
                return get_auth_response(error)
        
        # Get data from the database
        topics = list(Topic.objects.all().order_by('name').values('id', 'name', 'slug'))
        regions = list(Region.objects.all().order_by('name').values('id', 'code', 'name'))
        languages = list(Language.objects.all().order_by('name').values('id', 'iso_code', 'name'))
        
        # For publications, we need to handle the M2M relationships carefully
        publications_list = []
        publications = Publication.objects.all().order_by('-authority')[:20]
        
        for pub in publications:
            pub_data = {
                'id': pub.id,
                'name': pub.name,
                'website_url': pub.website_url,
                'logo_url': pub.logo_url if pub.logo_url else '',
                'description': pub.description if pub.description else '',
                'authority': float(pub.authority) if pub.authority else 1.0,
                'news_api_id': pub.news_api_id if pub.news_api_id else '',
                # Get related IDs
                'topic_ids': list(pub.topics.values_list('id', flat=True)),
                'region_ids': list(pub.regions.values_list('id', flat=True)),
                'language_ids': list(pub.languages.values_list('id', flat=True)),
            }
            publications_list.append(pub_data)
        
        # Assemble the response
        data = {
            'topics': topics,
            'regions': regions,
            'languages': languages,
            'publications': publications_list
        }
        
        # Return as JSON response with CORS headers
        response = JsonResponse(data, safe=False)
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        return response
    except Exception as e:
        logger.error(f"Error in basic_data view: {e}")
        logger.error(traceback.format_exc())
        error_response = JsonResponse({"error": str(e)}, status=500)
        error_response["Access-Control-Allow-Origin"] = "*"
        return error_response

@api_view(['GET'])
@permission_classes([AllowAny])  # Allow any user (no authentication required)
def get_reference_data(request):
    """
    Get all reference data for onboarding in a single request.
    Note: This DRF-based view has issues with recursion.
    Use basic_data() instead.
    """
    try:
        # Return sample data for now to debug the frontend connection
        data = {
            'topics': [
                {'id': 1, 'name': 'Business', 'slug': 'business'},
                {'id': 2, 'name': 'Entertainment', 'slug': 'entertainment'},
                {'id': 3, 'name': 'General', 'slug': 'general'},
                {'id': 4, 'name': 'Health', 'slug': 'health'},
                {'id': 5, 'name': 'Science', 'slug': 'science'},
                {'id': 6, 'name': 'Sports', 'slug': 'sports'},
                {'id': 7, 'name': 'Technology', 'slug': 'technology'}
            ],
            'regions': [
                {'id': 1, 'code': 'us', 'name': 'United States'},
                {'id': 2, 'code': 'gb', 'name': 'United Kingdom'},
                {'id': 3, 'code': 'ca', 'name': 'Canada'},
                {'id': 4, 'code': 'au', 'name': 'Australia'}
            ],
            'languages': [
                {'id': 1, 'iso_code': 'en', 'name': 'English'},
                {'id': 2, 'iso_code': 'es', 'name': 'Spanish'},
                {'id': 3, 'iso_code': 'fr', 'name': 'French'}
            ],
            'publications': [
                {
                    'id': 1,
                    'name': 'BBC News',
                    'website_url': 'https://www.bbc.co.uk/news',
                    'logo_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/6/62/BBC_News_2019.svg/1200px-BBC_News_2019.svg.png',
                    'description': 'BBC News is an operational business division of the British Broadcasting Corporation.',
                    'authority': 9.5,
                    'news_api_id': 'bbc-news',
                    'topic_ids': [1, 3, 7],
                    'region_ids': [2],
                    'language_ids': [1]
                },
                {
                    'id': 2,
                    'name': 'CNN',
                    'website_url': 'https://www.cnn.com',
                    'logo_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/b/b1/CNN.svg/1200px-CNN.svg.png',
                    'description': 'Cable News Network is a multinational news-based pay television channel.',
                    'authority': 9.0,
                    'news_api_id': 'cnn',
                    'topic_ids': [1, 2, 3],
                    'region_ids': [1],
                    'language_ids': [1]
                }
            ]
        }
        
        logger.info("Returning hardcoded reference data successfully")
        return Response(data)
        
    except Exception as e:
        logger.error(f"Error in get_reference_data: {e}")
        return Response(
            {"error": str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
