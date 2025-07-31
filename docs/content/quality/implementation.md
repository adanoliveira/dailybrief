# Implementation Guide

> **Technical implementation details for the Content Quality Assessment System**

## File Structure

```
backend/apps/content/quality/
├── __init__.py
├── models.py                           # Data models and domain logic
├── evaluator.py                        # Core evaluation orchestration
├── prompt_templates.py                 # Template system and management
├── html_preprocessor.py                # HTML optimization utilities
├── management/commands/                # Management commands
│   ├── evaluate_quality.py            # Single/batch evaluation
│   ├── evaluate_batch_by_ids.py       # ID-based batch evaluation
│   ├── compare_templates.py           # Template A/B testing
│   ├── calibrate_quality_evaluator.py # Accuracy calibration
│   ├── create_reference_examples.py   # Reference data curation
│   ├── test_full_content_quality.py   # Full content testing
│   └── show_prompt_example.py         # Prompt inspection
└── migrations/                        # Database migrations
    ├── 0001_initial.py
    ├── 0002_reference_examples.py
    └── ...
```

## Core Implementation Details

### 1. ContentQualityEvaluator Class

**Location**: `backend/apps/content/quality/evaluator.py`

```python
class ContentQualityEvaluator:
    """
    Central orchestration of quality evaluation process.
    Separates content domain logic from AI infrastructure.
    """
    
    def __init__(self, template_id: Optional[str] = None):
        self.ai_service = get_ai_service()
        self.template = get_template(template_id)
        self.template_id = template_id or "active"
        self.html_preprocessor = HTMLPreprocessor()
```

#### Key Methods

**Main Evaluation Pipeline**:
```python
def evaluate_article_quality(
    self,
    article: Article,
    include_html: bool = True,
    model_override: Optional[str] = None,
    use_html_preprocessing: bool = True
) -> QualityAssessmentResult:
    """
    Main entry point for quality evaluation.
    Returns comprehensive quality assessment.
    """
```

**Content Preparation**:
```python
def _prepare_extracted_content(self, article: Article) -> Dict[str, Any]:
    """
    Prepares structured content blocks for evaluation.
    Focuses on content blocks rather than raw text.
    """
    # Process ALL content blocks for complete assessment
    blocks_info = json.dumps(article.content_blocks, indent=2)
    
    # Prepare metadata with content domain knowledge
    metadata_info = {
        "word_count": article.word_count,
        "read_time": article.read_time_minutes,
        "fetch_status": article.fetch_status,
        "process_status": article.process_status,
        "has_images": article.has_images,
        "media_count": article.media_count,
        "paywall_detected": article.paywall_detected
    }
```

**HTML Preprocessing**:
```python
def _prepare_html_sample(
    self, 
    article: Article, 
    include_html: bool = True,
    use_preprocessing: bool = True,
    max_tokens: int = 50000  # Modern LLM context windows
) -> Dict[str, Any]:
    """
    Optimizes HTML for evaluation with structure preservation.
    Handles large articles with intelligent preprocessing.
    """
    if use_preprocessing:
        preprocessed = self.html_preprocessor.preprocess_for_evaluation(
            raw_html, 
            max_tokens=max_tokens,
            preserve_html_structure=True  # Key: preserves document structure
        )
        return {
            "html_sample": preprocessed.cleaned_html,
            "html_length": preprocessed.cleaned_size,
            "preprocessing_summary": self.html_preprocessor.get_preprocessing_summary(preprocessed)
        }
```

**Few-Shot Example Generation**:
```python
def _prepare_reference_examples(self, max_per_class: int = 1) -> str:
    """
    Template-based few-shot example preparation.
    Uses random selection for variety and template formatting.
    """
    few_shot_template = get_few_shot_template()
    
    # Get diverse examples across quality classes
    for quality_class in ['perfect', 'good', 'imperfect', 'awful']:
        examples = ReferenceQualityExample.objects.filter(
            quality_class=quality_class,
            use_in_prompts=True
        ).order_by('?')[:max_per_class]  # Random selection
        
        # Format each example using template
        for example in examples:
            template_data = self._prepare_few_shot_template_data(example, example_id, quality_class)
            formatted_example = few_shot_template.format(**template_data)
```

