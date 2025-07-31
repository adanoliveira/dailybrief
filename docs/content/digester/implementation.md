# Digest System Implementation

This document covers the implementation details, patterns, and code examples for the Daily Digest System.

## 🔧 Implementation Overview

The Daily Digest System is implemented using Django with a clean separation of concerns across multiple layers. This document provides detailed implementation guidance for developers working with the system.

## 📁 Code Organization

```
backend/apps/content/digest/
├── services/
│   ├── digest_service.py         # Main orchestrator
│   ├── digest_router.py          # Strategy routing
│   ├── articles_digest_strategy.py
│   ├── events_digest_strategy.py
│   ├── content_selector.py       # Article filtering
│   ├── ai_generator.py           # LLM interactions
│   └── __init__.py
├── models.py                     # Database models
├── views.py                      # REST API endpoints
├── urls.py                       # URL routing
├── tasks.py                      # Celery tasks
├── prompt_templates.py           # AI prompts
├── admin.py                      # Django admin
└── management/commands/          # CLI commands
```

## 🏗️ Core Implementation Patterns

### 1. Strategy Pattern Implementation

The digest system uses the Strategy pattern to support multiple generation algorithms:

```python
# Abstract base strategy
class AbstractDigestStrategy:
    """Base class for all digest generation strategies."""
    
    def __init__(self):
        self.content_selector = DigestContentSelector()
        self.ai_generator = DigestAIGenerator()
        self.logger = logging.getLogger(self.__class__.__name__.lower())
    
    def generate_digest_content(
        self,
        digest: Digest,
        followed_topics: List[Topic],
        preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate complete digest content. Must be implemented by subclasses."""
        raise NotImplementedError
    
    def get_display_name(self) -> str:
        """Get human-readable strategy name."""
        raise NotImplementedError
```

### 2. Service Layer Pattern

Services are implemented as stateless classes with clear responsibilities:

```python
class DigestContentSelector:
    """Service for intelligent content selection and filtering."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def get_topic_articles_for_fallback_digest(
        self,
        topic: Topic,
        target_date: datetime.date,
        max_articles: int = 30,
        user: Optional[User] = None,
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> List[Article]:
        """Get articles for topic-based digest generation."""
        
        # Calculate date range based on user preferences
        if user_preferences and user:
            user_timezone = user.profile.timezone if hasattr(user, 'profile') else 'UTC'
            start_date, end_date = self._calculate_date_range_from_preferences(
                target_date, user_preferences, user_timezone
            )
        else:
            # Fallback to default 48h window
            end_date = datetime.combine(target_date, datetime.max.time())
            start_date = end_date - timedelta(hours=48)
        
        # Build query with filters
        articles_query = Article.objects.filter(
            published_at__gte=start_date,
            published_at__lte=end_date,
            analyzer_status='completed',
            summarization_status='completed'
        ).select_related('primary_topic', 'primary_region', 'publication', 'structured_summary')
        
        # Apply topic filter
        articles_query = articles_query.filter(primary_topic=topic)
        
        # Apply user preferences
        articles_query = self._apply_user_filters(articles_query, user)
        
        return list(articles_query.order_by('-published_at')[:max_articles])
```

### 3. Database Transaction Pattern

Critical operations use database transactions for consistency:

```python
def generate_user_digest(self, user: User, date: datetime.date, force_regenerate: bool = False) -> Digest:
    """Generate digest with transaction safety."""
    
    start_time = timezone.now()
    
    try:
        with transaction.atomic():
            # Create or update digest record
            digest, created = Digest.objects.get_or_create(
                user=user,
                date=date,
                defaults={
                    'title': f"Your Daily Brief for {date.strftime('%B %d, %Y')}",
                    'generation_status': 'processing',
                    'user_timezone': user.profile.timezone,
                    'digest_preferences': user.profile.get_digest_preferences(),
                }
            )
            
            if not created and not force_regenerate:
                return digest
            
            # Update status
            digest.generation_status = 'processing'
            digest.error_message = ''
            digest.save()
            
            # Generate content
            result = self.router.generate_digest_content(
                digest=digest,
                followed_topics=self._get_user_followed_topics(user),
                preferences=digest.digest_preferences
            )
            
            # Update final status
            end_time = timezone.now()
            digest.generation_status = 'completed'
            digest.generation_duration_ms = int((end_time - start_time).total_seconds() * 1000)
            digest.is_published = True
            digest.save()
            
            return digest
            
    except Exception as e:
        # Update error status
        if 'digest' in locals():
            digest.generation_status = 'failed'
            digest.error_message = str(e)
            digest.save()
        raise
```

## 🧪 Testing Patterns

### 1. Unit Testing

Services are tested with mocked dependencies:

```python
class TestArticlesDigestStrategy(TestCase):
    """Test articles-based digest generation."""
    
    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@example.com')
        self.topic = Topic.objects.create(name='Technology', slug='technology')
        self.strategy = ArticlesDigestStrategy()
        
    @patch('apps.content.digest.services.ai_generator.DigestAIGenerator')
    def test_generate_digest_content(self, mock_ai_generator):
        """Test successful digest generation."""
        
        # Setup mocks
        mock_ai_generator.return_value.generate_topic_summary_from_articles.return_value = {
            'topic_abstract': 'Test abstract',
            'main_facts': ['Fact 1', 'Fact 2'],
            'perspectives': ['Perspective 1'],
            'cost': Decimal('0.05')
        }
        
        # Create test data
        digest = Digest.objects.create(
            user=self.user,
            date=date.today(),
            title='Test Digest'
        )
        
        # Execute
        result = self.strategy.generate_digest_content(
            digest=digest,
            followed_topics=[self.topic],
            preferences={'max_topics': 6, 'time_window': '48h'}
        )
        
        # Assertions
        self.assertEqual(result['strategy_used'], 'Articles-Based Digest')
        self.assertIn('topics_data', result)
        self.assertEqual(len(result['topics_data']), 1)
```

## 🚀 Performance Optimizations

### 1. Database Query Optimization

Efficient queries with selective prefetching:

```python
def get_digest_with_content(digest_id: str, user: User) -> Digest:
    """Optimized digest retrieval with minimal queries."""
    
    return Digest.objects.select_related(
        'user',
    ).prefetch_related(
        'digest_topics__topic',
        'digest_topics__stories__event',
        'digest_topics__stories__recommended_articles__publication',
        'stories__articles__publication'
    ).get(
        public_id=digest_id,
        user=user
    )
```

### 2. Caching Strategy

Strategic caching for expensive operations:

```python
from django.core.cache import cache

def get_user_articles_cached(user: User, date: datetime.date) -> List[Article]:
    """Get user articles with caching."""
    
    cache_key = f"user_articles_{user.id}_{date.isoformat()}"
    cached_articles = cache.get(cache_key)
    
    if cached_articles is not None:
        return cached_articles
    
    articles = list(Article.objects.filter(
        # ... query logic
    ))
    
    # Cache for 1 hour
    cache.set(cache_key, articles, 3600)
    return articles
```

This implementation guide provides a comprehensive foundation for working with the Daily Digest System, ensuring consistent patterns and best practices across the codebase.
