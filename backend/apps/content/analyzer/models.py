"""
Article Analyzer Models for DailyBrief.

Domain-specific models for content analysis including entities, events, and processing metadata.
Does not duplicate existing Article classification fields but enhances them.
"""
import uuid
import hashlib
from typing import List, Optional, Dict, Any
from decimal import Decimal

from django.db import models
from django.utils import timezone
from pgvector.django import VectorField, CosineDistance


class AnalyzerStatus(models.TextChoices):
    """Analysis processing status choices."""
    PENDING = 'pending', 'Pending Analysis'
    PROCESSING = 'processing', 'Processing Analysis'
    COMPLETED = 'completed', 'Analysis Completed'
    FAILED = 'failed', 'Analysis Failed'


class Entity(models.Model):
    """
    Master entity catalog with deduplication and semantic search.
    
    Stores canonical entities extracted from articles with alias resolution
    and vector embeddings for similarity matching.
    """
    # Core identification
    id = models.AutoField(primary_key=True)
    public_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    canonical_name = models.CharField(
        max_length=255, 
        unique=True, 
        help_text="Canonicalized name (lowercase, normalized)"
    )
    display_name = models.CharField(max_length=255, help_text="Human-readable display name")
    
    # Entity classification
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
        ],
        help_text="Entity type classification"
    )
    
    # External knowledge base linking
    wikidata_id = models.CharField(max_length=50, null=True, blank=True)
    
    # Vector embedding for semantic deduplication (1536-dim OpenAI)
    embedding = VectorField(
        dimensions=1536, 
        null=True, 
        blank=True,
        help_text="1536-dimensional OpenAI vector for semantic similarity"
    )
    
    # Usage tracking
    article_count = models.IntegerField(
        default=0, 
        help_text="Number of articles mentioning this entity"
    )
    first_seen_at = models.DateTimeField(auto_now_add=True)
    last_seen_at = models.DateTimeField(auto_now=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'analyzer_entity'
        indexes = [
            models.Index(fields=['canonical_name']),
            models.Index(fields=['entity_type']),
            models.Index(fields=['article_count']),
            models.Index(fields=['last_seen_at']),
        ]
        verbose_name = 'Entity'
        verbose_name_plural = 'Entities'
    
    def __str__(self):
        return f"{self.display_name} ({self.entity_type})"
    
    @classmethod
    def canonicalize_name(cls, name: str) -> str:
        """Canonicalize entity name for deduplication."""
        import re
        
        # Convert to lowercase
        canonical = name.lower().strip()
        # Remove special characters except $ for tickers and basic punctuation
        canonical = re.sub(r"[^\w\s$.-]", "", canonical)
        # Collapse multiple spaces
        canonical = re.sub(r"\s+", " ", canonical)
        
        return canonical
    
    @classmethod
    def find_similar(cls, name: str, entity_type: str, threshold: float = 0.10) -> Optional['Entity']:
        """
        Find similar entities using vector similarity.
        
        Args:
            name: Entity name to search for
            entity_type: Entity type for filtering
            threshold: Similarity threshold (lower = more similar)
            
        Returns:
            Most similar entity if found, None otherwise
        """
        if not name:
            return None
            
        # First try exact canonical match
        canonical = cls.canonicalize_name(name)
        try:
            return cls.objects.get(canonical_name=canonical)
        except cls.DoesNotExist:
            pass
        
        # Try alias match
        try:
            alias = EntityAlias.objects.select_related('entity').get(alias=canonical)
            return alias.entity
        except EntityAlias.DoesNotExist:
            pass
        
        # Vector similarity search (if we have embeddings)
        # This will be implemented when we add embedding generation
        return None


class EntityAlias(models.Model):
    """
    Alternative names and spellings for entities.
    
    Stores aliases, abbreviations, and alternative spellings to improve
    entity resolution and deduplication.
    """
    entity = models.ForeignKey(
        Entity, 
        on_delete=models.CASCADE, 
        related_name='aliases'
    )
    alias = models.CharField(
        max_length=255, 
        unique=True,
        help_text="Alternative name or spelling"
    )
    
    # Metadata
    alias_type = models.CharField(
        max_length=20,
        choices=[
            ('abbreviation', 'Abbreviation'),
            ('acronym', 'Acronym'),
            ('ticker', 'Stock Ticker'),
            ('nickname', 'Nickname'),
            ('spelling', 'Alternative Spelling'),
            ('translation', 'Translation'),
            ('other', 'Other'),
        ],
        default='other'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'analyzer_entity_alias'
        verbose_name_plural = 'Entity aliases'
    
    def __str__(self):
        return f"{self.alias} → {self.entity.display_name}"


class Event(models.Model):
    """
    Story events for clustering and timeline features.
    
    Represents major events or stories that span multiple articles,
    enabling story clustering and timeline visualization.
    """
    # Core identification
    id = models.AutoField(primary_key=True)
    public_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    title = models.CharField(max_length=255, help_text="Event title")
    abstract = models.TextField(help_text="AI-generated event summary")
    facts = models.JSONField(
        default=list, 
        help_text="Key facts extracted from related articles"
    )
    
    # Event classification
    event_type = models.CharField(
        max_length=20,
        choices=[
            ('product_launch', 'Product Launch'),
            ('earnings', 'Earnings/Financial'),
            ('policy_change', 'Policy Change'),
            ('incident', 'Incident/Crisis'),
            ('meeting', 'Meeting/Conference'),
            ('acquisition', 'Acquisition/Merger'),
            ('partnership', 'Partnership'),
            ('research', 'Research/Discovery'),
            ('legal', 'Legal/Court Decision'),
            ('election', 'Election/Political'),
            ('conflict', 'Conflict/War'),
            ('natural_disaster', 'Natural Disaster'),
            ('cultural', 'Cultural/Social'),
            ('sports', 'Sports Event'),
            ('other', 'Other'),
        ],
        default='other',
        help_text="Type of event for categorization"
    )
    
    # Deduplication and clustering
    event_hash = models.CharField(
        max_length=64, 
        unique=True, 
        help_text="SHA-256 hash for exact deduplication"
    )
    centroid_embed = VectorField(
        dimensions=1536, 
        help_text="Centroid embedding for event similarity clustering"
    )
    
    # Timeline and tracking
    first_seen_at = models.DateTimeField(help_text="When this event was first detected")
    last_seen_at = models.DateTimeField(help_text="Most recent article about this event")
    article_count = models.IntegerField(default=1, help_text="Number of articles about this event")
    
    # Integration with existing StoryGroup
    story_group = models.OneToOneField(
        'articles.StoryGroup',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='analyzer_event',
        help_text="Link to existing story group if applicable"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'analyzer_event'
        indexes = [
            models.Index(fields=['event_hash']),
            models.Index(fields=['event_type']),
            models.Index(fields=['last_seen_at']),
            models.Index(fields=['article_count']),
            models.Index(fields=['first_seen_at']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.article_count} articles)"
    
    @classmethod
    def generate_event_hash(cls, headline: str, facts: List[str]) -> str:
        """Generate deterministic hash for event deduplication."""
        # Use headline + first two facts for hash generation
        hash_input = headline.lower()
        if facts:
            hash_input += facts[0].lower() if len(facts) > 0 else ""
            hash_input += facts[1].lower() if len(facts) > 1 else ""
        
        return hashlib.sha256(hash_input.encode()).hexdigest()[:20]
    
    def update_centroid(self, new_embedding: List[float]):
        """Update centroid embedding with new article embedding."""
        if not self.centroid_embed:
            self.centroid_embed = new_embedding
        else:
            # Running average: new_centroid = (old * count + new) / (count + 1)
            current_centroid = list(self.centroid_embed)
            updated_centroid = [
                (old_val * self.article_count + new_val) / (self.article_count + 1)
                for old_val, new_val in zip(current_centroid, new_embedding)
            ]
            self.centroid_embed = updated_centroid
        
        self.article_count += 1
        self.last_seen_at = timezone.now()
        self.save()


class ArticleAnalysis(models.Model):
    """
    Processing metadata and analyzer-specific results.
    
    Stores analysis processing information and results that don't 
    belong in the main Article model. Classification results are
    stored in existing Article fields (topics, regions, language).
    """
    # Primary key and relationships
    id = models.AutoField(primary_key=True)
    public_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    article = models.OneToOneField(
        'articles.Article',
        on_delete=models.CASCADE,
        related_name='analyzer_result'
    )
    
    # Processing metadata
    analyzer_version = models.CharField(max_length=10, default='1.0')
    tokens_input = models.IntegerField(default=0, help_text="Total input tokens used")
    tokens_output = models.IntegerField(default=0, help_text="Total output tokens generated")
    processing_time_ms = models.IntegerField(default=0, help_text="Total processing time in milliseconds")
    cost_usd = models.DecimalField(
        max_digits=8, 
        decimal_places=6, 
        default=0,
        help_text="Total cost in USD"
    )
    ai_model_used = models.CharField(max_length=50, default='gpt-4o-mini')
    
    # Analysis confidence scores
    language_confidence = models.FloatField(
        default=0.0, 
        help_text="Confidence score for language detection"
    )
    primary_topic_confidence = models.FloatField(
        default=0.0, 
        help_text="Confidence score for primary topic classification"
    )
    primary_region_confidence = models.FloatField(
        default=0.0, 
        help_text="Confidence score for primary region detection"
    )
    
    # Analyzer-specific results (non-duplicated fields only)
    style_tone = models.CharField(
        max_length=20,
        choices=[
            ('factual', 'Factual'),
            ('opinion', 'Opinion'),
            ('narrative', 'Narrative'),
            ('analytical', 'Analytical'),
            ('satirical', 'Satirical'),
            ('sensational', 'Sensational'),
        ],
        null=True,
        blank=True,
        help_text="Article style and tone classification"
    )
    # Note: readability, reading_time, word_count, sentiment, keywords, entities 
    # are stored in existing Article fields to avoid duplication
    
    # Pipeline tracking
    stages_completed = models.JSONField(
        default=list, 
        help_text="List of completed analysis stages"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'analyzer_article_analysis'
        indexes = [
            models.Index(fields=['article']),
            models.Index(fields=['analyzer_version']),
            models.Index(fields=['created_at']),
        ]
        verbose_name = 'Article Analysis'
        verbose_name_plural = 'Article Analyses'
    
    def __str__(self):
        return f"Analysis for: {self.article.title[:50]}..."
    
    def mark_stage_completed(self, stage_name: str):
        """Mark an analysis stage as completed."""
        if not self.stages_completed:
            self.stages_completed = []
        
        if stage_name not in self.stages_completed:
            self.stages_completed.append(stage_name)
            self.save(update_fields=['stages_completed'])


# Link Tables
class ArticleEntity(models.Model):
    """Links articles to extracted entities."""
    article = models.ForeignKey(
        'articles.Article', 
        on_delete=models.CASCADE,
        related_name='article_entities'
    )
    entity = models.ForeignKey(
        Entity, 
        on_delete=models.CASCADE,
        related_name='entity_articles'
    )
    confidence = models.FloatField(
        default=1.0, 
        help_text="Confidence score for entity extraction"
    )
    mention_count = models.IntegerField(
        default=1, 
        help_text="Number of times entity is mentioned in article"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('article', 'entity')
        db_table = 'analyzer_article_entity'
        indexes = [
            models.Index(fields=['article']),
            models.Index(fields=['entity']),
            models.Index(fields=['confidence']),
        ]
    
    def __str__(self):
        return f"{self.article.title[:30]}... → {self.entity.display_name}"


class ArticleEvent(models.Model):
    """Links articles to their main event (one-to-one relationship)."""
    article = models.OneToOneField(
        'articles.Article', 
        on_delete=models.CASCADE, 
        primary_key=True,
        related_name='main_event'
    )
    event = models.ForeignKey(
        Event, 
        on_delete=models.CASCADE,
        related_name='articles'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'analyzer_article_event'
    
    def __str__(self):
        return f"{self.article.title[:30]}... → {self.event.title}"


class EventEntity(models.Model):
    """Links events to their associated entities."""
    event = models.ForeignKey(
        Event, 
        on_delete=models.CASCADE,
        related_name='event_entities'
    )
    entity = models.ForeignKey(
        Entity, 
        on_delete=models.CASCADE,
        related_name='entity_events'
    )
    relevance_score = models.FloatField(
        default=1.0, 
        help_text="Relevance of entity to event"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('event', 'entity')
        db_table = 'analyzer_event_entity'
        indexes = [
            models.Index(fields=['event']),
            models.Index(fields=['entity']),
            models.Index(fields=['relevance_score']),
        ]
    
    def __str__(self):
        return f"{self.event.title} ↔ {self.entity.display_name}"


class AnalyzerRequest(models.Model):
    """
    Tracks analyzer processing requests and pipeline progress.
    
    Used for monitoring, retrying failed requests, and performance analytics.
    Follows the same pattern as SummarizationRequest.
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
    status = models.CharField(max_length=30, choices=[
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
    current_stage = models.CharField(max_length=30, blank=True)
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
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['article', 'status']),
            models.Index(fields=['current_stage']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Analyzer request for: {self.article.title[:30]}... ({self.status})"
    
    def mark_stage_completed(self, stage_name: str):
        """Mark a pipeline stage as completed."""
        if not self.stages_completed:
            self.stages_completed = []
        
        if stage_name not in self.stages_completed:
            self.stages_completed.append(stage_name)
            self.save(update_fields=['stages_completed'])
    
    def get_pipeline_duration(self) -> Optional[int]:
        """Get total pipeline duration in milliseconds."""
        if self.pipeline_start_time and self.pipeline_end_time:
            delta = self.pipeline_end_time - self.pipeline_start_time
            return int(delta.total_seconds() * 1000)
        return None
    
    @property
    def is_in_progress(self) -> bool:
        """Check if request is currently being processed."""
        return self.status in [
            'linguistic_processing', 'entity_processing', 'event_processing',
            'topic_processing', 'region_processing'
        ]


class AnalyzerMetrics(models.Model):
    """
    Aggregated metrics for analyzer performance monitoring.
    
    Updated periodically to track cost, performance, and quality trends.
    """
    # Time period
    date = models.DateField(unique=True, help_text="Date for aggregated metrics")
    
    # Volume metrics
    articles_processed = models.IntegerField(default=0)
    articles_failed = models.IntegerField(default=0)
    success_rate = models.FloatField(default=0.0, help_text="Success rate percentage")
    
    # Cost metrics
    total_cost_usd = models.DecimalField(max_digits=10, decimal_places=6, default=0)
    avg_cost_per_article = models.DecimalField(max_digits=8, decimal_places=6, default=0)
    
    # Performance metrics
    avg_duration_ms = models.IntegerField(default=0)
    avg_tokens_used = models.IntegerField(default=0)
    
    # Entity metrics
    new_entities_created = models.IntegerField(default=0)
    entity_deduplication_rate = models.FloatField(default=0.0)
    
    # Event metrics
    new_events_created = models.IntegerField(default=0)
    event_clustering_rate = models.FloatField(default=0.0)
    
    # Classification metrics
    topic_assignment_rate = models.FloatField(default=0.0)
    region_assignment_rate = models.FloatField(default=0.0)
    
    # Pipeline stage metrics
    linguistic_failures = models.IntegerField(default=0)
    entity_failures = models.IntegerField(default=0)
    event_failures = models.IntegerField(default=0)
    topic_failures = models.IntegerField(default=0)
    region_failures = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'analyzer_metrics'
        ordering = ['-date']
    
    def __str__(self):
        return f"Analyzer metrics for {self.date}" 