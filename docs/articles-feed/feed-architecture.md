# Feed Architecture - Articles Feed

## Overview

The DailyBrief articles feed system is built on a modern, scalable architecture that delivers personalized news experiences through intelligent filtering, real-time search, and responsive design. The system combines Django's robust backend capabilities with Next.js's performance-optimized frontend to create a seamless news consumption experience.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Next.js 15)                    │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │    Home     │  │    World    │  │   Article Detail    │  │
│  │   /home     │  │   /world    │  │  /article/[id]      │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │           InfiniteNewsFeed Component                    │  │
│  │  • Infinite scrolling  • Search  • Filtering           │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │                API Integration Layer                    │  │
│  │  • Authentication  • Error handling  • Type safety     │  │
│  └─────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                                │
                                │ HTTPS/JWT
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                    Backend (Django 5)                      │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────┐  │
│  │                 API Endpoints                           │  │
│  │  • /personalized-feed/  • /world-feed/  • /<uuid>/     │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │              Business Logic Layer                       │  │
│  │  • User preference filtering  • Search  • Pagination   │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │                 Data Access Layer                       │  │
│  │  • ORM queries  • Database optimization  • Caching     │  │
│  └─────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                  Database (PostgreSQL)                     │
├─────────────────────────────────────────────────────────────┤
│  Articles  │  Topics  │  Publications  │  User Preferences  │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### Frontend Architecture

#### 1. Page Components
- **Home Page** (`/home`): Personalized feed with user's topic preferences
- **World Page** (`/world`): Global headlines from preferred regions
- **Article Detail** (`/article/[id]`): Full article view with AI summaries

#### 2. Shared Components
- **InfiniteNewsFeed**: Core feed component with infinite scrolling
- **NewsCard**: Individual article card with rich metadata
- **Navigation**: Unified mobile/desktop navigation system

#### 3. Infrastructure
- **API Layer**: Centralized API communication with authentication
- **State Management**: React hooks with user context
- **Type Safety**: Comprehensive TypeScript interfaces

### Backend Architecture

#### 1. API Layer
```python
# RESTful endpoints with consistent patterns
/api/articles/personalized-feed/  # User's personalized articles
/api/articles/world-feed/         # Global top headlines
/api/articles/<uuid>/             # Individual article details
```

#### 2. Business Logic
```python
# Intelligent filtering system
def get_personalized_articles(user):
    # Filter by user's topic preferences (required)
    articles = Article.objects.filter(topics__in=user_topics)
    
    # Additional filtering by publications (if available)
    if user_publications:
        articles = articles.filter(publication__in=user_publications)
    
    return articles.distinct()
```

#### 3. Data Models
```python
# Core entities with relationships
Article ←→ Topic (Many-to-Many)
Article → Publication (Foreign Key)
User ←→ Topic (Many-to-Many via UserTopic)
User ←→ Publication (Many-to-Many via UserPublication)
```

## Data Flow

### 1. Personalized Feed Flow

```
User Request → Authentication → User Preferences → Article Filtering → Response
     │              │                │                    │             │
     │              │                │                    │             │
     ▼              ▼                ▼                    ▼             ▼
┌─────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────┐
│Frontend │  │JWT Token    │  │UserTopic    │  │Article      │  │JSON     │
│Request  │  │Validation   │  │UserPub      │  │Queryset     │  │Response │
└─────────┘  └─────────────┘  └─────────────┘  └─────────────┘  └─────────┘
```

### 2. Search and Filtering Flow

```
User Input → Debounce → API Request → Database Query → Filtered Results
     │          │           │              │               │
     │          │           │              │               │
     ▼          ▼           ▼              ▼               ▼
┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────────────┐ ┌─────────┐
│Search   │ │500ms    │ │Backend  │ │Q(title__icontains│ │Article  │
│Input    │ │Delay    │ │API Call │ │ + description   │ │List     │
└─────────┘ └─────────┘ └─────────┘ └─────────────────┘ └─────────┘
```

### 3. Infinite Scroll Flow

