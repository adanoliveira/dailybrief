# API Reference

> **Complete API reference for the Content Quality Assessment System classes, methods, and interfaces**

## Overview

This reference provides detailed documentation for all public APIs, classes, and methods in the Content Quality Assessment System. The system follows domain-driven design principles with clear separation between content logic and AI infrastructure.

## Core Classes

### ContentQualityEvaluator

**Location**: `backend/apps/content/quality/evaluator.py`

Main orchestration class for content quality evaluation.

```python
class ContentQualityEvaluator:
    """
    Central orchestration of quality evaluation process.
    Separates content domain logic from AI infrastructure.
    """
```

#### Constructor

```python
def __init__(self, template_id: Optional[str] = None):
    """
    Initialize evaluator with optional template specification.
    
    Args:
        template_id: Template identifier to use for evaluation.
                    Defaults to ACTIVE_TEMPLATE if not specified.
    
    Raises:
        KeyError: If template_id is not found in AVAILABLE_TEMPLATES.
    """
```

#### Main Methods

##### evaluate_article_quality

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
    
    Args:
        article: Article instance to evaluate
        include_html: Whether to include HTML in evaluation
        model_override: Override default model selection
        use_html_preprocessing: Whether to use intelligent HTML preprocessing
        
    Returns:
        QualityAssessmentResult: Comprehensive quality assessment
        
    Raises:
        ArticleProcessingError: If article is not in 'completed' status
        AIServiceError: If AI service call fails
        ValidationError: If article content is invalid
        
    Example:
        ```python
        evaluator = ContentQualityEvaluator()
        result = evaluator.evaluate_article_quality(
            article=article,
            model_override="gpt-4o-mini"
        )
        print(f"Quality score: {result.overall_score}")
        ```
    """
```

#### Private Methods

##### _prepare_extracted_content

```python
def _prepare_extracted_content(self, article: Article) -> Dict[str, Any]:
    """
    Prepares structured content blocks for evaluation.
    
    Args:
        article: Article instance with content blocks
        
    Returns:
        Dict containing formatted content and metadata:
        - blocks_info: JSON-formatted content blocks
        - metadata_info: Article metadata dictionary
        - content_summary: High-level content summary
        
    Example Output:
        {
            "blocks_info": "[{\"type\": \"paragraph\", \"content\": \"...\"}]",
            "metadata_info": {
                "word_count": 1250,
                "read_time": 5,
                "has_images": True
            },
            "content_summary": "Technology article about AI advancements"
        }
    """
```

##### _prepare_html_sample

```python
def _prepare_html_sample(
    self, 
    article: Article, 
    include_html: bool = True,
    use_preprocessing: bool = True,
    max_tokens: int = 50000
) -> Dict[str, Any]:
    """
    Optimizes HTML for evaluation with structure preservation.
    
    Args:
        article: Article with raw HTML content
        include_html: Whether to include HTML in output
        use_preprocessing: Whether to apply intelligent preprocessing
        max_tokens: Maximum token limit for LLM context
        
    Returns:
        Dict containing processed HTML and metrics:
        - html_sample: Cleaned and optimized HTML
        - html_length: Character count of processed HTML
        - preprocessing_summary: Processing statistics
        
    Example Output:
        {
            "html_sample": "<article><h1>Title</h1><p>Content...</p></article>",
            "html_length": 12450,
            "preprocessing_summary": {
                "compression_ratio": 0.73,
                "preserved_structure": True
            }
        }
    """
```

##### _prepare_reference_examples

```python
def _prepare_reference_examples(self, max_per_class: int = 1) -> str:
    """
    Template-based few-shot example preparation.
    
    Args:
        max_per_class: Maximum examples per quality class
        
    Returns:
        Formatted string containing all reference examples
        
    Example Output:
        "=== REFERENCE EXAMPLES ===\n\n"
        "Example 1 (GOOD): Article about climate change...\n"
        "Expected scores: C:0.85 P:0.90 S:0.75 R:0.80\n\n"
        "Example 2 (POOR): Article with extraction issues...\n"
        "Expected scores: C:0.25 P:0.15 S:0.30 R:0.35"
    """
```

---

### Template System

#### BasePromptTemplate

**Location**: `backend/apps/content/quality/prompt_templates.py`

Abstract base class for all prompt templates.

```python
class BasePromptTemplate(ABC):
    """Abstract base ensuring consistent template interface"""
```

##### Abstract Properties

```python
@property
@abstractmethod
def metadata(self) -> PromptTemplateMetadata:
    """
    Template metadata for tracking and versioning.
    
    Returns:
        PromptTemplateMetadata: Metadata object containing:
        - name: Template name
        - version: Version string
        - description: Template description
        - author: Template author
        - created_date: Creation date
        - last_modified: Last modification date
    """

@property
@abstractmethod
def template_text(self) -> str:
    """
    The actual prompt template with variable placeholders.
    
    Returns:
        str: Template string with {variable} placeholders
    """
```

##### Methods

```python
def format(self, **kwargs) -> str:
    """
    Format template with provided variables.
    
    Args:
        **kwargs: Variable substitutions for template
        
    Returns:
        str: Formatted prompt ready for AI service
        
    Raises:
        KeyError: If required template variables are missing
        
    Example:
        ```python
        template = get_template("comprehensive_quality_evaluation_v3.1")
        prompt = template.format(
            title="News Article",
            content="Article content...",
            html_sample="<article>...</article>"
        )
        ```
    """

@property
def identifier(self) -> str:
    """
    Unique identifier combining name and version.
    
    Returns:
        str: Format "{name}_{version}"
        
    Example:
        "comprehensive_quality_evaluation_v3.1"
    """
```

#### Template Implementations

##### ComprehensiveQualityEvaluator

```python
class ComprehensiveQualityEvaluator(BasePromptTemplate):
    """
    Baseline comprehensive quality evaluation template.
    
    Features:
    - XML-like structured evaluation
    - Detailed explanations and examples
    - Fast evaluation times (~15 seconds)
    - Best for general assessment and production monitoring
    
    Optimal Use Cases:
    - Production quality monitoring
    - General content evaluation
    - High-quality content assessment
    """
```

##### StructuredRubricEvaluator

```python
class StructuredRubricEvaluator(BasePromptTemplate):
    """
    Anchor-based structured rubric evaluation template.
    
    Features:
    - 5-point anchor system (0.0, 0.25, 0.5, 0.75, 1.0)
    - Look-fors, Questions, and Red-flags for each dimension
    - Perfect for extreme quality detection
    - Decisive scoring behavior
    
    Optimal Use Cases:
    - Quality filtering and rejection decisions
    - Poor content detection
    - Binary classification tasks
    """
```

#### Template Management Functions

```python
def get_template(template_id: str = None) -> BasePromptTemplate:
    """
    Get template instance with fallback to active template.
    
    Args:
        template_id: Template identifier or None for default
        
    Returns:
        BasePromptTemplate: Template instance
        
    Raises:
        KeyError: If template_id not found in AVAILABLE_TEMPLATES
        
    Example:
        ```python
        # Get active template
        template = get_template()
        
        # Get specific template
        template = get_template("structured_rubric_evaluation_v2025-05-v3")
        ```
    """

def get_few_shot_template() -> BasePromptTemplate:
    """
    Get template for few-shot example formatting.
    
    Returns:
        BasePromptTemplate: Few-shot example template
    """

def list_available_templates() -> List[str]:
    """
    List all available template identifiers.
    
    Returns:
        List[str]: Template identifiers
        
    Example:
        ["comprehensive_quality_evaluation_v3.1", 
         "structured_rubric_evaluation_v2025-05-v3"]
    """
```

---

### Data Models

#### QualityAssessmentResult

**Location**: `backend/apps/content/quality/models.py`

Domain model representing evaluation results.

```python
@dataclass
class QualityAssessmentResult:
    """
    Pure domain object representing evaluation results.
    Immutable data class with comprehensive quality metrics.
    """
```

##### Fields

```python
# Core quality metrics (0 to 1 scale)
overall_score: float        # Final score (-1 to +1)
completeness: float         # How much content was captured (0-1)
purity: float              # How clean the content is (0-1)
structure: float           # How well structure is preserved (0-1)
readability: float         # How readable the content is (0-1)

# Meta information
confidence: float          # Evaluator confidence (0-1)
explanation: str           # Detailed assessment explanation
missing_elements: List[str] # Specific missing content items
noise_detected: List[str]  # Specific noise patterns found
key_strengths: List[str]   # Extraction strengths identified
improvement_areas: List[str] # Areas needing improvement

# Technical metadata
evaluation_time: float     # Processing time in seconds
model_used: str           # AI model identifier
tokens_used: int          # Token count for evaluation
cost_usd: Decimal         # Cost in USD
template_used: str        # Template identifier
template_version: str     # Template version
assessment_timestamp: datetime # When evaluation was performed
```

##### Methods

```python
def get_quality_classification(self) -> Tuple[str, str]:
    """
    Get quality classification based on overall score.
    
    Returns:
        Tuple[str, str]: (classification, description)
        
    Classifications:
        - ("EXCELLENT", "Perfect/near-perfect extraction") for score ≥ 0.8
        - ("GOOD", "High quality with minor issues") for score ≥ 0.5
        - ("FAIR", "Acceptable but needs improvement") for score ≥ 0.2
        - ("POOR", "Significant issues") for score ≥ -0.2
        - ("FAILED", "Extraction failure") for score < -0.2
    """

def to_dict(self) -> Dict[str, Any]:
    """
    Convert to dictionary for serialization.
    
    Returns:
        Dict[str, Any]: Dictionary representation
    """

def is_production_ready(self) -> bool:
    """
    Check if quality meets production standards.
    
    Returns:
        bool: True if overall_score >= 0.5
    """
```

#### QualityScoring

**Location**: `backend/apps/content/quality/models.py`

Database model for persistent quality storage.

```python
class QualityScoring(models.Model):
    """
    Persistent storage for quality evaluation results.
    Optimized for database queries and analytics.
    """
```

##### Fields

```python
# Primary key and relationships
id = models.AutoField(primary_key=True)
public_id = models.UUIDField(unique=True, default=uuid.uuid4)
article = models.ForeignKey('articles.Article', on_delete=models.CASCADE)

# Quality scores (DecimalField for precision)
overall_score = models.DecimalField(max_digits=4, decimal_places=3)
completeness_score = models.DecimalField(max_digits=4, decimal_places=3)
purity_score = models.DecimalField(max_digits=4, decimal_places=3)
structure_score = models.DecimalField(max_digits=4, decimal_places=3)
readability_score = models.DecimalField(max_digits=4, decimal_places=3)

# Assessment metadata
assessment_method = models.CharField(max_length=50)
confidence_score = models.DecimalField(max_digits=4, decimal_places=3)
processing_time_ms = models.IntegerField()

# Template tracking
template_used = models.CharField(max_length=100)
template_version = models.CharField(max_length=50)

# Additional metadata
explanation = models.TextField()
missing_elements = models.JSONField(default=list)
noise_detected = models.JSONField(default=list)

# Timestamps
created_at = models.DateTimeField(auto_now_add=True)
updated_at = models.DateTimeField(auto_now=True)
```

##### Class Methods

```python
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
    
    Args:
        completeness: Completeness score (0-1)
        purity: Purity score (0-1)
        structure: Structure score (0-1)
        readability: Readability score (0-1)
        
    Returns:
        float: Overall quality score (-1 to +1)
        
    Formula:
        base = completeness - (1 - purity)  # Range: -1 to +1
        structure_bonus = (structure - 0.5) * 0.3  # ±0.15
        readability_bonus = (readability - 0.5) * 0.2  # ±0.10
        overall = clamp(base + structure_bonus + readability_bonus, -1, 1)
        
    Example:
        ```python
        score = QualityScoring.calculate_overall_score(
            completeness=0.85,
            purity=0.90,
            structure=0.75,
            readability=0.80
        )
        # Returns: 0.785
        ```
    """

