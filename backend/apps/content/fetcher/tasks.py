"""
Celery tasks for content extraction (Step 1).
Optimized for speed and batch processing.
"""

import logging
from typing import List, Dict, Any
from celery import shared_task
from django.utils import timezone
from datetime import timedelta

from apps.articles.models import Article, FetchStatus
from .fetcher import ContentFetcher, FetchManager

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def fetch_article_content(self, article_id: int) -> Dict[str, Any]:
    """
    Fetch content for a single article (Step 1 only).
    Optimized for speed - no processing, just raw extraction.
    """
    
    try:
        article = Article.objects.get(id=article_id)
        
        # Check if article still needs fetching
        if not article.needs_fetch:
            return {
                'success': False,
                'article_id': article_id,
                'message': f'Article no longer needs fetching. Status: {article.fetch_status}'
            }
        
        # Perform extraction
        fetcher = ContentFetcher()
        result = fetcher.fetch_article_content(article)
        
        if result.success:
            logger.info(f"Fetch successful for article {article_id} using {result.strategy_used}")
            return {
                'success': True,
                'article_id': article_id,
                'strategy_used': result.strategy_used,
                'duration_ms': result.duration_ms,
                'has_basic_content': bool(article.basic_content),
                'has_raw_html': bool(article.raw_html),
                'paywall_detected': article.paywall_detected
            }
        else:
            logger.error(f"Fetch failed for article {article_id}: {result.error_message}")
            
            # Retry if we haven't exceeded max attempts
            if article.fetch_attempts < 3:
                raise self.retry(countdown=60 * (2 ** self.request.retries))
            
            return {
                'success': False,
                'article_id': article_id,
                'error_message': result.error_message,
                'attempts': article.fetch_attempts
            }
            
    except Article.DoesNotExist:
        logger.error(f"Article {article_id} not found")
        return {
            'success': False,
            'article_id': article_id,
            'error_message': 'Article not found'
        }
    
    except Exception as e:
        logger.exception(f"Unexpected error in fetch for article {article_id}: {str(e)}")
        
        # Retry on unexpected errors
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        return {
            'success': False,
            'article_id': article_id,
            'error_message': str(e),
            'retries_exhausted': True
        }


@shared_task
def fetch_batch_articles(article_ids: List[int]) -> Dict[str, Any]:
    """
    Fetch content for multiple articles in a batch.
    More efficient than individual tasks for bulk operations.
    """
    
    if not article_ids:
        return {
            'processed': 0,
            'successful': 0,
            'failed': 0,
            'message': 'No article IDs provided'
        }
    
    try:
        # Get articles that need fetching
        articles = Article.objects.filter(
            id__in=article_ids,
            fetch_status=FetchStatus.PENDING
        )
        
        if not articles:
            return {
                'processed': 0,
                'successful': 0,
                'failed': 0,
                'message': 'No articles need fetching'
            }
        
        # Perform batch fetching
        fetcher = ContentFetcher()
        results = fetcher.fetch_multiple_articles(list(articles))
        
        # Compile statistics
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful
        
        # Log results
        logger.info(f"Batch fetch completed: {successful} successful, {failed} failed out of {len(results)}")
        
        return {
            'processed': len(results),
            'successful': successful,
            'failed': failed,
            'article_ids': article_ids,
            'results': [
                {
                    'article_id': r.article.id if r.article else None,
                    'success': r.success,
                    'strategy_used': r.strategy_used,
                    'duration_ms': r.duration_ms,
                    'error_message': r.error_message
                }
                for r in results
            ]
        }
        
    except Exception as e:
        logger.exception(f"Batch fetch failed for articles {article_ids}: {str(e)}")
        return {
            'processed': 0,
            'successful': 0,
            'failed': len(article_ids),
            'error_message': str(e),
            'article_ids': article_ids
        }


@shared_task
def fetch_pending_articles(limit: int = 50) -> Dict[str, Any]:
    """
    Fetch content for pending articles automatically.
    Runs periodically to process new articles.
    """
    
    try:
        manager = FetchManager()
        result = manager.fetch_pending_articles(limit=limit)
        
        logger.info(f"Processed {result['processed']} pending articles: "
                   f"{result['successful']} successful, {result['failed']} failed")
        
        return result
        
    except Exception as e:
        logger.exception(f"Failed to process pending articles: {str(e)}")
        return {
            'processed': 0,
            'successful': 0,
            'failed': 0,
            'error_message': str(e)
        }


