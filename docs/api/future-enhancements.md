# API Infrastructure Enhancement Ideas

This document outlines potential enhancements to the DailyBrief API infrastructure and frontend/backend communication. These are **not currently implemented** but documented for future consideration when scaling or improving the system.

## Status: 📋 Ideas & Planning
- **Current State**: Basic API standardization completed, frontend/backend communication working
- **Priority**: Future enhancements (post-MVP)
- **Implementation**: Consider based on actual usage patterns and performance needs

---

## 1. Request Tracing & Correlation IDs

### Purpose
Enable end-to-end request tracking across frontend/backend for better debugging and monitoring.

### Implementation Ideas
```python
# Backend: Add to @api_view decorator
import uuid

def api_view(...):
    def wrapper(request, *args, **kwargs):
        # Add correlation ID for request tracing
        correlation_id = str(uuid.uuid4())
        request.correlation_id = correlation_id
        
        # Add to all responses
        response = view_func(request, *args, **kwargs)
        response["X-Correlation-ID"] = correlation_id
        return response
```

```typescript
// Frontend: Add to api-client.ts
export const apiClient = {
    async request(config) {
        const correlationId = crypto.randomUUID();
        config.headers['X-Correlation-ID'] = correlationId;
        
        try {
            const response = await axios(config);
            console.log(`[${correlationId}] API success:`, response.data);
            return response;
        } catch (error) {
            console.error(`[${correlationId}] API error:`, error);
            throw error;
        }
    }
};
```

### Benefits
- **Debugging**: Trace requests across logs
- **Monitoring**: Track request flows
- **Support**: Quick issue identification

### When to Implement
- When debugging becomes difficult across services
- When implementing proper monitoring/observability
- When support needs request tracing

---

## 2. Performance Monitoring & Metrics

### Purpose
Track API response times and system performance automatically.

### Implementation Ideas
```python
# Backend: Add timing to @api_view
def api_view(...):
    def wrapper(request, *args, **kwargs):
        start_time = time.time()
        
        response = view_func(request, *args, **kwargs)
        
        # Add performance headers
        response_time = (time.time() - start_time) * 1000
        response["X-Response-Time"] = f"{response_time:.2f}ms"
        
        # Log slow requests
        if response_time > 1000:  # > 1 second
            logger.warning(f"Slow request: {request.path} took {response_time:.2f}ms")
        
        return response
```

```typescript
// Frontend: Performance tracking
class APIPerformanceTracker {
    static trackRequest(endpoint: string, duration: number) {
        if (duration > 2000) {  // > 2 seconds
            console.warn(`Slow API call: ${endpoint} took ${duration}ms`);
        }
        
        // Could send to analytics service
        // analytics.track('api_performance', { endpoint, duration });
    }
}
```

### Benefits
- **Performance insights**: Identify slow endpoints
- **User experience**: Monitor frontend performance
- **Optimization**: Data-driven improvements

### When to Implement
- When performance becomes a concern
- When implementing analytics/monitoring
- When optimizing user experience

---

## 3. API Rate Limiting

### Purpose
Protect API endpoints from abuse and ensure fair usage.

### Implementation Ideas
```python
# Backend: Rate limiting decorator
from django.core.cache import cache

def rate_limit(limit=100, window=3600, skip_auth=False):
    """
    Rate limiting decorator for API views.
    
    Args:
        limit: Maximum requests allowed in the time window
        window: Time window in seconds (default: 1 hour)  
        skip_auth: Skip rate limiting for authenticated users
    """
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if skip_auth and request.user.is_authenticated:
                return view_func(request, *args, **kwargs)
            
            # Generate rate limit key
            ip_address = request.META.get('REMOTE_ADDR', 'unknown')
            user_id = request.user.id if request.user.is_authenticated else 'anonymous'
            cache_key = f"rate_limit:{ip_address}:{user_id}"
            
            # Check current count
            current_count = cache.get(cache_key, 0)
            
            if current_count >= limit:
                return create_error_response(
                    "Rate limit exceeded",
                    status=429,
                    error_code="RATE_LIMIT_EXCEEDED",
                    details={
                        "limit": limit,
                        "window_seconds": window,
                        "retry_after": window
                    }
                )
            
            # Increment count
            cache.set(cache_key, current_count + 1, timeout=window)
            return view_func(request, *args, **kwargs)
            
        return wrapper
    return decorator

# Usage
@rate_limit(limit=60, window=60)  # 60 requests per minute
@api_view(['GET'])
def public_endpoint(request):
    return create_response({'data': 'success'})
```

