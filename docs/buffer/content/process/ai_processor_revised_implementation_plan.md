# AI Processor Revised Implementation Plan

## Executive Summary

This revised plan implements an AI-powered content processor that complements our existing algorithmic processor, following the proven architectural patterns from our successful quality evaluation system. The AI processor will provide semantic content extraction with higher accuracy for complex layouts while maintaining cost efficiency through intelligent routing.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                   Content Processing Domain                 │
├─────────────────────────────────────────────────────────────┤
│  content/processor/  │  content/quality/                   │
│  ├── Algorithmic    │  ├── Quality Evaluation             │
│  ├── AI Processor   │  ├── Assessment & Scoring           │
│  ├── Routing Logic  │  └── HTML Preprocessing             │
│  └── Services       │                                       │
├─────────────────────────────────────────────────────────────┤
│              AI Infrastructure (aiproviders/)               │
│  ├── Provider Clients    ├── Response Standardization      │  
│  ├── Usage Tracking      ├── Model Configuration           │
│  └── Cost Monitoring     └── Error Handling                │
└─────────────────────────────────────────────────────────────┘
```

### Service Boundaries (Following DDD)

**AI Processor (content/processor/ai_processor.py)**
- **Purpose**: Semantic content extraction using LLM capabilities
- **Dependencies**: `aiproviders.AIProviderService`, `quality.HTMLPreprocessor`
- **Responsibilities**: Content extraction orchestration, response parsing, validation
- **Output**: Structured `ContentBlock` objects compatible with existing data models

**Quality Service Integration**
- **Reuse**: `HTMLPreprocessor`, `ContentBlock` models, validation patterns
- **Purpose**: Evaluate AI extraction results vs algorithmic results
- **Route Selection**: Quality scores determine optimal processor selection

## Proven Patterns to Reuse

### 1. Service Architecture Pattern
```python
# From quality/evaluator.py - PROVEN SUCCESSFUL
class ContentQualityEvaluator:
    def __init__(self, template_id: Optional[str] = None):
        self.ai_service = get_ai_service()  # Dependency injection
        self.template = get_template(template_id)  # Template management
        self.html_preprocessor = HTMLPreprocessor()  # HTML optimization

# Apply to AI Processor
class AIContentProcessor:
    def __init__(self, template_id: Optional[str] = None):
        self.ai_service = get_ai_service()  # Same AI service dependency  
        self.template = get_extraction_template(template_id)  # New extraction templates
        self.html_preprocessor = HTMLPreprocessor()  # Same preprocessing
        self.block_builder = ContentBlockBuilder()  # New: JSON → ContentBlock
```

### 2. HTML Preprocessing Pattern
```python
# From quality/evaluator.py - PROVEN 100% SUCCESS RATE
def _prepare_html_sample(self, article, use_preprocessing=True, max_tokens=50000):
    if use_preprocessing:
        preprocessed = self.html_preprocessor.preprocess_for_ai(
            article.raw_html,
            max_tokens=max_tokens,
            preserve_structure=True  # Critical for content extraction
        )
        return {
            "html_sample": preprocessed.optimized_html,
            "html_length": len(preprocessed.optimized_html),
            "preprocessing_summary": preprocessed.summary
        }
```

### 3. Template Management Pattern
```python
# From quality/prompt_templates.py - PROVEN TEMPLATE VERSIONING
class ExtractionPromptTemplate(BasePromptTemplate):
    """Content extraction template following proven quality evaluation patterns."""
    
    def __init__(self):
        super().__init__()
        self.identifier = "content_extraction_v2"
        self.version = "2.0"
        self.operation = "content_extraction"
    
    def format(self, preprocessed_html: str, article_metadata: dict) -> str:
        """Generate extraction prompt following quality evaluation success patterns."""
        pass
```

### 4. Response Parsing Pattern
```python
# From quality/evaluator.py - 100% JSON PARSING SUCCESS
def _create_extraction_result(self, llm_response: LLMResponse, processing_time: float):
    try:
        response_data = json.loads(llm_response.content.strip())
        
        # Validate structure (same pattern as quality evaluation)
        if not self._validate_extraction_response(response_data):
            return self._create_fallback_result("Invalid response structure")
        
        # Convert to domain objects
        content_blocks = self.block_builder.build_blocks(response_data["content_blocks"])
        
        return ProcessingResult(
            success=True,
            clean_content=self._blocks_to_text(content_blocks),
            content_blocks=content_blocks,
            extracted_metadata=response_data.get("extraction_metadata", {}),
            processing_time_ms=int(processing_time * 1000)
        )
    except json.JSONDecodeError:
        return self._create_fallback_result("JSON parsing failed")
