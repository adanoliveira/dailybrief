"""
Content Quality Evaluation Prompt Templates.

Unified JSON response format across all templates for consistency and improved
data structure. Templates optimized for modern LLMs with large context windows.
"""
from dataclasses import dataclass
from typing import Dict, Any
from abc import ABC, abstractmethod


@dataclass
class PromptTemplateMetadata:
    """Metadata for a prompt template version."""
    name: str
    version: str
    description: str
    created_by: str = "system"
    is_baseline: bool = False


class BasePromptTemplate(ABC):
    """Base class for all prompt templates."""
    
    @property
    @abstractmethod
    def metadata(self) -> PromptTemplateMetadata:
        """Return template metadata."""
        pass
    
    @property
    @abstractmethod
    def template_text(self) -> str:
        """Return the prompt template text."""
        pass
    
    def format(self, **kwargs) -> str:
        """Format the template with provided variables."""
        return self.template_text.format(**kwargs)
    
    @property
    def identifier(self) -> str:
        """Unique identifier for this template."""
        return f"{self.metadata.name}_{self.metadata.version}"


class FewShotExampleTemplate(BasePromptTemplate):
    """
    Template for individual few-shot examples.
    
    This template defines the structure for each reference example used in few-shot learning.
    The evaluator will hydrate this template for each example and concatenate them.
    """
    
    @property
    def metadata(self) -> PromptTemplateMetadata:
        return PromptTemplateMetadata(
            name="few_shot_example",
            version="v1.0",
            description="Template structure for individual few-shot reference examples"
        )
    
    @property
    def template_text(self) -> str:
        return """<example id="{example_id}">
<input>
EXTRACTED CONTENT:
Title: {title}
Author: {author}
Description: {description}
Content Blocks ({blocks_count} blocks): {content_blocks}
Metadata: {metadata}

ORIGINAL HTML SAMPLE ({html_length} chars):
{html_sample}
</input>

<expected_output>
{expected_json_output}
</expected_output>
</example>"""


# Unified JSON Response Format (used by all templates)
UNIFIED_JSON_SCHEMA = """{
  "template_version": "template_identifier_here",
  "evaluation_timestamp": "auto_generated",
  "scores": {
    "completeness": 0.0,
    "purity": 0.0,
    "structure": 0.0,
    "readability": 0.0
  },
  "confidence": 0.0,
  "assessment": {
    "explanation": "Detailed explanation of your assessment with specific examples from the content.",
    "missing_elements": ["Specific items missing from extraction", "Another missing element"],
    "noise_detected": ["Specific noise types found", "Another noise pattern"],
    "key_strengths": ["What worked well in extraction", "Another strength"],
    "improvement_areas": ["Specific improvements needed", "Another improvement area"]
  },
  "metadata": {
    "assessment_method": "llm_evaluation",
    "evidence_clarity": "high|medium|low",
    "pattern_consistency": "consistent|mixed|contradictory"
  }
}"""


