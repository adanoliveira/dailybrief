from rest_framework import serializers
from .models import Topic, Region, Language, Publication

class TopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topic
        fields = ['id', 'name', 'slug']

class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = ['id', 'code', 'name']

class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = ['id', 'iso_code', 'name']

class PublicationSerializer(serializers.ModelSerializer):
    # Use primary key related fields to avoid circular references
    topics = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    regions = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    languages = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    
    class Meta:
        model = Publication
        fields = [
            'id', 'name', 'website_url', 'logo_url', 
            'description', 'authority', 'news_api_id',
            'topics', 'regions', 'languages'
        ] 