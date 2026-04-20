"""
RSS Feed Fetcher Service.

Handles HTTP fetching of RSS/Atom feeds with conditional GET support,
error tracking, and auto-disable for broken feeds.
"""

import logging
import time
from dataclasses import dataclass

import feedparser
from django.utils import timezone

from apps.rssfeeds.models import RSSFeed

logger = logging.getLogger(__name__)

# Error thresholds
ERROR_PAUSE_THRESHOLD = 5
ERROR_DISABLE_THRESHOLD = 10


@dataclass
class FeedFetchResult:
    """Result of fetching a single RSS feed."""
    entries: list
    was_modified: bool
    http_status: int | None
    etag: str
    last_modified: str
    feed_title: str
    feed_type: str
    error: str | None = None


class FeedFetcher:
    """
    Fetches RSS/Atom feeds using feedparser with conditional GET.

    Supports:
    - ETag / Last-Modified for HTTP 304 (Not Modified) responses
    - Consecutive error tracking with auto-pause/disable
    - Feed metadata extraction on first fetch
    """

    def fetch(self, feed: RSSFeed) -> FeedFetchResult:
        """
        Fetch a single RSS feed, respecting conditional GET headers.

        Args:
            feed: RSSFeed instance to fetch

        Returns:
            FeedFetchResult with entries (empty if 304 or error)
        """
        try:
            # Build conditional GET params
            kwargs = {}
            if feed.etag:
                kwargs['etag'] = feed.etag
            if feed.last_modified:
                kwargs['modified'] = feed.last_modified

            # feedparser handles conditional GET natively
            parsed = feedparser.parse(
                feed.feed_url,
                **kwargs,
            )

            # Check for HTTP status
            http_status = getattr(parsed, 'status', None)

            # Handle 304 Not Modified
            if http_status == 304:
                self._record_success(feed, was_modified=False)
                return FeedFetchResult(
                    entries=[],
                    was_modified=False,
                    http_status=304,
                    etag=feed.etag,
                    last_modified=feed.last_modified,
                    feed_title=feed.title,
                    feed_type=feed.feed_type,
                )

            # Check for feed-level errors
            if parsed.bozo and not parsed.entries:
                error_msg = str(getattr(parsed, 'bozo_exception', 'Unknown parse error'))
                self._record_error(feed, error_msg)
                return FeedFetchResult(
                    entries=[],
                    was_modified=True,
                    http_status=http_status,
                    etag='',
                    last_modified='',
                    feed_title='',
                    feed_type='',
                    error=error_msg,
                )

            # Extract new conditional GET values
            new_etag = getattr(parsed, 'etag', '') or ''
            new_modified = getattr(parsed, 'modified', '') or ''

            # Update feed metadata on first successful fetch
            feed_title = getattr(parsed.feed, 'title', '') or ''
            feed_type = parsed.version or ''

            self._record_success(feed, was_modified=True, etag=new_etag,
                                 last_modified=new_modified, feed_title=feed_title,
                                 feed_type=feed_type)

            return FeedFetchResult(
                entries=parsed.entries,
                was_modified=True,
                http_status=http_status,
                etag=new_etag,
                last_modified=new_modified,
                feed_title=feed_title,
                feed_type=feed_type,
            )

        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            self._record_error(feed, error_msg)
            return FeedFetchResult(
                entries=[],
                was_modified=False,
                http_status=None,
                etag='',
                last_modified='',
                feed_title='',
                feed_type='',
                error=error_msg,
            )

    def _record_success(self, feed: RSSFeed, was_modified: bool,
                        etag: str = '', last_modified: str = '',
                        feed_title: str = '', feed_type: str = ''):
        """Update feed state after successful fetch."""
        update_fields = ['last_fetched_at', 'consecutive_errors']
        feed.last_fetched_at = timezone.now()
        feed.consecutive_errors = 0

        if was_modified:
            feed.last_successful_fetch_at = timezone.now()
            update_fields.append('last_successful_fetch_at')

        if etag:
            feed.etag = etag
            update_fields.append('etag')

        if last_modified:
            feed.last_modified = last_modified
            update_fields.append('last_modified')

        if feed_title and not feed.title:
            feed.title = feed_title[:255]
            update_fields.append('title')

        if feed_type and not feed.feed_type:
            feed.feed_type = feed_type[:20]
            update_fields.append('feed_type')

        if feed.status == 'error':
            feed.status = 'active'
            update_fields.append('status')

        feed.save(update_fields=update_fields)

    def _record_error(self, feed: RSSFeed, error_message: str):
        """Update feed state after failed fetch."""
        feed.last_fetched_at = timezone.now()
        feed.consecutive_errors += 1
        feed.last_error_message = error_message[:1000]

        if feed.consecutive_errors >= ERROR_DISABLE_THRESHOLD:
            feed.status = 'disabled'
            logger.warning(
                f"Feed disabled after {feed.consecutive_errors} consecutive errors: "
                f"{feed.publication.name} — {feed.feed_url}"
            )
        elif feed.consecutive_errors >= ERROR_PAUSE_THRESHOLD:
            feed.status = 'error'
            logger.warning(
                f"Feed paused after {feed.consecutive_errors} consecutive errors: "
                f"{feed.publication.name} — {feed.feed_url}"
            )

        feed.save(update_fields=[
            'last_fetched_at', 'consecutive_errors', 'last_error_message', 'status'
        ])
