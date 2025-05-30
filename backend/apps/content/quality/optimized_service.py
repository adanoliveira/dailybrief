"""
Optimized Content Quality Assessment Service.

This service combines smart pre-filtering with LLM evaluation to provide
cost-effective, accurate quality assessment. It first uses traditional
heuristics to identify obvious cases, then falls back to LLM evaluation
for uncertain cases.

Architecture:
1. Smart Pre-Filter: Fast traditional checks (30% of cases)
2. LLM Evaluation: Comprehensive semantic analysis (70% of cases)
3. Cost tracking and optimization metrics
"""
import logging
from typing import Optional, Dict, List
from dataclasses import dataclass
from decimal import Decimal

from apps.articles.models import Article
from apps.aiproviders.service import AIProviderService, LLMResponse
from .evaluator import ContentQualityEvaluator, QualityAssessmentResult
from .pre_filter import SmartPreFilter, PreFilterResult
from .models import QualityScoring


logger = logging.getLogger(__name__)


@dataclass
class OptimizedQualityResult:
    """
    Result from optimized quality assessment combining pre-filter and LLM.
    """
    quality_score: float                    # Final quality score (-1 to 1)
    assessment_method: str                  # "pre_filter" or "llm_evaluation"
    pre_filter_result: Optional[PreFilterResult]
    llm_result: Optional[QualityAssessmentResult]
    cost_savings: bool                      # Whether pre-filter saved LLM cost
    processing_time_ms: int                 # Total processing time
    confidence: float                       # Overall confidence in result


