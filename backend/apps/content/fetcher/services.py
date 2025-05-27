import logging
import random
from typing import Optional, Dict, Any
from django.utils import timezone
from django.db import transaction

from apps.articles.models import Article, ContentStatus, ProcessingStatus
from .models import ContentFetchLog, FetchAttempt
from .strategies import ContentExtractor, ExtractionResult
from .utils import validate_url, normalize_url, get_user_agents

logger = logging.getLogger(__name__)


class ContentFetchResult:
    """Result of content fetching operation."""
    
    def __init__(self, success: bool, article: Article, message: str = "", 
                 content_status: str = None, extraction_result: ExtractionResult = None):
        self.success = success
        self.article = article
        self.message = message
        self.content_status = content_status
        self.extraction_result = extraction_result


class ContentFetcher:
    """
    Main service for fetching and processing article content.
    Handles web scraping with robust error handling and fallback strategies.
    """
    
    def __init__(self):
        self.extractor = ContentExtractor()
        self.user_agents = get_user_agents()
    
    def fetch_article_content(self, article: Article) -> ContentFetchResult:
        """
        Attempt to fetch full article content with comprehensive error handling.
        
        Args:
            article (Article): Article instance to fetch content for
            
        Returns:
            ContentFetchResult: Result of the fetch operation
        """
        # Validate article URL
        if not validate_url(article.url):
            return self._handle_invalid_url(article)
        
        # Check if we should attempt fetching
        if not self._should_attempt_fetch(article):
            return ContentFetchResult(
                success=False,
                article=article,
                message="Maximum fetch attempts reached or already processed",
                content_status=article.content_status
            )
        
        # Normalize URL
        normalized_url = normalize_url(article.url)
        
        # Create fetch log entry
        fetch_log = self._create_fetch_log(article, normalized_url)
        
        try:
            # Update article status to fetching
            self._update_article_status(article, ContentStatus.FETCHING)
            
            # Select random user agent
            user_agent = random.choice(self.user_agents)
            
            # Attempt content extraction
            extraction_result = self.extractor.extract_content(normalized_url, user_agent, article)
            
            # Process extraction result
            return self._process_extraction_result(article, extraction_result, fetch_log)
            
        except Exception as e:
            logger.exception(f"Unexpected error fetching content for article {article.id}: {str(e)}")
            return self._handle_technical_error(article, fetch_log, str(e))
    
    def _should_attempt_fetch(self, article: Article) -> bool:
        """Check if we should attempt to fetch content for this article."""
        # Don't fetch if already has content
        if article.content_status in [
            ContentStatus.CONTENT_AVAILABLE, 
            ContentStatus.PARTIAL_CONTENT,
            ContentStatus.PAYWALL_BLOCKED,
            ContentStatus.ACCESS_DENIED
        ]:
            return False
        
        # Don't fetch if max attempts reached
        if article.content_fetch_attempts >= article.max_fetch_attempts:
            return False
        
        # Check if currently fetching
        if article.content_status == ContentStatus.FETCHING:
            # Check if fetch started more than 10 minutes ago (stuck)
            if (article.last_fetch_attempt and 
                timezone.now() - article.last_fetch_attempt > timezone.timedelta(minutes=10)):
                logger.warning(f"Article {article.id} stuck in fetching state, allowing retry")
                return True
            return False
        
        return True
    
    def _create_fetch_log(self, article: Article, url: str) -> ContentFetchLog:
        """Create a new fetch log entry."""
        attempt_number = article.content_fetch_attempts + 1
        
        return ContentFetchLog.objects.create(
            article_id=article.id,
            article_url=url,
            attempt_number=attempt_number,
            status='fetching',
            started_at=timezone.now()
        )
    
    def _update_article_status(self, article: Article, status: ContentStatus):
        """Update article content status and fetch tracking."""
        article.content_status = status
        article.content_fetch_attempts += 1
        article.last_fetch_attempt = timezone.now()
        article.save(update_fields=[
            'content_status', 'content_fetch_attempts', 'last_fetch_attempt'
        ])
    
    def _process_extraction_result(self, article: Article, result: ExtractionResult, 
                                 fetch_log: ContentFetchLog) -> ContentFetchResult:
        """Process the result of content extraction."""
        
        # Complete the fetch log
        fetch_log.completed_at = timezone.now()
        fetch_log.extraction_strategy = result.strategy_used
        fetch_log.error_message = result.error_message
        
        if result.paywall_detected:
            return self._handle_paywall(article, result, fetch_log)
        elif result.success and result.content:
            return self._handle_successful_extraction(article, result, fetch_log)
        else:
            return self._handle_failed_extraction(article, result, fetch_log)
    
    def _handle_successful_extraction(self, article: Article, result: ExtractionResult, 
                                    fetch_log: ContentFetchLog) -> ContentFetchResult:
        """Handle successful content extraction."""
        
        # Content validation is now done in ContentExtractor, so we can trust the result
        
        # Determine content status based on quality
        quality_score = result.quality_metrics.get('completeness', 0.0)
        
        if quality_score >= 0.7:
            content_status = ContentStatus.CONTENT_AVAILABLE
            content_source = 'full_fetch'
        elif quality_score >= 0.3:
            content_status = ContentStatus.PARTIAL_CONTENT
            content_source = 'partial_fetch'
        else:
            content_status = ContentStatus.METADATA_ONLY
            content_source = 'description'
        
        # Update article with extracted content
        with transaction.atomic():
            article.content = result.content
            article.content_status = content_status
            article.content_source = content_source
            article.content_completeness = quality_score
            article.content_quality_score = result.quality_metrics.get('quality', 0.0)
            
            # Update title and author if better versions found
            if result.title and len(result.title) > len(article.title or ""):
                article.title = result.title
            if result.author and not article.author:
                article.author = result.author
            
            # Store rich content data
            if result.rich_content:
                article.rich_content = result.rich_content
            
            if result.media_assets:
                article.media_assets = result.media_assets
            
            if result.formatting_data:
                article.formatting_data = result.formatting_data
            
            if result.content_structure:
                article.content_structure = result.content_structure
            
            # Update rich content metadata
            article.update_rich_content_metadata()
            
            # Recalculate content metrics
            self._update_content_metrics(article, result.content)
            
            article.save()
        
        # Update fetch log
        fetch_log.status = 'success'
        fetch_log.content_source = content_source
        fetch_log.content_length = len(result.content)
        fetch_log.content_quality_score = quality_score
        fetch_log.extracted_text_length = len(result.content)
        fetch_log.has_main_content = True
        fetch_log.content_completeness = quality_score
        fetch_log.save()
        
        # Mark fetch attempts as completed
        self._mark_fetch_completed(article, 'success')
        
        logger.info(f"Successfully fetched content for article {article.id} using {result.strategy_used}")
        
        return ContentFetchResult(
            success=True,
            article=article,
            message=f"Content fetched successfully using {result.strategy_used}",
            content_status=content_status,
            extraction_result=result
        )
    
    def _handle_paywall(self, article: Article, result: ExtractionResult, 
                       fetch_log: ContentFetchLog) -> ContentFetchResult:
        """Handle paywall detection."""
        
        # Update article status
        article.content_status = ContentStatus.PAYWALL_BLOCKED
        article.fetch_error_message = "Content blocked by paywall"
        
        # Use description as fallback content if available
        if article.description:
            article.use_description_as_content = True
            article.content_source = 'description'
            self._update_content_metrics(article, article.description)
        
        article.save()
        
        # Update fetch log
        fetch_log.status = 'paywall'
        fetch_log.paywall_detected = True
        fetch_log.paywall_indicators = result.paywall_indicators
        fetch_log.save()
        
        # Mark fetch attempts as completed (don't retry paywalls)
        self._mark_fetch_completed(article, 'paywall')
        
        logger.warning(f"Paywall detected for article {article.id}: {result.paywall_indicators}")
        
        return ContentFetchResult(
            success=False,
            article=article,
            message="Content blocked by paywall",
            content_status=ContentStatus.PAYWALL_BLOCKED,
            extraction_result=result
        )
    
    def _handle_failed_extraction(self, article: Article, result: ExtractionResult, 
                                 fetch_log: ContentFetchLog) -> ContentFetchResult:
        """Handle failed content extraction."""
        
        # Update fetch log
        fetch_log.status = 'failed'
        fetch_log.error_type = 'extraction_failed'
        fetch_log.save()
        
        # If we have a good description and this isn't a paywall, use description as fallback
        if (article.description and len(article.description) > 50 and 
            not result.paywall_detected and 
            article.content_fetch_attempts >= 1):  # Try fallback after first attempt
            
            return self._apply_fallback_strategy(article)
        
        # Determine if we should retry or give up
        elif article.content_fetch_attempts >= article.max_fetch_attempts:
            # Max attempts reached, use fallback strategy
            return self._apply_fallback_strategy(article)
        else:
            # Schedule retry
            article.content_status = ContentStatus.PENDING
            article.fetch_error_message = result.error_message
            article.save()
            
            self._schedule_retry(article)
            
            return ContentFetchResult(
                success=False,
                article=article,
                message=f"Extraction failed, will retry: {result.error_message}",
                content_status=ContentStatus.PENDING,
                extraction_result=result
            )
    
    def _handle_invalid_url(self, article: Article) -> ContentFetchResult:
        """Handle invalid URL."""
        article.content_status = ContentStatus.INVALID_URL
        article.fetch_error_message = "Invalid URL format"
        article.save()
        
        self._mark_fetch_completed(article, 'invalid_url')
        
        return ContentFetchResult(
            success=False,
            article=article,
            message="Invalid URL format",
            content_status=ContentStatus.INVALID_URL
        )
    
    def _handle_technical_error(self, article: Article, fetch_log: ContentFetchLog, 
                               error_message: str) -> ContentFetchResult:
        """Handle technical errors during fetching."""
        
        # Update fetch log
        fetch_log.status = 'technical_error'
        fetch_log.error_message = error_message
        fetch_log.error_type = 'technical_error'
        fetch_log.completed_at = timezone.now()
        fetch_log.save()
        
        # Update article
        article.content_status = ContentStatus.TECHNICAL_ERROR
        article.fetch_error_message = error_message
        article.save()
        
        # Schedule retry if not max attempts
        if article.content_fetch_attempts < article.max_fetch_attempts:
            self._schedule_retry(article)
        else:
            self._mark_fetch_completed(article, 'technical_error')
        
        return ContentFetchResult(
            success=False,
            article=article,
            message=f"Technical error: {error_message}",
            content_status=ContentStatus.TECHNICAL_ERROR
        )
    
    def _apply_fallback_strategy(self, article: Article) -> ContentFetchResult:
        """Apply fallback strategy when content fetching fails."""
        
        if article.description:
            # Use description as content
            article.content_status = ContentStatus.METADATA_ONLY
            article.content_source = 'description'
            article.use_description_as_content = True
            self._update_content_metrics(article, article.description)
            
            message = "Using description as fallback content"
            logger.info(f"Applied description fallback for article {article.id}")
        else:
            # No usable content
            article.content_status = ContentStatus.METADATA_ONLY
            article.content_source = 'summary_only'
            
            message = "No content available, metadata only"
            logger.warning(f"No fallback content available for article {article.id}")
        
        article.save()
        self._mark_fetch_completed(article, 'fallback_applied')
        
        return ContentFetchResult(
            success=bool(article.description),
            article=article,
            message=message,
            content_status=article.content_status
        )
    
    def _is_valid_text_content(self, content: str) -> bool:
        """Check if content is valid text (not corrupted/binary)."""
        if not content:
            return False
        
        # Check for binary/corrupted content indicators
        try:
            # Try to encode/decode to check for valid text
            content.encode('utf-8').decode('utf-8')
            
            # Check for excessive non-printable characters
            printable_chars = sum(1 for c in content if c.isprintable() or c.isspace())
            total_chars = len(content)
            
            if total_chars == 0:
                return False
            
            printable_ratio = printable_chars / total_chars
            
            # If less than 80% printable characters, likely corrupted
            if printable_ratio < 0.8:
                return False
            
            # Check for reasonable word structure
            words = content.split()
            if len(words) < 5:  # Too few words
                return False
            
            # Check average word length (should be reasonable for text)
            avg_word_length = sum(len(word) for word in words) / len(words)
            if avg_word_length > 20 or avg_word_length < 2:  # Unreasonable word lengths
                return False
            
            return True
            
        except (UnicodeDecodeError, UnicodeEncodeError):
            return False
    
    def _update_content_metrics(self, article: Article, content: str):
        """Update article content metrics."""
        if not content:
            return
        
        # Calculate word count and read time
        words = content.split()
        article.word_count = len(words)
        article.read_time_minutes = max(1, len(words) / 238)  # Average reading speed
        
        # Update content hash for deduplication
        import hashlib
        article.content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def _schedule_retry(self, article: Article):
        """Schedule retry for failed fetch."""
        fetch_attempt, created = FetchAttempt.objects.get_or_create(
            article_id=article.id,
            defaults={
                'attempts': 0,
                'max_attempts': article.max_fetch_attempts
            }
        )
        
        fetch_attempt.increment_attempt()
        
        logger.info(f"Scheduled retry for article {article.id}, attempt {fetch_attempt.attempts}")
    
    def _mark_fetch_completed(self, article: Article, final_status: str):
        """Mark fetch attempts as completed."""
        try:
            fetch_attempt = FetchAttempt.objects.get(article_id=article.id)
            fetch_attempt.mark_completed(final_status)
        except FetchAttempt.DoesNotExist:
            pass  # No fetch attempt record exists
    
    def get_articles_needing_fetch(self, limit: int = 100) -> list:
        """Get articles that need content fetching."""
        from django.db import models
        return list(Article.objects.filter(
            content_status=ContentStatus.PENDING,
            content_fetch_attempts__lt=models.F('max_fetch_attempts')
        ).order_by('published_at')[:limit])
    
    def get_articles_for_retry(self, limit: int = 50) -> list:
        """Get articles that are ready for retry."""
        retry_attempts = FetchAttempt.objects.filter(
            is_completed=False,
            next_retry_at__lte=timezone.now()
        ).values_list('article_id', flat=True)[:limit]
        
        return list(Article.objects.filter(
            id__in=retry_attempts,
            content_status=ContentStatus.PENDING
        ))


