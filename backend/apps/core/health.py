"""
Health check endpoint for monitoring services (Railway, etc.).
"""
from django.utils import timezone
from django.db import connection
from django.conf import settings
import os

from .api_utils import api_view, create_response


@api_view(['GET'], authenticate=False)
def health_check(request):
    """
    Health check endpoint for monitoring services.
    
    Returns basic system status and version information.
    No authentication required for monitoring purposes.
    """
    status = "healthy"
    checks = {}
    
    # Database connectivity check
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        checks["database"] = {"status": "ok", "message": "Database connection successful"}
    except Exception as e:
        checks["database"] = {"status": "error", "message": str(e)}
        status = "unhealthy"
    
    # Redis connectivity check (for Celery)
    try:
        import redis
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        r = redis.from_url(redis_url)
        r.ping()
        checks["redis"] = {"status": "ok", "message": "Redis connection successful"}
    except Exception as e:
        checks["redis"] = {"status": "error", "message": str(e)}
        status = "unhealthy"
    
    # Basic Django settings check
    checks["django"] = {
        "status": "ok", 
        "debug": settings.DEBUG,
        "version": "5.0.2"
    }
    
    data = {
        "status": status,
        "timestamp": timezone.now().isoformat(),
        "version": "1.0.0",
        "service": "dailybrief-backend",
        "checks": checks
    }
    
    # Return 200 for healthy, 503 for unhealthy
    response_status = 200 if status == "healthy" else 503
    return create_response(data, status=response_status) 