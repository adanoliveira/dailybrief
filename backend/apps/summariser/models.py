from django.db import models
from apps.articles.models import Article


class ArticleSummary(models.Model):
    """
    Stores AI-generated summaries for articles.
    """
    article = models.OneToOneField(
        Article, 
        on_delete=models.CASCADE, 
        related_name='summary'
    )
    
    # Summary content
    abstract = models.TextField(help_text="Short abstract of the article (1-3 sentences)")
    key_points = models.TextField(help_text="Key points extracted from the article")
    full_summary = models.TextField(help_text="Full detailed summary of the article")
    
    # Translation fields (for article summaries)
    is_translated = models.BooleanField(default=False)
    original_language = models.CharField(max_length=5, blank=True)
    
    # Metadata
    ai_provider = models.CharField(max_length=50, blank=True, help_text="Which AI provider generated this summary")
    prompt_tokens = models.IntegerField(default=0)
    completion_tokens = models.IntegerField(default=0)
    processing_time = models.FloatField(default=0.0, help_text="Time taken to generate the summary in seconds")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Summary of: {self.article.title[:50]}..."


class SummarizationRequest(models.Model):
    """
    Tracks requests for article summarization.
    Used for monitoring and retrying failed summarization attempts.
    """
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )
    
    article = models.ForeignKey(
        Article, 
        on_delete=models.CASCADE, 
        related_name='summarization_requests'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Attempt tracking
    attempts = models.IntegerField(default=0)
    max_attempts = models.IntegerField(default=3)
    
    # Error tracking
    last_error = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['article', 'status']),
        ]
    
    def __str__(self):
        return f"Summary request for: {self.article.title[:30]}... ({self.status})"