### 2. Template System Implementation

**Location**: `backend/apps/content/quality/prompt_templates.py`

#### Base Template Architecture

```python
class BasePromptTemplate(ABC):
    """Abstract base ensuring consistent template interface"""
    
    @property
    @abstractmethod
    def metadata(self) -> PromptTemplateMetadata:
        """Template metadata for tracking and versioning"""
        pass
    
    @property
    @abstractmethod
    def template_text(self) -> str:
        """The actual prompt template with variable placeholders"""
        pass
    
    def format(self, **kwargs) -> str:
        """Format template with provided variables"""
        return self.template_text.format(**kwargs)
    
    @property
    def identifier(self) -> str:
        """Unique identifier: name_version"""
        return f"{self.metadata.name}_{self.metadata.version}"
```

#### Template Registration System

```python
# Template registry with version control
AVAILABLE_TEMPLATES: Dict[str, BasePromptTemplate] = {
    "comprehensive_quality_evaluation_v3.1": ComprehensiveQualityEvaluator(),
    "structured_rubric_evaluation_v2025-05-v3": StructuredRubricEvaluator(),
    "few_shot_example_v1.0": FewShotExampleTemplate(),
}

# Configuration management
DEFAULT_TEMPLATE = "comprehensive_quality_evaluation_v3.1"
ACTIVE_TEMPLATE = "comprehensive_quality_evaluation_v3.1"
FEW_SHOT_TEMPLATE = "few_shot_example_v1.0"

def get_template(template_id: str = None) -> BasePromptTemplate:
    """Get template with fallback to active template"""
    if template_id is None:
        template_id = ACTIVE_TEMPLATE
    
    if template_id not in AVAILABLE_TEMPLATES:
        raise KeyError(f"Template '{template_id}' not found")
    
    return AVAILABLE_TEMPLATES[template_id]
```

#### Unified JSON Response Format

**Key Implementation Decision**: All templates use the same JSON structure without overall scores:

```python
UNIFIED_JSON_SCHEMA = """{
  "template_version": "template_identifier_here",
  "evaluation_timestamp": "auto_generated",
  "scores": {
    "completeness": 0.0,
    "purity": 0.0,
    "structure": 0.0,
    "readability": 0.0
  },
  "confidence": 0.0,
  "assessment": {
    "explanation": "Detailed explanation...",
    "missing_elements": ["list", "of", "missing", "elements"],
    "noise_detected": ["list", "of", "noise", "elements"],
    "key_strengths": ["list", "of", "strengths"],
    "improvement_areas": ["list", "of", "improvements"]
  },
  "metadata": {
    "assessment_method": "llm_evaluation",
    "evidence_clarity": "high|medium|low",
    "pattern_consistency": "consistent|mixed|contradictory"
  }
}"""
```

### 3. Domain Scoring Implementation

**Location**: `backend/apps/content/quality/models.py`

#### QualityScoring Class Methods

