# Content Fetcher Implementation Guide

> **Technical implementation details and integration patterns for the DailyBrief content fetching service**

## Overview

This guide provides detailed technical implementation information for the Content Fetcher service, including code patterns, integration approaches, and development best practices.

## Core Implementation

### Service Layer Implementation

#### ContentFetcher Class

The main orchestrator class that coordinates the extraction process:

```python
class ContentFetcher:
    """
    Fast content fetcher optimized for Step 1 extraction.
    Focuses on speed over processing quality.
    """
    
    def __init__(self):
        # Strategy pattern: ordered list of extraction strategies
        self.strategies = [
            BrowserSimulationStrategy(),  # Primary strategy
            AdvancedBypassStrategy(),     # Advanced techniques
            PaywallBypassStrategy(),      # Crawler bots
            BeautifulSoupStrategy()       # Reliable fallback
        ]
        
        # Performance configuration
        self.timeout_seconds = getattr(settings, 'FAST_FETCH_TIMEOUT', 10)
        self.max_retries = getattr(settings, 'FAST_FETCH_MAX_RETRIES', 2)
    
    def fetch_article_content(self, article: Article) -> FetchResult:
        """Main entry point for content fetching"""
        # URL preprocessing
        normalized_url = self._normalize_article_url(article)
        
        # Status management
        self._update_fetch_status(article, FetchStatus.FETCHING)
        
        # Strategy execution
        extraction_result = self._extract_with_strategies(normalized_url)
        
        # Result processing
        if extraction_result.success:
            self._store_extraction_results(article, extraction_result)
            self._update_fetch_status(article, FetchStatus.COMPLETED)
            self._queue_for_processing(article)
        
        return FetchResult(...)
```

#### FetchManager Class

Batch processing management for efficient bulk operations:

```python
class FetchManager:
    """
    Batch processing manager for content fetching operations.
    Optimizes bulk operations and resource utilization.
    """
    
    def fetch_pending_articles(self, limit: int = 50) -> Dict[str, Any]:
        """Process articles in batches for efficiency"""
        
        # Query optimization
        articles = Article.objects.filter(
            fetch_status=FetchStatus.PENDING
        ).select_related('publication').order_by('-created_at')[:limit]
        
        # Batch processing
        fetcher = ContentFetcher()
        results = []
        
        for article in articles:
            result = fetcher.fetch_article_content(article)
            results.append(result)
            
            # Rate limiting between requests
            if not result.success:
                time.sleep(1)  # Backoff on failures
        
        return self._compile_batch_statistics(results)
```

### Strategy Pattern Implementation

The Content Fetcher uses a sophisticated strategy pattern with four specialized extraction strategies, each designed for different types of web content restrictions.

#### Abstract Base Strategy

```python
class ExtractionStrategy(ABC):
    """Abstract base class for content extraction strategies."""
    
    def __init__(self):
        self.timeout = getattr(settings, 'EXTRACTION_TIMEOUT', 15)
        self.user_agent = getattr(settings, 'DEFAULT_USER_AGENT', 
                                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)')
    
    @property
    @abstractmethod
    def available(self) -> bool:
        """Check if this strategy is available."""
        pass
    
    @abstractmethod
    def extract(self, url: str) -> ExtractionResult:
        """Extract content from URL."""
        pass
```

#### BrowserSimulationStrategy Implementation

```python
class BrowserSimulationStrategy(ExtractionStrategy):
    """Advanced browser simulation with realistic behavior patterns."""
    
    def __init__(self):
        super().__init__()
        self.name = "BrowserSimulation"
        
        # Realistic browser configurations
        self.realistic_user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            # ... more user agents
        ]
        
        # Session management for connection pooling
        self.session = self._setup_session()
    
    def _setup_session(self):
        """Configure requests session with realistic settings."""
        session = requests.Session()
        
        # Retry strategy for resilience
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def extract(self, url: str) -> ExtractionResult:
        """Extract content using browser simulation."""
        
        # Try multiple browser configurations
        strategies = [
            self._try_chrome_simulation,
            self._try_firefox_simulation,
            self._try_safari_simulation,
            self._try_mobile_simulation,
        ]
        
        for strategy_func in strategies:
            result = strategy_func(url)
            if result.success and not result.paywall_detected:
                return result
            
            # Realistic timing between attempts
            time.sleep(random.uniform(0.5, 1.5))
        
        return result  # Return last attempt result
    
    def _get_chrome_headers(self, url: str) -> Dict[str, str]:
        """Generate realistic Chrome browser headers."""
        parsed_url = urlparse(url)
        
        return {
            'User-Agent': random.choice([ua for ua in self.realistic_user_agents if 'Chrome' in ua]),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Referer': random.choice(self.common_referers),
            'Cache-Control': 'max-age=0'
        }
```

