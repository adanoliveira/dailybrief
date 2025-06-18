"""
Content Enrichment Pipeline Tasks

Orchestrates the 4-stage content pipeline for articles, specifically targeting 
top headlines from the last 72 hours that come from the sync-top-headlines task.

Pipeline Flow:
1. Fetcher → Extract raw content from article URLs
2. Processor → Clean and structure content using AI
3. Summariser → Generate headlines and abstracts
4. Analyzer → Extract entities, topics, and metadata

Scope: Only processes top headlines published within the last 72 hours.
Each stage processes articles ready for that stage and moves them to the next queue.
Max retries: 3 per stage before removing from queue.
Uses existing batch tasks from individual content apps (fetcher, processor, summariser, analyzer).
"""

import logging
from typing import List, Dict, Any, Optional
from celery import shared_task, chain, group
from django.db import models, transaction
from django.utils import timezone
from datetime import timedelta

from apps.articles.models import Article, FetchStatus, ProcessingStatus, SummarizationStatus, AnalyzerStatus

# Import task functions from each stage
from apps.content.fetcher.tasks import fetch_pending_articles, fetch_batch_articles
from apps.content.processor.tasks import process_pending_articles, process_batch_articles
from apps.content.summariser.tasks import process_pending_summarizations, batch_summarize_articles
from apps.content.analyzer.tasks import process_pending_analysis, batch_analyze_articles

