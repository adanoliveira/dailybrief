from datetime import timedelta

from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Q, F, Count, Case, When, OuterRef, Subquery, Exists, Value, FloatField, ExpressionWrapper
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.core.paginator import Paginator
from django.views.decorators.http import require_http_methods
import uuid
import json
import logging

from apps.core.api_utils import (
    authenticate_request, get_auth_response,
    api_view, create_response, create_error_response, 
    create_success_response, parse_request_body
)
import re

from apps.feeds.models import UserTopic, UserRegion, UserPublication, UserLanguage
from .models import Article, UserArticleInteraction
from apps.content.summariser.models import ArticleSummary

logger = logging.getLogger(__name__)

# Maximum articles from a single publication per feed page
MAX_PER_PUBLICATION_PER_PAGE = 5


def _strip_html(text: str) -> str:
    """Strip HTML tags and decode entities from text for plain-text display."""
    if not text:
        return ''
    import html
    cleaned = re.sub(r'<[^>]+>', ' ', text)
    cleaned = html.unescape(cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned


def _diversify_articles(articles_data: list, max_per_source: int = MAX_PER_PUBLICATION_PER_PAGE) -> list:
    """
    Limit articles per publication and deduplicate by headline_cluster.

    Ensures no single source dominates a feed page and that the same
    story covered by multiple sources only appears once (highest-scored).
    """
    seen_sources = {}
    seen_clusters = set()
    result = []

    for article in articles_data:
        source_name = article.get('source', {}).get('name', 'Unknown')
        cluster_id = article.get('_cluster_id')

        # Skip if we've seen this story cluster already
        if cluster_id and cluster_id in seen_clusters:
            continue

        # Skip if this source hit the per-page cap
        source_count = seen_sources.get(source_name, 0)
        if source_count >= max_per_source:
            continue

        seen_sources[source_name] = source_count + 1
        if cluster_id:
            seen_clusters.add(cluster_id)

        # Remove internal field before sending to client
        article.pop('_cluster_id', None)
        result.append(article)

    return result


def _annotate_feed_rank(queryset):
    """
    Annotate a queryset with ``feed_rank`` — a time-decayed quality score
    used for relevance sorting.

    Feed rank blends two signals:

    1. **Quality score** — ``headline_score`` for scored articles (RSS),
       or a fallback derived from publication authority for unscored
       articles (NewsAPI, legacy).
    2. **Time decay** — a multiplier that reduces the effective score as
       the article ages, so fresh news surfaces above older stories of
       similar quality.

    Time decay bands:
        < 6 h   →  1.00  (full weight)
        6–12 h  →  0.90
        12–24 h →  0.75
        24–48 h →  0.50
        > 48 h  →  0.25

    The fallback for unscored articles is ``min(authority, 10) / 10 * 0.7``,
    which maps a publication with authority 9.5 to ~0.665 — comparable to a
    mid-tier scored article.
    """
    now = timezone.now()

    effective_score = Case(
        When(headline_score__gt=0, then=F('headline_score')),
        default=ExpressionWrapper(
            Coalesce(F('publication__authority'), Value(1.0)) / 10.0 * 0.7,
            output_field=FloatField(),
        ),
        output_field=FloatField(),
    )

    time_decay = Case(
        When(published_at__gte=now - timedelta(hours=6), then=Value(1.0)),
        When(published_at__gte=now - timedelta(hours=12), then=Value(0.9)),
        When(published_at__gte=now - timedelta(hours=24), then=Value(0.75)),
        When(published_at__gte=now - timedelta(hours=48), then=Value(0.5)),
        default=Value(0.25),
        output_field=FloatField(),
    )

    return queryset.annotate(
        feed_rank=ExpressionWrapper(
            effective_score * time_decay,
            output_field=FloatField(),
        )
    )


def _serialize_feed_article(article):
    """Serialize article for feed endpoints with internal fields for filtering/counting."""
    topics = [{'id': topic.id, 'name': topic.name, 'slug': topic.slug} for topic in article.topics.all()]
    publication_name = article.source_name or (article.publication.name if article.publication else 'Unknown')
    publication_logo = article.publication.logo_url if article.publication else None

    return {
        'id': str(article.public_id),
        'title': article.title,
        'visualTitle': article.extracted_metadata.get('visual_title') if article.extracted_metadata else None,
        'description': _strip_html(article.description or ''),
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
        '_cluster_id': article.headline_cluster_id,
        '_published_at': article.published_at,
    }


def _build_diversified_page(queryset, page: int, page_size: int) -> tuple[list, Paginator, object]:
    """
    Build a stable page while applying diversity rules.

    To avoid skipping records between pages, diversify from the beginning of the
    ordered queryset up to the requested window and then slice the requested
    page from that diversified sequence.
    """
    paginator = Paginator(queryset, page_size)
    page_obj = paginator.get_page(page)

    safe_page = max(page_obj.number, 1)
    target_end = safe_page * page_size
    fetch_step = max(page_size * 3, page_size)
    fetch_limit = min(paginator.count, max(target_end * 3, fetch_step))

    diversified_articles = []
    while fetch_limit > 0:
        candidates = list(queryset[:fetch_limit])
        serialized = [_serialize_feed_article(article) for article in candidates]
        diversified_articles = _diversify_articles(serialized)

        if len(diversified_articles) >= target_end or fetch_limit >= paginator.count:
            break
        fetch_limit = min(fetch_limit + fetch_step, paginator.count)

    start = (safe_page - 1) * page_size
    end = start + page_size
    return diversified_articles[start:end], paginator, page_obj


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

@api_view(['GET'], authenticate=True)
def personalized_feed(request):
    """
    Get personalized feed of top headlines based on user preferences
    
    Returns only top headlines with completed analysis, filtered by user's preferred topics, languages, and publications.
    (Note: analyzer_status='completed' filter is temporary for initial version)
    
    Query parameters:
    - page: page number (default: 1)
    - page_size: number of articles per page (default: 10)
    - sort: sorting method (relevance, newest, oldest) (default: relevance)
    - topic: filter by topic slug (optional)
    - search: search term (optional)
    - since: ISO timestamp - get only articles published after this time
    - count_only: boolean - return just the count of new articles (no article data)
    - latest_article_id: article public_id - alternative reference point to 'since'
    """
    user = request.user
    
    # Parse query parameters
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 10))
    sort = request.GET.get('sort', 'relevance')
    topic_slug = request.GET.get('topic')
    search_query = request.GET.get('search')
    since = request.GET.get('since')  # ISO timestamp
    count_only = request.GET.get('count_only', '').lower() == 'true'
    latest_article_id = request.GET.get('latest_article_id')
    
    # Base query - get top headlines only with completed analysis (temporary filter for initial version)
    queryset = Article.objects.filter(
        is_top_headline=True,
        analyzer_status='completed'
    ).select_related('language', 'publication').prefetch_related('topics')
    
    # Filter by user preferences (topics, languages, AND publications)
    user_topic_ids = UserTopic.objects.filter(user=user).values_list('topic_id', flat=True)
    user_language_codes = UserLanguage.objects.filter(user=user).values_list('language__iso_code', flat=True)
    user_publication_ids = UserPublication.objects.filter(user=user).values_list('publication_id', flat=True)
    
    # Always filter by user's preferred topics
    if user_topic_ids:
        queryset = queryset.filter(topics__in=user_topic_ids)
    else:
        # If user has no topic preferences, return empty queryset
        queryset = queryset.none()
    
    # Filter by user's preferred languages if available
    if user_language_codes:
        queryset = queryset.filter(language__iso_code__in=user_language_codes)
    
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
    
    # Apply time-based filtering for new article detection
    reference_time = None
    if since:
        try:
            from django.utils.dateparse import parse_datetime
            reference_time = parse_datetime(since)
            if reference_time:
                queryset = queryset.filter(published_at__gt=reference_time)
        except (ValueError, TypeError):
            pass  # Invalid timestamp, ignore
    elif latest_article_id:
        try:
            latest_article = Article.objects.get(public_id=latest_article_id)
            reference_time = latest_article.published_at
            queryset = queryset.filter(published_at__gt=reference_time)
        except Article.DoesNotExist:
            pass  # Article not found, ignore
    
    # For count_only requests, return early with just the count
    if count_only:
        new_articles_count = queryset.count()
        return create_success_response({
            'articles': [],
            'pagination': {
                'page': 1,
                'pageSize': 0,
                'totalPages': 0,
                'totalItems': new_articles_count,
                'hasNext': False,
                'hasPrevious': False
            },
            'new_articles_count': new_articles_count,
            'has_newer_content': new_articles_count > 0,
            'reference_time': reference_time.isoformat() if reference_time else None
        }, message=f"Found {new_articles_count} new analyzed personalized headlines")
    
    # Apply sorting
    if sort == 'newest':
        queryset = queryset.order_by('-published_at')
    elif sort == 'oldest':
        queryset = queryset.order_by('published_at')
    else:  # Default relevance sorting
        # Time-decayed headline score: fresh + important articles rank highest
        queryset = _annotate_feed_rank(queryset).order_by(
            '-feed_rank',
            '-published_at'
        )

    articles_data, paginator, page_obj = _build_diversified_page(queryset, page, page_size)

    # Calculate new articles count for enhanced response
    new_articles_count = 0
    if reference_time or since or latest_article_id:
        if reference_time:
            new_articles_count = len([
                a for a in articles_data
                if a.get('_published_at') and a['_published_at'] > reference_time
            ])
        else:
            new_articles_count = len(articles_data)

    for article in articles_data:
        article.pop('_published_at', None)
    
    # Build response with pagination metadata and new article detection
    response_data = {
        'articles': articles_data,
        'pagination': {
            'page': page,
            'pageSize': page_size,
            'totalPages': paginator.num_pages,
            'totalItems': paginator.count,
            'hasNext': page_obj.has_next(),
            'hasPrevious': page_obj.has_previous(),
        },
        'new_articles_count': new_articles_count,
        'has_newer_content': new_articles_count > 0,
        'reference_time': reference_time.isoformat() if reference_time else None
    }
    
    return create_success_response(
        response_data,
        message=f"Retrieved {len(articles_data)} analyzed personalized headlines"
    )

