# AI Content Processing - API Reference

## Overview

This document provides comprehensive API reference for all classes, methods, and interfaces in the AI content processing pipeline.

## Core Classes

### AIProcessor

Main orchestrator for AI-powered content extraction.

```python
class AIProcessor:
    """
    AI-powered content processor with graceful error handling and retry logic.
    
    Orchestrates the complete extraction pipeline from raw HTML to structured
    ContentBlock objects using LLM-based semantic understanding.
    """
    
    def __init__(self, template_id: Optional[str] = None):
        """
        Initialize AI processor with optional template override.
        
        Args:
            template_id: Optional template identifier to use instead of default
        """
    
    def extract_content(self, raw_html: str, article_metadata: dict) -> ProcessingResult:
        """
        Extract structured content from raw HTML using AI processing.
        
        Args:
            raw_html: Raw HTML content to process
            article_metadata: Dictionary containing article metadata
                - title: Article title (required)
                - url: Article URL (required)
                - source: Publication name (optional)
                - language: Language code (optional)
                - published_at: Publication timestamp (optional)
        
        Returns:
            ProcessingResult object containing:
                - success: Boolean indicating processing success
                - clean_content: Text representation of extracted content
                - content_blocks: List of ContentBlock objects
                - extracted_metadata: Additional metadata extracted during processing
                - processing_time_ms: Processing time in milliseconds
                - error_message: Error details if processing failed
        
        Raises:
            ProcessingError: If processing fails completely after retries
            ValidationError: If input validation fails
        """
    
    def _should_retry_ai_failure(self, error_message: str, attempt_count: int) -> bool:
        """
        Determine if an AI processing failure should be retried.
        
        Intelligently distinguishes between transient failures (network issues,
        rate limits) and permanent failures (invalid content, parsing errors).
        
        Args:
            error_message: Error message from failed processing attempt
            attempt_count: Current attempt number (1-based)
        
        Returns:
            Boolean indicating whether retry should be attempted
        """
    
    def _should_retry_exception(self, exception: Exception, attempt_count: int) -> bool:
        """
        Determine if an exception should trigger a retry.
        
        Args:
            exception: Exception that occurred during processing
            attempt_count: Current attempt number (1-based)
        
        Returns:
            Boolean indicating whether retry should be attempted
        """
```

### ContentBlockBuilder

Converts AI JSON responses to structured ContentBlock objects.

```python
class ContentBlockBuilder:
    """
    Builds ContentBlock objects from AI JSON responses with graceful error handling.
    
    Validates content structure, filters invalid blocks, and preserves valid
    content even when some blocks are malformed.
    """
    
    def __init__(self):
        """Initialize content block builder with validation rules."""
    
    def build_blocks(self, blocks_data: List[dict]) -> List[ContentBlock]:
        """
        Build ContentBlock objects from AI JSON response data.
        
        Applies comprehensive validation and filtering to ensure only valid
        blocks are included while preserving maximum content.
        
        Args:
            blocks_data: List of dictionaries containing block data from AI response
        
        Returns:
            List of valid ContentBlock objects
            
        Note:
            Invalid blocks are filtered out with warning-level logging.
            Processing continues with valid blocks even if some are invalid.
        """
    
    def _validate_block_structure(self, block_data: dict) -> bool:
        """
        Validate the structure of a single content block.
        
        Args:
            block_data: Dictionary containing block data
        
        Returns:
            Boolean indicating whether block structure is valid
        """
    
    def _validate_block_type(self, block_type: str) -> bool:
        """
        Validate content block type with forward compatibility.
        
        Args:
            block_type: Block type string from AI response
        
        Returns:
            Boolean indicating whether block type is supported
            
        Note:
            Unknown block types are logged but return False to filter them out.
            This provides forward compatibility for new block types.
        """
    
    def _create_content_block(self, block_data: dict, position: int) -> Optional[ContentBlock]:
        """
        Create a ContentBlock object from validated block data.
        
        Args:
            block_data: Validated block data dictionary
            position: Sequential position in the content
        
        Returns:
            ContentBlock object or None if creation fails
        """
```

### ExtractionTemplateManager

Manages AI prompt templates for content extraction.

```python
class ExtractionTemplateManager:
    """
    Manages prompt templates for AI content extraction.
    
    Handles template selection, formatting, and versioning for different
    content types and extraction scenarios.
    """
    
    def __init__(self, default_template: str = "comprehensive_v2"):
        """
        Initialize template manager with default template.
        
        Args:
            default_template: Default template identifier to use
        """
    
    def format_prompt(self, preprocessed_html: str, article_metadata: dict, 
                     template_id: Optional[str] = None) -> str:
        """
        Format extraction prompt using specified template.
        
        Args:
            preprocessed_html: HTML content optimized for AI processing
            article_metadata: Article metadata for context
            template_id: Optional template override
        
        Returns:
            Formatted prompt string ready for AI processing
        """
    
    def get_template(self, template_id: str) -> BasePromptTemplate:
        """
        Get template instance by identifier.
        
        Args:
            template_id: Template identifier
        
        Returns:
            Template instance
            
        Raises:
            TemplateNotFoundError: If template doesn't exist
        """
```

