# Content Fetcher Management Commands

> **Complete reference for Django management commands in the content fetching service**

## Overview

The Content Fetcher service provides comprehensive management commands for operational tasks, testing, debugging, and maintenance. These commands are essential for managing the content extraction pipeline.

## Core Commands

### fetch_content

Main command for processing articles through the content fetching pipeline.

```bash
./docker.sh django fetch_content [options]
```

#### Options

```bash
--limit INTEGER          Maximum number of articles to process (default: 50)
--verbose               Enable verbose output with detailed logging
--strategies TEXT       Comma-separated list of strategies to use
--dry-run              Preview operations without making changes
--filter-status TEXT    Only process articles with specific status
--publication TEXT      Only process articles from specific publication
```

#### Examples

```bash
# Process 10 pending articles with verbose output
./docker.sh django fetch_content --limit 10 --verbose

# Process using only browser simulation and advanced strategies
./docker.sh django fetch_content --strategies browser,advanced --limit 5

# Preview what would be processed without making changes
./docker.sh django fetch_content --dry-run --limit 20

# Process only failed articles for retry
./docker.sh django fetch_content --filter-status failed --limit 10
```

#### Output

```
Content Fetching Results:
========================
Articles processed: 10
Successful: 8 (80.0%)
Failed: 2 (20.0%)
Total duration: 23.4 seconds
Average per article: 2.34 seconds

Strategy Performance:
- BrowserSimulation: 5 successful, 1 failed
- AdvancedBypass: 3 successful, 1 failed

Failed Articles:
- Article 31180: Connection timeout after 15s
- Article 31182: All strategies failed - permanent failure
```

### test_fetcher

Comprehensive testing command for validating fetcher performance and strategy effectiveness.

```bash
./docker.sh django test_fetcher [options]
```

#### Options

```bash
--urls TEXT             Comma-separated list of URLs to test
--test-suite TEXT       Predefined test suite (politico,axios,nytimes,wsj,all)
--strategy TEXT         Test specific strategy only
--verbose              Enable detailed output for each test
--save-results         Save test results to database
--timeout INTEGER      Override default timeout (seconds)
```

#### Examples

```bash
# Test specific URL with verbose output
./docker.sh django test_fetcher --urls "https://arstechnica.com/tech-policy/2025/01/example/" --verbose

# Test problematic news sites
./docker.sh django test_fetcher --test-suite politico,axios,nytimes,wsj

# Test all strategies on comprehensive test suite
./docker.sh django test_fetcher --test-suite all --verbose

# Test only browser simulation strategy
./docker.sh django test_fetcher --strategy browser --test-suite all
```

#### Output

```
Fetcher Strategy Testing Results:
================================

Test Suite: Major News Sites (5 URLs)
======================================

✅ https://arstechnica.com/tech-policy/2025/01/tiktok-ban-takes-effect-sunday/
   Strategy: BrowserSimulation_try_chrome_simulation
   Duration: 1.847s
   Content: 8,234 chars
   Title: "TikTok ban takes effect Sunday as Supreme Court upholds law"
   Author: "Jon Brodkin"

✅ https://www.politico.com/news/2025/01/17/trump-tiktok-ban-00198765
   Strategy: AdvancedBypass_archive_org  
   Duration: 3.251s
   Content: 6,891 chars
   Title: "Trump says he'll likely give TikTok a 90-day extension"

✅ https://axios.com/2025/01/17/tiktok-ban-supreme-court-upholds
   Strategy: AdvancedBypass_archive_org
   Duration: 2.934s
   Content: 4,567 chars
   Title: "Supreme Court upholds TikTok ban in split decision"

✅ https://www.nytimes.com/2025/01/17/technology/tiktok-ban-supreme-court.html
   Strategy: AdvancedBypass_outline_com
   Duration: 2.673s
   Content: 12,456 chars
   Title: "Supreme Court Upholds Law That Could Ban TikTok"

✅ https://www.wsj.com/tech/tiktok-ban-supreme-court-decision-01234567
   Strategy: AdvancedBypass_outline_com
   Duration: 2.891s
   Content: 9,123 chars
   Title: "Supreme Court Backs TikTok Ban in Blow to App"

Overall Results:
- Success Rate: 100% (5/5)
- Average Duration: 2.719s
- Total Content: 41,271 characters
- Strategy Distribution:
  * BrowserSimulation: 1 (20%)
  * AdvancedBypass: 4 (80%)
```

### check_status

Monitor the status and health of the content fetching pipeline.

```bash
./docker.sh django check_status [options]
```

#### Options

