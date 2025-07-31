# Article Content Architecture - Analysis & Implementation Plan

## Overview

This document outlines our refined architecture for article content fetching, processing, and enhancement within the DailyBrief modular monolith. The design addresses the core challenge of transforming basic article metadata into rich, AI-enhanced content while handling real-world constraints like paywalls, access restrictions, and processing failures.

## Current State Analysis

### Existing Apps & Responsibilities
- **`newsapi/`** - NewsAPI integration with basic article metadata fetching
- **`feeds/`** - RSS feed management (future implementation)
- **`articles/`** - Article storage and retrieval APIs
- **`summariser/`** - AI summarization models (implementation pending)
- **Supporting apps:** `accounts/`, `digest/`, `notifications/`, `aiproviders/`

### Current Data Flow
```
NewsAPI → Article Metadata → Database Storage → Frontend Display
```

### Limitations
1. Only basic metadata available (title, description, URL, image)
2. No full article content
3. No AI-powered summaries or analysis
4. Limited content enrichment

## Proposed Architecture: 3-Domain Approach

### Domain-Driven Design Principles

Following DDD bounded contexts, we organize our system into three core domains:

#### 1. Sources Domain (Integration Layer)
**Responsibility:** Fetch article metadata from external sources
**Apps:** `sources/newsapi/`, `sources/feeds/`

#### 2. Content Domain (Processing Layer)  
**Responsibility:** Enhance articles with full content and AI analysis
**Apps:** `content/fetcher/`, `content/summariser/`, `content/analyzer/`

#### 3. Articles Domain (Repository Layer)
**Responsibility:** Manage article lifecycle and state
**Apps:** `articles/`

## Content Availability Challenges

### Real-World Content Access Issues

#### A. Access Restrictions
- **Paywalls:** Premium content behind subscription walls
- **Geo-blocking:** Content restricted by geographic location
- **User-agent blocking:** Sites blocking automated access
- **Rate limiting:** Aggressive throttling of requests
- **CAPTCHA protection:** Human verification requirements

#### B. Technical Issues
- **Server errors:** 5xx responses, timeouts
- **Invalid URLs:** 404s, redirects to unrelated content
- **Malformed HTML:** Broken markup, missing content
- **JavaScript-heavy sites:** Content loaded dynamically
- **CDN issues:** Content delivery network failures

#### C. Content Quality Issues
- **Incomplete articles:** Truncated or summary-only content
- **Advertisement pollution:** Excessive ads mixed with content
- **Poor formatting:** Unstructured or poorly marked-up content
- **Multiple languages:** Content in unexpected languages

### Content Availability States

We define a comprehensive state model for content availability:

```python
class ContentStatus(models.TextChoices):
    # Initial states
    PENDING = 'pending', 'Pending Fetch'
    FETCHING = 'fetching', 'Fetching Content'
    
    # Success states
    CONTENT_AVAILABLE = 'content_available', 'Full Content Available'
    PARTIAL_CONTENT = 'partial_content', 'Partial Content Available'
    METADATA_ONLY = 'metadata_only', 'Metadata Only (No Content)'
    
    # Failure states
    PAYWALL_BLOCKED = 'paywall_blocked', 'Blocked by Paywall'
    ACCESS_DENIED = 'access_denied', 'Access Denied'
    TECHNICAL_ERROR = 'technical_error', 'Technical Error'
    INVALID_URL = 'invalid_url', 'Invalid or Dead URL'
    TIMEOUT = 'timeout', 'Request Timeout'
    
    # Processing states
    PROCESSING = 'processing', 'AI Processing'
    COMPLETED = 'completed', 'Processing Completed'
    PROCESSING_FAILED = 'processing_failed', 'Processing Failed'
```

## Detailed Architecture Design

### Enhanced Article Model

