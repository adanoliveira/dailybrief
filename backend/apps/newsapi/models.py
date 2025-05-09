from django.db import models
from apps.articles.models import Article

# Create your models here.

class NewsAPIRequest(models.Model):
    """
    Tracks API requests to the News API service.
    Used for monitoring rate limits and debugging.
    """
    REQUEST_TYPES = (
        ('top_headlines', 'Top Headlines'),
        ('everything', 'Everything'),
        ('sources', 'Sources'),
    )
    
    request_type = models.CharField(max_length=20, choices=REQUEST_TYPES)
    endpoint = models.CharField(max_length=255)
    
    # Request parameters (stored as JSON)
    params = models.JSONField(default=dict)
    
    # Response metadata
    status_code = models.IntegerField(null=True, blank=True)
    success = models.BooleanField(default=False)
    error_message = models.TextField(blank=True)
    
    # Rate limit info
    rate_limit_remaining = models.IntegerField(null=True, blank=True)
    rate_limit_reset = models.DateTimeField(null=True, blank=True)
    
    # Response stats
    total_results = models.IntegerField(default=0)
    results_fetched = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['request_type']),
        ]
    
    def __str__(self):
        return f"{self.request_type} request at {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}"


class NewsAPISyncLog(models.Model):
    """
    Logs the sync process for News API data.
    Used to track when articles were last fetched.
    """
    SYNC_TYPES = (
        ('top_headlines', 'Top Headlines'),
        ('everything', 'Everything'),
        ('sources', 'Sources'),
        ('everything_by_publication', 'Everything By Publication'),
        ('everything_by_sources_batched', 'Everything By Sources Batched'),
    )
    
    STATUS_CHOICES = (
        ('started', 'Started'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )
    
    sync_type = models.CharField(max_length=50, choices=SYNC_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='started')
    
    # Sync parameters
    parameters = models.JSONField(default=dict, help_text="Parameters used for this sync")
    
    # Results
    articles_found = models.IntegerField(default=0)
    articles_created = models.IntegerField(default=0)
    articles_updated = models.IntegerField(default=0)
    
    # Error information
    error_message = models.TextField(blank=True)
    
    # Duration tracking
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.FloatField(null=True, blank=True)
    
    class Meta:
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['-started_at']),
            models.Index(fields=['sync_type', 'status']),
        ]
    
    def __str__(self):
        return f"{self.sync_type} sync {self.status} at {self.started_at.strftime('%Y-%m-%d %H:%M:%S')}"


class NewsAPIArticle(models.Model):
    """
    Stores NewsAPI-specific data for an article.
    Creates a clean separation between our domain model and the external API.
    """
    # Relationship to our core Article model
    article = models.OneToOneField(
        Article,
        on_delete=models.CASCADE,
        related_name='newsapi_data'
    )
    
    # NewsAPI specific fields
    source_id = models.CharField(max_length=255, blank=True, null=True)
    source_name = models.CharField(max_length=255, blank=True)
    domain = models.CharField(max_length=255, blank=True, null=True, db_index=True,
                             help_text="Normalized domain name extracted from article URL")
    newsapi_id = models.CharField(max_length=255, blank=True, null=True)
    category = models.CharField(max_length=100, blank=True, null=True)
    
    # Original JSON response
    raw_data = models.JSONField(default=dict)
    
    # Sync metadata
    sync_log = models.ForeignKey(
        NewsAPISyncLog, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='articles'
    )
    is_top_headline = models.BooleanField(default=False)
    
    # Timestamps
    fetched_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['source_id']),
            models.Index(fields=['newsapi_id']),
            models.Index(fields=['fetched_at']),
        ]
        verbose_name = "NewsAPI Article"
        verbose_name_plural = "NewsAPI Articles"
    
    def __str__(self):
        return f"NewsAPI: {self.source_name} - {self.article.title[:50]}"
