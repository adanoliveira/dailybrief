import logging
import hashlib
import re
from datetime import datetime
from django.utils import timezone
from django.db import transaction
from apps.articles.models import Article
from apps.articles.services.deduplication import (
    ArticleDeduplicator,
    compute_content_hash,
    normalize_url,
)
from apps.articles.services.headline_scoring import HeadlineScorer
from apps.articles.services.publication_matcher import PublicationMatcher
from apps.articles.services.story_clustering import StoryClustering
from apps.feeds.models import Language, Topic
from apps.newsapi.models import NewsAPIArticle
from apps.newsapi.utils import extract_domain

logger = logging.getLogger(__name__)

class ArticleProcessor:
    """
    Processes articles from NewsAPI and transforms them into Article model instances.
    Handles matching to publications, languages, topics, and regions.

    Delegates deduplication and publication matching to shared services in
    apps.articles.services so the same logic is reused by other gateways.
    """

    def __init__(self):
        self.publication_matcher = PublicationMatcher()
        self.deduplicator = ArticleDeduplicator()
        self.headline_scorer = HeadlineScorer()
        self.story_clustering = StoryClustering()
        self.language_mapping = self._get_language_mapping()
        self.topic_mapping = self._get_topic_mapping()
        self._active_feed_count_cache: dict[str, int] = {}

    def _get_active_feeds_in_market(self, lang_code: str | None) -> int:
        """
        Return active RSS feed count for a market, cached by 2-letter
        language code. Used as the centrality denominator so NewsAPI
        articles get the same small-market boost as RSS.
        """
        lang_short = (lang_code or 'en')[:2].lower() or 'en'
        if lang_short in self._active_feed_count_cache:
            return self._active_feed_count_cache[lang_short]

        from apps.rssfeeds.models import RSSFeed
        active_count = RSSFeed.objects.filter(
            status='active',
            language__iso_code__startswith=lang_short,
        ).count() or 15
        self._active_feed_count_cache[lang_short] = active_count
        return active_count

    def _get_language_mapping(self):
        """Create a mapping of language codes to our Language objects."""
        return {lang.iso_code.lower(): lang for lang in Language.objects.all()}

    def _get_topic_mapping(self):
        """Create a mapping of NewsAPI categories to our Topic objects."""
        return {topic.slug.lower(): topic for topic in Topic.objects.all()}

    def _parse_date(self, date_str):
        """Parse a date string from the NewsAPI format to a datetime object."""
        if not date_str:
            return timezone.now()

        try:
            return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            try:
                return datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                logger.warning(f"Could not parse date: {date_str}")
                return timezone.now()

    def _get_or_create_publication(self, source_id, source_name, article_url):
        """
        Find an existing publication or create a new one based on available information.
        Delegates to shared PublicationMatcher service.
        """
        return self.publication_matcher.match(
            source_id=source_id,
            source_name=source_name,
            article_url=article_url,
        )

    def _get_or_create_article(self, article_data, is_top_headline=False, sync_log=None, category=None, position=0, total_in_batch=1):
        """
        Get an existing article or create a new one based on content hash first, then URL.

        Args:
            article_data (dict): Article data from NewsAPI
            is_top_headline (bool, optional): Whether this is a top headline
            sync_log (NewsAPISyncLog, optional): The sync log this article is part of
            category (str, optional): Category from NewsAPI (for topic mapping)
            position (int): Index of this article within the API response.
            total_in_batch (int): Total articles in the same batch.

        Returns:
            tuple: (Article, NewsAPIArticle, bool) where bool indicates if created
        """
        url = article_data.get('url')
        if not url:
            return None, None, False

        # Extract content from API response
        title = article_data.get('title', '')
        description = article_data.get('description', '')
        content = article_data.get('content', '')

        # Use shared deduplicator (checks URL, content hash, fuzzy title)
        source_info = article_data.get('source', {})
        source_id = source_info.get('id', '').lower() if source_info.get('id') else None
        source_name = source_info.get('name', '')

        publication = self.publication_matcher.match_existing(
            source_id=source_id,
            article_url=url,
        )
        published_at = self._parse_date(article_data.get('publishedAt'))

        existing_article = self.deduplicator.find_duplicate(
            url=url,
            title=title,
            description=description,
            content=content,
            publication=publication,
            published_at=published_at,
        )

        if existing_article:
            # Ensure NewsAPIArticle satellite exists
            try:
                existing_newsapi_article = NewsAPIArticle.objects.get(article=existing_article)
            except NewsAPIArticle.DoesNotExist:
                domain = extract_domain(url)
                existing_newsapi_article = NewsAPIArticle(
                    article=existing_article,
                    source_id=(source_id or '')[:255],
                    source_name=source_name[:255],
                    domain=(domain or '')[:255],
                    newsapi_id=f"{source_id}:{hashlib.md5(url.encode()).hexdigest()[:8]}"[:255],
                    category=category or article_data.get('category'),
                    raw_data=article_data,
                    is_top_headline=is_top_headline,
                    sync_log=sync_log
                )
                existing_newsapi_article.save()

            # Update is_top_headline status if needed
            if is_top_headline and not existing_newsapi_article.is_top_headline:
                existing_newsapi_article.is_top_headline = True
                existing_newsapi_article.save(update_fields=['is_top_headline'])

            # If an existing article later appears in /top-headlines, refresh
            # score + triage so stale low-scored rows can be promoted.
            if is_top_headline:
                self._refresh_existing_article_for_top_headline(
                    existing_article,
                    position=position,
                    total_in_batch=total_in_batch,
                )

            logger.info(f"Found existing article: {title[:50]}...")
            return existing_article, existing_newsapi_article, False

        # No duplicate found — create new article
        if not publication:
            publication = self._get_or_create_publication(source_id, source_name, url)

        logger.info(f"Creating new article: {title[:50]}...")
        article, newsapi_article = self._create_article_pair(
            article_data, is_top_headline, sync_log, category, publication, published_at,
            position=position, total_in_batch=total_in_batch,
        )
        return article, newsapi_article, True

    def _refresh_existing_article_for_top_headline(self, article, position=0, total_in_batch=1):
        """
        Refresh score + triage when an existing article is later seen as a top headline.

        Without this, older rows can remain with stale low scores/triage decisions
        from a weaker ingestion context (or pre-scoring bug) and never enter the
        enrichment pipeline despite receiving a stronger editorial signal.
        """
        update_fields = []
        if not article.is_top_headline:
            article.is_top_headline = True
            update_fields.append('is_top_headline')

        cluster = article.headline_cluster
        cluster_size = cluster.article_count if cluster else 1
        burst = cluster.burst_score if cluster else 0.0

        lang_code = article.language.iso_code if getattr(article, 'language', None) else 'en'
        active_feeds_in_market = self._get_active_feeds_in_market(lang_code)
        updated_score = self.headline_scorer.score_newsapi_article(
            publication=article.publication,
            is_top_headline=True,
            position=position,
            total_in_batch=total_in_batch,
            centrality=0.33,
            burst=burst,
            cluster_size=cluster_size,
            active_feeds_in_market=active_feeds_in_market,
        )

        current_score = article.headline_score or 0.0
        if updated_score > current_score:
            article.headline_score = updated_score
            update_fields.append('headline_score')

        if update_fields:
            article.save(update_fields=update_fields)

        # Re-run Tier 1 only for non-accepted articles, so new editorial signal
        # can rescue previously rejected/pending rows.
        if article.triage_status in ('pending', 'pending_llm', 'rejected'):
            try:
                from apps.articles.services.triage import ArticleTriage
                triage = ArticleTriage()
                result = triage.tier1_algorithmic(article)
                triage.apply_result(article, result)
            except Exception as e:
                logger.warning(
                    f"Tier 1 re-triage failed for existing top-headline article {article.id}: {e}"
                )

    def _calculate_content_metrics(self, content, title, description):
        """Calculate various metrics about the article content."""
        full_text = f"{title} {description} {content}".strip()

        # Word count
        word_count = len(re.findall(r'\w+', full_text)) if full_text else 0

        # Read time (average reading speed: 238 words per minute)
        read_time = round(word_count / 238, 1) if word_count > 0 else 0.5

        # Content hash for deduplication
        content_hash = compute_content_hash(title, description, content)

        # Extract basic keywords
        stop_words = {'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'with', 'by'}
        words = re.findall(r'\b[a-z]{3,15}\b', full_text.lower())
        keywords = list(set([w for w in words if w not in stop_words]))[:10]

        return word_count, read_time, content_hash, keywords

    def _create_article_pair(self, article_data, is_top_headline=False, sync_log=None, category=None, publication=None, published_at=None, position=0, total_in_batch=1):
        """
        Create a new Article and associated NewsAPIArticle.

        Args:
            article_data (dict): Article data from NewsAPI
            is_top_headline (bool): Whether this is a top headline
            sync_log (NewsAPISyncLog, optional): The sync log
            category (str, optional): Category from NewsAPI
            publication (Publication, optional): Pre-resolved publication
            published_at (datetime, optional): Pre-parsed publish date
            position (int): Index within the API response batch (0-based).
                NewsAPI returns top headlines in priority order, so
                position is a usable tie-break signal.
            total_in_batch (int): Total articles in the same batch.
        """
        # Extract source info
        source_info = article_data.get('source', {})
        source_id = source_info.get('id', '').lower() if source_info.get('id') else None
        source_name = source_info.get('name', '')
        article_url = article_data.get('url', '')

        # Resolve publication if not passed
        if not publication:
            publication = self._get_or_create_publication(source_id, source_name, article_url)

        # Extract domain from article URL
        domain = extract_domain(article_url)

        # Get the language (default to English if not specified)
        language_code = article_data.get('language', 'en').lower()
        language = self.language_mapping.get(language_code, self.language_mapping.get('en'))

        # Parse date if not passed
        if not published_at:
            published_at = self._parse_date(article_data.get('publishedAt'))

        # Extract content from API response
        title = article_data.get('title', '')
        description = article_data.get('description', '')
        content = article_data.get('content', '')

        # Calculate content metrics
        word_count, read_time, content_hash, keywords = self._calculate_content_metrics(
            content, title, description
        )

        # Normalize URL for storage
        normalized_url = normalize_url(article_url) or article_url

        # Truncate fields to fit database constraints
        author = (article_data.get('author') or '')[:255]
        source_name = (source_name or '')[:255]
        title = (title or '')[:512]
        normalized_url = (normalized_url or '')[:1024]
        image_url = (article_data.get('urlToImage') or '')[:1024] or None

        # Cluster + score before save so headline_score is set on creation.
        # Mirrors the RSS path so NewsAPI articles compete on the same
        # 0-1 scale inside the budget queue.
        lang_code = language.iso_code if language else 'en'
        cluster = None
        centrality = 0.33
        burst = 0.0
        try:
            cluster, centrality, burst = self.story_clustering.assign_to_cluster(
                title=title,
                description=description,
                published_at=published_at,
                language=lang_code,
            )
        except Exception as e:
            logger.warning(f"Story clustering failed for NewsAPI article: {e}")

        cluster_size = cluster.article_count if cluster else 1
        active_feeds_in_market = self._get_active_feeds_in_market(lang_code)
        headline_score = self.headline_scorer.score_newsapi_article(
            publication=publication,
            is_top_headline=is_top_headline,
            position=position,
            total_in_batch=total_in_batch,
            centrality=centrality,
            burst=burst,
            cluster_size=cluster_size,
            active_feeds_in_market=active_feeds_in_market,
        )

        # Create the article
        article = Article(
            title=title,
            description=description,
            content=content,
            url=normalized_url,
            image_url=image_url,
            source_name=source_name,
            publication=publication,
            author=author,
            language=language,
            published_at=published_at,
            is_top_headline=is_top_headline,
            headline_score=headline_score,
            headline_cluster=cluster,
            summary_ready=False,
            word_count=word_count,
            read_time_minutes=read_time,
            content_hash=content_hash,
            keywords=keywords,
            popularity_score=0.0,
            relevance_score=0.0
        )
        article.save()

        # Process topics
        if category and category.lower() in self.topic_mapping:
            article.topics.add(self.topic_mapping[category.lower()])
        elif publication:
            article.topics.set(publication.topics.all())

        # Add regions from the publication
        if publication:
            article.regions.set(publication.regions.all())

        # Tier 1 triage: instant algorithmic decision.
        # Must run AFTER topics/regions are assigned (triage uses topic counts).
        # Mirrors the RSS path so NewsAPI articles aren't stuck in 'pending'
        # waiting for the deferred Celery sweep.
        try:
            from apps.articles.services.triage import ArticleTriage
            triage = ArticleTriage()
            result = triage.tier1_algorithmic(article)
            triage.apply_result(article, result)
        except Exception as e:
            logger.warning(f"Tier 1 triage failed for NewsAPI article {article.id}: {e}")
            # Article stays at triage_status='pending' — Celery task will pick it up

        # Create the NewsAPIArticle
        newsapi_id = f"{source_id}:{hashlib.md5(article.url.encode()).hexdigest()[:8]}"
        newsapi_article = NewsAPIArticle(
            article=article,
            source_id=(source_id or '')[:255],
            source_name=source_name,
            domain=(domain or '')[:255],
            newsapi_id=newsapi_id[:255],
            category=category or article_data.get('category'),
            raw_data=article_data,
            is_top_headline=is_top_headline,
            sync_log=sync_log
        )
        newsapi_article.save()

        return article, newsapi_article

    def process_articles(self, api_response, is_top_headline=False, sync_log=None, category=None):
        """
        Process a batch of articles from a NewsAPI response.

        Args:
            api_response (dict): The response from NewsAPI
            is_top_headline (bool, optional): Whether these are top headlines
            sync_log (NewsAPISyncLog, optional): The sync log to associate with articles
            category (str, optional): Category from NewsAPI (for topic mapping)

        Returns:
            tuple: (created_count, updated_count, total_count)
        """
        if not api_response or 'articles' not in api_response:
            logger.warning("Invalid API response, no articles found")
            return 0, 0, 0

        articles_data = api_response['articles']
        created_count = 0
        updated_count = 0
        total_in_batch = len(articles_data)

        for position, article_data in enumerate(articles_data):
            try:
                with transaction.atomic():
                    article, newsapi_article, created = self._get_or_create_article(
                        article_data,
                        is_top_headline,
                        sync_log,
                        category,
                        position=position,
                        total_in_batch=total_in_batch,
                    )

                    if article:
                        if created:
                            created_count += 1
                        else:
                            if is_top_headline and not article.is_top_headline:
                                article.is_top_headline = True
                                article.save(update_fields=['is_top_headline'])
                                updated_count += 1

                            if category and category.lower() in self.topic_mapping:
                                topic = self.topic_mapping[category.lower()]
                                if not article.topics.filter(id=topic.id).exists():
                                    article.topics.add(topic)
            except Exception as e:
                title = article_data.get('title', 'unknown')[:80]
                logger.error(f"Failed to process article '{title}': {e}")

        total_count = created_count + updated_count
        return created_count, updated_count, total_count
