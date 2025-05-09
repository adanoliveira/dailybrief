from django.contrib import admin
from .models import NewsAPIRequest, NewsAPISyncLog

@admin.register(NewsAPIRequest)
class NewsAPIRequestAdmin(admin.ModelAdmin):
    list_display = ('request_type', 'endpoint', 'status_code', 'success', 'created_at')
    list_filter = ('request_type', 'success', 'created_at')
    search_fields = ('endpoint', 'error_message')
    readonly_fields = ('created_at',)
    fieldsets = (
        ('Request', {
            'fields': ('request_type', 'endpoint', 'params')
        }),
        ('Response', {
            'fields': ('status_code', 'success', 'error_message', 'total_results', 'results_fetched')
        }),
        ('Rate Limits', {
            'fields': ('rate_limit_remaining', 'rate_limit_reset')
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )


@admin.register(NewsAPISyncLog)
class NewsAPISyncLogAdmin(admin.ModelAdmin):
    list_display = ('sync_type', 'status', 'started_at', 'completed_at', 'articles_created')
    list_filter = ('sync_type', 'status', 'started_at')
    search_fields = ('error_message',)
    readonly_fields = ('started_at', 'duration_seconds')
    fieldsets = (
        ('Sync Info', {
            'fields': ('sync_type', 'status', 'parameters')
        }),
        ('Results', {
            'fields': ('articles_found', 'articles_created', 'articles_updated', 'error_message')
        }),
        ('Timing', {
            'fields': ('started_at', 'completed_at', 'duration_seconds')
        }),
    )