## Data Models

### ContentBlock

Represents a structured content element extracted from articles.

```python
@dataclass
class ContentBlock:
    """
    Structured content block representing a semantic element from an article.
    
    Attributes:
        type: Block type (heading, paragraph, image, etc.)
        content: Main text content of the block
        level: Heading level (1-6) for heading blocks, None for others
        position: Sequential position in the content (0-based)
        metadata: Additional type-specific metadata
    """
    
    type: str
    content: str = ""
    level: Optional[int] = None
    position: int = 0
    metadata: dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """Convert ContentBlock to dictionary representation."""
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ContentBlock':
        """Create ContentBlock from dictionary data."""
    
    def is_valid(self) -> bool:
        """Validate ContentBlock structure and content."""
```

### ProcessingResult

Contains the complete result of content processing.

```python
@dataclass
class ProcessingResult:
    """
    Complete result of content processing operation.
    
    Attributes:
        success: Whether processing completed successfully
        clean_content: Plain text representation of extracted content
        content_blocks: List of structured content blocks
        extracted_metadata: Additional metadata extracted during processing
        processing_time_ms: Processing time in milliseconds
        token_usage: Number of tokens used in AI processing
        cost: Processing cost in USD
        error_message: Error details if processing failed
        retry_count: Number of retry attempts made
    """
    
    success: bool
    clean_content: str = ""
    content_blocks: List[ContentBlock] = field(default_factory=list)
    extracted_metadata: dict = field(default_factory=dict)
    processing_time_ms: int = 0
    token_usage: int = 0
    cost: float = 0.0
    error_message: str = ""
    retry_count: int = 0
    
    def to_dict(self) -> dict:
        """Convert ProcessingResult to dictionary representation."""
```

## Template Classes

### BasePromptTemplate

Base class for all extraction prompt templates.

```python
class BasePromptTemplate:
    """
    Base class for AI extraction prompt templates.
    
    Provides common functionality for template management, formatting,
    and response validation.
    """
    
    def __init__(self):
        """Initialize base template with common settings."""
        self.template_name = ""
        self.version = ""
        self.operation = "content_extraction"
    
    def format(self, preprocessed_html: str, article_metadata: dict) -> str:
        """
        Format the complete prompt for AI processing.
        
        Args:
            preprocessed_html: Optimized HTML content
            article_metadata: Article context information
        
        Returns:
            Complete prompt string
        """
    
    def get_system_prompt(self) -> str:
        """Get the system prompt component."""
    
    def get_user_prompt(self, preprocessed_html: str, article_metadata: dict) -> str:
        """Get the user prompt component with content."""
    
    def validate_response(self, response: dict) -> bool:
        """Validate AI response structure."""
```

### ComprehensiveExtractionTemplateV2

Enhanced extraction template with comprehensive content type support.

```python
class ComprehensiveExtractionTemplateV2(BasePromptTemplate):
    """
    Enhanced content extraction template supporting comprehensive content types.
    
    Supports:
    - Core content: headings, paragraphs, images, quotes, lists
    - Media embeds: Twitter, video, iframe, general embeds
    - Structured content: tables, code blocks
    - Layout elements: dividers, raw HTML
    
    Features:
    - Forward compatibility for unknown block types
    - Detailed metadata extraction
    - Few-shot learning examples
    - Token-optimized prompts
    """
    
    def __init__(self):
        super().__init__()
        self.template_name = "comprehensive_extraction_v2"
        self.version = "2.0"
        self.supported_block_types = {
            "heading", "subtitle", "paragraph", "image", "figure", "quote", "list",
            "twitter_embed", "video_embed", "iframe", "embed",
            "table", "code", "editorial_note", "divider", "raw_html"
        }
    
    def get_response_schema(self) -> dict:
        """Get JSON schema for expected AI response format."""
    
    def get_few_shot_examples(self) -> List[dict]:
        """Get few-shot learning examples for template calibration."""
```

## Utility Classes

### ProcessingRouter

Determines optimal processing route for articles.

```python
class ProcessingRouter:
    """
    Determines optimal processing strategy for articles.
    
    Routes between AI processor and algorithmic processor based on
    content complexity, publication preferences, and quality requirements.
    """
    
    def determine_route(self, article) -> str:
        """
        Determine optimal processing route for an article.
        
        Args:
            article: Article model instance
        
        Returns:
            Route identifier ("ai_enhanced" or "algorithmic")
        """
    
    def _analyze_content_complexity(self, article) -> float:
        """Analyze article content complexity (0.0-1.0)."""
    
    def _check_publication_preferences(self, article) -> dict:
        """Check publication-specific processing preferences."""
    
    def _requires_ai_processing(self, article) -> bool:
        """Determine if article requires AI processing."""
```