```typescript
// Frontend: Handle rate limit responses
export const handleRateLimit = (error: AxiosError) => {
    if (error.response?.status === 429) {
        const retryAfter = error.response.data?.details?.retry_after || 60;
        
        // Show user-friendly message
        toast.error(`Too many requests. Please try again in ${retryAfter} seconds.`);
        
        // Could implement automatic retry with backoff
        // setTimeout(() => retryRequest(), retryAfter * 1000);
    }
};
```

### Benefits
- **Security**: Prevent API abuse
- **Stability**: Protect system resources
- **Fair usage**: Ensure service availability

### When to Implement
- When API usage grows significantly
- When experiencing abuse or high load
- When moving to production with public endpoints

---

## 4. Health Checks & System Monitoring

### Purpose
Provide endpoints for monitoring system health and performance.

### Implementation Ideas
```python
# Backend: Health check endpoints
@api_view(['GET'], authenticate=False)
def health_check(request):
    """Comprehensive health check for load balancers and monitoring."""
    start_time = time.time()
    
    health_data = {
        "status": "healthy",
        "timestamp": timezone.now().isoformat(),
        "version": settings.API_VERSION,
        "environment": "development" if settings.DEBUG else "production",
        "checks": {}
    }
    
    # Database connectivity
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        health_data["checks"]["database"] = {"status": "healthy"}
    except Exception as e:
        health_data["checks"]["database"] = {"status": "unhealthy", "error": str(e)}
        health_data["status"] = "degraded"
    
    # Cache connectivity  
    try:
        cache.set("health_check", "ok", timeout=60)
        cache_value = cache.get("health_check")
        if cache_value == "ok":
            health_data["checks"]["cache"] = {"status": "healthy"}
        else:
            health_data["checks"]["cache"] = {"status": "unhealthy"}
            health_data["status"] = "degraded"
    except Exception as e:
        health_data["checks"]["cache"] = {"status": "unhealthy", "error": str(e)}
        health_data["status"] = "degraded"
    
    # Response time
    health_data["response_time_ms"] = round((time.time() - start_time) * 1000, 2)
    
    status_code = 200 if health_data["status"] == "healthy" else 503
    return create_success_response(health_data, status=status_code)

@api_view(['GET'], authenticate=False)
def ping(request):
    """Simple ping for basic connectivity."""
    return create_success_response({
        "message": "pong",
        "timestamp": timezone.now().isoformat()
    })
```

### URL Configuration
```python
# urls.py
urlpatterns = [
    path('api/health/', health_check, name='health_check'),
    path('api/ping/', ping, name='ping'),
    # ... other endpoints
]
```

### Benefits
- **Monitoring**: System health visibility
- **Load balancing**: Health check endpoints
- **DevOps**: Automated monitoring integration

### When to Implement
- When deploying to production
- When implementing load balancing
- When setting up monitoring/alerting

---

## 5. Enhanced Error Handling & Logging

### Purpose
Improve error visibility and debugging capabilities.

