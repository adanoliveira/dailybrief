"""
Content Enrichment Pipeline Tasks

Orchestrates the 4-stage content pipeline for articles, specifically targeting 
top headlines from the last 72 hours that come from the sync-top-headlines task.
Now filtered to only process articles from US and BR regions for cost optimization.

Pipeline Flow:
1. Fetcher → Extract raw content from article URLs
2. Processor → Clean and structure content using AI
3. Summariser → Generate headlines and abstracts
4. Analyzer → Extract entities, topics, and metadata

Scope: Only processes top headlines published within the last 72 hours from US and BR regions.
Each stage processes articles ready for that stage and moves them to the next queue.
Max retries: 3 per stage before removing from queue.
Uses existing batch tasks from individual content apps (fetcher, processor, summariser, analyzer).

Cost Optimization Strategy:
- Sync all top headlines globally for broad coverage
- Only run expensive AI processing on US and BR articles
- Reduces processing costs while maintaining comprehensive news gathering

Continuous Processing Strategy:
- Runs every 15-30 minutes to ensure complete processing
- Processes all stages synchronously (no fire-and-forget async tasks)
- Continues until all articles are either completed or failed
- Smart throttling during peak hours (every 10 minutes)
"""

import logging
from typing import List, Dict, Any, Optional
from celery import shared_task, chain, group
from django.db import models, transaction
from django.utils import timezone
from datetime import timedelta

from apps.articles.models import Article, FetchStatus, ProcessingStatus, SummarizationStatus, AnalyzerStatus

# Import task functions from each stage
from apps.content.fetcher.tasks import fetch_batch_articles
from apps.content.processor.tasks import process_batch_articles
from apps.content.summariser.tasks import batch_summarize_articles
from apps.content.analyzer.tasks import batch_analyze_articles

logger = logging.getLogger(__name__)

# Constants
PIPELINE_TIME_WINDOW_HOURS = 72
MAX_RETRY_ATTEMPTS = 3
TARGET_REGION_CODES = ['us', 'br']  # Only process US and Brazil articles


def _get_time_threshold() -> timezone.datetime:
    """Get the time threshold for pipeline processing (72 hours ago)."""
    return timezone.now() - timedelta(hours=PIPELINE_TIME_WINDOW_HOURS)


def _get_base_queryset():
    """
    Get base queryset for articles eligible for the content enrichment pipeline.

    Uses the topic-aware eligibility system which applies:
    1. Global headline_score threshold (0.70)
    2. Topic diversity floors (min 8 articles/topic, down to score 0.45)
    3. Topic caps (max 35 articles/topic)
    4. Per-publisher diminishing returns (soft cap 15/day)
    5. Cluster dedup (skip stories already processed via another source)

    Falls back to the legacy is_top_headline filter if eligibility check
    fails for any reason.
    """
    time_threshold = _get_time_threshold()

    try:
        from apps.articles.services.pipeline_eligibility import get_eligible_article_ids
        eligible_ids = get_eligible_article_ids(time_threshold)
        if eligible_ids:
            return Article.objects.filter(id__in=eligible_ids)
    except Exception as e:
        logger.warning(f"Pipeline eligibility check failed, using legacy filter: {e}")

    # Fallback: legacy filter
    return Article.objects.filter(
        is_top_headline=True,
        published_at__gte=time_threshold,
        regions__code__in=TARGET_REGION_CODES,
    ).distinct()


def _get_articles_for_stage(stage_filters: Dict[str, Any], limit: int) -> List[int]:
    """
    Get article IDs for a specific pipeline stage.
    
    Args:
        stage_filters: Additional filters specific to the stage
        limit: Maximum number of articles to return
    
    Returns:
        List of article IDs
    """
    queryset = _get_base_queryset().filter(**stage_filters).order_by('published_at')[:limit]
    return list(queryset.values_list('id', flat=True))


def _queue_async_task(task_func, article_ids: List[int], stage_name: str) -> Dict[str, Any]:
    """
    Queue an async task and return immediate summary.
    
    Args:
        task_func: The Celery task function to call
        article_ids: List of article IDs to process
        stage_name: Name of the stage for logging
    
    Returns:
        Dict with processing summary
    """
    task_func.delay(article_ids, force_regenerate=False)
    logger.info(f"{stage_name}: Queued {len(article_ids)} articles")
    
    return {
        'processed': len(article_ids),
        'successful': 0,  # Will be updated when task completes
        'failed': 0,
        'message': f'Queued {len(article_ids)} articles for {stage_name.lower()}'
    }


