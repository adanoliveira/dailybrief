from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import SimpleTestCase, TestCase
from django.utils import timezone

from apps.core.api_utils import create_jwt_token
from apps.feeds.models import Topic, UserTopic
from apps.articles.models import (
    AnalyzerStatus,
    Article,
    FetchStatus,
    ProcessingStatus,
    SummarizationStatus,
)


def build_article(**overrides):
    defaults = {
        "title": "Test Article",
        "description": "A long enough description " * 10,
        "url": "https://example.com/article",
        "published_at": timezone.now(),
        "fetch_status": FetchStatus.PENDING,
        "process_status": ProcessingStatus.PENDING,
        "summarization_status": SummarizationStatus.PENDING,
        "analyzer_status": AnalyzerStatus.PENDING,
        "fetch_attempts": 0,
        "process_attempts": 0,
        "summarization_attempts": 0,
        "analyzer_attempts": 0,
        "raw_html": "",
        "basic_content": "",
        "clean_content": "",
        "content_blocks": [],
        "content_quality_metrics": {},
    }
    defaults.update(overrides)
    return Article(**defaults)


class ArticleFetchAndProcessingPropertyTests(SimpleTestCase):
    def test_needs_fetch_true_only_for_pending_with_attempts_under_limit(self):
        article = build_article(fetch_status=FetchStatus.PENDING, fetch_attempts=2)
        self.assertTrue(article.needs_fetch)

    def test_needs_fetch_false_when_attempt_limit_reached(self):
        article = build_article(fetch_status=FetchStatus.PENDING, fetch_attempts=3)
        self.assertFalse(article.needs_fetch)

    def test_has_raw_content_uses_length_threshold(self):
        article = build_article(raw_html="<html>" + ("x" * 200) + "</html>")
        self.assertTrue(article.has_raw_content)

        article.raw_html = "<html>short</html>"
        self.assertFalse(article.has_raw_content)

    def test_needs_processing_requires_completed_fetch_and_raw_content(self):
        article = build_article(
            fetch_status=FetchStatus.COMPLETED,
            raw_html="<html>" + ("x" * 200) + "</html>",
            process_status=ProcessingStatus.PENDING,
            process_attempts=1,
        )
        self.assertTrue(article.needs_processing)

        article.process_attempts = 3
        self.assertFalse(article.needs_processing)

    def test_has_usable_content_checks_multiple_fallback_fields(self):
        article = build_article(content="", basic_content="", clean_content="", description="short")
        self.assertFalse(article.has_usable_content)

        article.basic_content = "b" * 120
        self.assertTrue(article.has_usable_content)

    def test_update_rich_content_metadata_tracks_media_fields(self):
        article = build_article(
            content_blocks=[
                {"type": "paragraph"},
                {"type": "image"},
                {"type": "figure"},
                {"type": "video"},
                {"type": "audio"},
            ]
        )

        article.update_rich_content_metadata()

        self.assertTrue(article.has_images)
        self.assertTrue(article.has_videos)
        self.assertTrue(article.has_audio)
        self.assertEqual(article.media_count, 4)

    def test_get_content_blocks_by_type_filters_blocks(self):
        article = build_article(
            content_blocks=[
                {"type": "paragraph", "content": "A"},
                {"type": "quote", "content": "B"},
                {"type": "paragraph", "content": "C"},
            ]
        )

        paragraphs = article.get_content_blocks_by_type("paragraph")

        self.assertEqual(len(paragraphs), 2)
        self.assertEqual([block["content"] for block in paragraphs], ["A", "C"])


