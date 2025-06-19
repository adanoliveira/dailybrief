"""
Celery tasks for Step 2 content processing.
Handles Safari mode, LLM enhancement, and hybrid processing with cost optimization.
"""

import logging
from typing import List, Dict, Any, Optional
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.db import transaction
from django.conf import settings

from apps.articles.models import Article, ProcessingStatus
from .services import ContentProcessor, ProcessingManager, _truncate_route_name
from .models import serialize_content_blocks

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, soft_time_limit=600, time_limit=900)
def process_article_content(self, article_id: int, route: str = None) -> Dict[str, Any]:
    """
    Process single article content using intelligent routing.
    
    Args:
        article_id: Article ID to process
        route: Optional route override ('algorithmic', 'llm_enhanced', 'hybrid')
    
    Returns:
        Dict with processing results
    """
    
    try:
        article = Article.objects.get(id=article_id)
        
        # Check if article needs processing
        if article.process_status == ProcessingStatus.COMPLETED:
            return {
                'success': True,
                'article_id': article_id,
                'message': 'Article already processed',
                'route_used': 'none'
            }
        
        # Update status to processing
        article.process_status = ProcessingStatus.PROCESSING
        article.process_attempts = (article.process_attempts or 0) + 1
        article.last_process_attempt = timezone.now()
        article.save(update_fields=['process_status', 'process_attempts', 'last_process_attempt'])
        
        # Process content
        processor = ContentProcessor()
        result = processor.process_article_content(article, route)
        
        if result.success:
            # Store results in database
            with transaction.atomic():
                article.clean_content = result.clean_content
                article.content_blocks = serialize_content_blocks(result.content_blocks)
                article.extracted_metadata = result.extracted_metadata
                article.content_quality_metrics = {
                    'overall_score': result.quality_score,
                    'processing_time_ms': result.processing_time_ms
                }
                article.process_status = ProcessingStatus.COMPLETED
                article.process_route = _truncate_route_name(getattr(result, 'route_used', 'llm_enhanced'))  # Dynamic route tracking
                article.process_duration_ms = result.processing_time_ms
                article.last_process_attempt = timezone.now()
                article.save()
            
            logger.info(f"Successfully processed article {article_id} with quality {result.quality_score}")
            
            return {
                'success': True,
                'article_id': article_id,
                'quality_score': result.quality_score,
                'processing_time_ms': result.processing_time_ms,
                'content_blocks_count': len(result.content_blocks),
                'route_used': route or 'auto'
            }
        
        else:
            # Handle processing failure
            article.process_status = ProcessingStatus.FAILED
            article.last_process_attempt = timezone.now()
            article.save(update_fields=['process_status', 'last_process_attempt'])
            
            logger.error(f"Failed to process article {article_id}: {result.error_message}")
            
            # Retry if we haven't exceeded max attempts
            if self.request.retries < self.max_retries:
                logger.info(f"Retrying article {article_id} (attempt {self.request.retries + 1})")
                raise self.retry(countdown=60 * (self.request.retries + 1))
            
            return {
                'success': False,
                'article_id': article_id,
                'error_message': result.error_message,
                'route_used': route or 'auto'
            }
    
    except Article.DoesNotExist:
        logger.error(f"Article {article_id} not found")
        return {
            'success': False,
            'article_id': article_id,
            'error_message': 'Article not found'
        }
    
    except Exception as e:
        # Handle both regular exceptions and timeout exceptions
        from celery.exceptions import SoftTimeLimitExceeded
        
        error_message = str(e)
        if isinstance(e, SoftTimeLimitExceeded):
            error_message = "Task timed out after 10 minutes"
            logger.warning(f"Article {article_id} processing timed out")
        else:
            logger.exception(f"Unexpected error processing article {article_id}: {str(e)}")
        
        # Update article status
        try:
            article = Article.objects.get(id=article_id)
            article.process_status = ProcessingStatus.FAILED
            article.last_process_attempt = timezone.now()
            article.process_error_message = error_message
            article.save(update_fields=['process_status', 'last_process_attempt', 'process_error_message'])
        except:
            pass
        
        # Don't retry timeout errors
        if not isinstance(e, SoftTimeLimitExceeded) and self.request.retries < self.max_retries:
            logger.info(f"Retrying article {article_id} due to error (attempt {self.request.retries + 1})")
            raise self.retry(countdown=60 * (self.request.retries + 1))
        
        return {
            'success': False,
            'article_id': article_id,
            'error_message': error_message
        }


