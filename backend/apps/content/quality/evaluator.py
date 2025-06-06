"""
Content Quality Evaluator - Content Domain Logic.

This module contains all the business logic for content quality assessment.
It uses @aiproviders as a service dependency for AI capabilities, but all
content-specific logic, prompts, and scoring remains in this domain.

Clear separation: 
- AI infrastructure: @aiproviders  
- Content domain logic: @content/quality
"""
import json
import time
import logging
from typing import Dict, List, Optional, Any
from decimal import Decimal

from apps.articles.models import Article
from apps.aiproviders.services import get_ai_service, LLMResponse
from .models import QualityAssessmentResult, QualityScoring, ReferenceQualityExample
from .prompt_templates import get_template, BasePromptTemplate, get_few_shot_template
from .html_preprocessor import HTMLPreprocessor, PreprocessedHTML


logger = logging.getLogger(__name__)


class ContentQualityEvaluator:
    """
    Content quality evaluator - contains domain-specific logic for assessment.
    
    This class focuses on content quality business logic:
    - Content analysis and preparation
    - Prompt template management and versioning
    - Domain-specific prompt engineering  
    - Quality scoring and interpretation
    - Content-specific evaluation criteria
    
    Uses @aiproviders service for AI infrastructure without embedding AI logic.
    """
    
    def __init__(self, template_id: Optional[str] = None):
        """
        Initialize the evaluator with AI service dependency and optional prompt template.
        
        Args:
            template_id: Template identifier to use, or None for active template
        """
        self.ai_service = get_ai_service()
        self.template = get_template(template_id)
        self.template_id = template_id or "active"
        self.html_preprocessor = HTMLPreprocessor()  # New: HTML optimization
    
    def evaluate_article_quality(
        self,
        article: Article,
        include_html: bool = True,
        model_override: Optional[str] = None,
        use_html_preprocessing: bool = True  # New: Control preprocessing
    ) -> QualityAssessmentResult:
        """
        Evaluate the quality of content extraction for an article.
        
        Contains all content-specific business logic for quality assessment.
        
        Args:
            article: Article instance to evaluate
            include_html: Whether to include HTML sample in evaluation
            model_override: Override the configured model
            use_html_preprocessing: Whether to use intelligent HTML preprocessing
            
        Returns:
            QualityAssessmentResult with comprehensive quality metrics
        """
        start_time = time.time()
        
        try:
            # Prepare content for evaluation (domain logic)
            extracted_content = self._prepare_extracted_content(article)
            
            # Prepare HTML sample with optional preprocessing (NEW)
            html_data = self._prepare_html_sample(
                article, 
                include_html=include_html,
                use_preprocessing=use_html_preprocessing
            )
            
            # Prepare reference examples for few-shot learning (NEW)
            reference_examples = self._prepare_reference_examples(max_per_class=1)
            
            # Generate evaluation prompt using template (domain logic)
            prompt = self.template.format(
                title=extracted_content["title"],
                author=extracted_content["author"],
                description=extracted_content["description"],
                blocks_count=extracted_content["blocks_count"],
                blocks_sample=extracted_content["blocks_sample"],
                metadata=extracted_content["metadata"],
                html_length=html_data["html_length"],
                html_sample=html_data["html_sample"],
                reference_examples=reference_examples
            )
            
            # Call AI service for evaluation (infrastructure dependency)
            llm_response = self.ai_service.call_llm(
                prompt=prompt,
                operation="quality_assessment",
                max_tokens=800,
                temperature=0.2,  # Low temperature for consistent evaluation
                model_override=model_override,
                response_format="json"
            )
            
            if not llm_response.success:
                logger.error(f"AI evaluation failed: {llm_response.error_message}")
                return self._create_fallback_result(
                    f"AI evaluation failed: {llm_response.error_message}",
                    time.time() - start_time
                )
            
            # Parse and create quality result (domain logic)
            result = self._create_quality_result(llm_response, time.time() - start_time)
            
            # Add template metadata to result
            result.template_used = self.template.identifier
            result.template_version = self.template.metadata.version
            
            # Add HTML preprocessing metadata (NEW)
            if html_data.get("preprocessing_summary"):
                logger.info(f"HTML preprocessing: {html_data['preprocessing_summary']}")
            
            return result
            
        except Exception as e:
            logger.error(f"Quality evaluation error for article {article.public_id}: {e}")
            return self._create_fallback_result(str(e), time.time() - start_time)
    
    def _prepare_extracted_content(self, article: Article) -> Dict[str, Any]:
        """
        Prepare extracted content data for comprehensive quality evaluation.
        
        Focuses on structured content blocks which provide better analysis capabilities
        than raw text. Content blocks contain all the information needed for quality
        assessment in a structured format that's easier for LLMs to analyze.
        """
        # Process content blocks - provide ALL blocks for complete structure assessment
        blocks_info = "[]"
        blocks_count = 0
        if article.content_blocks:
            blocks_count = len(article.content_blocks)
            if blocks_count > 0:
                # Provide ALL content blocks for comprehensive assessment
                blocks_info = json.dumps(article.content_blocks, indent=2)
        
        # Prepare metadata - content domain knowledge
        metadata_info = {
            "word_count": article.word_count,
            "read_time": article.read_time_minutes,
            "fetch_status": article.fetch_status,
            "process_status": article.process_status,
            "has_images": article.has_images,
            "media_count": article.media_count,
            "paywall_detected": article.paywall_detected
        }
        
        return {
            "title": article.title or "No title",
            "author": article.author or "No author",
            "description": article.description or "No description",
            "blocks_count": blocks_count,
            "blocks_sample": blocks_info,  # All blocks for complete assessment
            "metadata": json.dumps(metadata_info, indent=2)
        }
    
    def _prepare_html_sample(
        self, 
        article: Article, 
        include_html: bool = True,
        use_preprocessing: bool = True,
        max_tokens: int = 50000  # Increased from 12000 for full content assessment
    ) -> Dict[str, Any]:
        """
        Prepare HTML sample for AI evaluation optimized for modern large context windows.
        
        With modern LLMs supporting 1M+ tokens (GPT-4.1-mini), 128K+ tokens (GPT-4o-mini), and 
        200K+ tokens (o3), we can provide much more comprehensive HTML for 
        quality assessment. This enables better detection of extraction issues 
        throughout the complete document structure.
        
        Args:
            article: Article with raw HTML
            include_html: Whether to include HTML in evaluation
            use_preprocessing: Whether to use intelligent preprocessing
            max_tokens: Maximum tokens in preprocessed HTML (50K for full coverage)
            
        Returns:
            Dictionary with html_sample, html_length, and preprocessing metadata
        """
        if not include_html:
            return {
                "html_sample": "",
                "html_length": 0,
                "preprocessing_summary": "HTML disabled for evaluation"
            }
        
        raw_html = article.raw_html or ""
        
        if not raw_html:
            return {
                "html_sample": "",
                "html_length": 0,
                "preprocessing_summary": "No HTML available"
            }
        
        if use_preprocessing:
            # NEW: Use "just enough" preprocessing
            preprocessed = self.html_preprocessor.preprocess_for_evaluation(
                raw_html, 
                max_tokens=max_tokens,
                preserve_html_structure=True,  # NEW: Preserve HTML for quality evaluation
                base_url=article.url  # NEW: Convert relative URLs to absolute
            )
            
            preprocessing_summary = self.html_preprocessor.get_preprocessing_summary(preprocessed)
            
            return {
                "html_sample": preprocessed.cleaned_html,
                "html_length": preprocessed.cleaned_size,
                "preprocessing_summary": preprocessing_summary,
                "original_html_size": preprocessed.original_size,
                "compression_ratio": preprocessed.compression_ratio,
                "removed_elements": preprocessed.removed_elements,
                "preserved_structure": preprocessed.preserved_structure,
                "processing_method": preprocessed.processing_method,
                "content_density_info": preprocessed.content_density_info
            }
        else:
            # Fallback: Simple truncation (original method)
            max_chars = max_tokens * 4  # Rough token estimation
            if len(raw_html) > max_chars:
                html_sample = raw_html[:max_chars] + "\n... [truncated] ..."
            else:
                html_sample = raw_html
            
            return {
                "html_sample": html_sample,
                "html_length": len(html_sample),
                "preprocessing_summary": "Simple truncation used (legacy method)"
            }
    
    def _prepare_reference_examples(self, max_per_class: int = 1) -> str:
        """
        Prepare reference examples for few-shot learning using the FewShotExampleTemplate.
        
        This method:
        1. Retrieves reference examples from the database (1 per class by default)
        2. Uses random selection when multiple examples are available for variety
        3. Uses the FewShotExampleTemplate to format each example consistently
        4. Concatenates the formatted examples with proper wrapper structure
        5. Returns a clean, structured few-shot learning section
        
        Args:
            max_per_class: Maximum number of examples per quality class (default: 1)
            
        Returns:
            Formatted reference examples using template-based approach
        """
        try:
            # Get the few-shot template for consistent formatting
            few_shot_template = get_few_shot_template()
            
            # Get diverse reference examples across all quality classes
            examples_by_class = {}
            quality_classes = ['perfect', 'good', 'imperfect', 'awful']
            
            for quality_class in quality_classes:
                examples = ReferenceQualityExample.objects.filter(
                    quality_class=quality_class,
                    use_in_prompts=True
                ).order_by('?')[:max_per_class]  # Random selection using order_by('?')
                
                if examples:
                    examples_by_class[quality_class] = list(examples)
            
            if not examples_by_class:
                return "<!-- No reference examples available -->"
            
            # Build the formatted examples using template-based approach
            formatted_examples = []
            example_counter = {}  # Track count per quality class for ID generation
            
            # Process examples by quality class to ensure good distribution
            for quality_class in quality_classes:
                if quality_class not in examples_by_class:
                    continue
                    
                examples = examples_by_class[quality_class]
                
                for example in examples:
                    quality_class_upper = quality_class.upper()
                    
                    # Generate unique ID for this quality class
                    if quality_class_upper not in example_counter:
                        example_counter[quality_class_upper] = 0
                    example_counter[quality_class_upper] += 1
                    example_id = f"{quality_class_upper}-{chr(64 + example_counter[quality_class_upper])}"  # A, B, C, etc.
                    
                    # Prepare data for the few-shot template
                    template_data = self._prepare_few_shot_template_data(example, example_id, quality_class)
                    
                    # Use the template to format this example
                    formatted_example = few_shot_template.format(**template_data)
                    formatted_examples.append(formatted_example)
            
            # Wrap the formatted examples with consistent structure
            reference_text = "<<<EXAMPLES>>>\n"
            reference_text += "\n".join(formatted_examples)
            reference_text += "\n<<<END EXAMPLES>>>\n"
            
            # Add summary comment
            total_examples = sum(len(examples) for examples in examples_by_class.values())
            quality_summary = []
            for quality_class, examples in examples_by_class.items():
                quality_summary.append(f"{len(examples)} {quality_class}")
            
            reference_text += f"<!-- Reference examples: {total_examples} total ({', '.join(quality_summary)}) -->"
            
            return reference_text
            
        except Exception as e:
            logger.warning(f"Failed to prepare reference examples: {e}")
            return f"<!-- Reference examples unavailable: {e} -->"
    
    def _prepare_few_shot_template_data(self, example: 'ReferenceQualityExample', example_id: str, quality_class: str) -> Dict[str, Any]:
        """
        Prepare data for the FewShotExampleTemplate.
        
        Extracts and formats all necessary data from a reference example
        for consistent template hydration. Focuses on structured content blocks.
        
        Args:
            example: ReferenceQualityExample instance
            example_id: Unique identifier for this example
            quality_class: Quality classification ('perfect', 'good', etc.)
            
        Returns:
            Dictionary with all template variables ready for formatting
        """
        # Use stored content blocks (structured data)
        stored_blocks = example.stored_content_blocks or []
        
        # Calculate content length from blocks for metadata
        total_content_length = 0
        if stored_blocks:
            for block in stored_blocks:
                content = block.get('content', '')
                if isinstance(content, str):
                    total_content_length += len(content)
        
        # Prepare metadata (same format as actual evaluation)
        metadata_info = {
            "word_count": total_content_length // 5,  # Rough word count estimate
            "content_length": total_content_length,
            "blocks_count": len(stored_blocks),
            "quality_class": quality_class,
            "reference_score": example.reference_overall_score
        }
        
        # NEW: Use fresh HTML preprocessing with structure preservation
        # instead of old stored HTML that uses plain text format
        html_sample = "No HTML available"
        html_length = 0
        
        if example.article.raw_html:
            try:
                # Use same preprocessing as current evaluation with HTML structure preservation
                preprocessed = self.html_preprocessor.preprocess_for_evaluation(
                    example.article.raw_html,
                    max_tokens=12000,  # Smaller for reference examples
                    preserve_html_structure=True,  # Use HTML structure preservation
                    base_url=example.article.url  # Convert relative URLs to absolute
                )
                html_sample = preprocessed.cleaned_html
                html_length = preprocessed.cleaned_size
            except Exception as e:
                logger.warning(f"Failed to preprocess HTML for reference example {example_id}: {e}")
                # Fallback to stored HTML if preprocessing fails
                html_sample = example.stored_preprocessed_html or "HTML preprocessing failed"
                html_length = len(html_sample)
        
        # Create unified JSON response example
        unified_json_example = {
            "template_version": "reference_example",
            "evaluation_timestamp": "reference",
            "scores": {
                "completeness": example.reference_completeness,
                "purity": example.reference_purity,
                "structure": example.reference_structure,
                "readability": example.reference_readability
            },
            "confidence": 0.95,  # High confidence for reference examples
            "assessment": {
                "explanation": example.reference_explanation,
                "missing_elements": example.reference_missing_elements[:3],  # Limit for brevity
                "noise_detected": example.reference_noise_detected[:3],
                "key_strengths": example.reference_key_strengths[:2],
                "improvement_areas": example.reference_improvement_areas[:2]
            },
            "metadata": {
                "assessment_method": "reference_curation",
                "evidence_clarity": "high",
                "pattern_consistency": "consistent"
            }
        }
        
        # Format JSON with proper indentation
        expected_json_output = json.dumps(unified_json_example, indent=2)
        
        # Return all template variables
        return {
            "example_id": example_id,
            "title": example.article.title,
            "author": example.article.author or "No author",
            "description": example.article.description or "No description",
            "content_blocks": json.dumps(stored_blocks, indent=2) if stored_blocks else "[]",
            "blocks_count": len(stored_blocks),
            "metadata": json.dumps(metadata_info, indent=2),
            "html_sample": html_sample,
            "html_length": html_length,
            "expected_json_output": expected_json_output
        }
    
    def _create_quality_result(
        self,
        llm_response: LLMResponse,
        evaluation_time: float
    ) -> QualityAssessmentResult:
        """
        Create QualityAssessmentResult from AI response.
        
        Content domain logic - knows how to interpret AI response for content quality.
        Supports unified JSON format with nested scores and assessment objects.
        """
        try:
            # Clean the response content - remove markdown code blocks
            content = llm_response.content.strip()
            if content.startswith("```json"):
                content = content[7:]  # Remove ```json
            if content.endswith("```"):
                content = content[:-3]  # Remove trailing ```
            content = content.strip()
            
            # Parse JSON response
            evaluation_data = json.loads(content)
            
            # Handle unified JSON format with nested structures
            if "scores" in evaluation_data and "assessment" in evaluation_data:
                # NEW UNIFIED FORMAT: Nested scores and assessment objects
                scores = evaluation_data["scores"]
                assessment = evaluation_data["assessment"]
                
                # Extract scores
                completeness = float(scores.get("completeness", 0.0))
                purity = float(scores.get("purity", 0.0))
                structure = float(scores.get("structure", 0.0))
                readability = float(scores.get("readability", 0.0))
                confidence = float(evaluation_data.get("confidence", 0.5))
                
                # Use provided overall score if available, otherwise calculate
                if "overall" in scores:
                    overall_score = float(scores["overall"])
                else:
                    overall_score = QualityScoring.calculate_overall_score(
                        completeness, purity, structure, readability
                    )
                
                # Extract assessment details
                explanation = assessment.get("explanation", "No explanation provided")
                missing_elements = assessment.get("missing_elements", [])
                noise_detected = assessment.get("noise_detected", [])
                
            elif "scores" in evaluation_data:
                # LEGACY STRUCTURED FORMAT: Nested scores only (for backward compatibility)
                scores = evaluation_data["scores"]
                completeness = float(scores.get("completeness", 0.0))
                purity = float(scores.get("purity", 0.0))
                structure = float(scores.get("structure", 0.0))
                readability = float(scores.get("readability", 0.0))
                confidence = float(evaluation_data.get("confidence", 0.5))
                
                # Use final score if provided by template, otherwise calculate
                if "final" in scores:
                    overall_score = float(scores["final"])
                elif "overall" in scores:
                    overall_score = float(scores["overall"])
                else:
                    overall_score = QualityScoring.calculate_overall_score(
                        completeness, purity, structure, readability
                    )
                
                # Extract explanation and details (flat structure)
                explanation = evaluation_data.get("explanation", "No explanation provided")
                missing_elements = evaluation_data.get("missing_elements", [])
                noise_detected = evaluation_data.get("noise_detected", [])
                
            else:
                # LEGACY FLAT FORMAT: Direct score fields (for backward compatibility)
                completeness = float(evaluation_data.get("completeness", 0.0))
                purity = float(evaluation_data.get("purity", 0.0))
                structure = float(evaluation_data.get("structure", 0.0))
                readability = float(evaluation_data.get("readability", 0.0))
                confidence = float(evaluation_data.get("confidence", 0.5))
                
                # Calculate overall score using domain-specific formula
                overall_score = QualityScoring.calculate_overall_score(
                    completeness, purity, structure, readability
                )
                
                # Extract explanation and details
                explanation = evaluation_data.get("explanation", "No explanation provided")
                missing_elements = evaluation_data.get("missing_elements", [])
                noise_detected = evaluation_data.get("noise_detected", [])
            
            # Calculate cost estimate from AI response
            total_tokens = llm_response.usage.get("total_tokens", 0)
            cost_usd = self._calculate_cost(llm_response.provider, llm_response.model, total_tokens)
            
            return QualityAssessmentResult(
                overall_score=overall_score,
                completeness=completeness,
                purity=purity,
                structure=structure,
                readability=readability,
                confidence=confidence,
                explanation=explanation,
                missing_elements=missing_elements,
                noise_detected=noise_detected,
                evaluation_time=evaluation_time,
                model_used=llm_response.model,
                tokens_used=total_tokens,
                cost_usd=cost_usd
            )
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error(f"Failed to parse AI evaluation response: {e}")
            logger.error(f"AI response content: {llm_response.content}")
            return self._create_fallback_result(f"Failed to parse AI response: {e}", evaluation_time)
    
    def _calculate_cost(self, provider: str, model: str, total_tokens: int) -> Decimal:
        """
        Calculate cost estimate for AI usage using official OpenAI pricing (as of April 2025).
        
        Content domain logic - knows content-specific cost considerations.
        """
        cost_usd = Decimal('0.0')
        if provider == "openai":
            model_lower = model.lower()
            
            # Estimate prompt/completion token split (rough approximation: 80% prompt, 20% completion)
            prompt_tokens_est = int(total_tokens * 0.8)
            completion_tokens_est = int(total_tokens * 0.2)
            
            if 'gpt-4.1' in model_lower:
                if 'nano' in model_lower:
                    # GPT-4.1 Nano: $0.10/1M input, $0.40/1M output
                    input_cost = Decimal(str(prompt_tokens_est)) * Decimal('0.0000001')  # $0.10/1M
                    output_cost = Decimal(str(completion_tokens_est)) * Decimal('0.0000004')  # $0.40/1M
                    cost_usd = input_cost + output_cost
                elif 'mini' in model_lower:
                    # GPT-4.1 Mini: $0.40/1M input, $1.60/1M output
                    input_cost = Decimal(str(prompt_tokens_est)) * Decimal('0.0000004')  # $0.40/1M
                    output_cost = Decimal(str(completion_tokens_est)) * Decimal('0.0000016')  # $1.60/1M
                    cost_usd = input_cost + output_cost
                else:
                    # GPT-4.1 (full): $2.00/1M input, $8.00/1M output
                    input_cost = Decimal(str(prompt_tokens_est)) * Decimal('0.000002')  # $2.00/1M
                    output_cost = Decimal(str(completion_tokens_est)) * Decimal('0.000008')  # $8.00/1M
                    cost_usd = input_cost + output_cost
            elif 'gpt-4o-mini' in model_lower:
                # GPT-4o-mini: $0.15/1M input, $0.075/1M output (older pricing)
                input_cost = Decimal(str(prompt_tokens_est)) * Decimal('0.00000015')  # $0.15/1M
                output_cost = Decimal(str(completion_tokens_est)) * Decimal('0.000000075')  # $0.075/1M
                cost_usd = input_cost + output_cost
                
        return cost_usd
    
    def _create_fallback_result(self, error_message: str, evaluation_time: float) -> QualityAssessmentResult:
        """
        Create a fallback quality result when evaluation fails.
        
        Content domain logic - knows appropriate fallback values for content quality.
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


# Convenience function for direct evaluation
def evaluate_article_quality(
    article: Article,
    include_html: bool = True,
    model_override: Optional[str] = None
) -> QualityAssessmentResult:
    """
    Evaluate article quality using the content quality evaluator.
    
    Args:
        article: Article instance to evaluate
        include_html: Whether to include HTML sample
        model_override: Override the configured model
        
    Returns:
        QualityAssessmentResult with quality metrics
    """
    evaluator = ContentQualityEvaluator()
    return evaluator.evaluate_article_quality(article, include_html, model_override) 