@shared_task
def process_top_headlines_pipeline(limit: int = 50) -> Dict[str, Any]:
    """
    Main pipeline task that processes top headlines through all 4 stages.
    
    This task is designed to run after sync-top-headlines and processes articles
    marked as is_top_headline=True through the complete content enrichment pipeline.
    
    Args:
        limit: Maximum number of articles to process per stage
    
    Returns:
        Dict with detailed results from each pipeline stage
    """
    logger.info(f"Starting top headlines content enrichment pipeline (limit: {limit})")
    
    pipeline_start = timezone.now()
    results = {
        'pipeline_start': pipeline_start.isoformat(),
        'stage_1_fetch': None,
        'stage_2_process': None, 
        'stage_3_summarize': None,
        'stage_4_analyze': None,
        'pipeline_summary': {
            'total_articles_processed': 0,
            'successful_completions': 0,
            'pipeline_duration_ms': 0
        }
    }
    
    try:
        # STAGE 1: FETCH - Process articles needing content extraction
        logger.info("Pipeline Stage 1: Fetching content for top headlines")
        results['stage_1_fetch'] = _process_stage1_fetch_top_headlines(limit)
        
        # STAGE 2: PROCESS - Process articles with fetched content 
        logger.info("Pipeline Stage 2: Processing content for top headlines")
        results['stage_2_process'] = _process_stage2_process_top_headlines(limit)
        
        # STAGE 3: SUMMARIZE - Summarize articles with processed content
        logger.info("Pipeline Stage 3: Summarizing content for top headlines")
        results['stage_3_summarize'] = _process_stage3_summarize_top_headlines(limit)
        
        # STAGE 4: ANALYZE - Analyze articles with summaries
        logger.info("Pipeline Stage 4: Analyzing content for top headlines")
        results['stage_4_analyze'] = _process_stage4_analyze_top_headlines(limit)
        
        # Calculate pipeline summary
        pipeline_end = timezone.now()
        pipeline_duration = (pipeline_end - pipeline_start).total_seconds() * 1000
        
        # Count total articles that moved through pipeline
        total_processed = sum([
            results['stage_1_fetch'].get('processed', 0),
            results['stage_2_process'].get('processed', 0), 
            results['stage_3_summarize'].get('processed', 0),
            results['stage_4_analyze'].get('processed', 0)
        ])
        
        # Count articles that completed the full pipeline
        completed_articles = _count_fully_processed_headlines()
        
        results['pipeline_summary'] = {
            'total_articles_processed': total_processed,
            'successful_completions': completed_articles,
            'pipeline_duration_ms': int(pipeline_duration),
            'pipeline_end': pipeline_end.isoformat()
        }
        
        logger.info(f"Top headlines pipeline completed: {total_processed} total processed, "
                   f"{completed_articles} fully completed, {pipeline_duration:.0f}ms")
        
        return results
        
    except Exception as e:
        logger.exception(f"Top headlines pipeline failed: {str(e)}")
        results['pipeline_error'] = str(e)
        return results


def _process_stage1_fetch_top_headlines(limit: int) -> Dict[str, Any]:
    """Stage 1: Fetch content for top headlines that need fetching."""
    
    stage_filters = {
        'fetch_status': FetchStatus.PENDING,
        'fetch_attempts__lt': MAX_RETRY_ATTEMPTS
    }
    
    article_ids = _get_articles_for_stage(stage_filters, limit)
    
    if not article_ids:
        logger.info("No top headlines need fetching")
        return {'processed': 0, 'successful': 0, 'failed': 0, 'message': 'No articles need fetching'}
    
    logger.info(f"Stage 1: Processing {len(article_ids)} top headlines for fetching")
    
    # Use existing batch fetch task - call directly for synchronous execution
    from apps.content.fetcher.tasks import fetch_batch_articles as fetch_func
    return fetch_func(article_ids)


