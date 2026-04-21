"""Article tasks: cleanup and headline clustering maintenance.

Celery tasks for:
- Keeping the articles table bounded (weekly cleanup)
- Maintaining the headline clustering system (daily vectorizer rebuild, periodic cluster expiry)

See ``CELERY_BEAT_SCHEDULE`` in ``backend/dailybrief/settings.py``.
"""

import logging
from datetime import timedelta
from typing import Any, Dict

from celery import shared_task
from django.utils import timezone

from apps.articles.models import Article, FetchStatus

logger = logging.getLogger(__name__)


@shared_task
def cleanup_stale_articles(
    article_age_days: int = 30,
    unfetched_age_days: int = 7,
) -> Dict[str, Any]:
    """Delete articles that are no longer worth keeping.

    Two cutoffs:

    1. Any article older than ``article_age_days`` (by ``created_at``)
       is deleted regardless of status — digests are assembled from
       recent content only, so older rows just add DB weight.
    2. Any article older than ``unfetched_age_days`` whose fetch never
       started (``fetch_status == PENDING``) is deleted. These are
       typically dead URLs or sources that the fetcher could not reach
       in the active window and will never recover.

    Related rows (summaries, entities, embeddings, analyzer artefacts)
    are removed via ``on_delete=CASCADE``. Digest rows are unaffected
    because ``DigestStory`` references events, not articles.

    Args:
        article_age_days: Maximum age (in days) before an article is
            deleted regardless of status.
        unfetched_age_days: Maximum age (in days) for an article that
            has never started fetching.

    Returns:
        Summary dict with per-cutoff counts and total removed.
    """
    now = timezone.now()
    old_cutoff = now - timedelta(days=article_age_days)
    unfetched_cutoff = now - timedelta(days=unfetched_age_days)

    logger.info(
        "Starting cleanup_stale_articles (article_age_days=%s, unfetched_age_days=%s)",
        article_age_days,
        unfetched_age_days,
    )

    # Delete the unfetched-and-stuck set first so it doesn't double-count
    # against the general-age set.
    unfetched_qs = Article.objects.filter(
        fetch_status=FetchStatus.PENDING,
        created_at__lt=unfetched_cutoff,
    )
    unfetched_count = unfetched_qs.count()
    if unfetched_count:
        unfetched_qs.delete()

    old_qs = Article.objects.filter(created_at__lt=old_cutoff)
    old_count = old_qs.count()
    if old_count:
        old_qs.delete()

    total = unfetched_count + old_count
    logger.info(
        "cleanup_stale_articles removed %s articles (%s older than %sd, %s unfetched older than %sd)",
        total,
        old_count,
        article_age_days,
        unfetched_count,
        unfetched_age_days,
    )

    return {
        "success": True,
        "removed_total": total,
        "removed_older_than_days": old_count,
        "removed_unfetched_older_than_days": unfetched_count,
        "article_age_days": article_age_days,
        "unfetched_age_days": unfetched_age_days,
    }


@shared_task(name='articles.rebuild_headline_vectorizer')
def rebuild_headline_vectorizer() -> Dict[str, Any]:
    """Rebuild the TF-IDF vectorizer used for headline clustering.

    Runs daily to keep the vocabulary current with recent article titles.
    """
    from apps.articles.services.story_clustering import rebuild_vectorizer

    logger.info("Rebuilding headline TF-IDF vectorizer")
    rebuild_vectorizer()
    return {"success": True}


@shared_task(name='articles.expire_headline_clusters')
def expire_headline_clusters() -> Dict[str, Any]:
    """Expire old headline clusters that are past the active window.

    Runs every 4 hours to clean up clusters older than 12 hours.
    """
    from apps.articles.services.story_clustering import expire_old_clusters

    logger.info("Expiring old headline clusters")
    expired = expire_old_clusters()
    return {"success": True, "expired_count": expired}
