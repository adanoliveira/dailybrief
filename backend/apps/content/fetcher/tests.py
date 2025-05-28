"""
Tests for Step 1 content fetching functionality.
Tests the clean extraction, fetcher, and tasks modules.
"""

from django.test import TestCase
from django.utils import timezone
from unittest.mock import patch, MagicMock, Mock
import requests
from apps.articles.models import Article, FetchStatus
from apps.feeds.models import Language
from .extraction import ExtractionResult, PaywallBypassStrategy, BeautifulSoupStrategy
from .fetcher import ContentFetcher, FetchManager, FetchResult
from .utils import validate_url, normalize_url, clean_extracted_text


class UtilsTestCase(TestCase):
    """Test utility functions."""
    
    def test_validate_url(self):
        """Test URL validation."""
        # Valid URLs
        self.assertTrue(validate_url('https://example.com'))
        self.assertTrue(validate_url('http://example.com/article'))
        self.assertTrue(validate_url('https://subdomain.example.com/path?param=value'))
        
        # Invalid URLs
        self.assertFalse(validate_url('not-a-url'))
        self.assertFalse(validate_url(''))
        self.assertFalse(validate_url('example.com'))  # Missing scheme
    
    def test_normalize_url(self):
        """Test URL normalization."""
        # Remove tracking parameters
        url_with_tracking = 'https://example.com/article?utm_source=twitter&utm_campaign=test&id=123'
        normalized = normalize_url(url_with_tracking)
        self.assertEqual(normalized, 'https://example.com/article?id=123')
        
        # Keep non-tracking parameters
        url_with_params = 'https://example.com/search?q=test&page=2'
        normalized = normalize_url(url_with_params)
        self.assertEqual(normalized, 'https://example.com/search?q=test&page=2')
    
    def test_clean_extracted_text(self):
        """Test text cleaning functionality."""
        # Test whitespace normalization
        messy_text = "  This   is\n\n\na   test\t\ttext  "
        cleaned = clean_extracted_text(messy_text)
        self.assertEqual(cleaned, "This is a test text")
        
        # Test empty text
        self.assertEqual(clean_extracted_text(""), "")
        self.assertEqual(clean_extracted_text(None), "")


class ExtractionResultTestCase(TestCase):
    """Test ExtractionResult dataclass."""
    
    def test_successful_result(self):
        """Test creating a successful extraction result."""
        result = ExtractionResult(
            success=True,
            raw_html="<html><body>Test</body></html>",
            basic_content="Test content",
            title="Test Title"
        )
        
        self.assertTrue(result.success)
        self.assertEqual(result.title, "Test Title")
        self.assertEqual(result.basic_content, "Test content")
    
    def test_failed_result_validation(self):
        """Test that result validates properly on creation."""
        # Result with success=True but no raw_html should become failed
        result = ExtractionResult(success=True, raw_html="")
        
        self.assertFalse(result.success)
        self.assertEqual(result.error_message, "No raw HTML content extracted")


