from django.test import SimpleTestCase

from apps.articles.services.headline_scoring import HeadlineScorer


class HeadlineScorerMarketAdjustmentTests(SimpleTestCase):
    def setUp(self):
        self.scorer = HeadlineScorer()

    def test_market_adjustment_boosts_centrality_for_smaller_markets(self):
        baseline = self.scorer.compute_combined_score(
            authority=0.0,
            centrality=0.5,
            feed_signals=0.0,
            burst=0.0,
            active_feeds_in_market=15,
        )
        boosted = self.scorer.compute_combined_score(
            authority=0.0,
            centrality=0.5,
            feed_signals=0.0,
            burst=0.0,
            active_feeds_in_market=8,
        )

        self.assertGreater(boosted, baseline)

    def test_market_adjustment_caps_boosted_centrality_at_one(self):
        score = self.scorer.compute_combined_score(
            authority=0.0,
            centrality=0.9,
            feed_signals=0.0,
            burst=0.0,
            active_feeds_in_market=3,
        )
        self.assertEqual(score, 0.4)


class HeadlineScorerSafetyNetTests(SimpleTestCase):
    def setUp(self):
        self.scorer = HeadlineScorer()

    def test_safety_net_requires_strong_feed_signal(self):
        without_signal = self.scorer.compute_combined_score(
            authority=0.95,
            centrality=0.0,
            feed_signals=0.6,
            burst=0.0,
            cluster_size=1,
            active_feeds_in_market=15,
        )
        with_signal = self.scorer.compute_combined_score(
            authority=0.95,
            centrality=0.0,
            feed_signals=0.61,
            burst=0.0,
            cluster_size=1,
            active_feeds_in_market=15,
        )

        self.assertLess(without_signal, 0.60)
        self.assertEqual(with_signal, 0.60)


class NewsAPISignalsTests(SimpleTestCase):
    def setUp(self):
        self.scorer = HeadlineScorer()

    def test_top_headline_position_zero_is_max_signal(self):
        signal = self.scorer.compute_newsapi_signals(
            is_top_headline=True, position=0,
        )
        self.assertEqual(signal, 1.0)

    def test_top_headline_signal_decays_with_position(self):
        early = self.scorer.compute_newsapi_signals(
            is_top_headline=True, position=0,
        )
        mid = self.scorer.compute_newsapi_signals(
            is_top_headline=True, position=5,
        )
        late = self.scorer.compute_newsapi_signals(
            is_top_headline=True, position=20,
        )

        self.assertGreater(early, mid)
        self.assertGreater(mid, late)
        # Floor: even position 20+ stays well above the everything-pool baseline
        self.assertGreater(late, 0.60)

    def test_everything_endpoint_articles_get_flat_low_signal(self):
        first = self.scorer.compute_newsapi_signals(
            is_top_headline=False, position=0,
        )
        later = self.scorer.compute_newsapi_signals(
            is_top_headline=False, position=10,
        )
        self.assertEqual(first, 0.30)
        self.assertEqual(later, 0.30)


class ScoreNewsAPIArticleTests(SimpleTestCase):
    """End-to-end score sanity checks against the triage thresholds.

    ACCEPT_THRESHOLD=0.50, REJECT_THRESHOLD=0.25 in apps.articles.services.triage.
    """

    def setUp(self):
        self.scorer = HeadlineScorer()

    class _StubPublication:
        def __init__(self, authority):
            self.authority = authority

    def test_top_headline_from_authoritative_outlet_passes_accept(self):
        # Major outlet (authority=8.5/10) on /top-headlines, no cluster yet
        score = self.scorer.score_newsapi_article(
            publication=self._StubPublication(authority=8.5),
            is_top_headline=True,
            position=0,
        )
        self.assertGreaterEqual(score, 0.50)

    def test_top_headline_from_minor_outlet_routes_to_llm(self):
        # Minor outlet (authority=4/10), top-headlines → ambiguous band
        score = self.scorer.score_newsapi_article(
            publication=self._StubPublication(authority=4.0),
            is_top_headline=True,
            position=0,
        )
        self.assertGreaterEqual(score, 0.25)
        self.assertLess(score, 0.50)

    def test_everything_endpoint_articles_dont_auto_accept(self):
        # Even a major outlet's /everything article should not auto-accept
        # without clustering or burst signals — those need LLM review.
        score = self.scorer.score_newsapi_article(
            publication=self._StubPublication(authority=8.5),
            is_top_headline=False,
            position=0,
        )
        self.assertLess(score, 0.50)
        self.assertGreaterEqual(score, 0.25)

    def test_no_publication_still_produces_valid_score(self):
        # Defensive: a NewsAPI source we couldn't match should still get a
        # number, not crash. Top-headline status keeps it above the floor.
        score = self.scorer.score_newsapi_article(
            publication=None,
            is_top_headline=True,
            position=0,
        )
        self.assertGreater(score, 0.0)
        self.assertLessEqual(score, 1.0)