```
Scroll Event → Intersection Observer → Load More → Append Results → Update State
      │               │                    │            │              │
      │               │                    │            │              │
      ▼               ▼                    ▼            ▼              ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────┐ ┌─────────────┐
│User Scrolls │ │Trigger at   │ │Next Page    │ │Merge    │ │Re-render    │
│to Bottom    │ │Last Article │ │API Request  │ │Arrays   │ │Component    │
└─────────────┘ └─────────────┘ └─────────────┘ └─────────┘ └─────────────┘
```

## Key Design Patterns

### 1. Modular Monolith (Backend)

**Principle**: Organize code by domain while maintaining deployment simplicity

```python
backend/apps/
├── articles/          # Article domain
│   ├── models.py     # Article, StoryGroup
│   ├── views.py      # Feed endpoints
│   └── urls.py       # URL routing
├── feeds/            # User preferences domain
│   ├── models.py     # UserTopic, UserRegion, UserPublication
│   └── utils.py      # Helper functions
└── accounts/         # Authentication domain
    ├── auth_helpers.py
    └── views.py
```

**Benefits**:
- Clear separation of concerns
- Easy to understand and maintain
- Simple deployment model
- Shared database for consistency

### 2. Component Composition (Frontend)

**Principle**: Build complex UIs from simple, reusable components

```typescript
// Composition pattern
<InfiniteNewsFeed 
  feedType="personalized"
  topicSlug={selectedTopic}
  searchQuery={debouncedSearch}
  sortOrder={sortOrder}
>
  <NewsCard article={article} onRead={handleRead} />
</InfiniteNewsFeed>
```

**Benefits**:
- Reusable components
- Clear data flow
- Easy testing
- Maintainable codebase

### 3. Progressive Enhancement

**Principle**: Build core functionality first, enhance with JavaScript

```typescript
// Base functionality works without JavaScript
<Link href="/article/123">Read Article</Link>

// Enhanced with JavaScript interactions
<Button onClick={() => trackClick('article', article.id)}>
  Read Article
</Button>
```

## Performance Optimizations

### 1. Database Level

**Query Optimization**:
```python
# Efficient querying with joins
Article.objects.select_related('publication', 'language')
               .prefetch_related('topics')
               .filter(topics__in=user_topics)
               .distinct()
```

**Strategic Indexing**:
```python
class Meta:
    indexes = [
        models.Index(fields=['-published_at']),      # Chronological sorting
        models.Index(fields=['public_id']),          # UUID lookups
        models.Index(fields=['is_top_headline']),    # World feed filtering
        models.Index(fields=['relevance_score']),    # Relevance sorting
    ]
```

### 2. API Level

**Pagination Strategy**:
```python
# Server-side pagination with metadata
{
  "articles": [...],
  "pagination": {
    "page": 1,
    "pageSize": 10,
    "hasNext": true,
    "totalItems": 247
  }
}
```

**Response Optimization**:
```python
# Minimal data transfer
{
  "id": "uuid",
  "title": "...",
  "description": "...",
  "source": {"name": "...", "logoUrl": "..."},
  "publishedAt": "ISO-8601",
  "topics": [{"id": 1, "name": "...", "slug": "..."}]
}
```

### 3. Frontend Level

**Debounced Search**:
```typescript
// Prevent excessive API calls
useEffect(() => {
  const timer = setTimeout(() => {
    setDebouncedSearch(searchQuery)
  }, 500)
  return () => clearTimeout(timer)
}, [searchQuery])
```

**Memoized Callbacks**:
```typescript
// Prevent unnecessary re-renders
const loadArticles = useCallback(async (page, reset) => {
  // Implementation
}, [feedType, topicSlug, searchQuery, sortOrder])
```

## Security Architecture

### 1. Authentication Flow

```
Frontend → NextAuth → JWT Token → Backend Validation → Database Access
    │          │          │              │                    │
    │          │          │              │                    │
    ▼          ▼          ▼              ▼                    ▼
┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────────┐ ┌─────────────┐
│User     │ │Session  │ │Bearer   │ │JWT Decode   │ │User Model   │
│Login    │ │Creation │ │Token    │ │& Validate   │ │Lookup       │
└─────────┘ └─────────┘ └─────────┘ └─────────────┘ └─────────────┘
```

### 2. Data Protection

**Input Validation**:
```python
# Parameter validation
try:
    page = int(request.GET.get('page', 1))
    article_uuid = uuid.UUID(public_id)
except (ValueError, TypeError):
    return JsonResponse({"error": "Invalid parameters"}, status=400)
```

