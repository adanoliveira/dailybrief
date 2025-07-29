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
from decimal import Decimal

from apps.articles.models import Article, SummarizationStatus, ProcessingStatus
from .services import get_summarization_service
from .models import SummarizationRequest
from apps.content.summariser.models import ArticleEmbedding, ArticleSummary
from apps.content.summariser.services import SummarizationService

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=300, soft_time_limit=600, time_limit=900)
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
    
    # Queue individual summarization tasks asynchronously
    queued_count = 0
    failed_to_queue = 0
    
    for article_id in article_ids:
        try:
            summarize_article_pipeline.delay(article_id, force_regenerate)
            queued_count += 1
        except Exception as e:
            logger.error(f"Failed to queue summarization for article {article_id}: {str(e)}")
            failed_to_queue += 1
    
    logger.info(f"Batch summarization queued: {queued_count} successful, {failed_to_queue} failed to queue")
    
    return {
        'success': True,
        'articles_processed': len(article_ids),
        'successful': queued_count,
        'failed': failed_to_queue,
        'total_cost_usd': 0,  # Will be calculated when individual tasks complete
        'message': f'Queued {queued_count} articles for summarization'
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
def cleanup_stuck_summarization_articles() -> Dict[str, Any]:
    """
    Clean up articles stuck in PROCESSING status for summarization.
    
    Resets articles that have been stuck in PROCESSING status for more than 2 hours
    back to PENDING status, including those with null timestamps.
    """
    
    try:
        # Reset articles stuck in PROCESSING status for more than 2 hours
        stuck_threshold = timezone.now() - timezone.timedelta(hours=2)
        
        from django.db.models import Q
        
        # Include both articles with old timestamps AND articles with null timestamps (stuck without proper tracking)
        stuck_articles = Article.objects.filter(
            summarization_status=SummarizationStatus.PROCESSING
        ).filter(
            Q(last_summarization_attempt__lt=stuck_threshold) |
            Q(last_summarization_attempt__isnull=True)
        )
        
        stuck_count = stuck_articles.count()
        
        if stuck_count > 0:
            stuck_articles.update(
                summarization_status=SummarizationStatus.PENDING,
                summarization_error_message='Reset from stuck PROCESSING status'
            )
            
            logger.info(f"Reset {stuck_count} articles stuck in summarization PROCESSING status")
        
        # Clean up very old failed summarization attempts (older than 7 days)
        old_threshold = timezone.now() - timezone.timedelta(days=7)
        
        old_failed = Article.objects.filter(
            summarization_status=SummarizationStatus.FAILED,
            last_summarization_attempt__lt=old_threshold,
            summarization_attempts__gte=3
        )
        
        old_count = old_failed.count()
        
        if old_count > 0:
            # Don't reset these, just log for monitoring
            logger.info(f"Found {old_count} articles with old failed summarization attempts")
        
        # Calculate summarization queue health
        pending_count = Article.objects.filter(
            summarization_status=SummarizationStatus.PENDING,
            process_status=ProcessingStatus.COMPLETED  # Must have completed processing first
        ).count()
        
        processing_count = Article.objects.filter(
            summarization_status=SummarizationStatus.PROCESSING
        ).count()
        
        return {
            'stuck_articles_reset': stuck_count,
            'old_failed_articles': old_count,
            'pending_articles': pending_count,
            'processing_articles': processing_count,
            'cleanup_completed': True
        }
        
    except Exception as e:
        logger.exception(f"Summarization cleanup failed: {str(e)}")
        return {
            'stuck_articles_reset': 0,
            'old_failed_articles': 0,
            'cleanup_completed': False,
            'error_message': str(e)
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


@shared_task(bind=True, max_retries=3)
def generate_embeddings_batch(self, article_ids: List[int], force_regenerate: bool = False):
    """
    Generate embeddings for a batch of articles.
    
    Processes up to 50 articles per batch for optimal OpenAI API efficiency.
    Articles must have summaries before embeddings can be generated.
    
    Args:
        article_ids: List of article IDs to process
        force_regenerate: Whether to regenerate existing embeddings
    """
    from django.db import transaction
    from apps.articles.models import Article
    from apps.content.summariser.models import ArticleEmbedding, ArticleSummary
    from apps.content.summariser.services import SummarizationService
    
    try:
        logger.info(f"Starting embedding batch processing for {len(article_ids)} articles")
        
        # Initialize service
        service = SummarizationService()
        
        # Batch size limit for optimal API performance
        max_batch_size = 50
        if len(article_ids) > max_batch_size:
            # Split into smaller batches and process sequentially
            for i in range(0, len(article_ids), max_batch_size):
                batch = article_ids[i:i + max_batch_size]
                generate_embeddings_batch.delay(batch, force_regenerate)
            return {"status": "split_into_batches", "total_articles": len(article_ids)}
        
        # Get articles with summaries
        articles_query = Article.objects.select_related('structured_summary').filter(
            id__in=article_ids,
            structured_summary__isnull=False
        )
        
        if not force_regenerate:
            # Exclude articles that already have embeddings
            articles_query = articles_query.filter(embedding__isnull=True)
        
        articles_to_process = list(articles_query)
        
        if not articles_to_process:
            logger.info("No articles need embedding generation")
            return {"status": "no_articles_to_process", "processed": 0}
        
        # Prepare texts for batch embedding
        embedding_texts = []
        article_mapping = {}  # Maps index to article
        
        for idx, article in enumerate(articles_to_process):
            summary = article.structured_summary
            embedding_text = f"{summary.headline} - {summary.abstract}"
            embedding_texts.append(embedding_text)
            article_mapping[idx] = article
        
        # Generate embeddings in batch
        ai_response = service.ai_service.generate_embedding(
            texts=embedding_texts,
            operation='embedding_generation'
        )
        
        if not ai_response.success:
            logger.error(f"Batch embedding generation failed: {ai_response.error_message}")
            raise Exception(f"Batch embedding failed: {ai_response.error_message}")
        
        # Store embeddings for each article
        created_count = 0
        updated_count = 0
        
        with transaction.atomic():
            for idx, embedding_vector in enumerate(ai_response.embeddings):
                article = article_mapping[idx]
                embedding_text = embedding_texts[idx]
                
                # Calculate per-article cost (approximate)
                per_article_tokens = ai_response.usage.get('prompt_tokens', 0) // len(embedding_texts)
                per_article_cost = Decimal('0.00002')  # Approximate cost per embedding
                
                embedding, created = ArticleEmbedding.objects.update_or_create(
                    article=article,
                    defaults={
                        'embedding': embedding_vector,
                        'embedding_text': embedding_text,
                        'embedding_length': len(embedding_vector),
                        'tokens_used': per_article_tokens,
                        'processing_time_ms': int(ai_response.response_time * 1000),
                        'cost_usd': per_article_cost
                    }
                )
                
                if created:
                    created_count += 1
                else:
                    updated_count += 1
        
        logger.info(f"Batch embedding completed: {created_count} created, {updated_count} updated")
        
        return {
            "status": "success",
            "processed": len(embedding_texts),
            "created": created_count,
            "updated": updated_count,
            "total_cost_usd": float(ai_response.usage.get('prompt_tokens', 0) * Decimal('0.00000002')),
            "processing_time_ms": int(ai_response.response_time * 1000)
        }
        
    except Exception as e:
        logger.error(f"Embedding batch processing failed: {str(e)}")
        
        # Retry logic
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying embedding batch processing (attempt {self.request.retries + 1})")
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        return {
            "status": "failed",
            "error": str(e),
            "processed": 0
        }


@shared_task
def generate_embeddings_for_pending_summaries(limit: int = 100):
    """
    Generate embeddings for articles that have summaries but no embeddings.
    
    Automatically processes articles in batches for efficiency.
    
    Args:
        limit: Maximum number of articles to process
    """
    from apps.articles.models import Article
    
    try:
        # Find articles with summaries but no embeddings
        pending_articles = Article.objects.filter(
            structured_summary__isnull=False,
            embedding__isnull=True
        ).values_list('id', flat=True)[:limit]
        
        pending_ids = list(pending_articles)
        
        if not pending_ids:
            logger.info("No pending articles found for embedding generation")
            return {"status": "no_pending_articles", "processed": 0}
        
        logger.info(f"Found {len(pending_ids)} articles pending embedding generation")
        
        # Process in batches of 50
        batch_size = 50
        total_processed = 0
        
        for i in range(0, len(pending_ids), batch_size):
            batch = pending_ids[i:i + batch_size]
            generate_embeddings_batch.delay(batch, force_regenerate=False)
            total_processed += len(batch)
        
        return {
            "status": "batches_queued",
            "total_articles": len(pending_ids),
            "batches_created": (len(pending_ids) + batch_size - 1) // batch_size
        }
        
    except Exception as e:
        logger.error(f"Failed to queue pending embeddings: {str(e)}")
        return {"status": "failed", "error": str(e)}


@shared_task
def cleanup_orphaned_embeddings():
    """
    Clean up embeddings for articles that no longer have summaries.
    
    Maintenance task to keep embedding data consistent.
    """
    from apps.content.summariser.models import ArticleEmbedding
    
    try:
        # Find embeddings for articles without summaries
        orphaned_embeddings = ArticleEmbedding.objects.filter(
            article__structured_summary__isnull=True
        )
        
        count = orphaned_embeddings.count()
        
        if count > 0:
            orphaned_embeddings.delete()
            logger.info(f"Cleaned up {count} orphaned embeddings")
        
        return {"status": "success", "cleaned_up": count}
        
    except Exception as e:
        logger.error(f"Failed to cleanup orphaned embeddings: {str(e)}")
        return {"status": "failed", "error": str(e)}


@shared_task
def find_similar_articles(article_id: int, similarity_threshold: float = 0.22, limit: int = 5):
    """
    Find articles similar to the given article using embeddings.
    
    Args:
        article_id: ID of the target article
        similarity_threshold: Minimum cosine similarity (default from plan: 0.22)
        limit: Maximum number of similar articles to return
    """
    from apps.articles.models import Article
    from apps.content.summariser.models import ArticleEmbedding
    import math
    
    try:
        # Get target article's embedding
        target_embedding = ArticleEmbedding.objects.filter(
            article_id=article_id
        ).first()
        
        if not target_embedding:
            return {"status": "no_embedding", "similar_articles": []}
        
        # Use pgvector for efficient similarity search
        similar_embeddings = ArticleEmbedding.find_similar(
            target_embedding=target_embedding,
            similarity_threshold=similarity_threshold,
            limit=limit
        ).select_related('article', 'article__structured_summary')
        
        similar_articles = []
        for embedding in similar_embeddings:
            similar_articles.append({
                'article_id': embedding.article.id,
                'article_title': embedding.article.title,
                'headline': embedding.article.structured_summary.headline if hasattr(embedding.article, 'structured_summary') else None,
                'similarity_score': embedding.similarity,  # Annotated by pgvector
                'published_at': embedding.article.published_at.isoformat()
            })
        
        return {
            "status": "success",
            "target_article_id": article_id,
            "similar_articles": similar_articles,
            "total_found": len(similar_articles)
        }
        
    except Exception as e:
        logger.error(f"Failed to find similar articles for {article_id}: {str(e)}")
        return {"status": "failed", "error": str(e)} 