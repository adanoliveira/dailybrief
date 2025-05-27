from django.db import models
from django.contrib.auth.models import User
import uuid
from apps.feeds.models import Publication, Topic, Region, Language
from django.contrib.postgres.fields import ArrayField


class ContentStatus(models.TextChoices):
    """Content availability status choices."""
    # Initial states
    PENDING = 'pending', 'Pending Fetch'
    FETCHING = 'fetching', 'Fetching Content'
    
    # Success states
    CONTENT_AVAILABLE = 'content_available', 'Full Content Available'
    PARTIAL_CONTENT = 'partial_content', 'Partial Content Available'
    METADATA_ONLY = 'metadata_only', 'Metadata Only (No Content)'
    
    # Failure states
    PAYWALL_BLOCKED = 'paywall_blocked', 'Blocked by Paywall'
    ACCESS_DENIED = 'access_denied', 'Access Denied'
    TECHNICAL_ERROR = 'technical_error', 'Technical Error'
    INVALID_URL = 'invalid_url', 'Invalid or Dead URL'
    TIMEOUT = 'timeout', 'Request Timeout'


class ProcessingStatus(models.TextChoices):
    """AI processing status choices."""
    PENDING = 'pending', 'Pending Processing'
    PROCESSING = 'processing', 'AI Processing'
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
    Model for storing individual news articles.
    """
    public_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    # Article metadata
    title = models.CharField(max_length=512)
    description = models.TextField(blank=True, null=True)
    content = models.TextField(blank=True, null=True)
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
    
    # Content availability tracking
    content_status = models.CharField(
        max_length=20, 
        choices=ContentStatus.choices, 
        default=ContentStatus.PENDING,
        db_index=True
    )
    content_fetch_attempts = models.IntegerField(default=0)
    max_fetch_attempts = models.IntegerField(default=3)
    last_fetch_attempt = models.DateTimeField(null=True, blank=True)
    fetch_error_message = models.TextField(blank=True)
    
    # Content quality indicators
    content_completeness = models.FloatField(null=True, blank=True)  # 0.0-1.0
    content_quality_score = models.FloatField(null=True, blank=True)  # 0.0-1.0
    
    # Rich content fields
    rich_content = models.JSONField(default=dict, blank=True)  # Structured content blocks
    media_assets = models.JSONField(default=list, blank=True)  # Media metadata and URLs
    formatting_data = models.JSONField(default=dict, blank=True)  # Typography and structure info
    content_structure = models.JSONField(default=dict, blank=True)  # Article structure map
    
    # Rich content metadata
    has_images = models.BooleanField(default=False)
    has_videos = models.BooleanField(default=False)
    has_audio = models.BooleanField(default=False)
    media_count = models.PositiveIntegerField(default=0)
    formatting_score = models.FloatField(default=0.0)  # 0.0-1.0 richness score
    
    # Processing tracking
    processing_status = models.CharField(
        max_length=20,
        choices=ProcessingStatus.choices,
        default=ProcessingStatus.PENDING,
        db_index=True
    )
    processing_attempts = models.IntegerField(default=0)
    last_processing_attempt = models.DateTimeField(null=True, blank=True)
    
    # Fallback content strategy
    use_description_as_content = models.BooleanField(default=False)
    content_source = models.CharField(
        max_length=20,
        choices=[
            ('full_fetch', 'Full Content Fetched'),
            ('partial_fetch', 'Partial Content Fetched'),
            ('description', 'Using Description'),
            ('summary_only', 'Summary Only'),
        ],
        null=True, blank=True
    )
    
    class Meta:
        ordering = ['-published_at']
        indexes = [
            models.Index(fields=['-published_at']),
            models.Index(fields=['public_id']),
            models.Index(fields=['summary_ready']),
            models.Index(fields=['is_top_headline']),
            models.Index(fields=['content_hash']),
            models.Index(fields=['popularity_score']),
            models.Index(fields=['content_status']),
            models.Index(fields=['processing_status']),
            models.Index(fields=['content_status', 'processing_status']),
            models.Index(fields=['has_images']),
            models.Index(fields=['has_videos']),
            models.Index(fields=['media_count']),
            models.Index(fields=['formatting_score']),
        ]
    
    def __str__(self):
        return self.title
    
    @property
    def needs_content_fetch(self):
        """Check if article needs content fetching."""
        return (
            self.content_status == ContentStatus.PENDING and 
            self.content_fetch_attempts < self.max_fetch_attempts
        )
    
    @property
    def needs_processing(self):
        """Check if article needs AI processing."""
        return (
            self.content_status in [ContentStatus.CONTENT_AVAILABLE, ContentStatus.PARTIAL_CONTENT, ContentStatus.METADATA_ONLY] and
            self.processing_status == ProcessingStatus.PENDING
        )
    
    @property
    def has_usable_content(self):
        """Check if article has content that can be processed or displayed."""
        return (
            self.content_status in [ContentStatus.CONTENT_AVAILABLE, ContentStatus.PARTIAL_CONTENT] or
            (self.content_status == ContentStatus.METADATA_ONLY and self.description)
        )
    
    @property
    def has_rich_content(self):
        """Check if article has rich content (media or formatting)."""
        return (
            self.has_images or 
            self.has_videos or 
            self.has_audio or 
            self.formatting_score > 0.0
        )
    
    @property
    def rich_content_summary(self):
        """Get a summary of rich content features."""
        features = []
        if self.has_images:
            image_count = len([asset for asset in self.media_assets if asset.get('type') == 'image'])
            features.append(f"{image_count} image{'s' if image_count != 1 else ''}")
        if self.has_videos:
            video_count = len([asset for asset in self.media_assets if 'video' in asset.get('type', '')])
            features.append(f"{video_count} video{'s' if video_count != 1 else ''}")
        if self.has_audio:
            audio_count = len([asset for asset in self.media_assets if asset.get('type') == 'audio'])
            features.append(f"{audio_count} audio file{'s' if audio_count != 1 else ''}")
        
        if self.formatting_score > 0.5:
            features.append("rich formatting")
        
        return ", ".join(features) if features else "text only"
    
    def update_rich_content_metadata(self):
        """Update rich content metadata fields based on current data."""
        # Update media flags
        media_types = [asset.get('type', '') for asset in self.media_assets]
        self.has_images = any('image' in media_type for media_type in media_types)
        self.has_videos = any('video' in media_type for media_type in media_types)
        self.has_audio = any('audio' in media_type for media_type in media_types)
        self.media_count = len(self.media_assets)
        
        # Calculate formatting score
        formatting_elements = 0
        if self.formatting_data:
            for category, items in self.formatting_data.items():
                if isinstance(items, list):
                    formatting_elements += len(items)
        
        # Normalize formatting score (0.0-1.0)
        # More than 20 formatting elements = 1.0
        self.formatting_score = min(formatting_elements / 20.0, 1.0)
    
    def get_content_blocks_by_type(self, block_type: str):
        """Get content blocks of a specific type."""
        if not self.rich_content or 'blocks' not in self.rich_content:
            return []
        
        return [
            block for block in self.rich_content['blocks'] 
            if block.get('type') == block_type
        ]
    
    def get_media_assets_by_type(self, media_type: str):
        """Get media assets of a specific type."""
        return [
            asset for asset in self.media_assets 
            if asset.get('type') == media_type
        ]


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
