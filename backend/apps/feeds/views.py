from django.shortcuts import render
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from .models import Topic, Region, Language, Publication
from .serializers import TopicSerializer, RegionSerializer, LanguageSerializer, PublicationSerializer
import json
import logging
import traceback
from rest_framework.permissions import AllowAny
from apps.accounts.auth_helpers import authenticate_request, get_auth_response
from django.conf import settings
from django.db.models import Q

logger = logging.getLogger(__name__)

# Custom pagination class
class PublicationPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    
    def get_paginated_response(self, data):
        return Response({
            'results': data,
            'pagination': {
                'page': self.page.number,
                'page_size': self.page_size,
                'total_count': self.page.paginator.count,
                'total_pages': self.page.paginator.num_pages
            }
        })

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
    Get publications with pagination and flexible filtering.
    
    Parameters:
    - filter_mode: 'recommended' (default) or 'other'
        'recommended': Returns publications that match BOTH selected topics AND regions
        'other': Returns publications that DON'T match both criteria (complement)
    
    - topic_id: Can be specified multiple times for multiple topics (OR condition)
    - region_code: Can be specified multiple times for multiple regions (OR condition)
    - language_code: Filter by language
    - page: Page number (default: 1)
    - page_size: Results per page (default: 20)
    """
    # For OPTIONS requests (preflight CORS)
    if request.method == 'OPTIONS':
        response = Response({})
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        return response
    
    # Get the filter mode (recommended or other)
    filter_mode = request.query_params.get('filter_mode', 'recommended')
    
    # Get all topic IDs from query params (can be multiple)
    topic_ids = request.query_params.getlist('topic_id')
    
    # Get all region codes from query params (can be multiple)
    region_codes = request.query_params.getlist('region_code')
    
    # Get language code (single)
    language_code = request.query_params.get('language_code')
    
    # Start with all publications - always order by authority DESC, then ID ASC
    # This ensures deterministic ordering and prevents pagination duplicates
    publications = Publication.objects.all().order_by('-authority', 'id')
    
    # Apply topic and region filtering based on filter_mode
    if topic_ids and region_codes:
        if filter_mode == 'recommended':
            # For recommended: Get publications that match ANY of the topics AND ANY of the regions
            publications = publications.filter(
                topics__id__in=topic_ids,
                regions__code__in=region_codes
            ).distinct()
        elif filter_mode == 'other':
            # For other: Get publications that DON'T match (ANY topic AND ANY region)
            matching_pubs = Publication.objects.filter(
                topics__id__in=topic_ids,
                regions__code__in=region_codes
            ).distinct()
            publications = publications.exclude(id__in=matching_pubs.values_list('id', flat=True))
    elif topic_ids:
        # If only topics specified, filter by topics
        if filter_mode == 'recommended':
            publications = publications.filter(topics__id__in=topic_ids).distinct()
        else:
            publications = publications.exclude(topics__id__in=topic_ids).distinct()
    elif region_codes:
        # If only regions specified, filter by regions
        if filter_mode == 'recommended':
            publications = publications.filter(regions__code__in=region_codes).distinct()
        else:
            publications = publications.exclude(regions__code__in=region_codes).distinct()
    
    # Apply language filter if provided (always filter, not affected by filter_mode)
    if language_code:
        publications = publications.filter(languages__iso_code=language_code)
    
    # Log the query for debugging pagination issues
    logger.info(f"Publications query - Filter mode: {filter_mode}, Topics: {topic_ids}, Regions: {region_codes}")
    logger.info(f"Total matching publications: {publications.count()}")
    
    # Use DRF's pagination
    paginator = PublicationPagination()
    paginator.page_size = int(request.query_params.get('page_size', 20))
    paginated_publications = paginator.paginate_queryset(publications, request)
    
    # Check for duplicates in debug mode
    if settings.DEBUG:
        pub_ids = [p.id for p in paginated_publications]
        if len(pub_ids) != len(set(pub_ids)):
            logger.warning(f"Duplicate publication IDs detected: {pub_ids}")
    
    # Add related entities to each publication
    publications_list = []
    for pub in paginated_publications:
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
            'region_ids': list(pub.regions.values_list('code', flat=True)),
            'language_ids': list(pub.languages.values_list('iso_code', flat=True)),
        }
        publications_list.append(pub_data)
    
    # Use paginator to create response with pagination metadata
    paginated_response = paginator.get_paginated_response(publications_list)
    
    # Add CORS headers
    paginated_response["Access-Control-Allow-Origin"] = "*"
    paginated_response["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    paginated_response["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    
    return paginated_response

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
                # Get related IDs - use codes for regions and languages to be consistent with get_publications
                'topic_ids': list(pub.topics.values_list('id', flat=True)),
                'region_ids': list(pub.regions.values_list('code', flat=True)),
                'language_ids': list(pub.languages.values_list('iso_code', flat=True)),
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
