from django.db import models

# Create your models here.

class AIProviderUsage(models.Model):
    """
    Tracks usage of different AI providers for cost monitoring.
    """
    PROVIDER_CHOICES = (
        ('openai', 'OpenAI'),
        ('anthropic', 'Anthropic'),
        ('other', 'Other Provider'),
    )
    
    OPERATION_TYPES = (
        ('summarization', 'Article Summarization'),
        ('digest_generation', 'Digest Generation'),
        ('translation', 'Translation'),
        ('quality_assessment', 'Content Quality Assessment'),
        ('content_extraction', 'Content Extraction'),
        # Summarization pipeline operations
        ('rbc_compression', 'Rich Bullet Compression'),
        ('skeleton_summary', 'Skeleton Summary Generation'),
        ('summary_critique', 'Summary Critique Review'),
        ('summary_repair', 'Summary Repair'),
        ('embedding_generation', 'Embedding Generation'),
        # Analyzer pipeline operations
        ('linguistic_analysis', 'Linguistic Analysis'),
        ('entity_extraction', 'Entity Extraction'),
        ('event_detection', 'Event Detection'),
        ('topic_classification', 'Topic Classification'),
        ('region_classification', 'Region Classification'),
    )
    
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    model = models.CharField(max_length=50, help_text="Specific model used (e.g. 'gpt-3.5-turbo')")
    operation = models.CharField(max_length=30, choices=OPERATION_TYPES)
    
    # Usage metrics
    prompt_tokens = models.IntegerField(default=0)
    completion_tokens = models.IntegerField(default=0)
    total_tokens = models.IntegerField(default=0)
    
    # Cost tracking (in USD)
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=6, default=0)
    
    # Performance metrics
    response_time = models.FloatField(help_text="Response time in seconds", default=0)
    
    # Result metadata
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
    
    # Request/response data (for debugging)
    request_data = models.JSONField(default=dict, blank=True)
    response_data = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['provider', 'operation']),
        ]
        verbose_name_plural = 'AI provider usages'
    
    def __str__(self):
        return f"{self.provider} ({self.model}) for {self.operation} at {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}"


class AIProviderConfig(models.Model):
    """
    Configuration for different AI operations.
    Allows switching between providers for different operations.
    """
    OPERATION_TYPES = (
        ('summarization', 'Article Summarization'),
        ('digest_generation', 'Digest Generation'),
        ('translation', 'Translation'),
        ('quality_assessment', 'Content Quality Assessment'),
        ('content_extraction', 'Content Extraction'),
        # Summarization pipeline operations
        ('rbc_compression', 'Rich Bullet Compression'),
        ('skeleton_summary', 'Skeleton Summary Generation'),
        ('summary_critique', 'Summary Critique Review'),
        ('summary_repair', 'Summary Repair'),
        ('embedding_generation', 'Embedding Generation'),
        # Analyzer pipeline operations
        ('linguistic_analysis', 'Linguistic Analysis'),
        ('entity_extraction', 'Entity Extraction'),
        ('event_detection', 'Event Detection'),
        ('topic_classification', 'Topic Classification'),
        ('region_classification', 'Region Classification'),
    )
    
    PROVIDER_CHOICES = (
        ('openai', 'OpenAI'),
        ('anthropic', 'Anthropic'),
        ('other', 'Other Provider'),
    )
    
    operation = models.CharField(max_length=30, choices=OPERATION_TYPES, unique=True)
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    model = models.CharField(max_length=50, help_text="Specific model to use")
    
    # Configuration options
    config = models.JSONField(default=dict, help_text="Provider-specific configuration options")
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.operation} using {self.provider} ({self.model})"