# Convenience functions for common operations

def fetch_article_content(article_id: int) -> ContentFetchResult:
    """
    Fetch content for a single article by ID.
    
    Args:
        article_id (int): Article ID
        
    Returns:
        ContentFetchResult: Result of the fetch operation
    """
    try:
        article = Article.objects.get(id=article_id)
        fetcher = ContentFetcher()
        return fetcher.fetch_article_content(article)
    except Article.DoesNotExist:
        logger.error(f"Article {article_id} not found")
        return ContentFetchResult(
            success=False,
            article=None,
            message="Article not found"
        )


def batch_fetch_content(article_ids: list, max_concurrent: int = 5) -> Dict[int, ContentFetchResult]:
    """
    Fetch content for multiple articles.
    
    Args:
        article_ids (list): List of article IDs
        max_concurrent (int): Maximum concurrent fetches
        
    Returns:
        Dict[int, ContentFetchResult]: Results keyed by article ID
    """
    results = {}
    fetcher = ContentFetcher()
    
    articles = Article.objects.filter(id__in=article_ids)
    
    for article in articles:
        try:
            result = fetcher.fetch_article_content(article)
            results[article.id] = result
        except Exception as e:
            logger.exception(f"Error fetching content for article {article.id}: {str(e)}")
            results[article.id] = ContentFetchResult(
                success=False,
                article=article,
                message=f"Error: {str(e)}"
            )
    
    return results 