def _process_stage2_process_top_headlines(limit: int) -> Dict[str, Any]:
    """Stage 2: Process top headlines that have been fetched."""
    
    # Find top headlines ready for processing 
    ready_for_processing = _get_base_queryset().filter(
        fetch_status=FetchStatus.COMPLETED,
        process_status=ProcessingStatus.PENDING,
        process_attempts__lt=MAX_RETRY_ATTEMPTS
    ).filter(
        # Must have content from Stage 1
        models.Q(raw_html__isnull=False, raw_html__regex=r'.{100,}') |
        models.Q(basic_content__isnull=False, basic_content__regex=r'.{50,}')
    ).order_by('published_at')[:limit]
    
    article_ids = list(ready_for_processing.values_list('id', flat=True))
    
    if not article_ids:
        logger.info("No top headlines ready for processing")
        return {'processed': 0, 'successful': 0, 'failed': 0, 'message': 'No articles ready for processing'}
    
    logger.info(f"Stage 2: Processing {len(article_ids)} top headlines for AI processing")
    
    # Use existing batch process task - call directly for synchronous execution
    from apps.content.processor.tasks import process_batch_articles as process_func
    return process_func(article_ids)


def _process_stage3_summarize_top_headlines(limit: int) -> Dict[str, Any]:
    """Stage 3: Summarize top headlines that have been processed."""
    
    # Find top headlines ready for summarization
    ready_for_summarization = _get_base_queryset().filter(
        process_status=ProcessingStatus.COMPLETED,
        summarization_status=SummarizationStatus.PENDING,
        summarization_attempts__lt=MAX_RETRY_ATTEMPTS
    ).filter(
        # Must have processed content from Stage 2
        models.Q(clean_content__isnull=False, clean_content__regex=r'.{200,}') |
        models.Q(basic_content__isnull=False, basic_content__regex=r'.{200,}')
    ).order_by('published_at')[:limit]
    
    article_ids = list(ready_for_summarization.values_list('id', flat=True))
    
    if not article_ids:
        logger.info("No top headlines ready for summarization")
        return {'processed': 0, 'successful': 0, 'failed': 0, 'message': 'No articles ready for summarization'}
    
    logger.info(f"Stage 3: Processing {len(article_ids)} top headlines for summarization")
    
    # Use existing batch summarize task - queue async and return summary
    return _queue_async_task(batch_summarize_articles, article_ids, "Stage 3")


def _process_stage4_analyze_top_headlines(limit: int) -> Dict[str, Any]:
    """Stage 4: Analyze top headlines that have been summarized."""
    
    # Find top headlines ready for analysis
    ready_for_analysis = _get_base_queryset().filter(
        summarization_status=SummarizationStatus.COMPLETED,
        analyzer_status=AnalyzerStatus.PENDING,
        analyzer_attempts__lt=MAX_RETRY_ATTEMPTS
    ).filter(
        # Must have summarized content from Stage 3
        models.Q(clean_content__isnull=False, clean_content__regex=r'.{200,}') |
        models.Q(basic_content__isnull=False, basic_content__regex=r'.{200,}')
    ).order_by('published_at')[:limit]
    
    article_ids = list(ready_for_analysis.values_list('id', flat=True))
    
    if not article_ids:
        logger.info("No top headlines ready for analysis")
        return {'processed': 0, 'successful': 0, 'failed': 0, 'message': 'No articles ready for analysis'}
    
    logger.info(f"Stage 4: Processing {len(article_ids)} top headlines for analysis")
    
    # Use existing batch analyze task - queue async and return summary
    return _queue_async_task(batch_analyze_articles, article_ids, "Stage 4")


def _count_fully_processed_headlines() -> int:
    """Count top headlines from last 72h from US/BR regions that have completed all 4 pipeline stages."""
    return _get_base_queryset().filter(
        fetch_status=FetchStatus.COMPLETED,
        process_status=ProcessingStatus.COMPLETED,
        summarization_status=SummarizationStatus.COMPLETED,
        analyzer_status=AnalyzerStatus.COMPLETED
    ).count()


