# Analyzer Service Architecture

> **Technical architecture and design patterns for the AI Content Analysis Service**

This document provides a comprehensive overview of the analyzer service architecture, including the 8-stage processing pipeline, data models, deduplication strategies, and integration patterns.

## 📖 Table of Contents

- [System Overview](#system-overview)
- [8-Stage Processing Pipeline](#8-stage-processing-pipeline)
- [Data Architecture](#data-architecture)
- [Deduplication Strategies](#deduplication-strategies)
- [AI Model Integration](#ai-model-integration)
- [Performance & Scalability](#performance--scalability)

## System Overview

### Pipeline Position

The Analyzer Service operates as **Stage 5** in the DailyBrief content enrichment pipeline:

```
Content Enrichment Pipeline:
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Fetcher   │───►│  Processor  │───►│   Quality   │───►│ Summariser  │───►│  Analyzer   │
│  (Step 1)   │    │  (Step 2)   │    │  (Step 3)   │    │  (Step 4)   │    │  (Step 5)   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                                                                  │                    │
                                                          ArticleSummary       ArticleAnalysis
                                                          + Embedding          + Events + Entities
```

### Input Requirements

**Prerequisites:**
- Article must have `summarization_status = 'completed'`
- `ArticleSummary` record with structured data
- Optional: Article embedding for event clustering

**Input Data Structure:**
```python
{
    'headline': 'Article headline',
    'abstract': 'Summary abstract',
    'facts': ['[FACT] Key fact 1', '[STAT] Statistical data'],
    'opinions': ['[OPINION] Expert opinion'],
    'impact': ['[IMPACT] Potential consequences'],
    'embedding': [0.01, -0.02, ...]  # 1536-dim OpenAI embedding
}
```

### Output Artifacts

**Database Records Created:**
- `ArticleAnalysis` - Linguistic and classification metadata
- `Entity` records - Canonical entities with embeddings
- `Event` records - Clustered events with metadata
- `ArticleEntity` links - Article-entity relationships
- `ArticleEvent` links - Article-event relationships with relevance scores

## 8-Stage Processing Pipeline

### Stage 1: Language Detection

**Purpose:** Identify article language for downstream processing decisions

**Implementation:**
```python
def _stage_1_language_detection(self, article: Article, enhanced_content: str):
    # Primary: fastText language detection
    try:
        import fasttext
        model = fasttext.load_model('lid.176.bin')
        text = f"{enhanced_content[:1000]}"  # First 1000 chars
        predictions = model.predict(text, k=1)
        language = predictions[0][0].replace('__label__', '')
        confidence = float(predictions[1][0])
    except Exception:
        # Fallback: langdetect
        from langdetect import detect
        language = detect(enhanced_content[:1000])
        confidence = 0.8
    
    return {
        'language_detected': language,
        'language_confidence': confidence
    }
```

**Cost:** Free (open-source tools)

### Stage 2: Linguistic Analysis

**Purpose:** Extract readability, style, and structural metadata using optimized content strategies

**Implementation:**
```python
def _stage_2_linguistic_analysis(self, article: Article, content: str, analysis_record: ArticleAnalysis):
    # Get full content for accurate metrics (FREE operations)
    full_content = self._get_full_content_for_linguistic_analysis(article)
    
    # Readability scoring using full content (FREE)
    import textstat
    readability_flesch = textstat.flesch_reading_ease(full_content)
    word_count = textstat.lexicon_count(full_content)
    reading_time_minutes = word_count / 225.0  # 225 WPM average
    
    # Get truncated content for AI analysis (cost optimization)
    truncated_content = self._get_truncated_content_for_analysis(article, max_chars=5000)
    
    # Sentiment analysis using spaCy (FREE)
    sentiment_score = None
    if nlp:
        doc = nlp(truncated_content)
        sentiment_score = sum(token.sentiment for token in doc) / len(doc)
    
    # Style/tone classification (GPT-4o-mini)
    style_result = self._classify_style_tone(truncated_content)
    
    return {
        'readability_score': readability_flesch,
        'word_count': word_count,
        'read_time_minutes': reading_time_minutes,
        'sentiment_score': sentiment_score,
        'style_tone': style_result['style_tone']
    }

def _get_full_content_for_linguistic_analysis(self, article: Article) -> str:
    """Get complete content using content assembler for accurate metrics"""
    from apps.content.summariser.content_assembler import get_markdown_assembler
    
    content_blocks = getattr(article, 'content_blocks', None)
    if not content_blocks:
        return article.content if article.content else article.title
    
    assembler = get_markdown_assembler(
        max_chars=50000,  # High limit for full content
        use_intelligent_summarization=False,
        summarization_mode="custom"
    )
    
    return assembler.assemble_content(content_blocks, article.title)

def _get_truncated_content_for_analysis(self, article: Article, max_chars: int = 5000) -> str:
    """Get intelligently truncated content for AI analysis (cost optimization)"""
    from apps.content.summariser.content_assembler import get_markdown_assembler
    
    content_blocks = getattr(article, 'content_blocks', None)
    if not content_blocks:
        content = article.content if article.content else article.title
        return content[:max_chars] if len(content) > max_chars else content
    
    assembler = get_markdown_assembler(
        max_chars=max_chars,
        use_intelligent_summarization=True,
        summarization_mode="hybrid"  # Best balance of quality and structure
    )
    
    return assembler.assemble_content(content_blocks, article.title)
```

**Key Features:**
- **Dual Content Strategy**: Full content for accurate free metrics, truncated content for cost-optimized AI analysis
- **Content Assembler Integration**: Uses summariser service's intelligent content assembly
- **Hybrid Summarization**: Preserves document structure while optimizing for cost
- **Robust Fallbacks**: Multiple fallback mechanisms for missing content blocks

**Cost:** ~$0.000005 (style/tone classification only, reduced from using full content)

### Stage 3: Entity Extraction

**Purpose:** Identify and canonicalize named entities

**Implementation:**
```python
def _stage_3_entity_extraction(self, article: Article, enhanced_content: str):
    # spaCy NER
    import spacy
    nlp = spacy.load('en_core_web_lg')
    doc = nlp(enhanced_content)
    
    raw_entities = []
    for ent in doc.ents:
        if ent.label_ in SUPPORTED_ENTITY_TYPES:
            raw_entities.append({
                'text': ent.text,
                'label': ent.label_,
                'start': ent.start_char,
                'end': ent.end_char
            })
    
    # Ticker symbol extraction
    import re
    tickers = re.findall(r'\$[A-Z]{2,6}', enhanced_content)
    for ticker in tickers:
        raw_entities.append({
            'text': ticker,
            'label': 'FINANCIAL_ASSET'
        })
    
    # Entity resolution
    entity_ids = []
    for raw_entity in raw_entities:
        entity_id = self._resolve_entity(
            raw_entity['text'], 
            raw_entity['label']
        )
        entity_ids.append(entity_id)
    
    return {'entity_ids': entity_ids}
```

**Cost:** Free (spaCy processing)

### Stage 4: Event Detection

**Purpose:** Extract events using advanced reasoning prompts

**Implementation:**
```python
def _stage_4_event_detection(self, article: Article, enhanced_content: str):
    # Use reasoning-optimized prompt
    prompt = AnalyzerPrompts.event_detection_prompt(
        title=article.title,
        content=enhanced_content,
        published_at=article.published_at
    )
    
    # GPT-4.1-mini with reasoning framework
    response = self.ai_service.complete_text(
        prompt=prompt,
        operation='event_detection',
        temperature=0.1,
        max_tokens=600
    )
    
    # Parse structured JSON response
    events_data = json.loads(response.content)
    
    return {
        'events': events_data.get('events', []),
        'cost_usd': self._calculate_cost(response.usage)
    }
```

**Key Features:**
- Two-level event strategy (broad + specific)
- Relevance scoring rubric (≥0.7 threshold)
- Event naming protocol (nouns vs actions)
- Self-correction instructions

**Cost:** ~$0.000040 per article

### Stage 5: Topic Classification

**Purpose:** Assign primary and secondary topics from existing taxonomy

**Implementation:**
```python
def _stage_5_topic_classification(self, article: Article, enhanced_content: str):
    prompt = AnalyzerPrompts.topic_classification_prompt(
        headline=article.title,
        abstract=enhanced_content[:500]  # Truncate for cost
    )
    
    response = self.ai_service.complete_text(
        prompt=prompt,
        operation='topic_classification',
        temperature=0.0,
        max_tokens=100
    )
    
    topic_data = json.loads(response.content)
    
    return {
        'primary_topic': topic_data.get('primary_topic'),
        'secondary_topics': topic_data.get('secondary_topics', []),
        'cost_usd': self._calculate_cost(response.usage)
    }
```

**Cost:** ~$0.000020 per article

### Stage 6: Region Classification

**Purpose:** Identify geographic focus and all mentioned regions

**Implementation:**
```python
def _stage_6_region_classification(self, article: Article, enhanced_content: str, entity_ids: List[int]):
    # Get entity names for context
    entities = Entity.objects.filter(id__in=entity_ids)
    entity_names = [e.display_name for e in entities]
    
    prompt = AnalyzerPrompts.region_detection_prompt(
        headline=article.title,
        abstract=enhanced_content[:500],
        entities=entity_names[:5]  # Top 5 entities
    )
    
    response = self.ai_service.complete_text(
        prompt=prompt,
        operation='region_classification',
        temperature=0.0,
        max_tokens=100
    )
    
    region_data = json.loads(response.content)
    
    return {
        'primary_region': region_data.get('primary_region', 'universal'),
        'all_regions': region_data.get('all_regions', []),
        'cost_usd': self._calculate_cost(response.usage)
    }
```

**Cost:** ~$0.000010 per article

### Stage 7: Event Resolution

**Purpose:** Deduplicate and cluster events using embeddings

**Implementation:**
```python
def _stage_7_event_resolution(self, extracted_events: List[Dict], entity_ids: List[int], article: Article):
    event_ids = []
    
    for event_data in extracted_events:
        # Generate event hash for fast deduplication
        event_hash = self._generate_event_hash(event_data)
        
        # Check for existing event by hash
        existing_event = Event.objects.filter(event_hash=event_hash).first()
        
        if existing_event:
            event_id = existing_event.id
        else:
            # Embedding-based similarity search
            event_embedding = self._generate_event_embedding(event_data)
            similar_events = self._find_similar_events(event_embedding)
            
            if similar_events:
                # Use most similar event
                event_id = similar_events[0].id
            else:
                # Create new event
                event_id = self._create_new_event(event_data, event_hash, event_embedding)
        
        event_ids.append(event_id)
    
    return event_ids
```

**Features:**
- SHA-256 hash for exact deduplication
- Vector similarity for semantic clustering
- Entity overlap validation
- Centroid embedding updates

**Cost:** ~$0.000005 (embedding generation)

### Stage 8: Persistence

**Purpose:** Store all analysis results and create relationships

**Implementation:**
```python
def _stage_8_persistence(self, article: Article, analysis_results: Dict):
    # Create ArticleAnalysis record
    analysis = ArticleAnalysis.objects.create(
        article=article,
        language_detected=analysis_results['language'],
        readability_flesch=analysis_results['readability'],
        reading_time_sec=analysis_results['reading_time'],
        style_tone=analysis_results['style_tone'],
        primary_topic=analysis_results['primary_topic'],
        primary_region=analysis_results['primary_region'],
        # ... other fields
    )
    
    # Create entity relationships
    for entity_id in analysis_results['entity_ids']:
        ArticleEntity.objects.create(
            article=article,
            entity_id=entity_id
        )
    
    # Create event relationships with relevance scores
    for i, event_id in enumerate(analysis_results['event_ids']):
        event_data = analysis_results['events'][i]
        ArticleEvent.objects.create(
            article=article,
            event_id=event_id,
            relevance_score=event_data['relevance_score'],
            is_primary=event_data['is_primary']
        )
    
    # Update article status
    article.analyzer_status = AnalyzerStatus.COMPLETED
    article.analyzed_at = timezone.now()
    article.save()
```

**Cost:** Free (database operations)

## Data Architecture

### Core Models Relationships

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│     Article     │────►│ ArticleAnalysis │     │   AnalyzerRequest│
│                 │     │                 │     │                 │
│ - id            │     │ - language      │     │ - status        │
│ - title         │     │ - readability   │     │ - stages        │
│ - analyzer_status│     │ - style_tone    │     │ - cost_tracking │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         │                                                │
         ▼                                                ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  ArticleEntity  │────►│     Entity      │     │  ArticleEvent   │
│                 │     │                 │     │                 │
│ - article_id    │     │ - canonical_name│     │ - article_id    │
│ - entity_id     │     │ - entity_type   │     │ - event_id      │
│ - confidence    │     │ - embedding     │     │ - relevance_score│
└─────────────────┘     │ - wikidata_id   │     │ - is_primary    │
                        └─────────────────┘     └─────────────────┘
                                 │                        │
                                 ▼                        ▼
                        ┌─────────────────┐     ┌─────────────────┐
                        │   EntityAlias   │     │      Event      │
                        │                 │     │                 │
                        │ - entity_id     │     │ - title         │
                        │ - alias         │     │ - abstract      │
                        └─────────────────┘     │ - event_type    │
                                                │ - event_hash    │
                                                │ - embedding     │
                                                │ - article_count │
                                                └─────────────────┘
```

### Entity Resolution Architecture

**Canonical Entity Management:**
```python
class Entity(models.Model):
    # Core identification
    canonical_name = models.CharField(max_length=255, unique=True)
    display_name = models.CharField(max_length=255)
    entity_type = models.CharField(max_length=20, choices=ENTITY_TYPES)
    
    # External linking
    wikidata_id = models.CharField(max_length=50, null=True, blank=True)
    
    # Deduplication
    embedding = VectorField(dimensions=384)  # MiniLM embedding
    
    # Metadata
    article_count = models.IntegerField(default=0)
    first_seen_at = models.DateTimeField(auto_now_add=True)
    last_seen_at = models.DateTimeField(auto_now=True)
```

**Alias Management:**
```python
class EntityAlias(models.Model):
    entity = models.ForeignKey(Entity, on_delete=models.CASCADE, related_name='aliases')
    alias = models.CharField(max_length=255, unique=True)
```

### Event Clustering Architecture

**Event Model:**
```python
class Event(models.Model):
    # Core event data
    title = models.CharField(max_length=255)
    abstract = models.TextField()
    facts = models.JSONField(default=list)
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    
    # Deduplication
    event_hash = models.CharField(max_length=64, unique=True)
    embedding = VectorField(dimensions=1536)  # OpenAI embedding
    
    # Clustering metadata
    article_count = models.IntegerField(default=1)
    first_seen_at = models.DateTimeField()
    last_seen_at = models.DateTimeField()
```

**Event-Article Relationships:**
```python
class ArticleEvent(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    
    # Quality metrics
    relevance_score = models.FloatField()  # 0.7-1.0 range
    is_primary = models.BooleanField(default=False)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
```

## Deduplication Strategies

### Entity Deduplication

**Three-Phase Resolution:**

1. **Exact Canonical Match**
   ```python
   canonical = canonicalize_name(raw_name)  # lowercase, strip accents
   entity = Entity.objects.filter(canonical_name=canonical).first()
   ```

2. **Alias Lookup**
   ```python
   alias_match = EntityAlias.objects.filter(alias=canonical).first()
   if alias_match:
       return alias_match.entity_id
   ```

3. **Embedding Similarity**
   ```python
   embedding = generate_entity_embedding(canonical)
   similar = Entity.objects.order_by(
       embedding.cosine_distance(embedding)
   ).first()
   
   if similar and cosine_distance < 0.10:
       EntityAlias.objects.create(entity=similar, alias=canonical)
       return similar.id
   ```

### Event Deduplication

**Two-Phase Resolution:**

1. **Hash-Based Exact Match**
   ```python
   event_hash = sha256(f"{title}:{facts[0]}:{facts[1]}".encode()).hexdigest()
   existing = Event.objects.filter(event_hash=event_hash).first()
   ```

2. **Embedding Similarity with Entity Overlap**
   ```python
   # Vector similarity
   similar_events = Event.objects.order_by(
       embedding.cosine_distance(new_embedding)
   )[:5]
   
   # Validate with entity overlap
   for candidate in similar_events:
       if (cosine_distance < 0.18 and 
           shared_entities_count >= 2):
           return candidate.id
   ```

### Force Re-Analysis Cleanup

**Complete Event Cleanup:**
```python
def _cleanup_article_events(self, article: Article):
    # Remove all existing relationships
    existing_relationships = ArticleEvent.objects.filter(article=article)
    event_ids_to_check = list(existing_relationships.values_list('event_id', flat=True))
    existing_relationships.delete()
    
    # Find and delete orphaned events
    orphaned_events = Event.objects.filter(
        id__in=event_ids_to_check,
        articleevent__isnull=True  # No remaining relationships
    )
    orphaned_count = orphaned_events.count()
    orphaned_events.delete()
    
    logger.info(f"Cleaned up {orphaned_count} orphaned events")
```

## AI Model Integration

### Model Configuration

**Current Setup:**
```python
# Event detection: GPT-4.1-mini (primary)
'event_detection': {
    'operation': 'event_detection',
    'temperature': 0.1,
    'max_tokens': 600,
    'model_preference': 'gpt-4.1-mini'
}

# Topic/Region classification: GPT-4o-mini (cost-optimized)
'topic_classification': {
    'operation': 'topic_classification',
    'temperature': 0.0,
    'max_tokens': 100,
    'model_preference': 'gpt-4o-mini'
}
```

### Reasoning Model Support

**Advanced Model Compatibility:**
```python
# Support for reasoning models (o3-mini, o1-mini, etc.)
def _get_model_params(self, model_name: str, base_params: Dict) -> Dict:
    reasoning_models = ['o3', 'o3-mini', 'o1-mini', 'o1-preview', 'o4-mini']
    
    if model_name.lower() in reasoning_models:
        # Remove unsupported parameters
        params = base_params.copy()
        params.pop('temperature', None)
        params.pop('max_tokens', None)
        return params
    
    return base_params
```

### Prompt Engineering Framework

**Reasoning-Optimized Prompts:**
```python
def event_detection_prompt(title: str, content: str) -> str:
    return f"""# REASONING TASK: Event Extraction & Analysis

You are an expert news analyst using advanced reasoning to extract and categorize events.

## REASONING PROCESS

### STEP 1: Article Comprehension
- What is the ONE core event or story this article covers?
- What broader ongoing story does this belong to?

### STEP 2: Event Identification Strategy
Extract events at TWO levels:
1. **BROAD ONGOING EVENT**: Major ongoing story/situation
2. **SPECIFIC DEVELOPMENTS**: Recent specific events

### STEP 3: Event Naming Protocol
**CRITICAL RULE:** Always name events as NOUNS, never as ACTIONS

### STEP 4: Relevance Scoring Rubric
**1.0 - Central/Primary Event**: Main reason article was written
**0.9 - Highly Relevant Context**: Major ongoing story
**0.7 - Relevant Background**: Important context

### STEP 5: Self-Correction Check
Verify all events follow naming protocol and relevance thresholds

## INPUT ARTICLE
**Title:** {title}
**Content:** {content}

Return STRICT JSON with events array."""
```

## Performance & Scalability

### Processing Metrics

**Current Performance:**
- **Throughput**: 10-25 seconds per article
- **Success Rate**: 100% on tested articles
- **Cost Efficiency**: $0.000080 per article (58% under budget)
- **Memory Usage**: ~50MB per concurrent analysis

### Scalability Considerations

**Horizontal Scaling:**
```python
# Celery task distribution
@shared_task(bind=True, max_retries=3)
def analyze_article_pipeline(self, article_id: int):
    # Stateless processing allows easy horizontal scaling
    service = AnalyzerService()
    result = service.analyze_article(article_id)
    return result
```

**Database Optimization:**
```sql
-- Key indexes for performance
CREATE INDEX idx_article_analyzer_status ON articles(analyzer_status);
CREATE INDEX idx_entity_canonical ON entities(canonical_name);
CREATE INDEX idx_event_hash ON events(event_hash);
CREATE INDEX idx_article_event_relevance ON article_events(relevance_score DESC);

-- Vector indexes for similarity search
CREATE INDEX idx_entity_embedding ON entities USING hnsw (embedding vector_cosine_ops);
CREATE INDEX idx_event_embedding ON events USING hnsw (embedding vector_cosine_ops);
```

### Cost Optimization Strategies

**Token Efficiency:**
- Truncate content to 512 tokens for classification tasks
- Use headline + abstract for topic/region detection
- Cache embeddings to avoid regeneration
- Batch entity resolution operations

**Model Selection:**
- GPT-4.1-mini for complex reasoning (events)
- GPT-4o-mini for simple classification (topics, regions)
- Open-source tools for linguistic analysis (free)
- Strategic fallbacks for cost control 