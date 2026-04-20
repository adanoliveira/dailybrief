"""
Headline scoring service (Phase 1: authority-based).

Determines whether an article should enter the content enrichment pipeline
based on the authority of its source publication.

Phase 2 (future): Add cross-source centrality scoring based on title clustering.
"""

import logging

from apps.feeds.models import Publication

logger = logging.getLogger(__name__)

# Articles with a score at or above this threshold enter the pipeline
HEADLINE_THRESHOLD = 0.7


class HeadlineScorer:
    """
    Scores articles for pipeline eligibility.

    Phase 1: Pure authority-based scoring from Publication.authority field.

    Usage:
        scorer = HeadlineScorer()
        is_headline = scorer.should_process(publication)
        score = scorer.compute_score(publication)
    """

    def compute_score(self, publication: Publication | None) -> float:
        """
        Compute headline score for an article based on its publication.

        Args:
            publication: The article's Publication (may be None for unknown sources)

        Returns:
            Float score between 0.0 and 1.0
        """
        if not publication:
            return 0.0

        # Phase 1: authority-only scoring
        # Publication.authority defaults to 1.0, range is typically 0.0-10.0
        # Normalize to 0.0-1.0 scale (cap at 10.0)
        authority = min(publication.authority, 10.0) / 10.0
        return authority

    def should_process(self, publication: Publication | None) -> bool:
        """
        Determine if an article from this publication should enter the content pipeline.

        Args:
            publication: The article's Publication

        Returns:
            True if the article should be processed (is a "top headline").
        """
        return self.compute_score(publication) >= HEADLINE_THRESHOLD
