"""
Celery Tasks for Content Summarization.

Background tasks for the 4-stage summarization pipeline following
established patterns from other content processing services.
"""
import logging
from typing import List, Dict, Any
from celery import shared_task, chain, group
from django.db import transaction
from django.utils import timezone

from apps.articles.models import Article, SummarizationStatus
from .services import get_summarization_service
from .models import SummarizationRequest

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def summarize_article_pipeline(self, article_id: int, force_regenerate: bool = False):
    """
    Main summarization pipeline task.
    
    Orchestrates the complete 4-stage summarization process for a single article.
    Follows established error handling patterns from processor/tasks.py
    
    Args:
        article_id: ID of article to summarize
        force_regenerate: Whether to regenerate existing summaries
    """
    try:
        # Get article
        try:
            article = Article.objects.get(id=article_id)
        except Article.DoesNotExist:
            logger.error(f"Article {article_id} not found for summarization")
            return {'success': False, 'error': 'Article not found'}
        
        logger.info(f"Starting summarization pipeline for article {article_id}")
        
        # Get summarization service
        service = get_summarization_service()
        
        # Execute summarization
        result = service.summarize_article(article, force_regenerate=force_regenerate)
        
        if result.success:
            logger.info(f"Summarization pipeline completed for article {article_id}")
            return {
                'success': True,
                'article_id': article_id,
                'headline': result.headline,
                'abstract': result.abstract,
                'cost_usd': float(result.total_cost_usd),
                'duration_ms': result.total_duration_ms,
                'stages_completed': result.stages_completed,
                'required_critic': result.required_critic,
                'was_repaired': result.was_repaired
            }
        else:
            logger.error(f"Summarization pipeline failed for article {article_id}: {result.error_message}")
            
            # Retry on certain failures
            if result.failed_stage in ['rbc_compression', 'skeleton_summary'] and self.request.retries < self.max_retries:
                logger.info(f"Retrying summarization for article {article_id} (attempt {self.request.retries + 1})")
                raise self.retry(countdown=300)  # Retry after 5 minutes
            
            return {
                'success': False,
                'article_id': article_id,
                'error': result.error_message,
                'failed_stage': result.failed_stage
            }
    
    except Exception as e:
        logger.error(f"Unexpected error in summarization pipeline for article {article_id}: {str(e)}")
        
        # Update article status on unexpected error
        try:
            article = Article.objects.get(id=article_id)
            article.summarization_status = SummarizationStatus.FAILED
            article.summarization_error_message = f"Task error: {str(e)}"
            article.save(update_fields=['summarization_status', 'summarization_error_message'])
        except:
            pass
        
        # Retry on unexpected errors
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying summarization for article {article_id} after unexpected error")
            raise self.retry(countdown=600)  # Retry after 10 minutes
        
        return {
            'success': False,
            'article_id': article_id,
            'error': f"Task error: {str(e)}",
            'failed_stage': 'task_execution'
        }


@shared_task
def batch_summarize_articles(article_ids: List[int], force_regenerate: bool = False):
    """
    Batch summarization task for multiple articles.
    
    Processes multiple articles in parallel for digest generation or bulk operations.
    
    Args:
        article_ids: List of article IDs to summarize
        force_regenerate: Whether to regenerate existing summaries
    """
    logger.info(f"Starting batch summarization for {len(article_ids)} articles")
    
    # Create parallel tasks for each article
    job = group([
        summarize_article_pipeline.s(article_id, force_regenerate) 
        for article_id in article_ids
    ])
    
    # Execute and collect results
    result = job.apply_async()
    results = result.get()
    
    # Aggregate results
    successful = sum(1 for r in results if r.get('success', False))
    failed = len(results) - successful
    total_cost = sum(r.get('cost_usd', 0) for r in results if r.get('success', False))
    
    logger.info(f"Batch summarization completed: {successful} successful, {failed} failed, total cost: ${total_cost:.4f}")
    
    return {
        'success': True,
        'articles_processed': len(article_ids),
        'successful': successful,
        'failed': failed,
        'total_cost_usd': total_cost,
        'results': results
    }


@shared_task
def process_pending_summarizations(limit: int = 20):
    """
    Process articles that need summarization.
    
    Finds articles with suitable content that haven't been summarized yet
    and queues them for processing.
    
    Args:
        limit: Maximum number of articles to process in this batch
    """
    logger.info(f"Processing pending summarizations (limit: {limit})")
    
    from django.db import models
    
    # Find articles that need summarization
    pending_articles = Article.objects.filter(
        summarization_status=SummarizationStatus.PENDING
    ).filter(
        # Has suitable content for summarization
        models.Q(clean_content__isnull=False, clean_content__regex=r'.{200,}') |
        models.Q(basic_content__isnull=False, basic_content__regex=r'.{200,}')
    ).filter(
        # Limit retry attempts
        summarization_attempts__lt=3
    ).order_by(
        'published_at'  # Process older articles first
    )[:limit]
    
    if not pending_articles:
        logger.info("No pending articles found for summarization")
        return {'success': True, 'articles_queued': 0}
    
    # Queue summarization tasks
    queued_count = 0
    for article in pending_articles:
        try:
            # Queue the task
            summarize_article_pipeline.delay(article.id)
            queued_count += 1
            logger.debug(f"Queued summarization for article {article.id}")
            
        except Exception as e:
            logger.error(f"Failed to queue summarization for article {article.id}: {str(e)}")
    
    logger.info(f"Queued {queued_count} articles for summarization")
    
    return {
        'success': True,
        'articles_queued': queued_count,
        'articles_found': len(pending_articles)
    }


