"""
Content Quality Assessment Models.

Domain-specific models for content quality evaluation results and criteria.
Separate from AI provider infrastructure models.
"""
import uuid
from dataclasses import dataclass
from typing import List
from decimal import Decimal

from django.db import models


@dataclass
class QualityAssessmentResult:
    """
    Result of content quality assessment - pure domain model.
    
    Contains comprehensive quality metrics and explanations for 
    content pipeline optimization. This is domain logic, not AI infrastructure.
    """
    # Core quality metrics (0 to 1 scale)
    overall_score: float      # Final score (-1 to +1)
    completeness: float       # How much content was captured (0-1)
    purity: float            # How clean the content is (0-1)
    structure: float         # How well structure is preserved (0-1)
    readability: float       # How readable the content is (0-1)
    
    # Meta information
    confidence: float                    # Assessment confidence (0-1)
    explanation: str                     # Human-readable explanation
    missing_elements: List[str]          # What's missing from extraction
    noise_detected: List[str]           # Types of noise found
    
    # Technical metadata
    evaluation_time: float              # Time taken for evaluation
    model_used: str                     # AI model used for assessment
    tokens_used: int                    # Total tokens consumed
    cost_usd: Decimal                   # Estimated cost in USD


class QualityScoring(models.Model):
    """
    Database model for storing quality assessment results.
    
    Stores the results of quality evaluations for articles including
    both pre-filter and LLM evaluation results.
    """
    # Primary key and relationships
    id = models.AutoField(primary_key=True)
    public_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    article = models.ForeignKey(
        'articles.Article', 
        on_delete=models.CASCADE,
        related_name='quality_assessments'
    )
    
    # Quality scores
    overall_score = models.DecimalField(max_digits=4, decimal_places=3, help_text="Overall quality score (-1 to 1)")
    completeness_score = models.DecimalField(max_digits=4, decimal_places=3, null=True, blank=True)
    purity_score = models.DecimalField(max_digits=4, decimal_places=3, null=True, blank=True)
    structure_score = models.DecimalField(max_digits=4, decimal_places=3, null=True, blank=True)
    readability_score = models.DecimalField(max_digits=4, decimal_places=3, null=True, blank=True)
    
    # Assessment metadata
    assessment_method = models.CharField(
        max_length=50,
        choices=[
            ('pre_filter', 'Pre-filter Assessment'),
            ('llm_evaluation', 'LLM Evaluation'),
            ('error_fallback', 'Error Fallback'),
            ('batch_error', 'Batch Error'),
        ],
        help_text="Method used for assessment"
    )
    confidence_score = models.DecimalField(max_digits=4, decimal_places=3, help_text="Confidence in assessment")
    processing_time_ms = models.IntegerField(help_text="Processing time in milliseconds")
    cost_optimized = models.BooleanField(default=False, help_text="Whether cost was optimized via pre-filter")
    
    # Detailed results (LLM evaluation)
    detailed_feedback = models.TextField(null=True, blank=True, help_text="Detailed feedback from LLM")
    identified_issues = models.JSONField(null=True, blank=True, help_text="List of identified issues")
    
    # Pre-filter results
    pre_filter_reason = models.CharField(max_length=100, null=True, blank=True, help_text="Pre-filter decision reason")
    pre_filter_issues = models.JSONField(null=True, blank=True, help_text="Issues detected by pre-filter")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'content_quality_scoring'
        indexes = [
            models.Index(fields=['article']),
            models.Index(fields=['overall_score']),
            models.Index(fields=['assessment_method']),
            models.Index(fields=['created_at']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"QualityScoring for {self.article.title[:50]} - {self.overall_score}"
    
    # Dimension weights
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
        Calculate overall quality score using domain-specific formula.
        
        Args:
            completeness: Content completeness score (0-1)
            purity: Content purity score (0-1)
            structure: Structure preservation score (0-1)
            readability: Readability score (0-1)
            
        Returns:
            Overall score (-1 to +1)
        """
        # Primary calculation (Perspective 2 approach)
        base_score = completeness - (1 - purity)  # Range: -1 to +1
        
        # Enhanced with structure and readability bonuses
        structure_bonus = (structure - 0.5) * cls.STRUCTURE_BONUS_MULTIPLIER  # ±0.15 adjustment
        readability_bonus = (readability - 0.5) * cls.READABILITY_BONUS_MULTIPLIER  # ±0.10 adjustment
        
        final_score = base_score + structure_bonus + readability_bonus
        
        # Clamp to valid range
        return max(-1.0, min(1.0, final_score))
    
    @classmethod
    def get_quality_classification(cls, score: float) -> tuple[str, str]:
        """
        Get quality classification for a given score.
        
        Args:
            score: Overall quality score (-1 to +1)
            
        Returns:
            Tuple of (grade, description)
        """
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