"""
Headline scoring service (Phase 2: multi-signal scoring).

Determines whether an article should enter the content enrichment pipeline
using four signals:
  1. Publication authority (existing)
  2. Cross-source centrality (title clustering)
  3. Feed-level signals (position, categories, engagement)
  4. Burst/velocity (how fast multiple sources converge)

Combined: headline_score = 0.25*authority + 0.40*centrality + 0.20*feed_signals + 0.15*burst
Threshold: 0.45 (targets ~30-40% pass rate, down from 95%)
"""

import logging

from apps.feeds.models import Publication

logger = logging.getLogger(__name__)

# Articles with a score at or above this threshold enter the pipeline
# Calibrated on 776 articles: 0.60 yields ~30% pass rate
HEADLINE_THRESHOLD = 0.60

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

    def should_process(self, publication: Publication | None) -> bool:
        """
        Legacy Phase 1 API: determine eligibility from publication alone.

        Still used by NewsAPI processor which passes is_top_headline=True
        from the API endpoint. For RSS, use score_article() instead.
        """
        return self.compute_authority(publication) >= 0.7

    def compute_newsapi_signals(
        self,
        is_top_headline: bool = False,
        position: int = 0,
        total_in_batch: int = 1,
    ) -> float:
        """
        Compute NewsAPI editorial signal score (0-1).

        Substitutes for compute_feed_signals when scoring NewsAPI articles.
        NewsAPI doesn't expose RSS-style tags/comments, so the strongest
        signal is whether the article came from the /top-headlines endpoint
        (editorially curated by NewsAPI) versus /everything (background pool).

        Args:
            is_top_headline: True if article came from /top-headlines.
            position: Index of the article within the API response (0-based).
                      NewsAPI returns top headlines in priority order.
            total_in_batch: Total articles in the same batch (unused today,
                            reserved for future relative-position scaling).

        Returns:
            Float in [0.0, 1.0]. Top-headlines articles cluster in [0.7, 1.0];
            everything-endpoint articles get a flat 0.30 (they need
            non-editorial signals — clustering, authority — to clear triage).
        """
        if is_top_headline:
            # 85% editorial weight + 15% floor; position scales the editorial
            # weight only so that even position 20 stays at ~0.66.
            position_factor = max(1.0 - (position * 0.03), 0.7)
            return min(1.0, 0.85 * position_factor + 0.15)
        return 0.30

    def score_newsapi_article(
        self,
        publication: Publication | None = None,
        is_top_headline: bool = False,
        position: int = 0,
        total_in_batch: int = 1,
        centrality: float = 0.33,
        burst: float = 0.0,
        cluster_size: int = 1,
        active_feeds_in_market: int = 15,
    ) -> float:
        """
        Convenience method: compute full NewsAPI score from publication +
        editorial signals + clustering signals.

        Mirrors score_article() but uses compute_newsapi_signals() in place
        of feed_signals so NewsAPI articles compete on the same 0-1 scale
        as RSS. The combined-score formula is identical, which keeps both
        sources directly comparable inside the budget queue.
        """
        authority = self.compute_authority(publication)
        signals = self.compute_newsapi_signals(
            is_top_headline=is_top_headline,
            position=position,
            total_in_batch=total_in_batch,
        )
        return self.compute_combined_score(
            authority=authority,
            centrality=centrality,
            feed_signals=signals,
            burst=burst,
            cluster_size=cluster_size,
            active_feeds_in_market=active_feeds_in_market,
        )

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
