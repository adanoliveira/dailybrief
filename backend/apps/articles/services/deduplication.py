"""
Shared article deduplication service.

Provides a 3-layer dedup strategy used by all ingestion gateways (newsapi, rssfeeds, etc.)
to prevent duplicate Article records in the database.

Layers:
1. Normalized URL exact match
2. Content hash (MD5 of title + description + content)
3. Fuzzy title + same publication + time window match
"""

import hashlib
import logging
import re
from datetime import timedelta
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

from apps.articles.models import Article

logger = logging.getLogger(__name__)

# URL params to strip during normalization
TRACKING_PARAMS = {
    'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
    'ref', 'source', 'fbclid', 'gclid', 'mc_cid', 'mc_eid',
    'ncid', 'sr_share', 'mod', 'outputType',
}


def normalize_url(url: str) -> str:
    """
    Normalize a URL for deduplication purposes.

    Strips tracking params, www. prefix, trailing slashes, and fragments.
    """
    if not url:
        return ''

    try:
        parsed = urlparse(url)
        if not parsed.netloc:
            parsed = urlparse(f"https://{url}")
            if not parsed.netloc:
                return ''

        # Remove www. prefix
        netloc = re.sub(r'^www\.', '', parsed.netloc.lower())

        # Remove port 80/443
        netloc = re.sub(r':(80|443)$', '', netloc)

        # Strip tracking params
        params = parse_qs(parsed.query, keep_blank_values=False)
        filtered_params = {
            k: v for k, v in params.items()
            if k.lower() not in TRACKING_PARAMS
        }
        query_items = []
        for key in sorted(filtered_params):
            for value in sorted(filtered_params[key]):
                query_items.append((key, value))
        clean_query = urlencode(query_items, doseq=True)

        # Normalize scheme for web URLs
        scheme = parsed.scheme.lower()
        if scheme in ('http', 'https', ''):
            scheme = 'https'

        # Strip trailing slash from path
        path = parsed.path.rstrip('/')

        # Rebuild without fragment
        normalized = urlunparse((
            scheme,
            netloc,
            path,
            parsed.params,
            clean_query,
            '',  # no fragment
        ))
        return normalized
    except Exception:
        return url


def compute_content_hash(title: str, description: str, content: str) -> str | None:
    """
    Compute MD5 hash of article text for deduplication.
    Same algorithm used across all gateways for consistency.
    """
    full_text = f"{title or ''} {description or ''} {content or ''}".strip()
    if not full_text:
        return None
    return hashlib.md5(full_text.encode('utf-8')).hexdigest()


def _title_similarity(a: str, b: str) -> float:
    """
    Simple character-level similarity ratio between two strings.
    Uses SequenceMatcher-style calculation without importing difflib for speed.
    Falls back to token overlap for short strings.
    """
    if not a or not b:
        return 0.0

    a_lower = a.lower().strip()
    b_lower = b.lower().strip()

    if a_lower == b_lower:
        return 1.0

    # Token overlap (Jaccard similarity)
    tokens_a = set(re.findall(r'\w+', a_lower))
    tokens_b = set(re.findall(r'\w+', b_lower))

    if not tokens_a or not tokens_b:
        return 0.0

    intersection = tokens_a & tokens_b
    union = tokens_a | tokens_b

    return len(intersection) / len(union)


class ArticleDeduplicator:
    """
    Shared deduplication service for all ingestion gateways.

    Usage:
        deduplicator = ArticleDeduplicator()
        existing = deduplicator.find_duplicate(url, title, description, content, publication)
        if existing:
            # Article already exists, skip creation
        else:
            # Create new Article
    """

    def find_duplicate(
        self,
        url: str,
        title: str = '',
        description: str = '',
        content: str = '',
        publication=None,
        published_at=None,
    ) -> Article | None:
        """
        Check if an article already exists using 3-layer dedup.

        Args:
            url: Article URL
            title: Article title
            description: Article description/summary
            content: Article body content
            publication: Publication instance (for fuzzy title matching)
            published_at: Publish datetime (for time-window matching)

        Returns:
            Existing Article instance if duplicate found, None otherwise.
        """
        # Layer 1: Normalized URL match
        normalized = normalize_url(url)
        if normalized:
            match = Article.objects.filter(url=normalized).first()
            if not match and normalized.startswith('https://'):
                alternate = f"http://{normalized[8:]}"
                match = Article.objects.filter(url=alternate).first()
            if not match:
                # Also check against un-normalized URLs already in DB
                match = Article.objects.filter(url=url).first()
            if match:
                logger.debug(f"Dedup: URL match for '{title[:50]}'")
                return match

        # Layer 2: Content hash match
        content_hash = compute_content_hash(title, description, content)
        if content_hash:
            try:
                match = Article.objects.get(content_hash=content_hash)
                logger.debug(f"Dedup: Content hash match for '{title[:50]}'")
                return match
            except Article.DoesNotExist:
                pass
            except Article.MultipleObjectsReturned:
                match = Article.objects.filter(content_hash=content_hash).first()
                logger.warning(f"Dedup: Multiple articles with same hash: {content_hash}")
                return match

        # Layer 3: Fuzzy title + publication + time window
        if publication and title and published_at:
            time_window_start = published_at - timedelta(hours=2)
            time_window_end = published_at + timedelta(hours=2)

            candidates = Article.objects.filter(
                publication=publication,
                published_at__gte=time_window_start,
                published_at__lte=time_window_end,
            ).only('id', 'title')[:50]  # limit scan

            for candidate in candidates:
                if _title_similarity(title, candidate.title) > 0.85:
                    logger.debug(
                        f"Dedup: Fuzzy title match for '{title[:50]}' "
                        f"→ existing '{candidate.title[:50]}'"
                    )
                    return candidate

        return None
