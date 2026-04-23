"""
Celery Tasks for Content Analysis.

Background tasks for the 8-stage analysis pipeline following
established patterns from content/summariser/tasks.py
"""
import logging
from typing import List, Dict, Any
from celery import shared_task, chain, group
from django.db import transaction
from django.utils import timezone
from decimal import Decimal

from apps.articles.models import Article, AnalyzerStatus
from .services import AnalyzerService
from .models import AnalyzerRequest

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=300, soft_time_limit=600, time_limit=900)
def analyze_article_pipeline(self, article_id: int, force_regenerate: bool = False):
    """
    Main analysis pipeline task.
    
    Orchestrates the complete 8-stage analysis process for a single article.
    Follows established error handling patterns from summariser/tasks.py
    
    Args:
        article_id: ID of article to analyze
        force_regenerate: Whether to regenerate existing analysis
    """
    try:
        # Get article
        try:
            article = Article.objects.get(id=article_id)
        except Article.DoesNotExist:
            logger.error(f"Article {article_id} not found for analysis")
            return {'success': False, 'error': 'Article not found'}
        
        logger.info(f"Starting analysis pipeline for article {article_id}")
        
        # Get analyzer service
        service = AnalyzerService()
        
        # Execute analysis
        result = service.analyze_article(article, force=force_regenerate)
        
        if result['success']:
            logger.info(f"Analysis pipeline completed for article {article_id}")
            return {
                'success': True,
                'article_id': article_id,
                'cost_usd': float(result.get('cost_usd', 0)),
                'duration_ms': result.get('duration_ms', 0),
                'stages_completed': result.get('stages_completed', [])
            }
        else:
            error_msg = result.get('error', result.get('reason', 'Unknown error'))
            logger.error(f"Analysis pipeline failed for article {article_id}: {error_msg}")

            # Retry on certain failures
            failed_stage = result.get('failed_stage', '')
            if failed_stage in ['linguistic_processing', 'entity_processing'] and self.request.retries < self.max_retries:
                logger.info(f"Retrying analysis for article {article_id} (attempt {self.request.retries + 1})")
                raise self.retry(countdown=300)  # Retry after 5 minutes

            return {
                'success': False,
                'article_id': article_id,
                'error': error_msg,
                'failed_stage': failed_stage
            }
    
    except Exception as e:
        logger.error(f"Unexpected error in analysis pipeline for article {article_id}: {str(e)}")
        
        # Update article status on unexpected error
        try:
            article = Article.objects.get(id=article_id)
            article.analyzer_status = AnalyzerStatus.FAILED
            article.analyzer_error_message = f"Task error: {str(e)}"
            article.save(update_fields=['analyzer_status', 'analyzer_error_message'])
        except:
            pass
        
        # Retry on unexpected errors
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying analysis for article {article_id} after unexpected error")
            raise self.retry(countdown=600)  # Retry after 10 minutes
        
        return {
            'success': False,
            'article_id': article_id,
            'error': f"Task error: {str(e)}",
            'failed_stage': 'task_execution'
        }


@shared_task
def batch_analyze_articles(article_ids: List[int], force_regenerate: bool = False):
    """
    Batch analysis task for multiple articles.
    
    Processes multiple articles in parallel for digest generation or bulk operations.
    
    Args:
        article_ids: List of article IDs to analyze
        force_regenerate: Whether to regenerate existing analysis
    """
    logger.info(f"Starting batch analysis for {len(article_ids)} articles")
    
    # Queue individual analysis tasks asynchronously
    queued_count = 0
    failed_to_queue = 0
    
    for article_id in article_ids:
        try:
            analyze_article_pipeline.delay(article_id, force_regenerate)
            queued_count += 1
        except Exception as e:
            logger.error(f"Failed to queue analysis for article {article_id}: {str(e)}")
            failed_to_queue += 1
    
    logger.info(f"Batch analysis queued: {queued_count} successful, {failed_to_queue} failed to queue")
    
    return {
        'success': True,
        'articles_processed': len(article_ids),
        'successful': queued_count,
        'failed': failed_to_queue,
        'total_cost_usd': 0,  # Will be calculated when individual tasks complete
        'message': f'Queued {queued_count} articles for analysis'
    }


