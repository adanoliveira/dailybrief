from django.test import TestCase
from django.utils import timezone

from apps.articles.models import Article
from apps.articles.services.triage import (
    ArticleTriage,
    PUBLISHER_VOLUME_HARD_CAP,
)
from apps.feeds.models import Publication


class ArticleTriagePublisherVolumeTests(TestCase):
    def setUp(self):
        self.triage = ArticleTriage()
        self.publication = Publication.objects.create(
            name="High Volume Source",
            website_url="https://source.example.com",
        )

    def _create_accepted_for_publication(self, count: int):
        now = timezone.now()
        for idx in range(count):
            Article.objects.create(
                title=f"Accepted {idx}",
                url=f"https://source.example.com/a-{idx}",
                publication=self.publication,
                published_at=now,
                triage_status='accepted',
                triaged_at=now,
            )

    def test_tier1_rejects_when_publisher_hits_hard_cap(self):
        self._create_accepted_for_publication(PUBLISHER_VOLUME_HARD_CAP)

        candidate = Article.objects.create(
            title="Long neutral headline used to test hard cap rejection",
            url="https://source.example.com/candidate-hard-cap",
            publication=self.publication,
            published_at=timezone.now(),
            headline_score=0.92,
        )

        result = self.triage.tier1_algorithmic(candidate)

        self.assertEqual(result.status, 'rejected')
        self.assertIn('publisher_cap', result.reason)

    def test_tier1_applies_publisher_penalty_before_threshold_decision(self):
        # Soft cap is 10; with 12 accepted today the penalty is -0.04.
        self._create_accepted_for_publication(12)

        candidate = Article.objects.create(
            title="Long neutral headline used to test soft cap penalty behavior",
            url="https://source.example.com/candidate-soft-cap",
            publication=self.publication,
            published_at=timezone.now(),
            headline_score=0.73,
        )

        result = self.triage.tier1_algorithmic(candidate)

        self.assertEqual(result.status, 'pending_llm')
        self.assertAlmostEqual(result.score, 0.69, places=2)
