# Backend Implementation - Articles Feed

## Overview

The backend implementation provides RESTful API endpoints for serving personalized news feeds and world headlines. Built with Django, it handles complex filtering logic, user preferences, authentication, and pagination.

## File Structure

```
backend/apps/articles/
├── models.py              # Article and related models
├── views.py              # API endpoints for feeds
├── urls.py               # URL routing
└── migrations/           # Database migrations

backend/apps/feeds/
├── models.py             # User preference models
└── utils.py              # Helper functions

backend/apps/accounts/
├── auth_helpers.py       # JWT authentication utilities
└── views.py              # User preference endpoints
```

## Core Models

### Article Model (`backend/apps/articles/models.py`)

```python
class Article(models.Model):
    # Identifiers
    public_id = models.UUIDField(default=uuid.uuid4, unique=True)
    
    # Content
    title = models.CharField(max_length=512)
    description = models.TextField(blank=True, null=True)
    content = models.TextField(blank=True, null=True)
    url = models.URLField(max_length=1024)
    image_url = models.URLField(max_length=1024, null=True, blank=True)
    
    # Source information
    source_name = models.CharField(max_length=255, blank=True, null=True)
    publication = models.ForeignKey(Publication, on_delete=models.SET_NULL, null=True)
    author = models.CharField(max_length=255, blank=True, null=True)
    
    # Classification
    topics = models.ManyToManyField(Topic, related_name='articles', blank=True)
    regions = models.ManyToManyField(Region, related_name='articles', blank=True)
    language = models.ForeignKey(Language, on_delete=models.SET_NULL, null=True)
    
    # Metadata
    published_at = models.DateTimeField()
    is_top_headline = models.BooleanField(default=False)
    relevance_score = models.FloatField(default=0.0)
    read_time_minutes = models.FloatField(null=True, blank=True)
    
    # Performance indexes
    class Meta:
        indexes = [
            models.Index(fields=['-published_at']),
            models.Index(fields=['public_id']),
            models.Index(fields=['is_top_headline']),
            models.Index(fields=['relevance_score']),
        ]
```

**Key Features:**
- **UUID Public ID**: Secure external identifier, never expose internal IDs
- **Rich Metadata**: Content analysis, read time, relevance scoring
- **Flexible Relationships**: Many-to-many with topics, regions
- **Performance Optimized**: Strategic database indexes

### User Preference Models (`backend/apps/feeds/models.py`)

```python
class UserTopic(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)

class UserRegion(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    region = models.ForeignKey(Region, on_delete=models.CASCADE)

class UserPublication(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    publication = models.ForeignKey(Publication, on_delete=models.CASCADE)
```

## API Endpoints

### 1. Personalized Feed (`/api/articles/personalized-feed/`)

**Purpose**: Serves articles based on user's topic and publication preferences

**Method**: `GET`

**Authentication**: Required (JWT token)

**Query Parameters**:
- `page` (int): Page number (default: 1)
- `page_size` (int): Articles per page (default: 10)
- `sort` (string): Sorting method - `relevance`, `newest`, `oldest` (default: relevance)
- `topic` (string): Filter by topic slug (optional)
- `search` (string): Search term (optional)

**Filtering Logic**:
```python
# Always filter by user's preferred topics
if user_topic_ids:
    queryset = queryset.filter(topics__in=user_topic_ids)
else:
    queryset = queryset.none()  # No preferences = no results

# Additionally filter by publications if user has publication preferences
if user_publication_ids:
    queryset = queryset.filter(publication__in=user_publication_ids)

# Apply additional topic filter if specified (not "for-you")
if topic_slug and topic_slug != 'for-you':
    queryset = queryset.filter(topics__slug=topic_slug)
```

**Sorting Logic**:
```python
if sort == 'newest':
    queryset = queryset.order_by('-published_at')
elif sort == 'oldest':
    queryset = queryset.order_by('published_at')
else:  # relevance (default)
    queryset = queryset.order_by(
        '-relevance_score',
        '-is_top_headline', 
        '-published_at'
    )
```

**Response Format**:
```json
{
  "articles": [
    {
      "id": "uuid-string",
      "title": "Article Title",
      "description": "Article description",
      "source": {
        "name": "Publication Name",
        "logoUrl": "https://..."
      },
      "publishedAt": "2024-01-01T12:00:00Z",
      "imageUrl": "https://...",
      "url": "https://...",
      "isTopHeadline": true,
      "readTime": 5,
      "topics": [
        {"id": 1, "name": "Technology", "slug": "technology"}
      ]
    }
  ],
  "pagination": {
    "page": 1,
    "pageSize": 10,
    "totalPages": 5,
    "totalItems": 50,
    "hasNext": true,
    "hasPrevious": false
  }
}
```

### 2. World Feed (`/api/articles/world-feed/`)

**Purpose**: Serves top headlines from user's preferred regions

**Method**: `GET`

**Authentication**: Required (JWT token)

**Query Parameters**:
- `page` (int): Page number (default: 1)
- `page_size` (int): Articles per page (default: 10)
- `topic` (string): Filter by topic slug (optional)
- `search` (string): Search term (optional)

