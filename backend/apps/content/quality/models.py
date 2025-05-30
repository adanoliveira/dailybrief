"""
Content Quality Assessment Models.

Domain-specific models for content quality evaluation results and criteria.
Separate from AI provider infrastructure models.
"""
from dataclasses import dataclass
from typing import List
from decimal import Decimal


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


@dataclass
class QualityScoring:
    """
    Quality scoring configuration and formulas.
    
    Encapsulates the business logic for how quality scores are calculated.
    """
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