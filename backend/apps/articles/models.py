from django.db import models
from django.contrib.auth.models import User
import uuid
from apps.feeds.models import Publication, Topic, Region, Language
from django.contrib.postgres.fields import ArrayField


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
    
    class Meta:
        ordering = ['-published_at']
        indexes = [
            models.Index(fields=['-published_at']),
            models.Index(fields=['public_id']),
            models.Index(fields=['summary_ready']),
            models.Index(fields=['is_top_headline']),
            models.Index(fields=['content_hash']),
            models.Index(fields=['popularity_score']),
        ]
    
    def __str__(self):
        return self.title


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
