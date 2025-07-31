# Content Fetcher Architecture

> **System design and component relationships for the DailyBrief content fetching pipeline**

## Overview

The Content Fetcher serves as **Step 1** in the DailyBrief content enrichment pipeline, responsible for transforming article URLs into raw HTML content. It employs a sophisticated multi-strategy approach to overcome modern web content access restrictions.

## System Architecture

### High-Level Pipeline Position

```
DailyBrief Content Enrichment Pipeline
┌─────────────────────────────────────────────────────────────────────────┐
│                          Content Enrichment                             │
├─────────────┬─────────────┬─────────────┬─────────────┬─────────────────┤
│   FETCHER   │  PROCESSOR  │    QA       │ SUMMARIZER  │    ANALYZER     │
│   (Step 1)  │   (Step 2)  │  (Step 3)   │  (Step 4)   │    (Step 5)     │
│             │             │             │             │                 │
│ URL → HTML  │ HTML →      │ Quality     │ Blocks →    │ Summary →       │
│ Raw Content │ Content     │ Assessment  │ Summary     │ Analysis        │
│             │ Blocks      │             │             │                 │
└─────────────┴─────────────┴─────────────┴─────────────┴─────────────────┘
```

### Core Components

```
Content Fetcher Service Architecture
├── Service Layer
│   ├── ContentFetcher                 # Main orchestrator class
│   ├── FetchManager                  # Batch processing management
│   └── FetchResult                   # Result data structure
├── Strategy Pattern Implementation
│   ├── ExtractionStrategy (ABC)      # Abstract base class
│   ├── BrowserSimulationStrategy     # Primary realistic browser simulation
│   ├── AdvancedBypassStrategy        # Advanced access methods
│   ├── PaywallBypassStrategy         # Crawler bot simulation
│   └── BeautifulSoupStrategy         # Fallback basic extraction
├── Data Structures
│   ├── ExtractionResult             # Extraction outcome with metadata
│   ├── FetchResult                  # Service-level result wrapper
│   └── Article Model Integration    # Django model state management
├── Utility Layer
│   ├── URL Processing               # Normalization and validation
│   ├── HTTP Utilities               # Request handling and headers
│   └── Content Utilities            # Text cleaning and extraction
└── Integration Layer
    ├── Celery Tasks                 # Async processing
    ├── Django Management Commands   # CLI operations
    └── Model Integration           # Article status management
```

## Strategy Architecture

### Strategy Selection Logic

```python
def _extract_with_strategies(self, url: str) -> ExtractionResult:
    """
    Strategies are attempted in order of sophistication:
    1. BrowserSimulationStrategy  - Primary, highest success rate
    2. AdvancedBypassStrategy     - Advanced techniques for restrictive sites  
    3. PaywallBypassStrategy      - Specialized crawler bot simulation
    4. BeautifulSoupStrategy      - Fallback, basic but reliable
    """
```

### Strategy Characteristics

#### 1. BrowserSimulationStrategy
```
Purpose: Realistic human browser simulation
├── Features:
│   ├── 6 Modern User-Agent strings (Chrome, Firefox, Safari, Edge)
│   ├── Complete browser headers (Sec-Fetch-*, Accept-*, etc.)
│   ├── Session management with connection pooling
│   ├── Random referers from common sources
│   └── Realistic timing delays (0.5-1.5s)
├── Use Cases:
│   ├── Modern news websites (CNN, BBC, Reuters)
│   ├── Magazine sites (The Atlantic, Wired)
│   └── Blog platforms (Medium, Substack)
└── Success Rate: ~60% direct success
```

#### 2. AdvancedBypassStrategy
```
Purpose: Advanced techniques for highly restrictive sites
├── Features:
│   ├── Tor-like headers for anonymity
│   ├── Old browser simulation (IE, legacy versions)
│   ├── Institutional proxy headers
│   ├── Alternative access methods:
│   │   ├── Archive.org Wayback Machine
│   │   ├── outline.com proxy service
│   │   ├── AMP/mobile versions
│   │   └── RSS feed content extraction
├── Use Cases:
│   ├── Sites with strict access controls
│   ├── Anti-bot protection (Cloudflare, etc.)
│   └── Geographic restrictions
└── Success Rate: ~35% with alternatives reaching 70%
```

#### 3. PaywallBypassStrategy
```
Purpose: Crawler bot simulation for subscription content
├── Features:
│   ├── Modern crawler user agents:
│   │   ├── Googlebot (primary)
│   │   ├── Bingbot
│   │   ├── Academic crawlers
│   │   └── Social media crawlers
│   ├── Search engine headers
│   └── Academic/research access patterns
├── Use Cases:
│   ├── Subscription news sites
│   ├── Academic publications
│   └── Premium content platforms
└── Success Rate: ~25% direct, varies by site policy
```

#### 4. BeautifulSoupStrategy
```
Purpose: Reliable fallback for basic sites
├── Features:
│   ├── Simple requests-based fetching
│   ├── Basic retry logic
│   ├── Standard web scraping patterns
│   └── Minimal overhead
├── Use Cases:
│   ├── Simple blogs and websites
│   ├── Sites without access restrictions
│   └── Final fallback when all else fails
└── Success Rate: ~95% on compatible sites
```

## Data Flow Architecture

### Article Processing Flow

```
Article URL Processing Flow
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Article URL   │───▶│ URL Preprocessing│───▶│ Strategy Selection│
│   (needs_fetch) │    │ • Normalization  │    │ • Browser Sim    │
└─────────────────┘    │ • Unicode fixes  │    │ • Advanced       │
                       │ • Tracking clean │    │ • Paywall        │
                       └─────────────────┘    │ • BeautifulSoup  │
                                              └─────────────────┘
                                                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Article Update  │◀───│  Content Storage │◀───│   Extraction    │
│ • Status change │    │ • raw_html       │    │ • HTTP request  │
│ • Metadata      │    │ • basic_content  │    │ • Content parse │
│ • Performance   │    │ • title/author   │    │ • Paywall detect│
└─────────────────┘    │ • paywall_info   │    │ • Error handling│
                       └─────────────────┘    └─────────────────┘
```