class PaywallBypassStrategyTestCase(TestCase):
    """Test PaywallBypassStrategy."""
    
    def setUp(self):
        self.strategy = PaywallBypassStrategy()
    
    def test_strategy_available(self):
        """Test that strategy is available."""
        self.assertTrue(self.strategy.available)
    
    @patch('requests.get')
    def test_successful_extraction(self, mock_get):
        """Test successful content extraction."""
        # Mock successful HTTP response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
            <head><title>Test Article</title></head>
            <body>
                <article>
                    <h1>Test Article Title</h1>
                    <p>This is the article content.</p>
                </article>
            </body>
        </html>
        """
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = self.strategy.extract('https://example.com/article')
        
        self.assertTrue(result.success)
        self.assertIn("Test Article", result.title)
        self.assertIn("article content", result.basic_content)
        self.assertEqual(result.strategy_used, "PaywallBypass")
    
    @patch('requests.get')
    def test_request_failure(self, mock_get):
        """Test handling of request failures."""
        mock_get.side_effect = requests.RequestException("Connection failed")
        
        result = self.strategy.extract('https://example.com/article')
        
        self.assertFalse(result.success)
        self.assertIn("Request failed", result.error_message)
    
    def test_paywall_detection(self):
        """Test paywall detection functionality."""
        # HTML with paywall indicators
        paywall_html = """
        <html>
            <body>
                <div class="paywall">Subscribe to continue reading</div>
                <p>This article is for subscribers only.</p>
            </body>
        </html>
        """
        
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(paywall_html, 'html.parser')
        
        detected, indicators = self.strategy._detect_paywall(soup, paywall_html)
        self.assertTrue(detected)
        self.assertGreater(len(indicators), 0)


class BeautifulSoupStrategyTestCase(TestCase):
    """Test BeautifulSoupStrategy."""
    
    def setUp(self):
        self.strategy = BeautifulSoupStrategy()
    
    def test_strategy_available(self):
        """Test that strategy is available."""
        self.assertTrue(self.strategy.available)
    
    @patch('requests.get')
    def test_successful_extraction(self, mock_get):
        """Test successful content extraction."""
        # Mock successful HTTP response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
            <head><title>Test Article</title></head>
            <body>
                <h1>Article Title</h1>
                <p>This is the main content of the article.</p>
            </body>
        </html>
        """
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = self.strategy.extract('https://example.com/article')
        
        self.assertTrue(result.success)
        self.assertIn("Test Article", result.title)
        self.assertIn("main content", result.basic_content)
        self.assertEqual(result.strategy_used, "BeautifulSoup")


class ContentFetcherTestCase(TestCase):
    """Test ContentFetcher service."""
    
    def setUp(self):
        """Set up test data."""
        # Create a language
        self.language = Language.objects.create(
            iso_code='en',
            name='English'
        )
        
        # Create a test article
        self.article = Article.objects.create(
            title='Test Article',
            description='Test description',
            url='https://example.com/test-article',
            published_at=timezone.now(),
            language=self.language,
            fetch_status=FetchStatus.PENDING
        )
        
        self.fetcher = ContentFetcher()
    
    def test_article_needs_fetch(self):
        """Test that pending articles need fetching."""
        self.assertTrue(self.article.needs_fetch)
    
    def test_article_completed_no_fetch(self):
        """Test that completed articles don't need fetching."""
        self.article.fetch_status = FetchStatus.COMPLETED
        self.article.save()
        
        self.assertFalse(self.article.needs_fetch)
    
    @patch('apps.content.fetcher.fetcher.ContentFetcher._extract_with_strategies')
    def test_successful_fetch(self, mock_extract):
        """Test successful content fetching."""
        # Mock successful extraction
        mock_result = ExtractionResult(
            success=True,
            raw_html="<html><body>Test content</body></html>",
            basic_content="Test content extracted",
            title="Extracted Title",
            strategy_used="PaywallBypass",
            duration_ms=1500
        )
        mock_extract.return_value = mock_result
        
        result = self.fetcher.fetch_article_content(self.article)
        
        self.assertTrue(result.success)
        self.assertEqual(result.strategy_used, "PaywallBypass")
        self.assertGreater(result.duration_ms, 0)
        
        # Check article was updated
        self.article.refresh_from_db()
        self.assertEqual(self.article.fetch_status, FetchStatus.COMPLETED)
        self.assertEqual(self.article.basic_content, "Test content extracted")
        self.assertIsNotNone(self.article.raw_html)
    
    @patch('apps.content.fetcher.fetcher.ContentFetcher._extract_with_strategies')
    def test_failed_fetch(self, mock_extract):
        """Test failed content fetching."""
        # Mock failed extraction
        mock_result = ExtractionResult(
            success=False,
            error_message="All extraction strategies failed",
            strategy_used="none"
        )
        mock_extract.return_value = mock_result
        
        result = self.fetcher.fetch_article_content(self.article)
        
        self.assertFalse(result.success)
        self.assertIn("All extraction strategies failed", result.error_message)
        
        # Check article status was updated
        self.article.refresh_from_db()
        self.assertEqual(self.article.fetch_status, FetchStatus.FAILED)
    
    def test_article_doesnt_need_fetch(self):
        """Test handling of articles that don't need fetching."""
        self.article.fetch_status = FetchStatus.COMPLETED
        self.article.save()
        
        result = self.fetcher.fetch_article_content(self.article)
        
        self.assertFalse(result.success)
        self.assertIn("doesn't need fetching", result.error_message)


