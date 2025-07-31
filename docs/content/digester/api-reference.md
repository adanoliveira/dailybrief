# Digest API Reference

This document provides complete API reference for the Daily Digest System, including REST endpoints, Python APIs, and management commands.

## 🌐 REST API Endpoints

### User Digests

#### GET `/api/digest/latest/`
Get the user's latest digest.

**Authentication**: Required  
**Method**: GET  
**Parameters**: None

**Response**:
```json
{
  "success": true,
  "data": {
    "digest": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "Your Daily Brief for December 21, 2024",
      "date": "2024-12-21",
      "introduction": "Here's what's happening today...",
      "conclusion": "Stay informed, stay ahead...",
      "topics": [
        {
          "name": "Technology",
          "abstract": "Major developments in AI and tech...",
          "facts": [
            "OpenAI releases GPT-5",
            "Apple announces new MacBook Pro"
          ],
          "perspectives": [
            "Industry analysts see this as transformative",
            "Critics worry about implementation challenges"
          ],
          "stories": [
            {
              "title": "OpenAI's GPT-5 Breakthrough",
              "summary": "OpenAI today announced...",
              "recommended_articles": [
                {
                  "title": "GPT-5 Technical Analysis",
                  "url": "https://example.com/article1",
                  "publication": "TechCrunch"
                }
              ]
            }
          ]
        }
      ],
      "generation_duration_ms": 32500,
      "cost_usd": "0.089000"
    }
  }
}
```

#### GET `/api/digest/{digest_id}/`
Get specific digest by ID.

**Authentication**: Required  
**Method**: GET  
**Parameters**:
- `digest_id` (URL): Digest public UUID

**Response**: Same as latest digest

#### POST `/api/digest/generate/`
Generate new digest for user.

**Authentication**: Required  
**Method**: POST  
**Request Body**:
```json
{
  "date": "2024-12-21",  // Optional, defaults to today
  "force_regenerate": false,  // Optional, defaults to false
  "strategy": "articles_based"  // Optional, uses user preference
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "digest_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "processing",
    "estimated_completion": "2024-12-21T10:30:00Z"
  }
}
```

#### GET `/api/digest/history/`
Get user's digest history.

**Authentication**: Required  
**Method**: GET  
**Query Parameters**:
- `limit` (optional): Number of digests to return (default: 10, max: 50)
- `offset` (optional): Pagination offset (default: 0)

**Response**:
```json
{
  "success": true,
  "data": {
    "digests": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "title": "Your Daily Brief for December 21, 2024",
        "date": "2024-12-21",
        "generation_status": "completed",
        "topics_count": 4,
        "stories_count": 12,
        "generation_duration_ms": 32500
      }
    ],
    "total": 25,
    "has_next": true
  }
}
```

### Digest Configuration

#### GET `/api/digest/config/`
Get digest configuration options.

**Authentication**: Required  
**Method**: GET

**Response**:
```json
{
  "success": true,
  "data": {
    "available_strategies": {
      "articles_based": "Articles-Based Digest",
      "events_based": "Events-Based Digest"
    },
    "time_windows": {
      "24h": "Last 24 hours",
      "48h": "Last 48 hours",
      "72h": "Last 72 hours",
      "full_previous_day": "Complete previous day",
      "full_previous_2_days": "Complete 2 previous days"
    },
    "current_default_strategy": "articles_based",
    "user_preferences": {
      "digest_strategy": "articles_based",
      "time_window": "48h",
      "max_topics": 6,
      "max_articles_per_topic": 30
    }
  }
}
```

#### POST `/api/digest/config/`
Update digest configuration.

**Authentication**: Required (Staff only for global settings)  
**Method**: POST  
**Request Body**:
```json
{
  "default_strategy": "events_based",  // Global setting (staff only)
  "user_preferences": {  // User-specific settings
    "digest_strategy": "articles_based",
    "time_window": "48h",
    "max_topics": 6,
    "max_articles_per_topic": 30
  }
}
```

## 🐍 Python API Reference

### DigestService

Main service class for digest operations.

```python
from apps.content.digest.services import DigestService

class DigestService:
    def __init__(self):
        """Initialize digest service with router."""
        
    def generate_user_digest(
        self, 
        user: User, 
        date: datetime.date,
        force_regenerate: bool = False
    ) -> Digest:
        """
        Generate personalized digest for user.
        
        Args:
            user: User to generate digest for
            date: Date to generate digest for
            force_regenerate: Whether to regenerate existing digest
            
        Returns:
            Digest: Generated or existing digest
            
        Raises:
            ValueError: If user has no followed topics
            RuntimeError: If generation fails
        """
        
    def get_user_digest(self, user: User, date: datetime.date) -> Optional[Digest]:
        """
        Get existing digest for user and date.
        
        Args:
            user: User to get digest for
            date: Date to get digest for
            
        Returns:
            Digest instance if exists, None otherwise
        """
        
    def get_recent_digests(self, user: User, limit: int = 7) -> List[Digest]:
        """
        Get recent digests for user.
        
        Args:
            user: User to get digests for
            limit: Maximum number of digests to return
            
        Returns:
            List of recent Digest instances
        """
        
    def get_available_strategies(self) -> Dict[str, str]:
        """
        Get available digest generation strategies.
        
        Returns:
            Dictionary mapping strategy keys to display names
        """
        
    def set_default_strategy(self, strategy_name: str) -> bool:
        """
        Set default digest strategy.
        
        Args:
            strategy_name: Strategy key to set as default
            
        Returns:
            True if strategy was set, False if not found
        """
```