```python
class QualityScoring(models.Model):
    # Domain-specific constants
    COMPLETENESS_WEIGHT = 0.40
    PURITY_WEIGHT = 0.35
    STRUCTURE_WEIGHT = 0.15
    READABILITY_WEIGHT = 0.10
    
    # Bonus multipliers
    STRUCTURE_BONUS_MULTIPLIER = 0.3
    READABILITY_BONUS_MULTIPLIER = 0.2
    
    @classmethod
    def calculate_overall_score(
        cls,
        completeness: float,
        purity: float,
        structure: float,
        readability: float
    ) -> float:
        """
        Domain-specific formula for overall quality calculation.
        Moved from LLM to ensure consistency and reliability.
        """
        # Primary calculation
        base_score = completeness - (1 - purity)  # Range: -1 to +1
        
        # Enhancement bonuses
        structure_bonus = (structure - 0.5) * cls.STRUCTURE_BONUS_MULTIPLIER
        readability_bonus = (readability - 0.5) * cls.READABILITY_BONUS_MULTIPLIER
        
        final_score = base_score + structure_bonus + readability_bonus
        
        # Clamp to valid range
        return max(-1.0, min(1.0, final_score))
    
    @classmethod
    def get_quality_classification(cls, score: float) -> tuple[str, str]:
        """Quality thresholds for classification"""
        if score >= 0.8:
            return ("EXCELLENT", "Perfect/near-perfect extraction")
        elif score >= 0.5:
            return ("GOOD", "High quality with minor issues")
        elif score >= 0.2:
            return ("FAIR", "Acceptable but needs improvement")
        elif score >= -0.2:
            return ("POOR", "Significant issues")
        else:
            return ("FAILED", "Extraction failure")
```

#### Result Processing in Evaluator

**Critical Implementation**: Automatic fallback to programmatic calculation:

```python
def _create_quality_result(self, llm_response: LLMResponse, evaluation_time: float) -> QualityAssessmentResult:
    """
    Parse AI response and create domain result.
    Automatically calculates overall score if not provided.
    """
    # Extract individual dimension scores
    completeness = float(scores.get("completeness", 0.0))
    purity = float(scores.get("purity", 0.0))
    structure = float(scores.get("structure", 0.0))
    readability = float(scores.get("readability", 0.0))
    
    # Use provided overall score if available, otherwise calculate
    if "overall" in scores:
        overall_score = float(scores["overall"])
    else:
        # AUTOMATIC FALLBACK: Use domain-specific formula
        overall_score = QualityScoring.calculate_overall_score(
            completeness, purity, structure, readability
        )
```

### 4. HTML Preprocessing Implementation

**Location**: `backend/apps/content/quality/html_preprocessor.py`

#### Structure Preservation Logic

```python
def preprocess_for_evaluation(
    self,
    html_content: str,
    url: str = None,
    max_tokens: int = 50000,
    preserve_html_structure: bool = True
) -> PreprocessedHTML:
    """
    Intelligent HTML preprocessing with structure preservation.
    Optimized for quality evaluation rather than content extraction.
    """
    if preserve_html_structure:
        # Parse with structure preservation
        soup = BeautifulSoup(html_content, 'lxml')
        
        # Remove noise while preserving content structure
        self._remove_noise_elements(soup)
        
        # Preserve semantic HTML tags
        preserved_tags = {
            'div', 'section', 'article', 'main', 'header', 'footer',
            'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            'p', 'span', 'a', 'img', 'ul', 'ol', 'li',
            'blockquote', 'code', 'pre', 'table', 'tr', 'td', 'th'
        }
        
        # Clean and format with proper indentation
        cleaned_html = self._format_with_indentation(soup, preserved_tags)
        
    return PreprocessedHTML(
        cleaned_html=cleaned_html,
        original_size=len(html_content),
        cleaned_size=len(cleaned_html),
        compression_ratio=1 - (len(cleaned_html) / len(html_content)),
        processing_method="structure_preserving",
        preserved_structure=True
    )
```

### 5. Management Commands Implementation

#### Template Comparison Framework

**Location**: `backend/apps/content/quality/management/commands/compare_templates.py`