@shared_task
def cleanup_failed_pipeline_articles(max_attempts: int = MAX_RETRY_ATTEMPTS) -> Dict[str, Any]:
    """
    Clean up articles that have exceeded max retry attempts in any pipeline stage.
    
    Only cleans up top headlines from the last 72 hours from US/BR regions to match pipeline scope.
    Articles that fail all retries are marked as failed and removed from processing queues.
    
    Args:
        max_attempts: Maximum attempts before marking as failed (default: 3)
    
    Returns:
        Dict with cleanup statistics
    """
    logger.info(f"Cleaning up failed pipeline articles (max_attempts: {max_attempts})")
    
    cleanup_stats = {
        'fetch_failures': 0,
        'process_failures': 0,
        'summarization_failures': 0,
        'analyzer_failures': 0,
        'total_cleaned': 0
    }
    
    # Define cleanup operations
    cleanup_operations = [
        ('fetch_failures', 'fetch_status', FetchStatus.PENDING, FetchStatus.FAILED, 'fetch_attempts'),
        ('process_failures', 'process_status', ProcessingStatus.PENDING, ProcessingStatus.FAILED, 'process_attempts'),
        ('summarization_failures', 'summarization_status', SummarizationStatus.PENDING, SummarizationStatus.FAILED, 'summarization_attempts'),
        ('analyzer_failures', 'analyzer_status', AnalyzerStatus.PENDING, AnalyzerStatus.FAILED, 'analyzer_attempts'),
    ]
    
    try:
        with transaction.atomic():
            for stat_key, status_field, pending_status, failed_status, attempts_field in cleanup_operations:
                filter_kwargs = {
                    status_field: pending_status,
                    f'{attempts_field}__gte': max_attempts
                }
                update_kwargs = {status_field: failed_status}
                
                failures_count = _get_base_queryset().filter(**filter_kwargs).update(**update_kwargs)
                cleanup_stats[stat_key] = failures_count
            
            cleanup_stats['total_cleaned'] = sum(cleanup_stats[key] for key in cleanup_stats if key != 'total_cleaned')
        
        logger.info(f"Cleanup completed: {cleanup_stats['total_cleaned']} articles marked as failed (US/BR regions only)")
        return cleanup_stats
        
    except Exception as e:
        logger.exception(f"Cleanup failed: {str(e)}")
        cleanup_stats['error'] = str(e)
        return cleanup_stats


@shared_task  
def get_pipeline_status() -> Dict[str, Any]:
    """
    Get comprehensive status of the content enrichment pipeline.
    
    Returns statistics about articles in each stage of the pipeline,
    focusing on top headlines from the last 72 hours from US and BR regions (pipeline scope).
    """
    try:
        base_queryset = _get_base_queryset()
        
        # Define status queries for each stage
        status_queries = {
            'stage_1_pending': {'fetch_status': FetchStatus.PENDING, 'fetch_attempts__lt': MAX_RETRY_ATTEMPTS},
            'stage_1_processing': {'fetch_status': FetchStatus.FETCHING},
            'stage_1_completed': {'fetch_status': FetchStatus.COMPLETED},
            'stage_1_failed': {'fetch_status': FetchStatus.FAILED},
            
            'stage_2_pending': {'fetch_status': FetchStatus.COMPLETED, 'process_status': ProcessingStatus.PENDING, 'process_attempts__lt': MAX_RETRY_ATTEMPTS},
            'stage_2_processing': {'process_status': ProcessingStatus.PROCESSING},
            'stage_2_completed': {'process_status': ProcessingStatus.COMPLETED},
            'stage_2_failed': {'process_status': ProcessingStatus.FAILED},
            
            'stage_3_pending': {'process_status': ProcessingStatus.COMPLETED, 'summarization_status': SummarizationStatus.PENDING, 'summarization_attempts__lt': MAX_RETRY_ATTEMPTS},
            'stage_3_processing': {'summarization_status': SummarizationStatus.PROCESSING},
            'stage_3_completed': {'summarization_status': SummarizationStatus.COMPLETED},
            'stage_3_failed': {'summarization_status': SummarizationStatus.FAILED},
            
            'stage_4_pending': {'summarization_status': SummarizationStatus.COMPLETED, 'analyzer_status': AnalyzerStatus.PENDING, 'analyzer_attempts__lt': MAX_RETRY_ATTEMPTS},
            'stage_4_processing': {'analyzer_status': AnalyzerStatus.PROCESSING},
            'stage_4_completed': {'analyzer_status': AnalyzerStatus.COMPLETED},
            'stage_4_failed': {'analyzer_status': AnalyzerStatus.FAILED},
        }
        
        # Build pipeline status
        pipeline_status = {
            'timestamp': timezone.now().isoformat(),
            'time_window': f'{PIPELINE_TIME_WINDOW_HOURS}h',
            'target_regions': TARGET_REGION_CODES,
            'top_headlines_total': base_queryset.count(),
            'fully_processed': _count_fully_processed_headlines()
        }
        
        # Add counts for each stage
        for status_key, filters in status_queries.items():
            pipeline_status[status_key] = base_queryset.filter(**filters).count()
        
        # Calculate pipeline efficiency
        total_headlines = pipeline_status['top_headlines_total']
        fully_processed = pipeline_status['fully_processed']
        pipeline_status['completion_rate'] = (fully_processed / total_headlines * 100) if total_headlines > 0 else 0
        
        return pipeline_status
        
    except Exception as e:
        logger.exception(f"Failed to get pipeline status: {str(e)}")
        return {
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }


