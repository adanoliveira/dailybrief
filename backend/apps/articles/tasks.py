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


@shared_task(name='articles.triage_pending_articles')
def triage_pending_articles(limit: int = 200) -> Dict[str, Any]:
    """Process articles pending triage decisions.

    Runs every 15 minutes via Celery Beat. Also auto-accepts any
    pending_llm articles older than 1 hour (better to process than miss).

    Args:
        limit: Maximum articles to triage in this batch.

    Returns:
        Summary dict with accepted/rejected/error counts.
    """
    from apps.articles.services.triage import ArticleTriage, LLM_TIMEOUT_HOURS

    triage = ArticleTriage()
    now = timezone.now()
    timeout_cutoff = now - timedelta(hours=LLM_TIMEOUT_HOURS)

    # Auto-accept timed-out articles first
    timed_out = Article.objects.filter(
        triage_status='pending_llm',
        triaged_at__lt=timeout_cutoff,
    )
    auto_accepted = timed_out.update(
        triage_status='accepted',
        triage_reason='timeout: pending_llm exceeded 1h, auto-accepted',
        triage_method='algorithmic',
        triaged_at=now,
    )
    if auto_accepted:
        logger.info("Auto-accepted %d timed-out pending_llm articles", auto_accepted)

    # Process pending articles through the next required tier:
    # - pending: Tier 1 (algorithmic)
    # - pending_llm: Tier 2 (LLM)
    pending = Article.objects.filter(
        triage_status__in=['pending', 'pending_llm'],
    ).select_related(
        'publication', 'headline_cluster',
    ).prefetch_related('topics').order_by(
        '-headline_score'  # Highest-scored ambiguous articles first
    )[:limit]

    accepted = 0
    rejected = 0
    errors = 0

    for article in pending:
        if article.triage_status == 'pending':
            tier1_result = triage.tier1_algorithmic(article)
            triage.apply_result(article, tier1_result)

            if tier1_result.status == 'accepted':
                accepted += 1
                continue
            if tier1_result.status == 'rejected':
                rejected += 1
                continue
            if tier1_result.status != 'pending_llm':
                errors += 1
                continue

        # Article is pending_llm (either originally or after Tier 1).
        result = triage.tier2_llm_classify(article)
        triage.apply_result(article, result)

        if result.status == 'accepted':
            accepted += 1
        elif result.status == 'rejected':
            rejected += 1
        else:
            errors += 1

    logger.info(
        "Triage batch: %d accepted, %d rejected, %d errors, %d auto-accepted (timeout)",
        accepted, rejected, errors, auto_accepted,
    )

    return {
        "success": True,
        "accepted": accepted,
        "rejected": rejected,
        "errors": errors,
        "auto_accepted_timeout": auto_accepted,
        "total_processed": accepted + rejected + errors,
    }