class ArticleSummarizationSelectionTests(SimpleTestCase):
    def test_has_summarizable_content_uses_clean_or_basic_thresholds(self):
        article = build_article(clean_content="x" * 201)
        self.assertTrue(article.has_summarizable_content)

        article.clean_content = "x" * 150
        article.basic_content = "y" * 201
        self.assertTrue(article.has_summarizable_content)

        article.basic_content = "y" * 150
        self.assertFalse(article.has_summarizable_content)

    def test_best_content_for_summarization_prefers_rich_blocks(self):
        article = build_article(
            content_blocks=[
                {"type": "heading", "content": "H"},
                {"type": "paragraph", "content": "P1"},
                {"type": "paragraph", "content": "P2"},
                {"type": "paragraph", "content": "P3"},
            ],
            clean_content="clean " * 80,
            basic_content="basic " * 80,
        )

        with patch.object(article, "_get_markdown_content_from_blocks", return_value="# markdown body"):
            content, source = article.best_content_for_summarization

        self.assertEqual(source, "rich_content_blocks")
        self.assertEqual(content, "# markdown body")

    def test_best_content_for_summarization_falls_back_clean_then_basic(self):
        article = build_article(
            content_blocks=[{"type": "paragraph", "content": "only one block"}],
            clean_content="clean " * 70,
            basic_content="basic " * 70,
        )
        content, source = article.best_content_for_summarization
        self.assertEqual(source, "full_cleaned_text")
        self.assertTrue(content.startswith("clean"))

        article.clean_content = "short"
        content, source = article.best_content_for_summarization
        self.assertEqual(source, "imcomplete_text")
        self.assertTrue(content.startswith("basic"))

    def test_best_content_for_summarization_returns_none_when_insufficient(self):
        article = build_article(clean_content="short", basic_content="tiny", content_blocks=[])

        content, source = article.best_content_for_summarization

        self.assertIsNone(content)
        self.assertIsNone(source)


class ArticleAnalysisPropertyTests(SimpleTestCase):
    def test_needs_analysis_requires_completed_summarization_and_content(self):
        article = build_article(
            summarization_status=SummarizationStatus.COMPLETED,
            clean_content="x" * 150,
            analyzer_status=AnalyzerStatus.PENDING,
            analyzer_attempts=2,
        )
        self.assertTrue(article.needs_analysis)

        article.analyzer_attempts = 3
        self.assertFalse(article.needs_analysis)

    def test_best_content_for_analysis_prefers_clean_then_basic_then_description(self):
        article = build_article(clean_content="clean " * 30, basic_content="basic " * 30, description="desc " * 20)
        self.assertEqual(article.best_content_for_analysis, "clean " * 30)

        article.clean_content = "short"
        self.assertEqual(article.best_content_for_analysis, "basic " * 30)

        article.basic_content = "short"
        self.assertEqual(article.best_content_for_analysis, "desc " * 20)

        article.description = "tiny"
        self.assertIsNone(article.best_content_for_analysis)


class FeedViewRankingAndPaginationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="feed-user",
            email="feed-user@example.com",
            password="password123",
        )
        self.token = create_jwt_token(self.user)
        self.topic = Topic.objects.create(name="Business", slug="business")
        UserTopic.objects.create(user=self.user, topic=self.topic, weight=1.0)

        now = timezone.now()
        for i in range(45):
            article = Article.objects.create(
                title=f"Article {i}",
                description=f"Description {i}",
                url=f"https://example.com/article-{i}",
                source_name=f"Source {i}",
                published_at=now - timedelta(minutes=i),
                is_top_headline=True,
                analyzer_status=AnalyzerStatus.COMPLETED,
            )
            article.topics.add(self.topic)

    def _auth_header(self):
        return {"HTTP_AUTHORIZATION": f"Bearer {self.token}"}

    def test_personalized_feed_page_two_keeps_correct_offset_with_diversification(self):
        response = self.client.get(
            "/api/articles/feed?page=2&page_size=10&sort=newest",
            **self._auth_header(),
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()["data"]
        titles = [a["title"] for a in payload["articles"]]
        self.assertEqual(len(titles), 10)
        self.assertEqual(titles[0], "Article 10")
        self.assertEqual(titles[-1], "Article 19")

    def test_world_feed_page_two_keeps_correct_offset_with_diversification(self):
        response = self.client.get(
            "/api/articles/world?page=2&page_size=10",
            **self._auth_header(),
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()["data"]
        titles = [a["title"] for a in payload["articles"]]
        self.assertEqual(len(titles), 10)
        self.assertEqual(titles[0], "Article 10")
        self.assertEqual(titles[-1], "Article 19")


class FeedHtmlRenderingTests(TestCase):
    def test_article_detail_strips_html_from_description(self):
        article = Article.objects.create(
            title="HTML Description Article",
            description="<p>Hello&nbsp;<strong>world</strong></p>",
            url="https://example.com/html-article",
            source_name="Source HTML",
            published_at=timezone.now(),
            is_top_headline=True,
            analyzer_status=AnalyzerStatus.COMPLETED,
        )

        response = self.client.get(f"/api/articles/{article.public_id}")

        self.assertEqual(response.status_code, 200)
        payload = response.json()["data"]
        self.assertEqual(payload["description"], "Hello world")