@shared_task
def process_batch_articles(article_ids: List[int]) -> Dict[str, Any]:
    """
    Process content for multiple articles in a batch.
    More efficient for bulk operations with cost tracking.
    """
    
    if not article_ids:
        return {
            'processed': 0,
            'successful': 0,
            'failed': 0,
            'message': 'No article IDs provided'
        }
    
    try:
        # Get articles that need processing
        articles = Article.objects.filter(
            id__in=article_ids,
            process_status=ProcessingStatus.PENDING,
            fetch_status='completed'  # Must have completed Step 1
        )
        
        if not articles:
            return {
                'processed': 0,
                'successful': 0,
                'failed': 0,
                'message': 'No articles need processing'
            }
        
        # Process articles with cost tracking
        processor = ContentProcessor()
        results = []
        total_cost = 0.0
        route_counts = {'safari_mode': 0, 'llm_enhanced': 0, 'hybrid': 0}
        
        for article in articles:
            # Process and store the article, getting cost and route info
            processing_result = processor.process_article_content(article)
            
            # Store results in database if successful
            if processing_result.success:
                with transaction.atomic():
                    article.clean_content = processing_result.clean_content
                    article.content_blocks = serialize_content_blocks(processing_result.content_blocks)
                    article.extracted_metadata = processing_result.extracted_metadata
                    article.content_quality_metrics = {
                        'overall_score': processing_result.quality_score,
                        'processing_time_ms': processing_result.processing_time_ms
                    }
                    article.process_status = ProcessingStatus.COMPLETED
                    article.process_route = _truncate_route_name(getattr(processing_result, 'route_used', 'llm_enhanced'))
                    article.process_duration_ms = processing_result.processing_time_ms
                    article.process_cost_usd = 0.0001  # Estimated cost
                    article.process_attempts = (article.process_attempts or 0) + 1
                    article.last_process_attempt = timezone.now()
                    article.save()
            else:
                # Mark as failed
                article.process_status = ProcessingStatus.FAILED
                article.process_route = _truncate_route_name(getattr(processing_result, 'route_used', 'llm_enhanced'))  # Record the actual route even for failures
                article.process_attempts = (article.process_attempts or 0) + 1
                article.last_process_attempt = timezone.now()
                article.save(update_fields=['process_status', 'process_route', 'process_attempts', 'last_process_attempt'])
            
            # Create a ProcessResult-like object for consistency
            result = {
                'success': processing_result.success,
                'article': article,
                'processing_result': processing_result,
                'route_used': getattr(processing_result, 'route_used', 'llm_enhanced'),  # Dynamic route tracking
                'duration_ms': processing_result.processing_time_ms,
                'cost_usd': 0.0001 if processing_result.success else 0.0,  # Estimated cost
                'error_message': processing_result.error_message
            }
            results.append(result)
            
            if result['success']:
                total_cost += result['cost_usd']
                route_counts[result['route_used']] = route_counts.get(result['route_used'], 0) + 1
        
        # Compile statistics
        successful = sum(1 for r in results if r['success'])
        failed = len(results) - successful
        
        # Log batch results with cost analysis
        logger.info(f"Batch processing completed: {successful} successful, {failed} failed. "
                   f"Total cost: ${total_cost:.4f}, Routes: {route_counts}")
        
        return {
            'processed': len(results),
            'successful': successful,
            'failed': failed,
            'total_cost_usd': total_cost,
            'avg_cost_per_article': total_cost / len(results) if results else 0,
            'route_distribution': route_counts,
            'article_ids': article_ids,
            'results': [
                {
                    'article_id': r['article'].id if r['article'] else None,
                    'success': r['success'],
                    'route_used': r['route_used'],
                    'duration_ms': r['duration_ms'],
                    'cost_usd': r['cost_usd'],
                    'quality_score': r['processing_result'].quality_score if r['processing_result'] else 0,
                    'error_message': r['error_message']
                }
                for r in results
            ]
        }
        
    except Exception as e:
        logger.exception(f"Batch processing failed for articles {article_ids}: {str(e)}")
        return {
            'processed': 0,
            'successful': 0,
            'failed': len(article_ids),
            'error_message': str(e),
            'article_ids': article_ids
        }


@shared_task
def process_pending_articles(limit: int = 20) -> Dict[str, Any]:
    """
    Process content for pending articles automatically.
    Runs periodically to process articles that completed Step 1.
    """
    
    try:
        manager = ProcessingManager()
        result = manager.process_pending_articles(limit=limit)
        
        logger.info(f"Processed {result['processed']} pending articles: "
                   f"{result['successful']} successful, {result['failed']} failed. "
                   f"Total cost: ${result.get('total_cost_usd', 0):.4f}")
        
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
def retry_failed_processing(max_retries: int = 3) -> Dict[str, Any]:
    """
    Retry processing for articles that failed but haven't exceeded max attempts.
    """
    
    try:
        manager = ProcessingManager()
        result = manager.retry_failed_processing(max_retries=max_retries)
        
        logger.info(f"Retried {result['processed']} failed articles: "
                   f"{result['successful']} successful, {result['failed']} failed. "
                   f"Total cost: ${result.get('total_cost_usd', 0):.4f}")
        
        return result
        
    except Exception as e:
        logger.exception(f"Failed to retry failed processing: {str(e)}")
        return {
            'processed': 0,
            'successful': 0,
            'failed': 0,
            'error_message': str(e)
        }


