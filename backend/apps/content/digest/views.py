"""
API views for digest management and access.

Provides endpoints for:
- Retrieving user's digests (latest, by date, list)
- Generating digests on-demand
- Accessing digest content and metadata
- Admin digest management
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any

from django.http import JsonResponse, Http404
from django.contrib.auth.models import User
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator

from apps.core.api_utils import api_view, create_response, create_error_response
from .models import Digest, DigestTopic, DigestStory
from .services import DigestService
from .tasks import generate_user_digest

logger = logging.getLogger(__name__)


@api_view(['GET'])
def get_latest_digest(request):
    """
    Get the user's latest digest.
    
    Returns the most recent digest for the authenticated user.
    If no digest exists, returns appropriate message.
    
    Response:
    {
        "digest": DigestData or null,
        "message": "string (if no digest)",
        "success": true
    }
    """
    user = request.user
    
    # Get latest digest
    latest_digest = Digest.objects.filter(
        user=user,
        generation_status='completed'
    ).order_by('-date', '-created_at').first()
    
    if not latest_digest:
        return create_response({
            'digest': None,
            'message': 'No digests available. Follow some topics to start receiving daily briefs.',
            'success': True
        })
    
    # Serialize digest data
    digest_data = _serialize_digest(latest_digest)
    
    return create_response({
        'digest': digest_data,
        'success': True
    })


@api_view(['GET'])
def get_digest_by_date(request, date_str):
    """
    Get digest for a specific date.
    
    Args:
        date_str: Date in YYYY-MM-DD format
        
    Response:
    {
        "digest": DigestData or null,
        "date": "YYYY-MM-DD",
        "success": true
    }
    """
    user = request.user
    
    # Parse and validate date
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return create_error_response('Invalid date format. Use YYYY-MM-DD.', status=400)
    
    # Get digest for date
    digest = Digest.objects.filter(
        user=user,
        date=target_date
    ).first()
    
    if not digest:
        return create_response({
            'digest': None,
            'date': date_str,
            'message': f'No digest found for {date_str}',
            'success': True
        })
    
    # Serialize digest data
    digest_data = _serialize_digest(digest)
    
    return create_response({
        'digest': digest_data,
        'date': date_str,
        'success': True
    })


@api_view(['GET'])
def list_user_digests(request):
    """
    List user's digests with pagination.
    
    Query parameters:
        - page: Page number (default: 1)
        - page_size: Items per page (default: 10, max: 50)
        - status: Filter by generation status (optional)
        
    Response:
    {
        "digests": [DigestSummary, ...],
        "pagination": PaginationData,
        "success": true
    }
    """
    user = request.user
    
    # Get query parameters
    page = int(request.GET.get('page', 1))
    page_size = min(int(request.GET.get('page_size', 10)), 50)
    status_filter = request.GET.get('status')
    
    # Build query
    queryset = Digest.objects.filter(user=user).order_by('-date', '-created_at')
    
    if status_filter:
        queryset = queryset.filter(generation_status=status_filter)
    
    # Paginate
    paginator = Paginator(queryset, page_size)
    
    if page > paginator.num_pages:
        return create_error_response('Page not found', status=404)
    
    page_obj = paginator.get_page(page)
    
    # Serialize digest summaries
    digest_summaries = [
        _serialize_digest_summary(digest) 
        for digest in page_obj.object_list
    ]
    
    return create_response({
        'digests': digest_summaries,
        'pagination': {
            'page': page,
            'page_size': page_size,
            'total_pages': paginator.num_pages,
            'total_count': paginator.count,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous()
        },
        'success': True
    })


@api_view(['POST'])
def generate_digest_on_demand(request):
    """
    Generate a digest on-demand for the user.
    
    Request body:
    {
        "date": "YYYY-MM-DD" (optional, defaults to today),
        "force_regenerate": boolean (optional, defaults to false)
    }
    
    Response:
    {
        "digest_id": "uuid",
        "status": "generating|completed|failed",
        "message": "string",
        "success": true
    }
    """
    user = request.user
    
    # Parse request data
    try:
        import json
        data = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        return create_error_response('Invalid JSON in request body', status=400)
    
    target_date = data.get('date')
    force_regenerate = data.get('force_regenerate', False)
    
    # Validate date if provided
    if target_date:
        try:
            datetime.strptime(target_date, '%Y-%m-%d')
        except ValueError:
            return create_error_response('Invalid date format. Use YYYY-MM-DD.', status=400)
    
    # Check if user has followed topics
    if not user.preferred_topics.exists():
        return create_error_response('You must follow at least one topic to generate a digest.', status=400)
    
    # Check for existing digest if not regenerating
    if target_date and not force_regenerate:
        existing_digest = Digest.objects.filter(
            user=user,
            date=datetime.strptime(target_date, '%Y-%m-%d').date()
        ).first()
        
        if existing_digest:
            return create_response({
                'digest_id': str(existing_digest.public_id),
                'status': existing_digest.generation_status.lower(),
                'message': 'Digest already exists for this date',
                'success': True
            })
    
    # Create digest record immediately for tracking
    from django.utils import timezone
    from .models import Digest
    import uuid
    
    # Determine target date
    if target_date:
        date_obj = datetime.strptime(target_date, '%Y-%m-%d').date()
    else:
        date_obj = timezone.now().date()
    
    # Create or get digest record in 'generating' state
    digest, created = Digest.objects.get_or_create(
        user=user,
        date=date_obj,
        defaults={
            'public_id': uuid.uuid4(),
            'title': f"Daily Digest for {date_obj.strftime('%B %d, %Y')}",
            'generation_status': 'processing',
        }
    )
    
    # If digest already exists and we're not forcing regeneration, return existing
    if not created and not force_regenerate:
        return create_response({
            'digest_id': str(digest.public_id),
            'status': digest.generation_status.lower(),
            'message': 'Digest already exists for this date',
            'success': True
        })
    
    # Update existing digest to generating state if regenerating
    if not created and force_regenerate:
        digest.generation_status = 'processing'
        digest.error_message = ''
        digest.save()
    
    # Queue digest generation task
    try:
        task_result = generate_user_digest.delay(
            user_id=user.id,
            target_date=target_date,
            force_regenerate=force_regenerate
        )
        
        return create_response({
            'digest_id': str(digest.public_id),
            'task_id': task_result.id,
            'status': 'processing',
            'message': 'Digest generation started. Check back in a few minutes.',
            'success': True
        })
        
    except Exception as e:
        logger.error(f"Failed to queue digest generation for user {user.id}: {e}")
        return create_error_response('Failed to start digest generation. Please try again.', status=500)


@api_view(['GET'])
def get_digest_status(request, digest_id):
    """
    Get status of a digest by its public ID.
    
    Response:
    {
        "digest_id": "uuid",
        "status": "generating|completed|failed",
        "created_at": "ISO datetime",
        "updated_at": "ISO datetime",
        "error_message": "string (if failed)",
        "success": true
    }
    """
    user = request.user
    
    try:
        digest = Digest.objects.get(
            public_id=digest_id,
            user=user
        )
    except Digest.DoesNotExist:
        return create_error_response('Digest not found', status=404)
    
    return create_response({
        'digest_id': str(digest.public_id),
        'status': digest.generation_status.lower(),
        'created_at': digest.created_at.isoformat(),
        'updated_at': digest.updated_at.isoformat(),
        'error_message': digest.error_message,
        'metrics': {
            'topics_included': digest.topics_included,
            'events_included': digest.events_included,
            'articles_processed': digest.articles_processed,
            'reading_time_minutes': digest.reading_time_minutes,
            'generation_cost_usd': float(digest.generation_cost_usd),
            'generation_tokens_total': digest.tokens_input + digest.tokens_output
        } if digest.generation_status == 'completed' else None,
        'success': True
    })


@api_view(['GET'])
def get_digest_html(request, digest_id):
    """
    Get HTML content of a digest.
    
    Returns the formatted HTML content for display.
    
    Response:
    {
        "html_content": "string",
        "digest_id": "uuid",
        "success": true
    }
    """
    user = request.user
    
    try:
        digest = Digest.objects.get(
            public_id=digest_id,
            user=user,
            generation_status='completed'
        )
    except Digest.DoesNotExist:
        return create_error_response('Digest not found or not completed', status=404)
    
    return create_response({
        'html_content': digest.html_content,
        'digest_id': str(digest.public_id),
        'success': True
    })


# Helper functions for serialization


def _get_fallback_image_from_content_blocks(article) -> str:
    """
    Extract the first suitable image from article content blocks as fallback.
    
    Args:
        article: Article instance with content_blocks
        
    Returns:
        Image URL string or None if no suitable image found
    """
    if not article.content_blocks:
        return None
    
    # Look for image content blocks
    for block in article.content_blocks:
        if not isinstance(block, dict):
            continue
            
        block_type = block.get('type', '')
        metadata = block.get('metadata', {})
        
        # Check for img or figure blocks with valid src
        if block_type in ['img', 'image', 'figure']:
            image_src = metadata.get('src', '').strip()
            if image_src and image_src.startswith(('http://', 'https://')):
                # Additional validation: ensure it's not a tiny/icon image
                width = metadata.get('width')
                height = metadata.get('height')
                
                # Skip very small images (likely icons/logos)
                if width and height:
                    try:
                        w, h = int(width), int(height)
                        if w < 100 or h < 100:
                            continue
                    except (ValueError, TypeError):
                        pass
                
                # Check alt text for profile/author indicators (skip these)
                alt_text = metadata.get('alt', '').lower()
                author_indicators = ['headshot', 'profile', 'avatar', 'author', 'byline', 'contributor']
                if any(indicator in alt_text for indicator in author_indicators):
                    continue
                
                # This looks like a good content image
                return image_src
    
    return None


def _serialize_digest(digest: Digest) -> Dict[str, Any]:
    """Serialize complete digest data including topics and stories."""
    
    # Get topics with stories
    topics_data = []
    all_published_dates = []  # Collect all article published dates
    for digest_topic in digest.digest_topics.all().prefetch_related('stories__recommended_articles'):
        stories_data = []
        for story in digest_topic.stories.all():
            # Serialize recommended articles
            articles_data = []
            for article in story.recommended_articles.all():
                # Collect published dates for date range calculation
                if article.published_at:
                    all_published_dates.append(article.published_at)
                
                articles_data.append({
                    'id': str(article.public_id),
                    'title': article.title,
                    'url': article.url,
                    'imageUrl': article.image_url or _get_fallback_image_from_content_blocks(article),
                    'publication': article.publication.name if article.publication else None,
                    'publicationLogoUrl': article.publication.logo_url if article.publication else None,
                    'published_at': article.published_at.isoformat() if article.published_at else None,
                })
            
            stories_data.append({
                'id': str(story.id),
                'title': story.title,
                'abstract': story.enhanced_abstract or story.summary,  # Use enhanced_abstract with fallback
                'key_facts': story.key_facts or [],
                'perspectives': story.perspectives or [],
                'articles': articles_data,
                'article_count': story.article_count,
                'event_score': story.event_score,
                'event': {
                    'id': story.event.id if story.event else None,
                    'title': story.event.title if story.event else story.title,
                } if story.event else None
            })
        
        topics_data.append({
            'id': str(digest_topic.id),
            'title': digest_topic.topic.name,  # Use topic.name as title
            'abstract': digest_topic.topic_abstract,
            'score': 0,  # Field doesn't exist in model, using default
            'stories': stories_data
        })
    
    # Calculate article date range
    article_date_range = None
    if all_published_dates:
        all_published_dates.sort()
        min_date = all_published_dates[0]
        max_date = all_published_dates[-1]
        article_date_range = {
            'min_published_at': min_date.isoformat(),
            'max_published_at': max_date.isoformat(),
        }
    
    return {
        'id': str(digest.public_id),
        'title': digest.title,
        'headline': digest.headline,
        'date': digest.date.isoformat(),
        'introduction': digest.introduction,
        'conclusion': digest.conclusion,
        'topics': topics_data,
        'generation_status': digest.generation_status.upper(),
        'created_at': digest.created_at.isoformat(),
        'updated_at': digest.updated_at.isoformat(),
        'article_date_range': article_date_range,  # Add the new field
        'metrics': {
            'topics_included': digest.topics_included,
            'events_included': digest.events_included,
            'articles_processed': digest.articles_processed,
            'reading_time_minutes': digest.reading_time_minutes,
            'generation_cost_usd': float(digest.generation_cost_usd),
            'generation_tokens_total': digest.tokens_input + digest.tokens_output
        }
    }


def _serialize_digest_summary(digest: Digest) -> Dict[str, Any]:
    """Serialize digest summary for list views."""
    return {
        'id': str(digest.public_id),
        'title': digest.title,
        'headline': digest.headline,
        'date': digest.date.isoformat(),
        'introduction': digest.introduction[:200] + ('...' if len(digest.introduction) > 200 else ''),
        'generation_status': digest.generation_status,
        'created_at': digest.created_at.isoformat(),
        'topics_included': digest.topics_included,
        'events_included': digest.events_included,
        'articles_processed': digest.articles_processed,
        'reading_time_minutes': digest.reading_time_minutes,
        'generation_cost_usd': float(digest.generation_cost_usd)
    }