logger = logging.getLogger(__name__)


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
        stage1_result = _process_stage1_fetch_top_headlines(limit)
        results['stage_1_fetch'] = stage1_result
        
        # STAGE 2: PROCESS - Process articles with fetched content 
        logger.info("Pipeline Stage 2: Processing content for top headlines")
        stage2_result = _process_stage2_process_top_headlines(limit)
        results['stage_2_process'] = stage2_result
        
        # STAGE 3: SUMMARIZE - Summarize articles with processed content
        logger.info("Pipeline Stage 3: Summarizing content for top headlines")
        stage3_result = _process_stage3_summarize_top_headlines(limit)
        results['stage_3_summarize'] = stage3_result
        
        # STAGE 4: ANALYZE - Analyze articles with summaries
        logger.info("Pipeline Stage 4: Analyzing content for top headlines")
        stage4_result = _process_stage4_analyze_top_headlines(limit)
        results['stage_4_analyze'] = stage4_result
        
        # Calculate pipeline summary
        pipeline_end = timezone.now()
        pipeline_duration = (pipeline_end - pipeline_start).total_seconds() * 1000
        
        # Count total articles that moved through pipeline
        total_processed = sum([
            stage1_result.get('processed', 0),
            stage2_result.get('processed', 0), 
            stage3_result.get('processed', 0),
            stage4_result.get('processed', 0)
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
    
    # Only process headlines from the last 72 hours
    time_threshold = timezone.now() - timedelta(hours=72)
    
    # Find top headlines that need fetching
    pending_fetch = Article.objects.filter(
        is_top_headline=True,
        published_at__gte=time_threshold,  # Only last 72 hours
        fetch_status=FetchStatus.PENDING,
        fetch_attempts__lt=3  # Max retry limit
    ).order_by('published_at')[:limit]
    
    if not pending_fetch:
        logger.info("No top headlines need fetching")
        return {'processed': 0, 'successful': 0, 'failed': 0, 'message': 'No articles need fetching'}
    
    # Process in batch for efficiency
    article_ids = list(pending_fetch.values_list('id', flat=True))
    logger.info(f"Stage 1: Processing {len(article_ids)} top headlines for fetching")
    
    # Use existing batch fetch task - call directly for synchronous execution
    from apps.content.fetcher.tasks import fetch_batch_articles as fetch_func
    return fetch_func(article_ids)


def _process_stage2_process_top_headlines(limit: int) -> Dict[str, Any]:
    """Stage 2: Process top headlines that have been fetched."""
    
    # Only process headlines from the last 72 hours
    time_threshold = timezone.now() - timedelta(hours=72)
    
    # Find top headlines ready for processing 
    ready_for_processing = Article.objects.filter(
        is_top_headline=True,
        published_at__gte=time_threshold,  # Only last 72 hours
        fetch_status=FetchStatus.COMPLETED,
        process_status=ProcessingStatus.PENDING,
        process_attempts__lt=3  # Max retry limit
    ).filter(
        # Must have content from Stage 1
        models.Q(raw_html__isnull=False, raw_html__regex=r'.{100,}') |
        models.Q(basic_content__isnull=False, basic_content__regex=r'.{50,}')
    ).order_by('published_at')[:limit]
    
    if not ready_for_processing:
        logger.info("No top headlines ready for processing")
        return {'processed': 0, 'successful': 0, 'failed': 0, 'message': 'No articles ready for processing'}
    
    # Process in batch with AI processing
    article_ids = list(ready_for_processing.values_list('id', flat=True))
    logger.info(f"Stage 2: Processing {len(article_ids)} top headlines for AI processing")
    
    # Use existing batch process task - call directly for synchronous execution
    from apps.content.processor.tasks import process_batch_articles as process_func
    return process_func(article_ids)


def _process_stage3_summarize_top_headlines(limit: int) -> Dict[str, Any]:
    """Stage 3: Summarize top headlines that have been processed."""
    
    # Only process headlines from the last 72 hours
    time_threshold = timezone.now() - timedelta(hours=72)
    
    # Find top headlines ready for summarization
    ready_for_summarization = Article.objects.filter(
        is_top_headline=True,
        published_at__gte=time_threshold,  # Only last 72 hours
        process_status=ProcessingStatus.COMPLETED,
        summarization_status=SummarizationStatus.PENDING,
        summarization_attempts__lt=3  # Max retry limit
    ).filter(
        # Must have processed content from Stage 2
        models.Q(clean_content__isnull=False, clean_content__regex=r'.{200,}') |
        models.Q(basic_content__isnull=False, basic_content__regex=r'.{200,}')
    ).order_by('published_at')[:limit]
    
    if not ready_for_summarization:
        logger.info("No top headlines ready for summarization")
        return {'processed': 0, 'successful': 0, 'failed': 0, 'message': 'No articles ready for summarization'}
    
    # Process in batch
    article_ids = list(ready_for_summarization.values_list('id', flat=True))
    logger.info(f"Stage 3: Processing {len(article_ids)} top headlines for summarization")
    
    # Use existing batch summarize task - queue async and return summary
    result = batch_summarize_articles.delay(article_ids, force_regenerate=False)
    logger.info(f"Stage 3: Queued {len(article_ids)} articles for summarization")
    
    # Return immediate summary since we can't wait for async result
    return {
        'processed': len(article_ids),
        'successful': 0,  # Will be updated when task completes
        'failed': 0,
        'message': f'Queued {len(article_ids)} articles for summarization'
    }


def _process_stage4_analyze_top_headlines(limit: int) -> Dict[str, Any]:
    """Stage 4: Analyze top headlines that have been summarized."""
    
    # Only process headlines from the last 72 hours
    time_threshold = timezone.now() - timedelta(hours=72)
    
    # Find top headlines ready for analysis
    ready_for_analysis = Article.objects.filter(
        is_top_headline=True,
        published_at__gte=time_threshold,  # Only last 72 hours
        summarization_status=SummarizationStatus.COMPLETED,
        analyzer_status=AnalyzerStatus.PENDING,
        analyzer_attempts__lt=3  # Max retry limit
    ).filter(
        # Must have summarized content from Stage 3
        models.Q(clean_content__isnull=False, clean_content__regex=r'.{200,}') |
        models.Q(basic_content__isnull=False, basic_content__regex=r'.{200,}')
    ).order_by('published_at')[:limit]
    
    if not ready_for_analysis:
        logger.info("No top headlines ready for analysis")
        return {'processed': 0, 'successful': 0, 'failed': 0, 'message': 'No articles ready for analysis'}
    
    # Process in batch
    article_ids = list(ready_for_analysis.values_list('id', flat=True))
    logger.info(f"Stage 4: Processing {len(article_ids)} top headlines for analysis")
    
    # Use existing batch analyze task - queue async and return summary
    result = batch_analyze_articles.delay(article_ids, force_regenerate=False)
    logger.info(f"Stage 4: Queued {len(article_ids)} articles for analysis")
    
    # Return immediate summary since we can't wait for async result
    return {
        'processed': len(article_ids),
        'successful': 0,  # Will be updated when task completes
        'failed': 0,
        'message': f'Queued {len(article_ids)} articles for analysis'
    }


def _count_fully_processed_headlines() -> int:
    """Count top headlines from last 72h that have completed all 4 pipeline stages."""
    time_threshold = timezone.now() - timedelta(hours=72)
    return Article.objects.filter(
        is_top_headline=True,
        published_at__gte=time_threshold,  # Only last 72 hours
        fetch_status=FetchStatus.COMPLETED,
        process_status=ProcessingStatus.COMPLETED,
        summarization_status=SummarizationStatus.COMPLETED,
        analyzer_status=AnalyzerStatus.COMPLETED
    ).count()


@shared_task
def cleanup_failed_pipeline_articles(max_attempts: int = 3) -> Dict[str, Any]:
    """
    Clean up articles that have exceeded max retry attempts in any pipeline stage.
    
    Only cleans up top headlines from the last 72 hours to match pipeline scope.
    Articles that fail all retries are marked as failed and removed from processing queues.
    
    Args:
        max_attempts: Maximum attempts before marking as failed (default: 3)
    
    Returns:
        Dict with cleanup statistics
    """
    logger.info(f"Cleaning up failed pipeline articles (max_attempts: {max_attempts})")
    
    # Only clean up recent headlines (last 72 hours)
    time_threshold = timezone.now() - timedelta(hours=72)
    
    cleanup_stats = {
        'fetch_failures': 0,
        'process_failures': 0,
        'summarization_failures': 0,
        'analyzer_failures': 0,
        'total_cleaned': 0
    }
    
    try:
        with transaction.atomic():
            # Clean up Stage 1 failures
            fetch_failures = Article.objects.filter(
                is_top_headline=True,
                published_at__gte=time_threshold,  # Only last 72 hours
                fetch_status=FetchStatus.PENDING,
                fetch_attempts__gte=max_attempts
            ).update(fetch_status=FetchStatus.FAILED)
            cleanup_stats['fetch_failures'] = fetch_failures
            
            # Clean up Stage 2 failures  
            process_failures = Article.objects.filter(
                is_top_headline=True,
                published_at__gte=time_threshold,  # Only last 72 hours
                process_status=ProcessingStatus.PENDING,
                process_attempts__gte=max_attempts
            ).update(process_status=ProcessingStatus.FAILED)
            cleanup_stats['process_failures'] = process_failures
            
            # Clean up Stage 3 failures
            summarization_failures = Article.objects.filter(
                is_top_headline=True,
                published_at__gte=time_threshold,  # Only last 72 hours
                summarization_status=SummarizationStatus.PENDING,
                summarization_attempts__gte=max_attempts
            ).update(summarization_status=SummarizationStatus.FAILED)
            cleanup_stats['summarization_failures'] = summarization_failures
            
            # Clean up Stage 4 failures
            analyzer_failures = Article.objects.filter(
                is_top_headline=True,
                published_at__gte=time_threshold,  # Only last 72 hours
                analyzer_status=AnalyzerStatus.PENDING,
                analyzer_attempts__gte=max_attempts
            ).update(analyzer_status=AnalyzerStatus.FAILED)
            cleanup_stats['analyzer_failures'] = analyzer_failures
            
            cleanup_stats['total_cleaned'] = sum([
                fetch_failures, process_failures, 
                summarization_failures, analyzer_failures
            ])
        
        logger.info(f"Cleanup completed: {cleanup_stats['total_cleaned']} articles marked as failed")
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
    focusing on top headlines from the last 72 hours (pipeline scope).
    """
    try:
        # Only track recent headlines (last 72 hours) - the pipeline scope
        time_threshold = timezone.now() - timedelta(hours=72)
        
        # Count articles in each pipeline stage
        pipeline_status = {
            'timestamp': timezone.now().isoformat(),
            'time_window': '72h',
            'top_headlines_total': Article.objects.filter(
                is_top_headline=True,
                published_at__gte=time_threshold
            ).count(),
            'stage_1_pending': Article.objects.filter(
                is_top_headline=True,
                published_at__gte=time_threshold,
                fetch_status=FetchStatus.PENDING,
                fetch_attempts__lt=3
            ).count(),
            'stage_1_processing': Article.objects.filter(
                is_top_headline=True,
                published_at__gte=time_threshold,
                fetch_status=FetchStatus.FETCHING
            ).count(),
            'stage_1_completed': Article.objects.filter(
                is_top_headline=True,
                published_at__gte=time_threshold,
                fetch_status=FetchStatus.COMPLETED
            ).count(),
            'stage_1_failed': Article.objects.filter(
                is_top_headline=True,
                published_at__gte=time_threshold,
                fetch_status=FetchStatus.FAILED
            ).count(),
            'stage_2_pending': Article.objects.filter(
                is_top_headline=True,
                published_at__gte=time_threshold,
                fetch_status=FetchStatus.COMPLETED,
                process_status=ProcessingStatus.PENDING,
                process_attempts__lt=3
            ).count(),
            'stage_2_processing': Article.objects.filter(
                is_top_headline=True,
                published_at__gte=time_threshold,
                process_status=ProcessingStatus.PROCESSING
            ).count(),
            'stage_2_completed': Article.objects.filter(
                is_top_headline=True,
                published_at__gte=time_threshold,
                process_status=ProcessingStatus.COMPLETED
            ).count(),
            'stage_2_failed': Article.objects.filter(
                is_top_headline=True,
                published_at__gte=time_threshold,
                process_status=ProcessingStatus.FAILED
            ).count(),
            'stage_3_pending': Article.objects.filter(
                is_top_headline=True,
                published_at__gte=time_threshold,
                process_status=ProcessingStatus.COMPLETED,
                summarization_status=SummarizationStatus.PENDING,
                summarization_attempts__lt=3
            ).count(),
            'stage_3_processing': Article.objects.filter(
                is_top_headline=True,
                published_at__gte=time_threshold,
                summarization_status=SummarizationStatus.PROCESSING
            ).count(),
            'stage_3_completed': Article.objects.filter(
                is_top_headline=True,
                published_at__gte=time_threshold,
                summarization_status=SummarizationStatus.COMPLETED
            ).count(),
            'stage_3_failed': Article.objects.filter(
                is_top_headline=True,
                published_at__gte=time_threshold,
                summarization_status=SummarizationStatus.FAILED
            ).count(),
            'stage_4_pending': Article.objects.filter(
                is_top_headline=True,
                published_at__gte=time_threshold,
                summarization_status=SummarizationStatus.COMPLETED,
                analyzer_status=AnalyzerStatus.PENDING,
                analyzer_attempts__lt=3
            ).count(),
            'stage_4_processing': Article.objects.filter(
                is_top_headline=True,
                published_at__gte=time_threshold,
                analyzer_status=AnalyzerStatus.PROCESSING
            ).count(),
            'stage_4_completed': Article.objects.filter(
                is_top_headline=True,
                published_at__gte=time_threshold,
                analyzer_status=AnalyzerStatus.COMPLETED
            ).count(),
            'stage_4_failed': Article.objects.filter(
                is_top_headline=True,
                published_at__gte=time_threshold,
                analyzer_status=AnalyzerStatus.FAILED
            ).count(),
            'fully_processed': _count_fully_processed_headlines()
        }
        
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
    
    Only retries top headlines from the last 72 hours to match pipeline scope.
    
    Args:
        stage: Which stage to retry ('fetch', 'process', 'summarize', 'analyze', 'all')
        limit: Maximum number of articles to retry
    
    Returns:
        Dict with retry results
    """
    logger.info(f"Retrying failed pipeline stage: {stage} (limit: {limit})")
    
    # Only retry recent headlines (last 72 hours)
    time_threshold = timezone.now() - timedelta(hours=72)
    
    retry_results = {
        'stage': stage,
        'retried': 0,
        'successful': 0,
        'failed': 0
    }
    
    try:
        if stage in ['fetch', 'all']:
            # Retry failed fetches with attempts < 3
            failed_fetch = Article.objects.filter(
                is_top_headline=True,
                published_at__gte=time_threshold,  # Only last 72 hours
                fetch_status=FetchStatus.FAILED,
                fetch_attempts__lt=3
            )[:limit]
            
            if failed_fetch:
                # Reset status to pending for retry
                failed_fetch.update(fetch_status=FetchStatus.PENDING)
                retry_results['retried'] += len(failed_fetch)
                logger.info(f"Reset {len(failed_fetch)} failed fetch articles to pending")
        
        if stage in ['process', 'all']:
            # Retry failed processing with attempts < 3
            failed_process = Article.objects.filter(
                is_top_headline=True,
                published_at__gte=time_threshold,  # Only last 72 hours
                process_status=ProcessingStatus.FAILED,
                process_attempts__lt=3
            )[:limit]
            
            if failed_process:
                failed_process.update(process_status=ProcessingStatus.PENDING)
                retry_results['retried'] += len(failed_process)
                logger.info(f"Reset {len(failed_process)} failed process articles to pending")
        
        if stage in ['summarize', 'all']:
            # Retry failed summarization with attempts < 3
            failed_summarize = Article.objects.filter(
                is_top_headline=True,
                published_at__gte=time_threshold,  # Only last 72 hours
                summarization_status=SummarizationStatus.FAILED,
                summarization_attempts__lt=3
            )[:limit]
            
            if failed_summarize:
                failed_summarize.update(summarization_status=SummarizationStatus.PENDING)
                retry_results['retried'] += len(failed_summarize)
                logger.info(f"Reset {len(failed_summarize)} failed summarization articles to pending")
        
        if stage in ['analyze', 'all']:
            # Retry failed analysis with attempts < 3
            failed_analyze = Article.objects.filter(
                is_top_headline=True,
                published_at__gte=time_threshold,  # Only last 72 hours
                analyzer_status=AnalyzerStatus.FAILED,
                analyzer_attempts__lt=3
            )[:limit]
            
            if failed_analyze:
                failed_analyze.update(analyzer_status=AnalyzerStatus.PENDING)
                retry_results['retried'] += len(failed_analyze)
                logger.info(f"Reset {len(failed_analyze)} failed analysis articles to pending")
        
        logger.info(f"Retry operation completed: {retry_results['retried']} articles reset to pending")
        return retry_results
        
    except Exception as e:
        logger.exception(f"Retry operation failed: {str(e)}")
        retry_results['error'] = str(e)
        return retry_results 