@classmethod
def get_quality_classification(cls, score: float) -> Tuple[str, str]:
    """
    Get quality classification for given score.
    
    Args:
        score: Overall quality score (-1 to +1)
        
    Returns:
        Tuple[str, str]: (classification, description)
    """
```

##### Instance Methods

```python
def to_domain_result(self) -> QualityAssessmentResult:
    """
    Convert database model to domain result object.
    
    Returns:
        QualityAssessmentResult: Domain representation
    """

def get_dimension_scores(self) -> Dict[str, float]:
    """
    Get all dimension scores as dictionary.
    
    Returns:
        Dict[str, float]: {dimension: score} mapping
        
    Example:
        {
            "completeness": 0.85,
            "purity": 0.90,
            "structure": 0.75,
            "readability": 0.80,
            "overall": 0.785
        }
    """
```

#### ReferenceQualityExample

**Location**: `backend/apps/content/quality/models.py`

Model for curated reference examples used in few-shot learning.

```python
class ReferenceQualityExample(models.Model):
    """
    Curated ground truth examples for evaluation calibration.
    Used for few-shot learning and template accuracy testing.
    """
```

##### Fields

```python
# Primary identification
id = models.AutoField(primary_key=True)
public_id = models.UUIDField(unique=True, default=uuid.uuid4)
article = models.ForeignKey('articles.Article', on_delete=models.CASCADE)