#### AdvancedBypassStrategy Implementation

```python
class AdvancedBypassStrategy(ExtractionStrategy):
    """Advanced bypass techniques for highly restrictive sites."""
    
    def __init__(self):
        super().__init__()
        self.name = "AdvancedBypass"
        
        # Alternative access methods
        self.alternative_methods = [
            self._try_archive_org,
            self._try_outline_com,
            self._try_amp_version,
            self._try_mobile_version,
        ]
    
    def extract(self, url: str) -> ExtractionResult:
        """Extract using advanced bypass techniques."""
        
        # Try direct access with advanced headers
        for headers in self._get_advanced_headers_variants():
            result = self._try_advanced_method(url, headers)
            if result.success:
                return result
        
        # Try alternative access methods
        for method in self.alternative_methods:
            result = method(url)
            if result.success:
                return result
        
        return ExtractionResult(success=False, error_message="All advanced methods failed")
    
    def _try_archive_org(self, url: str) -> ExtractionResult:
        """Access content via Archive.org Wayback Machine."""
        try:
            # Wayback Machine API
            wayback_url = f"https://web.archive.org/web/{url}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (compatible; Archive.org_bot)',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            }
            
            response = requests.get(wayback_url, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            
            # Parse archived content
            soup = BeautifulSoup(response.content, 'html.parser')
            content_data = self._extract_advanced_content(soup, url)
            
            return ExtractionResult(
                success=True,
                raw_html=response.text,
                basic_content=content_data['content'],
                title=content_data['title'],
                author=content_data['author'],
                strategy_used=f"{self.name}_archive_org"
            )
            
        except Exception as e:
            return ExtractionResult(success=False, error_message=f"Archive.org failed: {str(e)}")
    
    def _try_outline_com(self, url: str) -> ExtractionResult:
        """Access content via outline.com proxy."""
        try:
            outline_url = f"https://outline.com/{url}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (compatible; OutlineBot/1.0)',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            }
            
            response = requests.get(outline_url, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            
            # Parse outline.com content
            soup = BeautifulSoup(response.content, 'html.parser')
            content_data = self._extract_advanced_content(soup, url)
            
            return ExtractionResult(
                success=True,
                raw_html=response.text,
                basic_content=content_data['content'],
                title=content_data['title'],
                author=content_data['author'],
                strategy_used=f"{self.name}_outline_com"
            )
            
        except Exception as e:
            return ExtractionResult(success=False, error_message=f"Outline.com failed: {str(e)}")
```

### Data Structures Implementation

#### ExtractionResult

```python
@dataclass
class ExtractionResult:
    """Result of Step 1 content extraction."""
    success: bool
    raw_html: str = ""
    basic_content: str = ""
    title: str = ""
    author: str = ""
    publish_date: Optional[str] = None
    extraction_metadata: Dict[str, Any] = field(default_factory=dict)
    paywall_detected: bool = False
    paywall_indicators: List[str] = field(default_factory=list)
    error_message: str = ""
    duration_ms: int = 0
    strategy_used: str = ""
    
    def __post_init__(self):
        """Validate extraction result after initialization."""
        if self.success and not self.raw_html:
            self.success = False
            self.error_message = "No raw HTML content extracted"
```

#### FetchResult

```python
@dataclass
class FetchResult:
    """Result of fast content fetching operation."""
    success: bool
    article: Optional[Article] = None
    error_message: str = ""
    extraction_result: Optional[ExtractionResult] = None
    duration_ms: int = 0
    strategy_used: str = ""
```

## URL Processing Implementation

### URL Normalization

```python
def normalize_url(url: str) -> str:
    """
    Normalize URL by handling Unicode escapes and removing tracking parameters.
    
    Enhanced to handle malformed URLs with Unicode escape sequences.
    """
    try:
        # Handle Unicode escape sequences
        if '\\\\u' in url:
            url = url.replace('\\\\u', '\\u')
            url = url.encode().decode('unicode_escape')
        elif '\\u' in url:
            url = url.encode().decode('unicode_escape')
        
        parsed = urlparse(url)
        
        # Remove tracking parameters
        tracking_params = [
            'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
            'fbclid', 'gclid', 'ref', 'source', 'campaign'
        ]
        
        # Reconstruct clean URL
        if parsed.query:
            query_params = []
            for param in parsed.query.split('&'):
                if '=' in param:
                    key, value = param.split('=', 1)
                    if key.lower() not in tracking_params:
                        query_params.append(param)
            query = '&'.join(query_params)
        else:
            query = ''
        
        normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        if query:
            normalized += f"?{query}"
            
        return normalized
        
    except Exception as e:
        logger.warning(f"URL normalization failed for {url}: {str(e)}")
        return url
```

