# AI Content Processing - Command Reference

## Overview

This document provides comprehensive reference for all management commands related to AI content processing, including processing articles, debugging, data quality fixes, and monitoring.

## Core Processing Commands

### `process_ready_articles`

Main command for processing articles with the AI pipeline.

```bash
./docker.sh django process_ready_articles [options]
```

#### Arguments

| Argument | Type | Description | Example |
|----------|------|-------------|---------|
| `--limit` | Integer | Maximum number of articles to process | `--limit 10` |
| `--languages` | String | Comma-separated language ISO codes | `--languages en,pt,es` |
| `--regions` | String | Comma-separated region codes | `--regions us,br,gb` |
| `--verbose` | Flag | Enable detailed output | `--verbose` |
| `--dry-run` | Flag | Show what would be processed without processing | `--dry-run` |

#### Usage Examples

```bash
# Process 5 articles with detailed output
./docker.sh django process_ready_articles --limit 5 --verbose

# Process only English and Portuguese articles
./docker.sh django process_ready_articles --languages en,pt --limit 10

# Process articles from US and UK regions only
./docker.sh django process_ready_articles --regions us,gb --limit 10

# Combined filtering: English articles from US regions
./docker.sh django process_ready_articles --languages en --regions us --limit 5 --verbose

# Preview what would be processed (no actual processing)
./docker.sh django process_ready_articles --languages en --limit 10 --dry-run
```

#### Output Format

```
Processing 3 articles with AI processor...

Filters applied:
  Languages: ['en', 'pt']
  Regions: ['us', 'br']

Articles to process (showing first 5):
  abc123-def456 [en] [us] - Breaking News: Major Discovery in AI Research Leads to...
  def456-ghi789 [pt] [br] - Tecnologia Avançada: Descoberta Revolucionária em...
  ghi789-jkl012 [en] [us] - Scientific Breakthrough: New Method for Content...

Processing article abc123-def456...
✓ AI processing completed successfully (59 blocks extracted)
  Quality score: 0.84
  Processing time: 190.2 seconds
  Token usage: 42,081 tokens
  Cost: $0.376

Summary:
  Total processed: 3
  Successful: 3 (100%)
  Failed: 0 (0%)
  Average processing time: 156.7 seconds
  Total cost: $1.12
```

### `debug_ai_processing`

Debug AI processing for specific articles.

```bash
./docker.sh django debug_ai_processing --article-id <public_id> [options]
```

#### Arguments

| Argument | Type | Description | Example |
|----------|------|-------------|---------|
| `--article-id` | String | Article public ID (required) | `--article-id abc123-def456` |
| `--template` | String | Specific template to use | `--template comprehensive_v2` |
| `--show-blocks` | Flag | Display extracted content blocks | `--show-blocks` |
| `--show-html` | Flag | Display preprocessed HTML | `--show-html` |

#### Usage Examples

```bash
# Debug specific article with default settings
./docker.sh django debug_ai_processing --article-id abc123-def456

# Debug with specific template and show extracted blocks
./docker.sh django debug_ai_processing --article-id abc123-def456 --template comprehensive_v2 --show-blocks

# Debug and show preprocessed HTML
./docker.sh django debug_ai_processing --article-id abc123-def456 --show-html
```

#### Output Format

```
=== AI Processing Debug for Article abc123-def456 ===

Article Details:
  Title: Breaking News: Major Discovery in AI Research
  URL: https://example.com/article
  Publication: TechCrunch
  Language: en
  Regions: ['us']
  Current Status: pending

Processing Configuration:
  Template: comprehensive_v2
  Model: gpt-4o
  Max Tokens: 8000
  Temperature: 0.1

HTML Preprocessing:
  Original HTML size: 45,832 characters
  Preprocessed size: 12,456 characters
  Reduction: 72.8%

AI Processing Result:
✓ Processing successful
  Blocks extracted: 59
  Valid blocks: 59 (100%)
  Invalid blocks filtered: 0
  Processing time: 190.2 seconds
  Token usage: 42,081 tokens
  Cost: $0.376

Content Blocks (first 5):
  1. heading (level=1): "Breaking News: Major Discovery in AI Research"
  2. paragraph: "Scientists at leading tech companies have announced..."
  3. image: "AI research laboratory" (src: /images/lab.jpg)
  4. paragraph: "The breakthrough represents a significant advancement..."
  5. quote: "This changes everything we know about artificial intelligence"

Quality Assessment:
  Overall Score: 0.84
  Completeness: 0.88
  Purity: 0.82
  Structure: 0.85
  Readability: 0.81
```

