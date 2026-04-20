from django.db import models


class RSSFeed(models.Model):
    """
    Represents an individual RSS/Atom feed URL with its sync state.
    A single Publication may have multiple feeds (e.g., NYT Business, NYT Tech).
    """

    STATUS_CHOICES = (
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('error', 'Error'),
        ('disabled', 'Disabled'),
    )

    publication = models.ForeignKey(
        'feeds.Publication',
        on_delete=models.CASCADE,
        related_name='rss_feeds',
    )
    feed_url = models.URLField(max_length=1024, unique=True)
    title = models.CharField(max_length=255, blank=True)

    # Classification
    topic = models.ForeignKey(
        'feeds.Topic', on_delete=models.SET_NULL, null=True, blank=True, related_name='rss_feeds'
    )
    region = models.ForeignKey(
        'feeds.Region', on_delete=models.SET_NULL, null=True, blank=True, related_name='rss_feeds'
    )
    language = models.ForeignKey(
        'feeds.Language', on_delete=models.SET_NULL, null=True, blank=True, related_name='rss_feeds'
    )

    # Sync state (HTTP conditional GET)
    etag = models.CharField(max_length=255, blank=True)
    last_modified = models.CharField(max_length=255, blank=True)
    last_fetched_at = models.DateTimeField(null=True, blank=True)
    last_successful_fetch_at = models.DateTimeField(null=True, blank=True)

    # Error tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    consecutive_errors = models.IntegerField(default=0)
    last_error_message = models.TextField(blank=True)

    # Feed metadata (auto-populated on first fetch)
    feed_type = models.CharField(max_length=20, blank=True)
    feed_description = models.TextField(blank=True)

    # Priority (1=highest, 10=lowest). Finance feeds get 1-3.
    priority = models.IntegerField(default=5)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['priority', 'publication__name']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['last_fetched_at']),
            models.Index(fields=['priority']),
        ]
        verbose_name = 'RSS Feed'
        verbose_name_plural = 'RSS Feeds'

    def __str__(self):
        return f"{self.publication.name} — {self.title or self.feed_url}"


class RSSFeedSyncLog(models.Model):
    """
    Audit log for RSS feed sync operations.
    Mirrors NewsAPISyncLog for consistency.
    """

    STATUS_CHOICES = (
        ('started', 'Started'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )

    feed = models.ForeignKey(
        RSSFeed, on_delete=models.CASCADE, null=True, blank=True, related_name='sync_logs'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='started')
    parameters = models.JSONField(default=dict, blank=True)

    articles_found = models.IntegerField(default=0)
    articles_created = models.IntegerField(default=0)
    articles_updated = models.IntegerField(default=0)

    # HTTP response info
    http_status = models.IntegerField(null=True, blank=True)
    was_modified = models.BooleanField(default=True)

    error_message = models.TextField(blank=True)

    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ['-started_at']
        verbose_name = 'RSS Feed Sync Log'
        verbose_name_plural = 'RSS Feed Sync Logs'

    def __str__(self):
        feed_name = self.feed.title if self.feed else 'batch'
        return f"{feed_name} — {self.status} ({self.started_at:%Y-%m-%d %H:%M})"


class RSSArticle(models.Model):
    """
    RSS-specific metadata for an article. One-to-one with the core Article model.
    Stores provenance information linking back to the originating feed.
    """

    article = models.OneToOneField(
        'articles.Article',
        on_delete=models.CASCADE,
        related_name='rss_data',
    )
    feed = models.ForeignKey(
        RSSFeed, on_delete=models.SET_NULL, null=True, related_name='articles'
    )

    # RSS-specific fields
    guid = models.CharField(max_length=1024, blank=True, db_index=True)
    domain = models.CharField(max_length=255, blank=True, null=True, db_index=True)

    # Original entry data
    raw_data = models.JSONField(default=dict)

    # Sync metadata
    sync_log = models.ForeignKey(
        RSSFeedSyncLog,
        on_delete=models.SET_NULL,
        null=True,
        related_name='articles',
    )

    fetched_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['guid']),
            models.Index(fields=['fetched_at']),
        ]
        verbose_name = 'RSS Article'
        verbose_name_plural = 'RSS Articles'

    def __str__(self):
        return f"RSS: {self.article.title[:60]}"
