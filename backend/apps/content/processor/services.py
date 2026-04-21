"""
Main Content Processor Service - Step 2 Processing
Coordinates between Safari mode and LLM processing based on intelligent routing.
"""

import time
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from django.db import transaction
from django.utils import timezone
from django.conf import settings

from apps.articles.models import Article, ProcessingStatus, FetchStatus
from .routing import ProcessingRouter, ComplexityAnalysis
from .algorithmic_processor import AlgorithmicProcessor, ProcessingResult
from .ai_processor import AIContentProcessor
from .rss_processor import process_rss_content

RSS_MIN_CONTENT_LENGTH = 200

logger = logging.getLogger(__name__)


def _truncate_route_name(route: str) -> str:
    """
    Truncate route name to 20 characters to fit DB field constraint.
    
    Args:
        route: Route name string
        
    Returns:
        Truncated route name (max 20 chars)
    """
    if not route:
        return ""
    return route[:20] if len(route) > 20 else route


def _ensure_timezone_aware(dt):
    """Ensure datetime is timezone-aware for proper storage."""
    if dt and hasattr(timezone, 'is_aware') and not timezone.is_aware(dt):
        return timezone.make_aware(dt)
    return dt


@dataclass
class ProcessResult:
    """Result of content processing operation."""
    success: bool
    article: Optional[Article] = None
    processing_result: Optional[ProcessingResult] = None
    route_used: str = ""
    duration_ms: int = 0
    cost_usd: float = 0.0
    error_message: str = ""