class ComprehensiveQualityEvaluator(BasePromptTemplate):
    """
    Comprehensive quality evaluation template with unified JSON response format.
    
    Features:
    - XML-like structure for clear content parsing
    - Complete methodology explanation for consistent evaluation
    - Unified JSON response format with version tracking
    - Optimized for 128K+ token context windows
    - Full content evaluation (no sampling)
    - Detailed pattern recognition guidance
    """
    
    @property
    def metadata(self) -> PromptTemplateMetadata:
        return PromptTemplateMetadata(
            name="comprehensive_quality_evaluation",
            version="v3.1",
            description="Comprehensive template with XML structure, detailed methodology, and unified JSON response",
            is_baseline=True
        )
    
    @property
    def template_text(self) -> str:
        return """You are an expert content extraction quality evaluator. Your task is to assess how well content was extracted from HTML source.

{reference_examples}

EVALUATION METHODOLOGY:
1. Compare extracted content against the original HTML source
2. Identify any missing content, noise, or structural issues
3. Assess the quality across four dimensions using evidence
4. Calculate scores based on the rubric (0.0-1.0 scale)
5. Provide confidence based on evidence clarity

SCORING RUBRIC:
- **Completeness (0.0-1.0)**: How much of the important content was captured?
  • 1.0: All content captured perfectly
  • 0.75: Minor content missing (≤5%)
  • 0.5: Some content missing (6-15%)
  • 0.25: Major content missing (16-30%)
  • 0.0: Most content missing (>30%)

- **Purity (0.0-1.0)**: How much noise/unwanted content is present?
  • 1.0: No noise detected
  • 0.75: Minimal noise (ads, navigation)
  • 0.5: Some noise (related links, sidebars)
  • 0.25: Heavy noise (multiple unwanted sections)
  • 0.0: Mostly noise, little actual content

- **Structure (0.0-1.0)**: How well is the original structure preserved?
  • 1.0: Perfect structure preservation
  • 0.75: Minor formatting issues
  • 0.5: Some structure lost (headings, lists)
  • 0.25: Major structure problems
  • 0.0: Structure completely lost

- **Readability (0.0-1.0)**: How readable and well-formatted is the output?
  • 1.0: Perfectly readable and formatted
  • 0.75: Minor readability issues
  • 0.5: Some formatting problems
  • 0.25: Hard to read, poor formatting
  • 0.0: Unreadable or garbled

**Overall Score**: Calculated programmatically using domain-specific formula - DO NOT include in response.

**Confidence**: Rate 0.0-1.0 based on:
- Evidence clarity in the HTML source
- Pattern consistency in extraction
- Assessment certainty level

NOW EVALUATE THIS CONTENT:

<extraction_data>
EXTRACTED CONTENT:
Title: {title}
Author: {author}
Description: {description}
Content Blocks ({blocks_count} blocks): {blocks_sample}
Metadata: {metadata}

ORIGINAL HTML SAMPLE ({html_length} chars):
{html_sample}
</extraction_data>

RESPOND WITH A SINGLE JSON OBJECT:
{{
  "template_version": "comprehensive-quality-evaluation-v3.1",
  "evaluation_timestamp": "2025-01-27T12:00:00Z",
  "scores": {{
    "completeness": 0.0,
    "purity": 0.0,
    "structure": 0.0,
    "readability": 0.0
  }},
  "confidence": 0.0,
  "assessment": {{
    "explanation": "Brief explanation of the overall assessment",
    "missing_elements": ["list", "of", "missing", "content"],
    "noise_detected": ["list", "of", "noise", "elements"],
    "key_strengths": ["list", "of", "extraction", "strengths"],
    "improvement_areas": ["list", "of", "areas", "needing", "improvement"]
  }},
  "metadata": {{
    "assessment_method": "comprehensive_analysis",
    "evidence_clarity": "high|medium|low",
    "pattern_consistency": "consistent|mixed|inconsistent"
  }}
}}"""


