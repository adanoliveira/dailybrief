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
from .models import QualityAssessmentResult, QualityScoring


logger = logging.getLogger(__name__)


class ContentQualityEvaluator:
    """
    Content quality evaluator - contains domain-specific logic for assessment.
    
    This class focuses on content quality business logic:
    - Content analysis and preparation
    - Domain-specific prompt engineering  
    - Quality scoring and interpretation
    - Content-specific evaluation criteria
    
    Uses @aiproviders service for AI infrastructure without embedding AI logic.
    """
    
    # LLM Evaluation Prompt Template - Content Domain Specific
    EVALUATION_PROMPT_TEMPLATE = """You are an expert content quality evaluator for news articles. Assess the extraction quality on a scale where:
- +1 = Perfect extraction (complete content, no noise, perfect structure)
- 0 = No content extracted (but original had content)
- -1 = All noise, no actual content

EXTRACTED CONTENT:
Title: {title}
Author: {author}
Description: {description}
Content ({content_length} chars): {content_sample}
Content Blocks ({blocks_count} blocks): {blocks_sample}
Metadata: {metadata}

ORIGINAL HTML SAMPLE ({html_length} chars):
{html_sample}

EVALUATION CRITERIA:
1. COMPLETENESS (0-1): How much core article content was captured? (Core content is the main text of the article, excluding navigation, ads, recommended articles, comment sections, etc.)
   - Check title, author, main text, headlines, subheadlines, etc.
   - Assess completeness vs truncation
   - Verify narrative coherence and conclusion
   - Check for rich content blocks (images, quotes, twitter embeds, videos, carousels, etc.)
   - Check for proper content formatting (paragraphs, links, headings, lists, bold, italic, pull quotes, etc.)

    Scoring Completeness:
    - 1 = Perfect extraction: 100% of original core content extracted (text, rich content blocks, formattting, etc.)
    - 0 = No content extracted: 0% of original core content extracted (no content extracted)
    - between 0 and 1: Partial extraction: % of original core content extracted (text, rich content blocks, formattting, etc.), proportionally to the amount of core content extracted.

2. PURITY (0-1): How clean is the extracted content? (Purity is the ratio of core content to all content extracted). Here are content pieces that are considered impure/noisy and should NOT be in the extracted content:
   - Identify navigation, ads, recommended articles, comment sections, etc.
   - Headlines, subheadlines for non core content sections (Recommended, Related, Comments, etc.)
   - Check for HTML artifacts, social buttons, paywall indicators, etc.
   - Assess repetition and irrelevant text  
   - Newsletter and signup related content, etc.
   - By lines in text
   - Timestamps, dates, times, etc.
   - Categories, breadcrumbs, etc.

   Scoring Purity:
   - 1 = Perfect purity: 100% of content extracted is core content (text, rich content blocks, formattting, etc.).
   - 0 = No purity: 100% of content extracted is noise (navigation, ads, recommended articles, comment sections, etc.).
   - between 0 and 1: Partial purity: % of content extracted that is core content.

3. STRUCTURE (0-1): How well is content structure preserved?
   - Proper paragraph breaks and headings, proper spacing between paragraphs and headings
   - Order of content blocks (main text, rich content blocks, etc.)
   - Logical flow and organization
   - Rich content blocks (images, quotes, embeds, carousels, etc.) captured integrally and properly formatted

4. READABILITY (0-1): How readable is the extracted content?
   - Clear, coherent sentences
   - Proper formatting and spacing
   - Natural flow for human consumption

SCORING FORMULA:
base_score = completeness - (1 - purity)  # Range: -1 to +1
structure_bonus = (structure - 0.5) * 0.3  # ±0.15 adjustment
readability_bonus = (readability - 0.5) * 0.2  # ±0.10 adjustment
final_score = clamp(base_score + structure_bonus + readability_bonus, -1, 1)

RESPONSE FORMAT (JSON only):
{{
    "completeness": 0.85,
    "purity": 0.92,
    "structure": 0.78,
    "readability": 0.88,
    "confidence": 0.90,
    "explanation": "High-quality extraction with complete main content. Minor navigation elements detected but overall very clean. Well-structured with proper paragraphs. Highly readable format.",
    "missing_elements": ["author byline", "publication date"],
    "noise_detected": ["social sharing buttons", "related articles"],
    "key_strengths": ["complete main text", "clean formatting", "proper structure"],
    "improvement_areas": ["remove social elements", "capture metadata better"]
}}

Respond with JSON only, no other text."""
    
    def __init__(self):
        """Initialize the evaluator with AI service dependency."""
        self.ai_service = get_ai_service()
    
    def evaluate_article_quality(
        self,
        article: Article,
        include_html: bool = True,
        model_override: Optional[str] = None
    ) -> QualityAssessmentResult:
        """
        Evaluate the quality of content extraction for an article.
        
        Contains all content-specific business logic for quality assessment.
        
        Args:
            article: Article instance to evaluate
            include_html: Whether to include HTML sample in evaluation
            model_override: Override the configured model
            
        Returns:
            QualityAssessmentResult with comprehensive quality metrics
        """
        start_time = time.time()
        
        try:
            # Prepare content for evaluation (domain logic)
            extracted_content = self._prepare_extracted_content(article)
            html_sample = self._prepare_html_sample(article) if include_html else ""
            
            # Generate evaluation prompt (domain logic)
            prompt = self._generate_evaluation_prompt(extracted_content, html_sample)
            
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
            return self._create_quality_result(llm_response, time.time() - start_time)
            
        except Exception as e:
            logger.error(f"Quality evaluation error for article {article.public_id}: {e}")
            return self._create_fallback_result(str(e), time.time() - start_time)
    
    def _prepare_extracted_content(self, article: Article) -> Dict[str, Any]:
        """
        Prepare extracted content data for evaluation.
        
        Content domain logic - knows how to analyze article content structure.
        """
        # Get the best available content
        content = ""
        if article.clean_content:
            content = article.clean_content
        elif article.basic_content:
            content = article.basic_content
        elif article.content:
            content = article.content
        
        # Process content blocks
        blocks_info = "None"
        blocks_count = 0
        if article.content_blocks:
            blocks_count = len(article.content_blocks)
            if blocks_count > 0:
                # Sample first few blocks for evaluation
                sample_blocks = article.content_blocks[:3]
                blocks_info = json.dumps(sample_blocks, indent=2)
        
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
            "content": content,
            "content_length": len(content),
            "content_sample": content[:2000] + "..." if len(content) > 2000 else content,
            "blocks_count": blocks_count,
            "blocks_sample": blocks_info,
            "metadata": json.dumps(metadata_info, indent=2)
        }
    
    def _prepare_html_sample(self, article: Article, max_length: int = 8000) -> str:
        """
        Prepare HTML sample for AI evaluation.
        
        Content domain logic - knows how to sample HTML effectively.
        """
        html = article.raw_html or ""
        if len(html) > max_length:
            # Take a representative sample from the beginning
            html = html[:max_length] + "\n... [truncated] ..."
        
        return html
    
    def _generate_evaluation_prompt(
        self,
        extracted_content: Dict[str, Any],
        html_sample: str
    ) -> str:
        """
        Generate the evaluation prompt for the AI.
        
        Content domain logic - contains content-specific prompt engineering.
        """
        return self.EVALUATION_PROMPT_TEMPLATE.format(
            title=extracted_content["title"],
            author=extracted_content["author"],
            description=extracted_content["description"],
            content_length=extracted_content["content_length"],
            content_sample=extracted_content["content_sample"],
            blocks_count=extracted_content["blocks_count"],
            blocks_sample=extracted_content["blocks_sample"],
            metadata=extracted_content["metadata"],
            html_length=len(html_sample),
            html_sample=html_sample
        )
    
    def _create_quality_result(
        self,
        llm_response: LLMResponse,
        evaluation_time: float
    ) -> QualityAssessmentResult:
        """
        Create QualityAssessmentResult from AI response.
        
        Content domain logic - knows how to interpret AI response for content quality.
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
            
            # Extract core metrics
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
        Calculate cost estimate for AI usage.
        
        Content domain logic - knows content-specific cost considerations.
        """
        cost_usd = Decimal('0.0')
        if provider == "openai" and "gpt-4o-mini" in model.lower():
            # Rough cost calculation for GPT-4o-mini
            cost_usd = Decimal(str(total_tokens)) * Decimal('0.0000001')  # ~$0.0001/1K tokens average
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