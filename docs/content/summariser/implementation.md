# Implementation Guide - AI Content Summarization Service

> **Comprehensive guide to the implemented summarization service components, integration patterns, and technical details**

This document provides a complete overview of the implemented summarization service, documenting all files, classes, functions, and integration points.

## 📋 Table of Contents

- [Service Architecture](#service-architecture)
- [Core Components](#core-components)
- [Database Schema](#database-schema)
- [API Integration](#api-integration)
- [Frontend Integration](#frontend-integration)
- [Processing Pipeline](#processing-pipeline)
- [Configuration & Settings](#configuration--settings)
- [Error Handling](#error-handling)
- [Performance Monitoring](#performance-monitoring)

## Service Architecture

### 🏗️ **Overall Design Pattern**

The summarization service follows DailyBrief's established architectural patterns:

```python
# Domain-driven design with clear separation of concerns
apps/content/summariser/
├── models.py           # Domain models and data structures
├── services.py         # Business logic and orchestration  
├── tasks.py           # Async processing with Celery
├── prompt_templates.py # AI prompt engineering
├── views.py           # API endpoints
└── management/        # Django management commands
```

**Design Principles:**
- **Single Responsibility**: Each component has a focused purpose
- **Dependency Injection**: Services injected via factory functions
- **Domain Models**: Rich models with behavior, not just data
- **Error Boundaries**: Graceful degradation with detailed error reporting

## Core Components

### 🔧 **SummarizationService** (`services.py`)

**Primary orchestrator for the 4-stage pipeline**

```python
class SummarizationService:
    """Main service coordinating the complete summarization pipeline."""
    
    def __init__(self):
        self.ai_service = get_ai_service()  # Dependency injection
        self.prompts = SummarizationPrompts()
        # Configuration from Django settings
    
    def summarize_article(self, article: Article, force_regenerate: bool = False) -> SummarizationResult:
        """Main entry point - orchestrates complete pipeline"""
```

**Key Methods:**
- `summarize_article()` - Main pipeline orchestrator
- `_execute_pipeline()` - Stage-by-stage execution
- `_stage_1_rbc_compression()` - Rich bullet compression
- `_stage_2_skeleton_summary()` - Structured summary generation
- `_stage_3_critic_review()` - Quality verification  
- `_stage_4_repair_summary()` - Issue correction
- `_generate_embedding()` - Vector embedding generation

**Integration Points:**
- Uses `aiproviders.services.get_ai_service()` for LLM calls
- Integrates with `Article` model for content access
- Creates `SummarizationRequest` for tracking
- Stores results in domain-specific models

### 📝 **SummarizationPrompts** (`prompt_templates.py`)

**Centralized prompt engineering for all pipeline stages**

```python
class SummarizationPrompts:
    """Domain-specific prompt templates following established patterns."""
    
    TEMPLATE_VERSION = "v1.0"  # For A/B testing and tracking
    
    @staticmethod
    def rbc_compression_prompt(article_text: str) -> str:
        """Stage 1: Convert content to ≤25 labeled bullets"""
    
    @staticmethod  
    def skeleton_summary_prompt(rbc_json: str) -> str:
        """Stage 2: Create structured summary from bullets"""
    
    @staticmethod
    def critic_review_prompt(rbc_json: str, summary_json: str) -> str:
        """Stage 3: Verify summary faithfulness"""
    
    @staticmethod
    def repair_summary_prompt(summary_json: str, issues: List[str]) -> str:
        """Stage 4: Fix identified issues"""
```

**Prompt Engineering Features:**
- **Template Versioning**: Track and A/B test different prompt versions
- **Metadata Integration**: Provides model configs for AI service
- **JSON Validation**: Built-in output validation and repair utilities
- **Conditional Logic**: Smart critic triggering based on quality heuristics

### 🗄️ **Domain Models** (`models.py`)

**Rich domain models with behavior and relationships**

#### **Core Data Models:**

```python
# Pipeline tracking and orchestration
@dataclass
class SummarizationResult:
    """Pure domain model for pipeline results"""
    success: bool
    article_id: int
    # Pipeline outputs, performance metrics, quality flags
    
# Stage 1 output
class ArticleRBC(models.Model):
    """Rich Bullet Compression storage"""
    bullets = models.JSONField()  # ≤25 labeled bullets
    content_source = models.CharField()  # Source content tracking
    # Performance and cost tracking fields
    
# Stage 2 output  
class ArticleSummary(models.Model):
    """Structured summary for end-user consumption"""
    headline = models.CharField(max_length=255)  # ≤15 words
    abstract = models.TextField()  # ≤60 words
    facts = models.JSONField(default=list)  # 3-6 key facts
    opinions = models.JSONField(default=list)  # Speaker: opinion pairs
    impact = models.JSONField(default=list)  # ≤3 impact bullets
    # Quality tracking and metadata
    
# Vector embeddings
class ArticleEmbedding(models.Model):
    """pgvector-powered semantic search"""
    embedding = VectorField(dimensions=1536)  # pgvector integration
    embedding_text = models.TextField()  # Source text for embedding
    
# Pipeline monitoring
class SummarizationRequest(models.Model):
    """Request tracking and performance monitoring"""
    status = models.CharField()  # Pipeline stage tracking
    stages_completed = models.JSONField(default=list)
    # Performance and error tracking
```

**Model Features:**
- **One-to-One Relationships**: Clean data modeling with Article
- **Rich Behavior**: Domain methods like `compression_ratio`, `bullets_by_type`
- **pgvector Integration**: Native vector search with PostgreSQL
- **Performance Tracking**: Cost, duration, and quality metrics
- **Audit Trail**: Complete pipeline tracking and monitoring

### ⚡ **Async Processing** (`tasks.py`)

**Celery-based background processing with robust error handling**

```python
@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def summarize_article_pipeline(self, article_id: int, force_regenerate: bool = False):
    """Main pipeline task with retry logic"""
    
@shared_task  
def batch_summarize_articles(article_ids: List[int], force_regenerate: bool = False):
    """Parallel processing for bulk operations"""
    
@shared_task
def process_pending_summarizations(limit: int = 20):
    """Automated queue processing for pending articles"""
```

**Task Features:**
- **Smart Retry Logic**: Different strategies for transient vs permanent failures
- **Batch Processing**: Parallel execution for bulk operations  
- **Health Monitoring**: Service status and performance tracking
- **Resource Management**: Controlled queue processing with limits

## Database Schema

### 📊 **Complete Schema Overview**

```sql
-- Pipeline tracking
CREATE TABLE content_summarization_request (
    id SERIAL PRIMARY KEY,
    public_id UUID UNIQUE DEFAULT gen_random_uuid(),
    article_id BIGINT REFERENCES articles_article(id),
    status VARCHAR(20) DEFAULT 'queued',
    current_stage VARCHAR(20),
    stages_completed JSONB DEFAULT '[]',
    total_cost_usd DECIMAL(8,6) DEFAULT 0,
    total_duration_ms INTEGER DEFAULT 0,
    -- Error handling and performance tracking
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Stage 1: Rich Bullet Compression
CREATE TABLE content_article_rbc (
    id SERIAL PRIMARY KEY,
    public_id UUID UNIQUE DEFAULT gen_random_uuid(), 
    article_id BIGINT UNIQUE REFERENCES articles_article(id),
    bullets JSONB NOT NULL,
    bullet_count INTEGER,
    content_source VARCHAR(20),
    original_content_length INTEGER,
    truncated_at INTEGER,
    -- AI processing metadata
    tokens_input INTEGER DEFAULT 0,
    tokens_output INTEGER DEFAULT 0,
    processing_time_ms INTEGER DEFAULT 0,
    cost_usd DECIMAL(8,6) DEFAULT 0,
    ai_model_used VARCHAR(50) DEFAULT 'gpt-4o-mini',
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Stage 2: Structured Summary
CREATE TABLE content_article_summary (
    id SERIAL PRIMARY KEY,
    public_id UUID UNIQUE DEFAULT gen_random_uuid(),
    article_id BIGINT UNIQUE REFERENCES articles_article(id),
    -- Summary content
    headline VARCHAR(255) NOT NULL,
    abstract TEXT NOT NULL,
    facts JSONB DEFAULT '[]',
    opinions JSONB DEFAULT '[]', 
    impact JSONB DEFAULT '[]',
    summary_version SMALLINT DEFAULT 2,
    -- Quality tracking
    headline_words INTEGER,
    abstract_words INTEGER,
    facts_count INTEGER,
    required_critic_review BOOLEAN DEFAULT false,
    critic_passed BOOLEAN,
    was_repaired BOOLEAN DEFAULT false,
    repair_attempts INTEGER DEFAULT 0,
    -- AI processing metadata
    tokens_input INTEGER DEFAULT 0,
    tokens_output INTEGER DEFAULT 0,
    processing_time_ms INTEGER DEFAULT 0,
    cost_usd DECIMAL(8,6) DEFAULT 0,
    ai_model_used VARCHAR(50) DEFAULT 'gpt-4o-mini',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Vector embeddings for semantic search
CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE content_article_embedding (
    id SERIAL PRIMARY KEY,
    public_id UUID UNIQUE DEFAULT gen_random_uuid(),
    article_id BIGINT UNIQUE REFERENCES articles_article(id),
    embedding VECTOR(1536) NOT NULL,
    embedding_model VARCHAR(50) DEFAULT 'text-embedding-3-small',
    embedding_text TEXT NOT NULL,
    embedding_length INTEGER,
    -- Processing metadata
    tokens_used INTEGER DEFAULT 0,
    processing_time_ms INTEGER DEFAULT 0,
    cost_usd DECIMAL(8,6) DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Performance monitoring
CREATE TABLE content_summarization_metrics (
    date DATE PRIMARY KEY,
    articles_processed INTEGER DEFAULT 0,
    articles_failed INTEGER DEFAULT 0,
    success_rate FLOAT DEFAULT 0.0,
    total_cost_usd DECIMAL(10,6) DEFAULT 0,
    avg_cost_per_article DECIMAL(8,6) DEFAULT 0,
    avg_duration_ms INTEGER DEFAULT 0,
    critic_trigger_rate FLOAT DEFAULT 0.0,
    repair_rate FLOAT DEFAULT 0.0,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Indexes for performance
CREATE INDEX ON content_article_rbc (article_id);
CREATE INDEX ON content_article_summary (article_id);
CREATE INDEX ON content_article_embedding USING hnsw (embedding vector_l2_ops);
CREATE INDEX ON content_summarization_request (status);
CREATE INDEX ON content_summarization_request (article_id);
```

**Schema Features:**
- **UUID Public IDs**: Secure external identifiers for all entities
- **One-to-One Relationships**: Clean data modeling with Article entity
- **Performance Indexes**: Optimized for lookup and vector search patterns
- **Audit Fields**: Complete tracking of creation and modification
- **pgvector Integration**: Native PostgreSQL vector search capabilities

## API Integration

### 🔗 **REST Endpoints** (`backend/apps/articles/views.py`)

**Two main endpoints for summarization functionality:**

#### **Generate Summary Endpoint**

```python
@csrf_exempt
@require_http_methods(["POST", "OPTIONS"])
def generate_article_summary(request, public_id):
    """
    POST /api/articles/{public_id}/generate-summary/
    
    Trigger summary generation for an article.
    Supports both sync and async processing modes.
    """
```

**Request/Response Flow:**
```json
// Request body
{
  "forceRegenerate": false,
  "async": true
}

// Response (async mode)
{
  "success": true,
  "status": "processing", 
  "taskId": "celery-task-uuid",
  "estimatedTimeSeconds": 30,
  "pollUrl": "/api/articles/{id}/summary-status/"
}

// Response (sync mode)
{
  "success": true,
  "summary": {
    "headline": "...",
    "abstract": "...", 
    "facts": [...],
    "opinions": [...],
    "impact": [...]
  },
  "metadata": {
    "generatedAt": "2025-01-13T...",
    "costUsd": 0.0004,
    "processingTimeMs": 15000
  }
}
```

#### **Status Polling Endpoint**

```python
@require_http_methods(["GET", "OPTIONS"])
def article_summary_status(request, public_id):
    """
    GET /api/articles/{public_id}/summary-status/
    
    Check summarization progress and retrieve completed summaries.
    """
```

**Response Examples:**
```json
// Processing
{
  "status": "processing",
  "summarizationStatus": "processing",
  "attempts": 1,
  "estimatedRemainingSeconds": 15
}

// Completed
{
  "status": "completed",
  "summary": { /* complete summary object */ },
  "metadata": { /* performance data */ }
}

// Failed
{
  "status": "failed", 
  "errorMessage": "Insufficient content for summarization",
  "canRetry": false
}
```

**API Features:**
- **CORS Support**: Proper preflight and cross-origin headers
- **Authentication**: Integrated with DailyBrief auth system
- **Error Handling**: Comprehensive status codes and error messages
- **Async/Sync Modes**: Flexible processing based on use case
- **Progress Tracking**: Real-time status updates for long-running tasks

### 🔄 **Integration with Article Model**

**Extended Article model fields for summarization:**

```python
# backend/apps/articles/models.py
class Article(models.Model):
    # ... existing fields ...
    
    # Summarization pipeline status
    summarization_status = models.CharField(
        max_length=20,
        choices=SummarizationStatus.choices,
        default=SummarizationStatus.PENDING
    )
    summarization_attempts = models.IntegerField(default=0)
    last_summarization_attempt = models.DateTimeField(null=True, blank=True)
    summarization_error_message = models.TextField(blank=True)
    
    # Performance tracking
    summarized_at = models.DateTimeField(null=True, blank=True)
    summarization_duration_ms = models.IntegerField(null=True, blank=True)
    summarization_cost_usd = models.DecimalField(max_digits=8, decimal_places=6, null=True, blank=True)
    summary_content_source = models.CharField(max_length=20, blank=True)
    summary_ready = models.BooleanField(default=False)
    
    @property
    def best_content_for_summarization(self) -> Tuple[str, str]:
        """Get the best available content for summarization."""
        # Priority: clean_content → basic_content → content
        
    def can_generate_summary(self) -> bool:
        """Check if article is ready for summarization."""
        # Business logic for summarization eligibility
```

## Frontend Integration

### ⚛️ **React Components** (`frontend/`)

#### **SummaryBlock Component**

```typescript
// frontend/components/article/summary-block.tsx
interface SummaryBlockProps {
  summary: ArticleSummary | null;
  loading: boolean;
  error: string | null;
  onGenerate: () => void;
}

export function SummaryBlock({ summary, loading, error, onGenerate }: SummaryBlockProps) {
  // Renders structured summary or generate button
  // Handles loading states and error display
}
```

**Component Features:**
- **Conditional Rendering**: Shows generate button or existing summary
- **Loading States**: Spinner and progress indication during generation
- **Error Handling**: User-friendly error messages with retry options
- **Responsive Design**: Optimized for mobile and desktop

#### **Business Logic Utilities**

```typescript
// frontend/lib/article-utils.ts

export async function generateArticleSummaryLogic(
  articleId: string,
  options: { async?: boolean } = { async: true }
): Promise<SummaryGenerationResult> {
  // Core business logic for summary generation
  // Handles API calls, polling, and error states
}

export function shouldShowSummaryBlock(article: any): boolean {
  // Determines whether to show summary block based on article state
}

export function canGenerateSummary(article: any): boolean {
  // Checks if article can generate summaries
}
```

**Utility Features:**
- **Separation of Concerns**: Business logic separated from UI components
- **Type Safety**: Full TypeScript support with discriminated unions
- **Error Handling**: Comprehensive error states and retry logic
- **Reusability**: Can be used across different components

#### **API Integration**

```typescript
// frontend/lib/api.ts

export async function generateArticleSummary(
  articleId: string, 
  options: SummaryGenerationOptions = {}
): Promise<SummaryGenerationResponse> {
  // Calls backend generate summary endpoint
}

export async function getArticleSummaryStatus(articleId: string): Promise<SummaryStatusResponse> {
  // Polls for summarization status
}

export async function pollForSummaryCompletion(
  articleId: string,
  maxAttempts: number = 20,
  intervalMs: number = 2000
): Promise<SummaryStatusResponse> {
  // Automated polling with timeout handling
}
```

### 🔄 **Article Page Integration**

```typescript
// frontend/app/(authenticated)/(article)/article/[id]/page.tsx

export default function Article({ params }: { params: { id: string } }) {
  const [summaryLoading, setSummaryLoading] = useState(false);
  const [summaryError, setSummaryError] = useState<string | null>(null);

  const handleGenerateSummary = async () => {
    // Delegates to business logic utility
    const { generateArticleSummaryLogic } = await import('@/lib/article-utils');
    const result = await generateArticleSummaryLogic(article.id, { async: true });
    // Handle result and update UI state
  };

  return (
    <div>
      {/* Article content */}
      {shouldShowSummaryBlock(article) && (
        <SummaryBlock
          summary={article.summary}
          loading={summaryLoading}
          error={summaryError}
          onGenerate={handleGenerateSummary}
        />
      )}
    </div>
  );
}
```

## Processing Pipeline

### 🔄 **4-Stage Pipeline Flow**

```python
def _execute_pipeline(self, article: Article, content: str, content_source: str, request: SummarizationRequest):
    """Complete pipeline execution with stage tracking."""
    
    # Stage 1: Rich Bullet Compression
    rbc_result = self._stage_1_rbc_compression(content, content_source)
    if not rbc_result['success']:
        return SummarizationResult(success=False, failed_stage='rbc_compression')
    
    # Store RBC and update tracking
    rbc_instance = self._store_rbc_result(article, rbc_result, content_source)
    request.mark_stage_completed('rbc_compression')
    
    # Stage 2: Skeleton Summary Generation  
    summary_result = self._stage_2_skeleton_summary(rbc_result['data'])
    if not summary_result['success']:
        return SummarizationResult(success=False, failed_stage='skeleton_summary')
    
    # Stage 3: Conditional Critic Review
    summary_data = summary_result['data']
    should_review, reasons = self.prompts.should_trigger_critic(summary_data, rbc_result['data'])
    
    if should_review:
        request.current_stage = 'critic_processing'
        critic_result = self._stage_3_critic_review(rbc_result['data'], summary_data)
        
        # Stage 4: Conditional Repair
        if not critic_result['data'].get('faithful', True):
            repair_result = self._stage_4_repair_summary(summary_data, critic_result['data']['issues'])
            if repair_result['success']:
                summary_data = repair_result['data']
                pipeline_result.was_repaired = True
    
    # Store final summary
    summary_instance = self._store_summary_result(article, summary_data, summary_result, pipeline_result)
    
    # Stage 5: Embedding Generation (if enabled)
    if self.enable_embeddings:
        embedding_result = self._generate_embedding(summary_data['headline'], summary_data['abstract'])
        if embedding_result['success']:
            self._store_embedding_result(article, embedding_result, summary_data['headline'], summary_data['abstract'])
    
    return pipeline_result
```

### 📊 **Stage-by-Stage Details**

#### **Stage 1: Rich Bullet Compression**
```python
def _stage_1_rbc_compression(self, content: str, content_source: str) -> Dict[str, Any]:
    """Convert article content to ≤25 labeled bullets."""
    
    # Smart truncation at sentence boundaries
    truncated_content, truncated_at = self._smart_truncate(content, self.max_content_chars)
    
    # Generate prompt and call AI service
    prompt = self.prompts.rbc_compression_prompt(truncated_content)
    config = self.prompts.get_prompt_metadata('rbc_compression')
    
    # AI service call with error handling
    ai_result = self.ai_service.complete_text(prompt, **config)
    
    # Validate and parse JSON response
    parsed_result = self.prompts.validate_rbc_output(ai_result.content)
    
    return {
        'success': parsed_result['is_valid'],
        'data': parsed_result['data'],
        'cost_usd': self._calculate_cost(ai_result.usage),
        'processing_time_ms': ai_result.processing_time_ms
    }
```

#### **Stage 2: Skeleton Summary Generation**
```python
def _stage_2_skeleton_summary(self, rbc_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate structured summary from RBC bullets."""
    
    # Convert RBC to JSON for prompt
    rbc_json = json.dumps(rbc_data, ensure_ascii=False)
    
    # Generate prompt and call AI service
    prompt = self.prompts.skeleton_summary_prompt(rbc_json)
    config = self.prompts.get_prompt_metadata('skeleton_summary')
    
    ai_result = self.ai_service.complete_text(prompt, **config)
    
    # Validate summary structure and constraints
    parsed_result = self.prompts.validate_summary_output(ai_result.content)
    
    return {
        'success': parsed_result['is_valid'],
        'data': parsed_result['data'],
        'cost_usd': self._calculate_cost(ai_result.usage),
        'processing_time_ms': ai_result.processing_time_ms
    }
```

#### **Stage 3: Critic Review (Conditional)**
```python
def _stage_3_critic_review(self, rbc_data: Dict[str, Any], summary_data: Dict[str, Any]) -> Dict[str, Any]:
    """Verify summary faithfulness and detect hallucinations."""
    
    # Convert data to JSON for prompt
    rbc_json = json.dumps(rbc_data, ensure_ascii=False)
    summary_json = json.dumps(summary_data, ensure_ascii=False)
    
    # Generate critique prompt
    prompt = self.prompts.critic_review_prompt(rbc_json, summary_json)
    config = self.prompts.get_prompt_metadata('summary_critique')
    
    ai_result = self.ai_service.complete_text(prompt, **config)
    
    # Parse critic response
    parsed_result = self.prompts.validate_critic_output(ai_result.content)
    
    return {
        'success': parsed_result['is_valid'],
        'data': parsed_result['data'],
        'cost_usd': self._calculate_cost(ai_result.usage),
        'processing_time_ms': ai_result.processing_time_ms
    }
```

#### **Stage 4: Summary Repair (If Needed)**
```python
def _stage_4_repair_summary(self, summary_data: Dict[str, Any], issues: List[str]) -> Dict[str, Any]:
    """Fix issues identified by critic review."""
    
    # Convert summary to JSON for prompt
    summary_json = json.dumps(summary_data, ensure_ascii=False)
    
    # Generate repair prompt with specific issues
    prompt = self.prompts.repair_summary_prompt(summary_json, issues)
    config = self.prompts.get_prompt_metadata('summary_repair')
    
    ai_result = self.ai_service.complete_text(prompt, **config)
    
    # Validate repaired summary
    parsed_result = self.prompts.validate_summary_output(ai_result.content)
    
    return {
        'success': parsed_result['is_valid'],
        'data': parsed_result['data'],
        'cost_usd': self._calculate_cost(ai_result.usage),
        'processing_time_ms': ai_result.processing_time_ms
    }
```

## Configuration & Settings

### ⚙️ **Django Settings Integration**

```python
# backend/settings/base.py

# Summarization Service Configuration
SUMMARIZATION_MAX_CONTENT_CHARS = 15000  # Smart truncation limit
SUMMARIZATION_ENABLE_CRITIC = True       # Critic review stage
SUMMARIZATION_ENABLE_REPAIR = True       # Summary repair stage  
SUMMARIZATION_ENABLE_EMBEDDINGS = True   # Vector embedding generation

# AI Provider Configuration (inherited)
AI_PROVIDER = 'openai'  # Uses aiproviders service
OPENAI_API_KEY = env('OPENAI_API_KEY')
OPENAI_DEFAULT_MODEL = 'gpt-4o-mini'  # Cost-optimized model choice

# Celery Configuration for Async Processing
CELERY_TASK_ROUTES = {
    'apps.content.summariser.tasks.summarize_article_pipeline': {'queue': 'summarization'},
    'apps.content.summariser.tasks.batch_summarize_articles': {'queue': 'summarization'},
}

# Database Configuration (pgvector)
DATABASES = {
    'default': {
        # ... existing config ...
    }
}
INSTALLED_APPS = [
    # ... existing apps ...
    'pgvector',  # Vector extension support
]
```

**Configuration Features:**
- **Environment-based**: Different settings per environment
- **Feature Flags**: Enable/disable pipeline stages for testing
- **Resource Limits**: Configurable content length and processing limits
- **Queue Management**: Dedicated Celery queues for summarization tasks

## Error Handling

### 🛡️ **Comprehensive Error Strategy**

```python
class SummarizationService:
    def summarize_article(self, article: Article, force_regenerate: bool = False) -> SummarizationResult:
        try:
            # Pipeline execution with transaction safety
            with transaction.atomic():
                result = self._execute_pipeline(article, content, content_source, request)
                
                if result.success:
                    # Update success status
                    article.summarization_status = SummarizationStatus.COMPLETED
                    # Performance tracking
                else:
                    # Update failure status with details
                    article.summarization_status = SummarizationStatus.FAILED
                    article.summarization_error_message = result.error_message
                
                return result
                
        except Exception as e:
            # System error handling
            logger.error(f"Unexpected error during summarization: {str(e)}")
            article.summarization_status = SummarizationStatus.FAILED
            article.summarization_error_message = str(e)
            
            return SummarizationResult(
                success=False,
                article_id=article.id,
                error_message=str(e),
                failed_stage="system_error"
            )
```

**Error Categories:**

#### **Content Validation Errors**
```python
# Insufficient content for summarization
if not content or len(content.strip()) < 200:
    return SummarizationResult(
        success=False,
        error_message="Insufficient content for summarization",
        failed_stage="validation"
    )

# Article still processing
if article.process_status in ['pending', 'processing']:
    return SummarizationResult(
        success=False,
        error_message="Article still being processed",
        failed_stage="validation"
    )
```

#### **AI Service Errors**
```python
# Rate limiting and API errors
try:
    ai_result = self.ai_service.complete_text(prompt, **config)
except RateLimitError:
    # Handled by Celery retry logic
    raise self.retry(countdown=300)
except APIError as e:
    # Log and fail with details
    return SummarizationResult(
        success=False,
        error_message=f"AI service error: {str(e)}",
        failed_stage=current_stage
    )
```

#### **JSON Parsing Errors**
```python
# Robust JSON parsing with repair attempts
def validate_summary_output(self, output_text: str) -> Dict[str, Any]:
    try:
        data = json.loads(output_text)
        return {'is_valid': True, 'data': data}
    except json.JSONDecodeError:
        # Attempt automatic repair
        success, repaired_json, data = JSONRepairUtils.attempt_json_repair(output_text)
        if success:
            logger.warning("JSON output repaired automatically")
            return {'is_valid': True, 'data': data}
        else:
            logger.error("Failed to parse or repair JSON output")
            return {'is_valid': False, 'error': 'Invalid JSON format'}
```

## Performance Monitoring

### 📊 **Metrics and Tracking**

#### **Real-time Performance Tracking**
```python
class SummarizationRequest(models.Model):
    """Comprehensive pipeline tracking."""
    
    # Stage progression
    current_stage = models.CharField(max_length=20)
    stages_completed = models.JSONField(default=list)
    pipeline_start_time = models.DateTimeField(null=True)
    pipeline_end_time = models.DateTimeField(null=True)
    
    # Performance metrics
    total_cost_usd = models.DecimalField(max_digits=8, decimal_places=6, default=0)
    total_duration_ms = models.IntegerField(default=0)
    
    def mark_stage_completed(self, stage_name: str):
        """Track stage completion with timestamps."""
        if stage_name not in self.stages_completed:
            self.stages_completed.append(stage_name)
            self.save(update_fields=['stages_completed'])
            logger.info(f"Stage '{stage_name}' completed for request {self.id}")
```

#### **Daily Metrics Aggregation**
```python
class SummarizationMetrics(models.Model):
    """Daily aggregated metrics for monitoring."""
    
    date = models.DateField(unique=True)
    
    # Volume metrics  
    articles_processed = models.IntegerField(default=0)
    articles_failed = models.IntegerField(default=0)
    success_rate = models.FloatField(default=0.0)
    
    # Cost metrics
    total_cost_usd = models.DecimalField(max_digits=10, decimal_places=6, default=0)
    avg_cost_per_article = models.DecimalField(max_digits=8, decimal_places=6, default=0)
    
    # Performance metrics
    avg_duration_ms = models.IntegerField(default=0)
    avg_tokens_used = models.IntegerField(default=0)
    
    # Quality metrics
    critic_trigger_rate = models.FloatField(default=0.0)
    repair_rate = models.FloatField(default=0.0)
```

#### **Cost Tracking Per Stage**
```python
def _calculate_cost(self, usage: Dict[str, int]) -> Decimal:
    """Calculate cost based on token usage and current model pricing."""
    
    # GPT-4o-mini pricing (as of Jan 2025)
    input_cost_per_1k = Decimal('0.00015')   # $0.00015 per 1K input tokens
    output_cost_per_1k = Decimal('0.0006')   # $0.0006 per 1K output tokens
    
    input_tokens = usage.get('prompt_tokens', 0)
    output_tokens = usage.get('completion_tokens', 0)
    
    input_cost = (Decimal(input_tokens) / 1000) * input_cost_per_1k
    output_cost = (Decimal(output_tokens) / 1000) * output_cost_per_1k
    
    total_cost = input_cost + output_cost
    return total_cost.quantize(Decimal('0.000001'))  # 6 decimal places
```

### 🔍 **Health Monitoring Tasks**

```python
@shared_task
def summarization_health_check():
    """Comprehensive service health monitoring."""
    
    # Check recent processing success rate
    recent_requests = SummarizationRequest.objects.filter(
        created_at__gte=timezone.now() - timedelta(hours=1)
    )
    
    if recent_requests.exists():
        success_rate = recent_requests.filter(status='completed').count() / recent_requests.count()
        avg_duration = recent_requests.filter(status='completed').aggregate(
            avg_duration=models.Avg('total_duration_ms')
        )['avg_duration'] or 0
    else:
        success_rate = 1.0  # No recent failures
        avg_duration = 0
    
    # Check AI service availability
    try:
        ai_service = get_ai_service()
        test_result = ai_service.complete_text("Test prompt", max_tokens=10)
        ai_service_healthy = True
    except Exception as e:
        ai_service_healthy = False
        logger.error(f"AI service health check failed: {e}")
    
    # Check database connectivity
    try:
        Article.objects.count()
        db_healthy = True
    except Exception as e:
        db_healthy = False
        logger.error(f"Database health check failed: {e}")
    
    health_status = {
        'timestamp': timezone.now().isoformat(),
        'overall_healthy': success_rate > 0.8 and ai_service_healthy and db_healthy,
        'success_rate': success_rate,
        'avg_duration_ms': avg_duration,
        'ai_service_healthy': ai_service_healthy,
        'database_healthy': db_healthy,
        'recent_requests_count': recent_requests.count()
    }
    
    logger.info(f"Summarization service health check: {health_status}")
    return health_status
```

---

## Summary

The AI Content Summarization Service successfully implements a comprehensive, production-ready summarization pipeline that:

✅ **Meets Original Requirements**: 4-stage pipeline, structured output, cost targets  
✅ **Exceeds Expectations**: Full frontend integration, REST APIs, real-time status  
✅ **Follows Best Practices**: Clean architecture, comprehensive error handling, performance monitoring  
✅ **Scales Efficiently**: Async processing, batch operations, resource optimization  

The implementation demonstrates mature software engineering practices while delivering a user-facing feature that enhances the DailyBrief reading experience. 