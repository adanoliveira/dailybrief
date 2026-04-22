"""
Story clustering service for cross-source centrality scoring.

Groups articles about the same news story using TF-IDF cosine similarity
on titles and descriptions. Cluster size indicates importance — when
multiple outlets cover the same story, it's genuinely headline-worthy.

Designed for ingestion-time performance (<15ms per article).
"""

import logging
import math
import pickle
from datetime import timedelta
from pathlib import Path

import numpy as np
from django.conf import settings
from django.utils import timezone
from scipy.sparse import vstack
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from apps.articles.models import Article, HeadlineCluster

logger = logging.getLogger(__name__)

# Clustering parameters
SIMILARITY_THRESHOLD = 0.45  # Cosine similarity for same-story detection
CLUSTER_WINDOW_HOURS = 6  # Only compare against clusters from the last N hours
CLUSTER_EXPIRY_HOURS = 12  # Mark clusters inactive after N hours

# Vectorizer cache path
VECTORIZER_CACHE_DIR = Path(settings.BASE_DIR) / '.cache'
VECTORIZER_CACHE_PATH = VECTORIZER_CACHE_DIR / 'headline_vectorizer.pkl'

# Stopwords for both English and Portuguese
STOPWORDS_EN = {
    'a', 'an', 'the', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
    'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
    'should', 'may', 'might', 'shall', 'can', 'need', 'dare', 'ought',
    'used', 'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from',
    'as', 'into', 'through', 'during', 'before', 'after', 'above', 'below',
    'between', 'out', 'off', 'over', 'under', 'again', 'further', 'then',
    'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all', 'each',
    'every', 'both', 'few', 'more', 'most', 'other', 'some', 'such', 'no',
    'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 'just',
    'because', 'but', 'and', 'or', 'if', 'while', 'about', 'up', 'its',
    'it', 'he', 'she', 'they', 'we', 'you', 'i', 'this', 'that', 'these',
    'those', 'what', 'which', 'who', 'whom', 'his', 'her', 'their', 'our',
    'my', 'your', 'new', 'says', 'said',
}

STOPWORDS_PT = {
    'a', 'o', 'e', 'de', 'do', 'da', 'dos', 'das', 'em', 'no', 'na',
    'nos', 'nas', 'um', 'uma', 'uns', 'umas', 'por', 'para', 'com', 'sem',
    'sob', 'sobre', 'entre', 'que', 'se', 'ao', 'aos', 'pelo', 'pela',
    'pelos', 'pelas', 'como', 'mais', 'menos', 'muito', 'muita', 'muitos',
    'muitas', 'outro', 'outra', 'outros', 'outras', 'esse', 'essa', 'esses',
    'essas', 'este', 'esta', 'estes', 'estas', 'aquele', 'aquela', 'isso',
    'isto', 'ele', 'ela', 'eles', 'elas', 'seu', 'sua', 'seus', 'suas',
    'nos', 'lhe', 'lhes', 'me', 'te', 'vos', 'foi', 'ser', 'ter', 'estar',
    'tem', 'pode', 'vai', 'diz', 'disse', 'ja', 'ainda', 'tambem', 'ou',
    'mas', 'nem', 'nao', 'sim', 'ha', 'sao',
}

ALL_STOPWORDS = list(STOPWORDS_EN | STOPWORDS_PT)