```python
class Article(models.Model):
    # Existing fields...
    
    # Content availability tracking
    content_status = models.CharField(
        max_length=20, 
        choices=ContentStatus.choices, 
        default=ContentStatus.PENDING
    )
    content_fetch_attempts = models.IntegerField(default=0)
    max_fetch_attempts = models.IntegerField(default=3)
    last_fetch_attempt = models.DateTimeField(null=True, blank=True)
    fetch_error_message = models.TextField(blank=True)
    
    # Content quality indicators
    content_completeness = models.FloatField(null=True, blank=True)  # 0.0-1.0
    content_quality_score = models.FloatField(null=True, blank=True)  # 0.0-1.0
    
    # Processing tracking
    processing_status = models.CharField(
        max_length=20,
        choices=ProcessingStatus.choices,
        default=ProcessingStatus.PENDING
    )
    processing_attempts = models.IntegerField(default=0)
    last_processing_attempt = models.DateTimeField(null=True, blank=True)
    
    # Fallback content strategy
    use_description_as_content = models.BooleanField(default=False)
    content_source = models.CharField(
        max_length=20,
        choices=[
            ('full_fetch', 'Full Content Fetched'),
            ('partial_fetch', 'Partial Content Fetched'),
            ('description', 'Using Description'),
            ('summary_only', 'Summary Only'),
        ],
        null=True, blank=True
    )
```

### Content Fetcher Service

```python
class ContentFetcher:
    """
    Handles web scraping with robust error handling and fallback strategies.
    """
    
    def fetch_article_content(self, article: Article) -> ContentFetchResult:
        """
        Attempt to fetch full article content with comprehensive error handling.
        """
        
    def _detect_paywall(self, response: requests.Response) -> bool:
        """Detect common paywall patterns."""
        
    def _extract_content(self, html: str, url: str) -> ExtractedContent:
        """Extract clean content using multiple strategies."""
        
    def _assess_content_quality(self, content: str) -> ContentQuality:
        """Assess completeness and quality of extracted content."""
        
    def _determine_fallback_strategy(self, article: Article) -> FallbackStrategy:
        """Determine best fallback when content unavailable."""
```

### Fallback Content Strategies

When full content is unavailable, we implement intelligent fallbacks:

#### 1. Description Enhancement
- Use NewsAPI description as primary content
- Enhance with AI-generated context
- Mark clearly as "summary-based" content

#### 2. Multi-Source Aggregation
- Attempt fetching from multiple URLs for same story
- Cross-reference with other news sources
- Use archive.org or cached versions

#### 3. AI-Powered Content Generation
- Generate expanded content from headlines and descriptions
- Create contextual summaries from related articles
- Provide background information on topics

#### 4. Graceful Degradation
- Clearly indicate content limitations to users
- Provide "Read Full Article" links prominently
- Offer alternative sources when available

## Implementation Strategy

### Phase 1: Core Content Fetching (Week 1)

#### 1.1 Create Content Fetcher App
```bash
backend/apps/content/
├── fetcher/
│   ├── models.py          # ContentFetchLog, FetchAttempt
│   ├── services.py        # ContentFetcher, ContentExtractor
│   ├── tasks.py           # Celery tasks for async fetching
│   ├── utils.py           # URL validation, content cleaning
│   └── strategies.py      # Extraction strategies per site type
```

#### 1.2 Enhance Article Model
- Add content status tracking fields
- Add content quality indicators
- Add processing state management
- Create database migration

#### 1.3 Content Extraction Pipeline
- Implement multiple extraction strategies (newspaper3k, BeautifulSoup, readability)
- Add paywall detection logic
- Implement content quality assessment
- Create retry mechanisms with exponential backoff

#### 1.4 Celery Task Integration
```python
@shared_task(name="content.fetch_article_content")
def fetch_article_content(article_id: int):
    """Async task to fetch and process article content."""

@shared_task(name="content.retry_failed_fetches")  
def retry_failed_fetches():
    """Periodic task to retry failed content fetches."""
```

### Phase 2: AI Enhancement (Week 2)

#### 2.1 Enhance Summariser App
- Implement OpenAI/Anthropic integration
- Add content-aware summarization
- Handle different content types (full vs. partial)
- Create fallback summarization for metadata-only articles