@api_view(['GET'], authenticate=True)
def world_feed(request):
    """
    Get world feed articles (top headlines from user's preferred regions)
    
    Returns only top headlines with completed analysis from user's preferred regions.
    (Note: analyzer_status='completed' filter is temporary for initial version)
    
    Query parameters:
    - page: page number (default: 1)
    - page_size: number of articles per page (default: 10)
    - topic: filter by topic slug (optional)
    - search: search term (optional)
    - since: ISO timestamp - get only articles published after this time
    - count_only: boolean - return just the count of new articles (no article data)
    - latest_article_id: article public_id - alternative reference point to 'since'
    """
    user = request.user

    # Parse query parameters
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 10))
    topic_slug = request.GET.get('topic')
    search_query = request.GET.get('search')
    since = request.GET.get('since')  # ISO timestamp
    count_only = request.GET.get('count_only', '').lower() == 'true'
    latest_article_id = request.GET.get('latest_article_id')
    
    # Base query - get top headlines with completed analysis (temporary filter for initial version)
    queryset = Article.objects.filter(
        is_top_headline=True,
        analyzer_status='completed'
    ).select_related('language', 'publication').prefetch_related('topics')
    
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
    
    # Apply time-based filtering for new article detection
    reference_time = None
    if since:
        try:
            from django.utils.dateparse import parse_datetime
            reference_time = parse_datetime(since)
            if reference_time:
                queryset = queryset.filter(published_at__gt=reference_time)
        except (ValueError, TypeError):
            pass  # Invalid timestamp, ignore
    elif latest_article_id:
        try:
            latest_article = Article.objects.get(public_id=latest_article_id)
            reference_time = latest_article.published_at
            queryset = queryset.filter(published_at__gt=reference_time)
        except Article.DoesNotExist:
            pass  # Article not found, ignore
    
    # For count_only requests, return early with just the count
    if count_only:
        new_articles_count = queryset.count()
        return create_success_response({
            'articles': [],
            'pagination': {
                'page': 1,
                'pageSize': 0,
                'totalPages': 0,
                'totalItems': new_articles_count,
                'hasNext': False,
                'hasPrevious': False
            },
            'new_articles_count': new_articles_count,
            'has_newer_content': new_articles_count > 0,
            'reference_time': reference_time.isoformat() if reference_time else None
        }, message=f"Found {new_articles_count} new analyzed world headlines")
    
    # Time-decayed headline score for world feed too
    queryset = _annotate_feed_rank(queryset).order_by('-feed_rank', '-published_at')

    articles_data, paginator, page_obj = _build_diversified_page(queryset, page, page_size)

    # Calculate new articles count for enhanced response
    new_articles_count = 0
    if reference_time or since or latest_article_id:
        if reference_time:
            new_articles_count = len([
                a for a in articles_data
                if a.get('_published_at') and a['_published_at'] > reference_time
            ])
        else:
            new_articles_count = len(articles_data)

    for article in articles_data:
        article.pop('_published_at', None)
    
    # Build response with pagination metadata and new article detection
    response_data = {
        'articles': articles_data,
        'pagination': {
            'page': page,
            'pageSize': page_size,
            'totalPages': paginator.num_pages,
            'totalItems': paginator.count,
            'hasNext': page_obj.has_next(),
            'hasPrevious': page_obj.has_previous(),
        },
        'new_articles_count': new_articles_count,
        'has_newer_content': new_articles_count > 0,
        'reference_time': reference_time.isoformat() if reference_time else None
    }
    
    return create_success_response(
        response_data,
        message=f"Retrieved {len(articles_data)} analyzed world headlines"
    )

