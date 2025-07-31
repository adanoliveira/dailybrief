# Analyzer Service API Reference

> **Complete API reference for the AI Content Analysis Service classes, methods, and data models**

This document provides comprehensive API documentation for all public interfaces, service classes, and data models in the analyzer service.

## 📖 Table of Contents

- [Service Classes](#service-classes)
- [Data Models](#data-models)
- [Task Functions](#task-functions)
- [Configuration](#configuration)

## Service Classes

### AnalyzerService

**Location:** `backend/apps/content/analyzer/services.py`

**Purpose:** Main orchestrator for the 8-stage analysis pipeline

#### Main Methods

##### `analyze_article(article, force=False)`

```python
def analyze_article(self, article: Article, force: bool = False) -> Dict[str, Any]:
    """
    Main entry point for article analysis
    
    Args:
        article (Article): Article instance to analyze
        force (bool): Whether to force re-analysis, cleaning existing events
        
    Returns:
        Dict containing:
            - success (bool): Whether analysis succeeded
            - article_id (int): ID of analyzed article
            - cost_usd (Decimal): Total cost of analysis
            - duration_ms (int): Processing time in milliseconds
            - stages_completed (List[str]): Successfully completed stages
            - error_message (str): Error details if failed
            - failed_stage (str): Stage where failure occurred
    
    Raises:
        ValueError: If article doesn't meet prerequisites
        Exception: For unexpected pipeline failures
    """
```

**Prerequisites:**
- Article must have `summarization_status = 'completed'`
- Article must have `ArticleSummary` record
- Article `analyzer_attempts < 3` (unless force=True)

**Processing Stages:**
1. Language detection (fastText/langdetect)
2. Linguistic analysis (textstat + GPT style classification)
3. Entity extraction (spaCy NER + resolution)
4. Event detection (GPT-4.1-mini with reasoning)
5. Topic classification (GPT-4o-mini)
6. Region detection (GPT-4o-mini)
7. Event resolution (embedding-based clustering)
8. Persistence (database storage)

## Data Models

### ArticleAnalysis

**Location:** `backend/apps/content/analyzer/models.py`

**Purpose:** Store linguistic and classification results for articles

#### Fields

```python
# Primary relationships
id = AutoField(primary_key=True)
public_id = UUIDField(default=uuid.uuid4, unique=True)
article = OneToOneField('articles.Article', related_name='analysis')

# Linguistic Analysis (Enhanced with Full Content Processing)
language_detected = CharField(max_length=5)  # ISO 639-1 code
language_confidence = FloatField(default=0.0)
readability_flesch = FloatField()  # 0-100 scale (calculated from full content)
reading_time_sec = IntegerField()  # Accurate calculation from full word count
word_count = IntegerField(default=0)  # Precise count from full content
sentiment_score = FloatField(null=True)  # spaCy sentiment analysis (truncated content)
style_tone = CharField(max_length=20, choices=STYLE_CHOICES)  # GPT analysis (truncated content)

# Classification Results
primary_topic = CharField(max_length=50, null=True)
secondary_topics = JSONField(default=list)
primary_region = CharField(max_length=10, default='universal')
regions_detected = JSONField(default=list)

# Processing metadata
analyzer_version = CharField(max_length=10, default='1.0')
tokens_input = IntegerField(default=0)
tokens_output = IntegerField(default=0)
processing_time_ms = IntegerField(default=0)
cost_usd = DecimalField(max_digits=8, decimal_places=6, default=0)
ai_model_used = CharField(max_length=50, default='gpt-4.1-mini')

# Timestamps
created_at = DateTimeField(auto_now_add=True)
updated_at = DateTimeField(auto_now=True)
```

### Entity

**Location:** `backend/apps/content/analyzer/models.py`

**Purpose:** Master entity catalog with deduplication

#### Fields

```python
# Core identification
public_id = UUIDField(default=uuid.uuid4, unique=True)
canonical_name = CharField(max_length=255, unique=True)
display_name = CharField(max_length=255)
entity_type = CharField(max_length=20, choices=ENTITY_TYPE_CHOICES)

# External linking
wikidata_id = CharField(max_length=50, null=True, blank=True)

# Deduplication
embedding = VectorField(dimensions=384, null=True, blank=True)  # MiniLM

# Usage statistics
article_count = IntegerField(default=0)
first_seen_at = DateTimeField(auto_now_add=True)
last_seen_at = DateTimeField(auto_now=True)
```

### Event

**Location:** `backend/apps/content/analyzer/models.py`

**Purpose:** Story events for clustering and timeline features

#### Fields

```python
# Core identification
public_id = UUIDField(default=uuid.uuid4, unique=True)
title = CharField(max_length=255)
abstract = TextField()  # AI-generated summary
facts = JSONField(default=list)  # Key facts from articles
event_type = CharField(max_length=20, choices=EVENT_TYPE_CHOICES)

# Deduplication
event_hash = CharField(max_length=64, unique=True)  # SHA-256
embedding = VectorField(dimensions=1536)  # OpenAI embedding

# Timeline metadata
first_seen_at = DateTimeField()
last_seen_at = DateTimeField()
article_count = IntegerField(default=1)
```

### ArticleEvent

**Location:** `backend/apps/content/analyzer/models.py`

**Purpose:** Link articles to events with relevance scoring

#### Fields

```python
article = ForeignKey('articles.Article', on_delete=CASCADE)
event = ForeignKey(Event, on_delete=CASCADE)

# Quality metrics
relevance_score = FloatField()  # 0.7-1.0 range
is_primary = BooleanField(default=False)

# Metadata
created_at = DateTimeField(auto_now_add=True)
```

## Task Functions

### analyze_article_pipeline

**Location:** `backend/apps/content/analyzer/tasks.py`

**Purpose:** Main Celery task for article analysis

```python
@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def analyze_article_pipeline(self, article_id: int, force_regenerate: bool = False):
    """
    Analyze article using full 8-stage pipeline
    
    Args:
        article_id (int): ID of article to analyze
        force_regenerate (bool): Whether to force re-analysis
        
    Returns:
        Dict with analysis results and metadata
        
    Retry Logic:
        - Transient failures (network, rate limit): Retry with backoff
        - Permanent failures (missing data): No retry
        - System errors: Exponential backoff up to 3 attempts
    """
```

### process_pending_analyses

**Location:** `backend/apps/content/analyzer/tasks.py`

**Purpose:** Batch processing of pending articles

```python
@shared_task
def process_pending_analyses(limit: int = 10):
    """
    Process articles waiting for analysis
    
    Args:
        limit (int): Maximum articles to queue
        
    Returns:
        Dict with queued task information
        
    Selection Criteria:
        - analyzer_status = 'pending'
        - summarization_status = 'completed'
        - Order by published_at DESC
    """
```

## Configuration

### AI Provider Configuration

**Operations:**

```python
ANALYZER_OPERATIONS = {
    'event_detection': {
        'operation': 'event_detection',
        'model_preference': 'gpt-4.1-mini',
        'temperature': 0.1,
        'max_tokens': 600,
        'cost_target': Decimal('0.000040'),
        'description': 'Event identification with reasoning framework'
    },
    'topic_classification': {
        'operation': 'topic_classification',
        'model_preference': 'gpt-4o-mini',
        'temperature': 0.0,
        'max_tokens': 100,
        'cost_target': Decimal('0.000020'),
        'description': 'Multi-level topic classification'
    },
    'region_detection': {
        'operation': 'region_detection',
        'model_preference': 'gpt-4o-mini',
        'temperature': 0.0,
        'max_tokens': 100,
        'cost_target': Decimal('0.000010'),
        'description': 'Geographic focus identification'
    },
    'style_classification': {
        'operation': 'style_classification',
        'model_preference': 'gpt-4o-mini',
        'temperature': 0.0,
        'max_tokens': 20,
        'cost_target': Decimal('0.000005'),
        'description': 'Style and tone classification'
    }
}
```

### Performance Targets

```python
PERFORMANCE_TARGETS = {
    'cost_per_article': Decimal('0.00019'),  # Budget ceiling
    'processing_time_ms': 15000,  # 15 seconds target
    'success_rate': 0.95,  # 95% success rate
    'relevance_threshold': 0.7,  # Minimum event relevance
}
```

This API reference provides complete documentation for integrating with and extending the analyzer service. 