### Implementation Ideas
```python
# Backend: Enhanced error logging
import structlog

logger = structlog.get_logger(__name__)

def api_view(...):
    def wrapper(request, *args, **kwargs):
        try:
            return view_func(request, *args, **kwargs)
        except Exception as e:
            # Structured logging
            logger.error(
                "API error occurred",
                view_function=view_func.__name__,
                request_path=request.path,
                request_method=request.method,
                user_id=getattr(request.user, 'id', None),
                error_type=type(e).__name__,
                error_message=str(e),
                traceback=traceback.format_exc()
            )
            
            # Return appropriate error response
            if settings.DEBUG:
                return create_error_response(
                    f"Internal server error: {str(e)}",
                    status=500,
                    details={
                        "exception_type": type(e).__name__,
                        "view_function": view_func.__name__
                    }
                )
            else:
                return create_error_response(
                    "An internal error occurred. Please try again.",
                    status=500
                )
```

```typescript
// Frontend: Enhanced error handling
class APIErrorHandler {
    static handle(error: AxiosError, context: string) {
        const errorData = {
            context,
            endpoint: error.config?.url,
            method: error.config?.method,
            status: error.response?.status,
            message: error.message,
            timestamp: new Date().toISOString()
        };
        
        // Log to console in development
        if (process.env.NODE_ENV === 'development') {
            console.error('API Error:', errorData);
        }
        
        // Could send to error tracking service
        // errorTracker.captureException(error, errorData);
        
        // Show user-friendly message
        this.showUserMessage(error);
    }
    
    private static showUserMessage(error: AxiosError) {
        if (error.response?.status === 429) {
            toast.error('Too many requests. Please try again later.');
        } else if (error.response?.status >= 500) {
            toast.error('Server error. Please try again.');
        } else if (error.response?.status === 401) {
            toast.error('Please log in to continue.');
        } else {
            toast.error('Something went wrong. Please try again.');
        }
    }
}
```

### Benefits
- **Debugging**: Better error visibility
- **User experience**: Friendly error messages
- **Monitoring**: Error tracking and alerting

### When to Implement
- When debugging becomes challenging
- When implementing error tracking
- When improving user experience

---

## 6. API Versioning Strategy

### Purpose
Enable API evolution without breaking existing clients.

### Implementation Ideas
```python
# Backend: URL-based versioning
# urls.py
urlpatterns = [
    path('api/v1/', include('apps.api.v1.urls')),
    path('api/v2/', include('apps.api.v2.urls')),  # Future version
]

# Header-based versioning alternative
def api_version(supported_versions=['1.0']):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            version = request.META.get('HTTP_API_VERSION', '1.0')
            
            if version not in supported_versions:
                return create_error_response(
                    f"Unsupported API version: {version}",
                    status=400,
                    details={"supported_versions": supported_versions}
                )
            
            request.api_version = version
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
```

```typescript
// Frontend: Version management
export const API_CONFIG = {
    version: '1.0',
    baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
    
    // Version-specific endpoints
    endpoints: {
        v1: {
            articles: '/api/v1/articles',
            feeds: '/api/v1/feeds'
        }
    }
};

// Add version header to requests
apiClient.defaults.headers['API-Version'] = API_CONFIG.version;
```

### Benefits
- **Backward compatibility**: Support multiple versions
- **Gradual migration**: Smooth API evolution
- **Client flexibility**: Version selection

### When to Implement
- When API changes might break clients
- When supporting mobile apps
- When planning major API changes

---

## 7. Caching Strategy

### Purpose
Improve API response times and reduce database load.

### Implementation Ideas
```python
# Backend: Response caching
from django.core.cache import cache
from django.utils.cache import make_template_fragment_key

def cache_response(timeout=300, key_func=None):
    """Cache API responses."""
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(request, *args, **kwargs)
            else:
                cache_key = f"api:{request.path}:{request.GET.urlencode()}"
            
            # Check cache
            cached_response = cache.get(cache_key)
            if cached_response:
                response = JsonResponse(cached_response)
                response["X-Cache"] = "HIT"
                return response
            
            # Generate response
            response = view_func(request, *args, **kwargs)
            
            # Cache successful responses
            if response.status_code == 200:
                cache.set(cache_key, response.data, timeout=timeout)
                response["X-Cache"] = "MISS"
            
            return response
        return wrapper
    return decorator

# Usage
@cache_response(timeout=600)  # 10 minutes
@api_view(['GET'])
def get_topics(request):
    # This response will be cached
    return create_response({'topics': Topic.objects.all()})
```

