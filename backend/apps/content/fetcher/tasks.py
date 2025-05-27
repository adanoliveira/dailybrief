import logging
from typing import List, Dict, Any
from celery import shared_task
from django.utils import timezone
from django.db import transaction

from apps.articles.models import Article, ContentStatus
from .services import ContentFetcher, fetch_article_content, batch_fetch_content
from .models import FetchAttempt

logger = logging.getLogger(__name__)


@shared_task(name="content.fetch_article_content", bind=True, max_retries=3)
def fetch_article_content_task(self, article_id: int) -> Dict[str, Any]:
    """
    Async task to fetch and process article content.
    
    Args:
        article_id (int): ID of the article to fetch content for
        
    Returns:
        Dict[str, Any]: Task result with success status and details
    """
    try:
        logger.info(f"Starting content fetch for article {article_id}")
        
        # Fetch content using the service
        result = fetch_article_content(article_id)
        
        if result.success:
            logger.info(f"Successfully fetched content for article {article_id}")
            return {
                'success': True,
                'article_id': article_id,
                'content_status': result.content_status,
                'message': result.message,
                'strategy_used': result.extraction_result.strategy_used if result.extraction_result else None
            }
        else:
            logger.warning(f"Failed to fetch content for article {article_id}: {result.message}")
            return {
                'success': False,
                'article_id': article_id,
                'content_status': result.content_status,
                'message': result.message,
                'error': result.message
            }
            
    except Exception as exc:
        logger.exception(f"Unexpected error in content fetch task for article {article_id}: {str(exc)}")
        
        # Retry the task with exponential backoff
        if self.request.retries < self.max_retries:
            # Exponential backoff: 60s, 300s, 900s
            countdown = 60 * (5 ** self.request.retries)
            logger.info(f"Retrying content fetch for article {article_id} in {countdown} seconds")
            raise self.retry(countdown=countdown, exc=exc)
        
        # Max retries reached, mark as failed
        try:
            article = Article.objects.get(id=article_id)
            article.content_status = ContentStatus.TECHNICAL_ERROR
            article.fetch_error_message = f"Task failed after {self.max_retries} retries: {str(exc)}"
            article.save()
        except Article.DoesNotExist:
            pass
        
        return {
            'success': False,
            'article_id': article_id,
            'message': f"Task failed after {self.max_retries} retries",
            'error': str(exc)
        }


@shared_task(name="content.batch_fetch_content")
def batch_fetch_content_task(article_ids: List[int], max_concurrent: int = 5) -> Dict[str, Any]:
    """
    Async task to fetch content for multiple articles.
    
    Args:
        article_ids (List[int]): List of article IDs to fetch content for
        max_concurrent (int): Maximum concurrent fetches
        
    Returns:
        Dict[str, Any]: Task result with batch processing summary
    """
    try:
        logger.info(f"Starting batch content fetch for {len(article_ids)} articles")
        
        # Process articles in batches
        results = batch_fetch_content(article_ids, max_concurrent)
        
        # Summarize results
        successful = sum(1 for r in results.values() if r.success)
        failed = len(results) - successful
        
        logger.info(f"Batch content fetch completed: {successful} successful, {failed} failed")
        
        return {
            'success': True,
            'total_articles': len(article_ids),
            'successful': successful,
            'failed': failed,
            'results': {
                article_id: {
                    'success': result.success,
                    'content_status': result.content_status,
                    'message': result.message
                }
                for article_id, result in results.items()
            }
        }
        
    except Exception as exc:
        logger.exception(f"Error in batch content fetch task: {str(exc)}")
        return {
            'success': False,
            'error': str(exc),
            'total_articles': len(article_ids),
            'successful': 0,
            'failed': len(article_ids)
        }