```bash
--detailed             Show detailed breakdown by publication and status
--recent HOURS         Show only articles from last N hours (default: 24)
--export FORMAT        Export results (json, csv)
```

#### Examples

```bash
# Basic status check
./docker.sh django check_status

# Detailed breakdown with recent articles only
./docker.sh django check_status --detailed --recent 6

# Export status to JSON
./docker.sh django check_status --export json
```

#### Output

```
Content Fetcher Pipeline Status:
===============================

Article Status Summary:
- Total articles: 31,178
- Pending fetch: 1,234 (4.0%)
- Successfully fetched: 29,567 (94.8%)
- Failed fetch: 377 (1.2%)

Recent Activity (24 hours):
- Articles added: 456
- Fetch attempts: 523
- Successful fetches: 478 (91.4%)
- Failed fetches: 45 (8.6%)

Performance Metrics:
- Average fetch duration: 2.3 seconds
- Success rate trend: ↗ +2.1% (24h)
- Most successful strategy: BrowserSimulation (65%)

Top Failure Reasons:
1. Connection timeout (32%)
2. Rate limiting (23%)
3. Paywall blocking (18%)
4. Invalid content structure (15%)
5. Other errors (12%)
```

### fix_malformed_urls

Identify and fix articles with malformed URLs containing Unicode escape sequences.

```bash
./docker.sh django fix_malformed_urls [options]
```

#### Options

```bash
--dry-run              Preview changes without applying them
--limit INTEGER        Maximum number of URLs to process
--verbose              Show detailed information about each fix
--pattern TEXT         Specific Unicode pattern to fix (default: all)
```

#### Examples

```bash
# Preview malformed URLs without fixing
./docker.sh django fix_malformed_urls --dry-run

# Fix malformed URLs with verbose output
./docker.sh django fix_malformed_urls --verbose --limit 100

# Fix only specific Unicode escape pattern
./docker.sh django fix_malformed_urls --pattern "\\u003d" --verbose
```

#### Output

```
Malformed URL Detection and Repair:
===================================

Scanning 31,178 articles for malformed URLs...

Found 23 articles with malformed URLs:

✅ Article 31178 (ABC News):
   Before: https://abcnews.go.com/US/story?id\\u003d122709741
   After:  https://abcnews.go.com/US/story?id=122709741
   Pattern: \\u003d → =

✅ Article 31201 (Reuters):
   Before: https://reuters.com/world/article\\u002f2025\\u002f01\\u002f17
   After:  https://reuters.com/world/article/2025/01/17
   Pattern: \\u002f → /

✅ Article 31205 (CNN):
   Before: https://cnn.com/news\\u003fref\\u003dhomepage\\u0026id\\u003d456
   After:  https://cnn.com/news?ref=homepage&id=456
   Pattern: Multiple Unicode escapes fixed

Summary:
- Articles scanned: 31,178
- Malformed URLs found: 23 (0.07%)
- URLs fixed: 23
- Most common pattern: \\u003d (equals sign) - 12 occurrences
- Articles marked for re-fetch: 23
```

### reset_article_status

Reset article fetch status for reprocessing, useful for testing and recovery.

```bash
./docker.sh django reset_article_status [options]
```

#### Options

```bash
--article-ids TEXT     Comma-separated list of article IDs
--status TEXT          Target status to reset (pending, failed, completed)
--publication TEXT     Reset all articles from specific publication
--limit INTEGER        Maximum number of articles to reset
--dry-run             Preview changes without applying them
```

#### Examples

```bash
# Reset specific articles to pending status
./docker.sh django reset_article_status --article-ids "31176,31174,31150" --status pending

# Reset all failed articles to pending for retry
./docker.sh django reset_article_status --status pending --limit 100

# Preview reset operation
./docker.sh django reset_article_status --publication "politico" --dry-run
```

#### Output

```
Article Status Reset Operation:
==============================

Target Articles: 3 (31176, 31174, 31150)
Target Status: pending

Article Status Changes:
✅ Article 31176: completed → pending
   - Cleared raw_html content (191,974 chars)
   - Reset fetch metadata
   - Reset fetch attempts to 0

✅ Article 31174: failed → pending  
   - Cleared error message
   - Reset fetch attempts to 0
   - Ready for retry

✅ Article 31150: completed → pending
   - Cleared raw_html content (156,432 chars)
   - Reset fetch metadata
   - Reset fetch attempts to 0

Summary:
- Articles processed: 3
- Successfully reset: 3
- Status changes: 3 → pending
- Total content cleared: 348,406 characters
```

## Testing Commands

### test_html_content

