"""
Management command to rescore all articles using the enhanced headline algorithm.

Usage:
    python manage.py rescore_headlines              # Rescore all articles from last 72h
    python manage.py rescore_headlines --days 7     # Rescore articles from last 7 days
    python manage.py rescore_headlines --dry-run    # Show what would change without saving
"""

import logging
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.articles.models import Article
from apps.articles.services.headline_scoring import HeadlineScorer
from apps.articles.services.story_clustering import StoryClustering, rebuild_vectorizer

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Rescore articles using the enhanced multi-signal headline algorithm'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days', type=int, default=3,
            help='Number of days back to rescore (default: 3)'
        )
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Show scoring results without saving'
        )
        parser.add_argument(
            '--rebuild-vectorizer', action='store_true',
            help='Force rebuild of the TF-IDF vectorizer before rescoring'
        )

    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']

        if options['rebuild_vectorizer']:
            self.stdout.write("Rebuilding TF-IDF vectorizer...")
            rebuild_vectorizer()
            self.stdout.write(self.style.SUCCESS("Vectorizer rebuilt."))

        cutoff = timezone.now() - timedelta(days=days)
        articles = Article.objects.filter(
            published_at__gte=cutoff
        ).select_related('publication', 'headline_cluster').order_by('-published_at')

        total = articles.count()
        self.stdout.write(f"Rescoring {total} articles from the last {days} days...")

        scorer = HeadlineScorer()
        clustering = StoryClustering()

        promoted = 0
        demoted = 0
        unchanged = 0
        predicted_headlines = 0

        for article in articles.iterator(chunk_size=200):
            # Compute authority
            authority = scorer.compute_authority(article.publication)

            # Compute centrality from existing cluster
            cluster = article.headline_cluster
            if article.headline_cluster:
                cluster_size = article.headline_cluster.article_count
                centrality = clustering._centrality_score(cluster_size)
                burst = article.headline_cluster.burst_score
            else:
                # Try to assign to a cluster
                lang = article.language.iso_code if article.language else 'en'
                cluster, centrality, burst = clustering.assign_to_cluster(
                    title=article.title,
                    description=article.description or '',
                    published_at=article.published_at,
                    language=lang,
                )
                cluster_size = cluster.article_count if cluster else 1
                if cluster and not dry_run:
                    article.headline_cluster = cluster

            # Use neutral feed signals for non-RSS articles, or compute from RSS data
            feed_signals = 0.5
            if hasattr(article, 'rss_data') and article.rss_data:
                rss = article.rss_data
                if rss.feed:
                    feed_signals = scorer.compute_feed_signals(
                        entry_index=0,  # Position not stored, use neutral
                        total_entries=1,
                        is_curated_feed=rss.feed.is_curated,
                        entry_tags=rss.raw_data.get('tags', []),
                        entry_data=rss.raw_data,
                    )

            # Count active feeds for this language market
            lang_short = (article.language.iso_code[:2] if article.language else 'en')
            try:
                from apps.rssfeeds.models import RSSFeed
                active_feeds = RSSFeed.objects.filter(
                    status='active',
                    language__iso_code__startswith=lang_short,
                ).count() or 15
            except Exception:
                active_feeds = 15

            new_score = scorer.compute_combined_score(
                authority=authority,
                centrality=centrality,
                feed_signals=feed_signals,
                burst=burst,
                cluster_size=cluster_size,
                active_feeds_in_market=active_feeds,
            )
            new_is_headline = new_score >= scorer.threshold
            old_is_headline = article.is_top_headline
            if new_is_headline:
                predicted_headlines += 1

            if new_is_headline and not old_is_headline:
                promoted += 1
            elif not new_is_headline and old_is_headline:
                demoted += 1
            else:
                unchanged += 1

            if not dry_run:
                article.headline_score = new_score
                article.is_top_headline = new_is_headline
                article.save(update_fields=[
                    'headline_score', 'is_top_headline', 'headline_cluster'
                ])

        new_headline_count = (
            articles.filter(is_top_headline=True).count()
            if not dry_run
            else predicted_headlines
        )
        pass_rate = (new_headline_count / total * 100) if total else 0

        self.stdout.write("")
        self.stdout.write(f"Results {'(DRY RUN)' if dry_run else ''}:")
        self.stdout.write(f"  Total articles:  {total}")
        self.stdout.write(f"  Promoted (new headlines):   {promoted}")
        self.stdout.write(f"  Demoted (removed from headlines): {demoted}")
        self.stdout.write(f"  Unchanged:       {unchanged}")
        self.stdout.write(f"  New pass rate:   ~{pass_rate:.1f}%")
        self.stdout.write(f"  Threshold:       {scorer.threshold}")

        if dry_run:
            self.stdout.write(self.style.WARNING("\nDry run — no changes saved."))
        else:
            self.stdout.write(self.style.SUCCESS("\nRescoring complete."))