@shared_task
def retry_failed_summarizations(max_retries: int = 3):
    """
    Retry articles that failed summarization.
    
    Finds articles with failed summarization status and retries them
    if they haven't exceeded the maximum retry count.
    
    Args:
        max_retries: Maximum number of retry attempts
    """
    logger.info(f"Retrying failed summarizations (max_retries: {max_retries})")
    
    # Find failed articles that can be retried
    failed_articles = Article.objects.filter(
        summarization_status=SummarizationStatus.FAILED,
        summarization_attempts__lt=max_retries
    ).order_by('last_summarization_attempt')[:20]  # Limit to 20 retries
    
    if not failed_articles:
        logger.info("No failed articles found for retry")
        return {'success': True, 'articles_retried': 0}
    
    # Reset status and queue for retry
    retried_count = 0
    for article in failed_articles:
        try:
            # Reset status
            article.summarization_status = SummarizationStatus.PENDING
            article.summarization_error_message = ""
            article.save(update_fields=['summarization_status', 'summarization_error_message'])
            
            # Queue the task
            summarize_article_pipeline.delay(article.id)
            retried_count += 1
            logger.debug(f"Retrying summarization for article {article.id}")
            
        except Exception as e:
            logger.error(f"Failed to retry summarization for article {article.id}: {str(e)}")
    
    logger.info(f"Retried {retried_count} failed summarizations")
    
    return {
        'success': True,
        'articles_retried': retried_count,
        'articles_found': len(failed_articles)
    }


@shared_task
def cleanup_old_summarization_requests(days_old: int = 30):
    """
    Clean up old summarization requests.
    
    Removes completed or failed summarization requests older than specified days
    to prevent database bloat.
    
    Args:
        days_old: Number of days after which to remove old requests
    """
    logger.info(f"Cleaning up summarization requests older than {days_old} days")
    
    # Calculate cutoff date
    cutoff_date = timezone.now() - timezone.timedelta(days=days_old)
    
    # Delete old completed and failed requests
    deleted_count, _ = SummarizationRequest.objects.filter(
        status__in=['completed', 'failed'],
        updated_at__lt=cutoff_date
    ).delete()
    
    logger.info(f"Cleaned up {deleted_count} old summarization requests")
    
    return {
        'success': True,
        'requests_deleted': deleted_count,
        'cutoff_date': cutoff_date.isoformat()
    }


@shared_task
def summarization_health_check():
    """
    Health check task for summarization system.
    
    Monitors the summarization pipeline health and reports on:
    - Pending articles count
    - Failed articles count  
    - Recent processing performance
    - AI provider status
    """
    logger.info("Running summarization health check")
    
    try:
        # Count pending articles
        pending_count = Article.objects.filter(
            summarization_status=SummarizationStatus.PENDING
        ).count()
        
        # Count failed articles
        failed_count = Article.objects.filter(
            summarization_status=SummarizationStatus.FAILED
        ).count()
        
        # Count completed articles (last 24 hours)
        yesterday = timezone.now() - timezone.timedelta(hours=24)
        completed_24h = Article.objects.filter(
            summarization_status=SummarizationStatus.COMPLETED,
            summarized_at__gte=yesterday
        ).count()
        
        # Check in-progress requests
        in_progress_count = SummarizationRequest.objects.filter(
            status__in=['rbc_processing', 'summary_processing', 'critic_processing', 'repair_processing']
        ).count()
        
        # Calculate average cost (last 100 completed)
        recent_summaries = Article.objects.filter(
            summarization_status=SummarizationStatus.COMPLETED,
            summarization_cost_usd__isnull=False
        ).order_by('-summarized_at')[:100]
        
        avg_cost = 0.0
        if recent_summaries:
            total_cost = sum(float(article.summarization_cost_usd or 0) for article in recent_summaries)
            avg_cost = total_cost / len(recent_summaries)
        
        health_status = {
            'success': True,
            'timestamp': timezone.now().isoformat(),
            'pending_articles': pending_count,
            'failed_articles': failed_count,
            'completed_24h': completed_24h,
            'in_progress': in_progress_count,
            'avg_cost_per_article': round(avg_cost, 6),
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


# Utility function to queue summarization for specific content sources
def queue_summarization_by_content_source(content_source: str, limit: int = 50):
    """
    Queue summarization for articles from specific content processing stage.
    
    Args:
        content_source: 'after_fetcher', 'after_processor', 'after_quality'
        limit: Maximum number of articles to queue
    """
    from django.db import models
    
    if content_source == 'after_fetcher':
        # Articles with basic_content but not processed
        articles = Article.objects.filter(
            basic_content__isnull=False,
            basic_content__regex=r'.{200,}',
            summarization_status=SummarizationStatus.PENDING
        )[:limit]
    elif content_source == 'after_processor':
        # Articles with clean_content
        articles = Article.objects.filter(
            clean_content__isnull=False,
            clean_content__regex=r'.{200,}',
            summarization_status=SummarizationStatus.PENDING
        )[:limit]
    elif content_source == 'after_quality':
        # Articles that have been quality assessed
        articles = Article.objects.filter(
            clean_content__isnull=False,
            clean_content__regex=r'.{200,}',
            content_quality_metrics__isnull=False,
            summarization_status=SummarizationStatus.PENDING
        )[:limit]
    else:
        logger.error(f"Invalid content source: {content_source}")
        return
    
    # Queue tasks
    for article in articles:
        summarize_article_pipeline.delay(article.id)
    
    logger.info(f"Queued {len(articles)} articles from {content_source} for summarization") 