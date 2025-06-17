"""
Smart Pre-Filter for Content Quality Assessment.

This module provides fast, traditional quality checks to avoid unnecessary LLM calls
for obvious cases, achieving 30%+ cost reduction while maintaining accuracy.

Uses simple heuristics to identify:
- Clear failures (empty content, extraction errors)
- Clear successes (long, clean content)
- Uncertain cases (need LLM evaluation)
"""
import logging
from dataclasses import dataclass
from typing import Optional, List, Dict
from decimal import Decimal

from apps.articles.models import Article


logger = logging.getLogger(__name__)


@dataclass
class PreFilterResult:
    """
    Result of pre-filter quality assessment.
    
    Used to determine if LLM evaluation is needed or if we can
    provide a quality score based on traditional heuristics alone.
    """
    score: Optional[float]          # Quality score if confident, None if uncertain
    confidence: float               # Confidence in assessment (0-1)
    reason: str                     # Explanation for the assessment
    should_use_llm: bool           # Whether LLM evaluation is recommended
    detected_issues: List[str]      # Issues found during pre-filtering


class SmartPreFilter:
    """
    Smart pre-filter for content quality assessment.
    
    Uses fast, traditional heuristics to identify obvious quality cases
    and avoid expensive LLM calls when possible.
    
    Cost optimization strategy:
    - High confidence cases (>85%): Return score directly
    - Low confidence cases: Recommend LLM evaluation
    """
    
    # Thresholds for quality assessment
    MIN_CONTENT_LENGTH = 100
    EXCELLENT_CONTENT_LENGTH = 3000
    MIN_TITLE_LENGTH = 10
    MAX_HTML_RATIO = 100           # HTML:content ratio threshold
    HIGH_CONFIDENCE_THRESHOLD = 0.85
    
    def quick_quality_assessment(self, article: Article) -> PreFilterResult:
        """
        Perform quick quality assessment using traditional heuristics.
        
        Args:
            article: Article instance to evaluate
            
        Returns:
            PreFilterResult with score (if confident) or LLM recommendation
        """
        try:
            # Get best available content
            content = self._get_best_content(article)
            content_length = len(content) if content else 0
            
            # Get HTML information
            html = article.raw_html or ""
            html_length = len(html)
            html_ratio = html_length / max(content_length, 1)
            
            detected_issues = []
            
            # Check for clear failure cases (high confidence)
            failure_result = self._check_failure_cases(
                article, content, content_length, html_ratio, detected_issues
            )
            if failure_result:
                return failure_result
            
            # Check for clear success cases (high confidence)
            success_result = self._check_success_cases(
                article, content, content_length, html_ratio, detected_issues
            )
            if success_result:
                return success_result
            
            # Uncertain case - recommend LLM evaluation
            return PreFilterResult(
                score=None,
                confidence=0.3,
                reason="uncertain_quality_needs_llm",
                should_use_llm=True,
                detected_issues=detected_issues
            )
            
        except Exception as e:
            logger.error(f"Pre-filter error for article {article.public_id}: {e}")
            return PreFilterResult(
                score=None,
                confidence=0.1,
                reason=f"pre_filter_error: {str(e)}",
                should_use_llm=True,
                detected_issues=["pre_filter_error"]
            )
    
    def _get_best_content(self, article: Article) -> str:
        """Get the best available content from article."""
        if article.clean_content:
            return article.clean_content
        elif article.basic_content:
            return article.basic_content
        elif article.content:
            return article.content
        return ""
    
    def _check_failure_cases(
        self, 
        article: Article, 
        content: str, 
        content_length: int, 
        html_ratio: float,
        detected_issues: List[str]
    ) -> Optional[PreFilterResult]:
        """
        Check for clear failure cases that indicate poor quality.
        
        Returns PreFilterResult if failure detected, None otherwise.
        """
        # Empty or very short content
        if content_length < self.MIN_CONTENT_LENGTH:
            detected_issues.append("insufficient_content")
            return PreFilterResult(
                score=-0.8,
                confidence=0.95,
                reason="empty_or_minimal_content",
                should_use_llm=False,
                detected_issues=detected_issues
            )
        
        # Extraction likely failed (way more HTML than content)
        if html_ratio > self.MAX_HTML_RATIO:
            detected_issues.append("extraction_failure")
            return PreFilterResult(
                score=-0.5,
                confidence=0.90,
                reason="extraction_failed_html_ratio_high",
                should_use_llm=False,
                detected_issues=detected_issues
            )
        
        # Missing critical metadata
        if not article.title or len(article.title.strip()) < 5:
            detected_issues.append("missing_title")
            return PreFilterResult(
                score=-0.3,
                confidence=0.88,
                reason="missing_or_invalid_title",
                should_use_llm=False,
                detected_issues=detected_issues
            )
        
        # Known paywall indicators with no bypass
        if article.paywall_detected and content_length < 500:
            detected_issues.append("paywall_blocking")
            return PreFilterResult(
                score=-0.4,
                confidence=0.87,
                reason="paywall_detected_minimal_content",
                should_use_llm=False,
                detected_issues=detected_issues
            )
        
        return None
    
    def _check_success_cases(
        self, 
        article: Article, 
        content: str, 
        content_length: int, 
        html_ratio: float,
        detected_issues: List[str]
    ) -> Optional[PreFilterResult]:
        """
        Check for clear success cases that indicate good quality.
        
        Returns PreFilterResult if success detected, None otherwise.
        """
        # Excellent indicators: long content, good metadata, clean extraction
        if (content_length > self.EXCELLENT_CONTENT_LENGTH and
            article.title and len(article.title.strip()) > self.MIN_TITLE_LENGTH and
            html_ratio < 5 and  # Very clean extraction
            article.word_count and article.word_count > 300):
            
            return PreFilterResult(
                score=0.85,
                confidence=0.88,
                reason="excellent_indicators_long_clean_content",
                should_use_llm=False,
                detected_issues=detected_issues
            )
        
        # Good indicators: decent content, structured blocks
        if (content_length > 1500 and
            article.title and len(article.title.strip()) > self.MIN_TITLE_LENGTH and
            html_ratio < 10 and
            article.content_blocks and len(article.content_blocks) > 3):
            
            return PreFilterResult(
                score=0.75,
                confidence=0.86,
                reason="good_indicators_structured_content",
                should_use_llm=False,
                detected_issues=detected_issues
            )
        
        return None
    
    def estimate_cost_savings(self, total_articles: int) -> Dict[str, float]:
        """
        Estimate cost savings from pre-filtering.
        
        Args:
            total_articles: Total number of articles to evaluate
            
        Returns:
            Dictionary with cost savings estimates
        """
        # Based on expected distribution from implementation plan
        expected_high_confidence = 0.30  # 30% of cases can be pre-filtered
        llm_cost_per_article = 0.0005    # ~$0.0005 per LLM evaluation
        
        articles_pre_filtered = total_articles * expected_high_confidence
        articles_needing_llm = total_articles - articles_pre_filtered
        
        cost_without_filter = total_articles * llm_cost_per_article
        cost_with_filter = articles_needing_llm * llm_cost_per_article
        savings = cost_without_filter - cost_with_filter
        
        return {
            "total_articles": total_articles,
            "articles_pre_filtered": articles_pre_filtered,
            "articles_needing_llm": articles_needing_llm,
            "cost_without_filter": cost_without_filter,
            "cost_with_filter": cost_with_filter,
            "savings_usd": savings,
            "savings_percentage": (savings / cost_without_filter) * 100
        } 