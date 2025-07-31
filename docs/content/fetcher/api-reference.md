# Content Fetcher API Reference

> **Complete API reference for classes, methods, and interfaces in the DailyBrief content fetching service**

## Core Classes

### ContentFetcher

Main orchestrator class for content extraction operations.

```python
class ContentFetcher:
    """
    Fast content fetcher optimized for Step 1 extraction.
    Focuses on speed over processing quality.
    """
```

#### Constructor

```python
def __init__(self):
    """
    Initialize ContentFetcher with configured strategies and settings.
    
    Attributes:
        strategies (List[ExtractionStrategy]): Ordered list of extraction strategies
        timeout_seconds (int): Request timeout from settings
        max_retries (int): Maximum retry attempts from settings
    """
```

#### Methods

##### fetch_article_content()

```python
def fetch_article_content(self, article: Article) -> FetchResult:
    """
    Fast content fetching for a single article.
    Only performs Step 1 extraction - no processing.
    
    Args:
        article (Article): Django Article model instance to fetch content for
        
    Returns:
        FetchResult: Result containing success status, extracted content, and metadata
        
    Raises:
        None: All exceptions are caught and returned in FetchResult.error_message
    """
```

##### fetch_multiple_articles()

```python
def fetch_multiple_articles(self, articles: List[Article]) -> List[FetchResult]:
    """
    Fetch content for multiple articles efficiently.
    
    Args:
        articles (List[Article]): List of Article instances to process
        
    Returns:
        List[FetchResult]: List of results for each article
    """
```

### FetchManager

Batch processing manager for efficient bulk operations.

```python
class FetchManager:
    """
    Batch processing manager for content fetching operations.
    Optimizes bulk operations and resource utilization.
    """
```

#### Methods

##### fetch_pending_articles()

```python
def fetch_pending_articles(self, limit: int = 50) -> Dict[str, Any]:
    """
    Fetch content for pending articles automatically.
    
    Args:
        limit (int): Maximum number of articles to process
        
    Returns:
        Dict[str, Any]: Processing statistics and results
            - processed (int): Number of articles processed
            - successful (int): Number of successful extractions
            - failed (int): Number of failed extractions
            - duration_seconds (float): Total processing time
            - articles (List[Dict]): Individual article results
    """
```

##### retry_failed_articles()

```python
def retry_failed_articles(self, max_retries: int = 3) -> Dict[str, Any]:
    """
    Retry fetching for articles that failed but haven't exceeded max attempts.
    
    Args:
        max_retries (int): Maximum retry attempts per article
        
    Returns:
        Dict[str, Any]: Retry operation statistics
    """
```

## Strategy Classes

### ExtractionStrategy (Abstract Base Class)

```python
class ExtractionStrategy(ABC):
    """Abstract base class for content extraction strategies."""
```

#### Properties

##### available

```python
@property
@abstractmethod
def available(self) -> bool:
    """
    Check if this strategy is available for use.
    
    Returns:
        bool: True if strategy can be used, False otherwise
    """
```

#### Methods

##### extract()

```python
@abstractmethod
def extract(self, url: str) -> ExtractionResult:
    """
    Extract content from URL using this strategy.
    
    Args:
        url (str): URL to extract content from
        
    Returns:
        ExtractionResult: Extraction outcome with content and metadata
    """
```

### BrowserSimulationStrategy

Advanced browser simulation strategy for realistic browsing behavior.

```python
class BrowserSimulationStrategy(ExtractionStrategy):
    """
    Advanced browser simulation strategy to bypass 403 Forbidden errors.
    Mimics real human browsing behavior with realistic headers, sessions, and timing.
    """
```

#### Attributes

- `name (str)`: Strategy identifier "BrowserSimulation"
- `realistic_user_agents (List[str])`: Modern browser user agent strings
- `common_referers (List[str])`: Common referer URLs for organic appearance
- `session (requests.Session)`: Persistent session with connection pooling

#### Methods

##### extract()

```python
def extract(self, url: str) -> ExtractionResult:
    """
    Extract content using advanced browser simulation.
    
    Tries multiple browser configurations in sequence:
    1. Chrome simulation
    2. Firefox simulation  
    3. Safari simulation
    4. Mobile simulation
    
    Args:
        url (str): URL to extract content from
        
    Returns:
        ExtractionResult: Best extraction result from attempted configurations
    """
```

### AdvancedBypassStrategy

Advanced bypass techniques for highly restrictive sites.

```python
class AdvancedBypassStrategy(ExtractionStrategy):
    """
    Advanced bypass techniques for highly restrictive sites.
    Uses alternative access methods when direct access fails.
    """
```

#### Methods

##### extract()

