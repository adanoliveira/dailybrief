# DailyBrief Task Queue Infrastructure

This document describes the asynchronous task processing infrastructure used in DailyBrief to handle background jobs, scheduled tasks, and periodic operations.

## Overview

DailyBrief uses Celery as the distributed task queue system with Redis as the message broker. This architecture enables the application to:

- Execute resource-intensive operations asynchronously
- Schedule periodic tasks for data synchronization
- Ensure reliable task execution even if the application is restarted
- Scale task processing independently from the web server

## Infrastructure Components

### Message Broker: Redis

- **Role**: Stores task messages and serves as a communication medium between Django application and Celery workers
- **Configuration**: Running in Docker container with persistence enabled
- **Connection**: `redis://redis:6379/0` 
- **Health check**: Automatic health check with 5-second intervals

### Task Queue: Celery

- **Version**: Celery 5.5.2
- **Task Result Backend**: Redis (same instance as the broker)
- **Serialization**: JSON (for both task and result serialization)
- **Time Zone**: Matches Django's TIME_ZONE setting (UTC)

### Workers and Schedulers

The system runs three key components:

1. **Celery Worker**
   - Container: `dailybrief-celery_worker-1`
   - Role: Executes tasks pulled from the queue
   - Concurrency: Auto-detected based on available CPU cores
   - Log level: INFO

2. **Celery Beat**
   - Container: `dailybrief-celery_beat-1`
   - Role: Scheduler that triggers periodic tasks
   - Schedule definition: Configured in Django settings via `CELERY_BEAT_SCHEDULE`

3. **Celery Flower**
   - Container: `dailybrief-flower-1`
   - Role: Web-based monitoring tool
   - URL: http://localhost:5555
   - Features: Real-time monitoring, task inspection, statistics, and management

## Configured Tasks

### NewsAPI Integration Tasks

| Task Name | Purpose | Schedule | Implementation |
|-----------|---------|----------|----------------|
| `newsapi.sync_headlines` | Fetches top headlines from multiple categories | Twice daily (5am, 2pm) | `apps/newsapi/tasks.py` |
| `newsapi.sync_recent_by_sources` | Fetches recent articles from known sources | Every 3 hours (6am-9pm) | `apps/newsapi/tasks.py` |
| `newsapi.sync_by_publication` | Synchronizes articles from specific publications | Daily at 2am | `apps/newsapi/tasks.py` |
| `newsapi.sync_sources` | Updates the list of available news sources | Weekly (Sunday 3am) | `apps/newsapi/tasks.py` |
| `newsapi.backfill_articles` | Backfills historical articles (manual) | On-demand | `apps/newsapi/tasks.py` |

### Schedule Details

```python
CELERY_BEAT_SCHEDULE = {
    # Top Headlines - Twice daily at 5am and 2pm
    'sync-top-headlines-morning': {
        'task': 'newsapi.sync_headlines',
        'schedule': crontab(hour=5, minute=0),
    },
    'sync-top-headlines-afternoon': {
        'task': 'newsapi.sync_headlines',
        'schedule': crontab(hour=14, minute=0),
    },
    
    # Recent Articles by Sources - Every 3 hours during the day
    'sync-recent-by-sources-6am': {
        'task': 'newsapi.sync_recent_by_sources',
        'schedule': crontab(hour=6, minute=0),
        'kwargs': {'hours': 3, 'batch_size': 20},
    },
    'sync-recent-by-sources-9am': {
        'task': 'newsapi.sync_recent_by_sources',
        'schedule': crontab(hour=9, minute=0),
        'kwargs': {'hours': 3, 'batch_size': 20},
    },
    # ... additional schedules ...
    
    # Sources update - Weekly
    'sync-sources-weekly': {
        'task': 'newsapi.sync_sources',
        'schedule': crontab(hour=3, minute=0, day_of_week=0),
        'kwargs': {'update_existing': True},
    },
}
```

## Task Results and Logging

All NewsAPI task executions are tracked in the `newsapi_synclog` table, which records:
- Operation type
- Status (started, completed, failed)
- Error messages (if any)
- Execution time
- Articles processed (created/updated)