#### 2.2 Content Analysis
- Sentiment analysis
- Entity extraction
- Keyword identification
- Topic classification refinement

#### 2.3 Quality-Aware Processing
- Adjust AI processing based on content availability
- Different prompts for different content types
- Quality scoring for generated summaries

### Phase 3: User Experience (Week 3)

#### 3.1 Frontend Content Display
- Content availability indicators
- Graceful degradation in UI
- Clear labeling of content types
- Enhanced "Read Full Article" CTAs

#### 3.2 Content Status Dashboard
- Admin interface for monitoring content fetch success rates
- Content quality metrics
- Paywall detection statistics
- Processing pipeline health

## Data Flow Architecture

### Complete Processing Pipeline

```
1. Source Integration
   NewsAPI → Article Metadata → articles.Article (content_status=PENDING)

2. Content Fetching  
   content.tasks.fetch_article_content()
   → content.fetcher.ContentFetcher.fetch_article_content()
   → Update Article (content_status=CONTENT_AVAILABLE|PAYWALL_BLOCKED|etc.)

3. AI Processing
   content.tasks.process_article()
   → content.summariser.SummarizationService.generate_summary()
   → content.analyzer.ContentAnalyzer.analyze_content()
   → Update Article (processing_status=COMPLETED)

4. Fallback Processing
   content.tasks.process_fallback_content()
   → Enhanced description-based processing
   → Alternative content strategies
```

### Error Handling & Retry Logic

```python
class ContentFetchStrategy:
    """
    Implements intelligent retry and fallback strategies.
    """
    
    def execute_with_fallbacks(self, article: Article) -> ProcessingResult:
        strategies = [
            self.fetch_full_content,
            self.fetch_with_different_user_agent,
            self.try_archive_version,
            self.enhance_description_content,
            self.generate_contextual_summary
        ]
        
        for strategy in strategies:
            result = strategy(article)
            if result.success:
                return result
                
        return self.mark_as_metadata_only(article)
```

## Monitoring & Analytics

### Key Metrics to Track

1. **Content Availability Rates**
   - Percentage of articles with full content
   - Paywall detection rates by publication
   - Technical error rates by domain

2. **Processing Success Rates**
   - AI summarization success rates
   - Content quality scores distribution
   - Processing time metrics

3. **User Experience Impact**
   - Click-through rates by content type
   - User engagement with different content formats
   - Feedback on content quality

### Dashboard Requirements

- Real-time content fetching status
- Publication-specific success rates
- Content quality trends over time
- Processing pipeline bottlenecks
- Cost tracking for AI services

## Risk Mitigation

### Technical Risks
- **Rate limiting:** Implement respectful crawling with delays
- **Legal concerns:** Respect robots.txt and terms of service
- **Performance impact:** Async processing, queue management
- **Cost control:** Monitor AI API usage and costs

### Content Quality Risks
- **Misinformation:** Implement source credibility scoring
- **Bias amplification:** Monitor AI-generated content for bias
- **Content freshness:** Implement content update mechanisms
- **User expectations:** Clear communication about content limitations

## Success Criteria

### Technical Success
- ≥70% of articles have some form of enhanced content
- ≥90% of processing pipeline uptime
- <5 second average content fetch time
- Graceful handling of all error scenarios

### User Experience Success
- Clear content availability indicators
- Seamless fallback experiences
- Improved user engagement with enhanced content
- Positive user feedback on content quality

## Next Steps

1. **Create content/fetcher app** with basic web scraping
2. **Enhance Article model** with status tracking
3. **Implement content extraction pipeline** with error handling
4. **Add Celery tasks** for async processing
5. **Create admin dashboard** for monitoring
6. **Enhance summariser app** with AI integration
7. **Update frontend** with content availability indicators

This architecture provides a robust foundation for handling the complexities of web content fetching while maintaining excellent user experience even when full content is unavailable. 