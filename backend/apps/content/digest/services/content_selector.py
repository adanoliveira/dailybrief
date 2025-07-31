"""
Content Selection Service for Digest Generation.

Handles filtering articles by user preferences, grouping by topic and event,
and ranking events by importance for digest inclusion.
"""

import logging
from typing import List, Dict, Any, Tuple, Optional
from collections import defaultdict
from datetime import datetime, timedelta
from django.db.models import QuerySet, Q, Count, F, Sum, Case, When, IntegerField
from django.contrib.auth.models import User
from django.utils import timezone
import numpy as np

from apps.articles.models import Article, AnalyzerStatus, SummarizationStatus
from apps.feeds.models import UserTopic, Topic
from apps.content.analyzer.models import ArticleEvent, Event

logger = logging.getLogger(__name__)


class DigestContentSelector:
    """
    Service for selecting and ranking content for digest generation.
    
    Handles:
    - Filtering articles by user preferences and timeframe
    - Grouping articles by topic and primary events
    - Ranking events by article count and relevance
    - Content selection based on digest preferences
    """
    
    def __init__(self):
        self.logger = logger
    
    def _calculate_date_range_from_preferences(
        self,
        target_date: datetime.date,
        preferences: Dict[str, Any],
        user_timezone: str = 'UTC'
    ) -> Tuple[datetime, datetime]:
        """
        Calculate date range based on user preferences.
        
        Args:
            target_date: Target date for the digest
            preferences: User's digest preferences containing time_window setting
            user_timezone: User's timezone string
            
        Returns:
            Tuple of (start_time, end_time) in UTC for database queries
        """
        import pytz
        
        time_window = preferences.get('time_window', '48h')
        
        try:
            user_tz = pytz.timezone(user_timezone)
        except pytz.UnknownTimeZoneError:
            self.logger.warning(f"Unknown timezone {user_timezone}, using UTC")
            user_tz = pytz.UTC
        
        if time_window == 'full_previous_day':
            # Full previous day: 00:00 to 23:59:59 of the previous day in user's timezone
            previous_date = target_date - timedelta(days=1)
            start_time_local = user_tz.localize(
                datetime.combine(previous_date, datetime.min.time())
            )
            end_time_local = user_tz.localize(
                datetime.combine(previous_date, datetime.max.time())
            )
        elif time_window == 'full_previous_2_days':
            # Full previous 2 days: 00:00 two days ago to 23:59:59 of the previous day
            two_days_ago = target_date - timedelta(days=2)
            previous_date = target_date - timedelta(days=1)
            start_time_local = user_tz.localize(
                datetime.combine(two_days_ago, datetime.min.time())
            )
            end_time_local = user_tz.localize(
                datetime.combine(previous_date, datetime.max.time())
            )
        elif time_window == '24h':
            # Last 24 hours from end of target_date
            end_time_local = user_tz.localize(
                datetime.combine(target_date, datetime.max.time())
            )
            start_time_local = end_time_local - timedelta(hours=24)
            
            # Convert to UTC
            start_time_utc = start_time_local.astimezone(pytz.UTC)
            end_time_utc = end_time_local.astimezone(pytz.UTC)
            
            self.logger.info(
                f"Date range for digest ({time_window}): {start_time_utc} to {end_time_utc} "
                f"({start_time_local} to {end_time_local} in {user_timezone})"
            )
            return start_time_utc, end_time_utc
        elif time_window == '48h':
            # Last 48 hours from end of target_date
            end_time_local = user_tz.localize(
                datetime.combine(target_date, datetime.max.time())
            )
            start_time_local = end_time_local - timedelta(hours=48)
            
            # Convert to UTC
            start_time_utc = start_time_local.astimezone(pytz.UTC)
            end_time_utc = end_time_local.astimezone(pytz.UTC)
            
            self.logger.info(
                f"Date range for digest ({time_window}): {start_time_utc} to {end_time_utc} "
                f"({start_time_local} to {end_time_local} in {user_timezone})"
            )
            return start_time_utc, end_time_utc
        elif time_window == '72h':
            # Last 72 hours from end of target_date
            end_time_local = user_tz.localize(
                datetime.combine(target_date, datetime.max.time())
            )
            start_time_local = end_time_local - timedelta(hours=72)
            
            # Convert to UTC
            start_time_utc = start_time_local.astimezone(pytz.UTC)
            end_time_utc = end_time_local.astimezone(pytz.UTC)
            
            self.logger.info(
                f"Date range for digest ({time_window}): {start_time_utc} to {end_time_utc} "
                f"({start_time_local} to {end_time_local} in {user_timezone})"
            )
            return start_time_utc, end_time_utc
        else:
            # Default to 48h if unknown preference
            self.logger.warning(f"Unknown time_window preference: {time_window}, defaulting to 48h")
            end_date = datetime.combine(target_date, datetime.max.time())
            start_date = end_date - timedelta(hours=48)
        
        # Convert to UTC for database queries (for full day options)
        start_time_utc = start_time_local.astimezone(pytz.UTC)
        end_time_utc = end_time_local.astimezone(pytz.UTC)
        
        self.logger.info(
            f"Date range for digest ({time_window}): {start_time_utc} to {end_time_utc} "
            f"({start_time_local} to {end_time_local} in {user_timezone})"
        )
        
        return start_time_utc, end_time_utc
    
    def get_top_events_for_topic(
        self,
        topic: Topic,
        target_date: datetime.date,
        max_events: int = 3,
        user: Optional[User] = None,
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get top events for a specific topic based on article mentions.
        
        Now includes both primary events (from articles where this is the primary topic)
        and secondary events (mentioned in articles from this topic but not as primary).
        
        Args:
            topic: Topic to get events for
            target_date: Date to filter articles
            max_events: Maximum number of events to return
            user: User for personalization (optional)
            user_preferences: User's digest preferences (optional)
            
        Returns:
            List of event data dictionaries with articles and scores
        """
        logger.info(f"Getting top events for topic {topic.name} on {target_date}")
        
        # Calculate date range based on user preferences
        if user_preferences and user:
            user_timezone = user.profile.timezone if hasattr(user, 'profile') else 'UTC'
            start_date, end_date = self._calculate_date_range_from_preferences(
                target_date, user_preferences, user_timezone
            )
        else:
            # Fallback to default 48h window
            end_date = datetime.combine(target_date, datetime.max.time())
            start_date = end_date - timedelta(hours=48)
        
        # Get articles for this topic in the date range
        articles_query = Article.objects.filter(
            primary_topic=topic,  # Focus on articles where this is the primary topic
            published_at__gte=start_date,
            published_at__lte=end_date,
            analyzer_status='completed'  # Only fully processed articles
        ).select_related('primary_topic', 'primary_region', 'publication')
        
        # Filter by user's preferred regions if available
        if user and hasattr(user, 'preferred_regions'):
            user_region_relations = user.preferred_regions.all()
            if user_region_relations.exists():
                user_regions = [ur.region for ur in user_region_relations]
                articles_query = articles_query.filter(regions__in=user_regions).distinct()
        
        articles = list(articles_query)
        
        if not articles:
            logger.info(f"No articles found for topic {topic.name} on {target_date}")
            return []
        
        logger.info(f"Found {len(articles)} articles for topic {topic.name}")
        
        # Group articles by both primary and secondary events
        event_groups = self._group_articles_by_primary_and_secondary_events(articles)
        
        if not event_groups:
            logger.info(f"No events found for articles in topic {topic.name}")
            return []
        
        # Score and rank events
        scored_events = []
        for event_id, event_data in event_groups.items():
            if not event_data['event']:  # Skip if no event
                continue
            
            score = self._calculate_comprehensive_event_score_with_clusters(event_data, event_groups)
            
            scored_events.append({
                'event': event_data['event'],
                'articles': event_data['primary_articles'] + event_data['secondary_articles'],
                'score': score,
                'primary_mentions': len(event_data['primary_articles']),
                'secondary_mentions': len(event_data['secondary_articles'])
            })
        
        # Sort by score (highest first) and return top events
        scored_events.sort(key=lambda x: x['score'], reverse=True)
        top_events = scored_events[:max_events]
        
        logger.info(f"Selected {len(top_events)} top events for topic {topic.name}")
        for i, event_data in enumerate(top_events):
            logger.info(f"  {i+1}. {event_data['event'].title} (score: {event_data['score']})")
        
        return top_events
    
    def get_topic_articles_for_fallback_digest(
        self,
        topic: Topic,
        target_date: datetime.date,
        max_articles: int = 30,  # Feed all available articles to LLM (up to 30)
        user: Optional[User] = None,
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> List[Article]:
        """
        Fallback method to get articles for a topic when no events are available.
        
        This is used when event-based digest generation fails, providing a 
        simple article-based digest using article summaries.
        
        Args:
            topic: Topic to get articles for
            target_date: Date to filter articles
            max_articles: Maximum number of articles to return
            user: User for personalization (optional)
            user_preferences: User's digest preferences (optional)
            
        Returns:
            List of articles with summaries, ordered by relevance
        """
        logger.info(f"Fallback: Getting articles for topic {topic.name} on {target_date}")
        
        # Calculate date range based on user preferences
        if user_preferences and user:
            user_timezone = user.profile.timezone if hasattr(user, 'profile') else 'UTC'
            start_date, end_date = self._calculate_date_range_from_preferences(
                target_date, user_preferences, user_timezone
            )
        else:
            # Fallback to default 48h window
            end_date = datetime.combine(target_date, datetime.max.time())
            start_date = end_date - timedelta(hours=48)
        
        # Get articles for this topic in the date range
        # Try primary_topic first, fallback to topics many-to-many if needed
        articles_query = Article.objects.filter(
            published_at__gte=start_date,
            published_at__lte=end_date,
            analyzer_status='completed',
            summarization_status='completed'  # Only articles with summaries
        ).select_related('primary_topic', 'primary_region', 'publication', 'structured_summary')
        
        # Filter by topic - try primary_topic first
        primary_topic_articles = articles_query.filter(primary_topic=topic)
        
        if primary_topic_articles.exists():
            articles_query = primary_topic_articles
            logger.info(f"Using primary_topic filter for {topic.name}")
        else:
            # Fallback to many-to-many topics field
            articles_query = articles_query.filter(topics=topic)
            logger.info(f"Fallback to topics many-to-many for {topic.name}")
        
        # Filter by user's preferred regions if available
        if user and hasattr(user, 'preferred_regions'):
            user_region_relations = user.preferred_regions.all()
            if user_region_relations.exists():
                user_regions = [ur.region for ur in user_region_relations]
                # Always use regions many-to-many field
                articles_query = articles_query.filter(regions__in=user_regions).distinct()
                logger.info(f"Filtered by user's preferred regions via regions field")
        
        # Filter by user's preferred languages if available
        if user and hasattr(user, 'preferred_languages'):
            user_language_relations = user.preferred_languages.all()
            if user_language_relations.exists():
                user_languages = [ul.language for ul in user_language_relations]
                articles_query = articles_query.filter(language__in=user_languages)
        
        # Only include articles that have structured summaries
        articles_query = articles_query.filter(structured_summary__isnull=False)
        
        # Order by published date (most recent first) and limit results
        articles = list(articles_query.order_by('-published_at')[:max_articles])
        
        if not articles:
            logger.info(f"No articles with summaries found for topic {topic.name} on {target_date}")
            return []
        
        logger.info(f"Found {len(articles)} articles with summaries for topic {topic.name}")
        for article in articles:
            logger.info(f"  - {article.title[:50]}... ({article.published_at})")
        
        return articles
    
    def _group_articles_by_primary_and_secondary_events(self, articles: List[Article]) -> Dict[int, Dict[str, Any]]:
        """
        Group articles by both their primary and secondary events.
        
        Args:
            articles: List of articles to group
            
        Returns:
            Dictionary mapping event_id to event data with primary and secondary articles
        """
        event_groups = defaultdict(lambda: {
            'event': None,
            'primary_articles': [],
            'secondary_articles': []
        })
        
        for article in articles:
            # Process primary event
            try:
                primary_event_link = ArticleEvent.objects.filter(
                    article=article,
                    is_primary=True
                ).select_related('event').first()
                
                if primary_event_link:
                    event_id = primary_event_link.event.id
                    if not event_groups[event_id]['event']:
                        event_groups[event_id]['event'] = primary_event_link.event
                    event_groups[event_id]['primary_articles'].append(article)
                
            except Exception as e:
                logger.warning(f"Error getting primary event for article {article.id}: {e}")
            
            # Process secondary events
            try:
                secondary_event_links = ArticleEvent.objects.filter(
                    article=article,
                    is_primary=False
                ).select_related('event')
                
                for secondary_link in secondary_event_links:
                    event_id = secondary_link.event.id
                    if not event_groups[event_id]['event']:
                        event_groups[event_id]['event'] = secondary_link.event
                    
                    # Only add to secondary if not already in primary for this event
                    if article not in event_groups[event_id]['primary_articles']:
                        event_groups[event_id]['secondary_articles'].append(article)
                
            except Exception as e:
                logger.warning(f"Error getting secondary events for article {article.id}: {e}")
        
        # Remove events with no articles
        filtered_groups = {
            event_id: event_data 
            for event_id, event_data in event_groups.items() 
            if event_data['primary_articles'] or event_data['secondary_articles']
        }
        
        logger.info(f"Found {len(filtered_groups)} events (primary + secondary) from {len(articles)} articles")
        
        return filtered_groups
    
    def _calculate_comprehensive_event_score(self, event_data: Dict[str, Any]) -> int:
        """
        Calculate importance score for an event based on both primary and secondary mentions.
        
        Score = primary_mentions * 2 + secondary_mentions * 1
        
        Args:
            event_data: Event data with primary and secondary articles
            
        Returns:
            Calculated score
        """
        primary_count = len(event_data['primary_articles'])
        secondary_count = len(event_data['secondary_articles'])
        
        # Same scoring as before: primary mentions weighted higher
        total_score = (primary_count * 2) + (secondary_count * 1)
        
        return total_score

    def _calculate_comprehensive_event_score_with_clusters(
        self, 
        event_data: Dict[str, Any], 
        all_events_data: Dict[int, Dict[str, Any]],
        cluster_distance_threshold: float = 0.30
    ) -> float:
        """
        Calculate importance score for an event including cluster boost from related events.
        
        Score = (primary_mentions * 2) + (secondary_mentions * 1) + (related_events * 0.5)
        
        Args:
            event_data: Event data with primary and secondary articles
            all_events_data: All events data for finding clusters
            cluster_distance_threshold: Distance threshold for related events (default: 0.30)
            
        Returns:
            Calculated score with cluster boost
        """
        primary_count = len(event_data['primary_articles'])
        secondary_count = len(event_data['secondary_articles'])
        
        # Base score: same as before
        base_score = (primary_count * 2) + (secondary_count * 1)
        
        # Find related events using semantic similarity
        target_articles = event_data['primary_articles'] + event_data['secondary_articles']
        related_events_count = self._count_related_events(
            target_event=event_data['event'],
            target_articles=target_articles,
            distance_threshold=cluster_distance_threshold
        )
        
        # Cluster boost: 0.5 points per related event
        cluster_boost = related_events_count * 0.5
        
        total_score = base_score + cluster_boost
        
        logger.info(
            f"Event '{event_data['event'].title[:50]}...': "
            f"base={base_score} + cluster_boost={cluster_boost:.1f} "
            f"({related_events_count} related) = {total_score:.1f}"
        )
        
        return total_score

    def _count_related_events(
        self, 
        target_event: 'Event', 
        target_articles: List[Article],
        distance_threshold: float = 0.30,
        digest_window_hours: int = 48
    ) -> int:
        """
        Count events that are semantically related to the target event.
        
        Considers all events from the digest window (cross-topic) but excludes
        events that share articles with the target event to avoid artificial clustering.
        
        Args:
            target_event: Event to find related events for
            target_articles: Articles associated with the target event
            distance_threshold: Semantic distance threshold for relatedness
            digest_window_hours: Hours to look back for related events
            
        Returns:
            Number of related events found
        """
        if target_event.centroid_embed is None or len(target_event.centroid_embed) == 0:
            return 0
        
        from django.utils import timezone
        from datetime import timedelta
        
        # Get all recent events from the digest window (cross-topic)
        cutoff_time = timezone.now() - timedelta(hours=digest_window_hours)
        recent_events = Event.objects.filter(
            last_seen_at__gte=cutoff_time,
            centroid_embed__isnull=False
        ).exclude(id=target_event.id)
        
        # Get article IDs associated with target event to exclude shared articles
        target_article_ids = set(article.id for article in target_articles)
        
        related_count = 0
        target_embedding = np.array(target_event.centroid_embed)
        
        for other_event in recent_events:
            # Skip events without embeddings (double-check)
            if other_event.centroid_embed is None or len(other_event.centroid_embed) == 0:
                continue
            
            # Check if this event shares any articles with target event
            other_event_article_ids = set(
                ArticleEvent.objects.filter(event=other_event)
                .values_list('article_id', flat=True)
            )
            
            # Skip if events share articles (would be artificial clustering)
            if target_article_ids.intersection(other_event_article_ids):
                continue
            
            # Calculate semantic distance using cosine similarity (same as event creation pipeline)
            other_embedding = np.array(other_event.centroid_embed)
            
            # Calculate cosine similarity manually (same logic as analyzer service)
            cosine_sim = np.dot(target_embedding, other_embedding) / (
                np.linalg.norm(target_embedding) * np.linalg.norm(other_embedding)
            )
            cosine_distance = 1 - cosine_sim
            
            # Count as related if within threshold (same as event creation pipeline)
            if cosine_distance < distance_threshold:
                related_count += 1
                logger.info(
                    f"  Related event found: '{other_event.title[:40]}...' "
                    f"(cosine_distance: {cosine_distance:.3f})"
                )
        
        return related_count
    
    def get_user_articles(
        self,
        user: User,
        start_date: datetime,
        end_date: datetime,
        followed_topics_only: bool = True
    ) -> List[Article]:
        """
        Get articles relevant to a user based on their preferences.
        
        Args:
            user: User to get articles for
            start_date: Start of date range
            end_date: End of date range
            followed_topics_only: Whether to filter by user's followed topics
            
        Returns:
            List of relevant articles
        """
        query = Article.objects.filter(
            published_at__gte=start_date,
            published_at__lte=end_date,
            analyzer_status='completed'
        ).select_related('primary_topic', 'primary_region', 'publication')
        
        # Filter by user's followed topics
        if followed_topics_only:
            user_topics = UserTopic.objects.filter(user=user).values_list('topic', flat=True)
            if user_topics:
                query = query.filter(primary_topic__in=user_topics)
            else:
                # User has no followed topics, return empty list
                return []
        
        # Filter by user's preferred regions if available
        if hasattr(user, 'preferred_regions'):
            user_region_relations = user.preferred_regions.all()
            if user_region_relations.exists():
                user_regions = [ur.region for ur in user_region_relations]
                query = query.filter(regions__in=user_regions).distinct()
        
        # Filter by user's preferred languages if available
        if hasattr(user, 'preferred_languages'):
            user_language_relations = user.preferred_languages.all()
            if user_language_relations.exists():
                user_languages = [ul.language for ul in user_language_relations]
                query = query.filter(language__in=user_languages)
        
        return list(query.order_by('-published_at'))
    
    def filter_articles_by_timeframe(
        self,
        target_date: datetime.date,
        hours: int = None,
        user_preferences: Optional[Dict[str, Any]] = None,
        user_timezone: str = 'UTC'
    ) -> Q:
        """
        Create Q object for filtering articles by timeframe.
        
        Args:
            target_date: Target date
            hours: Number of hours to look back (legacy parameter)
            user_preferences: User's digest preferences (optional)
            user_timezone: User's timezone string
            
        Returns:
            Q object for filtering
        """
        if user_preferences:
            # Use preferences-based date range calculation
            start_time, end_time = self._calculate_date_range_from_preferences(
                target_date, user_preferences, user_timezone
            )
        elif hours is not None:
            # Legacy hours-based calculation
            end_time = datetime.combine(target_date, datetime.max.time())
            start_time = end_time - timedelta(hours=hours)
        else:
            # Default to 48h window
            end_time = datetime.combine(target_date, datetime.max.time())
            start_time = end_time - timedelta(hours=48)
        
        return Q(
            published_at__gte=start_time,
            published_at__lte=end_time
        )
    
    def get_event_article_mentions(self, event: Event, hours: int = 24) -> Dict[str, List[Article]]:
        """
        Get all articles that mention an event, separated by mention type.
        
        Args:
            event: Event to get mentions for
            hours: Hours to look back from now
            
        Returns:
            Dictionary with 'primary' and 'secondary' article lists
        """
        cutoff_time = timezone.now() - timedelta(hours=hours)
        
        # Get primary mentions
        primary_article_events = ArticleEvent.objects.filter(
            event=event,
            is_primary=True,
            article__published_at__gte=cutoff_time
        ).select_related('article')
        
        primary_articles = [ae.article for ae in primary_article_events]
        
        # Get secondary mentions
        secondary_article_events = ArticleEvent.objects.filter(
            event=event,
            is_primary=False,
            article__published_at__gte=cutoff_time
        ).select_related('article')
        
        secondary_articles = [ae.article for ae in secondary_article_events]
        
        return {
            'primary': primary_articles,
            'secondary': secondary_articles
        }
    
    def get_trending_events(
        self,
        topic: Optional[Topic] = None,
        hours: int = 24,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get trending events based on recent article mentions.
        
        Args:
            topic: Optional topic filter
            hours: Hours to look back
            limit: Maximum number of events to return
            
        Returns:
            List of event data with scores and article counts
        """
        cutoff_time = timezone.now() - timedelta(hours=hours)
        
        # Build base query
        query = ArticleEvent.objects.filter(
            article__published_at__gte=cutoff_time,
            article__analyzer_status='completed'
        )
        
        # Filter by topic if specified
        if topic:
            query = query.filter(article__primary_topic=topic)
        
        # Aggregate mentions by event
        event_stats = query.values('event').annotate(
            primary_count=Count('id', filter=Q(is_primary=True)),
            secondary_count=Count('id', filter=Q(is_primary=False)),
            total_score=F('primary_count') * 2 + F('secondary_count')
        ).order_by('-total_score')[:limit]
        
        # Get full event objects and format results
        trending_events = []
        for stats in event_stats:
            try:
                event = Event.objects.get(id=stats['event'])
                trending_events.append({
                    'event': event,
                    'primary_mentions': stats['primary_count'],
                    'secondary_mentions': stats['secondary_count'],
                    'score': stats['total_score']
                })
            except Event.DoesNotExist:
                continue
        
        return trending_events
    
    def group_articles_by_topic_and_event(self, articles: QuerySet[Article]) -> Dict[int, Dict[str, Any]]:
        """
        Group articles by (topic, primary_event) combinations.
        
        Creates a nested structure organizing articles by their primary topic,
        then by their primary events within each topic. Also tracks secondary
        events for comprehensive event coverage.
        
        Args:
            articles: QuerySet of articles to group
            
        Returns:
            Dictionary structure:
            {
                topic_id: {
                    'topic': Topic instance,
                    'events': {
                        event_id: {
                            'event': Event instance,
                            'primary_articles': [Article, ...],
                            'secondary_articles': [Article, ...],
                            'total_articles': int,
                            'score': float
                        }
                    }
                }
            }
        """
        grouped = defaultdict(lambda: {
            'topic': None, 
            'events': defaultdict(lambda: {
                'event': None,
                'primary_articles': [],
                'secondary_articles': [],
                'total_articles': 0,
                'score': 0.0
            })
        })
        
        articles_processed = 0
        
        for article in articles:
            articles_processed += 1
            topic_id = article.primary_topic_id
            
            # Set topic reference
            if not grouped[topic_id]['topic']:
                grouped[topic_id]['topic'] = article.primary_topic
            
            # Process primary event
            primary_event_relation = article.article_events.filter(is_primary=True).first()
            if primary_event_relation:
                event_id = primary_event_relation.event_id
                event_data = grouped[topic_id]['events'][event_id]
                
                if not event_data['event']:
                    event_data['event'] = primary_event_relation.event
                
                event_data['primary_articles'].append(article)
                event_data['total_articles'] += 1
            
            # Process secondary events
            secondary_relations = article.article_events.filter(is_primary=False)
            for relation in secondary_relations:
                event_id = relation.event_id
                event_data = grouped[topic_id]['events'][event_id]
                
                if not event_data['event']:
                    event_data['event'] = relation.event
                
                # Only add to secondary if not already in primary
                if article not in event_data['primary_articles']:
                    event_data['secondary_articles'].append(article)
                    event_data['total_articles'] += 1
        
        # Calculate scores for all events
        for topic_data in grouped.values():
            for event_data in topic_data['events'].values():
                event_data['score'] = self.calculate_event_score(event_data)
        
        self.logger.info(
            f"Grouped {articles_processed} articles into "
            f"{len(grouped)} topics with "
            f"{sum(len(topic_data['events']) for topic_data in grouped.values())} total events"
        )
        
        return dict(grouped)
    
    def calculate_event_score(self, event_data: Dict[str, Any]) -> float:
        """
        Calculate event importance score.
        
        Uses the scoring formula: (primary_articles × 2.0) + (secondary_articles × 1.0)
        This gives more weight to events that are the primary focus of articles.
        
        Args:
            event_data: Event data dictionary with primary and secondary articles
            
        Returns:
            Calculated event score (higher = more important)
        """
        primary_count = len(event_data['primary_articles'])
        secondary_count = len(event_data['secondary_articles'])
        
        score = (primary_count * 2.0) + (secondary_count * 1.0)
        
        return score
    
    def select_digest_content(
        self, 
        grouped_data: Dict[int, Dict[str, Any]], 
        user_preferences: Dict[str, Any]
    ) -> Dict[int, Dict[str, Any]]:
        """
        Select final content for digest based on user preferences.
        
        Implements the selection algorithm:
        1. Rank topics by total event score
        2. Select top N topics (max 4, configurable)
        3. For each topic, select top M events (max 3, configurable)
        4. Return structured data ready for AI processing
        
        Args:
            grouped_data: Output from group_articles_by_topic_and_event
            user_preferences: User's digest preferences
            
        Returns:
            Structured digest content ready for AI generation
        """
        max_topics = user_preferences.get('max_topics', 4)
        max_events_per_topic = user_preferences.get('max_events_per_topic', 3)
        
        # Rank topics by total score
        topic_scores = []
        for topic_id, topic_data in grouped_data.items():
            total_score = sum(
                event_data['score'] 
                for event_data in topic_data['events'].values()
            )
            if total_score > 0:  # Only include topics with events
                topic_scores.append((topic_id, topic_data, total_score))
        
        # Sort by score and take top topics
        topic_scores.sort(key=lambda x: x[2], reverse=True)
        selected_topics = topic_scores[:max_topics]
        
        self.logger.info(
            f"Selected {len(selected_topics)} topics from {len(topic_scores)} candidates"
        )
        
        # For each selected topic, rank and select events
        digest_content = {}
        for topic_id, topic_data, topic_score in selected_topics:
            # Rank events within topic
            event_scores = [
                (event_id, event_data, event_data['score'])
                for event_id, event_data in topic_data['events'].items()
                if event_data['score'] > 0  # Only include events with articles
            ]
            event_scores.sort(key=lambda x: x[2], reverse=True)
            
            # Select top events
            selected_events = event_scores[:max_events_per_topic]
            
            digest_content[topic_id] = {
                'topic': topic_data['topic'],
                'total_score': topic_score,
                'events': [
                    {
                        'event': event_data['event'],
                        'primary_articles': event_data['primary_articles'],
                        'secondary_articles': event_data['secondary_articles'],
                        'score': event_data['score'],
                        'recommended_articles': self.select_recommended_articles(
                            event_data['primary_articles'] + event_data['secondary_articles']
                        )
                    }
                    for event_id, event_data, score in selected_events
                ]
            }
            
            self.logger.info(
                f"Topic '{topic_data['topic'].name}': "
                f"selected {len(selected_events)} events (score: {topic_score:.1f})"
            )
        
        return digest_content
    
    def select_recommended_articles(self, articles: List[Article], count: int = 3) -> List[Article]:
        """
        Select most recent/relevant articles for deep-dive recommendations.
        
        Selection criteria:
        1. Most recently published
        2. Has complete processing (summaries available)
        3. Variety in sources when possible
        
        Args:
            articles: List of articles to select from
            count: Number of articles to recommend (default 3)
            
        Returns:
            List of recommended articles for further reading
        """
        if not articles:
            return []
        
        # Filter to ensure articles have summaries
        articles_with_summaries = [
            article for article in articles 
            if hasattr(article, 'structured_summary') and article.structured_summary
        ]
        
        if not articles_with_summaries:
            # Fallback to any articles if none have summaries
            articles_with_summaries = articles
        
        # Sort by publication date (most recent first)
        sorted_articles = sorted(
            articles_with_summaries, 
            key=lambda a: a.published_at, 
            reverse=True
        )
        
        # Select top articles, trying to diversify sources
        recommended = []
        used_sources = set()
        
        for article in sorted_articles:
            if len(recommended) >= count:
                break
                
            source_name = article.publication.name if article.publication else article.source_name
            
            # Prefer different sources for variety
            if source_name not in used_sources or len(recommended) == 0:
                recommended.append(article)
                used_sources.add(source_name)
        
        # If we don't have enough articles with diverse sources, fill with most recent
        if len(recommended) < count:
            for article in sorted_articles:
                if len(recommended) >= count:
                    break
                if article not in recommended:
                    recommended.append(article)
        
        self.logger.debug(
            f"Selected {len(recommended)} recommended articles from {len(articles)} candidates"
        )
        
        return recommended[:count]
    
    def get_date_range_for_digest(
        self, 
        target_date: datetime, 
        user_timezone: str = 'UTC',
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> Tuple[datetime, datetime]:
        """
        Calculate the date range for digest content.
        
        Args:
            target_date: The date the digest is for
            user_timezone: User's timezone string
            user_preferences: User's digest preferences (optional)
            
        Returns:
            Tuple of (start_time, end_time) in UTC for database queries
        """
        if user_preferences:
            # Use new preferences-based approach
            return self._calculate_date_range_from_preferences(
                target_date.date(), user_preferences, user_timezone
            )
        
        # Legacy fallback: 24-hour window from 6 AM yesterday to 6 AM today
        import pytz
        
        try:
            user_tz = pytz.timezone(user_timezone)
        except pytz.UnknownTimeZoneError:
            self.logger.warning(f"Unknown timezone {user_timezone}, using UTC")
            user_tz = pytz.UTC
        
        # 6 AM on the target date in user's timezone
        end_time_local = user_tz.localize(
            datetime.combine(target_date.date(), datetime.min.time().replace(hour=6))
        )
        
        # 6 AM on the previous day in user's timezone
        start_time_local = end_time_local - timedelta(days=1)
        
        # Convert to UTC for database queries
        start_time_utc = start_time_local.astimezone(pytz.UTC)
        end_time_utc = end_time_local.astimezone(pytz.UTC)
        
        self.logger.info(
            f"Date range for digest (legacy): {start_time_utc} to {end_time_utc} "
            f"({start_time_local} to {end_time_local} in {user_timezone})"
        )
        
        return start_time_utc, end_time_utc
    
    def enhance_event_with_related_articles(
        self,
        event: 'Event',
        primary_articles: List[Article],
        secondary_articles: List[Article],
        digest_window_hours: int = 48
    ) -> Dict[str, Any]:
        """
        Enhance an event summary using primary, secondary, and related articles.
        
        Args:
            event: Event to enhance
            primary_articles: Articles where this is the primary event
            secondary_articles: Articles where this is a secondary event
            digest_window_hours: Hours to look back for related articles
            
        Returns:
            Dict with enhancement results and metadata
        """
        from django.utils import timezone
        from datetime import timedelta
        
        # Check if enhancement is needed
        all_article_ids = sorted([a.id for a in primary_articles + secondary_articles])
        
        # Skip if already enhanced with same articles recently (within 6 hours)
        if (event.last_enhanced_at and 
            event.enhanced_article_ids == all_article_ids and
            timezone.now() - event.last_enhanced_at < timedelta(hours=6)):
            
            logger.info(f"Event '{event.title}' already enhanced with same articles, skipping")
            return {
                'enhanced': False,
                'reason': 'already_enhanced',
                'enhanced_abstract': event.enhanced_abstract,
                'enhanced_facts': event.enhanced_facts,
                'enhanced_perspectives': event.enhanced_perspectives,
                'cost': 0
            }
        
        # Find related articles from semantically similar events
        related_articles = self._find_related_articles_for_event(
            event, 
            exclude_article_ids=all_article_ids,
            digest_window_hours=digest_window_hours
        )
        
        logger.info(
            f"Enhancing event '{event.title}' with {len(primary_articles)} primary, "
            f"{len(secondary_articles)} secondary, {len(related_articles)} related articles"
        )
        
        # Prepare event data for AI enhancement
        event_data = {
            'event': event,
            'primary_articles': primary_articles,
            'secondary_articles': secondary_articles,
            'related_articles': related_articles
        }
        
        # Generate enhanced summary using AI
        from apps.content.digest.services.ai_generator import DigestAIGenerator
        ai_generator = DigestAIGenerator()
        
        enhancement_result = ai_generator.enhance_event_summary_with_related(event_data)
        
        # Save enhanced summary to database
        if enhancement_result.get('enhanced_abstract'):
            event.enhanced_abstract = enhancement_result['enhanced_abstract']
            event.enhanced_facts = enhancement_result.get('key_facts', [])
            event.enhanced_perspectives = enhancement_result.get('perspectives', [])
            event.last_enhanced_at = timezone.now()
            event.enhanced_article_ids = all_article_ids
            event.enhancement_cost_usd = enhancement_result.get('cost', 0)
            event.save()
            
            logger.info(
                f"Saved enhanced summary for event '{event.title}': "
                f"{len(event.enhanced_facts)} facts, {len(event.enhanced_perspectives)} perspectives"
            )
        
        return {
            'enhanced': True,
            'enhanced_abstract': enhancement_result.get('enhanced_abstract', ''),
            'enhanced_facts': enhancement_result.get('key_facts', []),
            'enhanced_perspectives': enhancement_result.get('perspectives', []),
            'cost': enhancement_result.get('cost', 0),
            'articles_used': enhancement_result.get('articles_used', 0),
            'primary_count': enhancement_result.get('primary_count', 0),
            'secondary_count': enhancement_result.get('secondary_count', 0),
            'related_count': enhancement_result.get('related_count', 0)
        }
    
    def _find_related_articles_for_event(
        self,
        target_event: 'Event',
        exclude_article_ids: List[int],
        digest_window_hours: int = 48,
        distance_threshold: float = 0.30,
        max_related_articles: int = 3
    ) -> List[Article]:
        """
        Find articles from related events to provide additional context.
        
        Args:
            target_event: Event to find related articles for
            exclude_article_ids: Article IDs to exclude (already used)
            digest_window_hours: Hours to look back
            distance_threshold: Semantic distance threshold for relatedness
            max_related_articles: Maximum related articles to return
            
        Returns:
            List of related articles
        """
        if target_event.centroid_embed is None or len(target_event.centroid_embed) == 0:
            return []
        
        from django.utils import timezone
        from datetime import timedelta
        import numpy as np
        
        # Get recent events within digest window
        cutoff_time = timezone.now() - timedelta(hours=digest_window_hours)
        recent_events = Event.objects.filter(
            last_seen_at__gte=cutoff_time,
            centroid_embed__isnull=False
        ).exclude(id=target_event.id)
        
        related_articles = []
        target_embedding = np.array(target_event.centroid_embed)
        
        for other_event in recent_events:
            if other_event.centroid_embed is None or len(other_event.centroid_embed) == 0:
                continue
            
            # Calculate cosine distance (same as event clustering)
            other_embedding = np.array(other_event.centroid_embed)
            cosine_sim = np.dot(target_embedding, other_embedding) / (
                np.linalg.norm(target_embedding) * np.linalg.norm(other_embedding)
            )
            cosine_distance = 1 - cosine_sim
            
            # If events are related, get some articles from the related event
            if cosine_distance < distance_threshold:
                # Get articles from related event (excluding already used ones)
                event_articles = ArticleEvent.objects.filter(
                    event=other_event
                ).exclude(
                    article_id__in=exclude_article_ids
                ).select_related('article').order_by('-relevance_score')[:2]  # Max 2 per related event
                
                for article_event in event_articles:
                    if len(related_articles) >= max_related_articles:
                        break
                    related_articles.append(article_event.article)
                
                if len(related_articles) >= max_related_articles:
                    break
        
        logger.info(f"Found {len(related_articles)} related articles for event '{target_event.title}'")
        return related_articles 