class ContentProcessor:
    """
    Main content processor that coordinates different processing strategies.
    Routes content through Safari mode, LLM enhanced, or hybrid processing.
    """
    
    def __init__(self):
        self.router = ProcessingRouter()
        self.algorithmic_processor = AlgorithmicProcessor()
        self.llm_processor = AIContentProcessor()  # Use the existing AI processor
        
        # Processing settings
        self.max_attempts = getattr(settings, 'CONTENT_PROCESS_MAX_ATTEMPTS', 3)
        self.timeout_seconds = getattr(settings, 'CONTENT_PROCESS_TIMEOUT', 60)
    
    def _resolve_content_for_processing(self, article):
        """
        Resolve the best available content for processing.

        Priority:
        1. raw_html — full page HTML from fetcher (BrowserSimulation, etc.)
        2. content — HTML from RSS content:encoded (when fetch was skipped)
        3. basic_content — fallback, RSS content or partial extraction

        Returns (content_string, source_label) or (None, None).
        """
        if article.raw_html:
            return article.raw_html, 'raw_html'
        if article.content and len(article.content) > RSS_MIN_CONTENT_LENGTH:
            return article.content, 'rss_content'
        if article.basic_content and len(article.basic_content) > RSS_MIN_CONTENT_LENGTH:
            return article.basic_content, 'basic_content'
        return None, None

    def process_article_content(self, article, route: str = None) -> ProcessingResult:
        """
        Process article content using intelligent routing or specified route.

        Args:
            article: Article instance with raw_html, content, or basic_content
            route: Optional route override ('algorithmic', 'llm_enhanced', 'hybrid', 'rss_direct')

        Returns:
            ProcessingResult with processed content
        """

        content, content_source = self._resolve_content_for_processing(article)

        if not content:
            return ProcessingResult(
                success=False,
                error_message="No usable content available for processing"
            )

        # RSS feeds that delivered the full body already skipped the fetcher.
        # Top headlines get LLM processing for digest quality; others use local regex.
        if content_source in ('rss_content', 'basic_content') and not article.raw_html:
            if article.is_top_headline:
                logger.info(
                    f"Using LLM for top-headline RSS-direct article {article.id} "
                    f"(source={content_source})"
                )
                return self._process_rss_content_with_llm(article, content)
            logger.info(
                f"Using rss_direct route for article {article.id} "
                f"(source={content_source}, no raw_html)"
            )
            return self._process_rss_content(article, content)

        # Always use AI processor for raw_html path
        if not route:
            route = 'llm_enhanced'
            logger.info(f"Auto-selected AI processing route for article {article.id}")
        else:
            logger.info(f"Using specified route '{route}' for article {article.id}")

        # Process based on route (always use LLM enhanced for now)
        if route == 'rss_direct':
            return self._process_rss_content(article, content)
        elif route == 'algorithmic':
            logger.info(f"Overriding algorithmic route to use AI processing for article {article.id}")
            return self._process_llm_enhanced_mode(article)
        elif route == 'llm_enhanced':
            return self._process_llm_enhanced_mode(article)
        elif route == 'hybrid':
            logger.info(f"Overriding hybrid route to use AI processing for article {article.id}")
            return self._process_llm_enhanced_mode(article)
        else:
            logger.warning(f"Unknown route '{route}', using AI processing for article {article.id}")
            return self._process_llm_enhanced_mode(article)

    def _process_rss_content(self, article, html_content) -> ProcessingResult:
        """
        Process RSS-delivered article content without calling the LLM.

        RSS content:encoded is already the article body, so we just need to clean,
        structure, and validate it locally. Produces blocks/clean_content compatible
        with the rest of the pipeline (summarizer, analyzer).
        """
        logger.info(f"Processing article {article.id} via rss_direct route")

        result = process_rss_content(html_content, base_url=article.url or None)

        if result.success:
            logger.info(
                f"RSS direct processing successful for article {article.id}, "
                f"blocks: {len(result.content_blocks)}, quality: {result.quality_score}"
            )
        else:
            logger.warning(
                f"RSS direct processing failed for article {article.id}: {result.error_message}"
            )

        return result

    def _process_rss_content_with_llm(self, article, html_content) -> ProcessingResult:
        """
        Process RSS-delivered content through the LLM processor for higher quality.

        Used for top-headline RSS-direct articles that deserve LLM-quality
        content blocks for digest generation. Passes the RSS HTML content
        to the LLM processor (which normally reads article.raw_html).
        """
        logger.info(f"Processing article {article.id} via rss_llm_enhanced route")

        article_metadata = {
            'title': article.title,
            'author': article.author,
            'source_name': article.source_name,
            'published_at': _ensure_timezone_aware(article.published_at).isoformat() if article.published_at else None,
            'paywall_detected': False,
            'paywall_indicators': [],
        }

        result = self.llm_processor.process_content(
            html_content, article_metadata, base_url=article.url
        )

        if result.success:
            logger.info(
                f"RSS LLM processing successful for article {article.id}, "
                f"quality: {result.quality_score:.3f}"
            )
        else:
            # Fall back to regex processing if LLM fails
            logger.warning(
                f"RSS LLM processing failed for article {article.id}, "
                f"falling back to rss_direct: {result.error_message}"
            )
            result = process_rss_content(html_content, base_url=article.url or None)

        return result

    def _process_algorithmic_mode(self, article) -> ProcessingResult:
        """
        Process content using algorithmic (Safari-like) mode.
        Fast, reliable, low-cost processing.
        """
        
        logger.info(f"Processing article {article.id} with algorithmic mode")
        
        # Prepare article metadata
        article_metadata = {
            'title': article.title,
            'author': article.author,
            'published_date': _ensure_timezone_aware(article.published_at),
            'source_name': article.source_name,
            'url': article.url
        }
        
        # Process with algorithmic processor
        result = self.algorithmic_processor.process_content(article.raw_html, article_metadata)
        
        if result.success:
            logger.info(f"Algorithmic processing successful for article {article.id}, "
                       f"quality: {result.quality_score}, time: {result.processing_time_ms}ms")
        else:
            logger.error(f"Algorithmic processing failed for article {article.id}: {result.error_message}")
        
        return result
    
    def _process_llm_enhanced_mode(self, article) -> ProcessingResult:
        """
        Process content using LLM enhancement.
        """
        
        logger.info(f"Processing article {article.id} with LLM enhancement")
        
        # Get article metadata for processing
        article_metadata = {
            'title': article.title,
            'author': article.author,
            'source_name': article.source_name,
            'published_at': _ensure_timezone_aware(article.published_at).isoformat() if article.published_at else None,
            'paywall_detected': article.paywall_detected,
            'paywall_indicators': article.paywall_indicators
        }
        
        # Process with LLM enhancement
        result = self.llm_processor.process_content(article.raw_html, article_metadata, base_url=article.url)
        
        if result.success:
            logger.info(f"LLM processing successful for article {article.id}, "
                       f"quality: {result.quality_score:.3f}")
        else:
            logger.error(f"LLM processing failed for article {article.id}: {result.error_message}")
            
            # Instead of falling back to algorithmic, move back to fetch pending for retry
            # Only if we haven't exceeded max attempts
            if article.process_attempts < self.max_attempts:
                logger.info(f"Moving article {article.id} back to fetch pending for retry "
                           f"(attempt {article.process_attempts}/{self.max_attempts})")
                
                # Reset to fetch pending for retry
                article.fetch_status = FetchStatus.PENDING
                article.fetch_attempts = 0  # Reset fetch attempts to allow re-fetching
                article.fetch_error_message = ""  # Clear previous fetch errors
                article.process_error_message = result.error_message  # Keep AI processing error for debugging
                article.save(update_fields=[
                    'fetch_status', 
                    'fetch_attempts', 
                    'fetch_error_message', 
                    'process_error_message'
                ])
                
                # Return a special result indicating retry is needed
                return ProcessingResult(
                    success=False,
                    error_message=f"AI processing failed, moved to fetch pending for retry: {result.error_message}",
                    route_used="llm_retry_fetch",
                    processing_time_ms=result.processing_time_ms if hasattr(result, 'processing_time_ms') else 0
                )
            else:
                logger.warning(f"Article {article.id} has exceeded max attempts ({self.max_attempts}), "
                              f"marking as permanently failed")
                # If we've exceeded max attempts, mark as permanently failed
                return ProcessingResult(
                    success=False,
                    error_message=f"AI processing failed after {self.max_attempts} attempts: {result.error_message}",
                    route_used="llm_max_retry",
                    processing_time_ms=result.processing_time_ms if hasattr(result, 'processing_time_ms') else 0
                )
        
        return result
    
    def _process_hybrid_mode(self, article) -> ProcessingResult:
        """
        Process content using hybrid approach: algorithmic mode with LLM enhancement.
        """
        
        logger.info(f"Processing article {article.id} with hybrid approach")
        
        # Start with algorithmic mode processing
        algorithmic_result = self._process_algorithmic_mode(article)
        
        if not algorithmic_result.success:
            return algorithmic_result
        
        # Enhance with LLM if quality is below threshold or specific conditions are met
        should_enhance = (
            algorithmic_result.quality_score < 0.7 or
            article.paywall_detected or
            len(algorithmic_result.content_blocks) < 3
        )
        
        if should_enhance and self.llm_processor:
            logger.info(f"Enhancing algorithmic result with LLM for article {article.id}")
            
            # Use LLM to enhance specific elements
            enhanced_result = self._enhance_with_llm(article, algorithmic_result)
            
            if enhanced_result.success and enhanced_result.quality_score > algorithmic_result.quality_score:
                logger.info(f"LLM enhancement improved quality from {algorithmic_result.quality_score:.3f} "
                           f"to {enhanced_result.quality_score:.3f}")
                return enhanced_result
            else:
                logger.info(f"LLM enhancement did not improve quality, using algorithmic result")
        
        return algorithmic_result
    
    def _enhance_with_llm(self, article: Article, algorithmic_result: ProcessingResult) -> ProcessingResult:
        """
        Enhance algorithmic mode result with LLM processing for specific elements.
        """
        
        try:
            # Create enhanced metadata with algorithmic results
            enhanced_metadata = {
                'title': article.title,
                'author': article.author,
                'source_name': article.source_name,
                'published_at': _ensure_timezone_aware(article.published_at).isoformat() if article.published_at else None,
                'paywall_detected': article.paywall_detected,
                'algorithmic_quality': algorithmic_result.quality_score,
                'algorithmic_content_blocks': len(algorithmic_result.content_blocks),
                'enhancement_mode': True
            }
            
            # Process with LLM for enhancement
            llm_result = self.llm_processor.process_content(article.raw_html, enhanced_metadata, base_url=article.url)
            
            if llm_result.success:
                # Merge the best parts of both results
                merged_result = self._merge_processing_results(algorithmic_result, llm_result)
                return merged_result
            else:
                return algorithmic_result
                
        except Exception as e:
            logger.exception(f"LLM enhancement failed for article {article.id}: {str(e)}")
            return algorithmic_result
    
    def _merge_processing_results(self, algorithmic_result: ProcessingResult, llm_result: ProcessingResult) -> ProcessingResult:
        """
        Merge algorithmic mode and LLM processing results to get the best of both.
        """
        
        # Use LLM content if it's significantly better
        if llm_result.quality_score > algorithmic_result.quality_score + 0.1:
            base_result = llm_result
            fallback_result = algorithmic_result
        else:
            base_result = algorithmic_result
            fallback_result = llm_result
        
        # Merge metadata (take the more complete one)
        merged_metadata = base_result.extracted_metadata.copy()
        for key, value in fallback_result.extracted_metadata.items():
            if key not in merged_metadata or not merged_metadata[key]:
                merged_metadata[key] = value
        
        # Use the better content blocks if available
        content_blocks = base_result.content_blocks
        if len(fallback_result.content_blocks) > len(content_blocks):
            content_blocks = fallback_result.content_blocks
        
        # Calculate merged quality score
        merged_quality = max(base_result.quality_score, fallback_result.quality_score)
        
        # Create route name with length limit (20 chars max for DB field)
        base_route = base_result.route_used.replace('_failed', '').replace('_fail', '').replace('safari_fallback', 'safari').replace('safari_fb', 'safari').replace('safari_mode', 'safari')
        hybrid_route = f"hybrid_{base_route}"
        # Truncate to 20 characters if needed
        if len(hybrid_route) > 20:
            hybrid_route = hybrid_route[:20]
        
        return ProcessingResult(
            success=True,
            clean_content=base_result.clean_content,
            content_blocks=content_blocks,
            extracted_metadata=merged_metadata,
            quality_score=merged_quality,
            processing_time_ms=base_result.processing_time_ms + fallback_result.processing_time_ms,
            route_used=_truncate_route_name(hybrid_route)
        )
    
    def _store_processing_results(self, article: Article, result: ProcessingResult, route: str, cost: float):
        """
        Store content processing results in article model.
        """
        
        from .models import serialize_content_blocks
        
        with transaction.atomic():
            # Store processed content
            article.clean_content = result.clean_content
            article.content_blocks = serialize_content_blocks(result.content_blocks)  # Use unified serialization
            article.extracted_metadata = result.extracted_metadata
            article.content_quality_metrics = {
                'overall_score': result.quality_score,
                'processing_time_ms': result.processing_time_ms,
                'route_used': route
            }
            
            # Store processing metadata (truncate to fit DB constraint)
            article.process_route = _truncate_route_name(route)
            article.process_duration_ms = result.processing_time_ms
            article.process_cost_usd = cost
            
            # Update legacy content field for backward compatibility
            if not article.content:
                article.content = result.clean_content
            
            # Update rich content metadata
            article.update_rich_content_metadata()

            # Backfill image_url from content_blocks if still missing
            if not article.image_url and article.content_blocks:
                for block in article.content_blocks:
                    if block.get('type') in ('image', 'img', 'figure'):
                        src = (block.get('metadata') or {}).get('src')
                        if src and src.startswith('http'):
                            article.image_url = src[:1024]
                            break

            article.save()
    
    def _update_processing_status(self, article: Article, status: ProcessingStatus):
        """
        Update article processing status and related fields.
        """
        
        with transaction.atomic():
            article.process_status = status
            article.last_process_attempt = timezone.now()
            
            if status == ProcessingStatus.PROCESSING:
                article.process_attempts += 1
            elif status == ProcessingStatus.FAILED:
                article.process_attempts += 1
            
            article.save()
    
    def _handle_processing_error(self, article: Article, error_message: str, start_time: float) -> ProcessResult:
        """
        Handle processing errors and update article status.
        """
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        with transaction.atomic():
            article.process_status = ProcessingStatus.FAILED
            article.process_error_message = error_message
            article.process_attempts += 1
            article.last_process_attempt = timezone.now()
            article.save()
        
        return ProcessResult(
            success=False,
            article=article,
            error_message=error_message,
            duration_ms=duration_ms
        )
    
    def get_processing_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about processing performance.
        """
        
        from django.db.models import Count, Avg, Q
        from datetime import timedelta
        
        # Get stats for last 24 hours
        since = timezone.now() - timedelta(hours=24)
        
        stats = Article.objects.filter(
            last_process_attempt__gte=since
        ).aggregate(
            total_attempts=Count('id'),
            successful_processes=Count('id', filter=Q(process_status=ProcessingStatus.COMPLETED)),
            failed_processes=Count('id', filter=Q(process_status=ProcessingStatus.FAILED)),
            avg_duration=Avg('process_duration_ms'),
            avg_cost=Avg('process_cost_usd'),
            avg_quality=Avg('content_quality_metrics__overall_score')
        )
        
        # Calculate success rate
        total = stats['total_attempts'] or 0
        successful = stats['successful_processes'] or 0
        stats['success_rate'] = (successful / total * 100) if total > 0 else 0
        
        # Get route distribution
        route_stats = Article.objects.filter(
            last_process_attempt__gte=since,
            process_status=ProcessingStatus.COMPLETED
        ).values('process_route').annotate(
            count=Count('id'),
            avg_quality=Avg('content_quality_metrics__overall_score'),
            avg_cost=Avg('process_cost_usd')
        ).order_by('-count')
        
        stats['route_distribution'] = list(route_stats)
        
        # Get router statistics
        stats['routing_stats'] = self.router.get_routing_statistics()
        
        return stats


class ProcessingManager:
    """
    Manager for coordinating processing operations across multiple articles.
    """
    
    def __init__(self):
        self.processor = ContentProcessor()
    
    def process_pending_articles(self, limit: int = 20) -> Dict[str, Any]:
        """
        Process content for articles that need Step 2 processing.
        """
        
        # Get articles that need processing
        pending_articles = Article.objects.filter(
            process_status=ProcessingStatus.PENDING,
            fetch_status='completed',  # Must have completed Step 1
            process_attempts__lt=3
        ).order_by('last_fetch_attempt')[:limit]
        
        if not pending_articles:
            return {
                'processed': 0,
                'successful': 0,
                'failed': 0,
                'message': 'No pending articles to process'
            }
        
        # Process articles
        results = []
        total_cost = 0.0
        for article in pending_articles:
            result = self.processor.process_article_content(article)
            results.append(result)
            
            # Extract cost from the article after processing (cost is stored in process_cost_usd)
            if result.success:
                article.refresh_from_db()  # Get updated cost from database
                if article.process_cost_usd:
                    total_cost += float(article.process_cost_usd)
        
        # Compile statistics
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful
        
        return {
            'processed': len(results),
            'successful': successful,
            'failed': failed,
            'total_cost_usd': total_cost,
            'avg_cost_per_article': total_cost / len(results) if results else 0,
            'results': results
        }
    
    def retry_failed_processing(self, max_retries: int = 3) -> Dict[str, Any]:
        """
        Retry processing for articles that failed but haven't exceeded max attempts.
        """
        
        failed_articles = Article.objects.filter(
            process_status=ProcessingStatus.FAILED,
            process_attempts__lt=max_retries
        ).order_by('last_process_attempt')[:10]  # Limit retries
        
        if not failed_articles:
            return {
                'processed': 0,
                'successful': 0,
                'failed': 0,
                'message': 'No failed articles to retry'
            }
        
        # Reset status to pending for retry
        for article in failed_articles:
            article.process_status = ProcessingStatus.PENDING
            article.save()
        
        # Process articles
        results = []
        total_cost = 0.0
        for article in failed_articles:
            result = self.processor.process_article_content(article)
            results.append(result)
            
            # Extract cost from the article after processing (cost is stored in process_cost_usd)
            if result.success:
                article.refresh_from_db()  # Get updated cost from database
                if article.process_cost_usd:
                    total_cost += float(article.process_cost_usd)
        
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful
        
        return {
            'processed': len(results),
            'successful': successful,
            'failed': failed,
            'total_cost_usd': total_cost,
            'results': results
        } 