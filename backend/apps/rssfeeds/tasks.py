"""
Celery tasks for RSS feed syncing.
"""

import logging

from celery import shared_task

from apps.rssfeeds.services.sync_manager import RSSSyncManager

logger = logging.getLogger(__name__)


@shared_task(name='rssfeeds.sync_all_feeds')
def sync_all_feeds():
    """Sync all active RSS feeds. Runs every 2 hours."""
    manager = RSSSyncManager()
    result = manager.sync_all_active_feeds()
    logger.info(f"sync_all_feeds completed: {result}")
    return result


@shared_task(name='rssfeeds.sync_feeds_by_topic')
def sync_feeds_by_topic(topic_slug: str):
    """Sync feeds for a specific topic. Used for hourly finance syncs."""
    manager = RSSSyncManager()
    result = manager.sync_feeds_by_topic(topic_slug)
    logger.info(f"sync_feeds_by_topic({topic_slug}) completed: {result}")
    return result


@shared_task(name='rssfeeds.sync_feeds_by_region')
def sync_feeds_by_region(region_code: str):
    """Sync feeds for a specific region."""
    manager = RSSSyncManager()
    result = manager.sync_feeds_by_region(region_code)
    logger.info(f"sync_feeds_by_region({region_code}) completed: {result}")
    return result


@shared_task(name='rssfeeds.sync_single_feed')
def sync_single_feed(feed_id: int):
    """Sync a single feed by ID."""
    manager = RSSSyncManager()
    result = manager.sync_single_feed(feed_id)
    logger.info(f"sync_single_feed({feed_id}) completed: {result}")
    return result