**SQL Injection Prevention**:
```python
# ORM usage prevents SQL injection
Article.objects.filter(topics__in=user_topic_ids)  # Safe
# Never: f"SELECT * FROM articles WHERE topic IN {user_topics}"  # Unsafe
```

### 3. CORS Configuration

```python
# Proper CORS headers
response["Access-Control-Allow-Origin"] = "*"  # Development
response["Access-Control-Allow-Methods"] = "GET, OPTIONS"
response["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
```

## Scalability Considerations

### 1. Horizontal Scaling

**Stateless Design**:
- No server-side sessions
- JWT tokens for authentication
- Database-backed user preferences

**Load Balancing Ready**:
- RESTful API design
- No server affinity required
- Shared database state

### 2. Database Scaling

**Read Replicas**:
```python
# Future: Route read queries to replicas
class DatabaseRouter:
    def db_for_read(self, model, **hints):
        if model._meta.app_label == 'articles':
            return 'articles_read_replica'
        return 'default'
```

**Caching Strategy**:
```python
# Future: Redis integration
@cache_result(timeout=300)  # 5 minutes
def get_user_preferences(user_id):
    return UserTopic.objects.filter(user_id=user_id)
```

### 3. CDN Integration

**Static Assets**:
- Article images served via CDN
- Frontend assets optimized and cached
- API responses with proper cache headers

## Error Handling Strategy

### 1. Graceful Degradation

**Frontend Fallbacks**:
```typescript
// Progressive error handling
try {
  const articles = await getPersonalizedFeed(params)
  setArticles(articles)
} catch (error) {
  setError(error.message)
  // Show error state with retry option
}
```

**Backend Error Responses**:
```python
# Consistent error format
{
  "error": "Human-readable message",
  "code": "ERROR_CODE",
  "details": {}
}
```

### 2. Monitoring and Alerting

**Key Metrics**:
- API response times
- Error rates by endpoint
- Database query performance
- User engagement metrics

**Alert Thresholds**:
- Response time > 2 seconds
- Error rate > 5%
- Database connection pool exhaustion

## Testing Strategy

### 1. Backend Testing

```python
# Unit tests for business logic
class PersonalizedFeedTest(TestCase):
    def test_filters_by_user_topics(self):
        # Test implementation
        
# Integration tests for API endpoints
class FeedAPITest(TestCase):
    def test_personalized_feed_endpoint(self):
        # Test implementation
```

### 2. Frontend Testing

```typescript
// Component testing
describe('InfiniteNewsFeed', () => {
  it('loads articles on mount', async () => {
    // Test implementation
  })
})

// Integration testing
describe('Feed Integration', () => {
  it('navigates between feeds correctly', () => {
    // Test implementation
  })
})
```

### 3. End-to-End Testing

```typescript
// User journey testing
describe('Article Reading Flow', () => {
  it('allows user to browse and read articles', () => {
    cy.visit('/home')
    cy.get('[data-testid="article-card"]').first().click()
    cy.get('[data-testid="article-content"]').should('be.visible')
  })
})
```

## Future Architecture Enhancements

### 1. Microservices Evolution

**Service Boundaries**:
```
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   User Service  │  │ Article Service │  │ Search Service  │
│   • Auth        │  │ • CRUD          │  │ • Elasticsearch │
│   • Preferences │  │ • Filtering     │  │ • Analytics     │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

### 2. Event-Driven Architecture

**Event Streaming**:
```python
# Future: Event-driven updates
class ArticlePublishedEvent:
    article_id: str
    topics: List[str]
    publication_id: str
    
# Consumers update user feeds in real-time
```

### 3. Advanced Caching

**Multi-Layer Caching**:
```
Browser Cache → CDN → Redis → Database
     │            │      │        │
     │            │      │        │
     ▼            ▼      ▼        ▼
┌─────────┐ ┌─────────┐ ┌─────┐ ┌─────────┐
│Local    │ │Edge     │ │App  │ │Primary  │
│Storage  │ │Cache    │ │Cache│ │Database │
└─────────┘ └─────────┘ └─────┘ └─────────┘
```

This architecture provides a solid foundation for the DailyBrief articles feed system while maintaining flexibility for future enhancements and scaling requirements. 