### Content Extraction Enhancement

```python
def _extract_content_data(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
    """Enhanced content extraction with multiple fallback strategies."""
    
    return {
        'title': self._extract_title(soup),
        'author': self._extract_author(soup),
        'publish_date': self._extract_publish_date(soup),
        'content': self._extract_content(soup),
        'paywall_detected': self._detect_paywall(soup, str(soup))[0],
        'paywall_indicators': self._detect_paywall(soup, str(soup))[1]
    }

def _extract_title(self, soup: BeautifulSoup) -> str:
    """Extract title with multiple fallback strategies."""
    
    # Priority order for title extraction
    title_selectors = [
        'h1.article-title',
        'h1.entry-title',
        'h1.post-title',
        'h1[data-testid="headline"]',
        'h1.headline',
        '.article-header h1',
        '.entry-header h1',
        'article h1',
        'h1',
        'title'
    ]
    
    for selector in title_selectors:
        try:
            element = soup.select_one(selector)
            if element and element.get_text(strip=True):
                title = element.get_text(strip=True)
                # Clean up title
                title = re.sub(r'\s+', ' ', title)
                title = title.replace('\n', ' ').replace('\r', ' ')
                return title[:500]  # Truncate to model limit
        except Exception:
            continue
    
    return ""

def _extract_author(self, soup: BeautifulSoup) -> str:
    """Extract author with multiple fallback strategies."""
    
    author_selectors = [
        '[data-testid="author-name"]',
        '.author-name',
        '.byline-author',
        '.article-author',
        '.entry-author',
        'span.author',
        '.byline .author',
        'meta[name="author"]',
        'meta[property="article:author"]'
    ]
    
    for selector in author_selectors:
        try:
            if selector.startswith('meta'):
                element = soup.select_one(selector)
                if element and element.get('content'):
                    return element.get('content')[:200]
            else:
                element = soup.select_one(selector)
                if element and element.get_text(strip=True):
                    author = element.get_text(strip=True)
                    # Clean up author name
                    author = re.sub(r'\s+', ' ', author)
                    author = author.replace('By ', '').replace('by ', '')
                    return author[:200]
        except Exception:
            continue
    
    return ""
```

## Celery Task Implementation

### Individual Article Processing

```python
@shared_task(bind=True, max_retries=3)
def fetch_article_content(self, article_id: int) -> Dict[str, Any]:
    """
    Fetch content for a single article with retry logic.
    """
    
    try:
        article = Article.objects.get(id=article_id)
        
        # Validation
        if not article.needs_fetch:
            return {
                'success': False,
                'article_id': article_id,
                'message': f'Article no longer needs fetching. Status: {article.fetch_status}'
            }
        
        # Perform extraction
        fetcher = ContentFetcher()
        result = fetcher.fetch_article_content(article)
        
        if result.success:
            return {
                'success': True,
                'article_id': article_id,
                'strategy_used': result.strategy_used,
                'duration_ms': result.duration_ms,
                'has_basic_content': bool(article.basic_content),
                'has_raw_html': bool(article.raw_html),
                'paywall_detected': article.paywall_detected
            }
        else:
            # Intelligent retry logic
            if article.fetch_attempts < 3:
                raise self.retry(countdown=60 * (2 ** self.request.retries))
            
            return {
                'success': False,
                'article_id': article_id,
                'error_message': result.error_message,
                'attempts': article.fetch_attempts
            }
            
    except Article.DoesNotExist:
        return {
            'success': False,
            'article_id': article_id,
            'error_message': 'Article not found'
        }
    
    except Exception as e:
        logger.exception(f"Unexpected error in fetch for article {article_id}: {str(e)}")
        
        # Retry on unexpected errors
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        return {
            'success': False,
            'article_id': article_id,
            'error_message': str(e),
            'retries_exhausted': True
        }
```

### Batch Processing Implementation