class StoryClustering:
    """
    Assigns articles to story clusters based on title/description similarity.

    Uses a cached TF-IDF vectorizer and compares new articles against
    active cluster centroids using cosine similarity.
    """

    def __init__(self):
        self._vectorizer = None
        self._cluster_cache = None
        self._cache_loaded_at = None
        self._active_feed_count_cache: dict[str, int] = {}

    def _get_active_feeds_in_market(self, language_code: str | None) -> int:
        """
        Return active feed count for a market, cached by 2-letter language code.
        """
        lang_short = (language_code or 'en')[:2].lower() or 'en'
        if lang_short in self._active_feed_count_cache:
            return self._active_feed_count_cache[lang_short]

        try:
            from apps.rssfeeds.models import RSSFeed

            active_count = RSSFeed.objects.filter(
                status='active',
                language__iso_code__startswith=lang_short,
            ).count() or 15
        except Exception:
            active_count = 15

        self._active_feed_count_cache[lang_short] = active_count
        return active_count

    @property
    def vectorizer(self) -> TfidfVectorizer:
        if self._vectorizer is None:
            self._vectorizer = self._load_or_create_vectorizer()
        return self._vectorizer

    def assign_to_cluster(
        self,
        title: str,
        description: str,
        published_at,
        language: str = 'en',
    ) -> tuple[HeadlineCluster | None, float, float]:
        """
        Assign an article to an existing cluster or create a new one.

        Args:
            title: Article title
            description: Article description/summary
            published_at: Publication timestamp
            language: Language code (en, pt)

        Returns:
            Tuple of (cluster, centrality_score, burst_score)
        """
        text = self._prepare_text(title, description)
        if not text.strip():
            return None, 0.0, 0.0

        try:
            vector = self.vectorizer.transform([text])
        except Exception as e:
            logger.warning(f"Failed to vectorize text: {e}")
            return None, 0.0, 0.0

        # Find active clusters for this language
        cutoff = timezone.now() - timedelta(hours=CLUSTER_WINDOW_HOURS)
        active_clusters = list(
            HeadlineCluster.objects.filter(
                is_active=True,
                last_updated__gte=cutoff,
                language=language[:2],
            ).order_by('-last_updated')[:500]
        )

        if not active_clusters:
            cluster = self._create_cluster(title, published_at, language, vector)
            return cluster, self._centrality_score(1), 0.0

        # Load centroid vectors for active clusters
        best_score = 0.0
        best_cluster = None

        # Batch compute similarities against all active clusters
        cluster_vectors = self._get_cluster_vectors(active_clusters)
        if cluster_vectors is not None and cluster_vectors.shape[0] > 0:
            similarities = cosine_similarity(vector, cluster_vectors).flatten()
            best_idx = similarities.argmax()
            best_score = similarities[best_idx]
            if best_score >= SIMILARITY_THRESHOLD:
                best_cluster = active_clusters[best_idx]

        if best_cluster:
            # Join existing cluster
            best_cluster.article_count += 1
            best_cluster.last_updated = timezone.now()

            # Recalculate burst score
            cluster_articles = Article.objects.filter(
                headline_cluster=best_cluster
            ).values_list('published_at', flat=True)
            timestamps = list(cluster_articles)
            timestamps.append(published_at)
            best_cluster.burst_score = self._compute_burst_score(timestamps)

            best_cluster.save(update_fields=[
                'article_count', 'last_updated', 'burst_score'
            ])

            # Store the new vector for this cluster
            self._update_cluster_vector(best_cluster, vector)

            # Retroactively promote other articles in this cluster
            self._promote_cluster_articles(best_cluster)

            centrality = self._centrality_score(best_cluster.article_count)
            return best_cluster, centrality, best_cluster.burst_score
        else:
            # Create new cluster
            cluster = self._create_cluster(title, published_at, language, vector)
            return cluster, self._centrality_score(1), 0.0

    def _prepare_text(self, title: str, description: str) -> str:
        """Combine title and truncated description for vectorization."""
        desc = (description or '')[:200]
        return f"{title} {desc}".strip()

    def _centrality_score(self, cluster_size: int) -> float:
        """Convert cluster size to 0-1 centrality score using log scale."""
        return min(math.log2(cluster_size + 1) / 3.0, 1.0)

    def _compute_burst_score(self, timestamps) -> float:
        """Score based on how quickly multiple sources cover the story."""
        if len(timestamps) < 2:
            return 0.0

        sorted_ts = sorted(t for t in timestamps if t is not None)
        if len(sorted_ts) < 2:
            return 0.0

        first = sorted_ts[0]

        # Count sources within 2 hours of the first
        two_hour_count = sum(
            1 for t in sorted_ts
            if (t - first).total_seconds() < 7200
        )

        # 3+ sources within 1 hour = breaking news
        if len(sorted_ts) >= 3:
            time_for_three = (sorted_ts[2] - sorted_ts[0]).total_seconds()
            if time_for_three < 3600:
                return 1.0
            elif time_for_three < 7200:
                return 0.8

        return min(two_hour_count / 5.0, 1.0)

    def _create_cluster(self, title, published_at, language, vector) -> HeadlineCluster:
        """Create a new headline cluster."""
        now = timezone.now()
        cluster = HeadlineCluster.objects.create(
            representative_title=title[:512],
            article_count=1,
            first_seen=published_at or now,
            last_updated=now,
            burst_score=0.0,
            is_active=True,
            language=language[:2] if language else 'en',
        )
        self._store_cluster_vector(cluster, vector)
        return cluster

    def _promote_cluster_articles(self, cluster: HeadlineCluster):
        """
        Retroactively update headline scores for all articles in a cluster
        when the cluster grows.
        """
        from apps.articles.services.headline_scoring import HeadlineScorer

        scorer = HeadlineScorer()
        centrality = self._centrality_score(cluster.article_count)
        burst = cluster.burst_score

        active_feeds = self._get_active_feeds_in_market(cluster.language)

        articles = Article.objects.filter(
            headline_cluster=cluster
        ).select_related('publication')

        for article in articles:
            authority = min(article.publication.authority, 10.0) / 10.0 if article.publication else 0.0
            # Use a neutral feed_signals for retroactive promotion
            new_score = scorer.compute_combined_score(
                authority=authority,
                centrality=centrality,
                feed_signals=0.5,
                burst=burst,
                cluster_size=cluster.article_count,
                active_feeds_in_market=active_feeds,
            )
            if new_score != article.headline_score:
                article.headline_score = new_score
                article.is_top_headline = new_score >= scorer.threshold
                article.save(update_fields=['headline_score', 'is_top_headline'])

    # --- Vectorizer management ---

    def _load_or_create_vectorizer(self) -> TfidfVectorizer:
        """Load cached vectorizer or create a fresh one fitted on recent titles."""
        if VECTORIZER_CACHE_PATH.exists():
            try:
                with open(VECTORIZER_CACHE_PATH, 'rb') as f:
                    vectorizer = pickle.load(f)
                logger.debug("Loaded cached TF-IDF vectorizer")
                return vectorizer
            except Exception as e:
                logger.warning(f"Failed to load cached vectorizer: {e}")

        return self._fit_new_vectorizer()

    def _fit_new_vectorizer(self) -> TfidfVectorizer:
        """Fit a new vectorizer on recent article titles."""
        vectorizer = TfidfVectorizer(
            stop_words=ALL_STOPWORDS,
            max_features=20000,
            ngram_range=(1, 2),
            sublinear_tf=True,
            min_df=1,
            max_df=0.95,
        )

        # Fit on recent titles (last 7 days)
        cutoff = timezone.now() - timedelta(days=7)
        recent_articles = Article.objects.filter(
            published_at__gte=cutoff
        ).values_list('title', flat=True)[:5000]

        titles = list(recent_articles)
        if len(titles) < 10:
            # Not enough data — fit on a minimal corpus so transform works
            titles = [
                "breaking news headline story",
                "market update finance economy",
                "technology innovation startup",
                "politics government policy",
                "sports football basketball",
                "noticia economia mercado brasil",
                "politica governo eleicao",
                "esporte futebol campeonato",
                "tecnologia inovacao startup",
                "saude ciencia pesquisa",
            ]

        vectorizer.fit(titles)
        self._save_vectorizer(vectorizer)
        return vectorizer

    def _save_vectorizer(self, vectorizer: TfidfVectorizer):
        """Persist the fitted vectorizer to disk."""
        try:
            VECTORIZER_CACHE_DIR.mkdir(parents=True, exist_ok=True)
            with open(VECTORIZER_CACHE_PATH, 'wb') as f:
                pickle.dump(vectorizer, f)
            logger.info("Saved TF-IDF vectorizer to cache")
        except Exception as e:
            logger.warning(f"Failed to save vectorizer: {e}")

    # --- Cluster vector storage (using JSON field on HeadlineCluster) ---
    # For performance at our scale (~500 active clusters), we store vectors
    # as pickled sparse matrices in a simple file-based cache.

    def _get_cluster_vectors_path(self) -> Path:
        VECTORIZER_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        return VECTORIZER_CACHE_DIR / 'cluster_vectors.pkl'

    def _load_cluster_vectors(self) -> dict:
        """Load cluster_id -> vector mapping from cache."""
        path = self._get_cluster_vectors_path()
        if path.exists():
            try:
                with open(path, 'rb') as f:
                    return pickle.load(f)
            except Exception:
                pass
        return {}

    def _save_cluster_vectors(self, vectors: dict):
        """Save cluster vector cache."""
        path = self._get_cluster_vectors_path()
        try:
            with open(path, 'wb') as f:
                pickle.dump(vectors, f)
        except Exception as e:
            logger.warning(f"Failed to save cluster vectors: {e}")

    def _store_cluster_vector(self, cluster: HeadlineCluster, vector):
        """Store a vector for a cluster."""
        vectors = self._load_cluster_vectors()
        vectors[cluster.id] = vector
        self._save_cluster_vectors(vectors)

    def _update_cluster_vector(self, cluster: HeadlineCluster, new_vector):
        """Update cluster centroid with running average."""
        vectors = self._load_cluster_vectors()
        existing = vectors.get(cluster.id)
        if existing is not None:
            n = cluster.article_count
            # Running average of centroid
            updated = (existing * (n - 1) + new_vector) / n
            vectors[cluster.id] = updated
        else:
            vectors[cluster.id] = new_vector
        self._save_cluster_vectors(vectors)

    def _get_cluster_vectors(self, clusters: list) -> np.ndarray | None:
        """Get stacked vectors for a list of clusters."""
        vectors_cache = self._load_cluster_vectors()
        found_vectors = []
        found_clusters = []

        for i, cluster in enumerate(clusters):
            vec = vectors_cache.get(cluster.id)
            if vec is not None:
                found_vectors.append(vec)
                found_clusters.append(cluster)

        if not found_vectors:
            return None

        # Replace the input cluster list with only those that have vectors
        clusters.clear()
        clusters.extend(found_clusters)

        return vstack(found_vectors)


def rebuild_vectorizer():
    """Management command helper: rebuild and save a fresh vectorizer."""
    clustering = StoryClustering()
    clustering._vectorizer = clustering._fit_new_vectorizer()
    logger.info("Vectorizer rebuilt and cached")


def expire_old_clusters():
    """Mark clusters older than CLUSTER_EXPIRY_HOURS as inactive."""
    cutoff = timezone.now() - timedelta(hours=CLUSTER_EXPIRY_HOURS)
    expired = HeadlineCluster.objects.filter(
        is_active=True,
        last_updated__lt=cutoff,
    ).update(is_active=False)
    if expired:
        logger.info(f"Expired {expired} headline clusters")
    return expired
