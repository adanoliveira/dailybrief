from django.shortcuts import render
from django.http import JsonResponse
from .models import Topic, Region, Language, Publication
from .serializers import TopicSerializer, RegionSerializer, LanguageSerializer, PublicationSerializer
import json
import logging
import traceback
from django.conf import settings
from django.db.models import Q

# NEW: Import enhanced API utilities
from apps.core.api_utils import (
    api_view, create_response, create_error_response, 
    paginate_response
)

logger = logging.getLogger(__name__)

# Create your views here.

@api_view(['GET'], authenticate=False)
def get_topics(request):
    """
    Get all available topics/categories.
    Public endpoint - no authentication required.
    """
    topics = Topic.objects.all().order_by('name').values('id', 'name', 'slug')
    return create_response({'topics': list(topics)})

@api_view(['GET'], authenticate=False)
def get_regions(request):
    """
    Get all available regions.
    Public endpoint - no authentication required.
    """
    regions = Region.objects.all().order_by('name').values('id', 'code', 'name')
    return create_response({'regions': list(regions)})

@api_view(['GET'], authenticate=False)
def get_languages(request):
    """
    Get all available languages.
    Public endpoint - no authentication required.
    """
    languages = Language.objects.all().order_by('name').values('id', 'iso_code', 'name')
    return create_response({'languages': list(languages)})

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
    user = request.user  # Authenticated by @api_view
    
    # Get the filter mode (recommended or other)
    filter_mode = request.GET.get('filter_mode', 'recommended')
    
    # Get all topic IDs from query params (can be multiple)
    topic_ids = request.GET.getlist('topic_id')
    
    # Get all region codes from query params (can be multiple)
    region_codes = request.GET.getlist('region_code')
    
    # Get language code (single)
    language_code = request.GET.get('language_code')
    
    # Get pagination parameters
    page = int(request.GET.get('page', 1))
    page_size = min(int(request.GET.get('page_size', 20)), 100)  # Max 100 per page
    
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
    
    # Use enhanced pagination utility
    result = paginate_response(publications, page, page_size, max_page_size=100)
    
    # Transform publications to expected format
    publications_list = []
    for pub in result['items']:
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
    
    # Replace items with formatted data
    result['results'] = publications_list
    del result['items']  # Remove the raw items
    
    return create_response(result)

# Debug endpoint removed for production

@api_view(['GET'], authenticate=False)
def basic_data(request):
    """
    Get all reference data for onboarding in a single request.
    Public endpoint - provides data needed before user authentication.
    """
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
    
    return create_response(data)

@api_view(['GET'], authenticate=False)
def get_reference_data(request):
    """
    Get all reference data for onboarding in a single request.
    Legacy endpoint - use basic_data() instead.
    Provides hardcoded sample data for debugging.
    """
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
    return create_response(data)