```typescript
// Frontend: Client-side caching
class APICache {
    private static cache = new Map<string, {data: any, expires: number}>();
    
    static get(key: string) {
        const cached = this.cache.get(key);
        if (cached && cached.expires > Date.now()) {
            return cached.data;
        }
        this.cache.delete(key);
        return null;
    }
    
    static set(key: string, data: any, ttl: number = 300000) { // 5 minutes default
        this.cache.set(key, {
            data,
            expires: Date.now() + ttl
        });
    }
    
    static clear() {
        this.cache.clear();
    }
}

// Usage in API calls
export async function getTopics() {
    const cacheKey = 'topics';
    const cached = APICache.get(cacheKey);
    
    if (cached) {
        return cached;
    }
    
    const response = await apiClient.get('/api/feeds/topics/');
    APICache.set(cacheKey, response.data);
    return response.data;
}
```

### Benefits
- **Performance**: Faster response times
- **Scalability**: Reduced database load
- **User experience**: Quicker page loads

### When to Implement
- When API responses are slow
- When database queries are expensive
- When scaling to more users

---

## 8. Real-time Updates (WebSockets)

### Purpose
Enable real-time data updates without polling.

### Implementation Ideas
```python
# Backend: Django Channels for WebSockets
# consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer

class ArticleUpdatesConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("articles", self.channel_name)
        await self.accept()
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("articles", self.channel_name)
    
    async def article_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'article_update',
            'article': event['article']
        }))

# Send updates when articles are added
from channels.layers import get_channel_layer

def notify_article_added(article):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "articles",
        {
            'type': 'article_update',
            'article': serialize_article(article)
        }
    )
```

```typescript
// Frontend: WebSocket integration
class WebSocketManager {
    private ws: WebSocket | null = null;
    private callbacks: Map<string, Function[]> = new Map();
    
    connect() {
        this.ws = new WebSocket('ws://localhost:8000/ws/articles/');
        
        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleMessage(data);
        };
        
        this.ws.onopen = () => {
            console.log('WebSocket connected');
        };
        
        this.ws.onclose = () => {
            console.log('WebSocket disconnected');
            // Implement reconnection logic
        };
    }
    
    subscribe(event: string, callback: Function) {
        if (!this.callbacks.has(event)) {
            this.callbacks.set(event, []);
        }
        this.callbacks.get(event)!.push(callback);
    }
    
    private handleMessage(data: any) {
        const callbacks = this.callbacks.get(data.type) || [];
        callbacks.forEach(callback => callback(data));
    }
}

// Usage
const wsManager = new WebSocketManager();
wsManager.connect();

wsManager.subscribe('article_update', (data) => {
    // Update UI with new article
    updateArticlesList(data.article);
});
```

### Benefits
- **Real-time**: Instant updates
- **Engagement**: Better user experience
- **Efficiency**: No unnecessary polling

### When to Implement
- When real-time updates are needed
- When implementing collaborative features
- When reducing server load from polling

---

## Implementation Priority

### Phase 1 (Post-MVP)
1. **Health Checks** - Essential for production deployment
2. **Enhanced Error Handling** - Improves debugging and user experience

### Phase 2 (Growth)
3. **Performance Monitoring** - When performance becomes important
4. **Caching Strategy** - When scaling to more users

### Phase 3 (Scale)
5. **Rate Limiting** - When protecting against abuse
6. **Request Tracing** - When debugging becomes complex

### Phase 4 (Advanced)
7. **API Versioning** - When making breaking changes
8. **Real-time Updates** - When features require it

---

## Notes

- **Current State**: All basic API communication is working properly
- **Focus**: These are enhancements, not requirements
- **Decision Point**: Implement based on actual needs, not assumptions
- **Documentation**: Update this document as enhancements are implemented 