# Quality classification
quality_class = models.CharField(
    max_length=20, 
    choices=[
        ('perfect', 'Perfect Quality'),
        ('good', 'Good Quality'),
        ('imperfect', 'Imperfect Quality'),
        ('awful', 'Awful Quality')
    ]
)

# Reference scores (ground truth)
reference_overall_score = models.FloatField()
reference_completeness = models.FloatField()
reference_purity = models.FloatField()
reference_structure = models.FloatField()
reference_readability = models.FloatField()

# Reference assessment details
reference_explanation = models.TextField()
reference_missing_elements = models.JSONField(default=list)
reference_noise_detected = models.JSONField(default=list)
reference_key_strengths = models.JSONField(default=list)
reference_improvement_areas = models.JSONField(default=list)

# Usage configuration
use_in_prompts = models.BooleanField(default=True)
use_for_calibration = models.BooleanField(default=True)
use_for_benchmarking = models.BooleanField(default=True)

# Metadata
created_by = models.CharField(max_length=100, default='system')
notes = models.TextField(blank=True)
created_at = models.DateTimeField(auto_now_add=True)
updated_at = models.DateTimeField(auto_now=True)
```

##### Class Methods

```python
@classmethod
def get_for_prompts(cls, max_per_class: int = 1) -> QuerySet:
    """
    Get reference examples for use in prompts.
    
    Args:
        max_per_class: Maximum examples per quality class
        
    Returns:
        QuerySet: Filtered and limited examples
        
    Example:
        ```python
        examples = ReferenceQualityExample.get_for_prompts(max_per_class=2)
        for example in examples:
            print(f"{example.quality_class}: {example.reference_explanation}")
        ```
    """

