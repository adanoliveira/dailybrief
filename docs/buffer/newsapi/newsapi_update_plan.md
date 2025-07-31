# NewsAPI Update Plan

This document outlines the implementation plan for updating our NewsAPI integration services to enhance article collection and synchronization based on specific requirements.

## 1. Scheduled Updates Overview

| Type | Endpoint | Frequency | Purpose | Parameters |
|------|----------|-----------|---------|------------|
| Top Headlines | `/v2/top-headlines` | 2x daily (5am, 2pm) | Get breaking news | `category` |
| Recent Articles | `/v2/everything` | Every 3h (6am-9pm) | Build comprehensive archive | `sources`, `from` |
| Sources | `/v2/top-headlines/sources` | Weekly (Sunday 3am) | Update publication database | `country`, `language` |
| Backfill | `/v2/everything` | On-demand | Historical data | `sources`, `from`, `to` |

## 2. Detailed Implementation Requirements

### 2.1 Top Headlines

**Goal:** Collect breaking news and trending stories

**Implementation details:**
- Schedule: Twice daily at 5am and 2pm
- Endpoint: `/v2/top-headlines`
- Per update: Make 7 separate API calls, one for each category:
  - business, entertainment, general, health, science, sports, technology
- Parameters:
  - `category`: One of the 7 categories (separate calls)
- Processing:
  - Mark all articles as `is_top_headline=True`
  - Map NewsAPI category directly to our Topic model (exact match)
  - No time filter needed (API doesn't support it for this endpoint)

**Code updates:**
- Modify `sync_manager.py` to update `sync_top_headlines()` method
- Update Celery schedule to run at 5am and 2pm

### 2.2 Recent Articles

**Goal:** Build comprehensive article archive from key sources

**Implementation details:**
- Schedule: Every 3 hours during the day, starting at 6am
- Endpoint: `/v2/everything`
- Per update: Multiple API calls covering all registered publications
  - Group publications by 20 sources per request (API limit)
  - Prioritize by publication authority score
- Parameters:
  - `sources`: Comma-separated list of source IDs (max 20)
  - `from`: 3 hours ago in ISO format
  - `language`: Default to 'en'
- Processing:
  - Initially leave topic/category blank
  - Topics will be filled in later (potential ML classification)

**Code updates:**
- Create new method `sync_recent_by_sources_batched()` in `sync_manager.py`
- Add pagination support
- Update Celery schedule for 3-hour intervals

### 2.3 Sources Update

**Goal:** Maintain up-to-date publication database

**Implementation details:**
- Schedule: Weekly on Sunday at 3am
- Endpoint: `/v2/top-headlines/sources`
- Per update: Multiple API calls, one per country in our list
- Parameters:
  - `country`: Country code (separate call for each)
  - `language`: Optional filter
- Processing:
  - Update existing Publications
  - Create new Publications
  - Update related models (Topic, Language, Region)

**Code updates:**
- Create new `sync_sources()` method in `sync_manager.py`
- Create new management command `sync_sources.py`
- Add weekly Celery schedule

### 2.4 Backfill Strategy

**Goal:** Historical data collection

**Implementation details:**
- Approach: Similar to Recent Articles but with extended date ranges
- Schedule: On-demand (manual or scheduled)
- Date strategy: Process in 2-day chunks to respect API limits
  - Start with 30-28 days ago
  - Continue with 28-26 days ago
  - etc. until current date
- Parameters:
  - Same as Recent Articles but with specific date ranges
  - `from` and `to` parameters defining 2-day windows

**Code updates:**
- Enhance existing `backfill_articles.py` command
- Add chunking and date range logic

## 3. Technical Considerations

### 3.1 Pagination Handling

- Add support for NewsAPI pagination in all sync operations
- Process `totalResults` field from response
- Make multiple API calls with `page` parameter when needed
- Aggregate results before processing

### 3.2 Rate Limiting

- Track API usage with existing `NewsAPIRequest` model
- Implement exponential backoff for rate limited requests
- Add logging and alerting for rate limit issues
- Consider implementing request queue if needed

### 3.3 Publication Management

- Auto-register new publications found in articles
- Update mapping between NewsAPI sources and our Publication model
- Maintain publication metadata (logo, website, description)

## 4. Implementation Timeline

| Week | Focus Area | Tasks |
|------|------------|-------|
| 1 | Top Headlines | Update `sync_top_headlines()`, update scheduling |
| 1 | Recent Articles | Create `sync_recent_by_sources_batched()` |
| 2 | Sources | Implement `sync_sources()` and management command |
| 2 | Backfill | Enhance backfill with chunking strategy |
| 3 | Technical Tasks | Pagination, rate limiting, publication updates |
| 3 | Testing & Monitoring | Test coverage, monitoring, alerting |

## 5. API Usage Projection

Based on the planned schedule:
- Top Headlines: 14 requests/day (7 categories × 2 times)
- Recent Articles: ~30-60 requests/day (depends on number of publication batches × 5-6 times)
- Sources: ~10-15 requests/week (depends on number of countries)
- **Total: ~45-90 requests/day**

NewsAPI Developer plan allows 1,000 requests/day, which should be sufficient. 