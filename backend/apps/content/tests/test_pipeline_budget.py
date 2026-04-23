from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from apps.articles.models import Article, ProcessingStatus
from apps.content.tasks import _get_base_queryset
from apps.feeds.models import Publication, Region


class PipelineBudgetSelectorTests(TestCase):
    def setUp(self):
        self.now = timezone.now()
        self.region_us = Region.objects.create(code='us', name='United States')
        self.pub_a = Publication.objects.create(
            name='Publisher A',
            website_url='https://publisher-a.example.com',
        )
        self.pub_b = Publication.objects.create(
            name='Publisher B',
            website_url='https://publisher-b.example.com',
        )

    def _make_article(self, **overrides):
        defaults = {
            'title': f"Article {self.now.timestamp()}",
            'url': f"https://example.com/{self.now.timestamp()}-{Article.objects.count()}",
            'published_at': self.now,
            'triage_status': 'accepted',
            'headline_score': 0.8,
            'publication': self.pub_a,
        }
        defaults.update(overrides)
        article = Article.objects.create(**defaults)
        article.regions.add(self.region_us)
        return article

    def test_selector_never_uses_legacy_is_top_headline_fallback(self):
        legacy = Article.objects.create(
            title='Legacy top headline',
            url='https://example.com/legacy',
            published_at=self.now,
            triage_status='pending',
            is_top_headline=True,
            headline_score=0.95,
        )
        legacy.regions.add(self.region_us)

        queryset = _get_base_queryset()

        self.assertEqual(queryset.count(), 0)

    def test_budget_exhaustion_still_keeps_in_flight_articles(self):
        in_flight = self._make_article(
            process_attempts=1,
            fetch_attempts=1,
            process_status=ProcessingStatus.PENDING,
        )
        self._make_article(
            process_attempts=1,
            process_status=ProcessingStatus.COMPLETED,
            last_process_attempt=self.now,
        )
        new_candidate = self._make_article(
            title='New Candidate',
            url='https://example.com/new-candidate',
            process_attempts=0,
            fetch_attempts=0,
            summarization_attempts=0,
            analyzer_attempts=0,
        )

        with patch('apps.content.tasks.DAILY_PIPELINE_BUDGET', 1):
            ids = set(_get_base_queryset().values_list('id', flat=True))

        self.assertIn(in_flight.id, ids)
        self.assertNotIn(new_candidate.id, ids)

    def test_over_cap_publishers_are_excluded_for_new_entries(self):
        self._make_article(
            publication=self.pub_a,
            process_attempts=1,
            process_status=ProcessingStatus.COMPLETED,
            last_process_attempt=self.now,
        )
        capped_candidate = self._make_article(
            title='Capped Candidate',
            url='https://example.com/capped-candidate',
            publication=self.pub_a,
            process_attempts=0,
            fetch_attempts=0,
            summarization_attempts=0,
            analyzer_attempts=0,
        )
        allowed_candidate = self._make_article(
            title='Allowed Candidate',
            url='https://example.com/allowed-candidate',
            publication=self.pub_b,
            process_attempts=0,
            fetch_attempts=0,
            summarization_attempts=0,
            analyzer_attempts=0,
        )

        with patch('apps.content.tasks.DAILY_PIPELINE_BUDGET', 10), patch(
            'apps.content.tasks.PUBLISHER_PIPELINE_CAP', 1
        ):
            ids = set(_get_base_queryset().values_list('id', flat=True))

        self.assertNotIn(capped_candidate.id, ids)
        self.assertIn(allowed_candidate.id, ids)
