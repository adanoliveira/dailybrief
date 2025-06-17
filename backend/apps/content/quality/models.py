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
    
    # Template tracking (for A/B testing)
    template_used: str = "unknown"      # Template identifier used
    template_version: str = "unknown"   # Template version used


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
    
    # Template tracking (code-based templates)
    template_used = models.CharField(
        max_length=100, 
        null=True, 
        blank=True, 
        help_text="Template identifier used (e.g., 'quality_evaluation_v1.1-concise')"
    )
    template_version = models.CharField(
        max_length=50, 
        null=True, 
        blank=True, 
        help_text="Template version used (e.g., 'v1.1-concise')"
    )
    
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


# Remove PromptTemplate model - using code-based templates instead

# Keep PromptComparisonTest for formal A/B testing experiments (optional)
class PromptComparisonTest(models.Model):
    """
    Tracks formal A/B testing experiments comparing different prompt templates.
    
    This is for structured experiments, not day-to-day template usage tracking.
    Template versions are referenced by their code-based identifiers.
    """
    name = models.CharField(max_length=100, help_text="Test experiment name")
    description = models.TextField(help_text="Description of what's being tested")
    
    # Templates being compared (by identifier, not foreign key)
    baseline_template_id = models.CharField(
        max_length=100, 
        help_text="Baseline template identifier (e.g., 'quality_evaluation_v1.0')"
    )
    variant_template_id = models.CharField(
        max_length=100,
        help_text="Variant template identifier (e.g., 'quality_evaluation_v1.1-concise')"
    )
    
    # Test configuration
    sample_size = models.IntegerField(help_text="Number of articles to test on")
    content_type = models.CharField(
        max_length=20, 
        choices=[('clean', 'Clean'), ('basic', 'Basic'), ('raw', 'Raw'), ('mixed', 'Mixed')],
        default='mixed'
    )
    
    # Results
    baseline_avg_score = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    variant_avg_score = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    baseline_avg_cost = models.DecimalField(max_digits=8, decimal_places=6, null=True, blank=True)
    variant_avg_cost = models.DecimalField(max_digits=8, decimal_places=6, null=True, blank=True)
    baseline_avg_tokens = models.IntegerField(null=True, blank=True)
    variant_avg_tokens = models.IntegerField(null=True, blank=True)
    
    # Statistical significance
    score_improvement = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    cost_change = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    is_significant = models.BooleanField(null=True, blank=True)
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ('planned', 'Planned'),
            ('running', 'Running'),
            ('completed', 'Completed'),
            ('cancelled', 'Cancelled')
        ],
        default='planned'
    )
    
    # Timestamps
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} ({self.status})"


