"""
HybridProcessor -- chains HybridPreprocessor → HybridExtractor.

Public surface mirrors AlgorithmicProcessor / AIContentProcessor so callers can
swap routes without changing call sites.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, Optional

from ..models import ProcessingResult
from .extractor import HybridExtractor
from .preprocessor import HybridPreprocessor

logger = logging.getLogger(__name__)


class HybridProcessor:
    """
    Top-level entry point for the hybrid extraction route.

    Pipeline:
        1. HybridPreprocessor.preprocess(raw_html, base_url) → cleaned HTML + stats
        2. HybridExtractor.extract(cleaned_html, metadata)   → ProcessingResult

    The preprocessor's stats (size reduction, elements removed) are folded into
    `result.extracted_metadata["hybrid_preprocessing"]` so cost/quality analysis
    can correlate "% HTML stripped" with "extraction quality" at scale.
    """

    def __init__(
        self,
        template_id: Optional[str] = None,
        link_density_threshold: Optional[float] = None,
    ):
        kwargs = {}
        if link_density_threshold is not None:
            kwargs["link_density_threshold"] = link_density_threshold
        self.preprocessor = HybridPreprocessor(**kwargs)
        self.extractor = HybridExtractor(template_id=template_id)

    def process_content(
        self,
        raw_html: str,
        article_metadata: Dict[str, Any],
        base_url: Optional[str] = None,
        model_override: Optional[str] = None,
    ) -> ProcessingResult:
        start = time.time()

        pre = self.preprocessor.preprocess(raw_html, base_url=base_url)
        if not pre.success:
            return ProcessingResult(
                success=False,
                error_message=f"hybrid_preprocess_failed: {pre.error_message}",
                processing_time_ms=int((time.time() - start) * 1000),
                route_used="hybrid",
            )

        result = self.extractor.extract(
            cleaned_html=pre.cleaned_html,
            article_metadata=article_metadata or {},
            base_url=base_url,
            model_override=model_override,
        )

        # Fold preprocessing stats into the result for downstream analysis.
        meta = result.extracted_metadata or {}
        meta["hybrid_preprocessing"] = {
            "original_size_bytes": pre.original_size_bytes,
            "cleaned_size_bytes": pre.cleaned_size_bytes,
            "size_reduction_pct": pre.size_reduction_pct,
            "elements_removed": pre.elements_removed,
            "counts_by_reason": pre.counts_by_reason,
            "preprocess_time_ms": pre.processing_time_ms,
        }
        result.extracted_metadata = meta
        result.route_used = "hybrid"
        return result