## Data Quality Commands

### `fix_publication_regions`

Fix publications missing region assignments.

```bash
./docker.sh django fix_publication_regions [options]
```

#### Arguments

| Argument | Type | Description | Example |
|----------|------|-------------|---------|
| `--dry-run` | Flag | Preview changes without applying | `--dry-run` |
| `--verbose` | Flag | Show detailed assignment logic | `--verbose` |

#### Usage Examples

```bash
# Preview what would be fixed
./docker.sh django fix_publication_regions --dry-run

# Apply fixes with detailed output
./docker.sh django fix_publication_regions --verbose

# Just apply fixes
./docker.sh django fix_publication_regions
```

#### Output Format

```
DRY RUN MODE - No changes will be made
Found 625 publications without regions

Would assign Quartz India → ['India']
Would assign ESPN → ['United States']
Would assign BBC News → ['United Kingdom']
Would assign TechCrunch → ['United States']
...

Would update 625 publications
```

## Monitoring Commands

### Django Shell Queries

Monitor processing status and performance using Django shell:

```bash
./docker.sh django shell
```

#### Processing Status Overview

```python
from apps.articles.models import Article

# Processing status distribution
statuses = ['pending', 'processing', 'processed', 'ai_failed', 'failed']
for status in statuses:
    count = Article.objects.filter(process_status=status).count()
    print(f'{status}: {count}')

# Recent processing activity
from django.utils import timezone
from datetime import timedelta

recent = timezone.now() - timedelta(hours=24)
recent_processed = Article.objects.filter(
    last_process_attempt__gte=recent,
    process_status='processed'
).count()
print(f'Articles processed in last 24h: {recent_processed}')
```

#### Quality Metrics

```python
from apps.articles.models import Article

# Quality score distribution for recently processed articles
processed_articles = Article.objects.filter(
    process_status='processed',
    content_quality_metrics__isnull=False
)[:100]

quality_scores = []
for article in processed_articles:
    if article.content_quality_metrics:
        score = article.content_quality_metrics.get('quality_score', 0)
        quality_scores.append(score)

if quality_scores:
    avg_quality = sum(quality_scores) / len(quality_scores)
    print(f'Average quality score (last 100): {avg_quality:.3f}')
    print(f'Min: {min(quality_scores):.3f}, Max: {max(quality_scores):.3f}')
```

#### Processing Performance

```python
from apps.articles.models import Article
from django.db.models import Avg, Count

# Processing attempts distribution
attempt_stats = Article.objects.filter(
    process_attempts__gt=0
).aggregate(
    avg_attempts=Avg('process_attempts'),
    total_articles=Count('id')
)

print(f"Average processing attempts: {attempt_stats['avg_attempts']:.2f}")
print(f"Total articles with attempts: {attempt_stats['total_articles']}")

# Retry analysis
retry_counts = Article.objects.filter(
    process_attempts__gt=1
).values('process_attempts').annotate(
    count=Count('id')
).order_by('process_attempts')

print("\nRetry distribution:")
for stat in retry_counts:
    print(f"  {stat['process_attempts']} attempts: {stat['count']} articles")
```

### World Feed Validation

Check world feed content availability:

