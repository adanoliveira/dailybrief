from django.contrib import admin

from .models import RSSFeed, RSSArticle, RSSFeedSyncLog


@admin.register(RSSFeed)
class RSSFeedAdmin(admin.ModelAdmin):
    list_display = [
        'publication', 'title', 'status', 'priority', 'topic', 'region',
        'last_fetched_at', 'consecutive_errors',
    ]
    list_filter = ['status', 'priority', 'topic', 'region']
    search_fields = ['title', 'feed_url', 'publication__name']
    readonly_fields = ['etag', 'last_modified', 'last_fetched_at', 'last_successful_fetch_at', 'feed_type']
    actions = ['activate_feeds', 'pause_feeds', 'reset_errors']

    @admin.action(description='Activate selected feeds')
    def activate_feeds(self, request, queryset):
        queryset.update(status='active', consecutive_errors=0)

    @admin.action(description='Pause selected feeds')
    def pause_feeds(self, request, queryset):
        queryset.update(status='paused')

    @admin.action(description='Reset error counters')
    def reset_errors(self, request, queryset):
        queryset.update(consecutive_errors=0, last_error_message='', status='active')


@admin.register(RSSArticle)
class RSSArticleAdmin(admin.ModelAdmin):
    list_display = ['article', 'feed', 'domain', 'guid', 'fetched_at']
    list_filter = ['feed__publication']
    search_fields = ['article__title', 'guid', 'domain']
    raw_id_fields = ['article', 'feed', 'sync_log']


@admin.register(RSSFeedSyncLog)
class RSSFeedSyncLogAdmin(admin.ModelAdmin):
    list_display = [
        'feed', 'status', 'articles_found', 'articles_created',
        'was_modified', 'duration_seconds', 'started_at',
    ]
    list_filter = ['status', 'was_modified']
    search_fields = ['feed__title', 'feed__publication__name']
    readonly_fields = ['started_at']