@classmethod
def get_for_calibration(cls, quality_class: str = None) -> QuerySet:
    """
    Get examples for evaluator calibration.
    
    Args:
        quality_class: Optional filter by quality class
        
    Returns:
        QuerySet: Calibration examples
    """
```

---

### HTML Preprocessing

#### HTMLPreprocessor

**Location**: `backend/apps/content/quality/html_preprocessor.py`

Intelligent HTML optimization for quality evaluation.

```python
class HTMLPreprocessor:
    """
    Intelligent HTML optimization for quality evaluation.
    Preserves structure while reducing token usage.
    """
```

##### Methods

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
    
    Args:
        html_content: Raw HTML content
        url: Source URL for context-aware processing
        max_tokens: Maximum token limit for LLM context
        preserve_html_structure: Whether to preserve semantic structure
        
    Returns:
        PreprocessedHTML: Processed HTML with metrics
        
    Features:
        - Removes scripts, styles, and navigation
        - Preserves semantic HTML tags
        - Optimizes for LLM token efficiency
        - Maintains document hierarchy
        
    Example:
        ```python
        preprocessor = HTMLPreprocessor()
        result = preprocessor.preprocess_for_evaluation(
            html_content=raw_html,
            preserve_html_structure=True
        )
        print(f"Compression: {result.compression_ratio:.1%}")
        print(f"Size: {result.cleaned_size} chars")
        ```
    """

def get_preprocessing_summary(self, preprocessed: PreprocessedHTML) -> Dict[str, Any]:
    """
    Generate summary of preprocessing operations.
    
    Args:
        preprocessed: PreprocessedHTML result
        
    Returns:
        Dict[str, Any]: Processing statistics and metrics
        
    Example Output:
        {
            "compression_ratio": 0.73,
            "size_reduction": "74.2KB → 19.1KB",
            "preserved_structure": True,
            "processing_method": "structure_preserving",
            "removed_elements": ["script", "style", "nav"]
        }
    """
```

