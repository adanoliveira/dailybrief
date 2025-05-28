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

from apps.articles.models import Article, ProcessingStatus
from .safari_mode import SafariModeProcessor, ProcessingResult
from .routing import ProcessingRouter

logger = logging.getLogger(__name__)


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
    Main content processing service with intelligent routing.
    Coordinates Step 2 processing using Safari mode or LLM enhancement.
    """
    
    def __init__(self):
        self.safari_processor = SafariModeProcessor()
        self.router = ProcessingRouter()
        
        # LLM processor will be imported dynamically to avoid circular imports
        self._llm_processor = None
        
        # Processing settings
        self.max_attempts = getattr(settings, 'CONTENT_PROCESS_MAX_ATTEMPTS', 3)
        self.timeout_seconds = getattr(settings, 'CONTENT_PROCESS_TIMEOUT', 60)
    
    @property
    def llm_processor(self):
        """Lazy load LLM processor to avoid import issues."""
        if self._llm_processor is None:
            try:
                from .llm_enhanced import LLMEnhancedProcessor
                self._llm_processor = LLMEnhancedProcessor()
            except ImportError:
                logger.warning("LLM processor not available")
                self._llm_processor = None
        return self._llm_processor
    
    def process_article_content(self, article: Article) -> ProcessResult:
        """
        Main entry point for Step 2 content processing.
        """
        
        start_time = time.time()
        
        # Validate article is ready for processing
        if not article.needs_processing:
            return ProcessResult(
                success=False,
                article=article,
                error_message=f"Article doesn't need processing. Status: {article.process_status}"
            )
        
        # Update processing status
        self._update_processing_status(article, ProcessingStatus.PROCESSING)
        
        try:
            # Determine processing route
            route = self.router.determine_route(article)
            
            # Process content using selected route
            if route == 'safari_mode':
                processing_result = self._process_safari_mode(article)
                cost = 0.001  # Estimated cost for Safari mode
            elif route == 'llm_enhanced':
                processing_result = self._process_llm_enhanced(article)
                cost = 0.01  # Estimated cost for LLM processing
            elif route == 'hybrid':
                processing_result = self._process_hybrid(article)
                cost = 0.005  # Estimated cost for hybrid processing
            else:
                raise ValueError(f"Unknown processing route: {route}")
            
            if processing_result.success:
                # Store processing results
                self._store_processing_results(article, processing_result, route, cost)
                
                # Update status to completed
                self._update_processing_status(article, ProcessingStatus.COMPLETED)
                
                duration_ms = int((time.time() - start_time) * 1000)
                
                return ProcessResult(
                    success=True,
                    article=article,
                    processing_result=processing_result,
                    route_used=route,
                    duration_ms=duration_ms,
                    cost_usd=cost
                )
            else:
                # Handle processing failure
                return self._handle_processing_error(article, processing_result.error_message, start_time)
                
        except Exception as e:
            logger.exception(f"Content processing failed for article {article.id}: {str(e)}")
            return self._handle_processing_error(article, str(e), start_time)
    
    def _process_safari_mode(self, article: Article) -> ProcessingResult:
        """
        Process content using Safari Reader Mode algorithm.
        """
        
        logger.info(f"Processing article {article.id} with Safari mode")
        
        # Get article metadata for processing
        article_metadata = {
            'title': article.title,
            'author': article.author,
            'source_name': article.source_name,
            'published_at': article.published_at.isoformat() if article.published_at else None
        }
        
        # Process with Safari mode
        result = self.safari_processor.process_content(article.raw_html, article_metadata)
        
        if result.success:
            logger.info(f"Safari mode processing successful for article {article.id}, "
                       f"quality: {result.quality_score:.3f}")
        else:
            logger.error(f"Safari mode processing failed for article {article.id}: {result.error_message}")
        
        return result
    
    def _process_llm_enhanced(self, article: Article) -> ProcessingResult:
        """
        Process content using LLM enhancement.
        """
        
        if not self.llm_processor:
            logger.warning(f"LLM processor not available for article {article.id}, falling back to Safari mode")
            return self._process_safari_mode(article)
        
        logger.info(f"Processing article {article.id} with LLM enhancement")
        
        # Get article metadata for processing
        article_metadata = {
            'title': article.title,
            'author': article.author,
            'source_name': article.source_name,
            'published_at': article.published_at.isoformat() if article.published_at else None,
            'paywall_detected': article.paywall_detected,
            'paywall_indicators': article.paywall_indicators
        }
        
        # Process with LLM enhancement
        result = self.llm_processor.process_content(article.raw_html, article_metadata)
        
        if result.success:
            logger.info(f"LLM processing successful for article {article.id}, "
                       f"quality: {result.quality_score:.3f}")
        else:
            logger.error(f"LLM processing failed for article {article.id}: {result.error_message}")
            # Fallback to Safari mode
            logger.info(f"Falling back to Safari mode for article {article.id}")
            result = self._process_safari_mode(article)
        
        return result
    
    def _process_hybrid(self, article: Article) -> ProcessingResult:
        """
        Process content using hybrid approach: Safari mode with LLM enhancement.
        """
        
        logger.info(f"Processing article {article.id} with hybrid approach")
        
        # Start with Safari mode processing
        safari_result = self._process_safari_mode(article)
        
        if not safari_result.success:
            return safari_result
        
        # Enhance with LLM if quality is below threshold or specific conditions are met
        should_enhance = (
            safari_result.quality_score < 0.7 or
            article.paywall_detected or
            len(safari_result.content_blocks) < 3
        )
        
        if should_enhance and self.llm_processor:
            logger.info(f"Enhancing Safari result with LLM for article {article.id}")
            
            # Use LLM to enhance specific elements
            enhanced_result = self._enhance_with_llm(article, safari_result)
            
            if enhanced_result.success and enhanced_result.quality_score > safari_result.quality_score:
                logger.info(f"LLM enhancement improved quality from {safari_result.quality_score:.3f} "
                           f"to {enhanced_result.quality_score:.3f}")
                return enhanced_result
            else:
                logger.info(f"LLM enhancement did not improve quality, using Safari result")
        
        return safari_result
    
    def _enhance_with_llm(self, article: Article, safari_result: ProcessingResult) -> ProcessingResult:
        """
        Enhance Safari mode result with LLM processing for specific elements.
        """
        
        try:
            # Create enhanced metadata with Safari results
            enhanced_metadata = {
                'title': article.title,
                'author': article.author,
                'source_name': article.source_name,
                'published_at': article.published_at.isoformat() if article.published_at else None,
                'paywall_detected': article.paywall_detected,
                'safari_quality': safari_result.quality_score,
                'safari_content_blocks': len(safari_result.content_blocks),
                'enhancement_mode': True
            }
            
            # Process with LLM for enhancement
            llm_result = self.llm_processor.process_content(article.raw_html, enhanced_metadata)
            
            if llm_result.success:
                # Merge the best parts of both results
                merged_result = self._merge_processing_results(safari_result, llm_result)
                return merged_result
            else:
                return safari_result
                
        except Exception as e:
            logger.exception(f"LLM enhancement failed for article {article.id}: {str(e)}")
            return safari_result
    
    def _merge_processing_results(self, safari_result: ProcessingResult, llm_result: ProcessingResult) -> ProcessingResult:
        """
        Merge Safari mode and LLM processing results to get the best of both.
        """
        
        # Use LLM content if it's significantly better
        if llm_result.quality_score > safari_result.quality_score + 0.1:
            base_result = llm_result
            fallback_result = safari_result
        else:
            base_result = safari_result
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
        
        return ProcessingResult(
            success=True,
            clean_content=base_result.clean_content,
            content_blocks=content_blocks,
            extracted_metadata=merged_metadata,
            quality_score=merged_quality,
            processing_time_ms=base_result.processing_time_ms + fallback_result.processing_time_ms
        )
    
    def _store_processing_results(self, article: Article, result: ProcessingResult, route: str, cost: float):
        """
        Store processing results in the article model.
        """
        
        with transaction.atomic():
            # Store processed content
            article.clean_content = result.clean_content
            article.content_blocks = [
                {
                    'type': block.type,
                    'content': block.content,
                    'level': block.level,
                    'position': block.position,
                    'metadata': block.metadata
                }
                for block in result.content_blocks
            ]
            article.extracted_metadata = result.extracted_metadata
            article.content_quality_metrics = {
                'overall_score': result.quality_score,
                'processing_time_ms': result.processing_time_ms,
                'route_used': route
            }
            
            # Store processing metadata
            article.process_route = route
            article.process_duration_ms = result.processing_time_ms
            article.process_cost_usd = cost
            
            # Update legacy content field for backward compatibility
            if not article.content:
                article.content = result.clean_content
            
            # Update rich content metadata
            article.update_rich_content_metadata()
            
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
        for article in pending_articles:
            result = self.processor.process_article_content(article)
            results.append(result)
        
        # Compile statistics
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful
        total_cost = sum(r.cost_usd for r in results)
        
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
        for article in failed_articles:
            result = self.processor.process_article_content(article)
            results.append(result)
        
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful
        total_cost = sum(r.cost_usd for r in results)
        
        return {
            'processed': len(results),
            'successful': successful,
            'failed': failed,
            'total_cost_usd': total_cost,
            'results': results
        } 