**Filtering Logic**:
```python
# Base query - only top headlines
queryset = Article.objects.filter(is_top_headline=True)

# Filter by user's preferred regions
user_region_codes = UserRegion.objects.filter(user=user).values_list('region__code', flat=True)
if user_region_codes:
    queryset = queryset.filter(publication__regions__code__in=user_region_codes).distinct()

# Apply topic filter if specified (not "all")
if topic_slug and topic_slug != 'all':
    queryset = queryset.filter(topics__slug=topic_slug)
```

### 3. Article Detail (`/api/articles/<uuid>/`)

**Purpose**: Serves detailed article information including AI summaries

**Method**: `GET`

**Authentication**: Optional

**Response Includes**:
- Full article content
- AI-generated summary (if available)
- Complete metadata
- Related topics and source information

## Authentication System

### JWT Token Validation

```python
def authenticate_request(request):
    """
    Validates JWT token from Authorization header
    Returns: (is_authenticated, user, error_message)
    """
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return False, None, "Missing or invalid authorization header"
    
    token = auth_header.split(' ')[1]
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        user = User.objects.get(id=payload['user_id'])
        return True, user, None
    except (jwt.InvalidTokenError, User.DoesNotExist):
        return False, None, "Invalid or expired token"
```

### CORS Handling

All endpoints include proper CORS headers for cross-origin requests:

```python
# Handle OPTIONS request for CORS preflight
if request.method == "OPTIONS":
    response = JsonResponse({})
    response["Access-Control-Allow-Origin"] = "*"
    response["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    response["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response

# Add CORS headers to response
response = JsonResponse(response_data)
response["Access-Control-Allow-Origin"] = "*"
return response
```

## Database Optimization

### Query Optimization

```python
# Efficient querying with select_related and prefetch_related
queryset = Article.objects.select_related(
    'language', 'publication'
).prefetch_related('topics')

# Use distinct() to avoid duplicates from many-to-many joins
queryset = queryset.filter(topics__in=user_topic_ids).distinct()
```

### Indexes

Strategic database indexes for performance:
- `published_at` (DESC) - For chronological sorting
- `public_id` - For UUID lookups
- `is_top_headline` - For world feed filtering
- `relevance_score` - For relevance sorting

## Error Handling

### Validation

```python
# Parse and validate query parameters
try:
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 10))
except ValueError:
    return JsonResponse({"error": "Invalid page parameters"}, status=400)

# Validate UUID format
try:
    article_uuid = uuid.UUID(public_id)
except ValueError:
    return JsonResponse({"error": "Invalid article ID"}, status=400)
```

### Error Responses

```python
# Authentication errors
if not is_authenticated:
    return JsonResponse({"error": error_message}, status=401)

# Not found errors
except Article.DoesNotExist:
    return JsonResponse({"error": "Article not found"}, status=404)

# Server errors
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    return JsonResponse({"error": "Internal server error"}, status=500)
```

## URL Configuration

### Articles URLs (`backend/apps/articles/urls.py`)

```python
from django.urls import path
from . import views

urlpatterns = [
    path('personalized-feed/', views.personalized_feed, name='personalized_feed'),
    path('world-feed/', views.world_feed, name='world_feed'),
    path('<uuid:public_id>/', views.article_detail, name='article_detail'),
]
```

### Main URL Integration (`backend/dailybrief/urls.py`)

```python
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/articles/', include('apps.articles.urls')),
    path('api/accounts/', include('apps.accounts.urls')),
    # ... other patterns
]
```

## Performance Considerations

### Database Queries
- Use `select_related()` for foreign key relationships
- Use `prefetch_related()` for many-to-many relationships
- Apply `distinct()` to avoid duplicates from joins
- Limit query results with pagination

### Response Optimization
- Minimal data transfer with structured JSON
- Efficient serialization of model data
- Proper HTTP status codes and headers

### Caching Strategy (Future)
- Query result caching for frequently accessed data
- Redis integration for session and preference caching
- CDN integration for static content

## Testing Strategy

### Unit Tests
```python
class PersonalizedFeedTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='test@example.com')
        self.topic = Topic.objects.create(name='Technology', slug='technology')
        UserTopic.objects.create(user=self.user, topic=self.topic)
    
    def test_personalized_feed_filters_by_topics(self):
        # Test that feed only returns articles from user's topics
        pass
    
    def test_personalized_feed_requires_authentication(self):
        # Test that unauthenticated requests are rejected
        pass
```

### Integration Tests
- End-to-end API testing with real database
- Authentication flow testing
- Pagination and filtering validation

## Deployment Considerations

### Environment Variables
```python
# Required settings
SECRET_KEY = os.environ.get('SECRET_KEY')
DATABASE_URL = os.environ.get('DATABASE_URL')
CORS_ALLOWED_ORIGINS = os.environ.get('CORS_ALLOWED_ORIGINS', '').split(',')
```

### Database Migrations
```bash
# Apply migrations
python manage.py migrate

# Create new migrations after model changes
python manage.py makemigrations articles
```

### Monitoring
- Log all authentication failures
- Monitor query performance
- Track API response times
- Alert on error rate thresholds 