class OptimizedQualityService:
    """
    Optimized quality assessment service combining pre-filtering and LLM evaluation.
    
    This service provides the main interface for quality assessment in the application,
    automatically choosing the most cost-effective approach while maintaining accuracy.
    """
    
    def __init__(self):
        self.pre_filter = SmartPreFilter()
        self.llm_evaluator = ContentQualityEvaluator()
        self.ai_service = AIProviderService()
        
        # Cost tracking
        self.total_assessments = 0
        self.pre_filter_assessments = 0
        self.llm_assessments = 0
    
    async def assess_article_quality(
        self, 
        article: Article,
        force_llm: bool = False,
        provider: str = "openai"
    ) -> OptimizedQualityResult:
        """
        Assess article quality using optimized approach.
        
        Args:
            article: Article to assess
            force_llm: Skip pre-filter and use LLM directly
            provider: AI provider for LLM evaluation
            
        Returns:
            OptimizedQualityResult with quality score and metadata
        """
        import time
        start_time = time.time()
        
        self.total_assessments += 1
        
        try:
            # Step 1: Pre-filter assessment (unless forced to skip)
            pre_filter_result = None
            if not force_llm:
                pre_filter_result = self.pre_filter.quick_quality_assessment(article)
                
                # If pre-filter is confident, use its result
                if not pre_filter_result.should_use_llm:
                    self.pre_filter_assessments += 1
                    processing_time = int((time.time() - start_time) * 1000)
                    
                    return OptimizedQualityResult(
                        quality_score=pre_filter_result.score,
                        assessment_method="pre_filter",
                        pre_filter_result=pre_filter_result,
                        llm_result=None,
                        cost_savings=True,
                        processing_time_ms=processing_time,
                        confidence=pre_filter_result.confidence
                    )
            
            # Step 2: LLM evaluation for uncertain cases
            self.llm_assessments += 1
            llm_result = await self.llm_evaluator.evaluate_article(article, provider)
            
            processing_time = int((time.time() - start_time) * 1000)
            
            return OptimizedQualityResult(
                quality_score=llm_result.overall_score,
                assessment_method="llm_evaluation",
                pre_filter_result=pre_filter_result,
                llm_result=llm_result,
                cost_savings=False,
                processing_time_ms=processing_time,
                confidence=llm_result.confidence
            )
            
        except Exception as e:
            logger.error(f"Optimized quality assessment failed for {article.public_id}: {e}")
            processing_time = int((time.time() - start_time) * 1000)
            
            # Return fallback result
            return OptimizedQualityResult(
                quality_score=-0.5,  # Assume poor quality on error
                assessment_method="error_fallback",
                pre_filter_result=pre_filter_result,
                llm_result=None,
                cost_savings=False,
                processing_time_ms=processing_time,
                confidence=0.1
            )
    
    async def batch_assess_articles(
        self,
        articles: List[Article],
        provider: str = "openai",
        force_llm: bool = False,
        save_to_db: bool = True
    ) -> List[OptimizedQualityResult]:
        """
        Assess quality for a batch of articles.
        
        Args:
            articles: List of articles to assess
            provider: AI provider for LLM evaluations
            force_llm: Skip pre-filter for all articles
            save_to_db: Save results to QualityScoring table
            
        Returns:
            List of OptimizedQualityResult instances
        """
        results = []
        
        for i, article in enumerate(articles):
            logger.info(f"Processing article {i+1}/{len(articles)}: {article.public_id}")
            
            try:
                result = await self.assess_article_quality(
                    article, 
                    force_llm=force_llm,
                    provider=provider
                )
                results.append(result)
                
                # Save to database if requested
                if save_to_db:
                    await self._save_quality_result(article, result)
                    
            except Exception as e:
                logger.error(f"Failed to assess article {article.public_id}: {e}")
                # Add error result to maintain list consistency
                results.append(OptimizedQualityResult(
                    quality_score=-0.5,
                    assessment_method="batch_error",
                    pre_filter_result=None,
                    llm_result=None,
                    cost_savings=False,
                    processing_time_ms=0,
                    confidence=0.1
                ))
        
        return results
    
    async def _save_quality_result(
        self, 
        article: Article, 
        result: OptimizedQualityResult
    ) -> QualityScoring:
        """Save quality assessment result to database."""
        # Create the quality scoring record
        quality_scoring = QualityScoring.objects.create(
            article=article,
            overall_score=Decimal(str(result.quality_score)),
            assessment_method=result.assessment_method,
            confidence_score=Decimal(str(result.confidence)),
            processing_time_ms=result.processing_time_ms,
            cost_optimized=result.cost_savings
        )
        
        # Add detailed scores if from LLM evaluation
        if result.llm_result:
            quality_scoring.completeness_score = Decimal(str(result.llm_result.completeness_score))
            quality_scoring.purity_score = Decimal(str(result.llm_result.purity_score))
            quality_scoring.structure_score = Decimal(str(result.llm_result.structure_score))
            quality_scoring.readability_score = Decimal(str(result.llm_result.readability_score))
            quality_scoring.detailed_feedback = result.llm_result.detailed_feedback
            quality_scoring.identified_issues = result.llm_result.identified_issues
            quality_scoring.save()
        
        # Add pre-filter information if available
        if result.pre_filter_result:
            quality_scoring.pre_filter_reason = result.pre_filter_result.reason
            quality_scoring.pre_filter_issues = result.pre_filter_result.detected_issues
            quality_scoring.save()
        
        return quality_scoring
    
    def get_optimization_stats(self) -> Dict[str, any]:
        """
        Get current optimization statistics.
        
        Returns:
            Dictionary with cost savings and performance metrics
        """
        if self.total_assessments == 0:
            return {
                "total_assessments": 0,
                "pre_filter_rate": 0.0,
                "llm_rate": 0.0,
                "cost_savings_percentage": 0.0
            }
        
        pre_filter_rate = self.pre_filter_assessments / self.total_assessments
        llm_rate = self.llm_assessments / self.total_assessments
        cost_savings_percentage = pre_filter_rate * 100
        
        # Estimate cost savings
        llm_cost_per_assessment = 0.0005  # ~$0.0005 per LLM call
        total_cost_without_filter = self.total_assessments * llm_cost_per_assessment
        actual_cost = self.llm_assessments * llm_cost_per_assessment
        savings_usd = total_cost_without_filter - actual_cost
        
        return {
            "total_assessments": self.total_assessments,
            "pre_filter_assessments": self.pre_filter_assessments,
            "llm_assessments": self.llm_assessments,
            "pre_filter_rate": round(pre_filter_rate, 3),
            "llm_rate": round(llm_rate, 3),
            "cost_savings_percentage": round(cost_savings_percentage, 1),
            "estimated_cost_without_filter_usd": round(total_cost_without_filter, 4),
            "actual_cost_usd": round(actual_cost, 4),
            "savings_usd": round(savings_usd, 4)
        }
    
    def reset_stats(self):
        """Reset optimization statistics."""
        self.total_assessments = 0
        self.pre_filter_assessments = 0
        self.llm_assessments = 0
    
    async def compare_methods(
        self,
        articles: List[Article],
        provider: str = "openai"
    ) -> Dict[str, any]:
        """
        Compare pre-filter vs LLM assessment for analysis.
        
        Runs both methods on the same articles to evaluate
        pre-filter accuracy and identify optimization opportunities.
        
        Args:
            articles: Articles to compare on
            provider: AI provider for LLM evaluations
            
        Returns:
            Comparison metrics and analysis
        """
        pre_filter_results = []
        llm_results = []
        agreements = []
        
        for article in articles:
            # Get pre-filter result
            pre_filter_result = self.pre_filter.quick_quality_assessment(article)
            pre_filter_results.append(pre_filter_result)
            
            # Get LLM result
            llm_result = await self.llm_evaluator.evaluate_article(article, provider)
            llm_results.append(llm_result)
            
            # Check agreement (if pre-filter was confident)
            if pre_filter_result.score is not None:
                score_diff = abs(pre_filter_result.score - llm_result.overall_score)
                agreement = score_diff < 0.3  # Within 0.3 points
                agreements.append(agreement)
        
        # Calculate metrics
        total_articles = len(articles)
        confident_pre_filter = sum(1 for r in pre_filter_results if r.score is not None)
        pre_filter_rate = confident_pre_filter / total_articles if total_articles > 0 else 0
        
        if agreements:
            agreement_rate = sum(agreements) / len(agreements)
        else:
            agreement_rate = 0.0
        
        return {
            "total_articles": total_articles,
            "confident_pre_filter_decisions": confident_pre_filter,
            "pre_filter_rate": round(pre_filter_rate, 3),
            "agreement_rate": round(agreement_rate, 3),
            "agreements": len(agreements),
            "disagreements": len(agreements) - sum(agreements),
            "pre_filter_results": pre_filter_results,
            "llm_results": llm_results
        } 