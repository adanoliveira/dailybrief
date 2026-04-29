"""
Hybrid extraction pipeline (subtractive HTML preprocessor → AI extractor).

This package is intentionally separate from `algorithmic_processor.py` and
`ai_processor.py` so the three extraction paths stay truly independent and
A/B-comparable:

    • algo-only   → AlgorithmicProcessor (Safari Reader Mode; picks ONE element)
    • ai-only     → AIContentProcessor   (LLM extracts from raw_html)
    • hybrid      → HybridProcessor       (strip noise → smaller HTML → LLM)

The two parts of the hybrid path are deliberately split:

    HybridPreprocessor  -- SUBTRACTIVE: removes obvious non-content (scripts,
                          nav, ads, related-cards, popups, comments). Never
                          picks "the article element" -- that's the AI's job.
                          Output: smaller HTML, same shape.

    HybridExtractor     -- Calls the LLM on the pre-cleaned HTML, skipping
                          the AI processor's own internal preprocessor (which
                          would re-truncate to a 75k-token budget that no
                          longer applies to the smaller input).

Both pieces produce the same `ProcessingResult` shape as the originals so
downstream pipeline code (digest, articles_article persistence, scoring) is
unchanged.
"""

from .orchestrator import HybridProcessor
from .preprocessor import HybridPreprocessor, PreprocessResult
from .extractor import HybridExtractor

__all__ = [
    "HybridProcessor",
    "HybridPreprocessor",
    "HybridExtractor",
    "PreprocessResult",
]
