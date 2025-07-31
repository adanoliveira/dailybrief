# DailyBrief Summariser Service - Implementation Plan

> **Scope**: Django-native summarization service that transforms processed article content into structured summaries using a 4-stage AI pipeline. Integrates seamlessly with existing content enrichment architecture while maintaining cost efficiency (<$0.0005/article).

---

## 1. Architecture Overview & Pipeline Position

### 1.1 Flexible Pipeline Integration

```
NewsAPI/Feeds → Fetcher (Step 1) → Processor (Step 2) → [Quality (Step 3)] → **Summariser** → Digest Builder
                 │                    │                   │                        │
                 ▼                    ▼                   ▼                        ▼
              raw_html           clean_content      quality_metrics         article_summary
              basic_content      content_blocks    quality_score           article_rbc  
              paywall_status     extracted_metadata                        article_embedding
```

**Flexible Entry Points:**
- **After Fetcher**: Uses `basic_content` for lightweight summarization
- **After Processor**: Uses `clean_content` for high-quality summarization  
- **After Quality**: Uses quality-assessed content for premium summarization

### 1.2 Integration with Existing Architecture

**Follows Established Patterns:**
- Uses `aiproviders` service layer for AI communication
- Integrates with `Article` model's processing status tracking  
- Leverages existing Celery task infrastructure
- Maintains domain boundaries and service separation
- Uses UUID public_id + status tracking conventions

**Service Dependencies:**
- **Input**: Articles with available content (`basic_content` or `clean_content`)
- **AI Layer**: `apps.aiproviders.services.AIProviderService`
- **Background**: Existing Celery setup and task patterns
- **Storage**: Extends `Article` model relationships

---

## 2. Four-Stage Processing Pipeline

### 2.1 Stage 1: Rich Bullet Compression (RBC)
- **Purpose**: Lossless compression of article content into labeled bullets
- **Model**: `gpt-4o-mini`, Temperature: 0.3, Max tokens: 256
- **Output**: ≤25 labeled bullets `[FACT|STAT|QUOTE|OPINION|CONTEXT]`

### 2.2 Stage 2: Skeleton Summary Generation  
- **Purpose**: Create structured summary using only RBC bullets
- **Model**: `gpt-4o-mini`, Temperature: 0.25, Max tokens: 180
- **Output**: JSON with headline, abstract, facts, opinions, impact

### 2.3 Stage 3: Critic Review (Conditional)
- **Purpose**: Detect hallucinations and verify faithfulness
- **Triggers**: Abstract >60 words, Facts <3 items, "UNCERTAIN" flags
- **Model**: `gpt-4o-mini`, Temperature: 0.0, Max tokens: 120

### 2.4 Stage 4: Summary Repair (If Needed)
- **Purpose**: Fix identified issues while preserving structure
- **Trigger**: `faithful: false` from Stage 3
- **Model**: `gpt-4o-mini`, Temperature: 0.2, Max tokens: 180

---

## 3. Cost & Performance Targets

| Stage | Avg Tokens In/Out | Cost per Article | Latency (p95) |
|-------|------------------|------------------|---------------|
| RBC Compression | 1,200 / 150 | $0.00023 | 1.5s |
| Skeleton Summary | 350 / 120 | $0.00007 | 0.8s |
| Critic Review (20%) | 300 / 80 | $0.00006 | 0.7s |
| Embedding | 100 / 0 | $0.00002 | 0.2s |
| **Total Average** | - | **$0.00038** | ~2.5s |

**Daily Budget**: 10k articles = ~$3.80/day

---

*This plan maintains the technical excellence of the draft while ensuring flexible integration with DailyBrief's content processing pipeline.* 