@shared_task
def retry_failed_pipeline_stages(stage: str = 'all', limit: int = 20) -> Dict[str, Any]:
    """
    Retry articles that failed in specific pipeline stages.
    
    Only retries top headlines from the last 72 hours from US and BR regions to match pipeline scope.
    
    Args:
        stage: Which stage to retry ('fetch', 'process', 'summarize', 'analyze', 'all')
        limit: Maximum number of articles to retry
    
    Returns:
        Dict with retry results
    """
    logger.info(f"Retrying failed pipeline stage: {stage} (limit: {limit})")
    
    retry_results = {
        'stage': stage,
        'retried': 0,
        'successful': 0,
        'failed': 0
    }
    
    # Define retry operations
    retry_operations = {
        'fetch': ('fetch_status', FetchStatus.FAILED, FetchStatus.PENDING, 'fetch_attempts'),
        'process': ('process_status', ProcessingStatus.FAILED, ProcessingStatus.PENDING, 'process_attempts'),
        'summarize': ('summarization_status', SummarizationStatus.FAILED, SummarizationStatus.PENDING, 'summarization_attempts'),
        'analyze': ('analyzer_status', AnalyzerStatus.FAILED, AnalyzerStatus.PENDING, 'analyzer_attempts'),
    }
    
    try:
        stages_to_retry = retry_operations.keys() if stage == 'all' else [stage]
        
        for stage_name in stages_to_retry:
            if stage_name not in retry_operations:
                continue
                
            status_field, failed_status, pending_status, attempts_field = retry_operations[stage_name]
            
            filter_kwargs = {
                status_field: failed_status,
                f'{attempts_field}__lt': MAX_RETRY_ATTEMPTS
            }
            update_kwargs = {status_field: pending_status}
            
            # Get IDs first, then update without slicing
            failed_article_ids = list(_get_base_queryset().filter(**filter_kwargs)[:limit].values_list('id', flat=True))
            
            if failed_article_ids:
                count = _get_base_queryset().filter(id__in=failed_article_ids).update(**update_kwargs)
                retry_results['retried'] += count
                logger.info(f"Reset {count} failed {stage_name} articles to pending")
        
        logger.info(f"Retry operation completed: {retry_results['retried']} articles reset to pending")
        return retry_results
        
    except Exception as e:
        logger.exception(f"Retry operation failed: {str(e)}")
        retry_results['error'] = str(e)
        return retry_results 


