from django.db import models

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
    )
    
    STATUS_CHOICES = (
        ('started', 'Started'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )
    
    sync_type = models.CharField(max_length=20, choices=SYNC_TYPES)
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
