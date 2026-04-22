"""
Pipeline eligibility service — topic-aware dynamic threshold.

Determines which articles enter the content enrichment pipeline using
a global headline_score threshold with per-topic adjustments to
guarantee diversity:

- Topics with fewer than MIN_ARTICLES_PER_TOPIC articles above the
  global threshold get a lowered threshold (floor: TOPIC_FLOOR_THRESHOLD)
  so they're still represented in the digest.
- Topics with more than MAX_ARTICLES_PER_TOPIC articles above the
  threshold are capped — only the highest-scored articles proceed.

Additionally, cluster-based dedup prevents processing multiple versions
of the same story: if a cluster already has a fully-processed article,
new articles joining that cluster are skipped unless they score higher.
"""

import logging
from collections import defaultdict

from django.db import models
from django.utils import timezone

from apps.articles.models import Article, HeadlineCluster
from apps.articles.services.headline_scoring import (
    PUBLISHER_DAILY_SOFT_CAP,
    PUBLISHER_DIMINISHING_RATE,
)

logger = logging.getLogger(__name__)

# --- Pipeline processing threshold ---
# Higher than the ingestion threshold (0.60 in headline_scoring.py) which
# controls feed visibility. This threshold controls which articles enter
# the expensive AI processing pipeline (fetch → process → summarize → analyze).
PIPELINE_THRESHOLD = 0.70

# --- Topic diversity parameters ---

# Minimum articles per topic that should enter the pipeline daily.
# If a topic falls below this, the threshold is lowered for that topic.
MIN_ARTICLES_PER_TOPIC = 8

# Maximum articles per topic per day in the pipeline.
# Beyond this, only the highest-scored articles proceed.
MAX_ARTICLES_PER_TOPIC = 35

# Absolute floor — never accept articles below this score, even for
# underrepresented topics.
TOPIC_FLOOR_THRESHOLD = 0.45

# Region codes eligible for the pipeline
TARGET_REGION_CODES = ['us', 'br']


def get_eligible_article_ids(
    time_threshold,
    limit: int | None = None,
) -> list[int]:
    """
    Return IDs of articles eligible for the content enrichment pipeline.

    Applies three layers of filtering:

    1. **Global threshold** — only articles with headline_score >= HEADLINE_THRESHOLD
    2. **Topic diversity** — ensures MIN_ARTICLES_PER_TOPIC for underrepresented
       topics (by lowering threshold) and caps at MAX_ARTICLES_PER_TOPIC
    3. **Cluster dedup** — skips articles whose story cluster already has a
       fully-processed article (unless the new one scores higher)

    Returns a list of article IDs sorted by headline_score descending.
    """
    # Base pool: all scored articles in the time window and target regions
    base = Article.objects.filter(
        published_at__gte=time_threshold,
        regions__code__in=TARGET_REGION_CODES,
        headline_score__gt=0,
    ).exclude(
        # Already fully processed — don't re-enter
        analyzer_status='completed',
    ).select_related(
        'publication', 'headline_cluster',
    ).prefetch_related('topics').distinct()

    today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)

    # Count how many articles each publisher already has in the pipeline today
    publisher_daily_counts = dict(
        Article.objects.filter(
            is_top_headline=True,
            published_at__gte=today_start,
            analyzer_status='completed',
        ).values('publication_id').annotate(
            cnt=models.Count('id'),
        ).values_list('publication_id', 'cnt')
    )

    # Count articles already accepted per topic today
    topic_accepted_counts = defaultdict(int)
    for row in Article.objects.filter(
        is_top_headline=True,
        published_at__gte=today_start,
        analyzer_status='completed',
    ).values('topics__id').annotate(
        cnt=models.Count('id', distinct=True),
    ):
        if row['topics__id']:
            topic_accepted_counts[row['topics__id']] = row['cnt']

    # Clusters that already have a fully-processed article
    processed_clusters = set(
        Article.objects.filter(
            headline_cluster__isnull=False,
            analyzer_status='completed',
            published_at__gte=time_threshold,
        ).values_list('headline_cluster_id', flat=True).distinct()
    )

    # --- Scoring pass ---
    # Evaluate each article and decide accept/reject

    accepted = []  # [(article_id, effective_score, topic_ids)]
    topic_pending = defaultdict(list)  # topic_id → [(article_id, score)]

    for article in base.order_by('-headline_score').iterator(chunk_size=500):
        topic_ids = [t.id for t in article.topics.all()]
        pub_id = article.publication_id

        # Apply publisher diminishing returns
        pub_count = publisher_daily_counts.get(pub_id, 0)
        excess = max(0, pub_count - PUBLISHER_DAILY_SOFT_CAP)
        if excess > 0:
            penalty = max(1.0 - excess * PUBLISHER_DIMINISHING_RATE, 0.10)
            effective_score = article.headline_score * penalty
        else:
            effective_score = article.headline_score

        # Cluster dedup: skip if cluster already processed (unless this scores higher)
        if article.headline_cluster_id and article.headline_cluster_id in processed_clusters:
            # Check if this article scores higher than the processed one
            existing_best = Article.objects.filter(
                headline_cluster_id=article.headline_cluster_id,
                analyzer_status='completed',
            ).order_by('-headline_score').values_list('headline_score', flat=True).first()
            if existing_best and article.headline_score <= existing_best:
                continue  # Skip — cluster already has a better-scored processed article

        # Check global threshold
        if effective_score >= PIPELINE_THRESHOLD:
            # Check topic caps
            over_cap = False
            for tid in topic_ids:
                if topic_accepted_counts[tid] >= MAX_ARTICLES_PER_TOPIC:
                    over_cap = True
                    break
            if not over_cap:
                accepted.append((article.id, effective_score, topic_ids))
                publisher_daily_counts[pub_id] = pub_count + 1
                for tid in topic_ids:
                    topic_accepted_counts[tid] += 1
        else:
            # Below threshold — stash for potential topic rescue
            for tid in topic_ids:
                topic_pending[tid].append((article.id, effective_score))

    # --- Topic rescue pass ---
    # For topics below MIN_ARTICLES_PER_TOPIC, pull in the highest-scored
    # pending articles down to TOPIC_FLOOR_THRESHOLD
    for topic_id, pending in topic_pending.items():
        current_count = topic_accepted_counts.get(topic_id, 0)
        if current_count >= MIN_ARTICLES_PER_TOPIC:
            continue

        needed = MIN_ARTICLES_PER_TOPIC - current_count
        # Sort by score descending, take what we need above the floor
        candidates = sorted(pending, key=lambda x: -x[1])
        for article_id, score in candidates:
            if score < TOPIC_FLOOR_THRESHOLD:
                break
            if needed <= 0:
                break
            # Avoid duplicates
            if any(a_id == article_id for a_id, _, _ in accepted):
                continue
            accepted.append((article_id, score, [topic_id]))
            topic_accepted_counts[topic_id] += 1
            needed -= 1

    # Sort by effective score descending
    accepted.sort(key=lambda x: -x[1])

    ids = [a_id for a_id, _, _ in accepted]
    if limit:
        ids = ids[:limit]

    logger.info(
        f"Pipeline eligibility: {len(ids)} articles accepted "
        f"(threshold={PIPELINE_THRESHOLD}, topics={dict(topic_accepted_counts)})"
    )
    return ids