```python
class Command(BaseCommand):
    def _run_comparison(self, templates, reference_examples, options):
        """
        Comprehensive template comparison with statistical analysis.
        """
        for template_id in templates.keys():
            for ref_example in reference_examples:
                # Evaluate with this template
                evaluator = ContentQualityEvaluator(template_id=template_id)
                result = evaluator.evaluate_article_quality(
                    ref_example.article,
                    model_override=options['model']
                )
                
                # Calculate accuracy metrics (MAE)
                accuracy = self._calculate_accuracy(ref_example, result)
                
                # Store for statistical analysis
                template_results[template_id]['scores'].append(accuracy)
        
        # Generate comprehensive comparison report
        self._display_results(results, options)
    
    def _calculate_accuracy(self, ref_example, result):
        """Mean Absolute Error calculation for each dimension"""
        return {
            'completeness_mae': abs(result.completeness - ref_example.reference_completeness),
            'purity_mae': abs(result.purity - ref_example.reference_purity),
            'structure_mae': abs(result.structure - ref_example.reference_structure),
            'readability_mae': abs(result.readability - ref_example.reference_readability),
            'overall_mae': abs(result.overall_score - ref_example.reference_overall_score),
            'total_mae': sum([...]) / 5  # Average across all dimensions
        }
```

#### Batch Evaluation Implementation

**Location**: `backend/apps/content/quality/management/commands/evaluate_batch_by_ids.py`

```python
class Command(BaseCommand):
    def handle(self, *args, **options):
        """
        Batch evaluation with comprehensive statistics and error handling.
        """
        # Parse and validate article IDs
        article_ids = [int(id_str.strip()) for id_str in options['ids'].split(',')]
        
        # Initialize evaluator
        evaluator = ContentQualityEvaluator(template_id=options.get('template'))
        
        # Process each article with error handling
        for i, article in enumerate(articles, 1):
            try:
                result = evaluator.evaluate_article_quality(
                    article,
                    include_html=options['include_html'],
                    model_override=options['model']
                )
                
                # Rate limiting
                if i < len(articles):
                    time.sleep(options['delay'])
                    
            except Exception as e:
                # Graceful error handling
                self.stdout.write(self.style.ERROR(f"❌ Evaluation failed: {e}"))
                
        # Comprehensive statistical summary
        self._display_summary(results, options)
```

## Key Implementation Decisions

### 1. **Removed Overall Score from Templates**

**Problem**: LLMs were inconsistent at mathematical calculations
**Solution**: Templates only provide 4 dimension scores, overall calculated programmatically
**Impact**: 100% scoring consistency, eliminated calculation errors

### 2. **Structure-Preserving HTML Preprocessing**

**Problem**: Plain text preprocessing lost document hierarchy
**Solution**: Preserve semantic HTML tags with proper indentation
**Impact**: Better quality assessment, maintained content structure

### 3. **Template-Based Few-Shot Examples**

**Problem**: Hardcoded example formatting was inflexible
**Solution**: Template system for consistent example formatting
**Impact**: Maintainable few-shot learning, version control

### 4. **Removed Caching System**

**Problem**: Caching added complexity and debugging friction
**Solution**: Removed entire caching system for simplicity
**Impact**: ~100 lines less code, predictable behavior

### 5. **Domain-Driven Architecture**

**Problem**: AI infrastructure mixed with content logic
**Solution**: Clear separation of concerns with dependency injection
**Impact**: Testable, maintainable, provider-agnostic

## Database Schema Implementation

### Quality Scoring Model

```sql
CREATE TABLE content_quality_scoring (
    id SERIAL PRIMARY KEY,
    public_id UUID UNIQUE NOT NULL,
    article_id INTEGER REFERENCES articles_article(id),
    
    -- Quality scores (DECIMAL for precision)
    overall_score DECIMAL(4,3) NOT NULL,
    completeness_score DECIMAL(4,3),
    purity_score DECIMAL(4,3),
    structure_score DECIMAL(4,3),
    readability_score DECIMAL(4,3),
    
    -- Assessment metadata
    assessment_method VARCHAR(50) NOT NULL,
    confidence_score DECIMAL(4,3) NOT NULL,
    processing_time_ms INTEGER NOT NULL,
    
    -- Template tracking
    template_used VARCHAR(100),
    template_version VARCHAR(50),
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_quality_scoring_article ON content_quality_scoring(article_id);
CREATE INDEX idx_quality_scoring_overall ON content_quality_scoring(overall_score);
CREATE INDEX idx_quality_scoring_created ON content_quality_scoring(created_at);
```