### DigestRouter

Strategy routing and fallback management.

```python
from apps.content.digest.services import DigestRouter

class DigestRouter:
    def __init__(self):
        """Initialize router with available strategies."""
        
    def generate_digest_content(
        self,
        digest: Digest,
        followed_topics: List[Topic],
        preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Route digest generation to appropriate strategy.
        
        Args:
            digest: Digest instance to generate content for
            followed_topics: User's followed topics
            preferences: User's digest preferences
            
        Returns:
            Dictionary with generation results and metadata
        """
        
    def get_available_strategies(self) -> Dict[str, str]:
        """Get available strategies mapping."""
        
    def get_current_default_strategy(self) -> str:
        """Get current default strategy name."""
        
    def set_default_strategy(self, strategy_name: str) -> bool:
        """Set default strategy."""
```

### ContentSelector

Article selection and filtering service.

```python
from apps.content.digest.services import DigestContentSelector

class DigestContentSelector:
    def __init__(self):
        """Initialize content selector."""
        
    def get_topic_articles_for_fallback_digest(
        self,
        topic: Topic,
        target_date: datetime.date,
        max_articles: int = 30,
        user: Optional[User] = None,
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> List[Article]:
        """
        Get articles for topic-based digest generation.
        
        Args:
            topic: Topic to get articles for
            target_date: Date to filter articles
            max_articles: Maximum articles to return
            user: User for personalization (optional)
            user_preferences: User's digest preferences (optional)
            
        Returns:
            List of relevant articles
        """
        
    def get_top_events_for_topic(
        self,
        topic: Topic,
        target_date: datetime.date,
        max_events: int = 3,
        user: Optional[User] = None,
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get top events for topic based on article mentions.
        
        Args:
            topic: Topic to get events for
            target_date: Date to filter articles
            max_events: Maximum events to return
            user: User for personalization (optional)
            user_preferences: User's digest preferences (optional)
            
        Returns:
            List of event data dictionaries
        """
```

### AIGenerator

AI content generation service.

```python
from apps.content.digest.services import DigestAIGenerator

class DigestAIGenerator:
    def __init__(self):
        """Initialize AI generator with providers."""
        
    def generate_topic_summary_from_articles(
        self,
        articles: List[Article],
        topic: Topic,
        max_articles: int = 30
    ) -> Dict[str, Any]:
        """
        Generate topic summary from multiple articles.
        
        Args:
            articles: Articles to summarize
            topic: Topic context
            max_articles: Maximum articles to process
            
        Returns:
            Dictionary with summary content and metadata
        """
        
    def generate_digest_introduction(
        self,
        topics_data: List[Dict[str, Any]],
        user: User,
        date: datetime.date
    ) -> Dict[str, Any]:
        """
        Generate digest introduction.
        
        Args:
            topics_data: Topic summaries and content
            user: User for personalization
            date: Digest date
            
        Returns:
            Dictionary with introduction content and metadata
        """
        
    def generate_digest_conclusion(
        self,
        introduction: str,
        topic_abstracts: List[str],
        user: User,
        date: datetime.date
    ) -> Dict[str, Any]:
        """
        Generate digest conclusion.
        
        Args:
            introduction: Digest introduction text
            topic_abstracts: List of topic abstracts
            user: User for personalization
            date: Digest date
            
        Returns:
            Dictionary with conclusion content and metadata
        """
```

## 📊 Model Reference

### Digest Model

```python
class Digest(models.Model):
    # Identity
    public_id: UUIDField           # Public identifier
    user: ForeignKey              # Associated user
    date: DateField                # Digest date
    
    # Content
    title: CharField               # Digest title
    introduction: TextField        # AI-generated introduction
    conclusion: TextField          # AI-generated conclusion
    html_content: TextField        # Full HTML content
    
    # Status
    generation_status: CharField   # pending|processing|completed|failed
    error_message: TextField       # Error details if failed
    is_published: BooleanField     # Whether digest is published
    is_sent: BooleanField         # Whether digest was sent via email
    sent_at: DateTimeField        # When digest was sent
    
    # Performance metrics
    articles_processed: IntegerField        # Articles processed count
    events_included: IntegerField          # Events included count
    topics_included: IntegerField          # Topics included count
    generation_duration_ms: IntegerField  # Generation time in ms
    generation_cost_usd: DecimalField     # Generation cost in USD
    
    # AI metadata
    ai_model_used: CharField      # AI model used for generation
    tokens_input: IntegerField    # Total input tokens
    tokens_output: IntegerField   # Total output tokens
    
    # User context
    user_timezone: CharField      # User's timezone during generation
    digest_preferences: JSONField # User preferences snapshot
    
    # Timestamps
    created_at: DateTimeField     # Creation timestamp
    updated_at: DateTimeField     # Last update timestamp
```

