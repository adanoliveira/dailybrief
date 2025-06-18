from django.db import models
from django.contrib.auth.models import User
from apps.articles.models import Article
import uuid


class Digest(models.Model):
    """
    A daily digest of news articles for a user.
    """
    public_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='digests')
    
    # Digest metadata
    title = models.CharField(max_length=255)
    date = models.DateField(help_text="Date this digest covers")
    
    # Digest content
    introduction = models.TextField(help_text="AI-generated introduction to the day's stories")
    html_content = models.TextField(help_text="Full HTML content of the digest")
    
    # Generation status tracking
    generation_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending Generation'),
            ('processing', 'Processing'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
        ],
        default='pending',
        help_text="Current status of digest generation"
    )
    
    # Processing metadata
    articles_processed = models.IntegerField(default=0, help_text="Number of articles processed for this digest")
    events_included = models.IntegerField(default=0, help_text="Number of events included in this digest")
    topics_included = models.IntegerField(default=0, help_text="Number of topics included in this digest")
    generation_cost_usd = models.DecimalField(
        max_digits=8, 
        decimal_places=6, 
        default=0, 
        help_text="Total cost in USD for generating this digest"
    )
    generation_duration_ms = models.IntegerField(default=0, help_text="Time taken to generate digest in milliseconds")
    error_message = models.TextField(blank=True, help_text="Error message if generation failed")
    
    # User context
    user_timezone = models.CharField(max_length=50, default='UTC', help_text="User's timezone when digest was generated")
    digest_preferences = models.JSONField(default=dict, help_text="User preferences snapshot at generation time")
    
    # AI generation metadata
    ai_model_used = models.CharField(max_length=50, blank=True, help_text="AI model used for content generation")
    tokens_input = models.IntegerField(default=0, help_text="Total input tokens used")
    tokens_output = models.IntegerField(default=0, help_text="Total output tokens generated")
    
    # Status fields
    is_published = models.BooleanField(default=False)
    is_sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('user', 'date')
        ordering = ['-date']
        indexes = [
            models.Index(fields=['-date']),
            models.Index(fields=['public_id']),
            models.Index(fields=['generation_status']),
            models.Index(fields=['user', 'date']),
            models.Index(fields=['user', 'generation_status']),
        ]
    
    def __str__(self):
        return f"{self.user.username}'s digest for {self.date} ({self.generation_status})"


class DigestTopic(models.Model):
    """
    A topic section within a digest with its events and summary.
    Represents a high-level topic grouping (e.g., Technology, Politics) with AI-generated synthesis.
    """
    digest = models.ForeignKey(Digest, on_delete=models.CASCADE, related_name='digest_topics')
    topic = models.ForeignKey('feeds.Topic', on_delete=models.CASCADE, help_text="The topic this section covers")
    
    # AI-generated content
    topic_abstract = models.TextField(help_text="AI-generated topic summary (2-3 sentences)")
    main_facts = models.JSONField(
        default=list, 
        help_text="Top 5 facts across all events in this topic (list of strings)"
    )
    perspectives = models.JSONField(
        default=list, 
        help_text="Key perspectives/opinions from different sources (list of strings)"
    )
    
    # Metadata
    order = models.IntegerField(default=0, help_text="Display order within the digest")
    event_count = models.IntegerField(default=0, help_text="Number of events in this topic section")
    article_count = models.IntegerField(default=0, help_text="Total articles contributing to this topic")
    
    # Processing metadata
    generation_cost_usd = models.DecimalField(
        max_digits=6, 
        decimal_places=6, 
        default=0, 
        help_text="Cost to generate this topic summary"
    )
    tokens_input = models.IntegerField(default=0, help_text="Input tokens for this topic generation")
    tokens_output = models.IntegerField(default=0, help_text="Output tokens for this topic generation")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('digest', 'topic')
        ordering = ['order']
        indexes = [
            models.Index(fields=['digest', 'order']),
            models.Index(fields=['topic']),
        ]
        verbose_name_plural = 'Digest topics'
    
    def __str__(self):
        return f"{self.topic.name} in {self.digest.user.username}'s digest ({self.digest.date})"


class DigestStory(models.Model):
    """
    An event-based story within a topic section.
    Represents a specific event/story with AI-enhanced summary and article recommendations.
    """
    # Relationships
    digest = models.ForeignKey(Digest, on_delete=models.CASCADE, related_name='stories')
    digest_topic = models.ForeignKey(
        DigestTopic, 
        on_delete=models.CASCADE, 
        related_name='stories',
        null=True,
        blank=True,
        help_text="The topic section this story belongs to"
    )
    event = models.ForeignKey(
        'analyzer.Event', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        help_text="The primary event this story represents"
    )
    
    # Story content (existing)
    title = models.CharField(max_length=255)
    summary = models.TextField()
    
    # Enhanced content (new)
    enhanced_abstract = models.TextField(
        help_text="AI-enhanced event summary synthesizing multiple articles",
        blank=True
    )
    key_facts = models.JSONField(
        default=list, 
        help_text="Key facts from multiple articles about this event (list of strings)"
    )
    perspectives = models.JSONField(
        default=list, 
        help_text="Different viewpoints/opinions about this event (list of strings)"
    )
    
    # Article recommendations
    recommended_articles = models.ManyToManyField(
        Article, 
        related_name='digest_recommendations',
        blank=True,
        help_text="3 most recent/relevant articles for deep dive reading"
    )
    
    # Event metadata
    article_count = models.IntegerField(
        default=0, 
        help_text="Total articles mentioning this event (primary + secondary)"
    )
    primary_mentions = models.IntegerField(
        default=0, 
        help_text="Articles with this as primary event"
    )
    secondary_mentions = models.IntegerField(
        default=0, 
        help_text="Articles with this as secondary event"
    )
    event_score = models.FloatField(
        default=0.0, 
        help_text="Calculated importance score (primary_count * 2 + secondary_count)"
    )
    
    # Processing metadata
    generation_cost_usd = models.DecimalField(
        max_digits=6, 
        decimal_places=6, 
        default=0, 
        help_text="Cost to generate enhanced content for this story"
    )
    tokens_input = models.IntegerField(default=0, help_text="Input tokens for this story generation")
    tokens_output = models.IntegerField(default=0, help_text="Output tokens for this story generation")
    
    # Display order
    order = models.IntegerField(default=0)
    
    # Related articles (legacy - keeping for backward compatibility)
    articles = models.ManyToManyField(Article, related_name='digest_stories', blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['digest_topic__order', 'order']
        indexes = [
            models.Index(fields=['digest_topic', 'order']),
            models.Index(fields=['event']),
            models.Index(fields=['event_score']),
        ]
        verbose_name_plural = 'Digest stories'
    
    def __str__(self):
        topic_name = self.digest_topic.topic.name if self.digest_topic else "Unknown Topic"
        event_title = self.event.title if self.event else self.title
        return f"{event_title} in {topic_name} ({self.digest.date})"
