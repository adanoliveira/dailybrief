"""
HybridExtractor -- runs the LLM on already-cleaned HTML.

We intentionally re-use AIContentProcessor's machinery (LLM call, JSON parsing,
content-block validation, rate limiter, cost tracking) but invoke it with
`use_html_preprocessing=False` so the AI processor's own internal preprocessor
(which truncates to a 75k-token budget and does its own structural cleanup) is
bypassed. The HybridPreprocessor has already shrunk the HTML; running another
cleaner on top would mask the input difference we're measuring.

We also tag the result with `route_used="hybrid"` so the scoring harness and any
downstream telemetry can see which path produced the output.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from ..ai_processor import AIContentProcessor
from ..models import ProcessingResult

logger = logging.getLogger(__name__)


class HybridExtractor:
    """
    Wraps AIContentProcessor for the hybrid pipeline. The inputs differ from
    plain ai-only:

      • `cleaned_html` is the output of HybridPreprocessor (smaller than raw_html).
      • Internal HTML preprocessing is OFF -- we don't want a second cleaner pass.

    Everything else (prompt template, JSON schema, rate limiting, cost tracking)
    is identical to the production AI path. That keeps the comparison honest:
    differences in scoring will come from the input HTML, not from a different
    prompt or model.
    """

    def __init__(self, template_id: Optional[str] = None):
        # Reuse the production AI service. Same prompt, same model, same rate
        # limiter -- only the HTML input differs.
        self._ai = AIContentProcessor(template_id=template_id)

    def extract(
        self,
        cleaned_html: str,
        article_metadata: Dict[str, Any],
        base_url: Optional[str] = None,
        model_override: Optional[str] = None,
    ) -> ProcessingResult:
        result = self._ai.process_content(
            raw_html=cleaned_html,
            article_metadata=article_metadata or {},
            base_url=base_url,
            model_override=model_override,
            # Critical: the HTML is already preprocessed. Running the AI's own
            # preprocessor would shrink it again with a different policy and
            # invalidate the comparison.
            use_html_preprocessing=False,
        )
        # Annotate so downstream code can tell where this came from.
        result.route_used = "hybrid"
        return result
