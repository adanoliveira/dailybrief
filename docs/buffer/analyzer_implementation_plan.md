# Article Analyzer Service – Implementation Plan (v1.0)

> **Purpose** – Enrich summarized articles with machine-readable labels for topic grouping, entity extraction, event linking, region classification, and linguistic analysis. Integrates with existing DailyBrief architecture following established patterns from the summariser service.

---

## 1. Architecture Integration

### 1.1 Placement in Content Pipeline

```
Content Enrichment Pipeline:
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Fetcher   │───►│  Processor  │───►│   Quality   │───►│ Summariser  │───►│  Analyzer   │
│  (Step 1)   │    │  (Step 2)   │    │  (Step 3)   │    │  (Step 4)   │    │  (Step 5)   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                                                                  │                    │
                                                          ArticleSummary       ArticleAnalysis
                                                          + Embedding          + Entities + Events
```

### 1.2 Service Architecture

Following the summariser pattern:

```python
# apps/content/analyzer/services.py
class AnalyzerService:
    def __init__(self):
        self.ai_service = get_ai_service()      # From aiproviders
        self.prompts = AnalyzerPrompts()        # Domain-specific prompts
        
    def analyze_article(self, article, force_regenerate=False):
        """Main entry point - orchestrates analysis pipeline"""
        # 1. Validate prerequisites (needs summary)
        # 2. Execute analysis stages
        # 3. Store results and update article status
        # 4. Return AnalyzerResult
```

---

## 2. Data Model Integration

### 2.1 Enhance Existing Article Model

```python
# backend/apps/articles/models.py - ADD these fields
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
    
    # Performance tracking (consistent with summariser)
    analyzer_duration_ms = models.IntegerField(null=True, blank=True)
    analyzer_cost_usd = models.DecimalField(max_digits=8, decimal_places=6, null=True, blank=True)
    
    # Enhanced classification
    primary_topic = models.ForeignKey(
        'feeds.Topic', 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='primary_articles'
    )
    primary_region = models.ForeignKey(
        'feeds.Region',
        on_delete=models.SET_NULL,
        null=True,
        related_name='primary_articles'
    )
    
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

### 2.2 Analyzer Domain Models

```python
# apps/content/analyzer/models.py

class AnalyzerStatus(models.TextChoices):
    PENDING = 'pending', 'Pending Analysis'
    PROCESSING = 'processing', 'Processing Analysis'
    COMPLETED = 'completed', 'Analysis Completed'
    FAILED = 'failed', 'Analysis Failed'

class ArticleAnalysis(models.Model):
    """
    Core analysis results for an article.
    Stores linguistic, topical, and geographic analysis.
    """
    # Primary key and relationships
    id = models.AutoField(primary_key=True)
    public_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    article = models.OneToOneField(
        'articles.Article',
        on_delete=models.CASCADE,
        related_name='analysis'
    )
    
    # Linguistic Analysis
    language_detected = models.CharField(max_length=5, help_text="Detected language code")
    language_confidence = models.FloatField(default=0.0)
    readability_flesch = models.FloatField(help_text="Flesch readability score")
    reading_time_sec = models.IntegerField(help_text="Estimated reading time in seconds")
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
    
    # Topic Classification
    primary_topic_confidence = models.FloatField(default=0.0)
    secondary_topics = models.JSONField(default=list, help_text="List of secondary topic slugs")
    
    # Region Classification
    region_primary_confidence = models.FloatField(default=0.0)
    regions_detected = models.JSONField(default=list, help_text="List of region codes")
    
    # Processing metadata (consistent with summariser)
    analyzer_version = models.CharField(max_length=10, default='1.0')
    tokens_input = models.IntegerField(default=0)
    tokens_output = models.IntegerField(default=0)
    processing_time_ms = models.IntegerField(default=0)
    cost_usd = models.DecimalField(max_digits=8, decimal_places=6, default=0)
    ai_model_used = models.CharField(max_length=50, default='gpt-4o-mini')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Entity(models.Model):
    """
    Master entity catalog with deduplication.
    """
    # Core fields
    public_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    canonical_name = models.CharField(max_length=255, unique=True, help_text="Canonicalized name")
    display_name = models.CharField(max_length=255, help_text="Human-readable name")
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
    
    # Vector embedding for deduplication (384-dim MiniLM)
    embedding = VectorField(dimensions=384, null=True, blank=True)
    
    # Metadata
    article_count = models.IntegerField(default=0, help_text="Number of articles mentioning this entity")
    first_seen_at = models.DateTimeField(auto_now_add=True)
    last_seen_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'analyzer_entity'
        indexes = [
            models.Index(fields=['canonical_name']),
            models.Index(fields=['entity_type']),
            models.Index(fields=['article_count']),
        ]