@shared_task
def optimize_processing_routes() -> Dict[str, Any]:
    """
    Analyze processing performance and optimize routing thresholds.
    """
    
    try:
        from .routing import ProcessingRouter
        from django.db.models import Avg, Count, Q
        
        router = ProcessingRouter()
        
        # Get performance data for last 24 hours
        since = timezone.now() - timedelta(hours=24)
        
        # Analyze route performance
        route_performance = Article.objects.filter(
            last_process_attempt__gte=since,
            process_status=ProcessingStatus.COMPLETED
        ).values('process_route').annotate(
            count=Count('id'),
            avg_quality=Avg('content_quality_metrics__overall_score'),
            avg_cost=Avg('process_cost_usd'),
            avg_duration=Avg('process_duration_ms')
        )
        
        optimization_suggestions = []
        current_stats = router.get_routing_statistics()
        
        # Analyze if we should adjust thresholds
        for route_data in route_performance:
            route = route_data['process_route']
            quality = route_data['avg_quality'] or 0
            cost = route_data['avg_cost'] or 0
            count = route_data['count']
            
            if route == 'safari_mode' and quality > 0.8 and count > 10:
                # Safari mode is performing well, maybe increase LLM threshold
                optimization_suggestions.append({
                    'type': 'increase_llm_threshold',
                    'reason': f'Safari mode achieving {quality:.3f} quality',
                    'current_threshold': router.llm_threshold,
                    'suggested_threshold': min(0.8, router.llm_threshold + 0.05)
                })
            
            elif route == 'llm_enhanced' and quality < 0.7 and count > 5:
                # LLM not performing well, maybe decrease threshold
                optimization_suggestions.append({
                    'type': 'decrease_llm_threshold',
                    'reason': f'LLM mode only achieving {quality:.3f} quality',
                    'current_threshold': router.llm_threshold,
                    'suggested_threshold': max(0.4, router.llm_threshold - 0.05)
                })
        
        # Calculate cost efficiency
        total_articles = sum(r['count'] for r in route_performance)
        total_cost = sum(r['count'] * r['avg_cost'] for r in route_performance)
        avg_cost_per_article = total_cost / total_articles if total_articles > 0 else 0
        
        logger.info(f"Route optimization analysis: {len(optimization_suggestions)} suggestions, "
                   f"avg cost: ${avg_cost_per_article:.4f}")
        
        return {
            'analysis_completed': True,
            'articles_analyzed': total_articles,
            'avg_cost_per_article': avg_cost_per_article,
            'route_performance': list(route_performance),
            'optimization_suggestions': optimization_suggestions,
            'current_thresholds': {
                'llm_threshold': router.llm_threshold,
                'hybrid_threshold': router.hybrid_threshold
            }
        }
        
    except Exception as e:
        logger.exception(f"Route optimization failed: {str(e)}")
        return {
            'analysis_completed': False,
            'error_message': str(e)
        }


@shared_task
def cleanup_processing_data() -> Dict[str, Any]:
    """
    Clean up old processing data and reset stuck articles.
    """
    
    try:
        # Reset articles stuck in PROCESSING status for more than 2 hours
        stuck_threshold = timezone.now() - timedelta(hours=2)
        
        from django.db.models import Q
        
        # Include both articles with old timestamps AND articles with null timestamps (stuck without proper tracking)
        stuck_articles = Article.objects.filter(
            process_status=ProcessingStatus.PROCESSING
        ).filter(
            Q(last_process_attempt__lt=stuck_threshold) |
            Q(last_process_attempt__isnull=True)
        )
        
        stuck_count = stuck_articles.count()
        
        if stuck_count > 0:
            stuck_articles.update(
                process_status=ProcessingStatus.PENDING,
                process_error_message='Reset from stuck PROCESSING status'
            )
            
            logger.info(f"Reset {stuck_count} articles stuck in PROCESSING status")
        
        # Clean up very old failed processing attempts (older than 7 days)
        old_threshold = timezone.now() - timedelta(days=7)
        
        old_failed = Article.objects.filter(
            process_status=ProcessingStatus.FAILED,
            last_process_attempt__lt=old_threshold,
            process_attempts__gte=3
        )
        
        old_count = old_failed.count()
        
        if old_count > 0:
            # Don't reset these, just log for monitoring
            logger.info(f"Found {old_count} articles with old failed processing attempts")
        
        # Calculate processing queue health
        pending_count = Article.objects.filter(
            process_status=ProcessingStatus.PENDING,
            fetch_status='completed'
        ).count()
        
        processing_count = Article.objects.filter(
            process_status=ProcessingStatus.PROCESSING
        ).count()
        
        return {
            'stuck_articles_reset': stuck_count,
            'old_failed_articles': old_count,
            'pending_articles': pending_count,
            'processing_articles': processing_count,
            'cleanup_completed': True
        }
        
    except Exception as e:
        logger.exception(f"Processing cleanup failed: {str(e)}")
        return {
            'stuck_articles_reset': 0,
            'old_failed_articles': 0,
            'cleanup_completed': False,
            'error_message': str(e)
        }


