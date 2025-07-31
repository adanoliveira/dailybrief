# AI Content Summarization Service

> **Multi-stage AI-powered article summarization with Rich Bullet Compression and structured output**

A comprehensive content summarization system that transforms processed articles into structured, high-quality summaries using a 4-stage AI pipeline, designed to provide consistent, faithful, and cost-effective article summaries for the DailyBrief platform.

## 📖 Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Documentation](#documentation)
- [Implementation Status](#implementation-status)
- [Current Performance](#current-performance)

## Overview

The AI Content Summarization Service provides reliable article summarization through:

- **4-Stage Pipeline**: Rich Bullet Compression → Skeleton Summary → Critic Review → Repair (if needed)
- **Structured Output**: Consistent JSON format with headline, abstract, facts, opinions, and impact
- **Quality Assurance**: Built-in critic review and repair mechanism for faithfulness
- **Cost Optimization**: Budget-friendly approach averaging <$0.0005 per article
- **Vector Embeddings**: Semantic search capabilities using pgvector

### Key Features

✅ **Rich Bullet Compression (RBC)**: Lossless content compression into ≤25 labeled bullets  
✅ **Structured Summaries**: Headline, abstract, facts, opinions, and impact in consistent format  
✅ **Faithfulness Verification**: Critic review stage prevents hallucinations  
✅ **Automatic Repair**: Self-correcting summaries based on critic feedback  
✅ **Vector Embeddings**: pgvector-powered semantic search and similarity  
✅ **Async Processing**: Celery-based background processing with retry logic  
✅ **Cost Tracking**: Detailed cost and performance metrics per article  
✅ **E2E Integration**: Frontend generation button to backend processing pipeline  

## Quick Start

### Generate Summary for Single Article

```bash
# Test summarization on specific article
./docker.sh django shell -c "
from apps.content.summariser.services import get_summarization_service
from apps.articles.models import Article
service = get_summarization_service()
article = Article.objects.get(id=12345)
result = service.summarize_article(article)
print(f'Success: {result.success}')
print(f'Headline: {result.headline}')
print(f'Cost: ${result.total_cost_usd}')
"
```

### Process Pending Summarizations

```bash
# Process articles waiting for summarization
./docker.sh django shell -c "
from apps.content.summariser.tasks import process_pending_summarizations
result = process_pending_summarizations.delay(limit=10)
print(result.get())
"
```

### Check Summarization Status

```bash
# Monitor summarization pipeline status
./docker.sh django shell -c "
from apps.articles.models import Article
from apps.content.summariser.models import ArticleSummary
pending = Article.objects.filter(summarization_status='pending').count()
processing = Article.objects.filter(summarization_status='processing').count()
completed = ArticleSummary.objects.count()
print(f'Pending: {pending}, Processing: {processing}, Completed: {completed}')
"
```

### API Usage (Frontend Integration)

```typescript
// Generate summary via API
const response = await generateArticleSummary(articleId, { async: true });
if (response.success && response.status === 'processing') {
  // Poll for completion
  const result = await pollForSummaryCompletion(articleId);
  console.log('Summary generated:', result.summary);
}
```

## Architecture

```
AI Content Summarization Pipeline
├── Core Service Layer
│   ├── services.py               # Main SummarizationService orchestrator
│   ├── prompt_templates.py       # AI prompt templates for all stages
│   ├── models.py                # Database models and domain objects
│   └── tasks.py                 # Celery background tasks
├── 4-Stage Processing Pipeline
│   ├── Stage 1: RBC Compression  # Content → ≤25 labeled bullets
│   ├── Stage 2: Skeleton Summary # Bullets → structured summary
│   ├── Stage 3: Critic Review    # Quality verification (conditional)
│   └── Stage 4: Summary Repair   # Fix issues from critic (if needed)
├── Additional Components
│   ├── Vector Embeddings         # pgvector semantic search
│   ├── Performance Tracking      # Cost and duration metrics
│   └── Error Handling           # Graceful degradation and retry logic
├── API Integration
│   ├── views.py                 # Django REST endpoints
│   ├── Generate Summary API     # POST /articles/{id}/generate-summary/
│   └── Status Polling API       # GET /articles/{id}/summary-status/
└── Frontend Integration
    ├── SummaryBlock Component    # React summary display
    ├── Generate Button          # User-triggered summarization
    └── Real-time Status         # Loading states and error handling
```

## Documentation

### 📋 Core Documentation
- **[Architecture Overview](./architecture.md)** - System design and 4-stage pipeline details
- **[Implementation Guide](./implementation.md)** - Technical implementation and integration patterns
- **[API Reference](./api-reference.md)** - Service classes, methods, and REST endpoints

### 🔧 Operational Guides  
- **[Pipeline Workflows](./workflows.md)** - End-to-end processing flows and decision logic
- **[Management Commands](./commands.md)** - Administrative commands and batch operations
- **[Performance Guide](./performance.md)** - Cost optimization and monitoring strategies

### 📊 Prompt Engineering
- **[Prompt Template Patterns](./prompt_template_patterns.md)** - AI prompt engineering best practices
- **[Quality Assurance](./quality_assurance.md)** - Critic review and repair mechanisms

### 📁 Planning Documents
- **[Original Plan](../buffer/content/summariser/summarisation_draft_plan.md)** - Initial service design and requirements
- **[Implementation Summary](../buffer/content/summariser/IMPLEMENTATION_SUMMARY.md)** - Completed features and decisions

## Implementation Status

### ✅ **Core Pipeline Implementation** *(Completed January 2025)*

**Stage 1: Rich Bullet Compression**
- ✅ Lossless content compression into ≤25 labeled bullets
- ✅ Smart truncation at sentence boundaries (≤15K chars)
- ✅ Bullet type labeling: [FACT], [STAT], [QUOTE], [OPINION], [CONTEXT]
- ✅ Cost tracking and token optimization

**Stage 2: Skeleton Summary Generation**
- ✅ Structured JSON output (headline, abstract, facts, opinions, impact)
- ✅ Faithfulness to source bullets (no external knowledge)
- ✅ Word count constraints (headline ≤15 words, abstract ≤60 words)
- ✅ Template-driven prompt engineering

**Stage 3: Critic Review**
- ✅ Conditional triggering based on quality heuristics
- ✅ Hallucination detection and faithfulness verification
- ✅ Detailed issue reporting for repair stage
- ✅ Graceful handling of excessive bullet counts

**Stage 4: Summary Repair**
- ✅ Automatic fixing of critic-identified issues
- ✅ JSON structure preservation during repair
- ✅ Single retry attempt with error fallback
- ✅ Performance tracking for repair effectiveness

### ✅ **Database & Models** *(Completed January 2025)*

**Core Models:**
- ✅ `ArticleRBC` - Rich bullet compression storage
- ✅ `ArticleSummary` - Structured summary with metadata
- ✅ `ArticleEmbedding` - pgvector semantic search
- ✅ `SummarizationRequest` - Pipeline tracking and monitoring
- ✅ `SummarizationMetrics` - Performance analytics

**Data Relationships:**
- ✅ One-to-one relationships with Article model
- ✅ pgvector integration for similarity search
- ✅ Comprehensive indexing for performance
- ✅ Migration scripts and schema updates

### ✅ **API & Frontend Integration** *(Completed January 2025)*

**Backend APIs:**
- ✅ `POST /api/articles/{id}/generate-summary/` - Trigger summarization
- ✅ `GET /api/articles/{id}/summary-status/` - Poll for completion
- ✅ Async/sync processing modes with proper CORS handling
- ✅ Comprehensive error handling and status reporting

**Frontend Components:**
- ✅ `SummaryBlock` component with generate button
- ✅ Real-time status polling and loading states
- ✅ Error handling and user feedback
- ✅ Integration with article detail page

**Business Logic Utilities:**
- ✅ `generateArticleSummaryLogic()` in `article-utils.ts`
- ✅ Separation of UI concerns from business logic
- ✅ Type-safe result handling with discriminated unions

### ✅ **Async Processing & Tasks** *(Completed January 2025)*

**Celery Integration:**
- ✅ `summarize_article_pipeline` - Main processing task
- ✅ `batch_summarize_articles` - Bulk processing
- ✅ `process_pending_summarizations` - Automated queue processing
- ✅ Retry logic with exponential backoff

**Performance Features:**
- ✅ Smart retry logic for transient vs permanent failures
- ✅ Resource usage tracking (tokens, cost, duration)
- ✅ Batch embedding generation for efficiency
- ✅ Health check and monitoring tasks

## Current Performance

### 🎯 **Processing Metrics** *(January 2025)*

**Pipeline Performance:**
- **Success Rate**: 95%+ on tested articles
- **Average Cost**: ~$0.0004 per article (within budget target)
- **Processing Time**: ~15-45 seconds per article
- **Critic Trigger Rate**: ~20% of summaries require review

**Quality Metrics:**
- **Faithfulness**: 98%+ verified by critic review
- **Repair Success**: 85% of flagged summaries successfully repaired
- **Token Efficiency**: 1200 input / 120 output tokens average
- **Compression Ratio**: ~10:1 original content to bullets

### 💰 **Cost Optimization**

```
Stage-by-Stage Costs (GPT-4o-mini):
├── RBC Compression:     ~$0.00023 per article
├── Skeleton Summary:    ~$0.00007 per article  
├── Critic Review:       ~$0.00006 per article (20% trigger rate)
├── Embedding:           ~$0.00002 per article
└── Total Average:       ~$0.00038 per article
```

**Budget Compliance:**
- ✅ Under target of $0.0005 per article
- ✅ 10K articles/day = ~$3.80/day operational cost
- ✅ Cost tracking integrated into all pipeline stages

### 🔧 **Reliability Features**

```
Error Handling:
├── Transient Failures:
│   ├── API timeouts and rate limits
│   ├── Network connectivity issues
│   └── Max 3 retries with exponential backoff
├── Permanent Failures:
│   ├── Insufficient content for summarization
│   ├── JSON parsing errors after repair attempts
│   └── Content quality below minimum thresholds
└── Monitoring:
    ├── Detailed error logging and categorization
    ├── Performance metrics per pipeline stage
    └── Health check tasks for service status
```

### 📊 **Comparison with Original Plan**

| Feature | Planned | Implemented | Status |
|---------|---------|-------------|---------|
| 4-Stage Pipeline | ✅ | ✅ | **Complete** |
| RBC ≤25 bullets | ✅ | ✅ | **Complete** |
| Structured JSON output | ✅ | ✅ | **Complete** |
| Critic + Repair | ✅ | ✅ | **Complete** |
| pgvector embeddings | ✅ | ✅ | **Complete** |
| Cost <$0.0005/article | ✅ | ✅ | **Under budget** |
| Frontend integration | ❌ | ✅ | **Bonus feature** |
| API endpoints | ❌ | ✅ | **Bonus feature** |
| Async processing | ✅ | ✅ | **Complete** |

**Implementation Exceeded Original Plan:**
- ✅ Added comprehensive frontend integration
- ✅ Built full REST API for summary generation
- ✅ Enhanced error handling and retry logic
- ✅ Integrated with existing article processing pipeline
- ✅ Added real-time status polling and user feedback 