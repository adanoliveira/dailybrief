"""
Headline scoring service (Phase 2: multi-signal scoring).

Determines whether an article should enter the content enrichment pipeline
using four signals:
  1. Publication authority (existing)
  2. Cross-source centrality (title clustering)
  3. Feed-level signals (position, categories, engagement)
  4. Burst/velocity (how fast multiple sources converge)

Combined: headline_score = 0.25*authority + 0.40*centrality + 0.20*feed_signals + 0.15*burst

Per-publisher diminishing returns apply after PUBLISHER_DAILY_SOFT_CAP
articles from the same publisher pass the threshold in a day.
"""

import logging

from apps.feeds.models import Publication

logger = logging.getLogger(__name__)

# Ingestion threshold — articles at or above this are tagged is_top_headline=True
# and are visible in the feed. The higher pipeline processing threshold is
# defined in pipeline_eligibility.py (0.70) with topic-aware adjustments.
HEADLINE_THRESHOLD = 0.60

# After this many articles from a single publisher pass the threshold
# in a calendar day, a diminishing score penalty is applied.
# This naturally reduces prolific sources without a hard cutoff.
PUBLISHER_DAILY_SOFT_CAP = 15

# Score penalty per article beyond the soft cap: 5% per extra article
PUBLISHER_DIMINISHING_RATE = 0.05

# High-importance RSS category terms (case-insensitive matching)
HIGH_IMPORTANCE_TAGS = {
    # English
    'breaking', 'breaking-news', 'top-story', 'top-stories', 'featured',
    'exclusive', 'developing', 'urgent', 'lead', 'front-page', 'homepage',
    'editors-pick', 'editor-pick', 'editors-picks',
    # Portuguese
    'destaque', 'manchete', 'urgente', 'exclusivo', 'capa', 'principal',
    'plantao', 'plantão', 'últimas',
}