@shared_task
def get_processing_statistics() -> Dict[str, Any]:
    """
    Generate comprehensive processing performance statistics.
    """
    
    try:
        processor = ContentProcessor()
        stats = processor.get_processing_statistics()
        
        logger.info(f"Processing statistics: {stats['success_rate']:.1f}% success rate, "
                   f"avg cost: ${stats.get('avg_cost', 0):.4f}, "
                   f"avg quality: {stats.get('avg_quality', 0):.3f}")
        
        return stats
        
    except Exception as e:
        logger.exception(f"Failed to generate processing statistics: {str(e)}")
        return {
            'error_message': str(e),
            'statistics_available': False
        }


@shared_task
def process_high_priority_articles() -> Dict[str, Any]:
    """
    Process high-priority articles (trending, breaking news) with LLM enhancement.
    """
    
    try:
        # Get high-priority articles (you can customize this query)
        high_priority_articles = Article.objects.filter(
            process_status=ProcessingStatus.PENDING,
            fetch_status='completed',
            # Add your high-priority criteria here
            # e.g., is_trending=True, is_breaking=True, etc.
        ).order_by('-published_at')[:10]
        
        if not high_priority_articles:
            return {
                'processed': 0,
                'successful': 0,
                'failed': 0,
                'message': 'No high-priority articles to process'
            }
        
        # Force LLM processing for high-priority articles
        processor = ContentProcessor()
        results = []
        total_cost = 0.0
        
        for article in high_priority_articles:
            # Temporarily override routing to use LLM
            original_route = processor.router.determine_route(article)
            
            # Force LLM or hybrid processing
            if original_route == 'safari_mode':
                forced_route = 'llm_enhanced'
            else:
                forced_route = original_route
            
            # Process with forced route
            if forced_route == 'llm_enhanced':
                processing_result = processor._process_llm_enhanced(article)
                cost = 0.01
            elif forced_route == 'hybrid':
                processing_result = processor._process_hybrid(article)
                cost = 0.005
            else:
                processing_result = processor._process_safari_mode(article)
                cost = 0.001
            
            if processing_result.success:
                processor._store_processing_results(article, processing_result, forced_route, cost)
                processor._update_processing_status(article, ProcessingStatus.COMPLETED)
                total_cost += cost
            
            results.append({
                'article_id': article.id,
                'success': processing_result.success,
                'route_used': forced_route,
                'original_route': original_route,
                'quality_score': processing_result.quality_score,
                'cost_usd': cost
            })
        
        successful = sum(1 for r in results if r['success'])
        failed = len(results) - successful
        
        logger.info(f"High-priority processing completed: {successful} successful, {failed} failed. "
                   f"Total cost: ${total_cost:.4f}")
        
        return {
            'processed': len(results),
            'successful': successful,
            'failed': failed,
            'total_cost_usd': total_cost,
            'results': results
        }
        
    except Exception as e:
        logger.exception(f"High-priority processing failed: {str(e)}")
        return {
            'processed': 0,
            'successful': 0,
            'failed': 0,
            'error_message': str(e)
        }


# Periodic task configurations (add to celery beat schedule)
PROCESSING_PERIODIC_TASKS = {
    'process-pending-articles': {
        'task': 'apps.content.processor.tasks.process_pending_articles',
        'schedule': 600.0,  # Every 10 minutes
        'kwargs': {'limit': 20}
    },
    'retry-failed-processing': {
        'task': 'apps.content.processor.tasks.retry_failed_processing',
        'schedule': 1800.0,  # Every 30 minutes
        'kwargs': {'max_retries': 3}
    },
    'optimize-processing-routes': {
        'task': 'apps.content.processor.tasks.optimize_processing_routes',
        'schedule': 3600.0,  # Every hour
    },
    'cleanup-processing-data': {
        'task': 'apps.content.processor.tasks.cleanup_processing_data',
        'schedule': 3600.0,  # Every hour
    },
    'processing-statistics': {
        'task': 'apps.content.processor.tasks.get_processing_statistics',
        'schedule': 900.0,  # Every 15 minutes
    },
    'process-high-priority': {
        'task': 'apps.content.processor.tasks.process_high_priority_articles',
        'schedule': 300.0,  # Every 5 minutes
    }
} 