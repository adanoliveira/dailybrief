"""
Content Summarization Models for DailyBrief.

Domain-specific models for the 4-stage summarization pipeline:
RBC → Skeleton Summary → Critic Review → Repair (if needed) → Embedding
"""
import uuid
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from decimal import Decimal

from django.db import models
from django.utils import timezone
from pgvector.django import VectorField, CosineDistance


@dataclass
class SummarizationResult:
    """
    Result of complete summarization pipeline - pure domain model.
    
    Contains all pipeline outputs and performance metrics.
    """
    success: bool
    article_id: int
    
    # Pipeline outputs
    rbc_bullets: List[str] = None
    headline: str = ""
    abstract: str = ""
<<<<<<< HEAD
=======
    longer_abstract: str = ""
>>>>>>> main
    facts: List[str] = None
    opinions: List[str] = None
    impact: List[str] = None
    embedding: List[float] = None
    
    # Performance metrics
    total_cost_usd: Decimal = Decimal('0.0')
    total_duration_ms: int = 0
    stages_completed: List[str] = None
    
    # Quality flags
    required_critic: bool = False
    was_repaired: bool = False
    content_source: str = ""
    
    # Error handling
    error_message: str = ""
    failed_stage: str = ""


class ArticleRBC(models.Model):
    """
    Rich Bullet Compression - lossless content compression into labeled bullets.
    
    Stage 1 output: Article content compressed into ≤25 labeled bullet points
    that preserve key information while reducing token usage for subsequent stages.
    """
    # Primary key and relationships
    id = models.AutoField(primary_key=True)
    public_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    article = models.OneToOneField(
        'articles.Article',
        on_delete=models.CASCADE,
        related_name='rbc'
    )
    
    # RBC Content
    bullets = models.JSONField(help_text="List of labeled bullet points")
    rbc_version = models.SmallIntegerField(default=1)
    bullet_count = models.IntegerField(help_text="Number of bullets generated")
    
    # Content metadata
    content_source = models.CharField(
        max_length=20,
        choices=[
            ('imcomplete_text', 'Imcomplete Text'),
            ('full_cleaned_text', 'Full Cleaned Text'),
            ('rich_content_blocks', 'Rich Content Blocks')
        ],
        help_text="Source content used for RBC"
    )
    original_content_length = models.IntegerField(help_text="Original content character count")
    truncated_at = models.IntegerField(null=True, blank=True, help_text="Character position where content was truncated")
    
    # Processing metadata
    tokens_input = models.IntegerField(default=0)
    tokens_output = models.IntegerField(default=0)
    processing_time_ms = models.IntegerField(default=0)
    cost_usd = models.DecimalField(max_digits=8, decimal_places=6, default=0)
    ai_model_used = models.CharField(max_length=50, default='gpt-4o-mini')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'content_article_rbc'
        indexes = [
            models.Index(fields=['article']),
            models.Index(fields=['content_source']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"RBC for {self.article.title[:50]} ({self.bullet_count} bullets)"
    
    @property
    def bullets_by_type(self) -> Dict[str, List[str]]:
        """Get bullets organized by type."""
        organized = {'FACT': [], 'STAT': [], 'QUOTE': [], 'OPINION': [], 'CONTEXT': []}
        
        for bullet in self.bullets:
            for bullet_type in organized.keys():
                if bullet.startswith(f'[{bullet_type}]'):
                    organized[bullet_type].append(bullet)
                    break
        
        return organized
    
    @property
    def compression_ratio(self) -> float:
        """Calculate compression ratio (original chars / bullet chars)."""
        if not self.bullets:
            return 0.0
        
        bullet_chars = sum(len(bullet) for bullet in self.bullets)
        if bullet_chars == 0:
            return 0.0
            
        return self.original_content_length / bullet_chars


class ArticleSummary(models.Model):
    """
    Structured article summary for end-user consumption.
    
    Stage 2 output: Skeleton summary with headline, abstract, facts, opinions, and impact.
    Uses only RBC bullets as source to ensure faithfulness.
    """
    # Primary key and relationships  
    id = models.AutoField(primary_key=True)
    public_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    article = models.OneToOneField(
        'articles.Article',
        on_delete=models.CASCADE, 
        related_name='structured_summary'
    )
    
    # Summary Content (structured fields matching JSON schema)
    headline = models.CharField(max_length=255, help_text="≤15 words")
    abstract = models.TextField(help_text="≤60 words, neutral tone")
<<<<<<< HEAD
    facts = models.JSONField(default=list, help_text="3-6 key facts verbatim from RBC")
    opinions = models.JSONField(default=list, help_text="Speaker: opinion pairs")
    impact = models.JSONField(default=list, help_text="≤3 impact bullets prefixed with ⚡")
=======
    longer_abstract = models.TextField(null=True, blank=True, help_text="≤200 words, comprehensive compression")
    facts = models.JSONField(default=list, help_text="3-6 key facts verbatim from RBC")
    opinions = models.JSONField(default=list, help_text="Speaker: opinion pairs")
    impact = models.JSONField(default=list, help_text="≤3 impact bullets")
>>>>>>> main
    
    # Versioning and metadata
    summary_version = models.SmallIntegerField(default=2)
    content_source = models.CharField(max_length=20, help_text="Source used for summarization")
    
    # Word counts for validation
    headline_words = models.IntegerField(help_text="Headline word count")
    abstract_words = models.IntegerField(help_text="Abstract word count")
<<<<<<< HEAD
=======
    longer_abstract_words = models.IntegerField(null=True, blank=True, help_text="Longer abstract word count")
>>>>>>> main
    facts_count = models.IntegerField(help_text="Number of facts")
    
    # Processing metadata
    tokens_input = models.IntegerField(default=0)
    tokens_output = models.IntegerField(default=0)
    processing_time_ms = models.IntegerField(default=0)
    cost_usd = models.DecimalField(max_digits=8, decimal_places=6, default=0)
    ai_model_used = models.CharField(max_length=50, default='gpt-4o-mini')
    
    # Quality and processing flags
    required_critic_review = models.BooleanField(default=False, help_text="Whether critic review was triggered")
    critic_passed = models.BooleanField(null=True, blank=True, help_text="Result of critic review")
    was_repaired = models.BooleanField(default=False, help_text="Whether summary was repaired after critic")
    repair_attempts = models.IntegerField(default=0, help_text="Number of repair attempts")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'content_article_summary'
        indexes = [
            models.Index(fields=['article']),
            models.Index(fields=['summary_version']),
            models.Index(fields=['required_critic_review']),
            models.Index(fields=['was_repaired']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Summary: {self.headline}"
    
    @property
    def full_summary_dict(self) -> Dict[str, Any]:
        """Get complete summary as dictionary matching JSON schema."""
        return {
            'headline': self.headline,
            'abstract': self.abstract,
<<<<<<< HEAD
=======
            'longer_abstract': self.longer_abstract,
>>>>>>> main
            'facts': self.facts,
            'opinions': self.opinions,
            'impact': self.impact,
            'summary_version': self.summary_version,
            'tokens_in': self.tokens_input,
            'tokens_out': self.tokens_output
        }
    
    def update_word_counts(self):
        """Update word count fields from content."""
        self.headline_words = len(self.headline.split()) if self.headline else 0
        self.abstract_words = len(self.abstract.split()) if self.abstract else 0
<<<<<<< HEAD
=======
        self.longer_abstract_words = len(self.longer_abstract.split()) if self.longer_abstract else 0
>>>>>>> main
        self.facts_count = len(self.facts) if self.facts else 0


class ArticleEmbedding(models.Model):
    """
    Vector embeddings for semantic search and article similarity.
    
    Generated from headline + abstract for broad semantic matching.
    Future: Migrate to pgvector for performance at scale.
    """
    # Primary key and relationships
    id = models.AutoField(primary_key=True)
    public_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    article = models.OneToOneField(
        'articles.Article',
        on_delete=models.CASCADE,
        related_name='embedding'
    )
    
    # Vector data
    embedding = VectorField(dimensions=1536, help_text="1536-dimensional vector using pgvector")
    embedding_model = models.CharField(max_length=50, default='text-embedding-3-small')
    embedding_text = models.TextField(help_text="Text used for embedding generation")
    embedding_length = models.IntegerField(help_text="Vector dimension count")
    
    # Processing metadata
    tokens_used = models.IntegerField(default=0)
    processing_time_ms = models.IntegerField(default=0)
    cost_usd = models.DecimalField(max_digits=8, decimal_places=6, default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'content_article_embedding'
        indexes = [
            models.Index(fields=['article']),
            models.Index(fields=['embedding_model']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Embedding for {self.article.title[:50]}"
    
    @classmethod
    def find_similar(cls, article_id: int, threshold: float = 0.22, limit: int = 5) -> List[tuple]:
        """
        Find similar articles using pgvector cosine similarity.
        
        Args:
            article_id: ID of the article to find similar articles for
            threshold: Minimum similarity score (0-1, higher is more similar)
            limit: Maximum number of similar articles to return
            
        Returns:
            List of (article_id, similarity_score) tuples, sorted by similarity
        """
        # Get the target article's embedding
        target = cls.objects.filter(article_id=article_id).first()
        if not target:
            return []
            
        # Use pgvector's cosine similarity for efficient database-level search
        similar = cls.objects.annotate(
            similarity=1 - CosineDistance('embedding', target.embedding)
        ).filter(
            similarity__gte=threshold
        ).exclude(
            article_id=article_id  # Exclude the target article
        ).order_by(
            '-similarity'
        ).values_list(
            'article_id', 'similarity'
        )[:limit]
        
        return list(similar)


class SummarizationRequest(models.Model):
    """
    Tracks summarization requests and pipeline progress.
    
    Used for monitoring, retrying failed requests, and performance analytics.
    """
    # Primary key and relationships
    id = models.AutoField(primary_key=True)
    public_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    article = models.ForeignKey(
        'articles.Article',
        on_delete=models.CASCADE, 
        related_name='summarization_requests'
    )
    
    # Processing state
    status = models.CharField(max_length=20, choices=[
        ('queued', 'Queued'),
        ('rbc_processing', 'RBC Processing'),
        ('summary_processing', 'Summary Processing'),
        ('critic_processing', 'Critic Processing'),
        ('repair_processing', 'Repair Processing'),
        ('embedding_processing', 'Embedding Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ], default='queued', db_index=True)
    
    # Pipeline tracking
    current_stage = models.CharField(max_length=20, blank=True, help_text="Current processing stage")
    stages_completed = models.JSONField(default=list, help_text="List of completed stages")
    pipeline_start_time = models.DateTimeField(null=True, blank=True)
    pipeline_end_time = models.DateTimeField(null=True, blank=True)
    
    # Error handling
    attempts = models.IntegerField(default=0)
    max_attempts = models.IntegerField(default=3)
    last_error = models.TextField(blank=True)
    failed_stage = models.CharField(max_length=20, blank=True)
    
    # Performance tracking
    total_cost_usd = models.DecimalField(max_digits=8, decimal_places=6, default=0)
    total_duration_ms = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'content_summarization_request'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['article', 'status']),
            models.Index(fields=['current_stage']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Summarization request for: {self.article.title[:30]}... ({self.status})"
    
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
        return self.status in ['rbc_processing', 'summary_processing', 'critic_processing', 
                              'repair_processing', 'embedding_processing']


class SummarizationMetrics(models.Model):
    """
    Aggregated metrics for summarization performance monitoring.
    
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
    
    # Quality metrics
    critic_trigger_rate = models.FloatField(default=0.0, help_text="Percentage triggering critic review")
    repair_rate = models.FloatField(default=0.0, help_text="Percentage requiring repair")
    
    # Pipeline stage metrics
    rbc_failures = models.IntegerField(default=0)
    summary_failures = models.IntegerField(default=0)
    critic_failures = models.IntegerField(default=0)
    embedding_failures = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'content_summarization_metrics'
        ordering = ['-date']
    
    def __str__(self):
        return f"Summarization metrics for {self.date}"
