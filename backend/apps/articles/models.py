from django.db import models
from django.contrib.auth.models import User
import uuid
from apps.feeds.models import Publication, Topic, Region, Language


class Article(models.Model):
    """
    Model for storing individual news articles.
    """
    public_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    # Article metadata
    title = models.CharField(max_length=512)
    description = models.TextField(blank=True)
    content = models.TextField(blank=True)
    url = models.URLField()
    image_url = models.URLField(null=True, blank=True)
    
    # Source information
    source_name = models.CharField(max_length=255, blank=True)
    publication = models.ForeignKey(
        Publication, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='articles'
    )
    author = models.CharField(max_length=255, blank=True)
    
    # Classification fields
    topics = models.ManyToManyField(Topic, related_name='articles', blank=True)
    regions = models.ManyToManyField(Region, related_name='articles', blank=True)
    language = models.ForeignKey(
        Language, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='articles'
    )
    
    # Original news API identifier (if applicable)
    news_api_id = models.CharField(max_length=255, null=True, blank=True)
    
    # Dates
    published_at = models.DateTimeField()
    fetched_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Status flags
    is_top_headline = models.BooleanField(default=False)
    summary_ready = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-published_at']
        indexes = [
            models.Index(fields=['-published_at']),
            models.Index(fields=['public_id']),
            models.Index(fields=['summary_ready']),
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