@shared_task
def process_top_headlines_pipeline_continuous(
    limit_per_stage: int = 50, 
    max_total_limit: int = 200
) -> Dict[str, Any]:
    """
    Continuous processing pipeline that ensures all articles reach completion.
    
    Unlike the original pipeline that queues async tasks for stages 3&4, this version
    processes all stages synchronously and waits for completion. It continues processing
    until all articles (within the 72h top-headline filter) are either completed or failed.
    
    Args:
        limit_per_stage: Maximum articles to process per stage per run
        max_total_limit: Maximum total articles to process in this run
    
    Returns:
        Dict with comprehensive processing results
    """
    logger.info(f"Starting continuous pipeline (limit_per_stage: {limit_per_stage}, max_total: {max_total_limit})")
    
    pipeline_start = timezone.now()
    results = {
        'pipeline_start': pipeline_start.isoformat(),
        'continuous_mode': True,
        'cycles_completed': 0,
        'total_articles_processed': 0,
        'articles_remaining': 0,
        'stage_results': []
    }
    
    try:
        total_processed = 0
        cycle = 0
        
        # Continue processing until no more articles need processing or hit limits
        while total_processed < max_total_limit:
            cycle += 1
            cycle_start = timezone.now()
            
            logger.info(f"Continuous pipeline cycle {cycle} starting")
            
            cycle_results = {
                'cycle': cycle,
                'cycle_start': cycle_start.isoformat(),
                'stage_1_fetch': None,
                'stage_2_process': None,
                'stage_3_summarize': None,
                'stage_4_analyze': None,
                'cycle_processed': 0
            }
            
            # Process each stage synchronously
            cycle_results['stage_1_fetch'] = _process_stage1_fetch_continuous(limit_per_stage)
            cycle_results['stage_2_process'] = _process_stage2_process_continuous(limit_per_stage)
            cycle_results['stage_3_summarize'] = _process_stage3_summarize_continuous(limit_per_stage)
            cycle_results['stage_4_analyze'] = _process_stage4_analyze_continuous(limit_per_stage)
            
            # Count articles processed in this cycle
            cycle_processed = sum([
                cycle_results['stage_1_fetch'].get('processed', 0),
                cycle_results['stage_2_process'].get('processed', 0),
                cycle_results['stage_3_summarize'].get('processed', 0),
                cycle_results['stage_4_analyze'].get('processed', 0)
            ])
            
            cycle_results['cycle_processed'] = cycle_processed
            cycle_results['cycle_duration_ms'] = int((timezone.now() - cycle_start).total_seconds() * 1000)
            
            total_processed += cycle_processed
            results['stage_results'].append(cycle_results)
            
            logger.info(f"Cycle {cycle} completed: {cycle_processed} articles processed")
            
            # If no articles were processed this cycle, we're done
            if cycle_processed == 0:
                logger.info("No articles processed this cycle - pipeline completion reached")
                break
            
            # Safety limit: max 10 cycles per run to prevent infinite loops
            if cycle >= 10:
                logger.warning("Reached maximum cycles limit (10) - stopping")
                break
        
        # Final statistics
        pipeline_end = timezone.now()
        results.update({
            'cycles_completed': cycle,
            'total_articles_processed': total_processed,
            'articles_remaining': _count_articles_needing_processing(),
            'pipeline_duration_ms': int((pipeline_end - pipeline_start).total_seconds() * 1000),
            'pipeline_end': pipeline_end.isoformat(),
            'completion_status': 'completed' if _count_articles_needing_processing() == 0 else 'partial'
        })
        
        logger.info(f"Continuous pipeline completed: {cycle} cycles, {total_processed} articles, "
                   f"{results['articles_remaining']} remaining")
        
        return results
        
    except Exception as e:
        logger.exception(f"Continuous pipeline failed: {str(e)}")
        results['pipeline_error'] = str(e)
        return results


@shared_task
def complete_remaining_articles_pipeline(
    aggressive_mode: bool = True,
    limit_per_stage: int = 100
) -> Dict[str, Any]:
    """
    Completion sweep pipeline that focuses on finishing all remaining articles.
    
    This task is designed to run every 30 minutes and aggressively process any
    articles that are still in intermediate stages, ensuring nothing gets left behind.
    
    Args:
        aggressive_mode: If True, processes larger batches and includes stuck articles
        limit_per_stage: Maximum articles to process per stage
    
    Returns:
        Dict with completion sweep results
    """
    logger.info(f"Starting completion sweep (aggressive: {aggressive_mode}, limit: {limit_per_stage})")
    
    sweep_start = timezone.now()
    
    # Check what's left to process
    articles_needing_processing = _count_articles_needing_processing()
    
    if articles_needing_processing == 0:
        logger.info("Completion sweep: No articles need processing - system fully caught up")
        return {
            'sweep_start': sweep_start.isoformat(),
            'articles_needing_processing': 0,
            'sweep_needed': False,
            'message': 'All articles completed - no sweep needed'
        }
    
    logger.info(f"Completion sweep: {articles_needing_processing} articles need processing")
    
    # Use the continuous pipeline with higher limits
    enhanced_limit = limit_per_stage * 2 if aggressive_mode else limit_per_stage
    max_total = enhanced_limit * 4  # Process up to 4x limit across all stages
    
    results = process_top_headlines_pipeline_continuous.apply(
        kwargs={
            'limit_per_stage': enhanced_limit,
            'max_total_limit': max_total
        }
    ).get()
    
    # Add completion sweep metadata
    results.update({
        'sweep_mode': 'aggressive' if aggressive_mode else 'normal',
        'initial_articles_needing_processing': articles_needing_processing,
        'final_articles_needing_processing': _count_articles_needing_processing(),
        'sweep_effectiveness': articles_needing_processing - _count_articles_needing_processing()
    })
    
    return results


# Helper functions for continuous processing