@shared_task
def process_pending_analysis(limit: int = 20):
    """
    Process articles that need analysis.
    
    Finds articles that have been summarized but not analyzed yet
    and queues them for processing.
    
    Args:
        limit: Maximum number of articles to process in this batch
    """
    logger.info(f"Processing pending analysis (limit: {limit})")
    
    from django.db import models
    from apps.articles.models import SummarizationStatus
    
    # Find articles that need analysis
    # They should be summarized first (requirement for analyzer)
    pending_articles = Article.objects.filter(
        analyzer_status=AnalyzerStatus.PENDING,
        summarization_status=SummarizationStatus.COMPLETED  # Must be summarized first
    ).filter(
        # Has suitable content for analysis
        models.Q(clean_content__isnull=False, clean_content__regex=r'.{200,}') |
        models.Q(basic_content__isnull=False, basic_content__regex=r'.{200,}')
    ).filter(
        # Limit retry attempts
        analyzer_attempts__lt=3
    ).order_by(
        'published_at'  # Process older articles first
    )[:limit]
    
    if not pending_articles:
        logger.info("No pending articles found for analysis")
        return {'success': True, 'articles_queued': 0}
    
    # Queue analysis tasks
    queued_count = 0
    for article in pending_articles:
        try:
            # Queue the task
            analyze_article_pipeline.delay(article.id)
            queued_count += 1
            logger.debug(f"Queued analysis for article {article.id}")
            
        except Exception as e:
            logger.error(f"Failed to queue analysis for article {article.id}: {str(e)}")
    
    logger.info(f"Queued {queued_count} articles for analysis")
    
    return {
        'success': True,
        'articles_queued': queued_count,
        'articles_found': len(pending_articles)
    }


@shared_task
def retry_failed_analysis(max_retries: int = 3):
    """
    Retry articles that failed analysis.
    
    Finds articles with failed analysis status and retries them
    if they haven't exceeded the maximum retry count.
    
    Args:
        max_retries: Maximum number of retry attempts
    """
    logger.info(f"Retrying failed analysis (max_retries: {max_retries})")
    
    # Find failed articles that can be retried
    failed_articles = Article.objects.filter(
        analyzer_status=AnalyzerStatus.FAILED,
        analyzer_attempts__lt=max_retries
    ).order_by('last_analyzer_attempt')[:20]  # Limit to 20 retries
    
    if not failed_articles:
        logger.info("No failed articles found for retry")
        return {'success': True, 'articles_retried': 0}
    
    # Reset status and queue for retry
    retried_count = 0
    for article in failed_articles:
        try:
            # Reset status
            article.analyzer_status = AnalyzerStatus.PENDING
            article.analyzer_error_message = ""
            article.save(update_fields=['analyzer_status', 'analyzer_error_message'])
            
            # Queue the task
            analyze_article_pipeline.delay(article.id)
            retried_count += 1
            logger.debug(f"Retrying analysis for article {article.id}")
            
        except Exception as e:
            logger.error(f"Failed to retry analysis for article {article.id}: {str(e)}")
    
    logger.info(f"Retried {retried_count} failed analysis")
    
    return {
        'success': True,
        'articles_retried': retried_count,
        'articles_found': len(failed_articles)
    }


@shared_task
def cleanup_old_analyzer_requests(days_old: int = 30):
    """
    Clean up old analyzer requests.
    
    Removes completed or failed analyzer requests older than specified days
    to prevent database bloat.
    
    Args:
        days_old: Number of days after which to remove old requests
    """
    logger.info(f"Cleaning up analyzer requests older than {days_old} days")
    
    # Calculate cutoff date
    cutoff_date = timezone.now() - timezone.timedelta(days=days_old)
    
    # Delete old completed and failed requests
    deleted_count, _ = AnalyzerRequest.objects.filter(
        status__in=['completed', 'failed'],
        updated_at__lt=cutoff_date
    ).delete()
    
    logger.info(f"Cleaned up {deleted_count} old analyzer requests")
    
    return {
        'success': True,
        'requests_deleted': deleted_count,
        'cutoff_date': cutoff_date.isoformat()
    }


