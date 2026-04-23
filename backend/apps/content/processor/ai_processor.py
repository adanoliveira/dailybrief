"""
AI Content Processor - Semantic Content Extraction.

This module implements AI-powered content extraction following proven patterns
from the quality evaluation system. It uses the aiproviders service for AI
infrastructure and reuses HTML preprocessing patterns for reliability.

Following SOLID principles with clear separation of concerns:
- AI infrastructure: delegated to aiproviders service
- Content extraction logic: contained in this domain
- HTML preprocessing: reused from quality service
"""
import json
import time
import logging
import threading
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from django.conf import settings

from apps.aiproviders.services import get_ai_service, LLMResponse
from apps.content.quality.html_preprocessor import HTMLPreprocessor
from .content_block_builder import ContentBlockBuilder
from .extraction_templates import get_extraction_template
from .models import ContentBlock, ProcessingResult, serialize_content_blocks


logger = logging.getLogger(__name__)


class AIRateLimiter:
    """
    Thread-safe rate limiter for AI API calls to prevent hitting rate limits.
    
    Uses a simple token bucket approach with configurable rate and burst capacity.
    """
    
    def __init__(self, calls_per_minute: int = 20, burst_capacity: int = 5):
        """
        Initialize rate limiter.
        
        Args:
            calls_per_minute: Maximum calls allowed per minute
            burst_capacity: Maximum burst calls allowed
        """
        self.calls_per_minute = calls_per_minute
        self.burst_capacity = burst_capacity
        self.tokens = burst_capacity
        self.last_refill = time.time()
        self.lock = threading.Lock()
        
        # Calculate refill rate (tokens per second)
        self.refill_rate = calls_per_minute / 60.0
        
        logger.info(f"AI Rate limiter initialized: {calls_per_minute} calls/min, burst: {burst_capacity}")
    
    def acquire(self, timeout: float = 30.0) -> bool:
        """
        Acquire a token for making an AI call.
        
        Args:
            timeout: Maximum time to wait for a token (seconds)
            
        Returns:
            True if token acquired, False if timeout
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            with self.lock:
                # Refill tokens based on time elapsed
                now = time.time()
                time_elapsed = now - self.last_refill
                tokens_to_add = time_elapsed * self.refill_rate
                
                self.tokens = min(self.burst_capacity, self.tokens + tokens_to_add)
                self.last_refill = now
                
                # Check if we have tokens available
                if self.tokens >= 1.0:
                    self.tokens -= 1.0
                    return True
            
            # Wait a bit before trying again
            time.sleep(0.1)
        
        logger.warning(f"Rate limiter timeout after {timeout}s")
        return False
    
    def wait_if_needed(self) -> None:
        """
        Wait if rate limiting is needed. Blocks until a token is available.
        """
        if not self.acquire(timeout=60.0):  # Wait up to 1 minute
            logger.error("Rate limiter failed to acquire token within 60 seconds")
            # Continue anyway to avoid blocking the pipeline completely
            
    def get_status(self) -> Dict[str, Any]:
        """Get current rate limiter status."""
        with self.lock:
            return {
                'tokens_available': self.tokens,
                'calls_per_minute': self.calls_per_minute,
                'burst_capacity': self.burst_capacity,
                'last_refill': self.last_refill
            }


# Global rate limiter instance
_rate_limiter = None
_rate_limiter_lock = threading.Lock()


def get_rate_limiter() -> AIRateLimiter:
    """Get or create the global rate limiter instance."""
    global _rate_limiter
    
    if _rate_limiter is None:
        with _rate_limiter_lock:
            if _rate_limiter is None:
                # Get rate limiting settings from Django settings or use defaults
                calls_per_minute = getattr(settings, 'AI_RATE_LIMIT_CALLS_PER_MINUTE', 20)
                burst_capacity = getattr(settings, 'AI_RATE_LIMIT_BURST_CAPACITY', 5)
                _rate_limiter = AIRateLimiter(calls_per_minute, burst_capacity)
    
    return _rate_limiter


@dataclass
class ExtractionMetadata:
    """Metadata about the AI extraction process."""
    total_blocks: int
    estimated_word_count: int
    has_headings: bool
    has_paragraphs: bool
    has_images: bool
    has_lists: bool
    has_embeds: bool
    processing_time_ms: int
    token_usage: int
    cost_estimate: float
    template_used: str
    template_version: str


class AIContentProcessor:
    """
    AI-powered content processor following proven quality evaluation patterns.
    
    Uses aiproviders service for AI infrastructure and quality service patterns
    for HTML preprocessing and response handling. Maintains the same reliability
    and parsing success rate as the quality evaluation system.
    
    Responsibilities:
    - Content extraction orchestration
    - HTML preprocessing for optimal AI processing  
    - Response parsing and validation
    - Content block generation and validation
    - Error handling and fallback strategies
    """
    
    def __init__(self, template_id: Optional[str] = None):
        """
        Initialize AI processor with dependencies following quality evaluation patterns.
        
        Args:
            template_id: Template identifier to use, or None for default template
        """
        self.ai_service = get_ai_service()  # Same AI service dependency as quality
        self.template = get_extraction_template(template_id)  # Template management
        self.html_preprocessor = HTMLPreprocessor()  # Reuse proven preprocessing  
        self.block_builder = ContentBlockBuilder()  # Convert JSON → ContentBlock
        self.template_id = template_id or "content_extraction_v2"
        self.rate_limiter = get_rate_limiter()  # Rate limiting for AI calls
    
    def process_content(
        self, 
        raw_html: str, 
        article_metadata: Dict[str, Any],
        base_url: Optional[str] = None,
        model_override: Optional[str] = None,
        use_html_preprocessing: bool = True,
        capture_raw_response: bool = False
    ) -> ProcessingResult:
        """
        Main AI extraction pipeline following quality evaluation success patterns.
        
        Args:
            raw_html: Raw HTML content from article
            article_metadata: Article metadata (title, url, source, etc.)
            base_url: Base URL for resolving relative URLs in content
            model_override: Override the configured model
            use_html_preprocessing: Whether to use intelligent HTML preprocessing
            capture_raw_response: Whether to capture and return the raw AI response
            
        Returns:
            ProcessingResult with extracted content blocks and metadata
        """
        start_time = time.time()
        
        try:
            # Extract base_url from article_metadata if not provided
            if base_url is None and article_metadata:
                base_url = article_metadata.get('url')
            
            # 1. Preprocess HTML using proven patterns from quality evaluation
            preprocessed_data = self._prepare_html_for_extraction(
                raw_html,
                use_preprocessing=use_html_preprocessing,
                max_tokens=75000,  # Optimal for content extraction
                base_url=base_url  # Now properly passed for URL resolution
            )
            
            if not preprocessed_data["html_sample"]:
                return self._create_fallback_result(
                    "HTML preprocessing failed or no content found",
                    time.time() - start_time
                )
            
            # 2. Generate extraction prompt using template
            prompt = self.template.format(
                preprocessed_html=preprocessed_data["html_sample"],
                article_metadata=article_metadata
            )
            
            # 3. Apply rate limiting before AI call
            logger.info(f"Applying rate limiting before AI call...")
            rate_limit_start = time.time()
            self.rate_limiter.wait_if_needed()
            rate_limit_time = time.time() - rate_limit_start
            
            if rate_limit_time > 0.1:  # Log if we had to wait
                logger.info(f"Rate limiting applied: waited {rate_limit_time:.2f}s")
            
            # 4. Call AI service following quality evaluation patterns
            # Use generous token limit to avoid truncation - let the AI complete the response
            # Large articles can require 20k-30k+ output tokens for complete JSON responses
            llm_response = self.ai_service.call_llm(
                prompt=prompt,
                operation="content_extraction",
                max_tokens=None,  # Use high default (30k) for content extraction to avoid truncation
                temperature=0.1,  # Low temperature for consistent extraction
                model_override=model_override,
                response_format="json"
            )
            
            if not llm_response.success:
                logger.error(f"AI extraction failed: {llm_response.error_message}")
                return self._create_fallback_result(
                    f"AI extraction failed: {llm_response.error_message}",
                    time.time() - start_time
                )
            
            # 5. Parse and validate response using proven patterns
            result = self._create_extraction_result(
                llm_response, 
                time.time() - start_time,
                preprocessed_data,
                article_metadata
            )
            
            # 6. Add template and preprocessing metadata
            if hasattr(result, 'extracted_metadata'):
                result.extracted_metadata.update({
                    "template_used": self.template.identifier,
                    "template_version": self.template.version,
                    "html_preprocessing_summary": preprocessed_data.get("preprocessing_summary", ""),
                    "original_html_length": len(raw_html),
                    "preprocessed_html_length": preprocessed_data["html_length"]
                })
            
            logger.info(f"AI extraction completed successfully. "
                       f"Blocks: {len(result.content_blocks)}, "
                       f"Processing time: {result.processing_time_ms}ms, "
                       f"Tokens: {llm_response.usage.get('total_tokens', 0)}")
            
            if capture_raw_response:
                result.raw_response = llm_response.content
            
            return result
            
        except Exception as e:
            logger.error(f"AI content processing error: {e}")
            return self._create_fallback_result(str(e), time.time() - start_time)
    
    def _prepare_html_for_extraction(
        self, 
        raw_html: str,
        use_preprocessing: bool = True, 
        max_tokens: int = 75000,
        base_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Prepare HTML for AI extraction using proven preprocessing patterns.
        
        Reuses the same preprocessing logic that achieved 100% success in quality
        evaluation, optimized for content extraction tasks.
        
        Args:
            raw_html: Raw HTML content
            use_preprocessing: Whether to use intelligent preprocessing
            max_tokens: Maximum tokens in preprocessed HTML
            
        Returns:
            Dictionary with preprocessed HTML and metadata
        """
        if not use_preprocessing:
            # Basic fallback without preprocessing
            return {
                "html_sample": raw_html[:max_tokens * 4],  # Rough token estimate
                "html_length": len(raw_html),
                "preprocessing_summary": "No preprocessing used"
            }
        
        try:
            # Use proven HTML preprocessing from quality evaluation
            preprocessed = self.html_preprocessor.preprocess_for_evaluation(
                raw_html,
                max_tokens=max_tokens,
                preserve_html_structure=True,  # Critical for content extraction
                base_url=base_url  # Convert relative URLs to absolute
            )
            
            return {
                "html_sample": preprocessed.cleaned_html,
                "html_length": len(preprocessed.cleaned_html),
                "preprocessing_summary": self.html_preprocessor.get_preprocessing_summary(preprocessed),
                "tokens_saved": getattr(preprocessed, 'tokens_saved', 0),
                "compression_ratio": preprocessed.compression_ratio
            }
            
        except Exception as e:
            logger.error(f"HTML preprocessing failed: {e}")
            # Fallback to basic truncation
            truncated_html = raw_html[:max_tokens * 4]
            return {
                "html_sample": truncated_html,
                "html_length": len(truncated_html),
                "preprocessing_summary": f"Preprocessing failed: {e}, used truncation"
            }
    
    def _create_extraction_result(
        self,
        llm_response: LLMResponse,
        processing_time: float,
        preprocessed_data: Dict[str, Any],
        article_metadata: Optional[Dict[str, Any]] = None
    ) -> ProcessingResult:
        """
        Create extraction result from LLM response following quality evaluation patterns.
        
        Uses the same JSON parsing and validation patterns that achieved 100%
        parsing success in the quality evaluation system.
        
        Args:
            llm_response: Response from AI service
            processing_time: Total processing time in seconds
            preprocessed_data: HTML preprocessing metadata
            
        Returns:
            ProcessingResult with structured content blocks
        """
        try:
            # Parse JSON response with same error handling as quality evaluation
            response_content = llm_response.content.strip()
            
            # Remove common JSON formatting issues
            if response_content.startswith("```json"):
                response_content = response_content[7:]
            if response_content.endswith("```"):
                response_content = response_content[:-3]
            
            # Enhanced JSON parsing with truncation recovery
            try:
                response_data = json.loads(response_content)
            except json.JSONDecodeError as json_error:
                logger.error(f"JSON parsing failed: {json_error}")
                
                # Attempt to recover from truncation by finding the last complete JSON structure
                if "Unterminated string" in str(json_error) or "Expecting" in str(json_error):
                    logger.warning("Attempting to recover from truncated JSON response")
                    
                    # Try to find the last complete content block
                    lines = response_content.split('\n')
                    for i in range(len(lines) - 1, 0, -1):
                        test_content = '\n'.join(lines[:i])
                        
                        # Try to complete the JSON by adding closing braces
                        for attempt in [test_content, test_content + '}', test_content + '}}', test_content + '}}}']:
                            try:
                                response_data = json.loads(attempt)
                                logger.info(f"JSON recovery successful at line {i}")
                                break
                            except:
                                continue
                        else:
                            continue
                        break
                    else:
                        # If recovery fails, return fallback
                        return self._create_fallback_result(
                            f"JSON parsing failed: {json_error}",
                            processing_time
                        )
                else:
                    # For other JSON errors, fail immediately
                    return self._create_fallback_result(
                        f"JSON parsing failed: {json_error}",
                        processing_time
                    )
            
            # Validate response structure using proven patterns
            if not self._validate_extraction_response(response_data):
                return self._create_fallback_result(
                    "Invalid response structure from AI",
                    processing_time
                )
            
            # Convert AI response to ContentBlock objects
            content_blocks = self.block_builder.build_blocks(
                response_data.get("content_blocks", []),
                article_metadata
            )
            
            # Analyze heading hierarchy for quality assessment
            hierarchy_analysis = self.block_builder.analyze_heading_hierarchy(content_blocks)
            
            # Generate clean text content from blocks
            clean_content = self._blocks_to_text(content_blocks)
            
            # Extract and validate metadata
            extraction_metadata = response_data.get("extraction_metadata", {})
            author_information = response_data.get("author_information", {})
            extraction_feedback = response_data.get("extraction_feedback", {})
            
            # Enhanced: Extract visual title from AI response
            # Check if AI provided an extracted/visual title
            extracted_title = None
            if "extraction_metadata" in response_data and response_data["extraction_metadata"]:
                extracted_title = response_data["extraction_metadata"].get("extracted_title")
            
            # If no extracted title in metadata, check if AI provided title in article_metadata
            if not extracted_title and article_metadata:
                extracted_title = article_metadata.get("extracted_title")
            
            # If we have an extracted title, use it as visual_title (clean title without publication)
            if extracted_title:
                extraction_metadata["visual_title"] = extracted_title
                logger.info(f"Set visual_title from extracted title: '{extracted_title}'")
            
            # Author information is optional but should be validated if present
            if "author_information" in response_data:
                author_info = response_data["author_information"]
                if not isinstance(author_info, dict):
                    logger.warning("'author_information' is not a dictionary")
                else:
                    # Validate primary author structure if present
                    if "primary_author" in author_info:
                        primary = author_info["primary_author"]
                        if not isinstance(primary, dict):
                            logger.warning("'primary_author' is not a dictionary")
                        elif not primary.get("name") and not primary.get("display_name"):
                            logger.warning("Primary author missing both name and display_name")
            
            # Extraction feedback is optional but useful for system improvement
            if "extraction_feedback" in response_data:
                feedback = response_data["extraction_feedback"]
                if not isinstance(feedback, dict):
                    logger.warning("'extraction_feedback' is not a dictionary")
                else:
                    # Log feedback for system improvement
                    if feedback.get("unmapped_content"):
                        logger.info(f"AI reported {len(feedback['unmapped_content'])} unmapped content types")
                    if feedback.get("improvement_suggestions"):
                        logger.info(f"AI provided {len(feedback['improvement_suggestions'])} improvement suggestions")
                    
                    # Log content completeness assessment
                    if feedback.get("content_completeness"):
                        completeness = feedback["content_completeness"]
                        is_complete = completeness.get("is_complete")
                        percentage = completeness.get("estimated_completeness_percentage", 0)
                        if is_complete is False:
                            logger.warning(f"AI detected incomplete content: {percentage}% complete")
                            if completeness.get("truncation_indicators"):
                                indicators = ", ".join(completeness["truncation_indicators"][:3])
                                logger.warning(f"Truncation indicators: {indicators}")
                        else:
                            logger.info(f"AI assessed content as complete ({percentage}% complete)")
            
            # Create processing result following existing patterns
            result = ProcessingResult(
                success=True,
                clean_content=clean_content,
                content_blocks=content_blocks,
                extracted_metadata={
                    "ai_extraction": True,
                    "total_blocks": len(content_blocks),
                    "estimated_word_count": extraction_metadata.get("estimated_word_count", 0),
                    "content_types": self._analyze_content_types(content_blocks),
                    "heading_hierarchy": hierarchy_analysis,
                    "author_information": author_information,
                    "extraction_feedback": extraction_feedback,
                    "processing_time_ms": int(processing_time * 1000),
                    "token_usage": llm_response.usage.get("total_tokens", 0),
                    "estimated_cost_usd": llm_response.usage.get("estimated_cost", llm_response.usage.get("total_cost", 0.0)),
                    "provider": llm_response.provider,
                    "model": llm_response.model,
                    **extraction_metadata
                },
                quality_score=self._estimate_extraction_quality(content_blocks, clean_content),
                processing_time_ms=int(processing_time * 1000),
                route_used="llm_enhanced"
            )
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {e}")
            return self._create_fallback_result(
                f"JSON parsing failed: {e}",
                processing_time
            )
        except Exception as e:
            logger.error(f"Error creating extraction result: {e}")
            return self._create_fallback_result(
                f"Error creating extraction result: {e}",
                processing_time
            )
    
    def _validate_extraction_response(self, response_data: Dict[str, Any]) -> bool:
        """
        Validate extraction response structure using quality evaluation patterns.
        
        Uses the same validation logic that achieved 100% parsing success
        in the quality evaluation system.
        
        Args:
            response_data: Parsed JSON response from AI
            
        Returns:
            True if response structure is valid, False otherwise
        """
        # Check required top-level structure
        if not isinstance(response_data, dict):
            logger.error("Response is not a dictionary")
            return False
        
        if "content_blocks" not in response_data:
            logger.error("Missing 'content_blocks' in response")
            return False
        
        # Author information is optional but should be validated if present
        if "author_information" in response_data:
            author_info = response_data["author_information"]
            if not isinstance(author_info, dict):
                logger.warning("'author_information' is not a dictionary")
            else:
                # Validate primary author structure if present
                if "primary_author" in author_info:
                    primary = author_info["primary_author"]
                    if not isinstance(primary, dict):
                        logger.warning("'primary_author' is not a dictionary")
                    elif not primary.get("name") and not primary.get("display_name"):
                        logger.warning("Primary author missing both name and display_name")
        
        # Extraction feedback is optional but useful for system improvement
        if "extraction_feedback" in response_data:
            feedback = response_data["extraction_feedback"]
            if not isinstance(feedback, dict):
                logger.warning("'extraction_feedback' is not a dictionary")
            else:
                # Log feedback for system improvement
                if feedback.get("unmapped_content"):
                    logger.info(f"AI reported {len(feedback['unmapped_content'])} unmapped content types")
                if feedback.get("improvement_suggestions"):
                    logger.info(f"AI provided {len(feedback['improvement_suggestions'])} improvement suggestions")
        
        # Validate content blocks structure
        blocks = response_data["content_blocks"]
        if not isinstance(blocks, list):
            logger.error("'content_blocks' is not a list")
            return False
        
        # Validate and filter blocks structure with graceful error handling
        valid_types = {
            "heading", "subtitle", "paragraph", "image", "figure", "quote", "list", 
            "twitter_embed", "video_embed", "editorial_note", "iframe", "embed",
            "table", "code", "divider", "raw_html"
        }
        
        valid_blocks = []
        invalid_blocks = []
        
        for i, block in enumerate(blocks):
            if not isinstance(block, dict):
                logger.warning(f"Block {i} is not a dictionary, skipping")
                invalid_blocks.append(f"Block {i}: not a dictionary")
                continue
            
            # Required fields
            if "type" not in block:
                logger.warning(f"Block {i} missing 'type' field, skipping")
                invalid_blocks.append(f"Block {i}: missing 'type' field")
                continue
            
            if "position" not in block:
                logger.warning(f"Block {i} missing 'position' field, skipping")
                invalid_blocks.append(f"Block {i}: missing 'position' field")
                continue
            
            # Handle unknown content block types gracefully
            if block["type"] not in valid_types:
                logger.warning(f"Block {i} has unknown type: {block['type']}, skipping")
                invalid_blocks.append(f"Block {i}: unknown type '{block['type']}'")
                continue
            
            # Type-specific validation
            if not self._validate_content_block_type(block):
                logger.warning(f"Block {i} failed type-specific validation, skipping")
                invalid_blocks.append(f"Block {i}: failed type-specific validation")
                continue
            
            # Block is valid, add to valid list
            valid_blocks.append(block)
        
        # Update response data with only valid blocks
        response_data["content_blocks"] = valid_blocks
        
        # Log summary of validation results
        if invalid_blocks:
            logger.warning(f"Filtered out {len(invalid_blocks)} invalid blocks: {invalid_blocks}")
        
        if valid_blocks:
            logger.info(f"Successfully validated {len(valid_blocks)} content blocks")
            return True
        else:
            logger.error("No valid content blocks found after validation")
            return False
    
    def _validate_content_block_type(self, block: Dict[str, Any]) -> bool:
        """
        Validate content block based on its type.
        
        Args:
            block: Content block dictionary
            
        Returns:
            True if block is valid for its type, False otherwise
        """
        block_type = block["type"]
        
        if block_type == "heading":
            # Headings should have level and content
            return (
                isinstance(block.get("level"), int) and
                1 <= block.get("level", 0) <= 6 and
                isinstance(block.get("content"), str) and
                len(block.get("content", "")) > 0
            )
        
        elif block_type == "subtitle":
            # Subtitles should have content
            return (
                isinstance(block.get("content"), str) and
                len(block.get("content", "")) > 0
            )
        
        elif block_type == "paragraph":
            # Paragraphs should have content
            return (
                isinstance(block.get("content"), str) and
                len(block.get("content", "")) > 0
            )
        
        elif block_type == "image":
            # Images should have metadata with src
            metadata = block.get("metadata", {})
            return (
                isinstance(metadata, dict) and
                "src" in metadata and
                isinstance(metadata["src"], str) and
                len(metadata["src"]) > 0
            )
        
        elif block_type == "list":
            # Lists should have metadata with items and list_type
            metadata = block.get("metadata", {})
            return (
                isinstance(metadata, dict) and
                "items" in metadata and
                isinstance(metadata["items"], list) and
                len(metadata["items"]) > 0 and
                "list_type" in metadata and
                metadata["list_type"] in ["ul", "ol"]
            )
        
        elif block_type == "quote":
            # Quotes should have content
            return (
                isinstance(block.get("content"), str) and
                len(block.get("content", "")) > 0
            )
        
        elif block_type == "twitter_embed":
            # Twitter embeds should have metadata with tweet_id
            metadata = block.get("metadata", {})
            return (
                isinstance(metadata, dict) and
                "tweet_id" in metadata and
                isinstance(metadata["tweet_id"], str) and
                len(metadata["tweet_id"]) > 0
            )
        
        elif block_type == "video_embed":
            # Video embeds should have metadata with src
            metadata = block.get("metadata", {})
            return (
                isinstance(metadata, dict) and
                "src" in metadata and
                isinstance(metadata["src"], str) and
                len(metadata["src"]) > 0
            )
        
        elif block_type == "editorial_note":
            # Editorial notes should have content
            return (
                isinstance(block.get("content"), str) and
                len(block.get("content", "")) > 0
            )
        
        elif block_type == "iframe":
            # Iframes should have metadata with src
            metadata = block.get("metadata", {})
            return (
                isinstance(metadata, dict) and
                "src" in metadata and
                isinstance(metadata["src"], str) and
                len(metadata["src"]) > 0
            )
        
        elif block_type == "embed":
            # Generic embeds should have metadata with src or embed_code
            metadata = block.get("metadata", {})
            return (
                isinstance(metadata, dict) and
                ("src" in metadata or "embed_code" in metadata)
            )
        
        elif block_type == "table":
            # Tables should have metadata with rows or content
            metadata = block.get("metadata", {})
            return (
                isinstance(metadata, dict) and
                ("rows" in metadata or block.get("content"))
            )
        
        elif block_type == "code":
            # Code blocks should have content
            return (
                isinstance(block.get("content"), str) and
                len(block.get("content", "")) > 0
            )
        

        
        elif block_type == "divider":
            # Dividers don't need specific validation
            return True
        
        elif block_type == "raw_html":
            # Raw HTML should have content
            return (
                isinstance(block.get("content"), str) and
                len(block.get("content", "")) > 0
            )
        
        return True  # Allow unknown types to pass validation for forward compatibility
    
    def _blocks_to_text(self, content_blocks: List[ContentBlock]) -> str:
        """
        Convert content blocks to clean text following existing patterns.
        
        Args:
            content_blocks: List of ContentBlock objects
            
        Returns:
            Clean text representation of the content
        """
        text_parts = []
        
        for block in content_blocks:
            if block.type == "heading":
                # Add heading with proper spacing
                heading_text = f"\n{'#' * block.level} {block.content}\n"
                text_parts.append(heading_text)
            
            elif block.type == "paragraph":
                # Add paragraph with spacing
                text_parts.append(f"\n{block.content}\n")
            
            elif block.type == "quote":
                # Add blockquote formatting
                text_parts.append(f"\n> {block.content}\n")
            
            elif block.type == "list":
                # Add list items
                items = block.metadata.get("items", [])
                list_type = block.metadata.get("list_type", "ul")
                
                list_text = "\n"
                for i, item in enumerate(items):
                    if list_type == "ol":
                        list_text += f"{i + 1}. {item}\n"
                    else:
                        list_text += f"• {item}\n"
                list_text += "\n"
                text_parts.append(list_text)
            
            elif block.type == "image":
                # Add image description
                caption = block.metadata.get("caption", block.content)
                if caption:
                    text_parts.append(f"\n[Image: {caption}]\n")
            
            elif block.type == "video_embed":
                # Add video description
                embed_type = block.metadata.get("embed_type", "video")
                video_title = block.content or f"{embed_type.title()} video"
                text_parts.append(f"\n[{embed_type.title()} Video: {video_title}]\n")
            
            elif block.type == "editorial_note":
                # Add editorial note with special formatting
                note_type = block.metadata.get("note_type", "note")
                text_parts.append(f"\n[{note_type.title()}: {block.content}]\n")
            
            elif block.type == "twitter_embed":
                # Add tweet reference
                if block.content:
                    text_parts.append(f"\n[Tweet: {block.content}]\n")
        
        return "".join(text_parts).strip()
    
    def _analyze_content_types(self, content_blocks: List[ContentBlock]) -> Dict[str, int]:
        """
        Analyze content block types for metadata.
        
        Args:
            content_blocks: List of ContentBlock objects
            
        Returns:
            Dictionary with count of each content type
        """
        type_counts = {}
        for block in content_blocks:
            type_counts[block.type] = type_counts.get(block.type, 0) + 1
        return type_counts
    
    def _estimate_extraction_quality(
        self, 
        content_blocks: List[ContentBlock], 
        clean_content: str
    ) -> float:
        """
        Estimate extraction quality based on content analysis.
        
        Provides a preliminary quality score before full quality evaluation.
        
        Args:
            content_blocks: Extracted content blocks
            clean_content: Clean text content
            
        Returns:
            Quality score between 0.0 and 1.0
        """
        if not content_blocks:
            return 0.0
        
        score = 0.0
        max_score = 5.0
        
        # Factor 1: Has diverse content types (0-1 points)
        content_types = set(block.type for block in content_blocks)
        type_diversity = min(len(content_types) / 4.0, 1.0)  # Up to 4 types is good
        score += type_diversity
        
        # Factor 2: Has sufficient content length (0-1 points)
        word_count = len(clean_content.split())
        length_score = min(word_count / 500.0, 1.0)  # 500+ words is good
        score += length_score
        
        # Factor 3: Has structured content (0-1 points)
        has_headings = any(block.type == "heading" for block in content_blocks)
        has_paragraphs = any(block.type == "paragraph" for block in content_blocks)
        structure_score = 0.5 * has_headings + 0.5 * has_paragraphs
        score += structure_score
        
        # Factor 4: Content block count (0-1 points)
        block_count_score = min(len(content_blocks) / 20.0, 1.0)  # 20+ blocks is good
        score += block_count_score
        
        # Factor 5: Rich content presence (0-1 points)
        has_images = any(block.type == "image" for block in content_blocks)
        has_quotes = any(block.type == "quote" for block in content_blocks)
        has_lists = any(block.type == "list" for block in content_blocks)
        rich_content_score = 0.4 * has_images + 0.3 * has_quotes + 0.3 * has_lists
        score += rich_content_score
        
        return min(score / max_score, 1.0)
    
    def _create_fallback_result(self, error_message: str, processing_time: float) -> ProcessingResult:
        """
        Create fallback result for error cases following quality evaluation patterns.
        
        Args:
            error_message: Error description
            processing_time: Processing time in seconds
            
        Returns:
            ProcessingResult indicating failure
        """
        return ProcessingResult(
            success=False,
            clean_content="",
            content_blocks=[],
            extracted_metadata={
                "ai_extraction": True,
                "error": error_message,
                "processing_time_ms": int(processing_time * 1000),
                "template_used": self.template.identifier if self.template else "unknown",
            },
            quality_score=0.0,
            processing_time_ms=int(processing_time * 1000),
            error_message=error_message,
            route_used="llm_fail"
        )


def get_ai_processor(template_id: Optional[str] = None) -> AIContentProcessor:
    """
    Factory function to get AI processor instance following quality evaluation patterns.
    
    Args:
        template_id: Template identifier to use
        
    Returns:
        AIContentProcessor instance
    """
    return AIContentProcessor(template_id=template_id) 
