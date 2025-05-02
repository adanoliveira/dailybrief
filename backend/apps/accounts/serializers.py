from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile

class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for the UserProfile model."""
    
    class Meta:
        model = UserProfile
        fields = ['public_id', 'timezone', 'created_at', 'updated_at']
        read_only_fields = ['public_id', 'created_at', 'updated_at']


class UserSerializer(serializers.ModelSerializer):
    """Serializer for the User model with profile data."""
    
    profile = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'profile', 'date_joined']
        read_only_fields = ['id', 'date_joined'] 