class ReferenceQualityExample(models.Model):
    """
    Reference quality examples for evaluation calibration and few-shot learning.
    
    These are curated examples with known quality scores that serve multiple purposes:
    1. Few-shot examples in evaluation prompts 
    2. Calibration references for quality assessment
    3. Benchmarks for extraction pipeline evaluation
    """
    
    # Quality Categories
    class QualityClass(models.TextChoices):
        PERFECT = 'perfect', 'Perfect (>0.95)'
        GOOD = 'good', 'Good (0.80-0.95)'
        IMPERFECT = 'imperfect', 'Imperfect (0.00-0.80)'
        AWFUL = 'awful', 'Awful (<0.00)'
    
    # Basic identification
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    article = models.ForeignKey(
        'articles.Article', 
        on_delete=models.CASCADE,
        related_name='reference_quality_examples'
    )
    
    # Reference classification
    quality_class = models.CharField(
        max_length=20,
        choices=QualityClass.choices,
        help_text="Reference quality classification"
    )
    
    # Reference scores (ground truth)
    reference_overall_score = models.FloatField(
        help_text="Reference overall quality score (-1.0 to 1.0)"
    )
    reference_completeness = models.FloatField(
        help_text="Reference completeness score (0.0 to 1.0)"
    )
    reference_purity = models.FloatField(
        help_text="Reference purity score (0.0 to 1.0)"
    )
    reference_structure = models.FloatField(
        help_text="Reference structure score (0.0 to 1.0)"
    )
    reference_readability = models.FloatField(
        help_text="Reference readability score (0.0 to 1.0)"
    )
    
    # Reference explanation and patterns
    reference_explanation = models.TextField(
        help_text="Detailed explanation of quality assessment"
    )
    reference_missing_elements = models.JSONField(
        default=list,
        help_text="List of missing elements"
    )
    reference_noise_detected = models.JSONField(
        default=list,
        help_text="List of noise types detected"
    )
    reference_key_strengths = models.JSONField(
        default=list,
        help_text="List of extraction strengths"
    )
    reference_improvement_areas = models.JSONField(
        default=list,
        help_text="List of improvement areas"
    )
    
    # Stored content for examples
    stored_raw_html = models.TextField(
        blank=True,
        help_text="Stored raw HTML for reference"
    )
    stored_preprocessed_html = models.TextField(
        blank=True,
        help_text="Stored preprocessed HTML for reference"
    )
    stored_extracted_content = models.TextField(
        blank=True,
        help_text="Stored extracted content for reference"
    )
    stored_content_blocks = models.JSONField(
        default=list,
        help_text="Stored content blocks for reference"
    )
    
    # Usage and metadata
    use_in_prompts = models.BooleanField(
        default=True,
        help_text="Include in few-shot prompt examples"
    )
    use_for_calibration = models.BooleanField(
        default=True,
        help_text="Use for evaluation calibration"
    )
    use_for_benchmarking = models.BooleanField(
        default=True,
        help_text="Use for extraction pipeline benchmarking"
    )
    
    # Metadata
    created_by = models.CharField(max_length=100, default="system")
    notes = models.TextField(blank=True, help_text="Additional notes about this example")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'quality_reference_examples'
        ordering = ['quality_class', '-reference_overall_score']
        indexes = [
            models.Index(fields=['quality_class']),
            models.Index(fields=['use_in_prompts']),
            models.Index(fields=['use_for_calibration']),
        ]
    
    def __str__(self):
        return f"Reference {self.quality_class}: {self.article.title[:50]}... (Score: {self.reference_overall_score:.3f})"
    
    @property
    def short_title(self):
        """Shortened title for display."""
        return self.article.title[:50] + "..." if len(self.article.title) > 50 else self.article.title
    
    def get_reference_scores_dict(self):
        """Get reference scores as dictionary."""
        return {
            'overall': self.reference_overall_score,
            'completeness': self.reference_completeness,
            'purity': self.reference_purity,
            'structure': self.reference_structure,
            'readability': self.reference_readability
        }
    
    def get_formatted_example_text(self, include_html=True, max_content_chars=1000):
        """
        Get formatted text for use in prompt examples.
        
        Args:
            include_html: Whether to include HTML sample
            max_content_chars: Maximum characters of content to include
            
        Returns:
            Formatted example text for prompts
        """
        content_sample = self.stored_extracted_content
        if len(content_sample) > max_content_chars:
            content_sample = content_sample[:max_content_chars] + "..."
        
        html_sample = ""
        if include_html and self.stored_preprocessed_html:
            html_sample = self.stored_preprocessed_html[:max_content_chars] + "..."
        
        example = f"""
EXAMPLE - {self.quality_class.upper()} QUALITY:
Title: {self.article.title}
Content: {content_sample}
{f"HTML Sample: {html_sample}" if html_sample else ""}

Reference Assessment:
- Overall Score: {self.reference_overall_score:.3f}
- Completeness: {self.reference_completeness:.3f}, Purity: {self.reference_purity:.3f}
- Structure: {self.reference_structure:.3f}, Readability: {self.reference_readability:.3f}
- Explanation: {self.reference_explanation}
"""
        return example.strip()
    
    @classmethod
    def get_examples_for_prompts(cls, quality_classes=None, max_examples=3):
        """
        Get reference examples for use in prompts.
        
        Args:
            quality_classes: List of quality classes to include
            max_examples: Maximum number of examples to return
            
        Returns:
            QuerySet of reference examples
        """
        queryset = cls.objects.filter(use_in_prompts=True)
        
        if quality_classes:
            queryset = queryset.filter(quality_class__in=quality_classes)
        
        # Get diverse examples across quality classes
        examples = []
        for quality_class in cls.QualityClass.values:
            class_examples = queryset.filter(quality_class=quality_class)[:1]
            examples.extend(class_examples)
            
        return examples[:max_examples]
    
    @classmethod
    def get_calibration_set(cls):
        """Get full calibration dataset."""
        return cls.objects.filter(use_for_calibration=True).order_by('quality_class', '-reference_overall_score')
    
    @classmethod
    def get_benchmark_set(cls):
        """Get benchmark dataset for extraction evaluation."""
        return cls.objects.filter(use_for_benchmarking=True).order_by('quality_class', '-reference_overall_score') 