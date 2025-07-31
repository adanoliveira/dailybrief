# AI Processor Implementation Plan

## Overview

This document outlines the implementation of an AI-powered content processor to complement our existing algorithmic processor. The AI processor will extract structured content blocks from preprocessed HTML using LLM capabilities.

## Domain-Driven Architecture & Service Boundaries

### AI Providers Abstraction Layer
Our architecture follows domain-driven design principles with clear service boundaries:

```
┌─────────────────────────────────────────────────────────────┐
│                    Domain Services                          │
├─────────────────────────────────────────────────────────────┤
│  content/quality/     │  content/processor/                 │
│  ├── Quality         │  ├── Algorithmic Processor          │
│  │   Evaluation      │  ├── AI Processor (new)             │
│  ├── Assessment      │  ├── Content Routing                │
│  └── Scoring         │  └── Quality Assessment             │
├─────────────────────────────────────────────────────────────┤
│                  AI Providers Service                       │
│  ├── LLM Abstractions    ├── Prompt Management             │
│  ├── Model Selection     ├── Response Parsing              │
│  ├── Token Management    ├── Error Handling                │
│  └── Cost Tracking       └── Caching                       │
└─────────────────────────────────────────────────────────────┘
```

### Service Responsibilities

#### AIProviders Service (`backend/apps/aiproviders/`)
- **Purpose**: Internal AI/LLM abstraction layer for all domain services
- **Responsibilities**:
  - Abstract LLM provider differences (OpenAI, Anthropic, etc.)
  - Manage prompt templates and model selection
  - Handle token counting, rate limiting, and cost tracking
  - Provide consistent response parsing and error handling
  - Implement caching strategies across AI operations
  - Centralize AI configuration and monitoring

#### Quality Service (`backend/apps/content/quality/`)
- **Purpose**: Content quality assessment and evaluation
- **AI Usage**: Uses `aiproviders` for LLM-based quality evaluation
- **Domain Focus**: Quality metrics, scoring algorithms, assessment criteria
- **No Direct AI Logic**: Delegates all LLM operations to `aiproviders`

#### Processor Service (`backend/apps/content/processor/`)
- **Purpose**: Content extraction and processing
- **AI Usage**: Will use `aiproviders` for LLM-based content extraction
- **Domain Focus**: Content structure, semantic extraction, processing pipelines
- **No Direct AI Logic**: Delegates all LLM operations to `aiproviders`

### Architectural Benefits

1. **Single Responsibility**: Each service focuses on its domain expertise
2. **DRY Principle**: AI logic centralized in `aiproviders`, no duplication
3. **Consistent AI Operations**: Same patterns for prompt handling, response parsing
4. **Cost Management**: Centralized token tracking and optimization
5. **Testing & Mocking**: Single point for AI operation mocking in tests
6. **Provider Flexibility**: Easy to switch between LLM providers
7. **Monitoring**: Centralized AI operation logging and metrics

### Implementation Implication for AI Processor

The AI processor must follow the same architectural patterns as the quality service:

```python
# ❌ BAD: Direct LLM interaction in processor
class AIProcessor:
    def extract_content(self, html):
        # Direct OpenAI/Anthropic calls - violates architecture
        response = openai.chat.completions.create(...)
        
# ✅ GOOD: Use aiproviders abstraction
class AIProcessor:
    def __init__(self):
        from apps.aiproviders.services import AIService
        self.ai_service = AIService()
    
    def extract_content(self, html):
        # Delegate to aiproviders service
        response = self.ai_service.process_with_template(
            template_name="content_extraction_v1",
            content=html,
            **kwargs
        )
```

## Architecture Pattern Reuse

### From Quality Evaluation System
We can reuse these proven patterns from our quality evaluation system:

1. **HTML Preprocessing**: Reuse HTMLPreprocessor for consistent input preparation
2. **Prompt Template System**: Adapt BasePromptTemplate architecture for extraction prompts
3. **Structured JSON Response**: Similar response parsing and validation
4. **Content Block Modeling**: Reuse ContentBlock dataclasses
5. **Management Commands**: Similar testing and comparison commands
6. **Error Handling**: Proven error handling patterns
7. **AIProviders Integration**: Same patterns for delegating AI operations

## Component Architecture

