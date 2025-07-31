# API Endpoints - Articles Feed

## Overview

The Articles Feed API provides RESTful endpoints for accessing personalized news feeds, world headlines, and individual article details. All endpoints require authentication via JWT tokens and support CORS for cross-origin requests.

## Base URL

```
Production: https://api.dailybrief.com
Development: http://localhost:8000
```

## Authentication

All endpoints require a valid JWT token in the Authorization header:

```http
Authorization: Bearer <jwt_token>
```

## Endpoints

### 1. Personalized Feed

**Endpoint**: `GET /api/articles/personalized-feed/`

**Description**: Returns articles filtered by user's topic and publication preferences

**Authentication**: Required

**Query Parameters**:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | integer | 1 | Page number for pagination |
| `page_size` | integer | 10 | Number of articles per page (max: 50) |
| `sort` | string | "relevance" | Sort order: "relevance", "newest", "oldest" |
| `topic` | string | null | Filter by topic slug (optional) |
| `search` | string | null | Search term for title/description/content |

**Example Request**:
```http
GET /api/articles/personalized-feed/?page=1&page_size=10&sort=relevance&topic=technology&search=AI
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

**Response Format**:
```json
{
  "articles": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "Breaking: New AI Technology Revolutionizes Healthcare",
      "description": "Scientists have developed a groundbreaking AI system that can diagnose diseases with 99% accuracy.",
      "source": {
        "name": "TechCrunch",
        "logoUrl": "https://techcrunch.com/logo.png"
      },
      "publishedAt": "2024-01-15T14:30:00Z",
      "imageUrl": "https://example.com/article-image.jpg",
      "url": "https://techcrunch.com/article-url",
      "isTopHeadline": true,
      "readTime": 5,
      "topics": [
        {
          "id": 1,
          "name": "Technology",
          "slug": "technology"
        },
        {
          "id": 5,
          "name": "Health",
          "slug": "health"
        }
      ]
    }
  ],
  "pagination": {
    "page": 1,
    "pageSize": 10,
    "totalPages": 25,
    "totalItems": 247,
    "hasNext": true,
    "hasPrevious": false
  }
}
```

**Filtering Logic**:
1. Articles must be from user's preferred topics
2. If user has publication preferences, articles must also be from those publications
3. Additional topic filter applied if `topic` parameter is provided (except "for-you")
4. Search filter applied across title, description, and content

**Sorting Options**:
- **relevance** (default): `relevance_score DESC, is_top_headline DESC, published_at DESC`
- **newest**: `published_at DESC`
- **oldest**: `published_at ASC`

**Error Responses**:
```json
// 401 Unauthorized
{
  "error": "Invalid or expired token"
}

// 400 Bad Request
{
  "error": "Invalid page parameters"
}

// 500 Internal Server Error
{
  "error": "Internal server error"
}
```

### 2. World Feed

**Endpoint**: `GET /api/articles/world-feed/`

**Description**: Returns top headlines from publications serving user's preferred regions

**Authentication**: Required

**Query Parameters**:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | integer | 1 | Page number for pagination |
| `page_size` | integer | 10 | Number of articles per page (max: 50) |
| `topic` | string | null | Filter by topic slug (optional) |
| `search` | string | null | Search term for title/description/content |

**Example Request**:
```http
GET /api/articles/world-feed/?page=1&page_size=10&topic=business&search=economy
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

**Response Format**:
```json
{
  "articles": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "title": "Global Economy Shows Signs of Recovery",
      "description": "Economic indicators suggest a positive trend in global markets.",
      "source": {
        "name": "Reuters",
        "logoUrl": "https://reuters.com/logo.png"
      },
      "publishedAt": "2024-01-15T16:45:00Z",
      "imageUrl": "https://example.com/economy-image.jpg",
      "url": "https://reuters.com/article-url",
      "isTopHeadline": true,
      "readTime": 3,
      "topics": [
        {
          "id": 2,
          "name": "Business",
          "slug": "business"
        }
      ]
    }
  ],
  "pagination": {
    "page": 1,
    "pageSize": 10,
    "totalPages": 15,
    "totalItems": 143,
    "hasNext": true,
    "hasPrevious": false
  }
}
```

**Filtering Logic**:
1. Only articles marked as `is_top_headline = true`
2. Articles from publications serving user's preferred regions
3. Additional topic filter applied if `topic` parameter is provided (except "all")
4. Search filter applied across title, description, and content

**Sorting**: Always sorted by `published_at DESC` (newest first)

### 3. Article Detail

**Endpoint**: `GET /api/articles/<uuid>/`

**Description**: Returns detailed information for a specific article including AI summaries

**Authentication**: Optional (but recommended for personalization)

**Path Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `uuid` | UUID | Article's public UUID identifier |

