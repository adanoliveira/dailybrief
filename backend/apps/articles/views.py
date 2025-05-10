from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Q, F, Value, Count, Case, When, OuterRef, Subquery, Exists
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.core.paginator import Paginator
from django.views.decorators.http import require_http_methods
import uuid
import json
import logging

from apps.accounts.auth_helpers import authenticate_request, get_auth_response
from apps.feeds.models import UserTopic, UserRegion, UserPublication
from .models import Article, UserArticleInteraction

logger = logging.getLogger(__name__)

@require_http_methods(["GET", "OPTIONS"])
def personalized_feed(request):
    """
    Get personalized feed articles based on user preferences
    
    Query parameters:
    - page: page number (default: 1)
    - page_size: number of articles per page (default: 10)
    - sort: sorting method (relevance, newest, oldest) (default: relevance)
    - topic: filter by topic slug (optional)
    - search: search term (optional)
    """
    # Handle OPTIONS request for CORS
    if request.method == "OPTIONS":
        response = JsonResponse({})
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        return response

    # Authenticate user
    is_authenticated, user, error_message = authenticate_request(request)
    if not is_authenticated:
        return get_auth_response(error_message)
    
    # Parse query parameters
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 10))
    sort = request.GET.get('sort', 'relevance')
    topic_slug = request.GET.get('topic')
    search_query = request.GET.get('search')
    
    # Base query - get all articles
    queryset = Article.objects.select_related('language', 'publication').prefetch_related('topics')
    
    # Filter by user preferences (topics AND publications)
    user_topic_ids = UserTopic.objects.filter(user=user).values_list('topic_id', flat=True)
    user_publication_ids = UserPublication.objects.filter(user=user).values_list('publication_id', flat=True)
    
    # Articles must be from user's preferred topics AND from preferred publications
    preference_filter = Q(topics__in=user_topic_ids) & Q(publication__in=user_publication_ids)
    queryset = queryset.filter(preference_filter).distinct()
    
    # Apply topic filter if specified
    if topic_slug and topic_slug != 'for-you':
        queryset = queryset.filter(topics__slug=topic_slug)
    
    # Apply search filter if specified
    if search_query:
        queryset = queryset.filter(
            Q(title__icontains=search_query) | 
            Q(description__icontains=search_query) |
            Q(content__icontains=search_query)
        )
    
    # Apply sorting
    if sort == 'newest':
        queryset = queryset.order_by('-published_at')
    elif sort == 'oldest':
        queryset = queryset.order_by('published_at')
    else:  # Default relevance sorting
        # Complex sorting based on relevance criteria
        queryset = queryset.annotate(
            pub_authority=Coalesce('publication__authority', Value(1.0)),
        ).order_by(
            '-relevance_score',
            '-is_top_headline',
            '-pub_authority',
            '-published_at'
        )
    
    # Paginate the results
    paginator = Paginator(queryset, page_size)
    page_obj = paginator.get_page(page)
    
    # Prepare the response
    articles_data = []
    for article in page_obj:
        # Format the article data
        # Get article topics
        topics = [{'id': topic.id, 'name': topic.name, 'slug': topic.slug} for topic in article.topics.all()]
        
        # Get publication details
        publication_name = article.source_name or (article.publication.name if article.publication else 'Unknown')
        publication_logo = article.publication.logo_url if article.publication else None
        
        articles_data.append({
            'id': str(article.public_id),
            'title': article.title,
            'description': article.description or '',
            'source': {
                'name': publication_name,
                'logoUrl': publication_logo
            },
            'publishedAt': article.published_at.isoformat(),
            'imageUrl': article.image_url,
            'url': article.url,
            'isTopHeadline': article.is_top_headline,
            'readTime': round(article.read_time_minutes) if article.read_time_minutes else None,
            'topics': topics,
        })
    
    # Build response with pagination metadata
    response_data = {
        'articles': articles_data,
        'pagination': {
            'page': page,
            'pageSize': page_size,
            'totalPages': paginator.num_pages,
            'totalItems': paginator.count,
            'hasNext': page_obj.has_next(),
            'hasPrevious': page_obj.has_previous(),
        }
    }
    
    # Return the response
    response = JsonResponse(response_data)
    response["Access-Control-Allow-Origin"] = "*"
    return response