class StructuredRubricEvaluator(BasePromptTemplate):
    """
    Structured rubric-based evaluation template with explicit anchor points and unified JSON response.
    
    Features:
    - Clear 5-point anchor system (0.0, 0.25, 0.5, 0.75, 1.0)
    - Look-fors, Questions, and Red-flags for each dimension
    - Explicit scoring formula with bonuses
    - Unified JSON response format with version tracking
    - Few-shot examples integration
    """
    
    @property
    def metadata(self) -> PromptTemplateMetadata:
        return PromptTemplateMetadata(
            name="structured_rubric_evaluation",
            version="v2025-05-v3",
            description="Structured rubric template with clear anchor points and unified JSON response format",
            created_by="user_reference",
            is_baseline=False
        )
    
    @property
    def template_text(self) -> str:
        return """You are an impartial auditor of news-article extraction quality from raw HTML.  
Follow the rubric exactly, think step-by-step, then answer in **valid JSON only**.

<<<BEGIN RUBRIC>>>
Compare the extracted content blocks against the original HTML source.

For each axis, read the LOOK-FORS, QUESTIONS and RED-FLAGS, then assign a
score using the 5-point anchor grid. All scores are floats between 0 and 1.

### 1 COMPLETENESS
✅ LOOK-FORS: title • author • main text • headlines/subheadlines • conclusion • rich content blocks (images, quotes, embeds, videos, carousels) • proper formatting (paragraphs, links, headings, lists, bold, italic, pull quotes)  
🤔 QUESTIONS: Is 100% of core content captured? Does text flow intro → body → conclusion? Are rich content blocks present and intact? Is formatting preserved (paragraphs, headings, styling)?  
🚩 RED-FLAGS: "Read more…" teasers • truncated mid-sentence • missing headlines/subheadlines • missing rich content • lost formatting • incomplete narrative.

<!--
ANCHORS for COMPLETENESS
0.0  None of the article text / embeds captured.
0.25 Fragment (<25% present) or ends mid-sentence.
0.5  About half missing or heavily truncated.
0.75 ≥75% present; ≤2 minor omissions.
1.0  100% core text + all embeds + formatting, in order.
-->

### 2 PURITY
✅ LOOK-FORS: only core article content (main text, headlines, rich content blocks, proper formatting).  
🤔 QUESTIONS: What % of extracted content is core vs. noise? Any navigation/ads/comments mixed in? Are bylines, timestamps, categories properly placed in metadata or in article body?  
🚩 RED-FLAGS: navigation menus • ads/recommended articles • comment sections • social share buttons • paywall indicators • HTML artifacts • bylines in article body • timestamps/dates in text • categories/breadcrumbs • "Related" section headlines.

<!--
ANCHORS for PURITY
0.0  Output is all noise (nav, ads, etc.).
0.25 Mostly noise; core text <25%.
0.5  Rough 50/50 core vs. noise.
0.75 Minor noise ≤25% of chars.
1.0  100% core; zero noise.
-->

### 3 STRUCTURE
✅ LOOK-FORS: proper paragraph breaks • correct heading hierarchy • logical content order • rich content blocks in correct positions • proper spacing between elements.  
🤔 QUESTIONS: Are paragraphs properly separated? Is heading order maintained? Do rich content blocks appear where they belong? Is the logical flow preserved?  
🚩 RED-FLAGS: flat wall of text • headings out of order • misplaced rich content • poor spacing • content blocks shuffled.

<!--
ANCHORS for STRUCTURE
0.0  Structure destroyed (no paragraphs / headings).
0.25 Serious mis-ordering or single giant block.
0.5  Some structure, but multiple grouping errors.
0.75 Minor spacing / heading issues only.
1.0  Paragraphs & headings perfect; embeds inline.
-->

### 4 READABILITY
✅ LOOK-FORS: clear, coherent sentences • natural flow for human consumption • proper formatting and spacing • valid UTF-8 encoding.  
🤔 QUESTIONS: Does it read naturally? Are sentences clear and coherent? Is spacing appropriate? Any encoding issues or artifacts?  
🚩 RED-FLAGS: broken sentences • repeated content blocks • poor line breaks • mojibake/encoding errors • HTML artifacts like "&nbsp;" • unnatural text flow.

<!--
ANCHORS for READABILITY
0.0  Unreadable gibberish or encoding junk.
0.25 Hard to read; broken lines dominate.
0.5  Legible but many spacing / encoding flaws.
0.75 Minor readability nits only.
1.0  Flows like a well-edited article.
-->

### 5 CONFIDENCE
✅ LOOK-FORS: clear evidence patterns • consistent quality signals • unambiguous assessment criteria.  
🤔 QUESTIONS: How certain am I in these scores? Are there contradictory signals? Is the evidence clear?  
🚩 RED-FLAGS: mixed signals, unclear patterns, contradictory evidence, ambiguous content.

<!--
ANCHORS for CONFIDENCE
0.0  Contradictory evidence; impossible to assess reliably.
0.25 Very uncertain; conflicting signals dominate.
0.5  Some uncertainty; mixed or unclear evidence.
0.75 Mostly confident; minor ambiguities only.
1.0  Completely certain; clear, consistent evidence.
-->

THOUGHT PROCESS (keep internal — do NOT reveal)
• Answer anchor questions for each axis with notes.  
• Convert notes to 0-1 scores using anchors.  
• Draft concise explanation & bullet lists.

SCORING FORMULA (FOR REFERENCE ONLY - DO NOT CALCULATE)
The overall extraction quality score will be calculated programmatically using:

base = completeness − (1 − purity)       # −1 … +1  
s_bon = (structure − 0.5) × 0.3           # ±0.15  
r_bon = (readability − 0.5) × 0.2         # ±0.10  
overall = clamp(base + s_bon + r_bon, −1, 1)

<<<END RUBRIC>>>

{reference_examples}

<<<BEGIN SAMPLE>>>
EXTRACTED CONTENT:
Title: {title}
Author: {author}
Description: {description}
Content Blocks ({blocks_count} blocks): {blocks_sample}
Metadata: {metadata}

ORIGINAL HTML SAMPLE ({html_length} chars):
{html_sample}
<<<END SAMPLE>>>

<<<BEGIN RESPONSE FORMAT>>>
Return this EXACT JSON structure:

{{
  "template_version": "structured_rubric_evaluation_v2025-05-v3",
  "evaluation_timestamp": "auto_generated",
  "scores": {{
    "completeness": 0.75,
    "purity": 0.85,
    "structure": 0.70,
    "readability": 0.80
  }},
  "confidence": 0.85,
  "assessment": {{
    "explanation": "Based on the 5-point anchor system: [your detailed assessment referencing specific anchors and evidence]",
    "missing_elements": ["Specific missing items based on LOOK-FORS"],
    "noise_detected": ["Specific noise based on RED-FLAGS"], 
    "key_strengths": ["What met the anchor criteria well"],
    "improvement_areas": ["What fell short of anchor expectations"]
  }},
  "metadata": {{
    "assessment_method": "structured_rubric",
    "evidence_clarity": "high",
    "pattern_consistency": "consistent"
  }}
}}
<<<END RESPONSE FORMAT>>>


Follow the rubric anchors precisely. Return only valid JSON with the 4 dimension scores."""