#### PreprocessedHTML

```python
@dataclass
class PreprocessedHTML:
    """Result object for HTML preprocessing operations."""
    
    cleaned_html: str              # Processed HTML content
    original_size: int             # Original content size in characters
    cleaned_size: int              # Processed content size in characters
    compression_ratio: float       # Size reduction ratio (0-1)
    processing_method: str         # Method used for processing
    preserved_structure: bool      # Whether structure was preserved
    removed_elements: List[str]    # Types of elements removed
    processing_time: float         # Time taken for processing
```

---

### Management Commands

#### Command Base Classes

All management commands inherit from Django's `BaseCommand` and follow consistent patterns.

##### Common Parameters

```python
# Standard parameters across all commands
class CommonCommandMixin:
    def add_common_arguments(self, parser):
        """Add standard arguments to command parser."""
        parser.add_argument('--model', type=str, default='gpt-4o-mini',
                          help='AI model to use')
        parser.add_argument('--template', type=str, 
                          help='Template ID to use')
        parser.add_argument('--delay', type=float, default=2.0,
                          help='Delay between API calls')
        parser.add_argument('--verbose', action='store_true',
                          help='Detailed output')
```

#### Available Commands

##### evaluate_quality

```python
class Command(BaseCommand):
    """Evaluate content quality for articles."""
    
    def add_arguments(self, parser):
        """
        Command arguments:
        --article-id: Single article public ID
        --article-ids: Comma-separated public IDs
        --limit: Number of recent articles
        --include-html: Include HTML in evaluation
        --quality-class: Filter by quality class
        --max-examples: Maximum examples to process
        """

    def handle(self, *args, **options):
        """
        Main command execution.
        
        Returns comprehensive evaluation results with:
        - Individual article assessments
        - Quality distribution statistics
        - Performance metrics
        - Cost analysis
        """
```

##### compare_templates

```python
class Command(BaseCommand):
    """A/B test different prompt templates."""
    
    def add_arguments(self, parser):
        """
        Command arguments:
        --templates: Comma-separated template IDs
        --by-class: Compare across all quality classes
        --quality-class: Specific quality class filter
        --max-examples: Examples per quality class
        """

    def handle(self, *args, **options):
        """
        Template comparison execution.
        
        Returns:
        - Template performance rankings
        - Mean Absolute Error (MAE) calculations
        - Class-specific performance analysis
        - Optimization recommendations
        """
```

---

### Error Handling

#### Custom Exceptions

