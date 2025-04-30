from django.db import models
from django.contrib.auth.models import User
import uuid


class UserNotificationSettings(models.Model):
    """
    User preferences for notifications.
    """
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='notification_settings'
    )
    
    # Email notification preferences
    email_digest = models.BooleanField(default=True, help_text="Send daily digest via email")
    email_news_updates = models.BooleanField(default=False, help_text="Send email for important news updates")
    
    # Push notification preferences
    push_enabled = models.BooleanField(default=True, help_text="Enable push notifications")
    push_digest = models.BooleanField(default=True, help_text="Send push notification for daily digest")
    push_news_updates = models.BooleanField(default=False, help_text="Send push for important news updates")
    
    # Timing preferences
    preferred_time = models.TimeField(default='08:00', help_text="Preferred time to receive digest")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username}'s notification settings"


class PushSubscription(models.Model):
    """
    User's push notification subscriptions.
    Stores the subscription info needed for Web Push API.
    """
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='push_subscriptions'
    )
    
    # Subscription data
    endpoint = models.URLField(max_length=500)
    p256dh = models.CharField(max_length=255)
    auth = models.CharField(max_length=255)
    
    # Device info
    browser = models.CharField(max_length=100, blank=True)
    device = models.CharField(max_length=100, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('user', 'endpoint')
    
    def __str__(self):
        return f"{self.user.username}'s subscription on {self.device} {self.browser}"


class Notification(models.Model):
    """
    Record of notifications sent to users.
    """
    NOTIFICATION_TYPES = (
        ('digest', 'Daily Digest'),
        ('news_update', 'News Update'),
        ('system', 'System Notification'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('read', 'Read'),
    )
    
    public_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    
    # Notification content
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=255)
    body = models.TextField()
    
    # Optional link to content
    action_url = models.URLField(blank=True)
    
    # Delivery channels
    email_sent = models.BooleanField(default=False)
    push_sent = models.BooleanField(default=False)
    in_app_shown = models.BooleanField(default=False)
    
    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['public_id']),
        ]
    
    def __str__(self):
        return f"{self.notification_type} for {self.user.username}: {self.title}"