class FetchManagerTestCase(TestCase):
    """Test FetchManager service."""
    
    def setUp(self):
        """Set up test data."""
        # Create a language
        self.language = Language.objects.create(
            iso_code='en',
            name='English'
        )
        
        # Create test articles
        self.pending_articles = []
        for i in range(3):
            article = Article.objects.create(
                title=f'Test Article {i}',
                description=f'Test description {i}',
                url=f'https://example.com/test-article-{i}',
                published_at=timezone.now(),
                language=self.language,
                fetch_status=FetchStatus.PENDING
            )
            self.pending_articles.append(article)
        
        self.manager = FetchManager()
    
    @patch('apps.content.fetcher.fetcher.ContentFetcher.fetch_article_content')
    def test_fetch_pending_articles(self, mock_fetch):
        """Test fetching pending articles in batch."""
        # Mock successful fetches
        mock_fetch.return_value = FetchResult(
            success=True,
            duration_ms=1000,
            strategy_used="PaywallBypass"
        )
        
        result = self.manager.fetch_pending_articles(limit=5)
        
        self.assertEqual(result['processed'], 3)
        self.assertEqual(result['successful'], 3)
        self.assertEqual(result['failed'], 0)
        
        # Should have called fetch for each pending article
        self.assertEqual(mock_fetch.call_count, 3)
    
    def test_no_pending_articles(self):
        """Test handling when no articles need fetching."""
        # Mark all articles as completed
        Article.objects.filter(id__in=[a.id for a in self.pending_articles]).update(
            fetch_status=FetchStatus.COMPLETED
        )
        
        result = self.manager.fetch_pending_articles()
        
        self.assertEqual(result['processed'], 0)
        self.assertIn('No pending articles', result['message'])


class TasksTestCase(TestCase):
    """Test Celery tasks (without actually running Celery)."""
    
    def setUp(self):
        """Set up test data."""
        # Create a language
        self.language = Language.objects.create(
            iso_code='en',
            name='English'
        )
        
        # Create a test article
        self.article = Article.objects.create(
            title='Test Article',
            description='Test description',
            url='https://example.com/test-article',
            published_at=timezone.now(),
            language=self.language,
            fetch_status=FetchStatus.PENDING
        )
    
    @patch('apps.content.fetcher.tasks.ContentFetcher')
    def test_fetch_article_content_task(self, mock_fetcher_class):
        """Test the fetch_article_content task function."""
        from .tasks import fetch_article_content
        
        # Mock the fetcher
        mock_fetcher = Mock()
        mock_fetcher_class.return_value = mock_fetcher
        mock_fetcher.fetch_article_content.return_value = FetchResult(
            success=True,
            duration_ms=1000,
            strategy_used="PaywallBypass"
        )
        
        # Call the task function directly (not as Celery task)
        result = fetch_article_content(self.article.id)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['strategy_used'], "PaywallBypass")
        
        # Verify fetcher was called
        mock_fetcher.fetch_article_content.assert_called_once()
    
    def test_fetch_article_content_task_invalid_id(self):
        """Test task with invalid article ID."""
        from .tasks import fetch_article_content
        
        result = fetch_article_content(99999)  # Non-existent ID
        
        self.assertFalse(result['success'])
        self.assertIn('not found', result['error'])