@api_view(['GET'], authenticate=False)
def public_world_feed(request):
    """
    Get public world feed articles (top US headlines for unauthenticated users)
    Limited to latest 20 articles with completed analysis from US publications for marketing page.
    (Note: analyzer_status='completed' filter is temporary for initial version)
    
    Query parameters:
    - page: page number (default: 1)
    - page_size: number of articles per page (default: 10, max: 20)
    - topic: filter by topic slug (optional)
    - search: search term (optional)
    """
    # Parse query parameters
    page = int(request.GET.get('page', 1))
    page_size = min(int(request.GET.get('page_size', 10)), 20)  # Cap at 20 per page
    topic_slug = request.GET.get('topic')
    search_query = request.GET.get('search')
    
    # Base query - get top headlines from US publications only with completed analysis (temporary filter for initial version)
    # Only include articles with images for better visual showcase
    queryset = Article.objects.filter(
        is_top_headline=True,
        analyzer_status='completed',
        publication__regions__code='us',  # Only US publications
        image_url__isnull=False,  # Only articles with images
        image_url__gt=''  # Exclude empty image URLs
    ).select_related('language', 'publication').prefetch_related('topics').distinct()
    
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
    
    # Sort by published date (newest first) and limit to latest 20 articles
    queryset = queryset.order_by('-published_at')[:20]
    
    # Convert to list for pagination (since we're limiting to 20 total)
    all_articles = list(queryset)
    
    # Manual pagination for the limited set
    start_index = (page - 1) * page_size
    end_index = start_index + page_size
    page_articles = all_articles[start_index:end_index]
    
    # Calculate pagination metadata
    total_items = len(all_articles)
    total_pages = (total_items + page_size - 1) // page_size  # Ceiling division
    has_next = end_index < total_items
    has_previous = page > 1
    
    # Prepare the response
    articles_data = []
    for article in page_articles:
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
            'description': _strip_html(article.description or ''),
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
            'totalPages': total_pages,
            'totalItems': total_items,
            'hasNext': has_next,
            'hasPrevious': has_previous,
        }
    }
    
    return create_success_response(
        response_data,
        message=f"Retrieved {len(articles_data)} latest analyzed US headlines"
    )

