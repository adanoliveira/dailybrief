"""
Management command for manually triggering RSS feed syncs.

Usage:
    python manage.py sync_rss_feeds                     # Sync all active feeds
    python manage.py sync_rss_feeds --feed-id 5         # Sync a single feed
    python manage.py sync_rss_feeds --topic business    # Sync by topic
    python manage.py sync_rss_feeds --region us         # Sync by region
    python manage.py sync_rss_feeds --dry-run           # Show what would be synced
"""

from django.core.management.base import BaseCommand

from apps.rssfeeds.models import RSSFeed
from apps.rssfeeds.services.sync_manager import RSSSyncManager


class Command(BaseCommand):
    help = 'Sync RSS feeds manually'

    def add_arguments(self, parser):
        parser.add_argument('--feed-id', type=int, help='Sync a specific feed by ID')
        parser.add_argument('--topic', type=str, help='Sync feeds for a specific topic slug')
        parser.add_argument('--region', type=str, help='Sync feeds for a specific region code')
        parser.add_argument('--dry-run', action='store_true', help='Show feeds that would be synced without fetching')

    def handle(self, *args, **options):
        feed_id = options.get('feed_id')
        topic = options.get('topic')
        region = options.get('region')
        dry_run = options.get('dry_run')

        if dry_run:
            self._dry_run(feed_id, topic, region)
            return

        manager = RSSSyncManager()

        if feed_id:
            self.stdout.write(f"Syncing feed ID {feed_id}...")
            result = manager.sync_single_feed(feed_id)
        elif topic:
            self.stdout.write(f"Syncing feeds for topic: {topic}...")
            result = manager.sync_feeds_by_topic(topic)
        elif region:
            self.stdout.write(f"Syncing feeds for region: {region}...")
            result = manager.sync_feeds_by_region(region)
        else:
            self.stdout.write("Syncing all active feeds...")
            result = manager.sync_all_active_feeds()

        self.stdout.write(self.style.SUCCESS(f"Done: {result}"))

    def _dry_run(self, feed_id, topic, region):
        """Show what feeds would be synced."""
        if feed_id:
            feeds = RSSFeed.objects.filter(id=feed_id)
        elif topic:
            feeds = RSSFeed.objects.filter(status='active', topic__slug=topic)
        elif region:
            feeds = RSSFeed.objects.filter(status='active', region__code=region)
        else:
            feeds = RSSFeed.objects.filter(status='active')

        feeds = feeds.select_related('publication', 'topic', 'region').order_by('priority')

        self.stdout.write(f"\nWould sync {feeds.count()} feeds:\n")
        for feed in feeds:
            topic_name = feed.topic.name if feed.topic else '-'
            region_code = feed.region.code if feed.region else '-'
            self.stdout.write(
                f"  [{feed.priority}] {feed.publication.name} / {feed.title or feed.feed_url[:40]} "
                f"({topic_name}, {region_code}) — status={feed.status}"
            )