@shared_task(name="content.process_pending_articles")
def process_pending_articles_task(limit: int = 100) -> Dict[str, Any]:
    """
    Process articles that are pending content fetch.
    
    Args:
        limit (int): Maximum number of articles to process
        
    Returns:
        Dict[str, Any]: Task result with processing summary
    """
    try:
        logger.info(f"Processing pending articles (limit: {limit})")
        
        fetcher = ContentFetcher()
        articles = fetcher.get_articles_needing_fetch(limit)
        
        if not articles:
            logger.info("No pending articles found")
            return {
                'success': True,
                'message': 'No pending articles found',
                'processed': 0,
                'queued': 0
            }
        
        # Queue individual fetch tasks
        queued_count = 0
        for article in articles:
            try:
                fetch_article_content_task.delay(article.id)
                queued_count += 1
            except Exception as e:
                logger.error(f"Failed to queue fetch task for article {article.id}: {str(e)}")
        
        logger.info(f"Queued {queued_count} content fetch tasks")
        
        return {
            'success': True,
            'message': f'Queued {queued_count} content fetch tasks',
            'processed': len(articles),
            'queued': queued_count
        }
        
    except Exception as exc:
        logger.exception(f"Error in process pending articles task: {str(exc)}")
        return {
            'success': False,
            'error': str(exc),
            'processed': 0,
            'queued': 0
        }


@shared_task(name="content.retry_failed_fetches")
def retry_failed_fetches_task(limit: int = 50) -> Dict[str, Any]:
    """
    Retry articles that failed content fetching and are ready for retry.
    
    Args:
        limit (int): Maximum number of articles to retry
        
    Returns:
        Dict[str, Any]: Task result with retry summary
    """
    try:
        logger.info(f"Processing retry attempts (limit: {limit})")
        
        fetcher = ContentFetcher()
        articles = fetcher.get_articles_for_retry(limit)
        
        if not articles:
            logger.info("No articles ready for retry")
            return {
                'success': True,
                'message': 'No articles ready for retry',
                'processed': 0,
                'queued': 0
            }
        
        # Queue retry tasks
        queued_count = 0
        for article in articles:
            try:
                fetch_article_content_task.delay(article.id)
                queued_count += 1
            except Exception as e:
                logger.error(f"Failed to queue retry task for article {article.id}: {str(e)}")
        
        logger.info(f"Queued {queued_count} retry tasks")
        
        return {
            'success': True,
            'message': f'Queued {queued_count} retry tasks',
            'processed': len(articles),
            'queued': queued_count
        }
        
    except Exception as exc:
        logger.exception(f"Error in retry failed fetches task: {str(exc)}")
        return {
            'success': False,
            'error': str(exc),
            'processed': 0,
            'queued': 0
        }


@shared_task(name="content.cleanup_old_fetch_logs")
def cleanup_old_fetch_logs_task(days_to_keep: int = 30) -> Dict[str, Any]:
    """
    Clean up old fetch logs to prevent database bloat.
    
    Args:
        days_to_keep (int): Number of days of logs to keep
        
    Returns:
        Dict[str, Any]: Task result with cleanup summary
    """
    try:
        from .models import ContentFetchLog
        
        cutoff_date = timezone.now() - timezone.timedelta(days=days_to_keep)
        
        # Delete old fetch logs
        deleted_count, _ = ContentFetchLog.objects.filter(
            created_at__lt=cutoff_date
        ).delete()
        
        logger.info(f"Cleaned up {deleted_count} old fetch logs (older than {days_to_keep} days)")
        
        return {
            'success': True,
            'message': f'Cleaned up {deleted_count} old fetch logs',
            'deleted_count': deleted_count,
            'cutoff_date': cutoff_date.isoformat()
        }
        
    except Exception as exc:
        logger.exception(f"Error in cleanup old fetch logs task: {str(exc)}")
        return {
            'success': False,
            'error': str(exc),
            'deleted_count': 0
        }