```python
class QualityEvaluationError(Exception):
    """Base exception for quality evaluation errors."""
    pass

class ArticleProcessingError(QualityEvaluationError):
    """Article is not ready for quality evaluation."""
    pass

class TemplateNotFoundError(QualityEvaluationError):
    """Requested template is not available."""
    pass

class AIServiceError(QualityEvaluationError):
    """AI service call failed."""
    pass

class ValidationError(QualityEvaluationError):
    """Input validation failed."""
    pass
```

#### Error Handling Patterns

```python
# Standard error handling in evaluator
try:
    result = evaluator.evaluate_article_quality(article)
except ArticleProcessingError as e:
    logger.error(f"Article not ready: {e}")
    # Return fallback result or re-raise
except AIServiceError as e:
    logger.error(f"AI service failed: {e}")
    # Implement retry logic or fallback
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    # Return error result with diagnostics
```

---

### Configuration

#### Settings

```python
# Quality evaluation settings
QUALITY_EVALUATION_SETTINGS = {
    'DEFAULT_TEMPLATE': 'comprehensive_quality_evaluation_v3.1',
    'ACTIVE_TEMPLATE': 'comprehensive_quality_evaluation_v3.1',
    'FEW_SHOT_TEMPLATE': 'few_shot_example_v1.0',
    'DEFAULT_MODEL': 'gpt-4o-mini',
    'MAX_TOKENS_PER_EVALUATION': 50000,
    'DEFAULT_DELAY_SECONDS': 2.0,
    'MAX_REFERENCE_EXAMPLES_PER_CLASS': 1,
    'ENABLE_HTML_PREPROCESSING': True,
    'PRESERVE_HTML_STRUCTURE': True
}
```

#### Model Configuration

```python
AVAILABLE_MODELS = {
    'gpt-4o-mini': {
        'context_window': 128000,
        'cost_per_token': 0.00000015,
        'recommended_use': 'production'
    },
    'gpt-4.1-mini': {
        'context_window': 2000000,
        'cost_per_token': 0.0000006,
        'recommended_use': 'large_content'
    },
    'gpt-4.1-nano': {
        'context_window': 2000000,
        'cost_per_token': 0.00000015,
        'recommended_use': 'budget'
    }
}
```

---

### Usage Examples

#### Basic Evaluation

```python
from apps.content.quality.evaluator import ContentQualityEvaluator
from apps.articles.models import Article

# Basic evaluation
evaluator = ContentQualityEvaluator()
article = Article.objects.get(public_id='abc123-def456')
result = evaluator.evaluate_article_quality(article)

print(f"Overall Quality: {result.overall_score:.3f}")
print(f"Classification: {result.get_quality_classification()[0]}")
```

#### Template Comparison

```python
from apps.content.quality.prompt_templates import get_template

# Compare two templates
templates = [
    'comprehensive_quality_evaluation_v3.1',
    'structured_rubric_evaluation_v2025-05-v3'
]

results = {}
for template_id in templates:
    evaluator = ContentQualityEvaluator(template_id=template_id)
    result = evaluator.evaluate_article_quality(article)
    results[template_id] = result

# Analyze differences
template1, template2 = results.values()
score_diff = abs(template1.overall_score - template2.overall_score)
print(f"Score difference: {score_diff:.3f}")
```

#### Batch Processing

```python
from apps.content.quality.evaluator import ContentQualityEvaluator
import time

evaluator = ContentQualityEvaluator()
articles = Article.objects.filter(process_status='completed')[:10]

results = []
for article in articles:
    try:
        result = evaluator.evaluate_article_quality(article)
        results.append(result)
        time.sleep(2)  # Rate limiting
    except Exception as e:
        print(f"Failed to evaluate {article.public_id}: {e}")

# Analyze batch results
avg_score = sum(r.overall_score for r in results) / len(results)
print(f"Average quality score: {avg_score:.3f}")
```

---

## Related Documentation

- **[Architecture Overview](./architecture.md)** - System design and component relationships  
- **[Implementation Guide](./implementation.md)** - Technical implementation details
- **[Process Workflows](./workflows.md)** - End-to-end evaluation processes
- **[Command Reference](./commands.md)** - Management command documentation 