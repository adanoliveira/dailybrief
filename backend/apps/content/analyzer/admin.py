"""
Django Admin for Article Analyzer models.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import (
    Entity, EntityAlias, Event, ArticleAnalysis, ArticleEntity,
    ArticleEvent, EventEntity, AnalyzerRequest, AnalyzerMetrics
)


@admin.register(Entity)
class EntityAdmin(admin.ModelAdmin):
    list_display = ['display_name', 'entity_type', 'article_count', 'last_seen_at', 'created_at']
    list_filter = ['entity_type', 'created_at', 'last_seen_at']
    search_fields = ['display_name', 'canonical_name']
    readonly_fields = ['public_id', 'canonical_name', 'article_count', 'first_seen_at', 'last_seen_at']
    ordering = ['-last_seen_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('public_id', 'display_name', 'canonical_name', 'entity_type')
        }),
        ('External Links', {
            'fields': ('wikidata_id',)
        }),
        ('Usage Statistics', {
            'fields': ('article_count', 'first_seen_at', 'last_seen_at'),
            'classes': ('collapse',)
        }),
        ('Technical', {
            'fields': ('embedding',),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related()


@admin.register(EntityAlias)
class EntityAliasAdmin(admin.ModelAdmin):
    list_display = ['alias', 'entity', 'alias_type', 'created_at']
    list_filter = ['alias_type', 'created_at']
    search_fields = ['alias', 'entity__display_name']
    autocomplete_fields = ['entity']


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['title', 'article_count', 'first_seen_at', 'last_seen_at', 'created_at']
    list_filter = ['created_at', 'first_seen_at', 'last_seen_at']
    search_fields = ['title', 'abstract']
    readonly_fields = ['public_id', 'event_hash', 'article_count', 'first_seen_at', 'last_seen_at']
    ordering = ['-last_seen_at']
    
    fieldsets = (
        ('Event Information', {
            'fields': ('public_id', 'title', 'abstract')
        }),
        ('Timeline', {
            'fields': ('first_seen_at', 'last_seen_at', 'article_count')
        }),
        ('Technical', {
            'fields': ('event_hash', 'centroid_embed', 'facts'),
            'classes': ('collapse',)
        }),
        ('Integration', {
            'fields': ('story_group',),
            'classes': ('collapse',)
        })
    )


@admin.register(ArticleAnalysis)
class ArticleAnalysisAdmin(admin.ModelAdmin):
    list_display = ['article_title', 'analyzer_version', 'cost_usd', 'processing_time_ms', 'created_at']
    list_filter = ['analyzer_version', 'ai_model_used', 'style_tone', 'created_at']
    search_fields = ['article__title']
    readonly_fields = ['public_id', 'article', 'tokens_input', 'tokens_output', 'processing_time_ms', 'cost_usd']
    
    fieldsets = (
        ('Article', {
            'fields': ('public_id', 'article')
        }),
        ('Processing Info', {
            'fields': ('analyzer_version', 'ai_model_used', 'processing_time_ms', 'cost_usd')
        }),
        ('Token Usage', {
            'fields': ('tokens_input', 'tokens_output'),
            'classes': ('collapse',)
        }),
        ('Confidence Scores', {
            'fields': ('language_confidence', 'primary_topic_confidence', 'primary_region_confidence'),
            'classes': ('collapse',)
        }),
        ('Analysis Results', {
            'fields': ('style_tone',)
        }),
        ('Secondary Classifications', {
            'fields': ('secondary_topics', 'secondary_regions'),
            'classes': ('collapse',)
        }),
        ('Pipeline Tracking', {
            'fields': ('stages_completed',),
            'classes': ('collapse',)
        })
    )
    
    def article_title(self, obj):
        return obj.article.title[:50] + "..." if len(obj.article.title) > 50 else obj.article.title
    article_title.short_description = 'Article'


@admin.register(ArticleEntity)
class ArticleEntityAdmin(admin.ModelAdmin):
    list_display = ['article_title', 'entity_name', 'confidence', 'mention_count', 'created_at']
    list_filter = ['confidence', 'created_at', 'entity__entity_type']
    search_fields = ['article__title', 'entity__display_name']
    autocomplete_fields = ['entity']
    
    def article_title(self, obj):
        return obj.article.title[:30] + "..." if len(obj.article.title) > 30 else obj.article.title
    article_title.short_description = 'Article'
    
    def entity_name(self, obj):
        return obj.entity.display_name
    entity_name.short_description = 'Entity'


@admin.register(ArticleEvent)
class ArticleEventAdmin(admin.ModelAdmin):
    list_display = ['article_title', 'event_title', 'created_at']
    search_fields = ['article__title', 'event__title']
    autocomplete_fields = ['event']
    
    def article_title(self, obj):
        return obj.article.title[:30] + "..." if len(obj.article.title) > 30 else obj.article.title
    article_title.short_description = 'Article'
    
    def event_title(self, obj):
        return obj.event.title[:50] + "..." if len(obj.event.title) > 50 else obj.event.title
    event_title.short_description = 'Event'


@admin.register(EventEntity)
class EventEntityAdmin(admin.ModelAdmin):
    list_display = ['event_title', 'entity_name', 'relevance_score', 'created_at']
    list_filter = ['relevance_score', 'created_at']
    search_fields = ['event__title', 'entity__display_name']
    autocomplete_fields = ['event', 'entity']
    
    def event_title(self, obj):
        return obj.event.title[:30] + "..." if len(obj.event.title) > 30 else obj.event.title
    event_title.short_description = 'Event'
    
    def entity_name(self, obj):
        return obj.entity.display_name
    entity_name.short_description = 'Entity'


@admin.register(AnalyzerRequest)
class AnalyzerRequestAdmin(admin.ModelAdmin):
    list_display = ['article_title', 'status', 'current_stage', 'attempts', 'total_cost_usd', 'created_at']
    list_filter = ['status', 'current_stage', 'created_at']
    search_fields = ['article__title']
    readonly_fields = [
        'public_id', 'article', 'pipeline_start_time', 'pipeline_end_time',
        'total_cost_usd', 'total_duration_ms', 'completed_at'
    ]
    
    fieldsets = (
        ('Request Info', {
            'fields': ('public_id', 'article', 'status', 'current_stage')
        }),
        ('Pipeline Tracking', {
            'fields': ('stages_completed', 'pipeline_start_time', 'pipeline_end_time')
        }),
        ('Error Handling', {
            'fields': ('attempts', 'max_attempts', 'last_error', 'failed_stage'),
            'classes': ('collapse',)
        }),
        ('Performance', {
            'fields': ('total_cost_usd', 'total_duration_ms', 'completed_at'),
            'classes': ('collapse',)
        })
    )
    
    def article_title(self, obj):
        return obj.article.title[:40] + "..." if len(obj.article.title) > 40 else obj.article.title
    article_title.short_description = 'Article'


@admin.register(AnalyzerMetrics)
class AnalyzerMetricsAdmin(admin.ModelAdmin):
    list_display = [
        'date', 'articles_processed', 'success_rate', 'total_cost_usd', 
        'new_entities_created', 'new_events_created'
    ]
    list_filter = ['date']
    readonly_fields = [
        'date', 'articles_processed', 'articles_failed', 'success_rate',
        'total_cost_usd', 'avg_cost_per_article', 'avg_duration_ms', 'avg_tokens_used',
        'new_entities_created', 'entity_deduplication_rate',
        'new_events_created', 'event_clustering_rate',
        'topic_assignment_rate', 'region_assignment_rate'
    ]
    
    fieldsets = (
        ('Date', {
            'fields': ('date',)
        }),
        ('Volume Metrics', {
            'fields': ('articles_processed', 'articles_failed', 'success_rate')
        }),
        ('Cost Metrics', {
            'fields': ('total_cost_usd', 'avg_cost_per_article')
        }),
        ('Performance Metrics', {
            'fields': ('avg_duration_ms', 'avg_tokens_used')
        }),
        ('Entity Metrics', {
            'fields': ('new_entities_created', 'entity_deduplication_rate')
        }),
        ('Event Metrics', {
            'fields': ('new_events_created', 'event_clustering_rate')
        }),
        ('Classification Metrics', {
            'fields': ('topic_assignment_rate', 'region_assignment_rate')
        }),
        ('Pipeline Failure Metrics', {
            'fields': (
                'linguistic_failures', 'entity_failures', 'event_failures',
                'topic_failures', 'region_failures'
            ),
            'classes': ('collapse',)
        })
    ) 