@shared_task(name="content.update_content_metrics")
def update_content_metrics_task() -> Dict[str, Any]:
    """
    Update content metrics and statistics for monitoring.
    
    Returns:
        Dict[str, Any]: Task result with metrics summary
    """
    try:
        from .models import ContentFetchLog
        from django.db.models import Count, Avg, Q
        
        # Calculate content availability statistics
        total_articles = Article.objects.count()
        
        content_stats = Article.objects.aggregate(
            content_available=Count('id', filter=Q(content_status=ContentStatus.CONTENT_AVAILABLE)),
            partial_content=Count('id', filter=Q(content_status=ContentStatus.PARTIAL_CONTENT)),
            metadata_only=Count('id', filter=Q(content_status=ContentStatus.METADATA_ONLY)),
            paywall_blocked=Count('id', filter=Q(content_status=ContentStatus.PAYWALL_BLOCKED)),
            pending=Count('id', filter=Q(content_status=ContentStatus.PENDING)),
            failed=Count('id', filter=Q(content_status__in=[
                ContentStatus.TECHNICAL_ERROR, 
                ContentStatus.ACCESS_DENIED, 
                ContentStatus.INVALID_URL,
                ContentStatus.TIMEOUT
            ])),
            avg_quality_score=Avg('content_quality_score'),
            avg_completeness=Avg('content_completeness')
        )
        
        # Calculate fetch success rates
        recent_logs = ContentFetchLog.objects.filter(
            created_at__gte=timezone.now() - timezone.timedelta(days=7)
        )
        
        fetch_stats = recent_logs.aggregate(
            total_attempts=Count('id'),
            successful=Count('id', filter=Q(status='success')),
            paywall_detected=Count('id', filter=Q(status='paywall')),
            failed=Count('id', filter=Q(status='failed')),
            avg_response_time=Avg('response_time_ms')
        )
        
        # Calculate success rate
        success_rate = 0.0
        if fetch_stats['total_attempts'] > 0:
            success_rate = (fetch_stats['successful'] / fetch_stats['total_attempts']) * 100
        
        metrics = {
            'total_articles': total_articles,
            'content_availability': {
                'content_available': content_stats['content_available'] or 0,
                'partial_content': content_stats['partial_content'] or 0,
                'metadata_only': content_stats['metadata_only'] or 0,
                'paywall_blocked': content_stats['paywall_blocked'] or 0,
                'pending': content_stats['pending'] or 0,
                'failed': content_stats['failed'] or 0,
            },
            'quality_metrics': {
                'avg_quality_score': round(content_stats['avg_quality_score'] or 0.0, 3),
                'avg_completeness': round(content_stats['avg_completeness'] or 0.0, 3),
            },
            'fetch_performance': {
                'total_attempts_7d': fetch_stats['total_attempts'] or 0,
                'successful_7d': fetch_stats['successful'] or 0,
                'success_rate_7d': round(success_rate, 2),
                'paywall_rate_7d': round(
                    (fetch_stats['paywall_detected'] / max(fetch_stats['total_attempts'], 1)) * 100, 2
                ),
                'avg_response_time_ms': round(fetch_stats['avg_response_time'] or 0.0, 0),
            }
        }
        
        logger.info(f"Content metrics updated: {metrics}")
        
        return {
            'success': True,
            'message': 'Content metrics updated successfully',
            'metrics': metrics
        }
        
    except Exception as exc:
        logger.exception(f"Error in update content metrics task: {str(exc)}")
        return {
            'success': False,
            'error': str(exc)
        }


# Convenience functions for manual task execution

def queue_content_fetch(article_id: int) -> str:
    """
    Queue a content fetch task for a specific article.
    
    Args:
        article_id (int): Article ID
        
    Returns:
        str: Task ID
    """
    task = fetch_article_content_task.delay(article_id)
    logger.info(f"Queued content fetch task {task.id} for article {article_id}")
    return task.id


def queue_batch_fetch(article_ids: List[int]) -> str:
    """
    Queue a batch content fetch task.
    
    Args:
        article_ids (List[int]): List of article IDs
        
    Returns:
        str: Task ID
    """
    task = batch_fetch_content_task.delay(article_ids)
    logger.info(f"Queued batch fetch task {task.id} for {len(article_ids)} articles")
    return task.id 