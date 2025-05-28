"""
Fast Content Fetcher Service - Step 1 Only
Optimized for speed and raw content extraction without processing.
"""

import time
import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from django.db import transaction
from django.utils import timezone
from django.conf import settings

from apps.articles.models import Article, FetchStatus
from .extraction import (
    ExtractionResult, 
    ExtractionStrategy,
    PaywallBypassStrategy,
    BeautifulSoupStrategy
)

logger = logging.getLogger(__name__)


@dataclass
class FetchResult:
    """Result of fast content fetching operation."""
    success: bool
    article: Optional[Article] = None
    error_message: str = ""
    extraction_result: Optional[ExtractionResult] = None
    duration_ms: int = 0
    strategy_used: str = ""


class ContentFetcher:
    """
    Fast content fetcher optimized for Step 1 extraction.
    Focuses on speed over processing quality.
    """
    
    def __init__(self):
        self.strategies = [
            PaywallBypassStrategy(),
            BeautifulSoupStrategy()
        ]
        
        # Performance settings
        self.timeout_seconds = getattr(settings, 'FAST_FETCH_TIMEOUT', 10)
        self.max_retries = getattr(settings, 'FAST_FETCH_MAX_RETRIES', 2)
        self.user_agent = getattr(settings, 'FAST_FETCH_USER_AGENT', 
                                'Mozilla/5.0 (compatible; DailyBrief/1.0)')
    
    def fetch_article_content(self, article: Article) -> FetchResult:
        """
        Fast content fetching for a single article.
        Only performs Step 1 extraction - no processing.
        """
        
        start_time = time.time()
        
        # Validate article needs fetching
        if not article.needs_fetch:
            return FetchResult(
                success=False,
                article=article,
                error_message=f"Article doesn't need fetching. Status: {article.fetch_status}"
            )
        
        # Update fetch status to FETCHING
        self._update_fetch_status(article, FetchStatus.FETCHING)
        
        try:
            # Attempt extraction with available strategies
            extraction_result = self._extract_with_strategies(article.url)
            
            if extraction_result.success:
                # Store extraction results
                self._store_extraction_results(article, extraction_result)
                
                # Update status to COMPLETED
                self._update_fetch_status(article, FetchStatus.COMPLETED)
                
                # Queue for Step 2 processing
                self._queue_for_processing(article)
                
                duration_ms = int((time.time() - start_time) * 1000)
                
                return FetchResult(
                    success=True,
                    article=article,
                    extraction_result=extraction_result,
                    duration_ms=duration_ms,
                    strategy_used=extraction_result.strategy_used
                )
            else:
                # Handle extraction failure
                return self._handle_fetch_error(article, extraction_result.error_message, start_time)
                
        except Exception as e:
            logger.exception(f"Fast fetch failed for article {article.id}: {str(e)}")
            return self._handle_fetch_error(article, str(e), start_time)
    
    def fetch_multiple_articles(self, articles: List[Article]) -> List[FetchResult]:
        """
        Fetch content for multiple articles efficiently.
        """
        results = []
        
        for article in articles:
            if article.needs_fetch:
                result = self.fetch_article_content(article)
                results.append(result)
            else:
                results.append(FetchResult(
                    success=False,
                    article=article,
                    error_message="Article doesn't need fetching"
                ))
        
        return results
    
    def _extract_with_strategies(self, url: str) -> ExtractionResult:
        """
        Attempt extraction using available strategies in order.
        """
        
        for strategy in self.strategies:
            if not strategy.available:
                continue
                
            try:
                logger.info(f"Attempting fast extraction with {strategy.name} for {url}")
                
                result = strategy.extract(url)
                
                if result.success:
                    logger.info(f"Fast extraction successful with {strategy.name}")
                    return result
                else:
                    logger.warning(f"Fast extraction failed with {strategy.name}: {result.error_message}")
                    
            except Exception as e:
                logger.exception(f"Strategy {strategy.name} failed: {str(e)}")
                continue
        
        # All strategies failed
        return ExtractionResult(
            success=False,
            error_message="All extraction strategies failed",
            strategy_used="none"
        )
    
    def _store_extraction_results(self, article: Article, result: ExtractionResult):
        """
        Store extraction results in the article model.
        """
        
        with transaction.atomic():
            # Store raw content and basic info
            article.raw_html = result.raw_html
            article.basic_content = result.basic_content
            article.extraction_metadata = result.extraction_metadata
            
            # Update metadata if extracted
            if result.title and not article.title:
                article.title = result.title
            if result.author and not article.author:
                article.author = result.author
            
            # Store paywall detection results
            article.paywall_detected = result.paywall_detected
            article.paywall_indicators = result.paywall_indicators
            
            # Store extraction performance data
            article.fetch_strategy_used = result.strategy_used
            article.fetch_duration_ms = result.extraction_metadata.get('extraction_time_ms', 0)
            
            article.save()
    
    def _update_fetch_status(self, article: Article, status: FetchStatus):
        """
        Update article fetch status and related fields.
        """
        
        with transaction.atomic():
            article.fetch_status = status
            article.last_fetch_attempt = timezone.now()
            
            if status == FetchStatus.FETCHING:
                article.fetch_attempts += 1
            elif status == FetchStatus.FAILED:
                article.fetch_attempts += 1
            
            article.save()
    
    def _handle_fetch_error(self, article: Article, error_message: str, start_time: float) -> FetchResult:
        """
        Handle fetch errors and update article status.
        """
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        with transaction.atomic():
            article.fetch_status = FetchStatus.FAILED
            article.fetch_error_message = error_message
            article.fetch_attempts += 1
            article.last_fetch_attempt = timezone.now()
            article.save()
        
        return FetchResult(
            success=False,
            article=article,
            error_message=error_message,
            duration_ms=duration_ms
        )
    
    def _queue_for_processing(self, article: Article):
        """
        Queue article for Step 2 processing.
        """
        try:
            # Import here to avoid circular imports
            from apps.content.processor.tasks import process_article_content
            
            # Queue with small delay to allow for batching
            process_article_content.apply_async(
                args=[article.id],
                countdown=30  # 30 second delay for batching
            )
            
            logger.info(f"Queued article {article.id} for Step 2 processing")
            
        except ImportError:
            logger.warning("Step 2 processing not available - processor app not found")
        except Exception as e:
            logger.error(f"Failed to queue article {article.id} for processing: {str(e)}")
    
    def get_fetch_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about fetch performance.
        """
        
        from django.db.models import Count, Avg, Q
        from datetime import timedelta
        
        # Get stats for last 24 hours
        since = timezone.now() - timedelta(hours=24)
        
        stats = Article.objects.filter(
            last_fetch_attempt__gte=since
        ).aggregate(
            total_attempts=Count('id'),
            successful_fetches=Count('id', filter=Q(fetch_status=FetchStatus.COMPLETED)),
            failed_fetches=Count('id', filter=Q(fetch_status=FetchStatus.FAILED)),
            avg_duration=Avg('fetch_duration_ms'),
            paywall_detected_count=Count('id', filter=Q(paywall_detected=True))
        )
        
        # Calculate success rate
        total = stats['total_attempts'] or 0
        successful = stats['successful_fetches'] or 0
        stats['success_rate'] = (successful / total * 100) if total > 0 else 0
        
        # Get strategy usage
        strategy_stats = Article.objects.filter(
            last_fetch_attempt__gte=since,
            fetch_status=FetchStatus.COMPLETED
        ).values('fetch_strategy_used').annotate(
            count=Count('id')
        ).order_by('-count')
        
        stats['strategy_usage'] = list(strategy_stats)
        
        return stats


class FetchManager:
    """
    Manager for coordinating fetch operations across multiple articles.
    """
    
    def __init__(self):
        self.fetcher = ContentFetcher()
    
    def fetch_pending_articles(self, limit: int = 50) -> Dict[str, Any]:
        """
        Fetch content for pending articles in batches.
        """
        
        # Get articles that need fetching
        pending_articles = Article.objects.filter(
            fetch_status=FetchStatus.PENDING,
            fetch_attempts__lt=3
        ).order_by('published_at')[:limit]
        
        if not pending_articles:
            return {
                'processed': 0,
                'successful': 0,
                'failed': 0,
                'message': 'No pending articles to fetch'
            }
        
        # Fetch content for articles
        results = self.fetcher.fetch_multiple_articles(list(pending_articles))
        
        # Compile statistics
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful
        
        return {
            'processed': len(results),
            'successful': successful,
            'failed': failed,
            'results': results
        }
    
    def retry_failed_articles(self, max_retries: int = 3) -> Dict[str, Any]:
        """
        Retry fetching for failed articles that haven't exceeded max attempts.
        """
        
        failed_articles = Article.objects.filter(
            fetch_status=FetchStatus.FAILED,
            fetch_attempts__lt=max_retries
        ).order_by('last_fetch_attempt')[:20]  # Limit retries
        
        if not failed_articles:
            return {
                'processed': 0,
                'successful': 0,
                'failed': 0,
                'message': 'No failed articles to retry'
            }
        
        # Reset status to pending for retry
        for article in failed_articles:
            article.fetch_status = FetchStatus.PENDING
            article.save()
        
        # Fetch content
        results = self.fetcher.fetch_multiple_articles(list(failed_articles))
        
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful
        
        return {
            'processed': len(results),
            'successful': successful,
            'failed': failed,
            'results': results
        } 