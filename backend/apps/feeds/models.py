from django.db import models
from django.contrib.auth.models import User
import uuid


class Topic(models.Model):
    """
    Topics/categories for news articles (e.g., business, entertainment, general, etc.).
    """
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True, help_text="Description to help AI models with classification")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Region(models.Model):
    """
    Regions for news sources (e.g., us, gb, fr, etc.).
    """
    code = models.CharField(max_length=5, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, help_text="Description to help AI models with classification")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.code})"


class Language(models.Model):
    """
    Languages for news articles (e.g., en, fr, es, etc.).
    """
    iso_code = models.CharField(max_length=5, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, help_text="Description to help AI models with classification")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.iso_code})"


class Publication(models.Model):
    """
    News publications/sources.
    """
    name = models.CharField(max_length=255)
    news_api_id = models.CharField(max_length=255, null=True, blank=True)
    domain = models.CharField(max_length=255, null=True, blank=True, db_index=True, 
                             help_text="Normalized domain name (e.g., nytimes.com)")
    rss_url = models.URLField(null=True, blank=True)
    website_url = models.URLField()
    logo_url = models.URLField(null=True, blank=True)
    description = models.TextField(blank=True)
    authority = models.FloatField(default=1.0)  # Weight for ranking
    topics = models.ManyToManyField(Topic, related_name='publications', blank=True)
    languages = models.ManyToManyField(Language, related_name='publications', blank=True)
    regions = models.ManyToManyField(Region, related_name='publications', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


# User preferences models
class UserTopic(models.Model):
    """
    User's preferred topics.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='preferred_topics')
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='users')
    weight = models.FloatField(default=1.0)  # For personalized ranking
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'topic')

    def __str__(self):
        return f"{self.user.username} - {self.topic.name}"


class UserPublication(models.Model):
    """
    User's preferred publications.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='preferred_publications')
    publication = models.ForeignKey(Publication, on_delete=models.CASCADE, related_name='users')
    weight = models.FloatField(default=1.0)  # For personalized ranking
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'publication')

    def __str__(self):
        return f"{self.user.username} - {self.publication.name}"


class UserRegion(models.Model):
    """
    User's preferred regions.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='preferred_regions')
    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name='users')
    weight = models.FloatField(default=1.0)  # For personalized ranking
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'region')

    def __str__(self):
        return f"{self.user.username} - {self.region.name}"


class UserLanguage(models.Model):
    """
    User's preferred languages.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='preferred_languages')
    language = models.ForeignKey(Language, on_delete=models.CASCADE, related_name='users')
    weight = models.FloatField(default=1.0)  # For personalized ranking
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'language')

    def __str__(self):
        return f"{self.user.username} - {self.language.name}"