@api_view(['GET'], authenticate=False)
def article_detail(request, public_id):
    """
    Get details for a specific article
    """
    try:
        # Try to parse the public_id as UUID
        article_uuid = uuid.UUID(public_id)
    except ValueError:
        return create_error_response(
            "Invalid article ID",
            status=400,
            error_code="INVALID_ARTICLE_ID",
            details={"public_id": public_id}
        )
    
    try:
        # Get the article by public_id
        article = Article.objects.select_related(
            'language', 'publication'
        ).prefetch_related(
            'topics'
        ).get(public_id=article_uuid)
    except Article.DoesNotExist:
        return create_error_response(
            "Article not found",
            status=404,
            error_code="ARTICLE_NOT_FOUND",
            details={"public_id": public_id}
        )
    
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
        'description': _strip_html(article.description or ''),
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
    
    return create_success_response(
        article_data,
        message=f"Retrieved article details for {article.title[:50]}..."
    )

@api_view(['POST'], authenticate=True)
def generate_article_summary(request, public_id):
    """
    Generate or refresh the summary for a specific article.
    POST /articles/<public_id>/generate-summary/
    """
    
    # Initialize variables to prevent scope issues
    force_regenerate = False

    try:
        article_uuid = uuid.UUID(public_id)
    except ValueError:
        return create_error_response(
            "Invalid article ID",
            status=400,
            error_code="INVALID_ARTICLE_ID",
            details={"public_id": public_id}
        )

    try:
        article = Article.objects.get(public_id=article_uuid)
    except Article.DoesNotExist:
        return create_error_response(
            "Article not found",
            status=404,
            error_code="ARTICLE_NOT_FOUND",
            details={"public_id": public_id}
        )

    # Parse request body for options
    body, parse_error = parse_request_body(request)
    if parse_error:
        return parse_error
    
    # Get force_regenerate option from request body
    force_regenerate = body.get('forceRegenerate', False)

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
        return create_error_response(
            "Article cannot be summarized",
            status=422,
            error_code="ARTICLE_NOT_READY",
            details={
                "reason": "Article is still being processed or has insufficient content",
            "fetchStatus": article.fetch_status,
            "processStatus": article.process_status,
                "hasContent": bool(article.content and len(article.content) > 200),
                "isStillProcessing": isStillProcessing,
                "isProcessingFailed": isProcessingFailed
            }
        )

    # Check if already being processed
    if article.summarization_status == SummarizationStatus.PROCESSING:
        return create_error_response(
            "Summary generation already in progress",
            status=409,
            error_code="SUMMARY_IN_PROGRESS",
            details={
            "status": "processing",
                "message": "Please wait for the current summarization to complete",
                "article_id": public_id
            }
        )

    # Check if already completed and not forcing regeneration
    if (article.summarization_status == SummarizationStatus.COMPLETED and 
        hasattr(article, 'structured_summary') and 
        not force_regenerate):
        
        summary = article.structured_summary
        return create_success_response(
            {
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
                },
                "article_id": public_id
            },
            message="Summary already exists"
        )

    # Import and use the summarization service
    try:
        from apps.content.summariser.services import get_summarization_service
        from apps.content.summariser.tasks import summarize_article_pipeline
        
        # Check if we should process synchronously or asynchronously
        process_async = body.get('async', True)  # Default to async
        
        if process_async:
            # Queue the summarization task
            task = summarize_article_pipeline.delay(article.id, force_regenerate=force_regenerate)
            
            return create_success_response(
                {
                "status": "processing",
                "taskId": task.id,
                "estimatedTimeSeconds": 30,  # Rough estimate
                    "pollUrl": f"/api/articles/{public_id}/summary-status/",
                    "article_id": public_id
                },
                message="Summary generation started"
            )
        else:
            # Process synchronously (for immediate feedback)
            service = get_summarization_service()
            result = service.summarize_article(article, force_regenerate=force_regenerate)
            
            if result.success:
                return create_success_response(
                    {
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
                        },
                        "article_id": public_id
                    },
                    message="Summary generated successfully"
                )
            else:
                return create_error_response(
                    "Summary generation failed",
                    status=500,
                    error_code="SUMMARIZATION_FAILED",
                    details={
                        "error_message": result.error_message,
                    "failedStage": result.failed_stage,
                        "canRetry": result.failed_stage in ['rbc_compression', 'skeleton_summary'],
                        "article_id": public_id
                }
                )
                
    except ImportError as e:
        logger.error(f"Summarization service not available: {e}")
        return create_error_response(
            "Summarization service unavailable",
            status=503,
            error_code="SERVICE_UNAVAILABLE",
            details={
                "reason": "The summarization service is not properly configured",
                "service": "summarization",
                "article_id": public_id
        }
        )
    except Exception as e:
        logger.error(f"Unexpected error during summarization: {e}")
        return create_error_response(
            "Internal server error",
            status=500,
            error_code="INTERNAL_ERROR",
            details={
                "reason": "An unexpected error occurred during summary generation",
                "error_type": type(e).__name__,
                "article_id": public_id
            }
        )

@api_view(['GET'], authenticate=False)
def article_summary_status(request, public_id):
    """
    Check the status of summary generation for an article.
    GET /articles/<public_id>/summary-status/
    """
    try:
        article_uuid = uuid.UUID(public_id)
    except ValueError:
        return create_error_response(
            "Invalid article ID",
            status=400,
            error_code="INVALID_ARTICLE_ID",
            details={"public_id": public_id}
        )

    try:
        article = Article.objects.get(public_id=article_uuid)
    except Article.DoesNotExist:
        return create_error_response(
            "Article not found",
            status=404,
            error_code="ARTICLE_NOT_FOUND",
            details={"public_id": public_id}
        )

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
        "errorMessage": article.summarization_error_message if article.summarization_error_message else None,
        "article_id": public_id
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
    
    return create_success_response(
        response_data,
        message=f"Summary status: {current_status}"
    )