def _process_stage1_fetch_continuous(limit: int) -> Dict[str, Any]:
    """Stage 1 for continuous processing - same as original but with better logging."""
    return _process_stage1_fetch_top_headlines(limit)


def _process_stage2_process_continuous(limit: int) -> Dict[str, Any]:
    """Stage 2 for continuous processing - same as original but with better logging."""
    return _process_stage2_process_top_headlines(limit)


def _process_stage3_summarize_continuous(limit: int) -> Dict[str, Any]:
    """Stage 3 for continuous processing - SYNCHRONOUS version that waits for completion."""
    
    # Find top headlines ready for summarization
    ready_for_summarization = _get_base_queryset().filter(
        process_status=ProcessingStatus.COMPLETED,
        summarization_status=SummarizationStatus.PENDING,
        summarization_attempts__lt=MAX_RETRY_ATTEMPTS
    ).filter(
        # Must have processed content from Stage 2
        models.Q(clean_content__isnull=False, clean_content__regex=r'.{200,}') |
        models.Q(basic_content__isnull=False, basic_content__regex=r'.{200,}')
    ).order_by('published_at')[:limit]
    
    article_ids = list(ready_for_summarization.values_list('id', flat=True))
    
    if not article_ids:
        logger.info("Continuous Stage 3: No articles ready for summarization")
        return {'processed': 0, 'successful': 0, 'failed': 0, 'message': 'No articles ready for summarization'}
    
    logger.info(f"Continuous Stage 3: Processing {len(article_ids)} articles for summarization")
    
    # SYNCHRONOUS processing - wait for completion
    from apps.content.summariser.tasks import batch_summarize_articles as summarize_func
    result = summarize_func(article_ids, force_regenerate=False)
    
    logger.info(f"Continuous Stage 3 completed: {result}")
    return result


def _process_stage4_analyze_continuous(limit: int) -> Dict[str, Any]:
    """Stage 4 for continuous processing - SYNCHRONOUS version that waits for completion."""
    
    # Find top headlines ready for analysis
    ready_for_analysis = _get_base_queryset().filter(
        summarization_status=SummarizationStatus.COMPLETED,
        analyzer_status=AnalyzerStatus.PENDING,
        analyzer_attempts__lt=MAX_RETRY_ATTEMPTS
    ).filter(
        # Must have summarized content from Stage 3
        models.Q(clean_content__isnull=False, clean_content__regex=r'.{200,}') |
        models.Q(basic_content__isnull=False, basic_content__regex=r'.{200,}')
    ).order_by('published_at')[:limit]
    
    article_ids = list(ready_for_analysis.values_list('id', flat=True))
    
    if not article_ids:
        logger.info("Continuous Stage 4: No articles ready for analysis")
        return {'processed': 0, 'successful': 0, 'failed': 0, 'message': 'No articles ready for analysis'}
    
    logger.info(f"Continuous Stage 4: Processing {len(article_ids)} articles for analysis")
    
    # SYNCHRONOUS processing - wait for completion
    from apps.content.analyzer.tasks import batch_analyze_articles as analyze_func
    result = analyze_func(article_ids, force_regenerate=False)
    
    logger.info(f"Continuous Stage 4 completed: {result}")
    return result


def _count_articles_needing_processing() -> int:
    """Count total articles that still need processing in any stage."""
    base_queryset = _get_base_queryset()
    
    # Articles needing each stage (excluding failed ones)
    stage1_needed = base_queryset.filter(
        fetch_status=FetchStatus.PENDING,
        fetch_attempts__lt=MAX_RETRY_ATTEMPTS
    ).count()
    
    stage2_needed = base_queryset.filter(
        fetch_status=FetchStatus.COMPLETED,
        process_status=ProcessingStatus.PENDING,
        process_attempts__lt=MAX_RETRY_ATTEMPTS
    ).count()
    
    stage3_needed = base_queryset.filter(
        process_status=ProcessingStatus.COMPLETED,
        summarization_status=SummarizationStatus.PENDING,
        summarization_attempts__lt=MAX_RETRY_ATTEMPTS
    ).count()
    
    stage4_needed = base_queryset.filter(
        summarization_status=SummarizationStatus.COMPLETED,
        analyzer_status=AnalyzerStatus.PENDING,
        analyzer_attempts__lt=MAX_RETRY_ATTEMPTS
    ).count()
    
    return stage1_needed + stage2_needed + stage3_needed + stage4_needed 