from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Q, F, Count, Case, When, OuterRef, Subquery, Exists
from django.utils import timezone
from django.core.paginator import Paginator
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import uuid
import json
import logging

from apps.accounts.auth_helpers import authenticate_request, get_auth_response
from apps.feeds.models import UserTopic, UserRegion, UserPublication
from .models import Article, UserArticleInteraction
from apps.content.summariser.models import ArticleSummary

logger = logging.getLogger(__name__)

def get_best_content(article):
    """
    Get the best available content for an article, prioritizing processed content.
    
    Priority order:
    1. clean_content (from Step 2 processing)
    2. basic_content (from Step 1 extraction) 
    3. content (legacy field)
    4. description (as final fallback)
    
    Args:
        article (Article): The article instance
        
    Returns:
        str: The best available content
    """
    # Priority 1: Processed clean content from Step 2
    if article.clean_content and len(article.clean_content.strip()) > 100:
        return article.clean_content
    
    # Priority 2: Basic content from Step 1 extraction
    if article.basic_content and len(article.basic_content.strip()) > 100:
        return article.basic_content
    
    # Priority 3: Legacy content field
    if article.content and len(article.content.strip()) > 100:
        return article.content
    
    # Priority 4: Description as final fallback
    return article.description or ''

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
    
    # Filter by user preferences (topics AND publications if available)
    user_topic_ids = UserTopic.objects.filter(user=user).values_list('topic_id', flat=True)
    user_publication_ids = UserPublication.objects.filter(user=user).values_list('publication_id', flat=True)
    
    # Always filter by user's preferred topics
    if user_topic_ids:
        queryset = queryset.filter(topics__in=user_topic_ids)
    else:
        # If user has no topic preferences, return empty queryset
        queryset = queryset.none()
    
    # Additionally filter by publications if user has publication preferences
    if user_publication_ids:
        queryset = queryset.filter(publication__in=user_publication_ids)
    
    queryset = queryset.distinct()
    
    # Apply additional topic filter if specified (and not "for-you" which shows all user topics)
    if topic_slug and topic_slug != 'for-you':
        queryset = queryset.filter(topics__slug=topic_slug)
    
    # Apply search filter if specified
    if search_query:
        queryset = queryset.filter(
            Q(title__icontains=search_query) | 
            Q(description__icontains=search_query) |
            Q(content__icontains=search_query) |
            Q(clean_content__icontains=search_query) |
            Q(basic_content__icontains=search_query)
        )
    
    # Apply sorting
    if sort == 'newest':
        queryset = queryset.order_by('-published_at')
    elif sort == 'oldest':
        queryset = queryset.order_by('published_at')
    else:  # Default relevance sorting
        # Simplified sorting: relevance score → headlines → recency
        queryset = queryset.order_by(
            '-relevance_score',
            '-is_top_headline',
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
            'visualTitle': article.extracted_metadata.get('visual_title') if article.extracted_metadata else None,
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
    Get world feed articles (top headlines from user's preferred regions)
    
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

    # Authenticate user to get their region preferences
    is_authenticated, user, error_message = authenticate_request(request)
    if not is_authenticated:
        return get_auth_response(error_message)

    # Parse query parameters
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 10))
    topic_slug = request.GET.get('topic')
    search_query = request.GET.get('search')
    
    # Base query - get top headlines
    queryset = Article.objects.filter(is_top_headline=True).select_related('language', 'publication').prefetch_related('topics')
    
    # Filter by user's preferred regions
    user_region_codes = UserRegion.objects.filter(user=user).values_list('region__code', flat=True)
    if user_region_codes:
        # Filter articles from publications that serve the user's preferred regions
        queryset = queryset.filter(publication__regions__code__in=user_region_codes).distinct()
    
    # Apply topic filter if specified
    if topic_slug and topic_slug != 'all':
        queryset = queryset.filter(topics__slug=topic_slug)
    
    # Apply search filter if specified
    if search_query:
        queryset = queryset.filter(
            Q(title__icontains=search_query) | 
            Q(description__icontains=search_query) |
            Q(content__icontains=search_query) |
            Q(clean_content__icontains=search_query) |
            Q(basic_content__icontains=search_query)
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
            'visualTitle': article.extracted_metadata.get('visual_title') if article.extracted_metadata else None,
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
        # Prefer structured summary if exists
        if hasattr(article, 'structured_summary'):
            summary = article.structured_summary
        else:
            # Fallback to generic relation accessor if defined differently
            summary = ArticleSummary.objects.filter(article=article).first()
    except Exception as e:
        logger.warning(f"Failed to retrieve summary for article {article.id}: {e}")
        summary = None
    
    # Format topic data
    topics = [{'id': topic.id, 'name': topic.name, 'slug': topic.slug} for topic in article.topics.all()]
    
    # Get publication details
    publication_name = article.source_name or (article.publication.name if article.publication else 'Unknown')
    publication_logo = article.publication.logo_url if article.publication else None
    
    # Format the article data
    article_data = {
        'id': str(article.public_id),
        'title': article.title,
        'visualTitle': article.extracted_metadata.get('visual_title') if article.extracted_metadata else None,
        'description': article.description or '',
        'content': get_best_content(article),
        'source': {
            'name': publication_name,
            'logoUrl': publication_logo
        },
        'author': article.author,
        'publishedAt': article.published_at.isoformat(),
        'imageUrl': article.image_url,
        'url': article.url,
        'isTopHeadline': article.is_top_headline,
        'topics': topics,
        'readTime': round(article.read_time_minutes) if article.read_time_minutes else None,
        'summary': (
            {
                'headline': getattr(summary, 'headline', None),
                'abstract': getattr(summary, 'abstract', None),
                'facts': getattr(summary, 'facts', None),
                'opinions': getattr(summary, 'opinions', None),
                'impact': getattr(summary, 'impact', None),
                # Back-compat fields for older summaries
                'keyPoints': getattr(summary, 'key_points', None),
            }
            if summary else None
        ),
        # Rich content data
        'richContent': {
            'blocks': article.content_blocks if article.content_blocks else [],
            'mediaAssets': [],  # No separate media_assets field, derive from content_blocks
            'formattingData': article.extracted_metadata.get('formatting', {}) if article.extracted_metadata else {},
            'hasRichContent': article.has_rich_content,
            'mediaCount': article.media_count,
            'hasImages': article.has_images,
            'hasVideos': article.has_videos, 
            'hasAudio': article.has_audio,
            'formattingScore': article.content_quality_metrics.get('structure', 0.0) if article.content_quality_metrics else 0.0,
        },
        # Processing pipeline status fields
        'fetchStatus': article.fetch_status,
        'processStatus': article.process_status,
        'summarizationStatus': article.summarization_status,
        'summaryReady': article.summary_ready,
        # Legacy field for backward compatibility
        'contentStatus': article.process_status,
        'contentQuality': {
            'completeness': article.content_quality_metrics.get('completeness', 0.0) if article.content_quality_metrics else None,
            'qualityScore': article.content_quality_metrics.get('quality_score', 0.0) if article.content_quality_metrics else None,
        } if article.content_quality_metrics else None,
        # Additional content fields for frontend logic
        'cleanContent': article.clean_content or '',
        'basicContent': article.basic_content or ''
    }
    
    # Return the response
    response = JsonResponse(article_data)
    response["Access-Control-Allow-Origin"] = "*"
    return response

@csrf_exempt
@require_http_methods(["POST", "OPTIONS"])
def generate_article_summary(request, public_id):
    """
    Generate or refresh the summary for a specific article.
    POST /articles/<public_id>/generate-summary/
    """
    # Handle OPTIONS request for CORS
    if request.method == "OPTIONS":
        response = JsonResponse({})
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        return response

    # Authenticate user
    is_authenticated, user, error_message = authenticate_request(request)
    if not is_authenticated:
        return get_auth_response(error_message)

    try:
        article_uuid = uuid.UUID(public_id)
    except ValueError:
        response = JsonResponse({"error": "Invalid article ID"}, status=400)
        response["Access-Control-Allow-Origin"] = "*"
        return response

    try:
        article = Article.objects.get(public_id=article_uuid)
    except Article.DoesNotExist:
        response = JsonResponse({"error": "Article not found"}, status=404)
        response["Access-Control-Allow-Origin"] = "*"
        return response

    # Parse request body for options
    try:
        body = json.loads(request.body) if request.body else {}
        force_regenerate = body.get('forceRegenerate', False)
    except json.JSONDecodeError:
        response = JsonResponse({"error": "Invalid JSON in request body"}, status=400)
        response["Access-Control-Allow-Origin"] = "*"
        return response

    # Validate article can be summarized
    from apps.articles.models import SummarizationStatus
    
    # Check processing pipeline status
    fetchStatus = article.fetch_status
    processStatus = article.process_status
    
    # Article hasn't been processed yet - don't allow summary generation
    isStillProcessing = (
        fetchStatus in ['pending', 'fetching'] or 
        processStatus in ['pending', 'processing']
    )
    
    # Article processing explicitly failed - don't allow summary generation
    isProcessingFailed = (
        fetchStatus == 'failed' or 
        processStatus == 'failed'
    )
    
    # Check if we have adequate content for summarization
    hasRichContent = article.content_blocks and len(article.content_blocks) > 0
    hasCleanContent = article.clean_content and len(article.clean_content) > 300
    hasBasicContent = article.content and len(article.content) > 200
    
    canGenerateSummary = not isStillProcessing and not isProcessingFailed and (hasRichContent or hasCleanContent or hasBasicContent)
    
    if not canGenerateSummary:
        response = JsonResponse({
            "error": "Article cannot be summarized",
            "details": "Article is still being processed or has insufficient content",
            "fetchStatus": article.fetch_status,
            "processStatus": article.process_status,
            "hasContent": bool(article.content and len(article.content) > 200)
        }, status=422)
        response["Access-Control-Allow-Origin"] = "*"
        return response

    # Check if already being processed
    if article.summarization_status == SummarizationStatus.PROCESSING:
        response = JsonResponse({
            "error": "Summary generation already in progress",
            "status": "processing",
            "message": "Please wait for the current summarization to complete"
        }, status=409)
        response["Access-Control-Allow-Origin"] = "*"
        return response

    # Check if already completed and not forcing regeneration
    if (article.summarization_status == SummarizationStatus.COMPLETED and 
        hasattr(article, 'structured_summary') and 
        not force_regenerate):
        
        summary = article.structured_summary
        response_data = {
            "success": True,
            "message": "Summary already exists",
            "summary": {
                "headline": summary.headline,
                "abstract": summary.abstract,
                "facts": summary.facts,
                "opinions": summary.opinions,
                "impact": summary.impact,
                # Legacy fields for compatibility
                "keyPoints": summary.facts  # Map facts to keyPoints for backward compatibility
            },
            "metadata": {
                "generatedAt": summary.created_at.isoformat(),
                "costUsd": float(summary.cost_usd),
                "processingTimeMs": summary.processing_time_ms,
                "aiModel": summary.ai_model_used,
                "contentSource": summary.content_source,
                "wasRepaired": summary.was_repaired
            }
        }
        response = JsonResponse(response_data)
        response["Access-Control-Allow-Origin"] = "*"
        return response

    # Import and use the summarization service
    try:
        from apps.content.summariser.services import get_summarization_service
        from apps.content.summariser.tasks import summarize_article_pipeline
        
        # Check if we should process synchronously or asynchronously
        process_async = body.get('async', True)  # Default to async
        
        if process_async:
            # Queue the summarization task
            task = summarize_article_pipeline.delay(article.id, force_regenerate=force_regenerate)
            
            response_data = {
                "success": True,
                "message": "Summary generation started",
                "status": "processing",
                "taskId": task.id,
                "estimatedTimeSeconds": 30,  # Rough estimate
                "pollUrl": f"/api/articles/{public_id}/summary-status/"
            }
        else:
            # Process synchronously (for immediate feedback)
            service = get_summarization_service()
            result = service.summarize_article(article, force_regenerate=force_regenerate)
            
            if result.success:
                response_data = {
                    "success": True,
                    "message": "Summary generated successfully",
                    "summary": {
                        "headline": result.headline,
                        "abstract": result.abstract,
                        "facts": result.facts,
                        "opinions": result.opinions,
                        "impact": result.impact,
                        # Legacy fields for compatibility
                        "keyPoints": result.facts
                    },
                    "metadata": {
                        "generatedAt": timezone.now().isoformat(),
                        "costUsd": float(result.total_cost_usd),
                        "processingTimeMs": getattr(result, 'total_duration_ms', 0),
                        "contentSource": result.content_source,
                        "stagesCompleted": result.stages_completed,
                        "requiredCritic": result.required_critic,
                        "wasRepaired": result.was_repaired
                    }
                }
            else:
                response_data = {
                    "success": False,
                    "error": "Summary generation failed",
                    "details": result.error_message,
                    "failedStage": result.failed_stage,
                    "canRetry": result.failed_stage in ['rbc_compression', 'skeleton_summary']
                }
                
    except ImportError as e:
        logger.error(f"Summarization service not available: {e}")
        response_data = {
            "success": False,
            "error": "Summarization service unavailable",
            "details": "The summarization service is not properly configured"
        }
    except Exception as e:
        logger.error(f"Unexpected error during summarization: {e}")
        response_data = {
            "success": False,
            "error": "Internal server error",
            "details": "An unexpected error occurred during summary generation"
        }

    response = JsonResponse(response_data)
    response["Access-Control-Allow-Origin"] = "*"
    return response

@require_http_methods(["GET", "OPTIONS"])
def article_summary_status(request, public_id):
    """
    Check the status of summary generation for an article.
    GET /articles/<public_id>/summary-status/
    """
    # Handle OPTIONS request for CORS
    if request.method == "OPTIONS":
        response = JsonResponse({})
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        return response

    try:
        article_uuid = uuid.UUID(public_id)
    except ValueError:
        response = JsonResponse({"error": "Invalid article ID"}, status=400)
        response["Access-Control-Allow-Origin"] = "*"
        return response

    try:
        article = Article.objects.get(public_id=article_uuid)
    except Article.DoesNotExist:
        response = JsonResponse({"error": "Article not found"}, status=404)
        response["Access-Control-Allow-Origin"] = "*"
        return response

    # Get current summarization status
    status_map = {
        'pending': 'pending',
        'processing': 'processing', 
        'completed': 'completed',
        'failed': 'failed'
    }
    
    current_status = status_map.get(article.summarization_status, 'unknown')
    
    response_data = {
        "status": current_status,
        "summarizationStatus": article.summarization_status,
        "lastAttempt": article.last_summarization_attempt.isoformat() if article.last_summarization_attempt else None,
        "attempts": article.summarization_attempts,
        "errorMessage": article.summarization_error_message if article.summarization_error_message else None
    }
    
    # If completed, include the summary data
    if current_status == 'completed' and hasattr(article, 'structured_summary'):
        summary = article.structured_summary
        response_data["summary"] = {
            "headline": summary.headline,
            "abstract": summary.abstract,
            "facts": summary.facts,
            "opinions": summary.opinions,
            "impact": summary.impact,
            # Legacy fields for compatibility
            "keyPoints": summary.facts
        }
        response_data["metadata"] = {
            "generatedAt": summary.created_at.isoformat(),
            "costUsd": float(summary.cost_usd),
            "processingTimeMs": summary.processing_time_ms,
            "aiModel": summary.ai_model_used,
            "contentSource": summary.content_source,
            "wasRepaired": summary.was_repaired
        }
    
    # If processing, provide estimated completion time
    elif current_status == 'processing':
        # Rough estimate based on when processing started
        if article.last_summarization_attempt:
            elapsed_seconds = (timezone.now() - article.last_summarization_attempt).total_seconds()
            estimated_remaining = max(0, 30 - elapsed_seconds)  # Assume 30 seconds total
            response_data["estimatedRemainingSeconds"] = int(estimated_remaining)
    
    response = JsonResponse(response_data)
    response["Access-Control-Allow-Origin"] = "*"
    return response
