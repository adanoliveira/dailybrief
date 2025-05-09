from django.shortcuts import render
import json
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import user_passes_test

from apps.newsapi.models import NewsAPISyncLog

# Create your views here.

@csrf_exempt
@require_http_methods(["GET"])
@user_passes_test(lambda u: u.is_staff)
def sync_status(request):
    """
    View to check the status of recent sync operations.
    Only accessible to staff users.
    """
    # Get the most recent sync logs
    recent_logs = NewsAPISyncLog.objects.order_by('-started_at')[:10]
    
    # Format the logs as a list of dictionaries
    logs_data = [
        {
            'id': log.id,
            'sync_type': log.sync_type,
            'status': log.status,
            'started_at': log.started_at.isoformat() if log.started_at else None,
            'completed_at': log.completed_at.isoformat() if log.completed_at else None,
            'duration_seconds': log.duration_seconds,
            'articles_found': log.articles_found,
            'articles_created': log.articles_created,
            'articles_updated': log.articles_updated,
            'error_message': log.error_message if log.error_message else None,
        }
        for log in recent_logs
    ]
    
    return JsonResponse({
        'success': True,
        'logs': logs_data
    })

@csrf_exempt
@require_http_methods(["POST"])
@user_passes_test(lambda u: u.is_staff)
def trigger_sync(request):
    """
    View to manually trigger a sync operation.
    Only accessible to staff users.
    """
    try:
        from apps.newsapi.tasks import sync_headlines, sync_recent_articles, sync_by_publication
        
        data = json.loads(request.body)
        sync_type = data.get('sync_type', 'headlines')
        
        if sync_type == 'headlines':
            task = sync_headlines.delay()
            task_id = task.id
        elif sync_type == 'recent':
            hours = data.get('hours', 1)
            task = sync_recent_articles.delay(hours=hours)
            task_id = task.id
        elif sync_type == 'publication':
            days = data.get('days', 1)
            task = sync_by_publication.delay(days=days)
            task_id = task.id
        else:
            return JsonResponse({
                'success': False,
                'error': f'Unknown sync type: {sync_type}'
            }, status=400)
        
        return JsonResponse({
            'success': True,
            'message': f'Started {sync_type} sync',
            'task_id': task_id
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