```python
from apps.articles.models import Article
from apps.feeds.models import UserRegion, Publication

# Check world feed content for different regions
regions = ['us', 'gb', 'br', 'de', 'fr']

for region_code in regions:
    headlines = Article.objects.filter(
        is_top_headline=True,
        publication__regions__code=region_code
    ).count()
    print(f'{region_code.upper()}: {headlines} headlines')

# Check publications without regions
no_regions = Publication.objects.filter(regions__isnull=True).count()
print(f'\nPublications without regions: {no_regions}')
```

## Advanced Commands

### Batch Processing with Filtering

Process specific article sets with advanced filtering:

```bash
# Process articles from specific date range
./docker.sh django shell -c "
from apps.articles.models import Article
from datetime import datetime, timedelta
from django.utils import timezone

# Articles from last 3 days
cutoff = timezone.now() - timedelta(days=3)
recent_articles = Article.objects.filter(
    process_status='pending',
    published_at__gte=cutoff
)[:10]

print(f'Found {recent_articles.count()} recent articles for processing')
"

# Then process them
./docker.sh django process_ready_articles --limit 10 --verbose
```

### Template Testing

Test different extraction templates:

```bash
# Test with different templates
./docker.sh django debug_ai_processing --article-id abc123 --template comprehensive_v2
./docker.sh django debug_ai_processing --article-id abc123 --template specialized_news
```

### Performance Monitoring

Monitor token usage and costs:

```bash
# Get processing cost summary
./docker.sh django shell -c "
from apps.aiproviders.models import AIUsageLog
from datetime import datetime, timedelta
from django.utils import timezone

# Last 24 hours usage
recent = timezone.now() - timedelta(hours=24)
recent_usage = AIUsageLog.objects.filter(
    created_at__gte=recent,
    operation='content_extraction'
)

total_tokens = sum(log.token_usage for log in recent_usage)
total_cost = sum(log.cost for log in recent_usage)
article_count = recent_usage.count()

print(f'Last 24h processing:')
print(f'  Articles: {article_count}')
print(f'  Total tokens: {total_tokens:,}')
print(f'  Total cost: \${total_cost:.3f}')
if article_count > 0:
    print(f'  Avg cost per article: \${total_cost/article_count:.3f}')
"
```

## Error Handling Commands

### Check Failed Articles

Analyze processing failures:

```bash
./docker.sh django shell -c "
from apps.articles.models import Article

# Get failed articles with error messages
failed_articles = Article.objects.filter(
    process_status='ai_failed',
    process_error_message__isnull=False
)[:10]

print('Recent processing failures:')
for article in failed_articles:
    print(f'  {article.public_id}: {article.process_error_message[:100]}...')
"
```

### Retry Failed Articles

Manually retry specific failed articles:

```bash
# Reset article status for retry
./docker.sh django shell -c "
from apps.articles.models import Article

# Reset specific article
article = Article.objects.get(public_id='abc123-def456')
article.process_status = 'pending'
article.process_attempts = 0
article.process_error_message = ''
article.save()

print(f'Reset article {article.public_id} for retry')
"

# Then process normally
./docker.sh django process_ready_articles --limit 1 --verbose
```

## Best Practices

### Daily Operations

```bash
# Morning processing routine
./docker.sh django process_ready_articles --languages en,pt --regions us,br --limit 20 --verbose

# Check system health
./docker.sh django shell -c "
from apps.articles.models import Article
pending = Article.objects.filter(process_status='pending').count()
failed = Article.objects.filter(process_status='ai_failed').count()
print(f'Pending: {pending}, Failed: {failed}')
"
```

### Debugging Workflow

```bash
# 1. Identify problematic article
./docker.sh django shell -c "
from apps.articles.models import Article
failed = Article.objects.filter(process_status='ai_failed').first()
print(f'Debug article: {failed.public_id}')
"

# 2. Debug specific article
./docker.sh django debug_ai_processing --article-id <public_id> --show-blocks

# 3. Reset and retry if needed
./docker.sh django shell -c "
article = Article.objects.get(public_id='<public_id>')
article.process_status = 'pending'
article.process_attempts = 0
article.save()
"
```

This command reference provides comprehensive tools for managing the AI content processing pipeline effectively. 