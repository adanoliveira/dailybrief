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
        ]
    
    def __str__(self):
        return f"{self.user.username}'s digest for {self.date}"


class DigestStory(models.Model):
    """
    A clustered story within a digest.
    Each digest story may reference multiple underlying articles.
    """
    digest = models.ForeignKey(Digest, on_delete=models.CASCADE, related_name='stories')
    
    # Story content
    title = models.CharField(max_length=255)
    summary = models.TextField()
    
    # Display order
    order = models.IntegerField(default=0)
    
    # Related articles
    articles = models.ManyToManyField(Article, related_name='digest_stories')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order']
        verbose_name_plural = 'Digest stories'
    
    def __str__(self):
        return f"{self.title} ({self.digest.date})"