@shared_task
def analyzer_health_check():
    """
    Health check task for analyzer system.
    
    Monitors the analysis pipeline health and reports on:
    - Pending articles count
    - Failed articles count  
    - Recent processing performance
    - AI provider status
    """
    logger.info("Running analyzer health check")
    
    try:
        # Count pending articles
        pending_count = Article.objects.filter(
            analyzer_status=AnalyzerStatus.PENDING
        ).count()
        
        # Count failed articles
        failed_count = Article.objects.filter(
            analyzer_status=AnalyzerStatus.FAILED
        ).count()
        
        # Count completed articles (last 24 hours)
        yesterday = timezone.now() - timezone.timedelta(hours=24)
        completed_24h = Article.objects.filter(
            analyzer_status=AnalyzerStatus.COMPLETED,
            analyzed_at__gte=yesterday
        ).count()
        
        # Check in-progress requests
        in_progress_count = AnalyzerRequest.objects.filter(
            status__in=['linguistic_processing', 'entity_processing', 'event_processing', 'topic_processing', 'region_processing']
        ).count()
        
        # Calculate average cost (last 100 completed)
        recent_analysis = Article.objects.filter(
            analyzer_status=AnalyzerStatus.COMPLETED,
            analyzer_cost_usd__isnull=False
        ).order_by('-analyzed_at')[:100]
        
        avg_cost = 0.0
        if recent_analysis:
            total_cost = sum(float(article.analyzer_cost_usd or 0) for article in recent_analysis)
            avg_cost = total_cost / len(recent_analysis)
        
        # Check cost efficiency vs target (should be ≤ $0.00019)
        cost_efficiency = 'excellent' if avg_cost <= 0.00019 else 'acceptable' if avg_cost <= 0.0004 else 'high'
        
        health_status = {
            'success': True,
            'timestamp': timezone.now().isoformat(),
            'pending_articles': pending_count,
            'failed_articles': failed_count,
            'completed_24h': completed_24h,
            'in_progress': in_progress_count,
            'avg_cost_per_article': round(avg_cost, 6),
            'cost_efficiency': cost_efficiency,
            'target_cost': 0.00019,
            'health': 'good' if failed_count < pending_count * 0.1 else 'degraded'
        }
        
        logger.info(f"Health check completed: {health_status}")
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'timestamp': timezone.now().isoformat(),
            'health': 'critical'
        }


@shared_task
def analyze_articles_by_content_stage(content_stage: str, limit: int = 50):
    """
    Queue analysis for articles from specific content processing stage.
    
    Args:
        content_stage: 'after_summarizer' (recommended), 'after_quality', 'after_processor'
        limit: Maximum number of articles to queue
    """
    from django.db import models
    from apps.articles.models import SummarizationStatus
    
    logger.info(f"Queuing analysis for articles from {content_stage} (limit: {limit})")
    
    base_query = Article.objects.filter(
        analyzer_status=AnalyzerStatus.PENDING
    ).filter(
        # Has suitable content for analysis
        models.Q(clean_content__isnull=False, clean_content__regex=r'.{200,}') |
        models.Q(basic_content__isnull=False, basic_content__regex=r'.{200,}')
    )
    
    if content_stage == 'after_summarizer':
        # Recommended: Articles that have been summarized (optimal for analysis)
        articles = base_query.filter(
            summarization_status=SummarizationStatus.COMPLETED
        )[:limit]
    elif content_stage == 'after_quality':
        # Articles that have been quality assessed
        articles = base_query.filter(
            content_quality_metrics__isnull=False
        )[:limit]
    elif content_stage == 'after_processor':
        # Articles with clean_content from processor
        articles = base_query.filter(
            clean_content__isnull=False,
            clean_content__regex=r'.{200,}'
        )[:limit]
    else:
        logger.error(f"Invalid content stage: {content_stage}")
        return {'success': False, 'error': 'Invalid content stage'}
    
    # Queue tasks
    queued_count = 0
    for article in articles:
        try:
            analyze_article_pipeline.delay(article.id)
            queued_count += 1
        except Exception as e:
            logger.error(f"Failed to queue analysis for article {article.id}: {str(e)}")
    
    logger.info(f"Queued {queued_count} articles from {content_stage} for analysis")
    
    return {
        'success': True,
        'articles_queued': queued_count,
        'articles_found': len(articles),
        'content_stage': content_stage
    }


