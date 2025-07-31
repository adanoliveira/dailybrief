# Analyzer Service Implementation Guide

> **Technical implementation patterns and integration guide for the AI Content Analysis Service**

This document provides detailed implementation guidance for integrating, extending, and maintaining the analyzer service within the DailyBrief ecosystem.

## 📖 Table of Contents

- [Service Integration](#service-integration)
- [Database Schema](#database-schema)
- [Core Service Classes](#core-service-classes)
- [Prompt Engineering](#prompt-engineering)
- [Task Management](#task-management)
- [Extension Patterns](#extension-patterns)

## Service Integration

### Prerequisites Setup

The analyzer service requires articles to have completed summarization before analysis can begin.

**Article Model Extensions:**
```python
# backend/apps/articles/models.py
class Article(models.Model):
    # ... existing fields ...
    
    # ===== STEP 5: ANALYZER FIELDS =====
    analyzer_status = models.CharField(
        max_length=20,
        choices=AnalyzerStatus.choices,
        default=AnalyzerStatus.PENDING,
        db_index=True
    )
    analyzed_at = models.DateTimeField(null=True, blank=True)
    analyzer_attempts = models.IntegerField(default=0)
    last_analyzer_attempt = models.DateTimeField(null=True, blank=True)
    analyzer_error_message = models.TextField(blank=True)
    
    # Performance tracking
    analyzer_duration_ms = models.IntegerField(null=True, blank=True)
    analyzer_cost_usd = models.DecimalField(max_digits=8, decimal_places=6, null=True, blank=True)
    
    @property
    def needs_analysis(self):
        """Check if article needs analyzer processing"""
        return (
            self.summarization_status == SummarizationStatus.COMPLETED and
            hasattr(self, 'structured_summary') and
            self.analyzer_status == AnalyzerStatus.PENDING and
            self.analyzer_attempts < 3
        )
```

### Service Factory Pattern

**Service Instantiation:**
```python
# backend/apps/content/analyzer/services.py
def get_analyzer_service():
    """Factory function to get analyzer service instance"""
    return AnalyzerService()

class AnalyzerService:
    def __init__(self):
        self.ai_service = get_ai_service()
        self.prompts = AnalyzerPrompts()
        
        # Initialize tools
        self._init_spacy_model()
        self._init_fasttext_model()
    
    def _init_spacy_model(self):
        """Initialize spaCy model with fallback"""
        try:
            import spacy
            self.nlp = spacy.load('en_core_web_lg')
        except OSError:
            logger.warning("spaCy model en_core_web_lg not found. Falling back to en_core_web_sm.")
            try:
                self.nlp = spacy.load('en_core_web_sm')
            except OSError:
                logger.warning("No spaCy model found. Entity extraction will use regex fallback.")
                self.nlp = None
    
    def _init_fasttext_model(self):
        """Initialize fastText model with fallback"""
        try:
            import fasttext
            self.fasttext_model = fasttext.load_model('lid.176.bin')
        except Exception:
            logger.warning("fastText model not found. Using langdetect fallback.")
            self.fasttext_model = None

## Database Schema

### Core Models Implementation

The analyzer service introduces several new models for storing analysis results and managing entity/event relationships.

**ArticleAnalysis Model:**
```python
# backend/apps/content/analyzer/models.py
class ArticleAnalysis(models.Model):
    """Core analysis results for an article"""
    
    # Primary relationships
    id = models.AutoField(primary_key=True)
    public_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    article = models.OneToOneField(
        'articles.Article',
        on_delete=models.CASCADE,
        related_name='analysis'
    )
    
    # Linguistic Analysis
    language_detected = models.CharField(max_length=5, help_text="ISO 639-1 language code")
    language_confidence = models.FloatField(default=0.0)
    readability_flesch = models.FloatField(help_text="Flesch readability score 0-100")
    reading_time_sec = models.IntegerField(help_text="Estimated reading time in seconds")
    word_count = models.IntegerField(default=0)
    style_tone = models.CharField(
        max_length=20,
        choices=[
            ('factual', 'Factual'),
            ('opinion', 'Opinion'),
            ('narrative', 'Narrative'),
            ('analytical', 'Analytical'),
            ('satirical', 'Satirical'),
            ('sensational', 'Sensational'),
        ]
    )
    
    # Classification Results
    primary_topic = models.CharField(max_length=50, null=True, blank=True)
    secondary_topics = models.JSONField(default=list)
    primary_region = models.CharField(max_length=10, default='universal')
    regions_detected = models.JSONField(default=list)
    
    # Processing metadata
    analyzer_version = models.CharField(max_length=10, default='1.0')
    tokens_input = models.IntegerField(default=0)
    tokens_output = models.IntegerField(default=0)
    processing_time_ms = models.IntegerField(default=0)
    cost_usd = models.DecimalField(max_digits=8, decimal_places=6, default=0)
    ai_model_used = models.CharField(max_length=50, default='gpt-4.1-mini')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

**Entity Management Models:**
```python
class Entity(models.Model):
    """Master entity catalog with deduplication"""
    
    # Core identification
    public_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    canonical_name = models.CharField(max_length=255, unique=True)
    display_name = models.CharField(max_length=255)
    entity_type = models.CharField(
        max_length=20,
        choices=[
            ('PERSON', 'Person'),
            ('ORGANIZATION', 'Organization'),
            ('LOCATION', 'Location'),
            ('FACILITY', 'Facility'),
            ('EVENT', 'Event'),
            ('WORK', 'Creative Work'),
            ('PRODUCT', 'Product'),
            ('FINANCIAL_ASSET', 'Financial Asset'),
            ('LAW', 'Law/Regulation'),
            ('PROGRAM', 'Program/Policy'),
            ('OTHER', 'Other'),
        ]
    )
    
    # External linking
    wikidata_id = models.CharField(max_length=50, null=True, blank=True)
    
    # Deduplication embedding
    embedding = VectorField(dimensions=384, null=True, blank=True)
    
    # Usage statistics
    article_count = models.IntegerField(default=0)
    first_seen_at = models.DateTimeField(auto_now_add=True)
    last_seen_at = models.DateTimeField(auto_now=True)

class EntityAlias(models.Model):
    """Alternative names/spellings for entities"""
    entity = models.ForeignKey(Entity, on_delete=models.CASCADE, related_name='aliases')
    alias = models.CharField(max_length=255, unique=True)
```

**Event Clustering Models:**
```python
class Event(models.Model):
    """Story events for clustering and timeline features"""
    
    # Core identification
    public_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    title = models.CharField(max_length=255)
    abstract = models.TextField(help_text="AI-generated event summary")
    facts = models.JSONField(default=list, help_text="Key facts from articles")
    event_type = models.CharField(
        max_length=20,
        choices=[
            ('conflict', 'Conflict'),
            ('sports', 'Sports'),
            ('policy_change', 'Policy Change'),
            ('product_launch', 'Product Launch'),
            ('earnings', 'Earnings'),
            ('incident', 'Incident'),
            ('meeting', 'Meeting'),
            ('acquisition', 'Acquisition'),
            ('partnership', 'Partnership'),
            ('research', 'Research'),
            ('legal', 'Legal'),
            ('election', 'Election'),
            ('natural_disaster', 'Natural Disaster'),
            ('cultural', 'Cultural'),
            ('other', 'Other'),
        ],
        default='other'
    )
    
    # Deduplication
    event_hash = models.CharField(max_length=64, unique=True)
    embedding = VectorField(dimensions=1536, help_text="Event embedding for similarity")
    
    # Timeline metadata
    first_seen_at = models.DateTimeField()
    last_seen_at = models.DateTimeField()
    article_count = models.IntegerField(default=1)

class ArticleEvent(models.Model):
    """Links articles to events with relevance scoring"""
    article = models.ForeignKey('articles.Article', on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    
    # Quality metrics
    relevance_score = models.FloatField(help_text="Relevance score 0.7-1.0")
    is_primary = models.BooleanField(default=False)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('article', 'event')
```

## Core Service Classes

### Main Service Implementation

**AnalyzerService Class:**
```python
class AnalyzerService:
    """Main analyzer service orchestrating the 8-stage pipeline"""
    
    def analyze_article(self, article: Article, force: bool = False) -> Dict[str, Any]:
        """
        Main entry point for article analysis
        
        Args:
            article: Article instance to analyze
            force: Whether to force re-analysis
            
        Returns:
            Dict containing analysis results and metadata
        """
        # Validation
        if not force and not article.needs_analysis:
            return {
                'success': False,
                'reason': 'Article does not need analysis',
                'status': article.analyzer_status
            }
        
        # Force cleanup if needed
        if force:
            self._cleanup_article_events(article)
        
        # Create tracking request
        analyzer_request = AnalyzerRequest.objects.create(
            article=article,
            status='queued'
        )
        
        try:
            # Execute pipeline
            results = self._execute_analysis_pipeline(article, analyzer_request)
            
            # Store results
            if results['success']:
                self._save_analysis_results(article, results, analyzer_request)
                article.analyzer_status = AnalyzerStatus.COMPLETED
                article.analyzed_at = timezone.now()
            else:
                article.analyzer_status = AnalyzerStatus.FAILED
                article.analyzer_error_message = results.get('error_message', '')
            
            # Update attempt tracking
            article.analyzer_attempts += 1
            article.last_analyzer_attempt = timezone.now()
            article.analyzer_duration_ms = results.get('duration_ms', 0)
            article.analyzer_cost_usd = results.get('cost_usd', Decimal('0.00'))
            article.save()
            
            return results
            
        except Exception as e:
            logger.error(f"Analyzer pipeline failed for article {article.id}: {e}")
            analyzer_request.status = 'failed'
            analyzer_request.last_error = str(e)
            analyzer_request.save()
            
            return {
                'success': False,
                'error_message': f"Pipeline execution failed: {e}",
                'article_id': article.id
            }
```

### Entity Resolution Implementation

**Entity Resolver:**
```python
def _resolve_entity(self, raw_text: str, entity_type: str) -> int:
    """
    Resolve entity to canonical form with three-phase strategy
    
    Args:
        raw_text: Raw entity text from NER
        entity_type: spaCy entity type
        
    Returns:
        Entity ID (existing or newly created)
    """
    # Phase 1: Canonicalize name
    canonical_name = self._canonicalize_entity_name(raw_text)
    mapped_type = self._map_spacy_to_entity_type(entity_type)
    
    # Phase 2: Exact canonical match
    existing_entity = Entity.objects.filter(canonical_name=canonical_name).first()
    if existing_entity:
        self._update_entity_usage(existing_entity)
        return existing_entity.id
    
    # Phase 3: Alias lookup
    alias_match = EntityAlias.objects.select_related('entity').filter(
        alias=canonical_name
    ).first()
    if alias_match:
        self._update_entity_usage(alias_match.entity)
        return alias_match.entity.id
    
    # Phase 4: Embedding similarity search
    if len(canonical_name) > 3:  # Skip very short names
        embedding = self._generate_entity_embedding(canonical_name)
        similar_entities = Entity.objects.filter(
            entity_type=mapped_type
        ).order_by(
            self.embedding.cosine_distance(embedding)
        )[:3]
        
        for similar_entity in similar_entities:
            distance = self._calculate_cosine_distance(
                similar_entity.embedding, 
                embedding
            )
            if distance < 0.10:  # Very similar threshold
                # Create alias and return existing entity
                EntityAlias.objects.get_or_create(
                    entity=similar_entity,
                    alias=canonical_name
                )
                self._update_entity_usage(similar_entity)
                return similar_entity.id
    
    # Phase 5: Create new entity
    new_entity = Entity.objects.create(
        canonical_name=canonical_name,
        display_name=raw_text,
        entity_type=mapped_type,
        embedding=embedding if 'embedding' in locals() else None,
        article_count=1
    )
    
    logger.info(f"Created new entity: {new_entity.canonical_name} ({mapped_type})")
    return new_entity.id
```

## Content Processing Strategy

### Linguistic Analysis Implementation

The analyzer service uses a dual content strategy for optimal accuracy and cost efficiency:

**Full Content for Accurate Metrics:**
```python
def _get_full_content_for_linguistic_analysis(self, article: Article) -> str:
    """
    Get complete content using content assembler for accurate readability,
    word count, and reading time calculations.
    """
    from apps.content.summariser.content_assembler import get_markdown_assembler
    
    content_blocks = getattr(article, 'content_blocks', None)
    if not content_blocks:
        return article.content if article.content else article.title
    
    # Use content assembler with high character limit for full content
    assembler = get_markdown_assembler(
        max_chars=50000,  # High limit to get full content
        use_intelligent_summarization=False,  # Don't summarize for metrics
        summarization_mode="custom"
    )
    
    return assembler.assemble_content(content_blocks, article.title)
```

**Truncated Content for Cost Optimization:**
```python
def _get_truncated_content_for_analysis(self, article: Article, max_chars: int = 5000) -> str:
    """
    Get intelligently truncated content for sentiment and style analysis
    to optimize costs while maintaining content quality.
    """
    from apps.content.summariser.content_assembler import get_markdown_assembler
    
    content_blocks = getattr(article, 'content_blocks', None)
    if not content_blocks:
        content = article.content if article.content else article.title
        return content[:max_chars] if len(content) > max_chars else content
    
    # Use content assembler with intelligent summarization for cost optimization
    assembler = get_markdown_assembler(
        max_chars=max_chars,
        use_intelligent_summarization=True,
        summarization_mode="hybrid"  # Best balance of quality and structure
    )
    
    return assembler.assemble_content(content_blocks, article.title)
```

**Linguistic Analysis Pipeline:**
```python
def _stage_2_linguistic_analysis(self, article: Article, content: str, analysis_record: ArticleAnalysis):
    """
    Stage 2: Linguistic Analysis using optimized content strategies
    
    - Uses full content for FREE operations (readability, word count, reading time)
    - Uses truncated content for AI operations (sentiment, style/tone analysis)
    """
    # Get full content for accurate metrics (FREE operations)
    full_content = self._get_full_content_for_linguistic_analysis(article)
    
    # 1. Calculate readability metrics using full content (FREE - textstat)
    readability_score = textstat.flesch_reading_ease(full_content)
    word_count = textstat.lexicon_count(full_content)
    read_time_minutes = word_count / 225.0  # 225 WPM average
    
    # Update article with accurate metrics
    article.readability_score = readability_score
    article.word_count = word_count
    article.read_time_minutes = read_time_minutes
    article.save(update_fields=['readability_score', 'word_count', 'read_time_minutes'])
    
    # Get truncated content for AI analysis (cost optimization)
    truncated_content = self._get_truncated_content_for_analysis(article, max_chars=5000)
    
    # 2. Calculate sentiment score using spaCy (FREE)
    sentiment_score = None
    if nlp:
        doc = nlp(truncated_content)
        sentiment_score = sum(token.sentiment for token in doc) / len(doc)
        article.sentiment_score = sentiment_score
        article.save(update_fields=['sentiment_score'])
    
    # 3. Analyze style and tone using GPT-4o-mini (PAID)
    prompt = self.prompts.linguistic_analysis_prompt(article.title, truncated_content)
    response = self.ai_service.call_llm(
        prompt=prompt,
        operation="linguistic_analysis",
        max_tokens=150,
        temperature=0.1
    )
    
    result = self.prompts.validate_linguistic_output(response.content)
    style_tone = result.get('style_tone', 'factual')
    
    # Update analysis record
    analysis_record.style_tone = style_tone
    analysis_record.save(update_fields=['style_tone'])
    
    return {
        'readability_score': readability_score,
        'word_count': word_count,
        'read_time_minutes': read_time_minutes,
        'sentiment_score': sentiment_score,
        'style_tone': style_tone,
        'cost': response.usage.get('total_cost', 0)
    }
```

**Benefits of Dual Content Strategy:**
- **Accurate Metrics**: Full content ensures precise readability, word count, and reading time calculations
- **Cost Optimization**: Truncated content (5,000 chars) reduces AI analysis costs by 80-90%
- **Quality Preservation**: Intelligent summarization maintains document structure and key information
- **Robust Fallbacks**: Multiple fallback mechanisms handle missing content blocks gracefully

## Prompt Engineering

### Template Structure

The analyzer service uses advanced prompt engineering with reasoning frameworks for optimal AI performance.

**Event Detection Prompt:**
```python
@staticmethod
def event_detection_prompt(title: str, content: str, published_at: str = None) -> str:
    """Event detection with advanced reasoning framework"""
    published_info = f"\nPublished: {published_at}" if published_at else ""
    
    return f"""# REASONING TASK: Event Extraction & Analysis

You are an expert news analyst using advanced reasoning to extract and categorize events.

## REASONING PROCESS

### STEP 1: Article Comprehension
First, analyze what this article is fundamentally about:
- What is the ONE core event or story this article covers?
- What broader ongoing story does this belong to?
- What specific recent developments are being reported?

### STEP 2: Event Identification Strategy
Extract events at TWO levels:
1. **BROAD ONGOING EVENT** (if applicable): The major ongoing story/situation this belongs to
2. **SPECIFIC DEVELOPMENTS** (1-3): Recent specific events, announcements, or incidents

### STEP 3: Event Naming Protocol
**CRITICAL RULE:** Always name events as NOUNS (what happened), never as ACTIONS (who did what)

### STEP 4: Relevance Scoring Rubric
**1.0 - Central/Primary Event**: Main reason article was written
**0.9 - Highly Relevant Context**: Major ongoing story
**0.7 - Relevant Background**: Important context

### STEP 5: Self-Correction Check
Verify all events follow naming protocol and relevance thresholds

## INPUT ARTICLE
**Title:** {title}{published_info}
**Content:** {content}

Return STRICT JSON with events array."""
```

## Task Management

### Celery Integration

**Main Analysis Task:**
```python
# backend/apps/content/analyzer/tasks.py
@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def analyze_article_pipeline(self, article_id: int, force_regenerate: bool = False):
    """
    Main analyzer task with intelligent retry logic
    
    Args:
        article_id: ID of article to analyze
        force_regenerate: Whether to force re-analysis
        
    Returns:
        Dict with success status and metadata
    """
    try:
        from django.apps import apps
        Article = apps.get_model('articles', 'Article')
        
        article = Article.objects.get(id=article_id)
        service = get_analyzer_service()
        
        result = service.analyze_article(article, force_regenerate)
        
        if result['success']:
            return {
                'success': True,
                'article_id': article_id,
                'cost_usd': float(result.get('cost_usd', 0)),
                'duration_ms': result.get('duration_ms', 0),
                'stages_completed': result.get('stages_completed', [])
            }
        else:
            # Smart retry based on failure type
            error_message = result.get('error_message', '')
            
            # Transient failures - retry
            if any(keyword in error_message.lower() for keyword in [
                'timeout', 'rate limit', 'network', 'connection'
            ]):
                raise self.retry(countdown=300)
            
            # Permanent failures - don't retry
            return {
                'success': False,
                'article_id': article_id,
                'error': error_message,
                'failed_stage': result.get('failed_stage', 'unknown')
            }
            
    except Exception as e:
        logger.error(f"Analyzer task failed for article {article_id}: {e}")
        
        # System error retry logic
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=600 * (2 ** self.request.retries))
        
        return {
            'success': False,
            'article_id': article_id,
            'error': f"System error: {str(e)}"
        }

@shared_task
def process_pending_analyses(limit: int = 10):
    """Process articles waiting for analysis"""
    from django.apps import apps
    Article = apps.get_model('articles', 'Article')
    
    pending_articles = Article.objects.filter(
        analyzer_status='pending',
        summarization_status='completed'
    ).order_by('-published_at')[:limit]
    
    results = []
    for article in pending_articles:
        task_result = analyze_article_pipeline.delay(article.id)
        results.append({
            'article_id': article.id,
            'task_id': task_result.id
        })
    
    return {
        'queued_count': len(results),
        'tasks': results
    }
```

## Extension Patterns

### Adding New Analysis Stages

**Stage Extension Framework:**
```python
def _stage_9_custom_analysis(self, article: Article, enhanced_content: str, previous_results: Dict) -> Dict:
    """
    Template for adding new analysis stages
    
    Args:
        article: Article being analyzed
        enhanced_content: Processed content
        previous_results: Results from previous stages
        
    Returns:
        Dict with stage results and metadata
    """
    try:
        # Custom analysis logic here
        custom_result = self._perform_custom_analysis(enhanced_content)
        
        return {
            'success': True,
            'data': custom_result,
            'cost_usd': Decimal('0.00'),  # Update if using AI
            'duration_ms': 0  # Track processing time
        }
        
    except Exception as e:
        logger.error(f"Custom analysis failed for article {article.id}: {e}")
        return {
            'success': False,
            'error': str(e)
        }
```

### Custom Entity Types

**Entity Type Extension:**
```python
# Extend entity types in models.py
ENTITY_TYPE_CHOICES = [
    # Existing types...
    ('CUSTOM_TYPE', 'Custom Entity Type'),
    ('SPECIALIZED', 'Specialized Entity'),
]

# Custom resolution logic
def _map_custom_entity_type(self, spacy_label: str, context: str) -> str:
    """Map custom entity types based on context"""
    if 'custom_pattern' in context.lower():
        return 'CUSTOM_TYPE'
    
    return self._map_spacy_to_entity_type(spacy_label)
```

This implementation guide provides the foundation for extending and maintaining the analyzer service while following established patterns and best practices. 