### Reference Examples Model

```sql
CREATE TABLE quality_reference_examples (
    id SERIAL PRIMARY KEY,
    public_id UUID UNIQUE NOT NULL,
    article_id INTEGER REFERENCES articles_article(id),
    
    -- Classification
    quality_class VARCHAR(20) NOT NULL,
    
    -- Reference scores (ground truth)
    reference_overall_score REAL NOT NULL,
    reference_completeness REAL NOT NULL,
    reference_purity REAL NOT NULL,
    reference_structure REAL NOT NULL,
    reference_readability REAL NOT NULL,
    
    -- Reference details
    reference_explanation TEXT NOT NULL,
    reference_missing_elements JSONB DEFAULT '[]',
    reference_noise_detected JSONB DEFAULT '[]',
    reference_key_strengths JSONB DEFAULT '[]',
    reference_improvement_areas JSONB DEFAULT '[]',
    
    -- Usage flags
    use_in_prompts BOOLEAN DEFAULT TRUE,
    use_for_calibration BOOLEAN DEFAULT TRUE,
    use_for_benchmarking BOOLEAN DEFAULT TRUE,
    
    -- Metadata
    created_by VARCHAR(100) DEFAULT 'system',
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_reference_examples_quality_class ON quality_reference_examples(quality_class);
CREATE INDEX idx_reference_examples_prompts ON quality_reference_examples(use_in_prompts);
```

## Error Handling and Resilience

### Graceful Degradation

```python
def _create_fallback_result(self, error_message: str, evaluation_time: float) -> QualityAssessmentResult:
    """
    Fallback result when evaluation fails.
    Ensures system continues operating with degraded functionality.
    """
    return QualityAssessmentResult(
        overall_score=0.0,
        completeness=0.0,
        purity=0.0,
        structure=0.0,
        readability=0.0,
        confidence=0.0,
        explanation=f"Evaluation failed: {error_message}",
        missing_elements=["evaluation_failed"],
        noise_detected=["evaluation_error"],
        evaluation_time=evaluation_time,
        model_used="none",
        tokens_used=0,
        cost_usd=Decimal('0.0')
    )
```

### Rate Limiting and Retry Logic

```python
# Built into AI service layer
try:
    llm_response = self.ai_service.call_llm(
        prompt=prompt,
        operation="quality_assessment",
        max_tokens=800,
        temperature=0.2,
        model_override=model_override,
        response_format="json"
    )
except RateLimitError:
    # Automatic retry with exponential backoff
    time.sleep(retry_delay)
    # ... retry logic
```

## Testing Strategy

### Unit Tests

```python
# Test domain scoring logic
def test_calculate_overall_score():
    score = QualityScoring.calculate_overall_score(
        completeness=0.8, purity=0.9, structure=0.7, readability=0.8
    )
    assert -1.0 <= score <= 1.0

# Test template formatting
def test_template_formatting():
    template = get_template("comprehensive_quality_evaluation_v3.1")
    formatted = template.format(title="Test", author="Author", ...)
    assert "Test" in formatted
```

### Integration Tests

```python
# Test end-to-end evaluation
def test_article_evaluation():
    evaluator = ContentQualityEvaluator()
    result = evaluator.evaluate_article_quality(test_article)
    assert isinstance(result, QualityAssessmentResult)
    assert -1.0 <= result.overall_score <= 1.0
```

---

## Related Documentation

- **[Architecture Overview](./architecture.md)** - System design and relationships
- **[Process Workflows](./workflows.md)** - End-to-end processes
- **[Command Reference](./commands.md)** - Management command details 