Validate HTML content quality and structure for fetched articles.

```bash
./docker.sh django test_html_content [options]
```

#### Options

```bash
--article-ids TEXT     Test specific articles
--sample-size INTEGER  Random sample size to test (default: 10)
--min-content-length   Minimum content length threshold
--check-structure     Validate HTML structure
```

#### Examples

```bash
# Test HTML content quality for specific articles
./docker.sh django test_html_content --article-ids "31176,31174,31150"

# Test random sample of 20 articles
./docker.sh django test_html_content --sample-size 20 --check-structure
```

### check_articles

Quick health check for article data integrity.

```bash
./docker.sh django check_articles [options]
```

#### Options

```bash
--verbose              Detailed output
--fix-issues          Automatically fix detected issues
```

## Debugging Commands

### check_reset_articles

Utility for checking and managing article reset operations.

```bash
./docker.sh django check_reset_articles [options]
```

#### Options

```bash
--check-only          Only check status, don't reset
--article-ids TEXT    Specific articles to check
```

## Batch Processing Commands

### Celery Task Management

```bash
# Start fetcher worker
celery -A dailybrief worker -Q fetcher --loglevel=info

# Monitor fetcher queue
celery -A dailybrief inspect active_queues

# Purge fetcher queue
celery -A dailybrief purge -Q fetcher
```

### Batch Operations

```bash
# Process large batch of pending articles
./docker.sh django shell -c "
from apps.content.fetcher.tasks import fetch_batch_articles
from apps.articles.models import Article
pending_ids = list(Article.objects.filter(fetch_status='pending')[:100].values_list('id', flat=True))
result = fetch_batch_articles.delay(pending_ids)
print(result.get())
"
```

## Performance Monitoring Commands

### Custom Performance Analysis

```bash
# Analyze fetcher performance by strategy
./docker.sh django shell -c "
from apps.articles.models import Article
from django.db.models import Count, Avg
strategy_stats = Article.objects.exclude(
    fetch_strategy_used=''
).values('fetch_strategy_used').annotate(
    count=Count('id'),
    avg_duration=Avg('fetch_duration_ms')
).order_by('-count')
for stat in strategy_stats:
    print(f'{stat[\"fetch_strategy_used\"]}: {stat[\"count\"]} articles, avg {stat[\"avg_duration\"]:.1f}ms')
"
```

### Database Queries

```bash
# Find articles with specific fetch issues
./docker.sh django shell -c "
from apps.articles.models import Article
failed_articles = Article.objects.filter(
    fetch_status='failed',
    fetch_attempts__gte=3,
    paywall_detected=False
)
print(f'Permanently failed articles: {failed_articles.count()}')
"
```

## Configuration Commands

### Environment Setup

```bash
# Validate fetcher configuration
./docker.sh django shell -c "
from django.conf import settings
from apps.content.fetcher.fetcher import ContentFetcher
fetcher = ContentFetcher()
print(f'Strategies available: {len(fetcher.strategies)}')
print(f'Timeout: {fetcher.timeout_seconds}s')
print(f'Max retries: {fetcher.max_retries}')
"
```

## Automation Scripts

### Scheduled Processing

```bash
# Add to crontab for automated processing
0 */2 * * * /path/to/docker.sh django fetch_content --limit 100 >> /var/log/fetcher.log 2>&1
```

### Health Check Script

```bash
#!/bin/bash
# health_check.sh
echo "Checking fetcher health..."
./docker.sh django check_status --recent 1
if [ $? -eq 0 ]; then
    echo "✅ Fetcher is healthy"
else
    echo "❌ Fetcher has issues"
    exit 1
fi
```

## Best Practices

### Command Usage Guidelines

1. **Always use --dry-run first** for destructive operations
2. **Monitor verbose output** during testing and debugging
3. **Use --limit** to prevent overwhelming the system
4. **Check status regularly** to monitor pipeline health
5. **Reset articles carefully** - only when necessary for testing

### Performance Optimization

```bash
# Efficient batch processing
./docker.sh django fetch_content --limit 50 --strategies browser,advanced

# Targeted retry operations
./docker.sh django fetch_content --filter-status failed --limit 20

# Regular health monitoring
./docker.sh django check_status --recent 6
```

### Error Recovery

```bash
# Standard recovery workflow
1. ./docker.sh django check_status --detailed
2. ./docker.sh django fix_malformed_urls --dry-run
3. ./docker.sh django fix_malformed_urls --verbose
4. ./docker.sh django fetch_content --filter-status failed --limit 10
5. ./docker.sh django check_status
``` 