**Example Request**:
```http
GET /api/articles/550e8400-e29b-41d4-a716-446655440000/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

**Response Format**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Breaking: New AI Technology Revolutionizes Healthcare",
  "description": "Scientists have developed a groundbreaking AI system that can diagnose diseases with 99% accuracy.",
  "content": "Full article content here...",
  "source": {
    "name": "TechCrunch"
  },
  "author": "John Smith",
  "publishedAt": "2024-01-15T14:30:00Z",
  "imageUrl": "https://example.com/article-image.jpg",
  "url": "https://techcrunch.com/article-url",
  "isTopHeadline": true,
  "topics": [
    {
      "id": 1,
      "name": "Technology",
      "slug": "technology"
    },
    {
      "id": 5,
      "name": "Health",
      "slug": "health"
    }
  ],
  "readTime": 5,
  "summary": {
    "abstract": "AI system achieves 99% diagnostic accuracy, potentially transforming healthcare delivery and patient outcomes.",
    "keyPoints": [
      "New AI system developed by research team",
      "99% accuracy in disease diagnosis",
      "Potential to revolutionize healthcare",
      "Clinical trials show promising results"
    ]
  }
}
```

**Error Responses**:
```json
// 400 Bad Request
{
  "error": "Invalid article ID"
}

// 404 Not Found
{
  "error": "Article not found"
}
```

## CORS Support

All endpoints support CORS with the following configuration:

**Preflight Requests** (`OPTIONS`):
```http
OPTIONS /api/articles/personalized-feed/
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, OPTIONS
Access-Control-Allow-Headers: Content-Type, Authorization
```

**Response Headers**:
```http
Access-Control-Allow-Origin: *
```

## Rate Limiting

| Endpoint | Rate Limit | Window |
|----------|------------|--------|
| Personalized Feed | 100 requests | 1 hour |
| World Feed | 100 requests | 1 hour |
| Article Detail | 200 requests | 1 hour |

Rate limit headers included in responses:
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642694400
```

## Error Handling

### Standard Error Format

All error responses follow this format:
```json
{
  "error": "Human-readable error message",
  "code": "ERROR_CODE", // Optional
  "details": {} // Optional additional details
}
```

### HTTP Status Codes

| Status | Description | Common Causes |
|--------|-------------|---------------|
| 200 | Success | Request completed successfully |
| 400 | Bad Request | Invalid parameters, malformed UUID |
| 401 | Unauthorized | Missing/invalid JWT token |
| 403 | Forbidden | Token valid but insufficient permissions |
| 404 | Not Found | Article not found |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server-side error |

## Data Types

### Article Preview
```typescript
interface ArticlePreview {
  id: string                    // UUID
  title: string                 // Max 512 characters
  description: string           // Article summary
  source: {
    name: string               // Publication name
    logoUrl?: string           // Publication logo URL
  }
  publishedAt: string          // ISO 8601 datetime
  imageUrl?: string            // Article image URL
  url: string                  // Original article URL
  isTopHeadline: boolean       // Whether article is a top headline
  readTime?: number            // Estimated read time in minutes
  topics: Array<{
    id: number                 // Topic ID
    name: string              // Topic display name
    slug: string              // Topic URL slug
  }>
}
```

### Pagination Metadata
```typescript
interface PaginationMetadata {
  page: number                 // Current page number
  pageSize: number            // Items per page
  totalPages: number          // Total number of pages
  totalItems: number          // Total number of items
  hasNext: boolean            // Whether next page exists
  hasPrevious: boolean        // Whether previous page exists
}
```

### Article Detail
```typescript
interface ArticleDetail extends ArticlePreview {
  content: string             // Full article content
  author?: string            // Article author
  summary?: {
    abstract?: string        // AI-generated abstract
    keyPoints?: string[]     // Key points from article
  }
}
```

## Performance Considerations

### Database Optimization
- Queries use `select_related()` and `prefetch_related()` for efficiency
- Strategic database indexes on frequently queried fields
- Pagination limits prevent large result sets

### Response Optimization
- Minimal data transfer with structured JSON
- Efficient serialization of model relationships
- Proper HTTP caching headers (future enhancement)

### Monitoring
- Query performance tracking
- API response time monitoring
- Error rate alerting
- Rate limit monitoring

## Security

### Authentication
- JWT tokens with configurable expiration
- Token validation on every request
- Secure token signing with environment-specific secrets

### Input Validation
- UUID format validation for article IDs
- Parameter type validation and sanitization
- SQL injection prevention through ORM usage

### Data Privacy
- User preferences used for filtering without exposure
- No sensitive user data in API responses
- Audit logging for security monitoring

## Testing

### Unit Tests
```python
class PersonalizedFeedAPITest(TestCase):
    def test_requires_authentication(self):
        response = self.client.get('/api/articles/personalized-feed/')
        self.assertEqual(response.status_code, 401)
    
    def test_filters_by_user_topics(self):
        # Test implementation
        pass
```

### Integration Tests
```python
class FeedIntegrationTest(TestCase):
    def test_end_to_end_personalized_feed(self):
        # Test complete flow from authentication to response
        pass
```

### Load Testing
- Concurrent user simulation
- Database performance under load
- Rate limiting validation
- Response time benchmarking

## Future Enhancements

### Caching
- Redis integration for frequently accessed data
- CDN integration for static content
- Query result caching with TTL

### Advanced Features
- Real-time updates via WebSockets
- Article recommendation engine
- User interaction tracking
- Content personalization algorithms

### Analytics
- API usage analytics
- User behavior tracking
- Performance metrics dashboard
- A/B testing framework 