@shared_task
def retry_failed_fetches(max_retries: int = 3) -> Dict[str, Any]:
    """
    Retry fetching for articles that failed but haven't exceeded max attempts.
    """
    
    try:
        manager = FetchManager()
        result = manager.retry_failed_articles(max_retries=max_retries)
        
        logger.info(f"Retried {result['processed']} failed articles: "
                   f"{result['successful']} successful, {result['failed']} failed")
        
        return result
        
    except Exception as e:
        logger.exception(f"Failed to retry failed articles: {str(e)}")
        return {
            'processed': 0,
            'successful': 0,
            'failed': 0,
            'error_message': str(e)
        }


@shared_task
def cleanup_old_fetch_attempts() -> Dict[str, Any]:
    """
    Clean up old fetch attempts and reset articles that have been stuck.
    """
    
    try:
        # Reset articles stuck in FETCHING status for more than 1 hour
        stuck_threshold = timezone.now() - timedelta(hours=1)
        
        stuck_articles = Article.objects.filter(
            fetch_status=FetchStatus.FETCHING,
            last_fetch_attempt__lt=stuck_threshold
        )
        
        stuck_count = stuck_articles.count()
        
        if stuck_count > 0:
            stuck_articles.update(
                fetch_status=FetchStatus.PENDING,
                fetch_error_message='Reset from stuck FETCHING status'
            )
            
            logger.info(f"Reset {stuck_count} articles stuck in FETCHING status")
        
        # Clean up very old failed attempts (older than 7 days)
        old_threshold = timezone.now() - timedelta(days=7)
        
        old_failed = Article.objects.filter(
            fetch_status=FetchStatus.FAILED,
            last_fetch_attempt__lt=old_threshold,
            fetch_attempts__gte=3
        )
        
        old_count = old_failed.count()
        
        if old_count > 0:
            # Don't reset these, just log for monitoring
            logger.info(f"Found {old_count} articles with old failed fetch attempts")
        
        return {
            'stuck_articles_reset': stuck_count,
            'old_failed_articles': old_count,
            'cleanup_completed': True
        }
        
    except Exception as e:
        logger.exception(f"Cleanup task failed: {str(e)}")
        return {
            'stuck_articles_reset': 0,
            'old_failed_articles': 0,
            'cleanup_completed': False,
            'error_message': str(e)
        }


@shared_task
def get_fetch_statistics() -> Dict[str, Any]:
    """
    Generate fetch performance statistics.
    """
    
    try:
        fetcher = ContentFetcher()
        stats = fetcher.get_fetch_statistics()
        
        logger.info(f"Fetch statistics: {stats['success_rate']:.1f}% success rate, "
                   f"avg duration: {stats['avg_duration']:.0f}ms")
        
        return stats
        
    except Exception as e:
        logger.exception(f"Failed to generate fetch statistics: {str(e)}")
        return {
            'error_message': str(e),
            'statistics_available': False
        }


# Periodic task configurations (add to celery beat schedule)
FETCH_PERIODIC_TASKS = {
    'fetch-pending-articles': {
        'task': 'apps.content.fetcher.tasks.fetch_pending_articles',
        'schedule': 300.0,  # Every 5 minutes
        'kwargs': {'limit': 50}
    },
    'retry-failed-fetches': {
        'task': 'apps.content.fetcher.tasks.retry_failed_fetches',
        'schedule': 1800.0,  # Every 30 minutes
        'kwargs': {'max_retries': 3}
    },
    'cleanup-fetch-attempts': {
        'task': 'apps.content.fetcher.tasks.cleanup_old_fetch_attempts',
        'schedule': 3600.0,  # Every hour
    },
    'fetch-statistics': {
        'task': 'apps.content.fetcher.tasks.get_fetch_statistics',
        'schedule': 900.0,  # Every 15 minutes
    }
} 