from django.db import models
from django.contrib.auth.models import User
import uuid


class UserProfile(models.Model):
    """
    Extended user profile with additional fields for DailyBrief.
    Uses Django's built-in User model and extends it with a one-to-one field.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    public_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    timezone = models.CharField(max_length=50, default='UTC')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s profile"
