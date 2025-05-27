from django.test import TestCase
from django.utils import timezone
from unittest.mock import patch, MagicMock
from apps.articles.models import Article, ContentStatus, ProcessingStatus
from apps.feeds.models import Language
from .models import ContentFetchLog, FetchAttempt
from .services import ContentFetcher, ContentFetchResult
from .strategies import ExtractionResult
from .utils import validate_url, normalize_url, detect_paywall_indicators


class ContentFetcherUtilsTestCase(TestCase):
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
    
    def test_detect_paywall_indicators(self):
        """Test paywall detection."""
        # HTML with paywall indicators
        paywall_html = '''
        <html>
            <body>
                <div class="paywall">Subscribe to continue reading</div>
                <p>This article is for subscribers only.</p>
            </body>
        </html>
        '''
        
        detected, indicators = detect_paywall_indicators(paywall_html, 'https://example.com')
        self.assertTrue(detected)
        self.assertGreater(len(indicators), 0)
        
        # HTML without paywall indicators
        normal_html = '''
        <html>
            <body>
                <h1>Article Title</h1>
                <p>This is a normal article content.</p>
            </body>
        </html>
        '''
        
        detected, indicators = detect_paywall_indicators(normal_html, 'https://example.com')
        self.assertFalse(detected)
        self.assertEqual(len(indicators), 0)


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
            language=self.language
        )
        
        self.fetcher = ContentFetcher()
    
    def test_should_attempt_fetch_pending_article(self):
        """Test that pending articles should be fetched."""
        self.assertTrue(self.fetcher._should_attempt_fetch(self.article))
    
    def test_should_not_attempt_fetch_completed_article(self):
        """Test that completed articles should not be fetched again."""
        self.article.content_status = ContentStatus.CONTENT_AVAILABLE
        self.article.save()
        
        self.assertFalse(self.fetcher._should_attempt_fetch(self.article))
    
    def test_should_not_attempt_fetch_max_attempts_reached(self):
        """Test that articles with max attempts reached should not be fetched."""
        self.article.content_fetch_attempts = 3
        self.article.max_fetch_attempts = 3
        self.article.save()
        
        self.assertFalse(self.fetcher._should_attempt_fetch(self.article))
    
    def test_handle_invalid_url(self):
        """Test handling of invalid URLs."""
        self.article.url = 'invalid-url'
        self.article.save()
        
        result = self.fetcher.fetch_article_content(self.article)
        
        self.assertFalse(result.success)
        self.assertEqual(result.content_status, ContentStatus.INVALID_URL)
        
        # Refresh from database
        self.article.refresh_from_db()
        self.assertEqual(self.article.content_status, ContentStatus.INVALID_URL)
    
    @patch('apps.content.fetcher.services.ContentExtractor')
    def test_successful_content_extraction(self, mock_extractor_class):
        """Test successful content extraction."""
        # Mock the extractor
        mock_extractor = MagicMock()
        mock_extractor_class.return_value = mock_extractor
        
        # Mock successful extraction result
        mock_result = ExtractionResult(
            success=True,
            content="This is the extracted article content. " * 50,  # Long enough for good quality
            title="Extracted Title",
            author="Test Author",
            strategy_used="newspaper3k",
            quality_metrics={
                'completeness': 0.8,
                'quality': 0.9,
                'readability': 0.7,
                'relevance': 0.8
            }
        )
        mock_extractor.extract_content.return_value = mock_result
        
        # Create a new fetcher instance to use the mocked extractor
        fetcher = ContentFetcher()
        result = fetcher.fetch_article_content(self.article)
        
        self.assertTrue(result.success)
        self.assertEqual(result.content_status, ContentStatus.CONTENT_AVAILABLE)
        
        # Refresh from database and check updates
        self.article.refresh_from_db()
        self.assertEqual(self.article.content_status, ContentStatus.CONTENT_AVAILABLE)
        self.assertEqual(self.article.content_source, 'full_fetch')
        self.assertIsNotNone(self.article.content)
        self.assertGreater(self.article.word_count, 0)
    
    @patch('apps.content.fetcher.services.ContentExtractor')
    def test_paywall_detection(self, mock_extractor_class):
        """Test paywall detection handling."""
        # Mock the extractor
        mock_extractor = MagicMock()
        mock_extractor_class.return_value = mock_extractor
        
        # Mock paywall detection result
        mock_result = ExtractionResult(
            success=False,
            error_message="Paywall detected",
            strategy_used="newspaper3k",
            paywall_detected=True,
            paywall_indicators=["Text pattern: subscribe to continue reading"]
        )
        mock_extractor.extract_content.return_value = mock_result
        
        # Create a new fetcher instance to use the mocked extractor
        fetcher = ContentFetcher()
        result = fetcher.fetch_article_content(self.article)
        
        self.assertFalse(result.success)
        self.assertEqual(result.content_status, ContentStatus.PAYWALL_BLOCKED)
        
        # Refresh from database and check updates
        self.article.refresh_from_db()
        self.assertEqual(self.article.content_status, ContentStatus.PAYWALL_BLOCKED)
        self.assertTrue(self.article.use_description_as_content)


class ContentFetchLogTestCase(TestCase):
    """Test ContentFetchLog model."""
    
    def setUp(self):
        """Set up test data."""
        self.log = ContentFetchLog.objects.create(
            article_id=1,
            article_url='https://example.com/test',
            attempt_number=1,
            status='success',
            started_at=timezone.now() - timezone.timedelta(seconds=5),
            completed_at=timezone.now()
        )
    
    def test_duration_calculation(self):
        """Test duration calculation property."""
        duration = self.log.duration_ms
        self.assertIsNotNone(duration)
        self.assertGreater(duration, 0)
        self.assertLess(duration, 10000)  # Should be less than 10 seconds
    
    def test_string_representation(self):
        """Test string representation."""
        expected = "Fetch attempt 1 for article 1 - success"
        self.assertEqual(str(self.log), expected)


class FetchAttemptTestCase(TestCase):
    """Test FetchAttempt model."""
    
    def setUp(self):
        """Set up test data."""
        self.attempt = FetchAttempt.objects.create(
            article_id=1,
            attempts=0,
            max_attempts=3
        )
    
    def test_increment_attempt(self):
        """Test attempt increment with backoff calculation."""
        # First increment
        self.attempt.increment_attempt()
        self.assertEqual(self.attempt.attempts, 1)
        self.assertIsNotNone(self.attempt.next_retry_at)
        self.assertIsNotNone(self.attempt.last_attempt_at)
        
        # Second increment
        first_retry_time = self.attempt.next_retry_at
        self.attempt.increment_attempt()
        self.assertEqual(self.attempt.attempts, 2)
        self.assertGreater(self.attempt.next_retry_at, first_retry_time)
        
        # Third increment (max reached)
        self.attempt.increment_attempt()
        self.assertEqual(self.attempt.attempts, 3)
        self.assertTrue(self.attempt.is_completed)
        self.assertIsNone(self.attempt.next_retry_at)
    
    def test_mark_completed(self):
        """Test marking attempt as completed."""
        self.attempt.mark_completed('success')
        
        self.assertTrue(self.attempt.is_completed)
        self.assertEqual(self.attempt.final_status, 'success')
        self.assertIsNone(self.attempt.next_retry_at)
    
    def test_string_representation(self):
        """Test string representation."""
        expected = "Fetch attempts for article 1: 0/3"
        self.assertEqual(str(self.attempt), expected)