### DigestTopic Model

```python
class DigestTopic(models.Model):
    # Relationships
    digest: ForeignKey            # Parent digest
    topic: ForeignKey             # Associated topic
    
    # AI-generated content
    topic_abstract: TextField     # Topic summary (2-3 sentences)
    main_facts: JSONField        # Top 5 facts (list of strings)
    perspectives: JSONField      # Key perspectives (list of strings)
    
    # Metadata
    order: IntegerField          # Display order within digest
    event_count: IntegerField    # Number of events in topic
    article_count: IntegerField  # Total articles contributing
    
    # Performance tracking
    generation_cost_usd: DecimalField # Cost to generate topic
    tokens_input: IntegerField        # Input tokens for generation
    tokens_output: IntegerField       # Output tokens for generation
    
    # Timestamp
    created_at: DateTimeField    # Creation timestamp
```

### DigestStory Model

```python
class DigestStory(models.Model):
    # Relationships
    digest: ForeignKey           # Parent digest
    digest_topic: ForeignKey     # Parent topic section
    event: ForeignKey            # Associated event (optional)
    
    # Content
    title: CharField             # Story title
    summary: TextField           # Story summary
    enhanced_abstract: TextField # AI-enhanced event summary
    key_facts: JSONField        # Key facts (list of strings)
    perspectives: JSONField     # Different viewpoints (list of strings)
    
    # Article relationships
    recommended_articles: ManyToManyField # Recommended articles
    articles: ManyToManyField              # Legacy article relationship
    
    # Event metrics
    article_count: IntegerField      # Total articles mentioning event
    primary_mentions: IntegerField   # Primary event mentions
    secondary_mentions: IntegerField # Secondary event mentions
    event_score: FloatField         # Calculated importance score
    
    # Performance tracking
    generation_cost_usd: DecimalField # Cost to generate story
    tokens_input: IntegerField        # Input tokens
    tokens_output: IntegerField       # Output tokens
    
    # Display
    order: IntegerField          # Display order within topic
    
    # Timestamps
    created_at: DateTimeField    # Creation timestamp
    updated_at: DateTimeField    # Last update timestamp
```

## 🔧 Configuration Reference

### User Preferences Schema

```python
digest_preferences = {
    # Strategy selection
    "digest_strategy": "articles_based",  # "articles_based" | "events_based"
    
    # Content selection
    "time_window": "48h",         # "24h" | "48h" | "72h" | "full_previous_day" | "full_previous_2_days"
    "max_topics": 6,              # Maximum topics in digest (1-10)
    "max_events_per_topic": 3,    # Maximum events per topic (1-5)
    "max_articles_per_topic": 30, # Maximum articles per topic (10-50)
    
    # Content preferences
    "include_opinions": True,     # Include opinion pieces
    "include_impacts": True,      # Include impact analysis
    
    # Delivery preferences
    "preferred_time": "08:00",    # Preferred delivery time (HH:MM)
    "enabled": True,              # Whether digest generation is enabled
}
```

### Django Settings

```python
# Digest system settings
DIGEST_DEFAULT_STRATEGY = 'articles_based'
DIGEST_MAX_GENERATION_TIME = 300  # seconds
DIGEST_DEFAULT_TIME_WINDOW = '48h'

# AI model settings
OPENAI_MODEL_DIGEST = 'gpt-4o-mini'
ANTHROPIC_MODEL_DIGEST = 'claude-3-haiku-20240307'

# Cost limits
DIGEST_MAX_COST_PER_DIGEST = 0.50  # USD
DIGEST_DAILY_COST_LIMIT = 10.00    # USD per day
```

## 📈 Response Formats

### Success Response

```python
{
    "success": True,
    "data": {
        # Response data
    },
    "message": "Optional success message",
    "timestamp": "2024-12-21T10:30:00Z"
}
```

### Error Response

```python
{
    "success": False,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Human-readable error message",
        "details": {
            "field": "Specific field error"
        }
    },
    "timestamp": "2024-12-21T10:30:00Z"
}
```

### Common Error Codes

- `AUTHENTICATION_REQUIRED`: User not authenticated
- `PERMISSION_DENIED`: User lacks required permissions
- `VALIDATION_ERROR`: Invalid request data
- `NOT_FOUND`: Requested resource not found
- `RATE_LIMIT_EXCEEDED`: Too many requests
- `GENERATION_FAILED`: Digest generation failed
- `INSUFFICIENT_CONTENT`: Not enough content for digest
- `AI_PROVIDER_ERROR`: AI service unavailable

This API reference provides complete documentation for integrating with and extending the Daily Digest System.
