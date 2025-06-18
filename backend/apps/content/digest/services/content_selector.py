"""
DigestContentSelector Service

Handles content selection and filtering logic for digest generation.
Responsible for:
- Filtering articles based on user preferences and processing status
- Grouping articles by topic and primary events
- Ranking events by importance and user relevance
- Selecting recommended articles for deep-dive reading
"""

import logging
from typing import List, Dict, Any, Tuple, Optional
from collections import defaultdict
from datetime import datetime, timedelta
from django.db.models import QuerySet, Q
from django.contrib.auth.models import User
from django.utils import timezone

from apps.articles.models import Article, AnalyzerStatus, SummarizationStatus
from apps.feeds.models import UserTopic, Topic
from apps.content.analyzer.models import ArticleEvent, Event

logger = logging.getLogger(__name__)


class DigestContentSelector:
    """
    Service for selecting and organizing content for digest generation.
    
    This service implements the core content selection algorithm that:
    1. Filters articles based on user preferences and processing status
    2. Groups articles by (topic, primary_event) combinations
    3. Ranks events by importance within each topic
    4. Selects the most relevant content for digest inclusion
    """
    
    def __init__(self):
        self.logger = logger
    
    def get_user_articles(self, user: User, date_range: Tuple[datetime, datetime]) -> QuerySet[Article]:
        """
        Get articles matching user's topics from specified date range.
        
        Filters articles based on:
        - Published in the specified date range
        - Primary topic matches user's followed topics
        - Analyzer status is COMPLETED (has events, entities, summaries)
        - Summarization status is COMPLETED (has structured summaries)
        - Has event data available
        
        Args:
            user: User to get articles for
            date_range: Tuple of (start_time, end_time) for filtering
            
        Returns:
            QuerySet of filtered articles ready for digest processing
        """
        start_time, end_time = date_range
        
        # Get user's followed topics
        user_topic_ids = list(
            UserTopic.objects.filter(user=user).values_list('topic_id', flat=True)
        )
        
        if not user_topic_ids:
            self.logger.info(f"User {user.id} has no followed topics")
            return Article.objects.none()
        
        # Build the query
        queryset = Article.objects.filter(
            # Time range filter
            published_at__gte=start_time,
            published_at__lt=end_time,
            
            # User preference filter
            primary_topic_id__in=user_topic_ids,
            
            # Processing completion filter
            analyzer_status=AnalyzerStatus.COMPLETED,
            summarization_status=SummarizationStatus.COMPLETED,
            
            # Data availability filter
            article_events__isnull=False,  # Has events
        ).select_related(
            'primary_topic', 'structured_summary', 'publication'
        ).prefetch_related(
            'article_events__event', 'topics'
        ).distinct()
        
        article_count = queryset.count()
        self.logger.info(
            f"Found {article_count} articles for user {user.id} "
            f"from {start_time.date()} to {end_time.date()}"
        )
        
        return queryset
    
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
    
    def get_date_range_for_digest(self, target_date: datetime, user_timezone: str = 'UTC') -> Tuple[datetime, datetime]:
        """
        Calculate the date range for digest content.
        
        Uses 24-hour window from 6 AM yesterday to 6 AM today in user's timezone.
        
        Args:
            target_date: The date the digest is for
            user_timezone: User's timezone string
            
        Returns:
            Tuple of (start_time, end_time) in UTC for database queries
        """
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
            f"Date range for digest: {start_time_utc} to {end_time_utc} "
            f"({start_time_local} to {end_time_local} in {user_timezone})"
        )
        
        return start_time_utc, end_time_utc 