```python
def extract(self, url: str) -> ExtractionResult:
    """
    Extract using advanced bypass techniques.
    
    Attempts multiple access methods:
    1. Advanced headers with Tor-like anonymity
    2. Archive.org Wayback Machine access
    3. outline.com proxy service
    4. AMP/mobile version detection
    5. RSS feed content extraction
    
    Args:
        url (str): URL to extract content from
        
    Returns:
        ExtractionResult: Best result from attempted methods
    """
```

### PaywallBypassStrategy

Crawler bot simulation for subscription content access.

```python
class PaywallBypassStrategy(ExtractionStrategy):
    """
    Crawler bot simulation for subscription content access.
    Simulates search engine and academic crawlers.
    """
```

#### Attributes

- `crawler_user_agents (Dict[str, str])`: Modern crawler bot user agents
- `academic_crawlers (List[str])`: Academic and research crawler identities

### BeautifulSoupStrategy

Reliable fallback strategy using basic requests.

```python
class BeautifulSoupStrategy(ExtractionStrategy):
    """
    Reliable fallback strategy for basic content extraction.
    Uses standard requests library with minimal overhead.
    """
```

## Data Structures

### ExtractionResult

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
```

#### Fields

- `success (bool)`: Whether extraction was successful
- `raw_html (str)`: Complete HTML content of the page
- `basic_content (str)`: Extracted text content without HTML
- `title (str)`: Article title extracted from page
- `author (str)`: Article author if available
- `publish_date (Optional[str])`: Publication date if detected
- `extraction_metadata (Dict[str, Any])`: Additional extraction metadata
- `paywall_detected (bool)`: Whether paywall was detected
- `paywall_indicators (List[str])`: List of detected paywall signals
- `error_message (str)`: Error description if extraction failed
- `duration_ms (int)`: Extraction duration in milliseconds
- `strategy_used (str)`: Name of strategy that produced this result

### FetchResult

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

#### Fields

- `success (bool)`: Whether overall fetch operation was successful
- `article (Optional[Article])`: Django Article model instance
- `error_message (str)`: Error description if fetch failed
- `extraction_result (Optional[ExtractionResult])`: Detailed extraction result
- `duration_ms (int)`: Total fetch duration in milliseconds
- `strategy_used (str)`: Strategy that successfully extracted content

## Utility Functions

### URL Processing

#### normalize_url()

```python
def normalize_url(url: str) -> str:
    """
    Normalize URL by removing tracking parameters and fragments.
    Enhanced to handle Unicode escape sequences.
    
    Args:
        url (str): URL to normalize
        
    Returns:
        str: Normalized URL with tracking parameters removed
        
    Example:
        >>> normalize_url("https://example.com/article?utm_source=twitter&id=123")
        "https://example.com/article?id=123"
        
        >>> normalize_url("https://example.com/article\\u003fid\\u003d123")
        "https://example.com/article?id=123"
    """
```

#### validate_url()

```python
def validate_url(url: str) -> bool:
    """
    Validate if a URL is properly formatted.
    
    Args:
        url (str): URL to validate
        
    Returns:
        bool: True if URL is valid, False otherwise
        
    Example:
        >>> validate_url("https://example.com")
        True
        >>> validate_url("not-a-url")
        False
    """
```

### HTTP Utilities

#### get_request_headers()

```python
def get_request_headers(user_agent: str = None, referer: str = None) -> Dict[str, str]:
    """
    Get standard HTTP headers for requests.
    
    Args:
        user_agent (str, optional): Custom user agent string
        referer (str, optional): Referer header value
        
    Returns:
        Dict[str, str]: Complete HTTP headers dictionary
    """
```

#### make_http_request()

```python
def make_http_request(url: str, headers: Dict[str, str] = None, timeout: int = 10) -> requests.Response:
    """
    Make a simple HTTP request with error handling.
    
    Args:
        url (str): URL to request
        headers (Dict[str, str], optional): HTTP headers
        timeout (int): Request timeout in seconds
        
    Returns:
        requests.Response: HTTP response object
        
    Raises:
        requests.RequestException: If request fails
    """
```

### Content Processing

#### clean_extracted_text()

```python
def clean_extracted_text(text: str) -> str:
    """
    Basic text cleaning for extracted content.
    
    Args:
        text (str): Raw extracted text
        
    Returns:
        str: Cleaned text with normalized whitespace
    """
```

## Celery Tasks

### fetch_article_content

```python
@shared_task(bind=True, max_retries=3)
def fetch_article_content(self, article_id: int) -> Dict[str, Any]:
    """
    Fetch content for a single article (Step 1 only).
    Optimized for speed - no processing, just raw extraction.
    
    Args:
        article_id (int): ID of Article model instance to fetch
        
    Returns:
        Dict[str, Any]: Task result with success status and metrics
            - success (bool): Whether fetch was successful
            - article_id (int): ID of processed article
            - strategy_used (str): Strategy that succeeded
            - duration_ms (int): Fetch duration in milliseconds
            - has_basic_content (bool): Whether basic content was extracted
            - has_raw_html (bool): Whether raw HTML was extracted
            - paywall_detected (bool): Whether paywall was detected
            - error_message (str): Error description if failed
    
    Task Configuration:
        - bind=True: Task instance is passed as first argument
        - max_retries=3: Maximum retry attempts
        - queue: 'fetcher' (if configured)
    """