```

## Implementation Components

### 1. Core AI Processor Service
**File**: `backend/apps/content/processor/ai_processor.py`

```python
class AIContentProcessor:
    """
    AI-powered content processor following proven quality evaluation patterns.
    
    Uses aiproviders service for AI infrastructure and quality service patterns
    for HTML preprocessing and response handling.
    """
    
    def process_content(self, raw_html: str, article_metadata: dict) -> ProcessingResult:
        """Main extraction pipeline following quality evaluation success patterns."""
        
        # 1. Preprocess HTML (reuse proven pattern)
        preprocessed = self.html_preprocessor.preprocess_for_ai(raw_html, max_tokens=75000)
        
        # 2. Generate extraction prompt 
        prompt = self.template.format(
            preprocessed_html=preprocessed.optimized_html,
            article_metadata=article_metadata
        )
        
        # 3. Call AI service (same pattern as quality evaluation)
        llm_response = self.ai_service.call_llm(
            prompt=prompt,
            operation="content_extraction",
            max_tokens=4000,  # Sufficient for structured content
            temperature=0.1,  # Low temperature for consistent extraction
            response_format="json"
        )
        
        # 4. Parse and validate response (proven pattern)
        return self._create_extraction_result(llm_response, processing_time)
```

### 2. Extraction Prompt Templates  
**File**: `backend/apps/content/processor/extraction_templates.py`

Following the proven template architecture from quality evaluation:

```python
class ContentExtractionTemplateV2(BasePromptTemplate):
    """
    Enhanced content extraction template based on successful quality evaluation patterns.
    
    Uses proven prompt engineering techniques that achieved 100% JSON parsing success
    and 95%+ content accuracy in quality evaluation system.
    """
    
    identifier = "content_extraction_v2"
    version = "2.0"
    
    def format(self, preprocessed_html: str, article_metadata: dict) -> str:
        system_prompt = """You are an expert content extraction specialist with deep knowledge of web publishing and HTML structure. Your task is to extract clean, structured content from preprocessed HTML while preserving semantic meaning and proper formatting.

TASK: Extract main article content and structure it into semantic content blocks.

OUTPUT FORMAT: Return ONLY a JSON object with this exact structure:
{
  "content_blocks": [
    {
      "type": "heading|paragraph|image|quote|list|twitter_embed",
      "content": "text content",
      "level": "number for headings (1-6), null for others",
      "position": "sequential number starting from 0",
      "metadata": {
        "src": "image URL if applicable",
        "alt": "image alt text if applicable",
        "caption": "image caption if applicable",
        "href": "link URL if applicable",
        "list_type": "ul|ol for lists",
        "items": ["array", "of", "list", "items"],
        "tweet_id": "tweet ID for embeds",
        "embed_url": "embed URL if applicable"
      }
    }
  ],
  "extraction_metadata": {
    "total_blocks": "number",
    "estimated_word_count": "number",
    "has_headings": "boolean",
    "has_paragraphs": "boolean",
    "has_images": "boolean",
    "has_lists": "boolean",
    "has_embeds": "boolean"
  }
}

CONSTRAINTS:
- Extract only main article content (ignore navigation, ads, sidebars)
- Preserve content hierarchy and semantic relationships
- Include position numbers in sequential order
- Maintain original meaning and context
- Extract all metadata for rich content elements

Do not include any explanation outside the JSON response."""

        user_prompt = f"""Extract content from this preprocessed HTML:

ARTICLE METADATA:
Title: {article_metadata.get('title', 'Unknown')}
URL: {article_metadata.get('url', 'Unknown')}

HTML CONTENT:
{preprocessed_html}

Return the structured content blocks as JSON following the specified format."""

        return f"{system_prompt}\n\n{user_prompt}"
```

### 3. Content Block Builder
**File**: `backend/apps/content/processor/content_block_builder.py`

```python
class ContentBlockBuilder:
    """
    Converts AI extraction JSON responses to ContentBlock objects.
    
    Follows the same validation and conversion patterns as quality evaluation
    for consistent and reliable object creation.
    """
    
    def build_blocks(self, blocks_data: List[dict]) -> List[ContentBlock]:
        """Convert AI JSON response to ContentBlock objects."""
        content_blocks = []
        
        for i, block_data in enumerate(blocks_data):
            try:
                # Validate block structure
                if not self._validate_block_structure(block_data):
                    logger.warning(f"Invalid block structure at position {i}: {block_data}")
                    continue
                
                # Create ContentBlock following existing patterns
                block = ContentBlock(
                    type=block_data["type"],
                    content=block_data.get("content", ""),
                    level=block_data.get("level"),
                    position=block_data.get("position", i),
                    metadata=block_data.get("metadata", {})
                )
                
                # Type-specific validation and cleanup
                if self._validate_content_block(block):
                    content_blocks.append(block)
                
            except Exception as e:
                logger.error(f"Error building content block {i}: {e}")
                continue
        
        return content_blocks
