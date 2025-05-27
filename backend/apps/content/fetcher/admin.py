from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import ContentFetchLog, FetchAttempt


@admin.register(ContentFetchLog)
class ContentFetchLogAdmin(admin.ModelAdmin):
    """Admin interface for ContentFetchLog model."""
    
    list_display = [
        'article_id', 'article_link', 'status', 'attempt_number', 
        'extraction_strategy', 'content_quality_score', 'paywall_detected',
        'duration_display', 'created_at'
    ]
    list_filter = [
        'status', 'extraction_strategy', 'paywall_detected', 
        'has_main_content', 'created_at'
    ]
    search_fields = ['article_id', 'article_url', 'error_message']
    readonly_fields = [
        'article_id', 'article_url', 'started_at', 'completed_at', 
        'created_at', 'duration_display'
    ]
    ordering = ['-created_at']
    
    fieldsets = (
        ('Article Information', {
            'fields': ('article_id', 'article_link', 'article_url')
        }),
        ('Fetch Details', {
            'fields': (
                'status', 'attempt_number', 'extraction_strategy',
                'started_at', 'completed_at', 'duration_display'
            )
        }),
        ('Content Results', {
            'fields': (
                'content_source', 'content_length', 'content_quality_score',
                'extracted_text_length', 'has_main_content', 'content_completeness'
            )
        }),
        ('Technical Details', {
            'fields': (
                'response_status_code', 'response_time_ms', 'user_agent_used'
            ),
            'classes': ('collapse',)
        }),
        ('Error Information', {
            'fields': ('error_message', 'error_type'),
            'classes': ('collapse',)
        }),
        ('Paywall Detection', {
            'fields': ('paywall_detected', 'paywall_indicators'),
            'classes': ('collapse',)
        }),
    )
    
    def article_link(self, obj):
        """Create a link to the article in admin."""
        if obj.article_id:
            url = reverse('admin:articles_article_change', args=[obj.article_id])
            return format_html('<a href="{}" target="_blank">Article {}</a>', url, obj.article_id)
        return "N/A"
    article_link.short_description = "Article"
    
    def duration_display(self, obj):
        """Display the duration of the fetch attempt."""
        duration = obj.duration_ms
        if duration is not None:
            if duration < 1000:
                return f"{duration}ms"
            else:
                return f"{duration/1000:.1f}s"
        return "N/A"
    duration_display.short_description = "Duration"
    
    def get_queryset(self, request):
        """Optimize queryset for admin display."""
        return super().get_queryset(request).select_related()


@admin.register(FetchAttempt)
class FetchAttemptAdmin(admin.ModelAdmin):
    """Admin interface for FetchAttempt model."""
    
    list_display = [
        'article_id', 'article_link', 'attempts', 'max_attempts',
        'is_completed', 'final_status', 'next_retry_display', 'updated_at'
    ]
    list_filter = ['is_completed', 'final_status', 'created_at', 'updated_at']
    search_fields = ['article_id', 'final_status']
    readonly_fields = ['article_id', 'created_at', 'updated_at']
    ordering = ['-updated_at']
    
    fieldsets = (
        ('Article Information', {
            'fields': ('article_id', 'article_link')
        }),
        ('Attempt Tracking', {
            'fields': ('attempts', 'max_attempts', 'last_attempt_at')
        }),
        ('Retry Scheduling', {
            'fields': ('next_retry_at', 'next_retry_display')
        }),
        ('Status', {
            'fields': ('is_completed', 'final_status')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def article_link(self, obj):
        """Create a link to the article in admin."""
        if obj.article_id:
            url = reverse('admin:articles_article_change', args=[obj.article_id])
            return format_html('<a href="{}" target="_blank">Article {}</a>', url, obj.article_id)
        return "N/A"
    article_link.short_description = "Article"
    
    def next_retry_display(self, obj):
        """Display next retry time in a readable format."""
        if obj.next_retry_at:
            from django.utils import timezone
            now = timezone.now()
            if obj.next_retry_at > now:
                delta = obj.next_retry_at - now
                hours = delta.total_seconds() / 3600
                if hours < 1:
                    minutes = delta.total_seconds() / 60
                    return f"In {minutes:.0f} minutes"
                else:
                    return f"In {hours:.1f} hours"
            else:
                return "Ready now"
        return "No retry scheduled"
    next_retry_display.short_description = "Next Retry"
    
    def get_queryset(self, request):
        """Optimize queryset for admin display."""
        return super().get_queryset(request).select_related()
    
    actions = ['mark_for_retry', 'mark_completed']
    
    def mark_for_retry(self, request, queryset):
        """Mark selected attempts for immediate retry."""
        from django.utils import timezone
        updated = queryset.filter(is_completed=False).update(
            next_retry_at=timezone.now(),
            is_completed=False
        )
        self.message_user(request, f"Marked {updated} attempts for immediate retry.")
    mark_for_retry.short_description = "Mark for immediate retry"
    
    def mark_completed(self, request, queryset):
        """Mark selected attempts as completed."""
        updated = queryset.update(
            is_completed=True,
            final_status='admin_completed',
            next_retry_at=None
        )
        self.message_user(request, f"Marked {updated} attempts as completed.")
    mark_completed.short_description = "Mark as completed"
