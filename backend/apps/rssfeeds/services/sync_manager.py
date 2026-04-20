"""
RSS Sync Manager Service.

Orchestrates fetching and processing of RSS feeds.
"""

import logging
import time as time_module

from django.utils import timezone

from apps.rssfeeds.models import RSSFeed, RSSFeedSyncLog
from apps.rssfeeds.services.feed_fetcher import FeedFetcher
from apps.rssfeeds.services.article_processor import RSSArticleProcessor

logger = logging.getLogger(__name__)

# Polite delay between feed fetches (seconds)
INTER_FEED_DELAY = 0.5


class RSSSyncManager:
    """
    Orchestrates RSS feed syncing: fetch → process → log.

    Iterates over active feeds ordered by priority, fetching and processing
    each one with a small delay for polite crawling.
    """

    def __init__(self):
        self.fetcher = FeedFetcher()
        self.processor = RSSArticleProcessor()

    def sync_all_active_feeds(self) -> dict:
        """
        Sync all active RSS feeds ordered by priority.

        Returns:
            Summary dict with total counts.
        """
        feeds = RSSFeed.objects.filter(status='active').order_by('priority', 'last_fetched_at')
        return self._sync_feeds(feeds)

    def sync_feeds_by_topic(self, topic_slug: str) -> dict:
        """Sync only feeds matching a given topic slug."""
        feeds = RSSFeed.objects.filter(
            status='active',
            topic__slug=topic_slug,
        ).order_by('priority', 'last_fetched_at')
        return self._sync_feeds(feeds)

    def sync_feeds_by_region(self, region_code: str) -> dict:
        """Sync only feeds matching a given region code."""
        feeds = RSSFeed.objects.filter(
            status='active',
            region__code=region_code,
        ).order_by('priority', 'last_fetched_at')
        return self._sync_feeds(feeds)

    def sync_single_feed(self, feed_id: int) -> dict:
        """Sync a single feed by ID."""
        try:
            feed = RSSFeed.objects.get(id=feed_id)
        except RSSFeed.DoesNotExist:
            return {'error': f'Feed {feed_id} not found'}

        return self._sync_one(feed)

    def _sync_feeds(self, feeds) -> dict:
        """Iterate over a queryset of feeds and sync each."""
        total_created = 0
        total_updated = 0
        total_found = 0
        feeds_synced = 0
        feeds_skipped = 0

        for feed in feeds:
            result = self._sync_one(feed)

            if result.get('error'):
                feeds_skipped += 1
            else:
                feeds_synced += 1
                total_created += result.get('created', 0)
                total_updated += result.get('updated', 0)
                total_found += result.get('found', 0)

            # Polite delay between feeds
            time_module.sleep(INTER_FEED_DELAY)

        summary = {
            'feeds_synced': feeds_synced,
            'feeds_skipped': feeds_skipped,
            'articles_found': total_found,
            'articles_created': total_created,
            'articles_updated': total_updated,
        }
        logger.info(f"RSS sync complete: {summary}")
        return summary

    def _sync_one(self, feed: RSSFeed) -> dict:
        """Fetch and process a single feed."""
        start_time = timezone.now()

        # Create sync log
        sync_log = RSSFeedSyncLog.objects.create(
            feed=feed,
            status='started',
            parameters={'feed_url': feed.feed_url},
        )

        # Fetch
        fetch_result = self.fetcher.fetch(feed)

        # Update sync log with HTTP info
        sync_log.http_status = fetch_result.http_status
        sync_log.was_modified = fetch_result.was_modified

        if fetch_result.error:
            sync_log.status = 'failed'
            sync_log.error_message = fetch_result.error
            sync_log.completed_at = timezone.now()
            sync_log.duration_seconds = (timezone.now() - start_time).total_seconds()
            sync_log.save()
            return {'error': fetch_result.error}

        if not fetch_result.was_modified:
            # 304 Not Modified — nothing to process
            sync_log.status = 'completed'
            sync_log.articles_found = 0
            sync_log.completed_at = timezone.now()
            sync_log.duration_seconds = (timezone.now() - start_time).total_seconds()
            sync_log.save()
            return {'created': 0, 'updated': 0, 'found': 0, 'not_modified': True}

        # Process entries
        created, updated, found = self.processor.process_feed_entries(
            entries=fetch_result.entries,
            feed=feed,
            sync_log=sync_log,
        )

        # Finalize sync log
        sync_log.status = 'completed'
        sync_log.articles_found = found
        sync_log.articles_created = created
        sync_log.articles_updated = updated
        sync_log.completed_at = timezone.now()
        sync_log.duration_seconds = (timezone.now() - start_time).total_seconds()
        sync_log.save()

        logger.info(
            f"Synced {feed.publication.name}/{feed.title}: "
            f"{created} created, {updated} updated, {found} found"
        )

        return {'created': created, 'updated': updated, 'found': found}