@shared_task 
def generate_daily_digest_analysis():
    """
    Prepare analysis data for daily digest generation.
    
    Analyzes recent articles to identify:
    - Top entities and events
    - Regional/topic distributions
    - Trending keywords
    - Content patterns
    """
    logger.info("Starting daily digest analysis")
    
    try:
        from django.db.models import Count, Q
        from datetime import timedelta
        
        # Analyze articles from last 24 hours
        yesterday = timezone.now() - timedelta(hours=24)
        
        recent_articles = Article.objects.filter(
            analyzer_status=AnalyzerStatus.COMPLETED,
            analyzed_at__gte=yesterday
        )
        
        if not recent_articles.exists():
            logger.info("No analyzed articles from last 24 hours")
            return {'success': True, 'articles_analyzed': 0}
        
        # Top entities from recent articles
        from .models import ArticleEntity, Entity
        top_entities = Entity.objects.filter(
            articleentity__article__in=recent_articles
        ).annotate(
            mention_count=Count('articleentity__article')
        ).order_by('-mention_count')[:20]
        
        # Top events from recent articles
        from .models import ArticleEvent, Event
        top_events = Event.objects.filter(
            articleevent__article__in=recent_articles
        ).annotate(
            article_count=Count('articleevent__article')
        ).order_by('-article_count')[:10]
        
        # Regional distribution
        from apps.feeds.models import Region
        regional_stats = recent_articles.filter(
            primary_region__isnull=False
        ).values(
            'primary_region__code', 'primary_region__name'
        ).annotate(
            article_count=Count('id')
        ).order_by('-article_count')
        
        # Topic distribution
        from apps.feeds.models import Topic
        topic_stats = recent_articles.filter(
            primary_topic__isnull=False
        ).values(
            'primary_topic__slug', 'primary_topic__name'
        ).annotate(
            article_count=Count('id')
        ).order_by('-article_count')
        
        digest_data = {
            'success': True,
            'timestamp': timezone.now().isoformat(),
            'analysis_period': '24h',
            'articles_analyzed': recent_articles.count(),
            'top_entities': [
                {
                    'name': entity.display_name,
                    'type': entity.entity_type,
                    'mentions': entity.mention_count
                }
                for entity in top_entities
            ],
            'top_events': [
                {
                    'title': event.title,
                    'articles': event.article_count,
                    'first_seen': event.first_seen_at.isoformat() if event.first_seen_at else None
                }
                for event in top_events
            ],
            'regional_distribution': list(regional_stats),
            'topic_distribution': list(topic_stats)
        }
        
        logger.info(f"Daily digest analysis completed: {recent_articles.count()} articles")
        return digest_data
        
    except Exception as e:
        logger.error(f"Daily digest analysis failed: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }


# Utility functions for analysis pipeline coordination

def queue_analysis_after_summarization(article_id: int):
    """
    Queue analysis for an article after successful summarization.
    
    This is called by the summarization pipeline to automatically
    trigger analysis once summarization is complete.
    
    Args:
        article_id: ID of the summarized article
    """
    try:
        article = Article.objects.get(id=article_id)
        
        # Check if article is eligible for analysis
        if not article.needs_analysis:
            logger.debug(f"Article {article_id} does not need analysis")
            return
        
        # Queue analysis task
        analyze_article_pipeline.delay(article_id)
        logger.info(f"Queued analysis for article {article_id} after summarization")
        
    except Article.DoesNotExist:
        logger.error(f"Article {article_id} not found for post-summarization analysis")
    except Exception as e:
        logger.error(f"Failed to queue analysis for article {article_id}: {str(e)}")


@shared_task
def cleanup_stuck_analyzer_articles() -> Dict[str, Any]:
    """
    Clean up articles stuck in PROCESSING status for analysis.
    
    Resets articles that have been stuck in PROCESSING status for more than 2 hours
    back to PENDING status, including those with null timestamps.
    """
    
    try:
        # Reset articles stuck in PROCESSING status for more than 2 hours
        stuck_threshold = timezone.now() - timezone.timedelta(hours=2)
        
        from django.db.models import Q
        from apps.articles.models import SummarizationStatus
        
        # Include both articles with old timestamps AND articles with null timestamps (stuck without proper tracking)
        stuck_articles = Article.objects.filter(
            analyzer_status=AnalyzerStatus.PROCESSING
        ).filter(
            Q(last_analyzer_attempt__lt=stuck_threshold) |
            Q(last_analyzer_attempt__isnull=True)
        )
        
        stuck_count = stuck_articles.count()
        
        if stuck_count > 0:
            stuck_articles.update(
                analyzer_status=AnalyzerStatus.PENDING,
                analyzer_error_message='Reset from stuck PROCESSING status'
            )
            
            logger.info(f"Reset {stuck_count} articles stuck in analyzer PROCESSING status")
        
        # Clean up very old failed analysis attempts (older than 7 days)
        old_threshold = timezone.now() - timezone.timedelta(days=7)
        
        old_failed = Article.objects.filter(
            analyzer_status=AnalyzerStatus.FAILED,
            last_analyzer_attempt__lt=old_threshold,
            analyzer_attempts__gte=3
        )
        
        old_count = old_failed.count()
        
        if old_count > 0:
            # Don't reset these, just log for monitoring
            logger.info(f"Found {old_count} articles with old failed analyzer attempts")
        
        # Calculate analyzer queue health
        pending_count = Article.objects.filter(
            analyzer_status=AnalyzerStatus.PENDING,
            summarization_status=SummarizationStatus.COMPLETED  # Must have completed summarization first
        ).count()
        
        processing_count = Article.objects.filter(
            analyzer_status=AnalyzerStatus.PROCESSING
        ).count()
        
        return {
            'stuck_articles_reset': stuck_count,
            'old_failed_articles': old_count,
            'pending_articles': pending_count,
            'processing_articles': processing_count,
            'cleanup_completed': True
        }
        
    except Exception as e:
        logger.exception(f"Analyzer cleanup failed: {str(e)}")
        return {
            'stuck_articles_reset': 0,
            'old_failed_articles': 0,
            'cleanup_completed': False,
            'error_message': str(e)
        }


def get_analysis_pipeline_status():
    """
    Get current status of the analysis pipeline.
    
    Returns summary of pending, processing, and completed analysis tasks.
    """
    try:
        status = {
            'pending': Article.objects.filter(analyzer_status=AnalyzerStatus.PENDING).count(),
            'processing': Article.objects.filter(analyzer_status=AnalyzerStatus.PROCESSING).count(),
            'completed': Article.objects.filter(analyzer_status=AnalyzerStatus.COMPLETED).count(),
            'failed': Article.objects.filter(analyzer_status=AnalyzerStatus.FAILED).count(),
            'in_progress_requests': AnalyzerRequest.objects.filter(
                status__in=['linguistic_processing', 'entity_processing', 'event_processing', 'topic_processing', 'region_processing']
            ).count()
        }
        
        status['total'] = sum(status.values()) - status['in_progress_requests']  # Don't double count
        return status
        
    except Exception as e:
        logger.error(f"Failed to get pipeline status: {str(e)}")
        return {'error': str(e)} 