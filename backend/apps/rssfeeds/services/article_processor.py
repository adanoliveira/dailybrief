"""
RSS Article Processor Service.

Transforms feedparser entries into Article + RSSArticle records.
Delegates deduplication and publication matching to shared services.
"""

import logging
import re
import time
from datetime import datetime, timezone as datetime_timezone
from email.utils import parsedate_to_datetime

from django.db import transaction
from django.utils import timezone

from apps.articles.models import Article
from apps.articles.services.deduplication import (
    ArticleDeduplicator,
    compute_content_hash,
    normalize_url,
)
from apps.articles.services.headline_scoring import HeadlineScorer
from apps.articles.services.publication_matcher import PublicationMatcher
from apps.articles.services.story_clustering import StoryClustering
from apps.feeds.models import Language
from apps.feeds.utils import extract_domain
from apps.rssfeeds.models import RSSArticle, RSSFeed, RSSFeedSyncLog

logger = logging.getLogger(__name__)

# If RSS content exceeds this word count AND passes quality validation,
# skip the fetcher stage and use the RSS body directly.
FULL_CONTENT_WORD_THRESHOLD = 500

# Trailing markers that indicate the feed shipped a teaser rather than the full body.
_TRUNCATION_MARKERS = (
    '...',
    '…',
    '[...]',
    '[…]',
    'read more',
    'continue reading',
    'leia mais',
    'continuar lendo',
    'continuar leyendo',
    'ler mais',
)

# Minimum ratio of visible text to raw HTML. Values below this suggest the content
# is mostly markup/boilerplate rather than prose.
_MIN_TEXT_TO_HTML_RATIO = 0.3

# The tail window we inspect for truncation markers (characters from the end).
_TRUNCATION_TAIL_WINDOW = 120


def _looks_truncated(content: str) -> bool:
    """Return True if the RSS content ends with a typical teaser/truncation marker."""
    if not content:
        return False
    tail = re.sub(r'<[^>]+>', '', content)[-_TRUNCATION_TAIL_WINDOW:].strip().lower()
    if not tail:
        return False
    return any(tail.endswith(marker) for marker in _TRUNCATION_MARKERS)


def _has_paragraph_structure(content: str) -> bool:
    """Require at least two paragraph-like breaks (either <p> tags or double newlines)."""
    if not content:
        return False
    p_tag_count = len(re.findall(r'<p[\s>]', content, flags=re.IGNORECASE))
    if p_tag_count >= 2:
        return True
    double_breaks = content.count('\n\n')
    return double_breaks >= 2


def _text_to_html_ratio(content: str) -> float:
    """Compute the ratio of visible text length to total HTML length."""
    if not content:
        return 0.0
    text_only = re.sub(r'<[^>]+>', '', content).strip()
    if not content.strip():
        return 0.0
    return len(text_only) / len(content)


def rss_content_is_usable(content: str, word_count: int) -> bool:
    """
    Decide whether RSS body content is high-enough quality to skip the fetcher.

    Criteria:
    - word_count is already above FULL_CONTENT_WORD_THRESHOLD (caller enforces this)
    - Content is not ending with a teaser/truncation marker
    - Content has some paragraph structure
    - Content is not mostly HTML boilerplate
    """
    if word_count < FULL_CONTENT_WORD_THRESHOLD:
        return False
    if _looks_truncated(content):
        return False
    if not _has_paragraph_structure(content):
        return False
    if _text_to_html_ratio(content) < _MIN_TEXT_TO_HTML_RATIO:
        return False
    return True