class EntityAlias(models.Model):
    """
    Alternative names/spellings for entities.
    """
    entity = models.ForeignKey(Entity, on_delete=models.CASCADE, related_name='aliases')
    alias = models.CharField(max_length=255, unique=True)
    
    class Meta:
        db_table = 'analyzer_entity_alias'

class Event(models.Model):
    """
    Story events for clustering and timeline features.
    """
    # Core fields
    public_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    title = models.CharField(max_length=255)
    abstract = models.TextField(help_text="AI-generated event summary")
    facts = models.JSONField(default=list, help_text="Key facts from articles")
    
    # Deduplication
    event_hash = models.CharField(max_length=64, unique=True, help_text="SHA-256 hash for deduplication")
    centroid_embed = VectorField(dimensions=1536, help_text="Centroid embedding for similarity")
    
    # Timeline
    first_seen_at = models.DateTimeField()
    last_seen_at = models.DateTimeField()
    article_count = models.IntegerField(default=1)
    
    # Integration with existing StoryGroup
    story_group = models.OneToOneField(
        'articles.StoryGroup',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='analyzer_event'
    )
    
    class Meta:
        db_table = 'analyzer_event'
        indexes = [
            models.Index(fields=['event_hash']),
            models.Index(fields=['last_seen_at']),
            models.Index(fields=['article_count']),
        ]

# Link Tables
class ArticleEntity(models.Model):
    """Links articles to entities."""
    article = models.ForeignKey('articles.Article', on_delete=models.CASCADE)
    entity = models.ForeignKey(Entity, on_delete=models.CASCADE)
    confidence = models.FloatField(default=1.0)
    
    class Meta:
        unique_together = ('article', 'entity')
        db_table = 'analyzer_article_entity'

class ArticleEvent(models.Model):
    """Links articles to events (one-to-one for main event)."""
    article = models.OneToOneField('articles.Article', on_delete=models.CASCADE, primary_key=True)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    
    class Meta:
        db_table = 'analyzer_article_event'

class EventEntity(models.Model):
    """Links events to entities."""
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    entity = models.ForeignKey(Entity, on_delete=models.CASCADE)
    
    class Meta:
        unique_together = ('event', 'entity')
        db_table = 'analyzer_event_entity'

