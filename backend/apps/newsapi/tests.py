from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from apps.newsapi.services.article_processor import ArticleProcessor


class ExistingTopHeadlineRefreshTests(SimpleTestCase):
    def _build_processor(self):
        processor = ArticleProcessor.__new__(ArticleProcessor)
        processor.headline_scorer = MagicMock()
        return processor

    def _make_article(
        self,
        *,
        is_top_headline=False,
        headline_score=0.10,
        triage_status="rejected",
    ):
        article = MagicMock()
        article.id = 123
        article.is_top_headline = is_top_headline
        article.headline_score = headline_score
        article.triage_status = triage_status
        article.publication = MagicMock()
        article.language = SimpleNamespace(iso_code="en")
        article.headline_cluster = SimpleNamespace(article_count=4, burst_score=0.2)
        return article

    def test_existing_top_headline_is_rescored_and_retriaged(self):
        processor = self._build_processor()
        article = self._make_article(
            is_top_headline=False,
            headline_score=0.10,
            triage_status="rejected",
        )

        with patch.object(processor, "_get_active_feeds_in_market", return_value=15):
            processor.headline_scorer.score_newsapi_article.return_value = 0.72
            with patch("apps.articles.services.triage.ArticleTriage") as triage_cls:
                triage = triage_cls.return_value
                triage_result = MagicMock()
                triage.tier1_algorithmic.return_value = triage_result

                processor._refresh_existing_article_for_top_headline(
                    article,
                    position=0,
                    total_in_batch=20,
                )

        self.assertTrue(article.is_top_headline)
        self.assertEqual(article.headline_score, 0.72)
        article.save.assert_any_call(update_fields=["is_top_headline", "headline_score"])
        triage.tier1_algorithmic.assert_called_once_with(article)
        triage.apply_result.assert_called_once_with(article, triage_result)

    def test_accepted_articles_are_not_retriaged(self):
        processor = self._build_processor()
        article = self._make_article(
            is_top_headline=False,
            headline_score=0.30,
            triage_status="accepted",
        )

        with patch.object(processor, "_get_active_feeds_in_market", return_value=15):
            processor.headline_scorer.score_newsapi_article.return_value = 0.65
            with patch("apps.articles.services.triage.ArticleTriage") as triage_cls:
                processor._refresh_existing_article_for_top_headline(
                    article,
                    position=2,
                    total_in_batch=20,
                )

        self.assertTrue(article.is_top_headline)
        self.assertEqual(article.headline_score, 0.65)
        article.save.assert_any_call(update_fields=["is_top_headline", "headline_score"])
        triage_cls.assert_not_called()