```
AIProcessor Service (content/processor/)
├── AIProcessor (main service)
│   ├── Uses: aiproviders.AIService
│   └── Coordinates: extraction pipeline
├── HTMLPreprocessor (reused from quality)
├── ContentBlockBuilder (new)
│   ├── Converts: AI JSON → ContentBlock objects
│   └── Validates: content structure
├── ExtractionValidator (new)
└── Management Commands (new)

AIProviders Service (aiproviders/)
├── AIService (core abstraction)
├── PromptTemplateManager
│   ├── ExtractionPromptTemplate (new)
│   ├── Template versioning & selection
│   └── Few-shot example management
├── ResponseParser (reused/adapted)
├── ModelManager (provider selection)
└── CostTracker (token & expense monitoring)
```

### Integration with AIProviders Service

The AI processor will register its prompt templates with the `aiproviders` service:

```python
# In aiproviders/services.py - Template Registration
EXTRACTION_TEMPLATES = {
    "content_extraction_v1": ExtractionPromptTemplateV1,
    "content_extraction_v2": ExtractionPromptTemplateV2,
    "specialized_news_extraction": NewsExtractionTemplate,
}

# In processor/ai_processor.py - Usage
class AIProcessor:
    def __init__(self):
        self.ai_service = AIService()
        self.html_preprocessor = HTMLPreprocessor()
        self.block_builder = ContentBlockBuilder()
    
    def extract_content(self, raw_html: str, metadata: dict) -> ProcessingResult:
        # 1. Preprocess HTML using proven patterns
        preprocessed_html = self.html_preprocessor.preprocess_for_ai(raw_html)
        
        # 2. Delegate to aiproviders for AI processing
        ai_response = self.ai_service.process_with_template(
            template_name="content_extraction_v2",
            content=preprocessed_html,
            metadata=metadata,
            response_format="json"
        )
        
        # 3. Convert AI response to domain objects
        content_blocks = self.block_builder.build_blocks(ai_response)
        
        return ProcessingResult(
            success=True,
            clean_content=self._blocks_to_text(content_blocks),
            content_blocks=content_blocks,
            extracted_metadata=ai_response.get('extraction_metadata', {}),
            processing_time_ms=ai_response.get('processing_time_ms', 0)
        )
```

## Key Implementation Components

### 1. ExtractionPromptTemplate
- Similar to quality evaluation templates
- Focus on content extraction instructions
- Include HTML structure preservation guidelines
- Provide clear JSON schema for response

### 2. ContentExtractor
- Core extraction logic
- HTML preprocessing pipeline
- LLM interaction management
- Response validation and parsing

### 3. ContentBlockBuilder
- Convert AI response to ContentBlock objects
- Metadata extraction and cleaning
- Content validation and normalization

### 4. ExtractionValidator
- Validate extracted content completeness
- Check for missing essential elements
- Ensure content block consistency

## Input/Output Specification

### Input
- Raw HTML content
- Article metadata (title, URL, etc.)
- Extraction configuration options

### Output
- List of structured ContentBlock objects
- Extraction metadata (processing time, token usage, etc.)
- Quality indicators (completeness, structure preservation)

### JSON Response Schema
```json
{
  "content_blocks": [
    {
      "type": "heading|paragraph|image|quote|list|twitter_embed",
      "content": "string",
      "level": "number|null",
      "position": "number",
      "metadata": {
        "src": "string (for images)",
        "href": "string (for links)",
        "caption": "string",
        "list_type": "ul|ol",
        "items": ["array of strings"],
        "tweet_id": "string",
        "embed_url": "string"
      }
    }
  ],
  "extraction_metadata": {
    "total_blocks": "number",
    "processing_time_ms": "number",
    "token_usage": "number",
    "completeness_indicators": {
      "has_headings": "boolean",
      "has_paragraphs": "boolean", 
      "has_images": "boolean",
      "estimated_word_count": "number"
    }
  }
}
```

## Comparison with Algorithmic Processor

| Aspect | Algorithmic Processor | AI Processor |
|--------|----------------------|--------------|
| Approach | Rule-based Safari algorithm | LLM-powered extraction |
| Input | Raw HTML | Preprocessed HTML |
| Strengths | Fast, deterministic | Context-aware, adaptive |
| Weaknesses | Rigid rules, poor quality | Slower, token costs |
| Use Cases | Simple articles | Complex layouts, modern sites |

## Integration Points

### 1. Content Processing Pipeline
```python
def process_content(raw_html, metadata):
    # Try AI processor first
    ai_result = ai_processor.process_content(raw_html, metadata)
    
    # Evaluate quality
    ai_quality = quality_evaluator.assess(ai_result)
    
    # Fallback to algorithmic if needed
    if ai_quality.quality_score < THRESHOLD:
        algo_result = algorithmic_processor.process_content(raw_html, metadata)
        algo_quality = quality_evaluator.assess(algo_result)
        
        # Choose best result
        return best_result(ai_result, algo_result, ai_quality, algo_quality)
    
    return ai_result
```