class HeadlineScorer:
    """
    Multi-signal headline scoring for pipeline eligibility.

    Usage:
        scorer = HeadlineScorer()
        score = scorer.score_article(
            publication=pub,
            centrality=0.67,
            feed_signals=0.8,
            burst=0.5,
            cluster_size=3,
        )
        is_headline = score >= scorer.threshold
    """

    def __init__(self):
        self.threshold = HEADLINE_THRESHOLD

    def compute_authority(self, publication: Publication | None) -> float:
        """Normalize publication authority to 0-1 scale."""
        if not publication:
            return 0.0
        return min(publication.authority, 10.0) / 10.0

    def compute_feed_signals(
        self,
        entry_index: int = 0,
        total_entries: int = 1,
        is_curated_feed: bool = False,
        entry_tags: list | None = None,
        entry_data: dict | None = None,
    ) -> float:
        """
        Compute feed-level signals score (0-1).

        Args:
            entry_index: Position of entry in the feed (0-based)
            total_entries: Total entries in this feed batch
            is_curated_feed: Whether this is a top-stories/homepage feed
            entry_tags: List of tag dicts from feedparser (each has 'term')
            entry_data: Raw feedparser entry dict (for engagement signals)
        """
        pos = self._position_score(entry_index, is_curated_feed)
        cat = self._category_score(entry_tags)
        eng = self._engagement_score(entry_data)

        # Position is the most reliable signal
        return 0.50 * pos + 0.35 * cat + 0.15 * eng

    def compute_combined_score(
        self,
        authority: float = 0.0,
        centrality: float = 0.0,
        feed_signals: float = 0.0,
        burst: float = 0.0,
        cluster_size: int = 1,
        active_feeds_in_market: int = 15,
    ) -> float:
        """
        Compute the final headline score from all signals.

        Args:
            active_feeds_in_market: Number of active feeds for this language/market.
                Smaller markets (fewer feeds) get a centrality boost so that a
                cluster of 2 in a 7-feed market is weighted like a cluster of 4
                in a 15-feed market.

        Returns:
            Float between 0.0 and 1.0
        """
        # Adjust centrality for smaller markets
        adjusted_centrality = centrality
        if active_feeds_in_market < 12:
            market_factor = 12.0 / max(active_feeds_in_market, 3)
            adjusted_centrality = min(centrality * market_factor, 1.0)

        score = (
            0.25 * authority +
            0.40 * adjusted_centrality +
            0.20 * feed_signals +
            0.15 * burst
        )

        # Safety net: exclusive stories from elite outlets that are prominently
        # placed in the feed. Requires strong editorial signal (feed_signals)
        # to prevent prolific sources from flooding the feed.
        if authority > 0.90 and cluster_size == 1 and feed_signals > 0.6:
            score = max(score, 0.60)

        return min(score, 1.0)

    def score_article(
        self,
        publication: Publication | None = None,
        centrality: float = 0.0,
        feed_signals: float = 0.0,
        burst: float = 0.0,
        cluster_size: int = 1,
        active_feeds_in_market: int = 15,
    ) -> float:
        """
        Convenience method: compute full score from publication + signals.
        """
        authority = self.compute_authority(publication)
        return self.compute_combined_score(
            authority=authority,
            centrality=centrality,
            feed_signals=feed_signals,
            burst=burst,
            cluster_size=cluster_size,
            active_feeds_in_market=active_feeds_in_market,
        )

    def apply_publisher_diminishing_returns(
        self,
        score: float,
        publisher_daily_count: int,
    ) -> float:
        """
        Apply a diminishing score penalty when a publisher exceeds its
        daily soft cap.

        After PUBLISHER_DAILY_SOFT_CAP articles from the same publisher
        pass the threshold in a day, each additional article is penalised
        by PUBLISHER_DIMINISHING_RATE per extra article.  This naturally
        pushes lower-value articles from prolific sources below the
        threshold without a hard cutoff.

        Example with cap=15, rate=0.05:
            Article 16: score * 0.95
            Article 20: score * 0.75
            Article 30: score * 0.25
        """
        excess = max(0, publisher_daily_count - PUBLISHER_DAILY_SOFT_CAP)
        if excess == 0:
            return score
        penalty = 1.0 - (excess * PUBLISHER_DIMINISHING_RATE)
        return score * max(penalty, 0.10)  # floor at 10% to avoid negative

    def should_process(self, publication: Publication | None) -> bool:
        """
        Legacy Phase 1 API: determine eligibility from publication alone.

        Still used by NewsAPI processor which passes is_top_headline=True
        from the API endpoint. For RSS, use score_article() instead.
        """
        return self.compute_authority(publication) >= 0.7

    # --- Internal signal computations ---

    def _position_score(self, entry_index: int, is_curated: bool) -> float:
        """Score based on entry position in the feed."""
        if is_curated:
            # Top-stories/homepage feeds: first items are editorially chosen
            return max(1.0 - (entry_index * 0.15), 0.2)
        else:
            # Chronological feeds: position is weaker signal
            return max(1.0 - (entry_index * 0.05), 0.3)

    def _category_score(self, entry_tags: list | None) -> float:
        """Score based on RSS category/tag values."""
        if not entry_tags:
            return 0.0

        terms = set()
        for tag in entry_tags:
            term = ''
            if isinstance(tag, dict):
                term = (tag.get('term') or '').lower().strip()
            elif isinstance(tag, str):
                term = tag.lower().strip()
            if term:
                terms.add(term)

        if terms & HIGH_IMPORTANCE_TAGS:
            return 1.0
        return 0.0

    def _engagement_score(self, entry_data: dict | None) -> float:
        """Score based on comment/reply counts from RSS extensions."""
        if not entry_data:
            return 0.0

        comments = 0
        # slash:comments (WordPress feeds)
        slash_comments = entry_data.get('slash_comments')
        if slash_comments:
            try:
                comments = max(comments, int(slash_comments))
            except (ValueError, TypeError):
                pass

        # thr:total (Atom threading)
        thr_total = entry_data.get('thr_total')
        if thr_total:
            try:
                comments = max(comments, int(thr_total))
            except (ValueError, TypeError):
                pass

        # 50+ comments = max engagement score
        return min(comments / 50.0, 1.0)
