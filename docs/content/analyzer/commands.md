# Analyzer Management Commands

> **Administrative commands and testing tools for the AI Content Analysis Service**

This document provides comprehensive documentation for all management commands available in the analyzer service, including usage examples, options, and troubleshooting guidance.

## 📖 Table of Contents

- [Core Analysis Commands](#core-analysis-commands)
- [Testing & Validation Commands](#testing--validation-commands)
- [Configuration Commands](#configuration-commands)
- [Debugging Commands](#debugging-commands)
- [Usage Examples](#usage-examples)

## Core Analysis Commands

### `run_analyzer`

**Purpose:** Analyze individual articles with detailed output and error handling

**Location:** `backend/apps/content/analyzer/management/commands/run_analyzer.py`

**Usage:**
```bash
# Analyze single article
./docker.sh django run_analyzer --article-id 15158

# Force re-analysis (cleans old events)
./docker.sh django run_analyzer --article-id 15158 --force

# Analyze with verbose output
./docker.sh django run_analyzer --article-id 15158 --verbose
```

**Options:**
- `--article-id`: Required. ID of the article to analyze
- `--force`: Optional. Force re-analysis, cleaning existing events
- `--verbose`: Optional. Enable detailed logging output

**Output Example:**
```
INFO: Using enhanced content from summary components for article 15158 (2089 chars)
INFO: Stage 1: Language detection for article 15158
INFO: Stage 2: Linguistic analysis for article 15158
INFO: Full content assembled for article 15158: 8456 chars
INFO: Calculated readability metrics for article 15158: score=45.2, words=1789, read_time=8.0min
INFO: Truncated content assembled for article 15158: 4987 chars
INFO: Calculated sentiment score for article 15158: 0.12
INFO: Analyzed style/tone for article 15158: factual
INFO: Stage 3: Entity extraction for article 15158
INFO: Stage 5: Event extraction for article 15158
INFO: Stage 6: Region classification for article 15158
INFO: Stage 7: Topic classification for article 15158
INFO: Successfully analyzed article 15158 in 12800ms for $0.000050 (target: $0.00019)
```

**Error Handling:**
- Validates article exists and has completed summarization
- Provides detailed error messages for debugging
- Tracks cost and performance metrics

### `test_batch_analyzer`

**Purpose:** Test analysis on multiple articles with comprehensive reporting

**Location:** `backend/apps/content/analyzer/management/commands/test_batch_analyzer.py`

**Usage:**
```bash
# Test multiple articles
./docker.sh django test_batch_analyzer --article-ids 15157,15158,20103

# Force re-analysis on batch
./docker.sh django test_batch_analyzer --article-ids 15157,15158,20103 --force

# Test with detailed event output
./docker.sh django test_batch_analyzer --article-ids 15157,15158 --show-events
```

**Options:**
- `--article-ids`: Required. Comma-separated list of article IDs
- `--force`: Optional. Force re-analysis for all articles
- `--show-events`: Optional. Display detailed event information
- `--limit`: Optional. Maximum number of articles to process

**Output Example:**
```
Testing analyzer with 3 articles
Article IDs: [15157, 15158, 20103]
Found 3 articles to analyze

[1/3] Analyzing article 15157: FDA's plan to limit covid vaccines...
  → Events (2 total):
      • May 2025 FDA COVID-19 Vaccine Policy (PRIMARY)
        Type: policy_change | Relevance: 1.0 | Articles: 1
        Abstract: The FDA has introduced new guidelines limiting COVID-19 vaccine approvals...
      • COVID-19 Pandemic in the U.S.
        Type: other | Relevance: 0.9 | Articles: 1
        Abstract: The ongoing COVID-19 pandemic in the U.S., marked by over 1.2 million deaths...
  ✓ Success ($0.000080, 18363ms)

============================================================
BATCH ANALYSIS SUMMARY
============================================================
Articles processed: 3/3
Failed: 0
Total time: 55.2s
Total cost: $0.000240
Avg cost per article: $0.000080

Events created: 4
Events linked to articles: 6
Entities created: 0
Entities linked to articles: 35
Average articles per event: 0.1
```

## Testing & Validation Commands

### `test_analyzer_debug`

**Purpose:** Comprehensive debugging and validation tool for analyzer pipeline

**Location:** `backend/apps/content/analyzer/management/commands/test_analyzer_debug.py`

**Usage:**
```bash
# Debug specific article
./docker.sh django test_analyzer_debug --article-id 15158

# Debug with stage-by-stage output
./docker.sh django test_analyzer_debug --article-id 15158 --verbose

# Test specific stages only
./docker.sh django test_analyzer_debug --article-id 15158 --stages entity,event
```

**Features:**
- Stage-by-stage execution with detailed logging
- Cost tracking per stage
- Entity resolution debugging
- Event deduplication analysis
- Performance profiling

### `test_analyzer_enhancement`

**Purpose:** Test analyzer enhancements and new features

**Location:** `backend/apps/content/analyzer/management/commands/test_analyzer_enhancement.py`

**Usage:**
```bash
# Test enhanced event extraction
./docker.sh django test_analyzer_enhancement --test-events

# Test entity deduplication
./docker.sh django test_analyzer_enhancement --test-entities

# Test prompt improvements
./docker.sh django test_analyzer_enhancement --test-prompts
```

### `test_analyzer_optimization`

**Purpose:** Performance testing and optimization validation

**Location:** `backend/apps/content/analyzer/management/commands/test_analyzer_optimization.py`

**Usage:**
```bash
# Performance benchmark
./docker.sh django test_analyzer_optimization --benchmark

# Cost analysis
./docker.sh django test_analyzer_optimization --cost-analysis

# Memory usage profiling
./docker.sh django test_analyzer_optimization --memory-profile
```

### `test_classification_direct`

**Purpose:** Direct testing of AI classification models

**Location:** `backend/apps/content/analyzer/management/commands/test_classification_direct.py`

**Usage:**
```bash
# Test topic classification
./docker.sh django test_classification_direct --test-topics

# Test region detection
./docker.sh django test_classification_direct --test-regions

# Test style classification
./docker.sh django test_classification_direct --test-style

# Test all classifications
./docker.sh django test_classification_direct --test-all
```

## Pipeline Management Commands

### `cleanup_stuck_articles` (Enhanced)

**Purpose:** Clean up articles stuck in processing across all pipeline stages with flexible time controls

**Location:** `backend/apps/content/management/commands/cleanup_stuck_articles.py`

**Core Usage:**
```bash
# Check for stuck articles (default: 2h timeout)
./docker.sh django cleanup_stuck_articles --check-only

# Actually reset stuck articles
./docker.sh django cleanup_stuck_articles

# Show detailed information about stuck articles
./docker.sh django cleanup_stuck_articles --check-only --verbose
```

**Time Window Controls:**

**Convenience Presets:**
```bash
# Aggressive (30 minutes for all stages)
./docker.sh django cleanup_stuck_articles --aggressive

# Conservative (6 hours for all stages)  
./docker.sh django cleanup_stuck_articles --conservative
```

**Global Timeouts:**
```bash
# Set all stages to 1 hour
./docker.sh django cleanup_stuck_articles --timeout 1

# Set all stages to 45 minutes
./docker.sh django cleanup_stuck_articles --timeout-minutes 45
```

**Individual Stage Timeouts:**
```bash
# Hour precision
./docker.sh django cleanup_stuck_articles \
  --fetch-timeout 1 \
  --process-timeout 2 \
  --summarization-timeout 3 \
  --analysis-timeout 4

# Minute precision for specific stages
./docker.sh django cleanup_stuck_articles \
  --analysis-timeout-minutes 30 \
  --process-timeout-minutes 45
```

**Options:**
- `--check-only`: Preview what would be reset without making changes
- `--verbose`: Show detailed information about stuck articles
- `--timeout N`: Set timeout for all stages (hours)
- `--timeout-minutes N`: Set timeout for all stages (minutes)
- `--fetch-timeout N`: Hours for fetch timeout (default: 2)
- `--process-timeout N`: Hours for process timeout (default: 2)
- `--summarization-timeout N`: Hours for summarization timeout (default: 2)
- `--analysis-timeout N`: Hours for analysis timeout (default: 2)
- `--fetch-timeout-minutes N`: Minutes for fetch timeout (overrides hour setting)
- `--process-timeout-minutes N`: Minutes for process timeout (overrides hour setting)
- `--summarization-timeout-minutes N`: Minutes for summarization timeout (overrides hour setting)
- `--analysis-timeout-minutes N`: Minutes for analysis timeout (overrides hour setting)
- `--aggressive`: Use 30-minute timeouts for all stages
- `--conservative`: Use 6-hour timeouts for all stages

**Timeout Precedence (highest to lowest):**
1. Individual minute timeouts (`--*-timeout-minutes`)
2. Global timeouts (`--timeout`, `--timeout-minutes`)  
3. Presets (`--aggressive`, `--conservative`)
4. Individual hour timeouts (`--*-timeout`)
5. Defaults (2 hours for all stages)

**Output Example:**
```bash
./docker.sh django cleanup_stuck_articles --check-only --analysis-timeout-minutes 30 --verbose
```
```
🔍 Checking stuck articles across all pipeline stages...
⏱️  Timeout Configuration:
   • Fetch: 2.0h
   • Process: 2.0h
   • Summarization: 2.0h
   • Analysis: 0.5h

   ✅ No articles stuck in Fetching status
   ✅ No articles stuck in Processing status
   ✅ No articles stuck in Summarization status
   ⚠️  Found 28 articles stuck in Analysis status

   📋 Stuck Analysis Articles Details:
      • ID: 43185, Attempts: 1, Last: 2025-06-23 15:02:31
      • ID: 43205, Attempts: 1, Last: 2025-06-23 15:01:50
      • ID: 43186, Attempts: 1, Last: 2025-06-23 15:01:45
      ... and 25 more

📊 Summary: 28 stuck articles would be reset across all stages
   💡 Run without --check-only to actually reset these articles
```

**Common Use Cases:**

*Rate Limiting Recovery:*
```bash
# When hitting AI rate limits, use longer timeouts for analysis
./docker.sh django cleanup_stuck_articles --analysis-timeout-minutes 45
```

*Quick Emergency Recovery:*
```bash
# Aggressive cleanup during system outages
./docker.sh django cleanup_stuck_articles --aggressive
```

*Heavy Processing Periods:*
```bash
# Conservative timeouts during bulk processing
./docker.sh django cleanup_stuck_articles --conservative --analysis-timeout 8
```

*Targeted Stage Cleanup:*
```bash
# Focus only on analysis stage with custom timeout
./docker.sh django cleanup_stuck_articles \
  --fetch-timeout 6 \
  --process-timeout 6 \
  --summarization-timeout 6 \
  --analysis-timeout-minutes 30
```

### `reset_analyzer_status`

**Purpose:** Reset analyzer status for specific articles

**Location:** `backend/apps/content/analyzer/management/commands/reset_analyzer_status.py`

**Usage:**
```bash
# Reset specific articles to pending
./docker.sh django reset_analyzer_status --article-ids "123,456"

# Reset failed articles
./docker.sh django reset_analyzer_status --status failed

# Reset with cleanup
./docker.sh django reset_analyzer_status --article-ids "123,456" --cleanup-events
```

**Features:**
- Direct AI model testing without full pipeline
- Prompt template validation
- Model performance comparison
- Cost per operation analysis

## Configuration Commands

### `setup_analyzer_configs`

**Purpose:** Configure AI providers and operation settings for analyzer

**Location:** `backend/apps/content/analyzer/management/commands/setup_analyzer_configs.py`

**Usage:**
```bash
# Setup default configurations
./docker.sh django setup_analyzer_configs

# Setup with specific model preferences
./docker.sh django setup_analyzer_configs --event-model gpt-4.1-mini

# Setup with cost optimization
./docker.sh django setup_analyzer_configs --optimize-cost
```

**Configuration Areas:**
- AI model preferences per operation
- Cost and performance targets
- Prompt template versions
- Retry and timeout settings

**Operations Configured:**
```python
ANALYZER_OPERATIONS = {
    'event_detection': {
        'model_preference': 'gpt-4.1-mini',
        'temperature': 0.1,
        'max_tokens': 600,
        'cost_target': Decimal('0.000040')
    },
    'topic_classification': {
        'model_preference': 'gpt-4o-mini',
        'temperature': 0.0,
        'max_tokens': 100,
        'cost_target': Decimal('0.000020')
    },
    'region_detection': {
        'model_preference': 'gpt-4o-mini',
        'temperature': 0.0,
        'max_tokens': 100,
        'cost_target': Decimal('0.000010')
    },
    'style_classification': {
        'model_preference': 'gpt-4o-mini',
        'temperature': 0.0,
        'max_tokens': 20,
        'cost_target': Decimal('0.000005')
    }
}
```

## Debugging Commands

### Common Debugging Patterns

**Check Article Analysis Status:**
```bash
./docker.sh django shell -c "
from apps.articles.models import Article
from apps.content.analyzer.models import ArticleAnalysis, Event, ArticleEvent

article = Article.objects.get(id=15158)
print(f'Status: {article.analyzer_status}')
print(f'Attempts: {article.analyzer_attempts}')
print(f'Last attempt: {article.last_analyzer_attempt}')
print(f'Error: {article.analyzer_error_message}')

if hasattr(article, 'analysis'):
    analysis = article.analysis
    print(f'Language: {analysis.language_detected}')
    print(f'Style: {analysis.style_tone}')
    print(f'Topic: {analysis.primary_topic}')
    print(f'Region: {analysis.primary_region}')

events = ArticleEvent.objects.filter(article=article).select_related('event')
print(f'Events: {events.count()}')
for ae in events:
    print(f'  - {ae.event.title} (Primary: {ae.is_primary}, Relevance: {ae.relevance_score})')
"
```

**Examine Entity Resolution:**
```bash
./docker.sh django shell -c "
from apps.content.analyzer.models import Entity, EntityAlias, ArticleEntity

# Check entity catalog
entities = Entity.objects.all()[:10]
for entity in entities:
    print(f'{entity.canonical_name} ({entity.entity_type}) - {entity.article_count} articles')
    aliases = entity.aliases.all()
    if aliases:
        print(f'  Aliases: {[a.alias for a in aliases]}')

# Check article entities
article_entities = ArticleEntity.objects.filter(article_id=15158).select_related('entity')
for ae in article_entities:
    print(f'Entity: {ae.entity.display_name} ({ae.entity.entity_type})')
"
```

**Event Clustering Analysis:**
```bash
./docker.sh django shell -c "
from apps.content.analyzer.models import Event, ArticleEvent

# Check event catalog
events = Event.objects.order_by('-article_count')[:10]
for event in events:
    print(f'{event.title} - {event.article_count} articles, Type: {event.event_type}')
    print(f'  Hash: {event.event_hash[:10]}...')
    print(f'  Created: {event.first_seen_at}, Last seen: {event.last_seen_at}')

# Check for duplicate events
duplicates = Event.objects.values('title').annotate(count=Count('id')).filter(count__gt=1)
for dup in duplicates:
    print(f'Duplicate title: {dup[\"title\"]} ({dup[\"count\"]} events)')
"
```

## Usage Examples

### Complete Analysis Workflow

**1. Setup Configuration:**
```bash
# Configure AI providers
./docker.sh django setup_analyzer_configs

# Verify configuration
./docker.sh django shell -c "
from apps.aiproviders.models import AIProviderConfig
configs = AIProviderConfig.objects.filter(operation__startswith='analyzer_')
for config in configs:
    print(f'{config.operation}: {config.model_name} (${config.cost_per_request})')
"
```

**2. Test Single Article:**
```bash
# Test analysis
./docker.sh django run_analyzer --article-id 15158 --verbose

# Check results
./docker.sh django shell -c "
from apps.articles.models import Article
article = Article.objects.get(id=15158)
print(f'Status: {article.analyzer_status}')
print(f'Cost: ${article.analyzer_cost_usd}')
print(f'Duration: {article.analyzer_duration_ms}ms')
"
```

**3. Batch Testing:**
```bash
# Test multiple articles
./docker.sh django test_batch_analyzer --article-ids 15157,15158,20103 --force

# Analyze results
./docker.sh django shell -c "
from apps.content.analyzer.models import Event, ArticleEvent
from django.db.models import Count

# Event statistics
total_events = Event.objects.count()
avg_articles_per_event = Event.objects.aggregate(avg=Avg('article_count'))['avg']
print(f'Total events: {total_events}')
print(f'Average articles per event: {avg_articles_per_event:.2f}')

# Event type distribution
event_types = Event.objects.values('event_type').annotate(count=Count('id')).order_by('-count')
for et in event_types:
    print(f'{et[\"event_type\"]}: {et[\"count\"]} events')
"
```

### Performance Monitoring

**Cost Analysis:**
```bash
./docker.sh django shell -c "
from apps.articles.models import Article
from django.db.models import Avg, Sum

# Cost statistics
analyzed_articles = Article.objects.filter(analyzer_status='completed')
total_cost = analyzed_articles.aggregate(total=Sum('analyzer_cost_usd'))['total']
avg_cost = analyzed_articles.aggregate(avg=Avg('analyzer_cost_usd'))['avg']
avg_duration = analyzed_articles.aggregate(avg=Avg('analyzer_duration_ms'))['avg']

print(f'Analyzed articles: {analyzed_articles.count()}')
print(f'Total cost: ${total_cost:.6f}')
print(f'Average cost per article: ${avg_cost:.6f}')
print(f'Average duration: {avg_duration:.0f}ms')

# Daily processing volume
from django.utils import timezone
from datetime import timedelta

today = timezone.now().date()
yesterday = today - timedelta(days=1)

today_articles = analyzed_articles.filter(analyzed_at__date=today).count()
yesterday_articles = analyzed_articles.filter(analyzed_at__date=yesterday).count()

print(f'Articles analyzed today: {today_articles}')
print(f'Articles analyzed yesterday: {yesterday_articles}')
"
```

### Troubleshooting Common Issues

**Fix Failed Analyses:**
```bash
# Reset failed articles for retry
./docker.sh django shell -c "
from apps.articles.models import Article

failed_articles = Article.objects.filter(
    analyzer_status='failed',
    analyzer_attempts__lt=3
)

print(f'Found {failed_articles.count()} failed articles to retry')

for article in failed_articles:
    article.analyzer_status = 'pending'
    article.analyzer_error_message = ''
    article.save()
    print(f'Reset article {article.id} for retry')
"

# Process pending articles
./docker.sh django shell -c "
from apps.content.analyzer.tasks import analyze_article_pipeline

pending_articles = Article.objects.filter(analyzer_status='pending')[:5]
for article in pending_articles:
    task = analyze_article_pipeline.delay(article.id)
    print(f'Queued article {article.id}: {task.id}')
"
```

**Clean Up Orphaned Data:**
```bash
# Remove orphaned events
./docker.sh django shell -c "
from apps.content.analyzer.models import Event, ArticleEvent

orphaned_events = Event.objects.filter(articleevent__isnull=True)
count = orphaned_events.count()
orphaned_events.delete()
print(f'Deleted {count} orphaned events')
"

# Remove orphaned entities
./docker.sh django shell -c "
from apps.content.analyzer.models import Entity, ArticleEntity

orphaned_entities = Entity.objects.filter(articleentity__isnull=True, article_count=0)
count = orphaned_entities.count()
orphaned_entities.delete()
print(f'Deleted {count} orphaned entities')
"
```

This command reference provides comprehensive guidance for operating and maintaining the analyzer service in production and development environments. 