### 2. Quality-Based Routing
- Use existing quality evaluation system
- Route based on content complexity
- A/B test different processors
- Adaptive routing based on success rates

## File Structure

```
# AI Processor Domain Logic (content/processor/)
backend/apps/content/processor/
├── ai_processor.py                 # Main AI processor service
├── content_block_builder.py        # Convert AI JSON → ContentBlock objects
├── extraction_validator.py         # Validate extraction completeness
├── management/
│   └── commands/
│       ├── extract_with_ai.py     # Test AI extraction
│       ├── compare_processors.py  # Compare AI vs Algorithmic
│       └── benchmark_extraction.py # Performance benchmarking
└── tests/
    ├── test_ai_processor.py
    └── test_content_block_builder.py

# AI Abstraction Layer (aiproviders/)
backend/apps/aiproviders/
├── services.py                     # Core AIService (existing)
├── prompt_templates/               # Centralized prompt management
│   ├── __init__.py
│   ├── base_template.py           # Base template (existing)
│   ├── quality_templates.py       # Quality evaluation templates (existing)
│   └── extraction_templates.py    # Content extraction templates (new)
├── models.py                       # AI operation tracking (existing)
└── management/
    └── commands/
        └── test_extraction_templates.py # Template testing

# Reused Components (content/quality/)
backend/apps/content/quality/
├── html_preprocessor.py            # Reused for AI extraction
└── models.py                       # ContentBlock, ProcessingResult models
```

### Template Organization Strategy

Following the domain-driven pattern established by the quality service:

```python
# aiproviders/prompt_templates/extraction_templates.py
class ExtractionPromptTemplateV1(BasePromptTemplate):
    """Basic content extraction template."""
    template_name = "content_extraction_v1"
    version = "1.0"
    
class ExtractionPromptTemplateV2(BasePromptTemplate):
    """Enhanced extraction with social media support."""
    template_name = "content_extraction_v2" 
    version = "2.0"

class NewsExtractionTemplate(BasePromptTemplate):
    """Specialized template for news articles."""
    template_name = "specialized_news_extraction"
    version = "1.0"

# Registration in aiproviders/services.py
from .prompt_templates.extraction_templates import (
    ExtractionPromptTemplateV1,
    ExtractionPromptTemplateV2, 
    NewsExtractionTemplate
)

AVAILABLE_TEMPLATES.update({
    "content_extraction_v1": ExtractionPromptTemplateV1,
    "content_extraction_v2": ExtractionPromptTemplateV2,
    "specialized_news_extraction": NewsExtractionTemplate,
})
```

## Implementation Phases

### Phase 1: Core Infrastructure
1. Create AIProcessor service class
2. Implement basic extraction prompt template
3. Build ContentBlockBuilder
4. Create management command for testing

### Phase 2: Template Optimization
1. Develop comprehensive extraction prompts
2. Add specialized templates for different content types
3. Implement few-shot examples
4. Test on diverse content samples

### Phase 3: Integration & Comparison
1. Integrate with existing pipeline
2. Build processor comparison system
3. Implement quality-based routing
4. Performance optimization

### Phase 4: Production Deployment
1. A/B testing framework
2. Monitoring and alerting
3. Cost optimization
4. Adaptive routing logic

## Success Metrics

### Quality Metrics
- Content completeness (>85%)
- Structure preservation (>90%)
- Metadata accuracy (>95%)
- Processing success rate (>98%)

### Performance Metrics
- Processing time (<30 seconds)
- Token efficiency (<100k tokens per article)
- Cost per extraction (<$0.02)
- Quality score improvement vs algorithmic

## Risk Mitigation

### Content Quality Risks
- Implement multiple validation layers
- Use quality evaluation for routing decisions
- Maintain algorithmic processor as fallback
- Regular prompt template updates

### Cost & Performance Risks
- Token usage monitoring and alerts
- Implement intelligent caching
- Use cheaper models for simple content
- Batch processing for efficiency

## Next Steps

1. **Immediate**: Implement core AIProcessor service
2. **Week 1**: Build extraction prompt templates
3. **Week 2**: Create comparison and testing infrastructure
4. **Week 3**: Integration with existing pipeline
5. **Week 4**: Production testing and optimization

## Reference Implementations

- Quality evaluation system: `backend/apps/content/quality/`
- Algorithmic processor: `backend/apps/content/processor/algorithmic_processor.py`
- Content models: `backend/apps/content/models.py`
- Management commands: `backend/apps/content/management/commands/` 