```

### 4. Processor Integration
**File**: Update `backend/apps/content/processor/services.py`

```python
class ContentProcessingService:
    """Enhanced processing service with AI processor integration."""
    
    def __init__(self):
        self.algorithmic_processor = AlgorithmicProcessor()
        self.ai_processor = AIContentProcessor()
        self.router = ProcessingRouter()
        self.quality_evaluator = ContentQualityEvaluator()
    
    def process_article_content(self, article) -> ProcessingResult:
        """
        Intelligent content processing with quality-based routing.
        
        Uses routing logic to determine optimal processor, then evaluates
        results for quality and potential re-processing.
        """
        # Determine optimal processing route
        route = self.router.determine_route(article)
        
        if route == "llm_enhanced":
            # Use AI processor
            result = self.ai_processor.process_content(article.raw_html, {
                "title": article.title,
                "url": article.url,
                "source": article.feed.title if article.feed else "Unknown"
            })
        else:
            # Use algorithmic processor
            result = self.algorithmic_processor.process_content(article.raw_html, {
                "title": article.title,
                "url": article.url
            })
        
        # Evaluate result quality
        quality_result = self.quality_evaluator.evaluate_extraction_quality(result)
        
        # Consider re-processing if quality is poor and we haven't tried AI yet
        if (quality_result.overall_score < 0.7 and route != "llm_enhanced" and 
            not getattr(article, '_ai_processing_attempted', False)):
            
            logger.info(f"Re-processing article {article.public_id} with AI processor due to low quality")
            article._ai_processing_attempted = True
            result = self.ai_processor.process_content(article.raw_html, {
                "title": article.title,
                "url": article.url,
                "source": article.feed.title if article.feed else "Unknown"
            })
        
        return result
```

## Testing and Validation Infrastructure

### 1. Management Commands
**File**: `backend/apps/content/processor/management/commands/extract_with_ai.py`

```python
class Command(BaseCommand):
    """Test AI extraction on individual articles following quality evaluation patterns."""
    
    def handle(self, *args, **options):
        # Test AI extraction with detailed output
        # Compare with algorithmic results
        # Validate content block structure
        # Report token usage and costs
```

**File**: `backend/apps/content/processor/management/commands/compare_processors.py`

```python
class Command(BaseCommand):
    """Compare AI vs Algorithmic processor performance following quality evaluation patterns."""
    
    def handle(self, *args, **options):
        # Process sample articles with both processors
        # Evaluate quality scores for each
        # Compare processing times and costs
        # Generate performance report
```

### 2. Template Registration
**Update**: `backend/apps/aiproviders/services.py`

```python
# Add extraction template registration
AVAILABLE_TEMPLATES = {
    # Existing quality templates
    "quality_assessment_v1": QualityAssessmentTemplateV1,
    "quality_assessment_v2": QualityAssessmentTemplateV2,
    
    # New extraction templates  
    "content_extraction_v1": ContentExtractionTemplateV1,
    "content_extraction_v2": ContentExtractionTemplateV2,
    "specialized_news_extraction": SpecializedNewsExtractionTemplate,
}
```

## Success Metrics & Validation

### Quality Benchmarks (Based on Quality Evaluation Success)
- **JSON Parsing Success**: Target 100% (matching quality evaluation)
- **Content Block Accuracy**: Target 90%+ for all block types
- **Content Completeness**: Target 85%+ vs original HTML
- **Processing Success Rate**: Target 98%+

### Performance Targets
- **Processing Time**: <45 seconds per article (vs 23s for quality evaluation)
- **Token Efficiency**: <75K tokens per article for extraction
- **Cost Efficiency**: <$0.02 per extraction
- **Quality Improvement**: 15%+ vs algorithmic processor

### Validation Methods
1. **A/B Testing**: Route traffic between processors and compare results
2. **Quality Evaluation**: Use existing quality system to assess extraction results
3. **Manual Review**: Spot-check complex articles for accuracy
4. **Cost Monitoring**: Track token usage and processing costs

## Implementation Timeline

### Phase 1: Foundation (Week 1)
- [ ] Create `AIContentProcessor` service class
- [ ] Implement `ContentExtractionTemplateV2` 
- [ ] Build `ContentBlockBuilder` with validation
- [ ] Create basic management commands for testing

### Phase 2: Integration (Week 2)  
- [ ] Integrate with existing processing pipeline
- [ ] Enhance routing logic for AI processor selection
- [ ] Build processor comparison infrastructure
- [ ] Implement quality-based re-processing logic

### Phase 3: Optimization (Week 3)
- [ ] Optimize prompt templates based on test results
- [ ] Implement specialized templates for different content types
- [ ] Add comprehensive error handling and fallbacks
- [ ] Performance tuning and cost optimization

### Phase 4: Production (Week 4)
- [ ] A/B testing framework for gradual rollout
- [ ] Monitoring and alerting for AI processor
- [ ] Documentation and team training
- [ ] Production deployment and monitoring

## Risk Mitigation

### Technical Risks
- **Content Quality**: Use quality evaluation for validation and routing decisions
- **API Failures**: Maintain algorithmic processor as reliable fallback
- **JSON Parsing**: Apply proven parsing patterns from quality evaluation system
- **Token Limits**: Implement intelligent HTML preprocessing and content chunking

### Business Risks  
- **Cost Control**: Monitor token usage with alerts and budget limits
- **Processing Speed**: Parallel processing and smart routing for performance
- **Accuracy**: Continuous template optimization based on quality metrics
- **Reliability**: Multiple validation layers and graceful degradation

This revised plan leverages all the proven patterns from our successful quality evaluation system while adding the new extraction capabilities. The architecture maintains clear service boundaries and follows the same dependency injection patterns that achieved 100% parsing success in quality evaluation. 