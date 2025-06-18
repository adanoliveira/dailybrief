from django.shortcuts import render
import json
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import user_passes_test

# NEW: Import enhanced API utilities
from apps.core.api_utils import (
    api_view, create_response, create_error_response, 
    parse_request_body
)

from apps.newsapi.models import NewsAPISyncLog

# Create your views here.

@api_view(['GET'], staff_required=True)
def sync_status(request):
    """
    View to check the status of recent sync operations.
    Only accessible to staff users.
    """
    user = request.user  # Guaranteed to be staff by @api_view
    
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
    
    return create_response({
        'logs': logs_data,
        'total_logs': len(logs_data)
    })

@api_view(['POST'], staff_required=True)
def trigger_sync(request):
    """
    View to manually trigger a sync operation.
    Only accessible to staff users.
    """
    user = request.user  # Guaranteed to be staff by @api_view
    
    # Parse request body
    data, error = parse_request_body(request)
    if error:
        return error
    
    sync_type = data.get('sync_type', 'headlines')
    
    # Validate sync_type
    valid_sync_types = ['headlines', 'recent', 'publication']
    if sync_type not in valid_sync_types:
        return create_error_response(
            f'Invalid sync_type: {sync_type}',
            status=400,
            error_code='INVALID_SYNC_TYPE',
            details={
                'valid_types': valid_sync_types,
                'received': sync_type
            }
        )
    
    try:
        from apps.newsapi.tasks import sync_headlines, sync_recent_articles, sync_by_publication
        
        if sync_type == 'headlines':
            task = sync_headlines.delay()
            task_id = task.id
            message = 'Started headlines sync'
        elif sync_type == 'recent':
            hours = data.get('hours', 1)
            # Validate hours parameter
            if not isinstance(hours, int) or hours < 1 or hours > 24:
                return create_error_response(
                    'Hours must be an integer between 1 and 24',
                    status=400,
                    error_code='INVALID_HOURS_PARAMETER'
                )
            task = sync_recent_articles.delay(hours=hours)
            task_id = task.id
            message = f'Started recent articles sync ({hours} hours)'
        elif sync_type == 'publication':
            days = data.get('days', 1)
            # Validate days parameter
            if not isinstance(days, int) or days < 1 or days > 7:
                return create_error_response(
                    'Days must be an integer between 1 and 7',
                    status=400,
                    error_code='INVALID_DAYS_PARAMETER'
                )
            task = sync_by_publication.delay(days=days)
            task_id = task.id
            message = f'Started publication sync ({days} days)'
        
        return create_response({
            'message': message,
            'task_id': task_id,
            'sync_type': sync_type,
            'triggered_by': user.email
        })
        
    except ImportError as e:
        return create_error_response(
            'Sync tasks not available',
            status=503,
            error_code='TASKS_UNAVAILABLE',
            details={'import_error': str(e)}
        )
    except Exception as e:
        return create_error_response(
            f'Failed to trigger sync: {str(e)}',
            status=500,
            error_code='SYNC_TRIGGER_FAILED'
        )
