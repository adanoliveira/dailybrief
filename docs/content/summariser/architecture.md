# Architecture Overview - AI Content Summarization Service

> **System design and component relationships for the 4-stage AI summarization pipeline**

This document provides a high-level overview of the summarization service architecture, explaining how components interact and the design decisions behind the implementation.

## 📋 Table of Contents

- [System Overview](#system-overview)
- [Component Architecture](#component-architecture)
- [Data Flow](#data-flow)
- [Integration Points](#integration-points)
- [Design Patterns](#design-patterns)
- [Scalability Considerations](#scalability-considerations)

## System Overview

### 🎯 **Design Goals**

The summarization service was designed with these core principles:

- **Reliability**: Graceful error handling and automatic recovery
- **Performance**: Cost-effective processing under $0.0005 per article
- **Quality**: Multi-stage verification to prevent hallucinations
- **Scalability**: Async processing with horizontal scaling capability
- **Maintainability**: Clean separation of concerns and testable components

### 🏗️ **High-Level Architecture**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend UI   │────│   REST APIs     │────│  Core Service   │
│                 │    │                 │    │                 │
│ • SummaryBlock  │    │ • Generate      │    │ • Pipeline      │
│ • Generate Btn  │    │ • Status Poll   │    │ • Stage Mgmt    │
│ • Status Poll   │    │ • CORS Support  │    │ • Error Handle  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                       ┌─────────────────┐             │
                       │  AI Providers   │◄────────────┘
                       │                 │
                       │ • OpenAI GPT    │
                       │ • Embedding API │
                       │ • Rate Limiting │
                       └─────────────────┘
                                │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Async Tasks    │    │   Data Models   │    │   Database      │
│                 │    │                 │    │                 │
│ • Celery Queue  │────│ • Domain Objects│────│ • PostgreSQL    │
│ • Retry Logic   │    │ • Relationships │    │ • pgvector      │
│ • Batch Proc    │    │ • Validation    │    │ • Indexes       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Component Architecture

### 🔧 **Core Service Layer**

#### **SummarizationService** (Orchestrator)
```python
class SummarizationService:
    """Main business logic coordinator"""
    
    def __init__(self):
        self.ai_service = get_ai_service()      # Dependency injection
        self.prompts = SummarizationPrompts()   # Domain-specific prompts
        # Configuration from Django settings
    
    def summarize_article(self, article, force_regenerate=False):
        """Main entry point - orchestrates entire pipeline"""
        # 1. Validate content and prerequisites
        # 2. Execute 4-stage pipeline
        # 3. Handle errors and performance tracking
        # 4. Store results and update article status
```

**Responsibilities:**
- Pipeline orchestration and stage coordination
- Error handling and transaction management  
- Performance tracking and cost calculation
- Integration with AI providers and database models

#### **SummarizationPrompts** (Prompt Engineering)
```python
class SummarizationPrompts:
    """Centralized prompt templates and AI configuration"""
    
    TEMPLATE_VERSION = "v1.0"  # Versioning for A/B testing
    
    @staticmethod
    def rbc_compression_prompt(article_text: str) -> str:
        """Stage 1: Content → ≤25 labeled bullets"""
    
    @staticmethod  
    def skeleton_summary_prompt(rbc_json: str) -> str:
        """Stage 2: Bullets → structured summary"""
    
    # ... additional prompt methods
```

**Responsibilities:**
- Domain-specific prompt engineering for each stage
- AI model configuration and parameter management
- Output validation and JSON repair utilities
- Template versioning and A/B testing support

### 📊 **Data Architecture**

#### **Domain Models** (Rich Data Objects)
```python
# Pipeline tracking
class SummarizationRequest(models.Model):
    """Request lifecycle and performance monitoring"""
    status = models.CharField()              # Current pipeline stage
    stages_completed = models.JSONField()    # Progress tracking
    total_cost_usd = models.DecimalField()   # Cost accumulation
    
# Stage 1 output
class ArticleRBC(models.Model):
    """Rich Bullet Compression storage"""
    bullets = models.JSONField()            # ≤25 labeled bullets
    compression_ratio = property()          # Calculated metric
    bullets_by_type = property()            # Organized by label
    
# Stage 2 output
class ArticleSummary(models.Model):
    """Structured summary for end users"""
    headline = models.CharField()           # ≤15 words
    abstract = models.TextField()           # ≤60 words  
    facts = models.JSONField()              # Key facts array
    full_summary_dict = property()          # Complete JSON representation
    
# Vector search
class ArticleEmbedding(models.Model):
    """Semantic search capabilities"""
    embedding = VectorField(dimensions=1536) # pgvector integration
    find_similar = classmethod()             # Similarity search
```

**Design Patterns:**
- **One-to-One Relationships**: Clean data modeling with Article entity
- **Rich Domain Models**: Business logic embedded in model methods
- **Property Methods**: Calculated fields for derived data
- **Class Methods**: Domain-specific query operations

### ⚡ **Async Processing Layer**

#### **Celery Task Architecture**
```python
@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def summarize_article_pipeline(self, article_id: int, force_regenerate: bool = False):
    """Main processing task with smart retry logic"""
    
    try:
        # Get service and execute pipeline
        service = get_summarization_service()
        result = service.summarize_article(article, force_regenerate)
        
        if result.success:
            return {'success': True, 'article_id': article_id, ...}
        else:
            # Smart retry based on failure type
            if result.failed_stage in ['rbc_compression', 'skeleton_summary']:
                raise self.retry(countdown=300)  # Retry transient failures
            return {'success': False, 'error': result.error_message}
            
    except Exception as e:
        # System error retry logic
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=600)
        return {'success': False, 'error': str(e)}
```

**Task Features:**
- **Smart Retry Logic**: Different strategies for different failure types
- **Resource Management**: Controlled queue processing with limits
- **Batch Operations**: Parallel processing for bulk operations
- **Health Monitoring**: Service status and performance tracking

## Data Flow

### 🔄 **End-to-End Processing Flow**

```
User Action (Frontend)
│
├─ Generate Button Click
│  └─ handleGenerateSummary()
│     └─ generateArticleSummaryLogic()
│        └─ API Call: POST /articles/{id}/generate-summary/
│
API Endpoint (Backend)
│
├─ generate_article_summary()
│  ├─ Validate article and content
│  ├─ Check existing summaries
│  └─ Queue Celery task OR process synchronously
│
Async Processing (Celery)
│
├─ summarize_article_pipeline.delay()
│  └─ SummarizationService.summarize_article()
│     │
│     ├─ Stage 1: RBC Compression
│     │  ├─ Smart truncate content (≤15K chars)
│     │  ├─ Generate RBC prompt
│     │  ├─ Call AI service (GPT-4o-mini)
│     │  ├─ Parse and validate JSON
│     │  └─ Store ArticleRBC instance
│     │
│     ├─ Stage 2: Skeleton Summary
│     │  ├─ Convert RBC to JSON prompt
│     │  ├─ Call AI service for summary
│     │  ├─ Validate structure and constraints
│     │  └─ Prepare for critic review
│     │
│     ├─ Stage 3: Critic Review (Conditional)
│     │  ├─ Check if critic needed (heuristics)
│     │  ├─ Generate critic prompt
│     │  ├─ Verify faithfulness to source
│     │  └─ Identify issues for repair
│     │
│     ├─ Stage 4: Repair (If Needed)
│     │  ├─ Generate repair prompt with issues
│     │  ├─ Call AI service for fixes
│     │  ├─ Validate repaired output
│     │  └─ Update repair tracking
│     │
│     ├─ Stage 5: Embedding Generation
│     │  ├─ Combine headline + abstract
│     │  ├─ Call embedding API
│     │  ├─ Store in pgvector
│     │  └─ Enable semantic search
│     │
│     └─ Finalization
│        ├─ Store ArticleSummary instance
│        ├─ Update Article status and metrics
│        ├─ Calculate total cost and duration
│        └─ Return SummarizationResult
│
Status Polling (Frontend)
│
├─ pollForSummaryCompletion()
│  └─ Repeated calls to GET /articles/{id}/summary-status/
│     └─ Returns current status and result when complete
│
Result Display
│
└─ SummaryBlock component renders structured summary
   ├─ Headline (≤15 words)
   ├─ Abstract (≤60 words)  
   ├─ Key Facts (3-6 items)
   ├─ Opinions (Speaker: statement)
   └─ Impact bullets (≤3 items)
```

### 📊 **Data Transformation Pipeline**

```
Article Content (Input)
│
├─ Content Selection Priority:
│  ├─ 1. clean_content (from processor)
│  ├─ 2. basic_content (from processor)
│  └─ 3. content (legacy field)
│
├─ Smart Truncation (≤15K chars)
│  └─ Truncate at sentence boundaries
│
Stage 1: Rich Bullet Compression
│
├─ Input: Raw article text
├─ Output: ≤25 labeled bullets
│  ├─ [FACT] factual statements
│  ├─ [STAT] statistics and numbers
│  ├─ [QUOTE] direct quotations
│  ├─ [OPINION] viewpoints and analysis
│  └─ [CONTEXT] background information
│
Stage 2: Skeleton Summary Generation
│
├─ Input: RBC bullets JSON
├─ Output: Structured summary
│  ├─ headline: ≤15 words
│  ├─ abstract: ≤60 words
│  ├─ facts: 3-6 key facts (verbatim from bullets)
│  ├─ opinions: Speaker attribution format
│  └─ impact: ≤3 impact statements
│
Stage 3: Quality Verification
│
├─ Input: RBC + Summary
├─ Critic Triggers:
│  ├─ Abstract >60 words
│  ├─ Facts count <3
│  ├─ Contains "UNCERTAIN" flags
│  └─ Complex article indicators
├─ Output: Faithfulness assessment
│  ├─ faithful: true/false
│  ├─ issues: Array of specific problems
│  └─ confidence: 0.0-1.0 score
│
Stage 4: Repair (Conditional)
│
├─ Input: Original summary + Issues list
├─ Process: Fix identified problems
├─ Output: Corrected summary
│  └─ Same structure as Stage 2
│
Stage 5: Vector Embedding
│
├─ Input: headline + " - " + abstract
├─ Model: text-embedding-3-small
├─ Output: 1536-dimensional vector
└─ Storage: pgvector for similarity search
```

## Integration Points

### 🔗 **External Dependencies**

#### **AI Providers Service Integration**
```python
# apps/aiproviders/services.py integration
def _stage_1_rbc_compression(self, content: str, content_source: str):
    # Use centralized AI service
    ai_result = self.ai_service.complete_text(
        prompt=self.prompts.rbc_compression_prompt(content),
        **self.prompts.get_prompt_metadata('rbc_compression')
    )
    
    # Standardized result format
    return {
        'success': True,
        'data': parsed_data,
        'cost_usd': self._calculate_cost(ai_result.usage),
        'processing_time_ms': ai_result.processing_time_ms
    }
```

#### **Article Model Integration**
```python
# apps/articles/models.py extensions
class Article(models.Model):
    # Summarization status tracking
    summarization_status = models.CharField(choices=SummarizationStatus.choices)
    summarization_attempts = models.IntegerField(default=0)
    
    # Performance metrics
    summarized_at = models.DateTimeField(null=True)
    summarization_cost_usd = models.DecimalField(null=True)
    
    # Business logic properties
    @property
    def best_content_for_summarization(self) -> Tuple[str, str]:
        """Priority: clean_content → basic_content → content"""
    
    def can_generate_summary(self) -> bool:
        """Business rules for summarization eligibility"""
```

### 🔄 **API Integration Patterns**

#### **RESTful Endpoint Design**
```python
# Async processing pattern
POST /api/articles/{id}/generate-summary/
{
    "async": true,              # Processing mode
    "forceRegenerate": false    # Regeneration flag
}

# Response for async mode
{
    "success": true,
    "status": "processing",
    "taskId": "celery-task-uuid",
    "pollUrl": "/api/articles/{id}/summary-status/"
}

# Status polling endpoint
GET /api/articles/{id}/summary-status/
{
    "status": "completed",
    "summary": { /* structured summary */ },
    "metadata": { /* performance data */ }
}
```

#### **Frontend Integration Pattern**
```typescript
// Business logic separation
const result = await generateArticleSummaryLogic(articleId, { async: true });

if (result.success && result.status === 'completed') {
    // Update UI with summary
    setArticle(prev => ({ ...prev, summary: result.summary }));
} else if (!result.success) {
    // Handle error state
    setSummaryError(result.error);
}
```

## Design Patterns

### 🏛️ **Architectural Patterns**

#### **Domain-Driven Design (DDD)**
- **Domain Models**: Rich objects with business behavior
- **Service Layer**: Orchestration and business logic
- **Repository Pattern**: Data access abstraction
- **Domain Events**: Pipeline stage completion tracking

#### **Factory Pattern**
```python
def get_summarization_service() -> SummarizationService:
    """Factory function for service creation with dependencies."""
    return SummarizationService()

def get_ai_service():
    """Centralized AI provider factory from aiproviders service."""
    return AIProviderFactory.create_service(settings.AI_PROVIDER)
```

#### **Strategy Pattern**
```python
class SummarizationPrompts:
    """Different strategies for different processing stages"""
    
    def get_prompt_metadata(self, stage: str) -> Dict[str, Any]:
        """Stage-specific configuration strategy"""
        configs = {
            'rbc_compression': {
                'temperature': 0.3,
                'max_tokens': 8192,
                'model_preference': 'gpt-4o-mini'
            },
            'skeleton_summary': {
                'temperature': 0.25,
                'max_tokens': 4096,
                'model_preference': 'gpt-4o-mini'
            }
            # ... stage-specific strategies
        }
        return configs.get(stage, {})
```

#### **Command Pattern**
```python
@shared_task
def summarize_article_pipeline(article_id: int, force_regenerate: bool = False):
    """Encapsulates summarization request as command object"""
    
    # Command execution with full context
    return {
        'command': 'summarize_article',
        'article_id': article_id,
        'force_regenerate': force_regenerate,
        'result': execution_result
    }
```

### 🔒 **Error Handling Patterns**

#### **Circuit Breaker Pattern**
```python
def _execute_pipeline(self, article, content, content_source, request):
    """Fail-fast with detailed error categorization"""
    
    # Stage 1 failure
    rbc_result = self._stage_1_rbc_compression(content, content_source)
    if not rbc_result['success']:
        return SummarizationResult(
            success=False,
            failed_stage='rbc_compression',
            error_message=rbc_result['error']
        )
    
    # Continue only if previous stage succeeded
    # Prevents cascade failures and resource waste
```

#### **Retry Pattern with Exponential Backoff**
```python
@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def summarize_article_pipeline(self, article_id, force_regenerate=False):
    try:
        # Processing logic
        pass
    except (RateLimitError, APITimeoutError):
        # Transient errors - retry with backoff
        countdown = 300 * (2 ** self.request.retries)  # Exponential backoff
        raise self.retry(countdown=countdown)
    except ContentValidationError:
        # Permanent errors - do not retry
        return {'success': False, 'error': 'Permanent failure'}
```

## Scalability Considerations

### ⚡ **Performance Optimization**

#### **Async Processing Architecture**
```python
# Horizontal scaling through queue distribution
CELERY_TASK_ROUTES = {
    'apps.content.summariser.tasks.summarize_article_pipeline': {
        'queue': 'summarization_high_priority'
    },
    'apps.content.summariser.tasks.batch_summarize_articles': {
        'queue': 'summarization_batch'
    },
    'apps.content.summariser.tasks.process_pending_summarizations': {
        'queue': 'summarization_background'
    }
}

# Worker scaling configuration
# High priority: 4 workers for real-time requests
# Batch: 2 workers for bulk operations  
# Background: 1 worker for automated processing
```

#### **Database Optimization**
```sql
-- Optimized indexing strategy
CREATE INDEX CONCURRENTLY idx_article_summarization_status 
ON articles_article (summarization_status) 
WHERE summarization_status IN ('pending', 'processing');

CREATE INDEX CONCURRENTLY idx_summarization_request_status_date
ON content_summarization_request (status, created_at);

-- pgvector similarity search optimization
CREATE INDEX CONCURRENTLY idx_article_embedding_vector
ON content_article_embedding 
USING hnsw (embedding vector_l2_ops)
WITH (m = 16, ef_construction = 64);
```

#### **Cost Management**
```python
# Smart batching for embedding generation
@shared_task
def generate_embeddings_batch(article_ids: List[int]):
    """Batch up to 96 articles per API call for cost efficiency"""
    
    # OpenAI embedding API supports batch processing
    # Reduces per-request overhead and improves throughput
    texts = []
    for article_id in article_ids[:96]:  # API limit
        summary = ArticleSummary.objects.get(article_id=article_id)
        texts.append(f"{summary.headline} - {summary.abstract}")
    
    # Single API call for multiple embeddings
    embeddings = self.ai_service.create_embeddings(texts)
    
    # Bulk database insertion
    embedding_objects = []
    for i, article_id in enumerate(article_ids):
        embedding_objects.append(ArticleEmbedding(
            article_id=article_id,
            embedding=embeddings[i],
            embedding_text=texts[i]
        ))
    
    ArticleEmbedding.objects.bulk_create(embedding_objects, ignore_conflicts=True)
```

### 📈 **Scaling Strategies**

#### **Horizontal Scaling**
- **Queue Distribution**: Separate queues for different priority levels
- **Worker Specialization**: Dedicated workers for different task types
- **Load Balancing**: Distribute processing across multiple instances
- **Database Sharding**: Future consideration for embedding storage

#### **Vertical Scaling**
- **Memory Optimization**: Efficient JSON handling and caching
- **CPU Optimization**: Parallel processing within single tasks
- **I/O Optimization**: Connection pooling and batch operations
- **Cache Strategy**: Redis caching for frequently accessed summaries

#### **Resource Management**
```python
class SummarizationService:
    def __init__(self):
        # Configurable resource limits
        self.max_content_chars = getattr(settings, 'SUMMARIZATION_MAX_CONTENT_CHARS', 15000)
        self.max_concurrent_requests = getattr(settings, 'SUMMARIZATION_MAX_CONCURRENT', 10)
        self.enable_critic = getattr(settings, 'SUMMARIZATION_ENABLE_CRITIC', True)
        
    def _smart_truncate(self, text: str, max_chars: int) -> Tuple[str, Optional[int]]:
        """Intelligent content truncation to stay within token limits"""
        if len(text) <= max_chars:
            return text, None
        
        # Find last complete sentence within limit
        truncated = text[:max_chars]
        last_sentence_end = max(
            truncated.rfind('.'),
            truncated.rfind('!'),
            truncated.rfind('?')
        )
        
        if last_sentence_end > max_chars * 0.8:  # Keep if >80% of content
            return truncated[:last_sentence_end + 1], last_sentence_end + 1
        else:
            return truncated, max_chars
```

---

## Summary

The AI Content Summarization Service architecture demonstrates:

✅ **Clean Separation of Concerns**: Domain logic, data access, and presentation layers clearly separated  
✅ **Scalable Design**: Async processing with horizontal scaling capabilities  
✅ **Robust Error Handling**: Multiple failure modes handled gracefully  
✅ **Performance Optimization**: Cost-effective processing with intelligent resource management  
✅ **Integration Patterns**: Clean interfaces with existing DailyBrief systems  

The architecture supports both current MVP requirements and future enhancements while maintaining code quality and operational reliability. 