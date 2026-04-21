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
    BrowserSimulationStrategy,
    AdvancedBypassStrategy,
    PaywallBypassStrategy,
    BeautifulSoupStrategy
)
from .utils import normalize_url, validate_url

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
            BrowserSimulationStrategy(),  # Primary strategy - realistic browser simulation
            AdvancedBypassStrategy(),     # Advanced techniques for restrictive sites
            PaywallBypassStrategy(),      # Crawler bots for paywalls  
            BeautifulSoupStrategy()       # Fallback - basic requests
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
        
        # Normalize URL before fetching (handle Unicode escapes, remove tracking params)
        normalized_url = self._normalize_article_url(article)
        
        # Update fetch status to FETCHING
        self._update_fetch_status(article, FetchStatus.FETCHING)
        
        try:
            # Attempt extraction with available strategies using normalized URL
            extraction_result = self._extract_with_strategies(normalized_url)
            
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

            # Extract og:image and og:description from fetched HTML
            if result.raw_html:
                self._enrich_metadata_from_html(article, result.raw_html)

            article.save()

    def _enrich_metadata_from_html(self, article: Article, html: str):
        """
        Extract og:image and og:description from fetched HTML to enrich article metadata.
        Upgrades image_url if a higher quality source is found.
        """
        og_image = self._extract_og_tag(html, 'og:image')
        if og_image and og_image.startswith('http'):
            if self._should_upgrade_image(og_image, article.image_url):
                article.image_url = og_image[:1024]

        if not article.description:
            og_desc = self._extract_og_tag(html, 'og:description')
            if og_desc and len(og_desc) > 10:
                import html as html_mod
                article.description = html_mod.unescape(og_desc)[:500]

    @staticmethod
    def _extract_og_tag(html: str, property_name: str) -> str | None:
        """Extract an Open Graph meta tag value from raw HTML."""
        from bs4 import BeautifulSoup
        import re as _re

        # Parse HTML properly first so tag-attribute ordering doesn't matter.
        try:
            soup = BeautifulSoup(html[:100000], 'html.parser')
            wanted = property_name.lower()
            for tag in soup.find_all('meta'):
                prop = (tag.get('property') or tag.get('name') or '').strip().lower()
                if prop == wanted:
                    content = (tag.get('content') or '').strip()
                    if content:
                        return content
        except Exception:
            # Fall through to regex fallback.
            pass

        patterns = [
            rf'property="{property_name}"\s+content="([^"]+)"',
            rf'content="([^"]+)"\s+property="{property_name}"',
            rf"property='{property_name}'\s+content='([^']+)'",
            rf"content='([^']+)'\s+property='{property_name}'",
        ]
        for pattern in patterns:
            match = _re.search(pattern, html[:50000], _re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None

    @staticmethod
    def _should_upgrade_image(new_url: str, current_url: str | None) -> bool:
        """Determine if a new image URL is better than the current one."""
        if not current_url:
            return True
        # BBC low-res thumbnails
        if '/standard/240/' in current_url:
            return True
        # NYT cropped square thumbnails
        if 'mediumSquare' in current_url:
            return True
        # Empty or placeholder
        if len(current_url) < 10:
            return True
        return False
    
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
    
    def _normalize_article_url(self, article: Article) -> str:
        """
        Normalize article URL and update the database if changed.
        Handles Unicode escapes, removes tracking parameters, etc.
        
        Args:
            article: Article instance
            
        Returns:
            str: Normalized URL
        """
        original_url = article.url
        normalized_url = normalize_url(original_url)
        
        # Update article URL in database if it changed
        if original_url != normalized_url:
            logger.info(f"Article {article.id}: Normalizing URL")
            logger.debug(f"  Original:  {original_url}")
            logger.debug(f"  Normalized: {normalized_url}")
            
            with transaction.atomic():
                article.url = normalized_url
                article.save(update_fields=['url'])
        
        # Validate the normalized URL
        if not validate_url(normalized_url):
            logger.warning(f"Article {article.id}: Normalized URL is still invalid: {normalized_url}")
        
        return normalized_url
    
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