### FilterManager

Handles language and region filtering for article processing.

```python
class FilterManager:
    """
    Manages filtering logic for article processing.
    
    Applies language and region filters to optimize processing
    for specific user preferences and system requirements.
    """
    
    def apply_language_filter(self, queryset, language_codes: List[str]):
        """
        Apply language filtering to article queryset.
        
        Args:
            queryset: Django queryset of articles
            language_codes: List of ISO language codes
        
        Returns:
            Filtered queryset
        """
    
    def apply_region_filter(self, queryset, region_codes: List[str]):
        """
        Apply region filtering to article queryset.
        
        Args:
            queryset: Django queryset of articles
            region_codes: List of region codes
        
        Returns:
            Filtered queryset
        """
    
    def validate_filters(self, language_codes: List[str], region_codes: List[str]) -> dict:
        """Validate filter parameters and return validation results."""
```

## Integration Classes

### AIServiceIntegration

Integration layer with AIProviders service.

```python
class AIServiceIntegration:
    """
    Integration layer with centralized AI service.
    
    Handles token management, cost tracking, and provider abstraction
    for content extraction operations.
    """
    
    def __init__(self):
        """Initialize AI service integration."""
        from apps.aiproviders.services import get_ai_service
        self.ai_service = get_ai_service()
    
    def process_with_ai(self, prompt: str, max_tokens: Optional[int] = None) -> dict:
        """
        Process content using AI service with optimized token management.
        
        Args:
            prompt: Formatted extraction prompt
            max_tokens: Optional token limit override
        
        Returns:
            AI service response with usage tracking
        """
    
    def get_optimal_token_limit(self, model_name: str) -> int:
        """Get optimal token limit for specified model."""
    
    def track_usage(self, operation: str, tokens: int, cost: float):
        """Track token usage and costs for monitoring."""
```

## Constants and Enums

### Block Types

```python
class BlockType:
    """Supported content block types."""
    
    # Core content types
    HEADING = "heading"
    SUBTITLE = "subtitle"
    PARAGRAPH = "paragraph"
    IMAGE = "image"
    FIGURE = "figure"
    QUOTE = "quote"
    LIST = "list"
    
    # Media and embeds
    TWITTER_EMBED = "twitter_embed"
    VIDEO_EMBED = "video_embed"
    IFRAME = "iframe"
    EMBED = "embed"
    
    # Structured content
    TABLE = "table"
    CODE = "code"
    EDITORIAL_NOTE = "editorial_note"
    
    # Layout elements
    DIVIDER = "divider"
    RAW_HTML = "raw_html"
    
    @classmethod
    def all_types(cls) -> Set[str]:
        """Get all supported block types."""
        return {
            cls.HEADING, cls.SUBTITLE, cls.PARAGRAPH, cls.IMAGE, cls.FIGURE,
            cls.QUOTE, cls.LIST, cls.TWITTER_EMBED, cls.VIDEO_EMBED,
            cls.IFRAME, cls.EMBED, cls.TABLE, cls.CODE, cls.EDITORIAL_NOTE,
            cls.DIVIDER, cls.RAW_HTML
        }
```

### Processing Status

```python
class ProcessingStatus:
    """Article processing status values."""
    
    PENDING = "pending"
    PROCESSING = "processing"
    PROCESSED = "processed"
    AI_FAILED = "ai_failed"
    FAILED = "failed"
    
    @classmethod
    def active_statuses(cls) -> List[str]:
        """Get statuses indicating active processing."""
        return [cls.PENDING, cls.PROCESSING]
    
    @classmethod
    def completed_statuses(cls) -> List[str]:
        """Get statuses indicating completed processing."""
        return [cls.PROCESSED, cls.AI_FAILED, cls.FAILED]
```

## Configuration

### Token Limits

```python
TOKEN_LIMITS = {
    "gpt-4.1-preview": 30000,  # Close to 32,768 limit but safe
    "gpt-4o": 8000,           # Conservative for 128k context
    "gpt-4": 8000,            # Proven reliable limit
    "gpt-3.5-turbo": 4000,    # Standard conservative limit
}

DEFAULT_TOKEN_LIMIT = 4000  # Conservative default for unknown models
```

### Retry Configuration

```python
RETRY_CONFIG = {
    "max_attempts": 3,
    "base_delay_seconds": 2,
    "max_delay_seconds": 60,
    "backoff_strategy": "exponential",
    
    "transient_indicators": [
        "timeout", "timed out", "rate_limit", "rate limit",
        "503", "502", "500", "network", "connection",
        "unavailable", "overloaded", "busy"
    ],
    
    "permanent_indicators": [
        "invalid_json", "json", "parsing", "malformed",
        "token_limit", "too_long", "invalid_content",
        "unsupported", "blocked", "filtered"
    ]
}
```

This API reference provides comprehensive documentation for all components in the AI content processing pipeline, enabling developers to understand, use, and extend the system effectively. 