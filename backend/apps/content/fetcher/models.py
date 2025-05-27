from django.db import models
from django.utils import timezone
import uuid


class ContentFetchLog(models.Model):
    """
    Tracks content fetching attempts for articles.
    Used for monitoring, debugging, and retry logic.
    """
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('fetching', 'Fetching'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('paywall', 'Paywall Detected'),
        ('access_denied', 'Access Denied'),
        ('timeout', 'Timeout'),
        ('invalid_url', 'Invalid URL'),
        ('technical_error', 'Technical Error'),
    )
    
    CONTENT_SOURCE_CHOICES = (
        ('full_fetch', 'Full Content Fetched'),
        ('partial_fetch', 'Partial Content Fetched'),
        ('description_fallback', 'Using Description as Fallback'),
        ('no_content', 'No Content Available'),
    )
    
    # Reference to the article (we'll use article_id to avoid circular imports)
    article_id = models.IntegerField(db_index=True)
    article_url = models.URLField(max_length=1024)
    
    # Fetch attempt details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    attempt_number = models.IntegerField(default=1)
    
    # Content extraction results
    content_source = models.CharField(
        max_length=20, 
        choices=CONTENT_SOURCE_CHOICES, 
        null=True, 
        blank=True
    )
    content_length = models.IntegerField(null=True, blank=True)
    content_quality_score = models.FloatField(null=True, blank=True)  # 0.0-1.0
    
    # Technical details
    response_status_code = models.IntegerField(null=True, blank=True)
    response_time_ms = models.IntegerField(null=True, blank=True)
    user_agent_used = models.CharField(max_length=255, blank=True)
    extraction_strategy = models.CharField(max_length=50, blank=True)
    
    # Error tracking
    error_message = models.TextField(blank=True)
    error_type = models.CharField(max_length=50, blank=True)
    
    # Paywall detection
    paywall_detected = models.BooleanField(default=False)
    paywall_indicators = models.JSONField(default=list, blank=True)
    
    # Content analysis
    extracted_text_length = models.IntegerField(null=True, blank=True)
    has_main_content = models.BooleanField(default=False)
    content_completeness = models.FloatField(null=True, blank=True)  # 0.0-1.0
    
    # Timestamps
    started_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['article_id', '-created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['-created_at']),
            models.Index(fields=['paywall_detected']),
        ]
        verbose_name = 'Content Fetch Log'
        verbose_name_plural = 'Content Fetch Logs'
    
    def __str__(self):
        return f"Fetch attempt {self.attempt_number} for article {self.article_id} - {self.status}"
    
    @property
    def duration_ms(self):
        """Calculate the duration of the fetch attempt in milliseconds."""
        if self.completed_at and self.started_at:
            return int((self.completed_at - self.started_at).total_seconds() * 1000)
        return None


class FetchAttempt(models.Model):
    """
    Simplified model to track retry attempts for failed fetches.
    Used by the retry mechanism to implement exponential backoff.
    """
    article_id = models.IntegerField(db_index=True)
    attempts = models.IntegerField(default=0)
    max_attempts = models.IntegerField(default=3)
    
    # Retry scheduling
    next_retry_at = models.DateTimeField(null=True, blank=True)
    last_attempt_at = models.DateTimeField(null=True, blank=True)
    
    # Status tracking
    is_completed = models.BooleanField(default=False)
    final_status = models.CharField(max_length=20, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('article_id',)
        indexes = [
            models.Index(fields=['next_retry_at']),
            models.Index(fields=['is_completed']),
        ]
        verbose_name = 'Fetch Attempt Tracker'
        verbose_name_plural = 'Fetch Attempt Trackers'
    
    def __str__(self):
        return f"Fetch attempts for article {self.article_id}: {self.attempts}/{self.max_attempts}"
    
    def increment_attempt(self):
        """Increment the attempt counter and update timestamps."""
        self.attempts += 1
        self.last_attempt_at = timezone.now()
        
        # Calculate next retry time with exponential backoff
        if self.attempts < self.max_attempts:
            # Exponential backoff: 1 hour, 4 hours, 16 hours
            backoff_hours = 1 * (4 ** (self.attempts - 1))
            self.next_retry_at = timezone.now() + timezone.timedelta(hours=backoff_hours)
        else:
            # Max attempts reached
            self.is_completed = True
            self.next_retry_at = None
        
        self.save()
    
    def mark_completed(self, status):
        """Mark the fetch attempts as completed with a final status."""
        self.is_completed = True
        self.final_status = status
        self.next_retry_at = None
        self.save()
