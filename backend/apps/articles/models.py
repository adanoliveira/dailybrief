from django.db import models
from django.contrib.auth.models import User
import uuid
from apps.feeds.models import Publication, Topic, Region, Language
from django.contrib.postgres.fields import ArrayField


class FetchStatus(models.TextChoices):
    """Step 1 fetch status choices."""
    PENDING = 'pending', 'Pending Fetch'
    FETCHING = 'fetching', 'Fetching Content'
    COMPLETED = 'completed', 'Fetch Completed'
    FAILED = 'failed', 'Fetch Failed'


class ProcessingStatus(models.TextChoices):
    """Step 2 processing status choices."""
    PENDING = 'pending', 'Pending Processing'
    PROCESSING = 'processing', 'Processing Content'
    COMPLETED = 'completed', 'Processing Completed'
    FAILED = 'failed', 'Processing Failed'


class StoryGroup(models.Model):
    """
    A group of related articles that form a comprehensive story.
    Used for clustering articles about the same event or ongoing story.
    """
    title = models.CharField(max_length=255)
    summary = models.TextField(blank=True)
    public_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    # Timeframe
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(null=True, blank=True)
    is_ongoing = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title


class Article(models.Model):
    """
    Model for storing individual news articles with 4-step processing pipeline.
    """
    public_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    # Article metadata
    title = models.CharField(max_length=512)
    description = models.TextField(blank=True, null=True)
    content = models.TextField(blank=True, null=True)  # Final content for backward compatibility
    url = models.URLField(max_length=1024)
    image_url = models.URLField(max_length=1024, null=True, blank=True)
    
    # Source information
    source_name = models.CharField(max_length=255, blank=True, null=True)
    publication = models.ForeignKey(
        Publication, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='articles'
    )
    author = models.CharField(max_length=255, blank=True, null=True)
    
    # Classification fields
    topics = models.ManyToManyField(Topic, related_name='articles', blank=True)
    regions = models.ManyToManyField(Region, related_name='articles', blank=True)
    language = models.ForeignKey(
        Language, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='articles'
    )
    
    # Dates
    published_at = models.DateTimeField()
    fetched_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Content analysis
    keywords = ArrayField(models.CharField(max_length=100), blank=True, null=True)
    word_count = models.IntegerField(null=True, blank=True)
    read_time_minutes = models.FloatField(null=True, blank=True)
    content_hash = models.CharField(max_length=64, null=True, blank=True)
    sentiment_score = models.FloatField(null=True, blank=True)
    entities = models.JSONField(default=dict, blank=True)
    
    # Ranking and metrics
    popularity_score = models.FloatField(default=0.0)
    relevance_score = models.FloatField(default=0.0)
    
    # Relationships
    related_articles = models.ManyToManyField('self', symmetrical=False, blank=True, related_name='related_to')
    story_group = models.ForeignKey(StoryGroup, on_delete=models.SET_NULL, null=True, blank=True, related_name='articles')
    
    # Status flags
    is_top_headline = models.BooleanField(default=False)
    summary_ready = models.BooleanField(default=False)
    
    # ===== STEP 1: EXTRACTION FIELDS =====
    # Raw content from Step 1 extraction
    raw_html = models.TextField(blank=True)  # Full HTML for Step 2 processing
    basic_content = models.TextField(blank=True)  # Quick text for immediate display
    extraction_metadata = models.JSONField(default=dict, blank=True)  # Basic extraction info
    
    # Step 1 status tracking
    fetch_status = models.CharField(
        max_length=20,
        choices=FetchStatus.choices,
        default=FetchStatus.PENDING,
        db_index=True
    )
    fetch_strategy_used = models.CharField(max_length=50, blank=True)
    fetch_duration_ms = models.IntegerField(null=True, blank=True)
    fetch_attempts = models.IntegerField(default=0)
    last_fetch_attempt = models.DateTimeField(null=True, blank=True)
    fetch_error_message = models.TextField(blank=True)
    
    # Paywall detection from Step 1
    paywall_detected = models.BooleanField(default=False)
    paywall_indicators = models.JSONField(default=list, blank=True)
    
    # ===== STEP 2: PROCESSING FIELDS =====
    # Step 2 processing status and results
    process_status = models.CharField(
        max_length=20,
        choices=ProcessingStatus.choices,
        default=ProcessingStatus.PENDING,
        db_index=True
    )
    process_route = models.CharField(
        max_length=20,
        choices=[
            ('safari_mode', 'Safari Reader Mode'),
            ('llm_enhanced', 'LLM Enhanced'),
            ('hybrid', 'Hybrid Processing')
        ],
        null=True, blank=True
    )
    
    # Processed content (Step 2 output)
    clean_content = models.TextField(blank=True)  # Safari-like clean content
    content_blocks = models.JSONField(default=list, blank=True)  # Structured content blocks
    extracted_metadata = models.JSONField(default=dict, blank=True)  # Enhanced metadata
    content_quality_metrics = models.JSONField(default=dict, blank=True)  # Quality assessment
    
    # Processing performance tracking
    process_duration_ms = models.IntegerField(null=True, blank=True)
    process_cost_usd = models.DecimalField(max_digits=8, decimal_places=6, null=True, blank=True)
    process_attempts = models.IntegerField(default=0)
    last_process_attempt = models.DateTimeField(null=True, blank=True)
    process_error_message = models.TextField(blank=True)
    
    # Rich content metadata (derived from content_blocks)
    has_images = models.BooleanField(default=False)
    has_videos = models.BooleanField(default=False)
    has_audio = models.BooleanField(default=False)
    media_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['-published_at']
        indexes = [
            models.Index(fields=['-published_at']),
            models.Index(fields=['public_id']),
            models.Index(fields=['summary_ready']),
            models.Index(fields=['is_top_headline']),
            models.Index(fields=['content_hash']),
            models.Index(fields=['popularity_score']),
            models.Index(fields=['fetch_status']),
            models.Index(fields=['process_status']),
            models.Index(fields=['fetch_status', 'process_status']),
            models.Index(fields=['paywall_detected']),
            models.Index(fields=['process_route']),
            models.Index(fields=['has_images']),
            models.Index(fields=['has_videos']),
            models.Index(fields=['media_count']),
        ]
    
    def __str__(self):
        return self.title
    
    # ===== STEP 1 PROPERTIES =====
    @property
    def needs_fetch(self):
        """Check if article needs Step 1 fetching."""
        return (
            self.fetch_status == FetchStatus.PENDING and 
            self.fetch_attempts < 3  # Max attempts
        )
    
    @property
    def has_raw_content(self):
        """Check if article has raw HTML from Step 1."""
        return bool(self.raw_html and len(self.raw_html) > 100)
    
    @property
    def has_basic_content(self):
        """Check if article has basic content for immediate display."""
        return bool(self.basic_content and len(self.basic_content) > 50)
    
    # ===== STEP 2 PROPERTIES =====
    @property
    def needs_processing(self):
        """Check if article needs Step 2 processing."""
        return (
            self.fetch_status == FetchStatus.COMPLETED and
            self.has_raw_content and
            self.process_status == ProcessingStatus.PENDING and
            self.process_attempts < 3  # Max attempts
        )
    
    @property
    def has_clean_content(self):
        """Check if article has processed clean content from Step 2."""
        return bool(self.clean_content and len(self.clean_content) > 100)
    
    @property
    def processing_route_display(self):
        """Get human-readable processing route."""
        route_map = {
            'safari_mode': 'Safari Reader Mode',
            'llm_enhanced': 'LLM Enhanced',
            'hybrid': 'Hybrid Processing'
        }
        return route_map.get(self.process_route, 'Unknown')
    
    @property
    def has_usable_content(self):
        """Check if article has any usable content."""
        return bool(
            self.content or 
            self.basic_content or 
            self.clean_content or 
            (self.description and len(self.description) > 100)
        )
    
    @property
    def has_rich_content(self):
        """Check if article has rich content data."""
        return bool(self.content_blocks and len(self.content_blocks) > 0)
    
    @property
    def rich_content_summary(self):
        """Get a summary of rich content available."""
        return {
            'has_content': self.has_rich_content,
            'blocks_count': len(self.content_blocks) if self.content_blocks else 0,
            'media_count': self.media_count,
            'has_images': self.has_images,
            'has_videos': self.has_videos,
            'has_audio': self.has_audio,
            'quality_score': self.content_quality_metrics.get('overall_score', 0) if self.content_quality_metrics else 0
        }
    
    def update_rich_content_metadata(self):
        """Update rich content metadata fields from content_blocks."""
        if self.content_blocks:
            # Updated to match the actual block types generated by our processor
            image_types = ['img', 'figure', 'image']  # Include both 'img' and 'figure' for images
            video_types = ['video']
            audio_types = ['audio']
            
            self.has_images = any(block.get('type') in image_types for block in self.content_blocks)
            self.has_videos = any(block.get('type') in video_types for block in self.content_blocks)
            self.has_audio = any(block.get('type') in audio_types for block in self.content_blocks)
            
            # Count all media types including img and figure
            media_types = image_types + video_types + audio_types
            self.media_count = len([block for block in self.content_blocks if block.get('type') in media_types])
        else:
            self.has_images = False
            self.has_videos = False
            self.has_audio = False
            self.media_count = 0
    
    def get_content_blocks_by_type(self, block_type: str):
        """Get content blocks of a specific type."""
        if not self.content_blocks:
            return []
        return [block for block in self.content_blocks if block.get('type') == block_type]


class UserArticleInteraction(models.Model):
    """
    Tracks user interactions with articles for personalization.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='article_interactions')
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='user_interactions')
    
    # Interaction types
    read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    bookmarked = models.BooleanField(default=False)
    bookmarked_at = models.DateTimeField(null=True, blank=True)
    
    clicked = models.BooleanField(default=False)
    clicked_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('user', 'article')
        indexes = [
            models.Index(fields=['user', 'read']),
            models.Index(fields=['user', 'bookmarked']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.article.title[:30]}..."