```python
@shared_task
def fetch_batch_articles(article_ids: List[int]) -> Dict[str, Any]:
    """
    Fetch content for multiple articles in a batch.
    Optimized for bulk operations with statistical aggregation.
    """
    
    if not article_ids:
        return {
            'processed': 0,
            'successful': 0,
            'failed': 0,
            'message': 'No article IDs provided'
        }
    
    try:
        # Efficient querying
        articles = Article.objects.filter(
            id__in=article_ids,
            fetch_status=FetchStatus.PENDING
        )
        
        if not articles:
            return {
                'processed': 0,
                'successful': 0,
                'failed': 0,
                'message': 'No articles need fetching'
            }
        
        # Batch processing with performance tracking
        fetcher = ContentFetcher()
        results = []
        start_time = time.time()
        
        for article in articles:
            result = fetcher.fetch_article_content(article)
            results.append(result)
            
            # Rate limiting for respectful crawling
            if not result.success:
                time.sleep(1)  # Backoff on failures
        
        # Compile comprehensive statistics
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful
        total_duration = time.time() - start_time
        
        return {
            'processed': len(results),
            'successful': successful,
            'failed': failed,
            'total_duration_seconds': total_duration,
            'average_duration_per_article': total_duration / len(results) if results else 0,
            'article_ids': article_ids,
            'success_rate': successful / len(results) if results else 0,
            'results': [
                {
                    'article_id': r.article.id if r.article else None,
                    'success': r.success,
                    'strategy_used': r.strategy_used,
                    'duration_ms': r.duration_ms,
                    'error_message': r.error_message
                }
                for r in results
            ]
        }
        
    except Exception as e:
        logger.exception(f"Batch fetch failed for articles {article_ids}: {str(e)}")
        return {
            'processed': 0,
            'successful': 0,
            'failed': len(article_ids),
            'error_message': str(e),
            'article_ids': article_ids
        }
```

## Django Model Integration

### Article Model Enhancement

```python
class Article(models.Model):
    """Enhanced Article model with comprehensive fetcher integration."""
    
    # Fetch status tracking
    fetch_status = models.CharField(
        max_length=20, 
        choices=FetchStatus.choices,
        default=FetchStatus.PENDING,
        db_index=True
    )
    fetch_attempts = models.IntegerField(default=0)
    last_fetch_attempt = models.DateTimeField(null=True, blank=True)
    
    # Content storage
    raw_html = models.TextField(blank=True)
    basic_content = models.TextField(blank=True)
    
    # Enhanced metadata
    title = models.CharField(max_length=500)
    author = models.CharField(max_length=200, blank=True)
    
    # Paywall detection
    paywall_detected = models.BooleanField(default=False)
    paywall_indicators = models.JSONField(default=list)
    
    # Performance tracking
    fetch_strategy_used = models.CharField(max_length=50, blank=True)
    fetch_duration_ms = models.IntegerField(default=0)
    extraction_metadata = models.JSONField(default=dict)
    
    @property
    def needs_fetch(self) -> bool:
        """Determine if article needs content fetching."""
        return (
            self.fetch_status == FetchStatus.PENDING or
            (self.fetch_status == FetchStatus.FAILED and self.fetch_attempts < 3)
        )
    
    @property
    def can_retry_fetch(self) -> bool:
        """Determine if article can be retried for fetching."""
        return (
            self.fetch_status == FetchStatus.FAILED and
            self.fetch_attempts < 3 and
            self.last_fetch_attempt and
            timezone.now() - self.last_fetch_attempt > timedelta(hours=1)
        )
    
    class Meta:
        indexes = [
            models.Index(fields=['fetch_status', 'created_at']),
            models.Index(fields=['fetch_attempts', 'last_fetch_attempt']),
        ]
```

## Error Handling Patterns

### Graceful Error Handling

```python
def _handle_fetch_error(self, article: Article, error_message: str, start_time: float) -> FetchResult:
    """
    Handle fetch errors with intelligent retry logic and status management.
    """
    
    duration_ms = int((time.time() - start_time) * 1000)
    
    # Determine if error is retryable
    retryable_errors = [
        'timeout', 'connection', 'network', 'rate limit', 
        '502', '503', '504', 'temporary'
    ]
    
    is_retryable = any(keyword in error_message.lower() for keyword in retryable_errors)
    
    with transaction.atomic():
        if is_retryable and article.fetch_attempts < 3:
            # Mark for retry
            article.fetch_status = FetchStatus.FAILED
            article.fetch_error_message = f"Retryable error: {error_message}"
            article.save()
            
            logger.warning(f"Retryable error for article {article.id}: {error_message}")
        else:
            # Permanent failure
            article.fetch_status = FetchStatus.FAILED
            article.fetch_error_message = f"Permanent error: {error_message}"
            article.save()
            
            logger.error(f"Permanent fetch failure for article {article.id}: {error_message}")
    
    return FetchResult(
        success=False,
        article=article,
        error_message=error_message,
        duration_ms=duration_ms
    )
```