# Updated Template Registry
AVAILABLE_TEMPLATES: Dict[str, BasePromptTemplate] = {
    "comprehensive_quality_evaluation_v3.1": ComprehensiveQualityEvaluator(),
    "structured_rubric_evaluation_v2025-05-v3": StructuredRubricEvaluator(),
    "few_shot_example_v1.0": FewShotExampleTemplate(),
}

# Configuration - can be changed for testing
DEFAULT_TEMPLATE = "comprehensive_quality_evaluation_v3.1"
ACTIVE_TEMPLATE = "comprehensive_quality_evaluation_v3.1"  # Keep comprehensive as winner
FEW_SHOT_TEMPLATE = "few_shot_example_v1.0"


def get_template(template_id: str = None) -> BasePromptTemplate:
    """
    Get a prompt template by ID.
    
    Args:
        template_id: Template identifier, or None for active template
        
    Returns:
        BasePromptTemplate instance
        
    Raises:
        KeyError: If template_id not found
    """
    if template_id is None:
        template_id = ACTIVE_TEMPLATE
    
    if template_id not in AVAILABLE_TEMPLATES:
        raise KeyError(f"Template '{template_id}' not found. Available: {list(AVAILABLE_TEMPLATES.keys())}")
    
    return AVAILABLE_TEMPLATES[template_id]


def get_few_shot_template() -> FewShotExampleTemplate:
    """Get the few-shot example template."""
    return AVAILABLE_TEMPLATES[FEW_SHOT_TEMPLATE]


def list_templates() -> Dict[str, PromptTemplateMetadata]:
    """List all available templates with their metadata."""
    return {
        template_id: template.metadata 
        for template_id, template in AVAILABLE_TEMPLATES.items()
    }


def get_baseline_template() -> BasePromptTemplate:
    """Get the baseline template for comparisons."""
    for template in AVAILABLE_TEMPLATES.values():
        if template.metadata.is_baseline:
            return template
    
    # Fallback to default if no baseline marked
    return get_template(DEFAULT_TEMPLATE) 