@require_http_methods(["GET", "OPTIONS"])
def world_feed(request):
    """
    Get world feed articles (top headlines across all sources)
    
    Query parameters:
    - page: page number (default: 1)
    - page_size: number of articles per page (default: 10)
    - topic: filter by topic slug (optional)
    - search: search term (optional)
    """
    # Handle OPTIONS request for CORS
    if request.method == "OPTIONS":
        response = JsonResponse({})
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "GET, OPTIONS" 
        response["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        return response

    # Parse query parameters
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 10))
    topic_slug = request.GET.get('topic')
    search_query = request.GET.get('search')
    
    # Base query - get top headlines
    queryset = Article.objects.filter(is_top_headline=True).select_related('language', 'publication').prefetch_related('topics')
    
    # Apply topic filter if specified
    if topic_slug and topic_slug != 'all':
        queryset = queryset.filter(topics__slug=topic_slug)
    
    # Apply search filter if specified
    if search_query:
        queryset = queryset.filter(
            Q(title__icontains=search_query) | 
            Q(description__icontains=search_query) |
            Q(content__icontains=search_query)
        )
    
    # Sort by published date (newest first)
    queryset = queryset.order_by('-published_at')
    
    # Paginate the results
    paginator = Paginator(queryset, page_size)
    page_obj = paginator.get_page(page)
    
    # Prepare the response
    articles_data = []
    for article in page_obj:
        # Format the article data
        # Get article topics
        topics = [{'id': topic.id, 'name': topic.name, 'slug': topic.slug} for topic in article.topics.all()]
        
        # Get publication details
        publication_name = article.source_name or (article.publication.name if article.publication else 'Unknown')
        publication_logo = article.publication.logo_url if article.publication else None
        
        articles_data.append({
            'id': str(article.public_id),
            'title': article.title,
            'description': article.description or '',
            'source': {
                'name': publication_name,
                'logoUrl': publication_logo
            },
            'publishedAt': article.published_at.isoformat(),
            'imageUrl': article.image_url,
            'url': article.url,
            'isTopHeadline': article.is_top_headline,
            'readTime': round(article.read_time_minutes) if article.read_time_minutes else None,
            'topics': topics,
        })
    
    # Build response with pagination metadata
    response_data = {
        'articles': articles_data,
        'pagination': {
            'page': page,
            'pageSize': page_size,
            'totalPages': paginator.num_pages,
            'totalItems': paginator.count,
            'hasNext': page_obj.has_next(),
            'hasPrevious': page_obj.has_previous(),
        }
    }
    
    # Return the response
    response = JsonResponse(response_data)
    response["Access-Control-Allow-Origin"] = "*"
    return response

@require_http_methods(["GET", "OPTIONS"])
def article_detail(request, public_id):
    """
    Get details for a specific article
    """
    # Handle OPTIONS request for CORS
    if request.method == "OPTIONS":
        response = JsonResponse({})
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        return response

    try:
        # Try to parse the public_id as UUID
        article_uuid = uuid.UUID(public_id)
    except ValueError:
        return JsonResponse({"error": "Invalid article ID"}, status=400)
    
    try:
        # Get the article by public_id
        article = Article.objects.select_related(
            'language', 'publication'
        ).prefetch_related(
            'topics'
        ).get(public_id=article_uuid)
    except Article.DoesNotExist:
        return JsonResponse({"error": "Article not found"}, status=404)
    
    # Get summaries if available
    summary = None
    try:
        summary = article.summary.first()
    except:
        pass
    
    # Format topic data
    topics = [{'id': topic.id, 'name': topic.name, 'slug': topic.slug} for topic in article.topics.all()]
    
    # Format the article data
    article_data = {
        'id': str(article.public_id),
        'title': article.title,
        'description': article.description or '',
        'content': article.content or '',
        'source': {
            'name': article.source_name or (article.publication.name if article.publication else 'Unknown')
        },
        'author': article.author,
        'publishedAt': article.published_at.isoformat(),
        'imageUrl': article.image_url,
        'url': article.url,
        'isTopHeadline': article.is_top_headline,
        'topics': topics,
        'readTime': round(article.read_time_minutes) if article.read_time_minutes else None,
        'summary': {
            'abstract': summary.abstract if summary else None,
            'keyPoints': summary.key_points if summary and hasattr(summary, 'key_points') else None,
        } if summary else None
    }
    
    # Return the response
    response = JsonResponse(article_data)
    response["Access-Control-Allow-Origin"] = "*"
    return response