## Performance Optimization Patterns

### Connection Pooling

```python
class ContentFetcher:
    """Implementation with connection pooling optimization."""
    
    def __init__(self):
        self.strategies = [...]
        
        # Shared session for connection pooling
        self.session = self._create_optimized_session()
    
    def _create_optimized_session(self):
        """Create optimized requests session with connection pooling."""
        session = requests.Session()
        
        # Connection pooling configuration
        adapter = HTTPAdapter(
            pool_connections=10,
            pool_maxsize=20,
            max_retries=Retry(
                total=3,
                backoff_factor=0.3,
                status_forcelist=[500, 502, 503, 504]
            )
        )
        
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        
        # Default headers for efficiency
        session.headers.update({
            'Connection': 'keep-alive',
            'Accept-Encoding': 'gzip, deflate',
        })
        
        return session
```

### Memory Management

```python
def _extract_with_strategies(self, url: str) -> ExtractionResult:
    """Extract with memory management optimization."""
    
    for strategy in self.strategies:
        if not strategy.available:
            continue
            
        try:
            result = strategy.extract(url)
            
            if result.success:
                # Validate content size to prevent memory issues
                if len(result.raw_html) > 10 * 1024 * 1024:  # 10MB limit
                    logger.warning(f"Content too large for {url}: {len(result.raw_html)} bytes")
                    result.raw_html = result.raw_html[:10 * 1024 * 1024]
                
                return result
            
            # Clean up failed attempts to free memory
            del result
            
        except Exception as e:
            logger.exception(f"Strategy {strategy.name} failed: {str(e)}")
            continue
        
        # Force garbage collection between strategies
        import gc
        gc.collect()
    
    return ExtractionResult(
        success=False,
        error_message="All extraction strategies failed"
    )
```

## Testing Implementation

### Strategy Testing

```python
class TestContentFetcher(TestCase):
    """Comprehensive test suite for content fetcher."""
    
    def setUp(self):
        self.fetcher = ContentFetcher()
        self.test_urls = [
            'https://arstechnica.com/tech-policy/2025/01/example/',
            'https://www.politico.com/news/2025/01/example',
            'https://www.nytimes.com/2025/01/example.html',
        ]
    
    def test_browser_simulation_strategy(self):
        """Test browser simulation strategy."""
        strategy = BrowserSimulationStrategy()
        
        for url in self.test_urls:
            with self.subTest(url=url):
                result = strategy.extract(url)
                
                # Validate result structure
                self.assertIsInstance(result, ExtractionResult)
                self.assertIsInstance(result.success, bool)
                
                if result.success:
                    self.assertGreater(len(result.raw_html), 0)
                    self.assertGreater(len(result.basic_content), 0)
    
    def test_paywall_detection(self):
        """Test paywall detection accuracy."""
        strategy = BrowserSimulationStrategy()
        
        # Test with known paywall URLs
        paywall_urls = [
            'https://www.wsj.com/articles/example',
            'https://www.nytimes.com/2025/01/example.html',
        ]
        
        for url in paywall_urls:
            result = strategy.extract(url)
            if result.success:
                # Should detect paywall indicators
                self.assertTrue(len(result.paywall_indicators) > 0)
```

## Configuration and Settings

### Django Settings Integration

```python
# settings.py
CONTENT_FETCHER_SETTINGS = {
    'EXTRACTION_TIMEOUT': 15,
    'FAST_FETCH_TIMEOUT': 10,
    'FAST_FETCH_MAX_RETRIES': 3,
    'DEFAULT_USER_AGENT': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'MAX_CONTENT_SIZE': 10 * 1024 * 1024,  # 10MB
    'ENABLE_ARCHIVE_ORG': True,
    'ENABLE_OUTLINE_COM': True,
    'RATE_LIMIT_DELAY': 1.0,  # seconds between requests
}

# Celery configuration for fetcher tasks
CELERY_ROUTES = {
    'apps.content.fetcher.tasks.fetch_article_content': {'queue': 'fetcher'},
    'apps.content.fetcher.tasks.fetch_batch_articles': {'queue': 'fetcher_batch'},
}
```

This implementation guide provides comprehensive coverage of the technical patterns and integration approaches used in the Content Fetcher service, enabling developers to understand, maintain, and extend the system effectively. 