from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile

class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for the UserProfile model."""
    
    class Meta:
        model = UserProfile
        fields = ['public_id', 'timezone', 'onboarding_completed', 'created_at', 'updated_at']
        read_only_fields = ['public_id', 'created_at', 'updated_at']


class UserSerializer(serializers.ModelSerializer):
    """Serializer for the User model with profile data."""
    
    profile = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'profile', 'date_joined']
        read_only_fields = ['id', 'date_joined']


class OnboardingDataSerializer(serializers.Serializer):
    """Serializer for onboarding data."""
    
    topics = serializers.ListField(
        child=serializers.IntegerField(),
        required=True,
        help_text="List of topic IDs"
    )
    regions = serializers.ListField(
        child=serializers.CharField(),
        required=True,
        help_text="List of region codes"
    )
    languages = serializers.ListField(
        child=serializers.CharField(),
        required=True,
        help_text="List of language ISO codes"
    )
    publications = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text="List of publication IDs"
    ) 