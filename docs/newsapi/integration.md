# NewsAPI Integration

This document explains how DailyBrief integrates with NewsAPI to fetch, process, and store news articles. The integration focuses on efficient API usage, reliable data storage, and automatic publication matching.

## Overview

The NewsAPI integration consists of several components:

1. **Models** - Database tables to store API-related data
2. **Services** - Business logic to fetch and process data
3. **Tasks** - Scheduled operations to keep data fresh
4. **Commands** - Management utilities for maintenance

The system follows these core principles:
- Separation of concerns with distinct service responsibilities
- Efficient API usage through pagination and batching
- Reliable domain-based publication matching
- Automatic management of data relationships

## Architecture

### Data Flow

```
┌────────────┐    ┌────────────┐    ┌────────────┐    ┌────────────┐
│            │    │            │    │            │    │            │
│  NewsAPI   │───►│NewsAPIService│──►│ArticleProcessor│──►│ SyncManager │
│            │    │            │    │            │    │            │
└────────────┘    └────────────┘    └────────────┘    └────────────┘
                        │                 │                  │
                        ▼                 ▼                  ▼
                  ┌────────────┐    ┌────────────┐    ┌────────────┐
                  │            │    │            │    │            │
                  │NewsAPIRequest│   │NewsAPIArticle│   │NewsAPISyncLog│
                  │            │    │            │    │            │
                  └────────────┘    └────────────┘    └────────────┘
                                          │
                                          │
                                          ▼
                                    ┌────────────┐
                                    │            │
                                    │  Article   │
                                    │            │
                                    └────────────┘
                                          │
                                          │
                                          ▼
                                    ┌────────────┐
                                    │            │
                                    │Publication │
                                    │            │
                                    └────────────┘
```

### Domain-Based Publication Matching

A critical part of our architecture is the domain-based publication matching system:

1. Each article URL is processed to extract its normalized domain
2. Publications are matched with articles based on these domains
3. When new domains are encountered, publications are automatically created
4. Logo URLs are automatically generated using Google's favicon service

This approach ensures that articles are correctly categorized by their source publication, even when NewsAPI source IDs are inconsistent or missing.

## Models

### NewsAPIArticle

Stores NewsAPI-specific metadata for articles and manages the relationship with our core Article model.

| Field | Type | Description |
|-------|------|-------------|
| article | ForeignKey | One-to-one relation to the core Article model |
| source_id | CharField | The original source ID from NewsAPI |
| source_name | CharField | The name of the source from NewsAPI |
| domain | CharField | Normalized domain extracted from article URL |
| newsapi_id | CharField | Composite ID for deduplication |
| category | CharField | Category from NewsAPI (if available) |
| raw_data | JSONField | Complete original response for reference |
| is_top_headline | BooleanField | Whether this came from top-headlines endpoint |
| sync_log | ForeignKey | Reference to the sync operation that created this |
| fetched_at | DateTimeField | When this was fetched from API |
| updated_at | DateTimeField | When this was last updated |

### NewsAPISyncLog

Tracks sync operations for monitoring and debugging.

| Field | Type | Description |
|-------|------|-------------|
| sync_type | CharField | Type of sync (headlines, everything, etc.) |
| status | CharField | Status (started, completed, failed) |
| parameters | JSONField | Parameters used for this sync |
| articles_found | IntegerField | Total articles found |
| articles_created | IntegerField | New articles created |
| articles_updated | IntegerField | Existing articles updated |
| error_message | TextField | Error details if failed |
| started_at | DateTimeField | When sync started |
| completed_at | DateTimeField | When sync finished |
| duration_seconds | FloatField | How long the sync took |

### NewsAPIRequest

Tracks individual API requests for rate limit monitoring.

| Field | Type | Description |
|-------|------|-------------|
| request_type | CharField | Type of request (top_headlines, everything, sources) |
| endpoint | CharField | API endpoint called |
| params | JSONField | Request parameters |
| status_code | IntegerField | HTTP status code |
| success | BooleanField | Whether request succeeded |
| error_message | TextField | Error details if failed |
| rate_limit_remaining | IntegerField | Remaining API quota (from headers) |
| rate_limit_reset | DateTimeField | When rate limit resets |
| total_results | IntegerField | Total results available |
| results_fetched | IntegerField | Results fetched in this request |
| created_at | DateTimeField | When request was made |

