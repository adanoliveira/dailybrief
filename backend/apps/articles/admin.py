from django.contrib import admin

from .models import HeadlineCluster


@admin.register(HeadlineCluster)
class HeadlineClusterAdmin(admin.ModelAdmin):
    list_display = [
        'representative_title', 'article_count', 'burst_score',
        'language', 'is_active', 'first_seen', 'last_updated',
    ]
    list_filter = ['is_active', 'language']
    search_fields = ['representative_title']
    readonly_fields = ['first_seen', 'last_updated', 'created_at']