class RSSArticleProcessor:
    """
    Processes RSS feed entries into Article + RSSArticle records.

    Uses shared services for dedup, publication matching, and headline scoring.
    """

    def __init__(self):
        self.deduplicator = ArticleDeduplicator()
        self.publication_matcher = PublicationMatcher()
        self.headline_scorer = HeadlineScorer()
        self.story_clustering = StoryClustering()
        self._language_cache = {lang.iso_code.lower(): lang for lang in Language.objects.all()}
        self._active_feed_count_cache: dict[str, int] = {}

    def _get_active_feeds_in_market(self, lang_code: str | None) -> int:
        """
        Return active feed count for a market, cached by 2-letter language code.

        Keeps ingestion fast by avoiding one query per new article.
        """
        lang_short = (lang_code or 'en')[:2].lower() or 'en'
        if lang_short in self._active_feed_count_cache:
            return self._active_feed_count_cache[lang_short]

        active_count = RSSFeed.objects.filter(
            status='active',
            language__iso_code__startswith=lang_short,
        ).count() or 15
        self._active_feed_count_cache[lang_short] = active_count
        return active_count

    def process_feed_entries(
        self,
        entries: list,
        feed: RSSFeed,
        sync_log: RSSFeedSyncLog,
    ) -> tuple[int, int, int]:
        """
        Process a batch of RSS entries for a given feed.

        Args:
            entries: List of feedparser entry dicts
            feed: The RSSFeed these entries came from
            sync_log: The sync log to associate articles with

        Returns:
            Tuple of (created_count, updated_count, total_found)
        """
        created = 0
        updated = 0
        total_entries = len(entries)

        for entry_index, entry in enumerate(entries):
            try:
                with transaction.atomic():
                    _, _, was_created, was_updated = self._process_entry(
                        entry, feed, sync_log, entry_index, total_entries
                    )
                    if was_created:
                        created += 1
                    elif was_updated:
                        updated += 1
            except Exception as e:
                title = entry.get('title', 'unknown')[:80]
                logger.error(f"Failed to process RSS entry '{title}': {e}")

        return created, updated, total_entries

    def _process_entry(
        self, entry: dict, feed: RSSFeed, sync_log: RSSFeedSyncLog,
        entry_index: int = 0, total_entries: int = 1,
    ) -> tuple[Article | None, RSSArticle | None, bool, bool]:
        """Process a single RSS entry."""
        # Extract basic fields
        url = entry.get('link', '')
        if not url:
            return None, None, False, False

        title = (entry.get('title') or '')[:512]
        description = self._extract_description(entry)
        content = self._extract_content(entry)
        published_at = self._parse_published_date(entry)
        guid = (entry.get('id') or entry.get('link') or '')[:1024]

        # Use the feed's publication directly (no guessing needed)
        publication = self.publication_matcher.match_by_publication(feed.publication)

        # Check for duplicates using shared deduplicator
        existing = self.deduplicator.find_duplicate(
            url=url,
            title=title,
            description=description,
            content=content,
            publication=publication,
            published_at=published_at,
        )

        if existing:
            # Ensure RSSArticle satellite exists
            if not hasattr(existing, 'rss_data'):
                try:
                    RSSArticle.objects.get(article=existing)
                except RSSArticle.DoesNotExist:
                    RSSArticle.objects.create(
                        article=existing,
                        feed=feed,
                        guid=guid,
                        domain=extract_domain(url) or '',
                        raw_data=self._serialize_entry(entry),
                        sync_log=sync_log,
                    )

            # Existing rows from a duplicate sync should not increment cluster counters.
            # Only backfill cluster assignment once for legacy articles that predate
            # the headline_cluster field.
            if not existing.headline_cluster:
                lang_code = feed.language.iso_code if feed.language else 'en'
                try:
                    cluster, _, _ = self.story_clustering.assign_to_cluster(
                        title=existing.title,
                        description=existing.description or '',
                        published_at=existing.published_at,
                        language=lang_code,
                    )
                    if cluster:
                        existing.headline_cluster = cluster
                        existing.save(update_fields=['headline_cluster'])
                except Exception as e:
                    logger.debug(f"Clustering failed for existing article: {e}")

            return existing, None, False, False

        # Create new article
        article, rss_article = self._create_article(
            entry, feed, sync_log, url, title, description, content,
            published_at, guid, publication, entry_index, total_entries,
        )
        return article, rss_article, True, False

    def _create_article(
        self, entry, feed, sync_log, url, title, description, content,
        published_at, guid, publication, entry_index=0, total_entries=1,
    ) -> tuple[Article, RSSArticle]:
        """Create a new Article + RSSArticle pair."""
        # Compute feed-level signals
        feed_signals = self.headline_scorer.compute_feed_signals(
            entry_index=entry_index,
            total_entries=total_entries,
            is_curated_feed=feed.is_curated,
            entry_tags=entry.get('tags', []),
            entry_data=entry,
        )

        # Compute cross-source centrality via clustering
        lang_code = feed.language.iso_code if feed.language else 'en'
        cluster = None
        centrality = 0.33  # default for single-source
        burst = 0.0
        try:
            cluster, centrality, burst = self.story_clustering.assign_to_cluster(
                title=title,
                description=description,
                published_at=published_at,
                language=lang_code,
            )
        except Exception as e:
            logger.warning(f"Story clustering failed: {e}")

        # Compute combined headline score
        authority = self.headline_scorer.compute_authority(publication)
        cluster_size = cluster.article_count if cluster else 1
        active_feeds_in_market = self._get_active_feeds_in_market(lang_code)

        headline_score = self.headline_scorer.compute_combined_score(
            authority=authority,
            centrality=centrality,
            feed_signals=feed_signals,
            burst=burst,
            cluster_size=cluster_size,
            active_feeds_in_market=active_feeds_in_market,
        )
        is_headline = headline_score >= self.headline_scorer.threshold

        # Content metrics
        full_text = f"{title} {description} {content}".strip()
        word_count = len(re.findall(r'\w+', full_text)) if full_text else 0
        read_time = round(word_count / 238, 1) if word_count > 0 else 0.5
        content_hash = compute_content_hash(title, description, content)

        # Normalize URL
        normalized_url = normalize_url(url) or url

        # Language from feed config
        language = None
        if feed.language:
            language = feed.language
        else:
            language = self._language_cache.get('en')

        # Image extraction
        image_url = self._extract_image(entry)

        # Determine fetch_status based on RSS content quality.
        # Only skip the fetcher when the RSS body passes quality validation —
        # otherwise truncated/boilerplate content would fail later stages.
        rss_content_words = len(re.findall(r'\w+', content)) if content else 0
        if rss_content_is_usable(content, rss_content_words):
            fetch_status = 'completed'
            # Store clean text in basic_content (strip HTML tags)
            basic_content = re.sub(r'<[^>]+>', '', content).strip()
            basic_content = re.sub(r'\s+', ' ', basic_content)
            fetch_strategy_used = 'rss_content'
        else:
            fetch_status = 'pending'
            basic_content = ''
            fetch_strategy_used = ''

        # Author
        author = (entry.get('author') or '')[:255]

        article = Article(
            title=title,
            description=description,
            content=content,
            url=normalized_url[:1024],
            image_url=(image_url or '')[:1024] or None,
            source_name=(publication.name if publication else '')[:255],
            publication=publication,
            author=author,
            language=language,
            published_at=published_at,
            is_top_headline=is_headline,
            headline_score=headline_score,
            headline_cluster=cluster,
            summary_ready=False,
            word_count=word_count,
            read_time_minutes=read_time,
            content_hash=content_hash,
            keywords=self._extract_keywords(title, description),
            popularity_score=0.0,
            relevance_score=0.0,
            fetch_status=fetch_status,
            basic_content=basic_content,
            fetch_strategy_used=fetch_strategy_used,
        )
        article.save()

        # Assign topic and region from the feed
        if feed.topic:
            article.topics.add(feed.topic)
        elif publication:
            article.topics.set(publication.topics.all())

        if feed.region:
            article.regions.add(feed.region)
        elif publication:
            article.regions.set(publication.regions.all())

        # Tier 1 triage: instant algorithmic decision
        # Must run AFTER topics/regions are assigned (triage uses topic counts)
        try:
            from apps.articles.services.triage import ArticleTriage
            triage = ArticleTriage()
            result = triage.tier1_algorithmic(article)
            triage.apply_result(article, result)
        except Exception as e:
            logger.warning(f"Tier 1 triage failed for article {article.id}: {e}")
            # Article stays at triage_status='pending' — Celery task will pick it up

        # Create RSSArticle satellite
        domain = extract_domain(url) or ''
        rss_article = RSSArticle(
            article=article,
            feed=feed,
            guid=guid,
            domain=domain[:255],
            raw_data=self._serialize_entry(entry),
            sync_log=sync_log,
        )
        rss_article.save()

        return article, rss_article

    def _extract_description(self, entry: dict) -> str:
        """Extract description/summary from an RSS entry, with content fallback."""
        desc = entry.get('summary', '') or entry.get('description', '') or ''
        if desc:
            return desc

        # Fallback: extract first 1-2 sentences from content body
        content = self._extract_content(entry)
        if content:
            # Strip HTML tags
            text = re.sub(r'<[^>]+>', '', content).strip()
            text = re.sub(r'\s+', ' ', text)
            if len(text) > 30:
                # Take first 2 sentences
                sentences = re.split(r'(?<=[.!?])\s+', text)
                desc = ' '.join(sentences[:2])
                return desc[:500]

        return ''

    def _extract_content(self, entry: dict) -> str:
        """
        Extract the best available content from an RSS entry.
        Prefers content:encoded (full content) over summary.
        """
        # Check for content:encoded (common in WordPress feeds)
        if 'content' in entry and entry['content']:
            # feedparser normalizes content:encoded into entry.content list
            for content_item in entry['content']:
                if content_item.get('value'):
                    return content_item['value']

        return ''

    def _extract_image(self, entry: dict) -> str | None:
        """Extract image URL from RSS entry, with multiple fallback layers."""
        url = self._extract_image_from_media_fields(entry)
        if url:
            return self._upgrade_image_url(url)

        # Fallback: parse <img> tags from content/summary HTML
        url = self._extract_image_from_html(entry)
        if url:
            return url

        return None

    def _extract_image_from_media_fields(self, entry: dict) -> str | None:
        """Extract image from feedparser's parsed media fields."""
        # media:thumbnail
        if 'media_thumbnail' in entry and entry['media_thumbnail']:
            return entry['media_thumbnail'][0].get('url')

        # media:content
        if 'media_content' in entry and entry['media_content']:
            for media in entry['media_content']:
                if media.get('medium') == 'image' or 'image' in media.get('type', ''):
                    return media.get('url')

        # enclosure
        if 'enclosures' in entry and entry['enclosures']:
            for enc in entry['enclosures']:
                if 'image' in enc.get('type', ''):
                    return enc.get('href') or enc.get('url')

        # links with type=image
        for link in entry.get('links', []):
            if 'image' in link.get('type', ''):
                return link.get('href')

        return None

    def _extract_image_from_html(self, entry: dict) -> str | None:
        """Parse <img> tags from RSS content/summary HTML."""
        from bs4 import BeautifulSoup

        for field_name in ('content', 'summary'):
            html = ''
            if field_name == 'content' and entry.get('content'):
                for item in entry['content']:
                    html += item.get('value', '')
            else:
                html = entry.get(field_name, '') or ''

            if '<img' not in html:
                continue

            soup = BeautifulSoup(html, 'html.parser')
            for img in soup.find_all('img'):
                src = img.get('src') or img.get('data-src') or ''
                if not src or not src.startswith('http'):
                    continue
                # Skip tracking pixels
                src_lower = src.lower()
                if any(p in src_lower for p in (
                    'pixel', 'tracking', 'beacon', '1x1',
                    'doubleclick', 'googletagmanager', 'facebook.com/tr',
                )):
                    continue
                # Skip tiny images
                w = img.get('width', '')
                h = img.get('height', '')
                try:
                    if w and h and int(w) <= 2 and int(h) <= 2:
                        continue
                except (ValueError, TypeError):
                    pass
                return self._upgrade_image_url(src)

        return None

    def _upgrade_image_url(self, url: str) -> str:
        """Upgrade known low-resolution image URL patterns to higher quality."""
        if not url:
            return url
        # BBC: /ace/standard/240/ → /ace/standard/960/
        if 'ichef.bbci.co.uk/ace/standard/240/' in url:
            return url.replace('/standard/240/', '/standard/960/')
        # NYT: mediumSquareAt3X → superJumbo
        if 'static01.nyt.com' in url and 'mediumSquare' in url:
            return re.sub(r'-mediumSquareAt\dX', '-superJumbo', url)
        return url

    def _extract_keywords(self, title: str, description: str) -> list:
        """Extract basic keywords from title and description."""
        text = f"{title} {description}".strip()
        if not text:
            return []
        stop_words = {
            'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to',
            'for', 'with', 'by', 'de', 'da', 'do', 'dos', 'das', 'em', 'no',
            'na', 'um', 'uma', 'que', 'com', 'para', 'por', 'sobre', 'como',
        }
        words = re.findall(r'\b[a-zA-ZÀ-ú]{3,15}\b', text.lower())
        return list(set(w for w in words if w not in stop_words))[:10]

    def _parse_published_date(self, entry: dict) -> datetime:
        """Parse published date from RSS entry."""
        # Try published_parsed (feedparser's pre-parsed time struct)
        for field in ('published_parsed', 'updated_parsed'):
            time_struct = entry.get(field)
            if time_struct:
                try:
                    return datetime(*time_struct[:6], tzinfo=datetime_timezone.utc)
                except (TypeError, ValueError):
                    pass

        # Try raw date strings
        for field in ('published', 'updated'):
            date_str = entry.get(field)
            if date_str:
                try:
                    parsed = parsedate_to_datetime(date_str)
                    if parsed is None:
                        continue
                    if timezone.is_naive(parsed):
                        parsed = timezone.make_aware(parsed, datetime_timezone.utc)
                    return parsed
                except (TypeError, ValueError):
                    pass

        return timezone.now()

    def _serialize_entry(self, entry: dict) -> dict:
        """Serialize feedparser entry to JSON-safe dict."""
        # feedparser entries contain time.struct_time objects that aren't JSON serializable
        safe = {}
        for key, value in entry.items():
            if isinstance(value, time.struct_time):
                safe[key] = time.strftime('%Y-%m-%dT%H:%M:%SZ', value)
            elif isinstance(value, (str, int, float, bool, type(None))):
                safe[key] = value
            elif isinstance(value, (list, dict)):
                try:
                    import json
                    json.dumps(value)
                    safe[key] = value
                except (TypeError, ValueError):
                    safe[key] = str(value)
            else:
                safe[key] = str(value)
        return safe