## Services

### NewsAPIService (`newsapi_service.py`)

Handles direct communication with the NewsAPI endpoints and tracks usage.

Key methods:
- `get_everything()` - Access NewsAPI's /everything endpoint 
- `get_top_headlines()` - Access NewsAPI's /top-headlines endpoint
- `get_sources()` - Access NewsAPI's /sources endpoint
- `fetch_articles_by_date_range()` - Fetch articles within specific dates
- `fetch_recent_articles()` - Fetch articles published in last X hours

### ArticleProcessor (`article_processor.py`)

Transforms NewsAPI articles into DailyBrief Article models, handling publication and topic matching.

Key methods:
- `process_articles()` - Process batch of articles from API response
- `_get_or_create_article()` - Find existing or create new article
- `_get_or_create_publication()` - Find or create publication for source
- `_calculate_content_metrics()` - Extract metrics (word count, read time)

### SyncManager (`sync_manager.py`)

Orchestrates the sync process with high-level methods for different sync types.

Key methods:
- `sync_top_headlines()` - Sync headlines by category
- `sync_everything_by_publication()` - Sync articles from specific publications
- `sync_recent_by_sources_batched()` - Sync recent articles from multiple sources
- `backfill_articles()` - Historical backfill of articles
- `sync_sources()` - Update available sources from NewsAPI

## Scheduled Tasks

The following Celery tasks are scheduled for periodic execution:

| Task | Function | Schedule | Description |
|------|----------|----------|-------------|
| `newsapi.sync_headlines` | Fetch top headlines | Twice daily (5am, 2pm) | Fetches breaking news and top stories |
| `newsapi.sync_recent_by_sources` | Fetch recent by source | Daily (4am) | Fetches previous day's articles from configured sources |
| `newsapi.sync_sources` | Update source list | Weekly (Sunday 3am) | Updates the list of available news sources |

For detailed information on the task queue infrastructure, scheduled task configuration, and task monitoring, see the [Queue Infrastructure Documentation](../queues/queue_infra.md).

## Management Commands

### Core Commands

| Command | Description | Example |
|---------|-------------|---------|
| `test_task` | Run any sync task manually | `./docker.sh django test_task sync_headlines` |
| `sync_sources_direct` | Update publication sources | `./docker.sh django sync_sources_direct` |

### Domain & Publication Management

| Command | Description | Example |
|---------|-------------|---------|
| `backfill_domains` | Update domain fields for existing data | `./docker.sh django backfill_domains` |
| `create_missing_publications` | Create publications for domains | `./docker.sh django create_missing_publications` |
| `link_articles_to_publications` | Connect articles to publications | `./docker.sh django link_articles_to_publications` |
| `add_publication_logos` | Add logo URLs to publications | `./docker.sh django add_publication_logos` |

## Utilities

The integration includes several utility functions:

### `feeds.utils.py`

| Function | Description |
|----------|-------------|
| `extract_domain()` | Extract and normalize domain from URL |
| `generate_logo_url()` | Generate logo URL for a publication domain |

### `newsapi.utils.py`

| Function | Description |
|----------|-------------|
| `update_publication_domain()` | Update domain for a Publication |
| `update_newsapi_article_domain()` | Update domain for a NewsAPIArticle |

## Implementation Details

### Domain Extraction

URLs are processed to extract normalized domains:
- Remove protocol (`http://`, `https://`) 
- Remove `www.` prefix
- Extract base domain (`example.com`)

Example: `https://www.nytimes.com/article/123` → `nytimes.com`

### Publication Logo Generation

Publication logos are automatically generated using Google's favicon service:

```
https://www.google.com/s2/favicons?domain={domain}&sz=128
```

This provides high-quality icons at 128px size for a professional look.

### Rate Limiting & Batching

To respect NewsAPI's rate limits:
- Source batching (max 20 sources per request)
- Pagination (100 articles per page)
- Time-based chunking for backfills 
- Request tracking and monitoring

## Troubleshooting

### Common Issues

- **API Rate Limiting**: If you see `rateLimited` errors, reduce frequency or batch size
- **Missing Publications**: Run `create_missing_publications` then `link_articles_to_publications`
- **Missing Logos**: Run `add_publication_logos` to update missing logos

### Monitoring

- Check sync logs in the admin panel or database
- Review recent API requests for rate limit status
- Check Celery logs for task execution details 