"""
Article triage service — three-tier system for pipeline eligibility.

Determines which articles enter the expensive content enrichment pipeline
(fetch → process → summarize → analyze) using a cascading approach:

Tier 1 (Algorithmic, instant, $0):
    Auto-accept articles with headline_score >= ACCEPT_THRESHOLD
    Auto-reject articles with headline_score < REJECT_THRESHOLD
    Route ambiguous articles (between thresholds) to Tier 2

Tier 2 (LLM micro-classification, gpt-4.1-nano, ~$0.00005/article):
    Score articles on impact, novelty, significance using journalistic criteria
    Accept if composite score >= LLM_ACCEPT_THRESHOLD, reject otherwise

Tier 3 (Cluster promotion, async, $0):
    When a story cluster grows, rescue previously rejected articles
    if the cluster now indicates cross-source importance

Design principles:
    - Tier 1 handles ~60% of decisions (no cost, no latency)
    - Tier 2 handles ~35% (negligible cost, async)
    - Tier 3 handles ~5% (corrects false rejections)
    - Failures never block ingestion — articles stay 'pending'
    - Topic scarcity boosts underrepresented topics
"""

import json
import logging
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal

from django.db import models
from django.utils import timezone

logger = logging.getLogger(__name__)

# --- Tier 1 thresholds ---
ACCEPT_THRESHOLD = 0.75     # Auto-accept without LLM
REJECT_THRESHOLD = 0.35     # Auto-reject without LLM
TOPIC_SCARCITY_BONUS = 0.10 # Boost for topics with < 5 accepted articles today
TOPIC_SATURATION_PENALTY = 0.05  # Penalty for topics with > 30 accepted articles today

# --- Publisher volume controls (rolling 24h window) ---
PUBLISHER_VOLUME_SOFT_CAP = 10       # Start penalizing after this many accepted/24h
PUBLISHER_VOLUME_HARD_CAP = 25       # Auto-reject after this many accepted/24h
PUBLISHER_VOLUME_PENALTY_RATE = 0.02 # Score penalty per article above soft cap

# --- Tier 2 thresholds ---
LLM_ACCEPT_THRESHOLD = 0.55  # Composite (impact+novelty+significance)/30
LLM_DAILY_CAP = 1000         # Max LLM triage calls per day (cost guard)
LLM_TIMEOUT_HOURS = 1        # Auto-accept pending_llm articles older than this

# --- Tier 3 thresholds ---
PROMOTION_MIN_CLUSTER_SIZE = 3   # Minimum cluster size to trigger promotion
PROMOTION_MIN_SCORE = 0.45       # Floor score for promoted articles

# --- Prompt ---
TRIAGE_PROMPT_VERSION = "v1"
TRIAGE_PROMPT_TEMPLATE = """You are a news editor deciding whether an article should be included in a daily news digest for professionals.

Score this article on three dimensions (0-10 each):

IMPACT: How many people does this affect? Does it change money, policy, health, safety, or markets?
NOVELTY: Is this genuinely new information, or a routine update / rehash / promotional content?
SIGNIFICANCE: Will this still matter in a week? Does it represent a turning point or trend?

Article:
  Title: {title}
  Source: {source_name} (reputation: {authority_label})
  Description: {description}
  Topic: {topic_name}
  Published: {time_ago}
  Coverage: {cluster_size} source(s) covering this story

Respond ONLY with this JSON (no other text):
{{"impact": N, "novelty": N, "significance": N, "action": "process" or "skip", "reason": "one sentence"}}"""


@dataclass
class TriageResult:
    """Result of a triage decision."""
    status: str       # 'accepted', 'rejected', 'pending_llm'
    score: float | None
    reason: str
    method: str       # 'algorithmic', 'llm', 'cluster_promotion'
    cost_usd: Decimal | None = None


