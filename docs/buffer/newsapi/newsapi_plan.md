# NewsAPI Integration Implementation Plan

## 1. Overview

This document outlines the implementation strategy for integrating NewsAPI into DailyBrief. We'll use NewsAPI as our primary source for news articles in the MVP, with plans to extend to other sources later.

## 2. Architecture

### Components
- **NewsAPI Service**: Wrapper around the NewsAPI client
- **Article Processor**: Converts NewsAPI responses to our article model
- **Sync Manager**: Orchestrates the fetching and processing flow
- **Celery Tasks**: Scheduled jobs for regular updates
- **Logging & Monitoring**: Track API usage and errors

### Data Flow
1. NewsAPI client makes requests to external API
2. Raw responses are validated and transformed
3. Processed articles are saved to the database via the articles app
4. Sync metadata is recorded for tracking

## 3. Implementation Details

### 3.1 NewsAPI Service

Create a service class that wraps the NewsAPI client:

```python
# apps/newsapi/services/newsapi_service.py

class NewsAPIService:
    def __init__(self, api_key=None):
        self.api_key = api_key or settings.NEWSAPI_API_KEY
        self.client = NewsApiClient(api_key=self.api_key)
        
    def get_everything(self, **params):
        """Fetch articles from the /everything endpoint"""
        return self.client.get_everything(**params)
        
    def get_top_headlines(self, **params):
        """Fetch articles from the /top-headlines endpoint"""
        return self.client.get_top_headlines(**params)
```

### 3.2 Article Processor

Create a service to transform NewsAPI responses to our article model:

```python
# apps/newsapi/services/article_processor.py

class ArticleProcessor:
    def __init__(self):
        # Inject dependencies if needed
        pass
        
    def process_articles(self, api_response):
        """Process a batch of articles from NewsAPI response"""
        articles = []
        for article_data in api_response.get('articles', []):
            processed_article = self._process_single_article(article_data)
            if processed_article:
                articles.append(processed_article)
        return articles
        
    def _process_single_article(self, article_data):
        """Process a single article from NewsAPI"""
        # Map NewsAPI fields to our model
        # Add metadata, classify content, etc.
        # Return Article object (not saved yet)
```

### 3.3 Sync Manager

Create a service to orchestrate the sync process:

```python
# apps/newsapi/services/sync_manager.py

class NewsSyncManager:
    def __init__(self):
        self.api_service = NewsAPIService()
        self.processor = ArticleProcessor()
        
    def backfill_articles(self, days=30):
        """Fetch and save historical articles"""
        # Logic to fetch articles from the past X days
        
    def sync_recent_articles(self):
        """Fetch and save recent articles"""
        # Logic for incremental updates
        
    def sync_top_headlines(self):
        """Fetch and save current top headlines"""
        # Logic for headlines across configured sources
```

### 3.4 Celery Tasks

Configure Celery tasks for scheduling:

```python
# apps/newsapi/tasks.py

@shared_task
def sync_headlines():
    """Sync top headlines from NewsAPI"""
    manager = NewsSyncManager()
    return manager.sync_top_headlines()
    
@shared_task
def sync_recent_articles():
    """Sync recent articles from NewsAPI"""
    manager = NewsSyncManager()
    return manager.sync_recent_articles()
    
@shared_task
def backfill_articles(days=30):
    """Backfill articles from NewsAPI"""
    manager = NewsSyncManager()
    return manager.backfill_articles(days=days)
```

### 3.5 Models Extensions

Add NewsAPI-specific tracking models:

```python
# apps/newsapi/models.py

class NewsAPIRequest(models.Model):
    """Track requests made to NewsAPI"""
    request_type = models.CharField(max_length=20)  # 'everything', 'top-headlines'
    endpoint = models.CharField(max_length=255)
    params = models.JSONField()
    status = models.CharField(max_length=20)
    rate_limits = models.JSONField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)

class NewsAPISyncLog(models.Model):
    """Log information about sync operations"""
    sync_type = models.CharField(max_length=20)
    status = models.CharField(max_length=20)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True)
    articles_fetched = models.IntegerField(default=0)
    articles_processed = models.IntegerField(default=0)
    articles_saved = models.IntegerField(default=0)
    error_message = models.TextField(null=True, blank=True)
```

## 4. Initial Backfill Strategy

1. Divide the 30-60 day period into smaller chunks (e.g., 7-day periods)
2. For each chunk, fetch articles using date range parameters
3. Process and save articles in batches to avoid memory issues
4. Track progress to enable resume functionality if the process fails
5. Handle rate limiting by respecting the API's limits

```python
def backfill_strategy(days=30, chunk_size=7):
    """Strategy for backfilling articles"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # Split into chunks
    current_end = end_date
    chunk_start = end_date - timedelta(days=chunk_size)
    
    while chunk_start >= start_date:
        # Fetch chunk
        # Process chunk
        # Update tracking
        
        current_end = chunk_start
        chunk_start = chunk_start - timedelta(days=chunk_size)
```

## 5. Hourly Update Strategy

1. Track the timestamp of the most recent article fetched
2. In each hourly update, fetch articles published since that timestamp
3. Process and save new articles
4. Handle duplicates by checking against existing articles
5. Update the timestamp for the next run

## 6. Error Handling

1. **API Rate Limits**: Implement exponential backoff and request throttling
2. **Service Unavailability**: Log errors and retry at next scheduled interval
3. **Data Processing Errors**: Log errors and continue with other articles
4. **Transaction Management**: Use atomic transactions for saving batches

## 7. Monitoring

1. Log all API requests with params and responses
2. Track articles fetched, processed, and saved
3. Monitor rate limit usage to avoid hitting caps
4. Set up alerts for sync failures or API issues

## 8. Schedule Setup

Configure Celery Beat schedule:

```python
# settings.py or another appropriate location

CELERY_BEAT_SCHEDULE = {
    'sync-top-headlines': {
        'task': 'apps.newsapi.tasks.sync_headlines',
        'schedule': crontab(minute=0),  # Every hour
    },
    'sync-recent-articles': {
        'task': 'apps.newsapi.tasks.sync_recent_articles',
        'schedule': crontab(minute=30),  # Every hour at :30
    },
}
```

## 9. Testing Strategy

1. **Unit Tests**: Test individual components with mocked responses
2. **Integration Tests**: Test the full flow with a staging NewsAPI key
3. **Manual Verification**: Verify sample articles make it through the pipeline
4. **Load Testing**: Ensure the system can handle large article batches

## 10. Implementation Timeline

### Phase 1 (Day 1-2)
- Set up NewsAPI service class
- Create basic article processor
- Implement models for tracking

### Phase 2 (Day 3-4)
- Implement backfill functionality
- Create one-time Celery task for backfill
- Test with small date ranges

### Phase 3 (Day 5-6)
- Implement hourly sync process
- Configure Celery Beat schedule
- Test the full pipeline

### Phase 4 (Day 7)
- Refine error handling and monitoring
- Optimize for performance
- Documentation and code review 