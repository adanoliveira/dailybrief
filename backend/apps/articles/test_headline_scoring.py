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