class ArticleTriage:
    """
    Three-tier article triage for pipeline eligibility.

    Usage:
        triage = ArticleTriage()

        # Tier 1 (inline during ingestion — instant)
        result = triage.tier1_algorithmic(article)
        article.triage_status = result.status
        article.save()

        # Tier 2 (async Celery task — for 'pending_llm' articles)
        result = triage.tier2_llm_classify(article)

        # Tier 3 (called from cluster promotion)
        triage.tier3_promote_from_cluster(cluster)
    """

    def __init__(self):
        self._daily_counts_cache = None
        self._daily_counts_date = None
        self._rolling_publisher_cache = None
        self._rolling_publisher_cache_key = None
        self._llm_calls_today = None

    def _invalidate_count_caches(self) -> None:
        """Invalidate cached topic/publisher counts used in triage decisions."""
        self._daily_counts_cache = None
        self._daily_counts_date = None
        self._rolling_publisher_cache = None
        self._rolling_publisher_cache_key = None

    def _publisher_hard_cap_reached(self, article) -> bool:
        """Return True when this article's publisher is already at hard cap in rolling 24h."""
        if not article.publication_id:
            return False
        counts = self._get_daily_publisher_counts()
        return counts.get(article.publication_id, 0) >= PUBLISHER_VOLUME_HARD_CAP

    # ------------------------------------------------------------------
    # Tier 1: Algorithmic pre-filter
    # ------------------------------------------------------------------

    def tier1_algorithmic(self, article) -> TriageResult:
        """
        Instant algorithmic triage. Runs inline during article ingestion.

        Returns:
            TriageResult with status 'accepted', 'rejected', or 'pending_llm'
        """
        score = article.headline_score

        # Apply title quality adjustment
        title_adj = self._title_quality_signals(article.title)
        adjusted_score = score + title_adj

        # Apply topic scarcity/saturation adjustment
        topic_ids = list(article.topics.values_list('id', flat=True))
        topic_adj = self._topic_scarcity_adjustment(topic_ids)
        adjusted_score += topic_adj

        # Apply publisher volume penalty so high-volume sources face stricter gates.
        pub_adj = self._publisher_volume_adjustment(article)
        if pub_adj <= -1.0:
            return TriageResult(
                status='rejected',
                score=adjusted_score,
                reason=f'publisher_cap: {PUBLISHER_VOLUME_HARD_CAP} accepted/24h exceeded',
                method='algorithmic',
            )
        adjusted_score += pub_adj

        # Decision
        if adjusted_score >= ACCEPT_THRESHOLD:
            return TriageResult(
                status='accepted',
                score=adjusted_score,
                reason=(
                    f'algorithmic_accept: score={adjusted_score:.3f} '
                    f'(headline={score:.3f}, title={title_adj:+.3f}, topic={topic_adj:+.3f}, pub={pub_adj:+.3f})'
                ),
                method='algorithmic',
            )
        elif adjusted_score < REJECT_THRESHOLD:
            return TriageResult(
                status='rejected',
                score=adjusted_score,
                reason=f'algorithmic_reject: score={adjusted_score:.3f} below floor {REJECT_THRESHOLD}',
                method='algorithmic',
            )
        else:
            return TriageResult(
                status='pending_llm',
                score=adjusted_score,
                reason=f'ambiguous: score={adjusted_score:.3f} in [{REJECT_THRESHOLD}, {ACCEPT_THRESHOLD})',
                method='algorithmic',
            )

    def _publisher_volume_adjustment(self, article) -> float:
        """
        Penalize/reject articles from high-volume publishers.

        Returns:
            0.0 for normal volume (rolling 24h)
            negative penalty above soft cap (rolling 24h)
            -1.0 to force rejection above hard cap (rolling 24h)
        """
        if not article.publication_id:
            return 0.0

        if self._publisher_hard_cap_reached(article):
            return -1.0

        counts = self._get_daily_publisher_counts()
        publisher_count = counts.get(article.publication_id, 0)
        if publisher_count > PUBLISHER_VOLUME_SOFT_CAP:
            over = publisher_count - PUBLISHER_VOLUME_SOFT_CAP
            return -(over * PUBLISHER_VOLUME_PENALTY_RATE)
        return 0.0

    def _title_quality_signals(self, title: str) -> float:
        """
        Compute title-based quality adjustment (-0.10 to +0.08).

        Positive signals: statistics/numbers, named entities
        Negative signals: clickbait questions, ALL CAPS, too short/vague
        """
        if not title:
            return -0.05

        adjustment = 0.0

        # Positive: contains statistics or monetary figures
        if re.search(r'\d+%|\$[\d.]+[BMK]?|R\$\s?[\d.,]+|\d+\s*(million|billion|milhão|bilhão)', title, re.IGNORECASE):
            adjustment += 0.05

        # Positive: contains 2+ proper nouns (named entities)
        proper_nouns = re.findall(r'\b[A-Z][a-záéíóúãõç]+(?:\s[A-Z][a-záéíóúãõç]+)*', title)
        if len(proper_nouns) >= 2:
            adjustment += 0.03

        # Negative: question headline (often clickbait)
        if title.rstrip().endswith('?'):
            adjustment -= 0.03

        # Negative: ALL CAPS words (tabloid style)
        caps_words = re.findall(r'\b[A-Z]{3,}\b', title)
        # Exclude common acronyms like USA, FBI, BBB, CEO, etc.
        non_acronym_caps = [w for w in caps_words if len(w) > 4]
        if non_acronym_caps:
            adjustment -= 0.05

        # Negative: too short / too vague
        if len(title) < 25:
            adjustment -= 0.05

        # Negative: listicle/compound title format
        if re.search(r'^\d+\s+(coisas|dicas|fatos|razões|things|tips|ways|reasons)\b', title, re.IGNORECASE):
            adjustment -= 0.03

        return max(-0.10, min(0.08, adjustment))

    def _topic_scarcity_adjustment(self, topic_ids: list[int]) -> float:
        """
        Boost underrepresented topics, penalize saturated ones.

        Uses cached daily counts to avoid per-article DB queries.
        """
        if not topic_ids:
            return 0.0

        counts = self._get_daily_topic_counts()
        adjustments = []

        for tid in topic_ids:
            count = counts.get(tid, 0)
            if count < 5:
                adjustments.append(TOPIC_SCARCITY_BONUS)
            elif count > 30:
                adjustments.append(-TOPIC_SATURATION_PENALTY)
            else:
                adjustments.append(0.0)

        # Use the best adjustment (most favorable topic)
        return max(adjustments) if adjustments else 0.0

    def _get_daily_topic_counts(self) -> dict[int, int]:
        """Return cached count of accepted articles per topic today."""
        from apps.articles.models import Article

        today = timezone.now().date()
        if self._daily_counts_cache and self._daily_counts_date == today:
            return self._daily_counts_cache

        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        counts = defaultdict(int)
        for row in Article.objects.filter(
            triage_status='accepted',
            triaged_at__gte=today_start,
        ).values('topics__id').annotate(
            cnt=models.Count('id', distinct=True),
        ):
            if row['topics__id']:
                counts[row['topics__id']] = row['cnt']

        self._daily_counts_cache = dict(counts)
        self._daily_counts_date = today
        return self._daily_counts_cache

    def _get_daily_publisher_counts(self) -> dict[int, int]:
        """Return cached count of accepted articles per publisher in the rolling last 24h."""
        from apps.articles.models import Article

        cache_key = timezone.now().replace(second=0, microsecond=0)
        if self._rolling_publisher_cache is not None and self._rolling_publisher_cache_key == cache_key:
            return self._rolling_publisher_cache

        window_start = timezone.now() - timedelta(hours=24)
        counts: dict[int, int] = {}
        for row in Article.objects.filter(
            triage_status='accepted',
            triaged_at__gte=window_start,
        ).values('publication_id').annotate(
            cnt=models.Count('id'),
        ):
            if row['publication_id']:
                counts[row['publication_id']] = row['cnt']

        self._rolling_publisher_cache = counts
        self._rolling_publisher_cache_key = cache_key
        return self._rolling_publisher_cache

    # ------------------------------------------------------------------
    # Tier 2: LLM micro-classification
    # ------------------------------------------------------------------

    def tier2_llm_classify(self, article) -> TriageResult:
        """
        LLM-based triage for ambiguous articles. Runs async in Celery.

        Uses gpt-4.1-nano (~$0.00005/article) to score on journalistic
        criteria: impact, novelty, significance.
        """
        # Enforce publisher hard cap consistently across tiers.
        if self._publisher_hard_cap_reached(article):
            return TriageResult(
                status='rejected',
                score=article.headline_score,
                reason=f'publisher_cap: {PUBLISHER_VOLUME_HARD_CAP} accepted/24h exceeded',
                method='algorithmic',
            )

        # Check daily LLM cap
        if self._get_llm_calls_today() >= LLM_DAILY_CAP:
            logger.warning("LLM triage daily cap reached, auto-accepting article %s", article.id)
            return TriageResult(
                status='accepted',
                score=article.headline_score,
                reason='llm_cap_reached: auto-accepted due to daily cap',
                method='algorithmic',
            )

        try:
            from apps.aiproviders.services import AIProviderService
            ai_service = AIProviderService()

            prompt = self._build_triage_prompt(article)
            response = ai_service.call_llm(
                prompt=prompt,
                operation='article_triage',
                max_tokens=100,
                temperature=0.1,
            )
            # Count attempted LLM calls in-process so the daily cap is enforced
            # within a single batch run as well.
            if self._llm_calls_today is None:
                self._llm_calls_today = self._get_llm_calls_today()
            self._llm_calls_today += 1

            if not response.success:
                logger.warning("LLM triage failed for article %s: %s", article.id, response.error_message)
                return TriageResult(
                    status='accepted',
                    score=article.headline_score,
                    reason=f'llm_error: {response.error_message[:100]}; auto-accepted',
                    method='algorithmic',
                )

            # Parse LLM response
            scores = self._parse_llm_response(response.content)
            if scores is None:
                return TriageResult(
                    status='accepted',
                    score=article.headline_score,
                    reason='llm_parse_error: could not parse response; auto-accepted',
                    method='algorithmic',
                )

            composite = (scores['impact'] + scores['novelty'] + scores['significance']) / 30.0
            action = 'accepted' if composite >= LLM_ACCEPT_THRESHOLD else 'rejected'
            cost = Decimal(str(response.usage.get('estimated_cost', 0))) if response.usage else None

            return TriageResult(
                status=action,
                score=composite,
                reason=f'llm_{action}: impact={scores["impact"]}, novelty={scores["novelty"]}, significance={scores["significance"]}; {scores.get("reason", "")}',
                method='llm',
                cost_usd=cost,
            )

        except Exception as e:
            logger.exception("LLM triage exception for article %s", article.id)
            return TriageResult(
                status='accepted',
                score=article.headline_score,
                reason=f'llm_exception: {str(e)[:100]}; auto-accepted',
                method='algorithmic',
            )

    def _build_triage_prompt(self, article) -> str:
        """Build the LLM prompt for article triage."""
        # Authority label
        authority = article.publication.authority if article.publication else 0
        if authority >= 8:
            authority_label = "major/authoritative"
        elif authority >= 6:
            authority_label = "established"
        elif authority >= 4:
            authority_label = "mid-tier"
        else:
            authority_label = "minor/unknown"

        # Topic name
        topics = list(article.topics.values_list('name', flat=True))
        topic_name = topics[0] if topics else 'Unknown'

        # Time ago
        age = timezone.now() - article.published_at
        if age.total_seconds() < 3600:
            time_ago = f"{int(age.total_seconds() / 60)} minutes ago"
        elif age.total_seconds() < 86400:
            time_ago = f"{int(age.total_seconds() / 3600)} hours ago"
        else:
            time_ago = f"{age.days} days ago"

        # Cluster size
        cluster_size = article.headline_cluster.article_count if article.headline_cluster else 1

        # Description (truncated)
        description = (article.description or '')[:300].strip()
        if not description:
            description = (article.title or '')

        return TRIAGE_PROMPT_TEMPLATE.format(
            title=article.title,
            source_name=article.source_name or (article.publication.name if article.publication else 'Unknown'),
            authority_label=authority_label,
            description=description,
            topic_name=topic_name,
            time_ago=time_ago,
            cluster_size=cluster_size,
        )

    def _parse_llm_response(self, content: str) -> dict | None:
        """Parse the JSON response from the LLM."""
        try:
            # Strip markdown code fences if present
            cleaned = content.strip()
            if cleaned.startswith('```'):
                cleaned = cleaned.split('\n', 1)[1] if '\n' in cleaned else cleaned[3:]
                if cleaned.endswith('```'):
                    cleaned = cleaned[:-3]
                cleaned = cleaned.strip()
            if cleaned.startswith('json'):
                cleaned = cleaned[4:].strip()

            data = json.loads(cleaned)

            # Validate required fields
            for key in ('impact', 'novelty', 'significance'):
                val = data.get(key)
                if not isinstance(val, (int, float)) or not (0 <= val <= 10):
                    logger.warning("Invalid LLM triage score: %s=%s", key, val)
                    return None

            return data

        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.warning("Failed to parse LLM triage response: %s — content: %s", e, content[:200])
            return None

    def _get_llm_calls_today(self) -> int:
        """Count LLM triage calls made today."""
        if self._llm_calls_today is not None:
            return self._llm_calls_today

        from apps.articles.models import Article
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        count = Article.objects.filter(
            triage_method='llm',
            triaged_at__gte=today_start,
        ).count()
        self._llm_calls_today = count
        return count

    # ------------------------------------------------------------------
    # Tier 3: Cluster promotion
    # ------------------------------------------------------------------

    @staticmethod
    def tier3_check_promotion(cluster) -> list:
        """
        Check if any rejected articles in this cluster should be promoted.

        Called from story_clustering._promote_cluster_articles() when a
        cluster grows.

        Returns list of article IDs that were promoted.
        """
        from apps.articles.models import Article

        if cluster.article_count < PROMOTION_MIN_CLUSTER_SIZE:
            return []

        # Already has a processed article? No need to promote
        has_processed = Article.objects.filter(
            headline_cluster=cluster,
            triage_status='accepted',
            analyzer_status='completed',
        ).exists()
        if has_processed:
            return []

        # Find rejected articles in this cluster above the promotion floor
        candidates = Article.objects.filter(
            headline_cluster=cluster,
            triage_status='rejected',
            headline_score__gte=PROMOTION_MIN_SCORE,
        ).order_by('-headline_score')

        promoted = []
        for article in candidates[:1]:  # Promote only the best one
            article.triage_status = 'promoted'
            article.triage_method = 'cluster_promotion'
            article.triage_reason = (
                f'cluster_promoted: cluster grew to {cluster.article_count} sources, '
                f'headline_score={article.headline_score:.3f}'
            )
            article.triaged_at = timezone.now()
            article.save(update_fields=[
                'triage_status', 'triage_method', 'triage_reason', 'triaged_at'
            ])
            promoted.append(article.id)
            logger.info(
                "Tier 3: Promoted article %s (score=%.3f) from cluster '%s' (%d sources)",
                article.id, article.headline_score,
                cluster.representative_title[:50],
                cluster.article_count,
            )

        return promoted

    # ------------------------------------------------------------------
    # Convenience: apply triage result to an article
    # ------------------------------------------------------------------

    def apply_result(self, article, result: TriageResult):
        """Apply a TriageResult to an article and save."""
        article.triage_status = result.status
        article.triage_score = result.score
        article.triage_reason = result.reason[:255]
        article.triage_method = result.method
        article.triage_cost_usd = result.cost_usd
        article.triaged_at = timezone.now()
        article.save(update_fields=[
            'triage_status', 'triage_score', 'triage_reason',
            'triage_method', 'triage_cost_usd', 'triaged_at',
        ])
        # Keep rolling counters fresh for subsequent decisions in the same batch.
        self._invalidate_count_caches()
