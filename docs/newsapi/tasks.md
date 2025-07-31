# NewsAPI Scheduled Tasks

This document details the scheduled Celery tasks that keep our news content fresh and relevant.

## Task Schedule Overview

| Task | Schedule | Description |
|------|----------|-------------|
| `newsapi.sync_headlines` | Twice daily (5am, 2pm) | Fetch breaking news and top headlines |
| `newsapi.sync_recent_by_sources` | Daily (4am) | Fetches previous day's articles from configured sources |
| `newsapi.sync_sources` | Weekly (Sunday 3am) | Update the list of available news sources |

**Note**: The `sync_by_publication` task exists but is not scheduled by default. It can be run manually as needed.

## Task Definitions

### `sync_headlines`

Fetches top headlines from NewsAPI, typically breaking news and major stories.

**Implementation:**
```python
@shared_task(name="newsapi.sync_headlines")
def sync_headlines(categories=None):
    """
    Sync top headlines from NewsAPI.
    
    Args:
        categories (list, optional): List of categories to sync. If None, uses default categories.
    
    Returns:
        tuple: (created_count, updated_count, success)
    """
    try:
        logger.info("Starting headlines sync task")
        sync_manager = SyncManager()
        return sync_manager.sync_top_headlines(categories=categories)
    except Exception as e:
        logger.exception(f"Error in sync_headlines task: {e}")
        return 0, 0, False
```

**Key Features:**
- Fetches by category (business, entertainment, health, science, etc.)
- Marks articles as top headlines for featured display
- Higher priority for breaking news

### `sync_recent_by_sources`

Fetches recent articles from specific sources, configured to run every few hours.

**Implementation:**
```python
@shared_task(name="newsapi.sync_recent_by_sources")
def sync_recent_by_sources(hours=24, batch_size=20):
    """
    Sync recent articles from multiple sources.
    
    Args:
        hours (int): Number of hours to look back
        batch_size (int): Maximum sources per request (NewsAPI limit is 20)
    
    Returns:
        tuple: (created_count, updated_count, success)
    """
    try:
        logger.info(f"Starting recent articles by sources sync (last {hours} hours)")
        sync_manager = SyncManager()
        return sync_manager.sync_recent_by_sources_batched(hours=hours, batch_size=batch_size)
    except Exception as e:
        logger.exception(f"Error in sync_recent_by_sources task: {e}")
        return 0, 0, False
```

**Key Features:**
- Batches sources into groups of 20 (NewsAPI limit)
- Fetches articles from the past 24 hours
- Uses domain matching to link articles to publications

### `sync_by_publication`

Fetches articles from specific major publications on a daily basis.

**Implementation:**
```python
@shared_task(name="newsapi.sync_by_publication")
def sync_by_publication(days=1):
    """
    Sync articles from specific publications.
    
    Args:
        days (int): Number of days to look back
    
    Returns:
        tuple: (created_count, updated_count, success)
    """
    try:
        logger.info(f"Starting articles by publication sync (last {days} days)")
        sync_manager = SyncManager()
        return sync_manager.sync_everything_by_publication(days=days)
    except Exception as e:
        logger.exception(f"Error in sync_by_publication task: {e}")
        return 0, 0, False
```

**Key Features:**
- Focuses on high-authority publications
- Fetches articles from the past day
- More comprehensive coverage of major sources

### `sync_sources`

Updates the list of available news sources from NewsAPI weekly.

**Implementation:**
```python
@shared_task(name="newsapi.sync_sources")
def sync_sources(update_existing=True):
    """
    Sync available news sources from NewsAPI.
    
    Args:
        update_existing (bool): Whether to update existing publications
    
    Returns:
        tuple: (created_count, updated_count, success)
    """
    try:
        logger.info("Starting sources sync task")
        # Use the management command for direct API access
        call_command('sync_sources_direct', update_existing=update_existing)
        return True
    except Exception as e:
        logger.exception(f"Error in sync_sources task: {e}")
        return False
```

**Key Features:**
- Updates the Publication table with new sources
- Maintains metadata like categories, languages, countries
- Creates relationships between publications and topics

### `backfill_articles`

One-time or occasional task to backfill historical articles (not scheduled).

**Implementation:**
```python
@shared_task(name="newsapi.backfill_articles")
def backfill_articles(days=30, chunk_size=7):
    """
    Backfill historical articles from NewsAPI.
    
    Args:
        days (int): Total days to backfill
        chunk_size (int): Size of each chunk in days
    
    Returns:
        tuple: (created_count, updated_count, success)
    """
    try:
        logger.info(f"Starting articles backfill for past {days} days")
        sync_manager = SyncManager()
        return sync_manager.backfill_articles(days=days, chunk_size=chunk_size)
    except Exception as e:
        logger.exception(f"Error in backfill_articles task: {e}")
        return 0, 0, False
```

**Key Features:**
- Chunks requests to respect API limits
- Can backfill up to 30 days (NewsAPI limit)
- Processes articles in batches

## Celery Configuration

The tasks are scheduled in `settings.py` using the `CELERY_BEAT_SCHEDULE` setting:

```python
CELERY_BEAT_SCHEDULE = {
    # Top Headlines - Twice daily at 5am and 2pm
    'sync-top-headlines-morning': {
        'task': 'newsapi.sync_headlines',
        'schedule': crontab(hour=5, minute=0),  # 5:00 AM
    },
    'sync-top-headlines-afternoon': {
        'task': 'newsapi.sync_headlines',
        'schedule': crontab(hour=14, minute=0),  # 2:00 PM
    },
    
    # Recent Articles by Sources - Once per day at 4am to get previous day's news
    'sync-recent-by-sources-daily': {
        'task': 'newsapi.sync_recent_by_sources',
        'schedule': crontab(hour=4, minute=0),  # 4:00 AM
        'kwargs': {'hours': 24, 'batch_size': 20},
    },
    
    # Sources update - Weekly on Sunday at 3:00 AM
    'sync-sources-weekly': {
        'task': 'newsapi.sync_sources',
        'schedule': crontab(hour=3, minute=0, day_of_week=0),  # Sunday at 3:00 AM
        'kwargs': {'update_existing': True},
    },
}
```

For more details on the queue infrastructure, refer to the [Queue Infrastructure Documentation](../queues/queue_infra.md).

## Optimizations

The tasks are optimized for the NewsAPI free tier, which includes:
- 100 requests per day
- 50 per 12-hour period
- Maximum of 100 results per request

Key optimizations:
1. **Batch Processing**: Sources processed in batches of 20
2. **Pagination**: Results processed 100 at a time
3. **Scheduled Frequency**: Tasks spaced out to avoid rate limits
4. **Error Handling**: Robust error recovery and logging

## Task Monitoring

You can monitor task execution through:

1. **Django Admin**: Check the `NewsAPISyncLog` model
2. **Celery Logs**: Review worker logs with `docker logs dailybrief-celery_worker-1`
3. **Database**: Query the `newsapi_newsapisynclog` table directly

## Manual Execution

To run any task manually for testing:

```bash
# Using the test_task management command
./docker.sh django test_task sync_headlines

# Or directly via Celery
./docker.sh django shell -c "from apps.newsapi.tasks import sync_headlines; sync_headlines.delay()"
``` 