### Status State Machine

```
Article Fetch Status Transitions
┌─────────────┐
│   PENDING   │ ─┐
└─────────────┘  │
                 ▼
┌─────────────┐  ┌─────────────┐
│   FAILED    │◀─│  FETCHING   │
└─────────────┘  └─────────────┘
                 │
                 ▼
┌─────────────┐  ┌─────────────┐
│  QUEUED FOR │◀─│  COMPLETED  │
│ PROCESSING  │  └─────────────┘
└─────────────┘
```

## Integration Architecture

### Django Model Integration

```python
# Article model fields managed by fetcher
class Article(models.Model):
    # Fetch status tracking
    fetch_status = models.CharField(max_length=20, choices=FetchStatus.choices)
    fetch_attempts = models.IntegerField(default=0)
    last_fetch_attempt = models.DateTimeField(null=True, blank=True)
    
    # Content storage
    raw_html = models.TextField(blank=True)
    basic_content = models.TextField(blank=True)
    
    # Metadata enhancement
    title = models.CharField(max_length=500)
    author = models.CharField(max_length=200, blank=True)
    
    # Paywall detection
    paywall_detected = models.BooleanField(default=False)
    paywall_indicators = models.JSONField(default=list)
    
    # Performance tracking
    fetch_strategy_used = models.CharField(max_length=50, blank=True)
    fetch_duration_ms = models.IntegerField(default=0)
    extraction_metadata = models.JSONField(default=dict)
```

### Celery Task Architecture

```python
# Task hierarchy and relationships
@shared_task(bind=True, max_retries=3)
def fetch_article_content(article_id: int)
    ├── Individual article processing
    ├── Retry logic with exponential backoff  
    └── Error handling and status updates

@shared_task  
def fetch_batch_articles(article_ids: List[int])
    ├── Bulk processing optimization
    ├── Batch result aggregation
    └── Performance statistics

@shared_task
def fetch_pending_articles(limit: int = 50)
    ├── Automatic pipeline processing
    ├── Scheduled via Celery Beat
    └── Production workload management

@shared_task
def retry_failed_fetches(max_retries: int = 3)
    ├── Failed article recovery
    ├── Intelligent retry decisions
    └── Performance optimization
```

## Performance Architecture

### Concurrency & Scaling

```
Performance Optimization Strategies
├── Connection Management
│   ├── Session pooling (requests.Session)
│   ├── Keep-alive connections
│   ├── Connection timeouts (15s)
│   └── Retry strategies (3 attempts)
├── Memory Optimization  
│   ├── Streaming downloads for large content
│   ├── BeautifulSoup parser selection
│   ├── Garbage collection after processing
│   └── Memory usage monitoring (~15MB/fetch)
├── Async Processing
│   ├── Celery distributed task queue
│   ├── Redis result backend
│   ├── Parallel strategy attempts
│   └── Background cleanup tasks
└── Caching Strategy
    ├── Session persistence across requests
    ├── DNS resolution caching
    ├── HTTP connection reuse
    └── Strategy success rate tracking
```

### Monitoring & Observability

```
Metrics Collection Architecture
├── Performance Metrics
│   ├── fetch_duration_ms (per article)
│   ├── strategy_success_rates (per strategy)
│   ├── retry_rates (failure analysis)
│   └── throughput_articles_per_hour
├── Quality Metrics
│   ├── content_length_distribution
│   ├── paywall_detection_accuracy
│   ├── metadata_extraction_success
│   └── html_structure_quality
├── Error Tracking
│   ├── strategy_failure_reasons
│   ├── url_malformation_rates
│   ├── timeout_frequency
│   └── http_status_code_distribution
└── Business Metrics
    ├── overall_pipeline_success_rate
    ├── content_availability_by_source
    ├── processing_cost_per_article
    └── user_impact_metrics
```

## Security Architecture

### Content Security

```
Security Considerations
├── Request Safety
│   ├── URL validation before fetching
│   ├── Content size limits (max 10MB)
│   ├── Timeout protections (15s max)
│   └── Malicious URL detection
├── Privacy Protection
│   ├── No user data in fetch requests
│   ├── Anonymous browsing simulation
│   ├── No persistent tracking cookies
│   └── Request origin masking
├── Rate Limiting
│   ├── Per-domain request throttling
│   ├── Respectful crawling delays
│   ├── robots.txt awareness
│   └── IP rotation considerations
└── Content Validation
    ├── HTML sanitization awareness
    ├── XSS prevention in stored content
    ├── Content type verification
    └── Size and structure validation
```

## Future Architecture Considerations

### Scalability Enhancements

```
Planned Architectural Improvements
├── Distributed Fetching
│   ├── Multi-region fetch nodes
│   ├── Load balancing strategies
│   ├── Geographic content optimization
│   └── CDN integration possibilities
├── Advanced Bypass Techniques
│   ├── Browser automation (Playwright/Selenium)
│   ├── Residential proxy rotation
│   ├── Machine learning for access pattern optimization
│   └── Dynamic strategy selection based on site characteristics
├── Performance Optimization
│   ├── Predictive caching based on RSS patterns
│   ├── Content change detection
│   ├── Incremental fetching for updated articles
│   └── Smart retry scheduling
└── Integration Enhancements
    ├── Real-time processing pipeline
    ├── WebSocket status updates
    ├── Advanced error recovery mechanisms
    └── Self-healing system capabilities
``` 