from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from apps.articles.models import Article
from apps.articles.tasks import triage_pending_articles
from apps.feeds.models import Publication


class TriagePendingTasksTests(TestCase):
    def setUp(self):
        self.now = timezone.now()
        self.pub_capped = Publication.objects.create(
            name="Capped Publisher",
            website_url="https://capped.example.com",
        )
        self.pub_open = Publication.objects.create(
            name="Open Publisher",
            website_url="https://open.example.com",
        )

    def _create_accepted(self, publication, count):
        for idx in range(count):
            Article.objects.create(
                title=f"Accepted {idx}",
                url=f"https://{publication.id}.example.com/accepted-{idx}",
                publication=publication,
                published_at=self.now,
                triage_status='accepted',
                triaged_at=self.now,
            )

    def test_timeout_resolution_respects_publisher_hard_cap(self):
        self._create_accepted(self.pub_capped, 25)

        timed_out_capped = Article.objects.create(
            title="Timed out capped",
            url="https://capped.example.com/timed-out",
            publication=self.pub_capped,
            published_at=self.now,
            headline_score=0.6,
            triage_status='pending_llm',
            triaged_at=self.now - timedelta(hours=2),
        )
        timed_out_open = Article.objects.create(
            title="Timed out open",
            url="https://open.example.com/timed-out",
            publication=self.pub_open,
            published_at=self.now,
            headline_score=0.6,
            triage_status='pending_llm',
            triaged_at=self.now - timedelta(hours=2),
        )

        result = triage_pending_articles(limit=50)

        timed_out_capped.refresh_from_db()
        timed_out_open.refresh_from_db()

        self.assertEqual(timed_out_capped.triage_status, 'rejected')
        self.assertIn('timeout_publisher_cap', timed_out_capped.triage_reason)

        self.assertEqual(timed_out_open.triage_status, 'accepted')
        self.assertIn('timeout', timed_out_open.triage_reason)

        self.assertEqual(result['auto_rejected_timeout_publisher_cap'], 1)
        self.assertEqual(result['auto_accepted_timeout'], 1)