```

### fetch_batch_articles

```python
@shared_task
def fetch_batch_articles(article_ids: List[int]) -> Dict[str, Any]:
    """
    Fetch content for multiple articles in a batch.
    More efficient than individual tasks for bulk operations.
    
    Args:
        article_ids (List[int]): List of Article IDs to process
        
    Returns:
        Dict[str, Any]: Batch processing results
            - processed (int): Number of articles processed
            - successful (int): Number of successful extractions
            - failed (int): Number of failed extractions
            - total_duration_seconds (float): Total processing time
            - success_rate (float): Success rate as decimal (0.0-1.0)
            - results (List[Dict]): Individual article results
    """
```

### fetch_pending_articles

```python
@shared_task
def fetch_pending_articles(limit: int = 50) -> Dict[str, Any]:
    """
    Fetch content for pending articles automatically.
    Runs periodically to process new articles.
    
    Args:
        limit (int): Maximum number of articles to process
        
    Returns:
        Dict[str, Any]: Processing statistics
    
    Scheduling:
        Typically scheduled via Celery Beat for automated processing
    """
```

### retry_failed_fetches

```python
@shared_task
def retry_failed_fetches(max_retries: int = 3) -> Dict[str, Any]:
    """
    Retry fetching for articles that failed but haven't exceeded max attempts.
    
    Args:
        max_retries (int): Maximum retry attempts per article
        
    Returns:
        Dict[str, Any]: Retry operation statistics
    """
```

## Django Model Integration

### Article Model Fields

The fetcher service manages the following Article model fields:

#### Status Fields

- `fetch_status`: Current fetch status (PENDING, FETCHING, COMPLETED, FAILED)
- `fetch_attempts`: Number of fetch attempts made
- `last_fetch_attempt`: Timestamp of last fetch attempt

#### Content Fields

- `raw_html`: Complete HTML content of the article page
- `basic_content`: Extracted text content without HTML markup

#### Metadata Fields

- `title`: Article title (enhanced by fetcher if not present)
- `author`: Article author (extracted during fetching)

#### Paywall Fields

- `paywall_detected`: Boolean indicating paywall presence
- `paywall_indicators`: JSON array of detected paywall signals

#### Performance Fields

- `fetch_strategy_used`: Name of successful extraction strategy
- `fetch_duration_ms`: Fetch operation duration in milliseconds
- `extraction_metadata`: JSON object with additional extraction data

### Model Properties

#### needs_fetch

```python
@property
def needs_fetch(self) -> bool:
    """
    Determine if article needs content fetching.
    
    Returns:
        bool: True if article should be fetched
    """
```

#### can_retry_fetch

```python
@property
def can_retry_fetch(self) -> bool:
    """
    Determine if article can be retried for fetching.
    
    Returns:
        bool: True if article is eligible for retry
    """
```

## Exception Handling

### Strategy Exceptions

All strategy methods catch exceptions internally and return failed ExtractionResult objects rather than raising exceptions. This ensures the strategy pattern can continue attempting other strategies.

### Task Retry Logic

Celery tasks implement intelligent retry logic:

- **Transient Errors**: Network timeouts, rate limits, 5xx errors
- **Permanent Errors**: 4xx errors, invalid URLs, content structure issues
- **Retry Backoff**: Exponential backoff with 60s base delay

### Error Categorization

```python
retryable_errors = [
    'timeout', 'connection', 'network', 'rate limit', 
    '502', '503', '504', 'temporary'
]
```

## Configuration

### Django Settings

```python
# Content Fetcher Configuration
CONTENT_FETCHER_SETTINGS = {
    'EXTRACTION_TIMEOUT': 15,
    'FAST_FETCH_TIMEOUT': 10, 
    'FAST_FETCH_MAX_RETRIES': 3,
    'DEFAULT_USER_AGENT': 'Mozilla/5.0 (...)',
    'MAX_CONTENT_SIZE': 10 * 1024 * 1024,  # 10MB
    'ENABLE_ARCHIVE_ORG': True,
    'ENABLE_OUTLINE_COM': True,
    'RATE_LIMIT_DELAY': 1.0,
}
```

### Celery Configuration

```python
CELERY_ROUTES = {
    'apps.content.fetcher.tasks.fetch_article_content': {'queue': 'fetcher'},
    'apps.content.fetcher.tasks.fetch_batch_articles': {'queue': 'fetcher_batch'},
}
``` 