This provides a historical record of task executions that can be queried through the admin interface or via SQL.

## Monitoring and Management

### Using Celery Flower

Flower provides a web interface for monitoring and managing Celery tasks:

- **Dashboard**: http://localhost:5555
- **Features**:
  - Real-time monitoring of active tasks
  - Task history and result inspection
  - Worker status and resource usage
  - Task rate monitoring
  - Failed task analysis

### Command-Line Monitoring

You can also monitor tasks using the following commands:

```bash
# View Celery worker logs
docker logs -f dailybrief-celery_worker-1

# View Beat scheduler logs
docker logs -f dailybrief-celery_beat-1

# Check currently running tasks
docker exec dailybrief-celery_worker-1 celery -A dailybrief inspect active

# View scheduled tasks
docker exec dailybrief-celery_worker-1 celery -A dailybrief inspect scheduled

# Check worker statistics
docker exec dailybrief-celery_worker-1 celery -A dailybrief inspect stats
```

### Database-Level Monitoring

Query the database to check sync logs:

```sql
-- Connect to PostgreSQL
docker exec -it dailybrief-db-1 psql -U postgres

-- In the PostgreSQL shell
\c dailybrief

-- View recent sync logs
SELECT id, sync_type, status, started_at, completed_at, 
       articles_created, articles_updated, error_message
FROM newsapi_synclog 
ORDER BY started_at DESC 
LIMIT 10;

-- View failed tasks
SELECT id, sync_type, status, error_message, started_at
FROM newsapi_synclog 
WHERE status = 'failed'
ORDER BY started_at DESC;
```

## Manual Task Execution

You can manually trigger tasks for testing or debugging using a custom management command:

```bash
# Run the sync_headlines task
./docker.sh django test_task sync_headlines

# Run the sync_recent_by_sources task
./docker.sh django test_task sync_recent_by_sources

# Run the sync_by_publication task
./docker.sh django test_task sync_by_publication

# Run the sync_sources task
./docker.sh django test_task sync_sources
```

## Task Execution Model

1. **Task Definition**: Tasks are defined in app-specific `tasks.py` files, using the `@shared_task` decorator
2. **Task Registration**: The Celery app discovers tasks from all installed Django apps
3. **Task Triggering**: Tasks are triggered either by:
   - Schedule (defined in `CELERY_BEAT_SCHEDULE`)
   - Manual execution (via code or management command)
   - API endpoint (selected tasks)
4. **Task Execution**: Worker pulls tasks from Redis queue and executes them
5. **Result Handling**: Results are stored in Redis and application-specific database records

## Adding New Tasks

To add new tasks to the system:

1. Create a function in an app's `tasks.py` file
2. Apply the `@shared_task` decorator
3. Implement proper logging and error handling
4. If periodic, add to `CELERY_BEAT_SCHEDULE` in settings
5. For manual execution, update the `test_task.py` management command

Example:
```python
@shared_task(name="app.task_name")
def task_function():
    logger.info("Starting task")
    try:
        # Task implementation
        return {'success': True, 'result': result}
    except Exception as e:
        logger.error(f"Task failed: {str(e)}")
        return {'success': False, 'error': str(e)}
```

## Troubleshooting

### Common Issues

1. **Tasks not running on schedule**:
   - Check Celery Beat logs: `docker logs dailybrief-celery_beat-1`
   - Verify timezone configuration in settings
   - Restart the Celery Beat service: `docker restart dailybrief-celery_beat-1`

2. **Tasks fail to execute**:
   - Check worker logs: `docker logs dailybrief-celery_worker-1`
   - Check the database for error messages in the relevant log tables
   - Verify that required environment variables are set

3. **Worker not consuming tasks**:
   - Check Redis connection: `docker exec -it dailybrief-redis-1 redis-cli ping`
   - Verify broker URL configuration
   - Restart the worker: `docker restart dailybrief-celery_worker-1`

4. **Flower dashboard not accessible**:
   - Check if the Flower container is running: `docker ps | grep flower`
   - Check Flower logs: `docker logs dailybrief-flower-1`
   - Verify port mapping in docker-compose.yml 