class AnalyzerRequest(models.Model):
    """
    Tracks analyzer processing requests (follows SummarizationRequest pattern).
    """
    # Primary key and relationships
    id = models.AutoField(primary_key=True)
    public_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    article = models.ForeignKey(
        'articles.Article',
        on_delete=models.CASCADE,
        related_name='analyzer_requests'
    )
    
    # Processing state
    status = models.CharField(max_length=20, choices=[
        ('queued', 'Queued'),
        ('linguistic_processing', 'Linguistic Processing'),
        ('entity_processing', 'Entity Processing'),
        ('event_processing', 'Event Processing'),
        ('topic_processing', 'Topic Processing'),
        ('region_processing', 'Region Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ], default='queued', db_index=True)
    
    # Pipeline tracking
    stages_completed = models.JSONField(default=list)
    pipeline_start_time = models.DateTimeField(null=True, blank=True)
    pipeline_end_time = models.DateTimeField(null=True, blank=True)
    
    # Error handling
    attempts = models.IntegerField(default=0)
    max_attempts = models.IntegerField(default=3)
    last_error = models.TextField(blank=True)
    failed_stage = models.CharField(max_length=30, blank=True)
    
    # Performance tracking
    total_cost_usd = models.DecimalField(max_digits=8, decimal_places=6, default=0)
    total_duration_ms = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'analyzer_request'
        ordering = ['-created_at']
```

---

## 3. Service Implementation

### 3.1 Core Service Class

```python
# apps/content/analyzer/services.py
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from decimal import Decimal

@dataclass
class AnalyzerResult:
    """Result of complete analyzer pipeline."""
    success: bool
    article_id: int
    
    # Analysis outputs
    linguistic_analysis: Dict[str, Any] = None
    entities_extracted: List[Dict[str, Any]] = None
    events_extracted: List[Dict[str, Any]] = None
    topics_classified: Dict[str, Any] = None
    regions_detected: Dict[str, Any] = None
    
    # Performance metrics
    total_cost_usd: Decimal = Decimal('0.0')
    total_duration_ms: int = 0
    stages_completed: List[str] = None
    
    # Error handling
    error_message: str = ""
    failed_stage: str = ""

class AnalyzerService:
    """
    Main analyzer service following SummarizationService patterns.
    """
    
    def __init__(self):
        self.ai_service = get_ai_service()
        self.prompts = AnalyzerPrompts()
        
    def analyze_article(self, article, force_regenerate=False) -> AnalyzerResult:
        """
        Main entry point for article analysis.
        
        Args:
            article: Article instance with completed summary
            force_regenerate: Whether to regenerate existing analysis
            
        Returns:
            AnalyzerResult with analysis data or error information
        """
        # Validate prerequisites
        if not self._validate_article_ready(article):
            return AnalyzerResult(
                success=False,
                article_id=article.id,
                error_message="Article not ready for analysis (missing summary)"
            )
        
        # Check existing analysis
        if not force_regenerate and hasattr(article, 'analysis'):
            return AnalyzerResult(
                success=True,
                article_id=article.id,
                linguistic_analysis=self._get_existing_analysis(article)
            )
        
        # Create processing request
        request = AnalyzerRequest.objects.create(
            article=article,
            status='queued'
        )
        
        try:
            # Execute analysis pipeline
            result = self._execute_analysis_pipeline(article, request)
            
            # Store results
            if result.success:
                self._save_analysis_results(article, result, request)
                article.analyzer_status = AnalyzerStatus.COMPLETED
                article.analyzed_at = timezone.now()
            else:
                article.analyzer_status = AnalyzerStatus.FAILED
                article.analyzer_error_message = result.error_message
            
            article.analyzer_attempts += 1
            article.last_analyzer_attempt = timezone.now()
            article.save()
            
            return result
            
        except Exception as e:
            logger.error(f"Analyzer pipeline failed for article {article.id}: {e}")
            request.status = 'failed'
            request.last_error = str(e)
            request.save()
            
            return AnalyzerResult(
                success=False,
                article_id=article.id,
                error_message=f"Pipeline execution failed: {e}"
            )
    
    def _execute_analysis_pipeline(self, article, request) -> AnalyzerResult:
        """Execute the 6-stage analysis pipeline."""
        start_time = time.time()
        total_cost = Decimal('0.0')
        stages_completed = []
        
        # Get summary data as input
        summary = article.structured_summary
        summary_data = {
            'headline': summary.headline,
            'abstract': summary.abstract,
            'facts': summary.facts,
            'opinions': summary.opinions,
            'impact': summary.impact,
            'embed': list(article.embedding.embedding) if hasattr(article, 'embedding') else []
        }
        
        # Stage 1: Linguistic Analysis
        linguistic_result = self._stage_linguistic_analysis(summary_data, request)
        if not linguistic_result['success']:
            return AnalyzerResult(
                success=False,
                article_id=article.id,
                failed_stage='linguistic_analysis',
                error_message=linguistic_result['error']
            )
        total_cost += linguistic_result['cost_usd']
        stages_completed.append('linguistic_analysis')
        
        # Stage 2: Entity Extraction
        entity_result = self._stage_entity_extraction(summary_data, request)
        if not entity_result['success']:
            return AnalyzerResult(
                success=False,
                article_id=article.id,
                failed_stage='entity_extraction',
                error_message=entity_result['error']
            )
        total_cost += entity_result['cost_usd']
        stages_completed.append('entity_extraction')
        
        # Stage 3: Event Extraction
        event_result = self._stage_event_extraction(summary_data, entity_result['entities'], request)
        if not event_result['success']:
            return AnalyzerResult(
                success=False,
                article_id=article.id,
                failed_stage='event_extraction',
                error_message=event_result['error']
            )
        total_cost += event_result['cost_usd']
        stages_completed.append('event_extraction')
        
        # Stage 4: Topic Classification
        topic_result = self._stage_topic_classification(summary_data, request)
        if not topic_result['success']:
            return AnalyzerResult(
                success=False,
                article_id=article.id,
                failed_stage='topic_classification',
                error_message=topic_result['error']
            )
        total_cost += topic_result['cost_usd']
        stages_completed.append('topic_classification')
        
        # Stage 5: Region Detection
        region_result = self._stage_region_detection(summary_data, entity_result['entities'], request)
        if not region_result['success']:
            return AnalyzerResult(
                success=False,
                article_id=article.id,
                failed_stage='region_detection',
                error_message=region_result['error']
            )
        total_cost += region_result['cost_usd']
        stages_completed.append('region_detection')
        
        total_duration = int((time.time() - start_time) * 1000)
        
        return AnalyzerResult(
            success=True,
            article_id=article.id,
            linguistic_analysis=linguistic_result['data'],
            entities_extracted=entity_result['entities'],
            events_extracted=event_result['events'],
            topics_classified=topic_result['topics'],
            regions_detected=region_result['regions'],
            total_cost_usd=total_cost,
            total_duration_ms=total_duration,
            stages_completed=stages_completed
        )
```

### 3.2 Prompt Templates

```python
# apps/content/analyzer/prompt_templates.py
class AnalyzerPrompts:
    """
    Centralized prompt templates for analyzer pipeline.
    """
    
    TEMPLATE_VERSION = "v1.0"
    
    @staticmethod
    def topic_classification_prompt(headline: str, abstract: str, facts: List[str]) -> str:
        """Topic classification using existing topic taxonomy."""
        facts_text = "\n".join(f"- {fact}" for fact in facts[:3])
        
        return f"""You are TopicClassifier-GPT. Classify this article into exactly ONE primary topic and up to THREE secondary topics from our taxonomy:

AVAILABLE TOPICS:
business, entertainment, general, health, science, sports, technology, cryptocurrency, us-politics, world-politics, climate, ai, markets

Return STRICT JSON:
{{
    "primary_topic": "topic_slug",
    "secondary_topics": ["topic1", "topic2"],
    "confidence": 0.95
}}

ARTICLE:
HEADLINE: {headline}
ABSTRACT: {abstract}
FACTS:
{facts_text}"""

    @staticmethod
    def region_detection_prompt(headline: str, abstract: str, entities: List[str]) -> str:
        """Region detection using ISO-3166-1 codes."""
        entities_text = ", ".join(entities[:5]) if entities else "None"
        
        return f"""You are RegionDetector-GPT. Identify the geographic focus of this article using ISO-3166-1 country codes.

Return STRICT JSON:
{{
    "primary_region": "US",
    "all_regions": ["US", "MX"],
    "confidence": 0.90
}}

Use "universal" if no specific region applies.

ARTICLE:
HEADLINE: {headline}
ABSTRACT: {abstract}
ENTITIES: {entities_text}"""

    @staticmethod
    def event_extraction_prompt(headline: str, abstract: str, facts: List[str]) -> str:
        """Event extraction for story clustering."""
        facts_text = "\n".join(f"- {fact}" for fact in facts[:3])
        
        return f"""You are EventExtractor-GPT. Identify the main event in this article for story clustering.

Return STRICT JSON:
{{
    "main_event": {{
        "title": "Event Title",
        "description": "Brief description",
        "entities": ["entity1", "entity2"]
    }},
    "secondary_events": []
}}

ARTICLE:
HEADLINE: {headline}
ABSTRACT: {abstract}
FACTS:
{facts_text}"""

    @staticmethod
    def style_tone_prompt(headline: str, abstract: str) -> str:
        """Style and tone classification."""
        return f"""You are StyleClassifier-GPT. Classify the tone of this article.

TONES: factual, opinion, narrative, analytical, satirical, sensational

Return STRICT JSON:
{{
    "style_tone": "factual",
    "confidence": 0.85
}}

ARTICLE:
HEADLINE: {headline}
ABSTRACT: {abstract}"""
```

---

## 4. Processing Pipeline Implementation

### 4.1 Stage Implementations

```python
# apps/content/analyzer/services.py (continued)

def _stage_linguistic_analysis(self, summary_data: Dict, request) -> Dict:
    """Stage 1: Linguistic analysis using free tools + GPT for style."""
    try:
        # Language detection (free)
        import fasttext
        model = fasttext.load_model('lid.176.bin')  # Download if needed
        text = f"{summary_data['headline']} {summary_data['abstract']}"
        lang_result = model.predict(text, k=1)
        language = lang_result[0][0].replace('__label__', '')
        confidence = float(lang_result[1][0])
        
        # Readability (free)
        import textstat
        readability = textstat.flesch_reading_ease(text)
        
        # Reading time (free)
        word_count = len(text.split())
        reading_time_sec = max(30, int(word_count * 60 / 200))  # 200 WPM
        
        # Style tone (GPT)
        style_prompt = self.prompts.style_tone_prompt(
            summary_data['headline'], 
            summary_data['abstract']
        )
        
        style_result = self.ai_service.complete_text(
            prompt=style_prompt,
            temperature=0.0,
            max_tokens=50
        )
        
        style_data = json.loads(style_result.content)
        
        return {
            'success': True,
            'data': {
                'language': language,
                'language_confidence': confidence,
                'readability_flesch': readability,
                'reading_time_sec': reading_time_sec,
                'style_tone': style_data['style_tone']
            },
            'cost_usd': self._calculate_cost(style_result.usage)
        }
        
    except Exception as e:
        logger.error(f"Linguistic analysis failed: {e}")
        return {'success': False, 'error': str(e)}

def _stage_entity_extraction(self, summary_data: Dict, request) -> Dict:
    """Stage 2: Entity extraction using spaCy + entity resolution."""
    try:
        import spacy
        nlp = spacy.load('en_core_web_lg')
        
        # Extract entities from summary text
        text = f"{summary_data['headline']} {summary_data['abstract']}"
        doc = nlp(text)
        
        raw_entities = []
        for ent in doc.ents:
            if ent.label_ in ['PERSON', 'ORG', 'GPE', 'LOC', 'EVENT', 'WORK_OF_ART', 'PRODUCT']:
                raw_entities.append({
                    'text': ent.text,
                    'label': ent.label_,
                    'start': ent.start_char,
                    'end': ent.end_char
                })
        
        # Add ticker symbols
        import re
        tickers = re.findall(r'\$[A-Z]{2,6}', text)
        for ticker in tickers:
            raw_entities.append({
                'text': ticker,
                'label': 'FINANCIAL_ASSET',
                'start': 0,
                'end': 0
            })
        
        # Resolve entities to canonical form
        resolved_entities = []
        for raw_ent in raw_entities:
            entity_id = self._resolve_entity(raw_ent['text'], raw_ent['label'])
            resolved_entities.append({
                'entity_id': entity_id,
                'text': raw_ent['text'],
                'type': self._map_spacy_to_entity_type(raw_ent['label'])
            })
        
        return {
            'success': True,
            'entities': resolved_entities,
            'cost_usd': Decimal('0.0')  # spaCy is free
        }
        
    except Exception as e:
        logger.error(f"Entity extraction failed: {e}")
        return {'success': False, 'error': str(e)}
```

---

## 5. Async Processing & API Integration

### 5.1 Celery Tasks

```python
# apps/content/analyzer/tasks.py
from celery import shared_task

@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def analyze_article_pipeline(self, article_id: int, force_regenerate: bool = False):
    """
    Main analyzer task following summarize_article_pipeline pattern.
    """
    try:
        from django.apps import apps
        Article = apps.get_model('articles', 'Article')
        
        article = Article.objects.get(id=article_id)
        service = get_analyzer_service()
        
        result = service.analyze_article(article, force_regenerate)
        
        if result.success:
            return {
                'success': True,
                'article_id': article_id,
                'cost_usd': float(result.total_cost_usd),
                'duration_ms': result.total_duration_ms,
                'stages_completed': result.stages_completed
            }
        else:
            # Smart retry based on failure type
            if result.failed_stage in ['linguistic_analysis', 'topic_classification']:
                raise self.retry(countdown=300)  # Retry transient failures
            
            return {
                'success': False,
                'article_id': article_id,
                'error': result.error_message,
                'failed_stage': result.failed_stage
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
    """Process articles waiting for analysis."""
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

### 5.2 API Endpoints

```python
# apps/content/analyzer/views.py
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json

@csrf_exempt
@require_http_methods(["POST", "OPTIONS"])
def generate_article_analysis(request, public_id):
    """Generate analysis for an article (matches summariser API pattern)."""
    
    # Handle CORS preflight
    if request.method == "OPTIONS":
        response = JsonResponse({})
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type"
        return response
    
    try:
        # Get article
        article = Article.objects.get(public_id=public_id)
        
        # Parse request body
        data = json.loads(request.body) if request.body else {}
        async_processing = data.get('async', True)
        force_regenerate = data.get('forceRegenerate', False)
        
        # Check if analysis already exists
        if not force_regenerate and hasattr(article, 'analysis'):
            response_data = {
                'success': True,
                'status': 'completed',
                'analysis': {
                    'primary_topic': article.primary_topic.slug if article.primary_topic else None,
                    'language': article.analysis.language_detected,
                    'style_tone': article.analysis.style_tone,
                    'reading_time_sec': article.analysis.reading_time_sec
                }
            }
        elif async_processing:
            # Queue async processing
            task = analyze_article_pipeline.delay(article.id, force_regenerate)
            article.analyzer_status = 'processing'
            article.save()
            
            response_data = {
                'success': True,
                'status': 'processing',
                'taskId': task.id,
                'pollUrl': f'/api/articles/{public_id}/analysis-status/'
            }
        else:
            # Synchronous processing
            service = get_analyzer_service()
            result = service.analyze_article(article, force_regenerate)
            
            if result.success:
                response_data = {
                    'success': True,
                    'status': 'completed',
                    'analysis': result.linguistic_analysis,
                    'cost_usd': float(result.total_cost_usd),
                    'duration_ms': result.total_duration_ms
                }
            else:
                response_data = {
                    'success': False,
                    'error': result.error_message,
                    'failed_stage': result.failed_stage
                }
        
        response = JsonResponse(response_data)
        response["Access-Control-Allow-Origin"] = "*"
        return response
        
    except Article.DoesNotExist:
        response = JsonResponse({'success': False, 'error': 'Article not found'}, status=404)
        response["Access-Control-Allow-Origin"] = "*"
        return response
    except Exception as e:
        response = JsonResponse({'success': False, 'error': str(e)}, status=500)
        response["Access-Control-Allow-Origin"] = "*"
        return response

@require_http_methods(["GET", "OPTIONS"])
def get_analysis_status(request, public_id):
    """Get analysis status for an article."""
    
    # Handle CORS preflight
    if request.method == "OPTIONS":
        response = JsonResponse({})
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        return response
    
    try:
        article = Article.objects.select_related('analysis', 'primary_topic').get(public_id=public_id)
        
        if article.analyzer_status == 'completed' and hasattr(article, 'analysis'):
            response_data = {
                'status': 'completed',
                'analysis': {
                    'primary_topic': article.primary_topic.slug if article.primary_topic else None,
                    'language': article.analysis.language_detected,
                    'style_tone': article.analysis.style_tone,
                    'reading_time_sec': article.analysis.reading_time_sec,
                    'readability_flesch': article.analysis.readability_flesch
                },
                'metadata': {
                    'cost_usd': float(article.analyzer_cost_usd or 0),
                    'duration_ms': article.analyzer_duration_ms or 0,
                    'analyzed_at': article.analyzed_at.isoformat() if article.analyzed_at else None
                }
            }
        elif article.analyzer_status == 'failed':
            response_data = {
                'status': 'failed',
                'error': article.analyzer_error_message
            }
        else:
            response_data = {
                'status': article.analyzer_status
            }
        
        response = JsonResponse(response_data)
        response["Access-Control-Allow-Origin"] = "*"
        return response
        
    except Article.DoesNotExist:
        response = JsonResponse({'error': 'Article not found'}, status=404)
        response["Access-Control-Allow-Origin"] = "*"
        return response
```

---

## 6. Implementation Timeline

### Week 1: Foundation
- [ ] Create analyzer app structure
- [ ] Implement core models (ArticleAnalysis, Entity, Event)
- [ ] Add analyzer fields to Article model
- [ ] Create database migrations

### Week 2: Core Service
- [ ] Implement AnalyzerService class
- [ ] Create prompt templates
- [ ] Build linguistic analysis stage
- [ ] Build entity extraction stage

### Week 3: Advanced Stages
- [ ] Implement event extraction
- [ ] Build topic classification
- [ ] Add region detection
- [ ] Create entity/event resolution algorithms

### Week 4: Integration
- [ ] Implement Celery tasks
- [ ] Create API endpoints
- [ ] Add to aiproviders operation types
- [ ] Testing and optimization

---

## 7. Cost & Performance Targets

### 7.1 Cost Breakdown (Target: ≤ $0.0003/article)

| Stage | Tool | Estimated Cost |
|-------|------|----------------|
| Linguistic | fastText + textstat + GPT style | $0.00005 |
| Entity Extraction | spaCy (free) | $0.00000 |
| Event Extraction | GPT-4o-mini | $0.00008 |
| Topic Classification | GPT-4o-mini | $0.00010 |
| Region Detection | GPT-4o-mini | $0.00005 |
| **Total** | | **$0.00028** |

### 7.2 Performance Metrics
- **Processing Time**: < 15 seconds per article
- **Success Rate**: > 95%
- **Entity Accuracy**: > 90% (spot checks)
- **Topic Accuracy**: > 95% (existing taxonomy)

---

## 8. Quality Assurance & Monitoring

### 8.1 Validation Metrics
- Entity deduplication ratio: `COUNT(DISTINCT canonical_name) / COUNT(*)` > 0.95
- Event singleton share: `SUM(article_count=1) / COUNT(*)` < 40%
- Topic assignment rate: > 95% articles get primary_topic
- Region assignment rate: > 90% articles get primary_region

### 8.2 Monitoring Dashboards
- Cost tracking per operation (reuse AIProviderUsage)
- Processing success rates by stage
- Entity/event catalog growth rates
- Article analysis completion rates

---

This implementation plan provides a comprehensive roadmap for building the analyzer service that integrates seamlessly with your existing DailyBrief architecture while delivering the enhanced content classification and entity extraction capabilities needed for advanced news aggregation features. 