"""
Events-Based Digest Strategy.

This strategy generates digests by processing articles through event detection,
clustering, and semantic analysis. This provides sophisticated content synthesis
but is more complex and potentially less reliable.

Key features:
- Event detection and clustering
- Semantic similarity analysis
- Multi-article event synthesis
- Complex scoring and ranking
"""

import logging
from decimal import Decimal
from typing import Dict, Any, List
from django.db import transaction

from apps.content.digest.services.digest_router import DigestStrategy
from apps.content.digest.services.content_selector import DigestContentSelector
from apps.content.digest.services.ai_generator import DigestAIGenerator
from apps.content.digest.models import Digest, DigestTopic, DigestStory
from apps.feeds.models import Topic
from apps.articles.models import Article

logger = logging.getLogger(__name__)


class EventsDigestStrategy(DigestStrategy):
    """
    Events-based digest generation strategy.
    
    This strategy processes articles through event detection and clustering
    to create sophisticated multi-perspective digest content.
    """
    
    def __init__(self):
        self.content_selector = DigestContentSelector()
        self.ai_generator = DigestAIGenerator()
        self.logger = logger
    
    def get_strategy_name(self) -> str:
        """Get human-readable name for this strategy."""
        return "Events-Based Digest"
    
    def generate_digest_content(
        self,
        digest: Digest,
        followed_topics: List[Topic],
        preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate digest content using events-based approach.
        
        Args:
            digest: Digest instance to populate
            followed_topics: Topics the user follows
            preferences: User's digest preferences
            
        Returns:
            Dictionary with generation metrics and results
        """
        self.logger.info(f"Starting events-based digest generation for {digest.user.username}")
        
        # Clear existing content for regeneration
        DigestTopic.objects.filter(digest=digest).delete()
        DigestStory.objects.filter(digest=digest).delete()
        
        # Configuration
        max_topics = min(preferences.get('max_topics', 6), len(followed_topics))
        max_events_per_topic = preferences.get('max_events_per_topic', 3)
        
        # Metrics tracking
        metrics = {
            'total_articles_processed': 0,
            'total_events_included': 0,
            'total_cost': Decimal('0.00'),
            'total_input_tokens': 0,
            'total_output_tokens': 0,
            'topics_processed': 0,
            'topics_with_events': 0,
            'fallback_topics': 0
        }
        
        selected_topics_data = []
        
        # Step 1: Process each topic for events
        for topic in followed_topics[:max_topics]:
            self.logger.info(f"Processing topic: {topic.name}")
            metrics['topics_processed'] += 1
            
            # Get top events for this topic
            topic_events = self.content_selector.get_top_events_for_topic(
                topic=topic,
                target_date=digest.date,
                max_events=max_events_per_topic,
                user=digest.user,
                user_preferences=preferences
            )
            
            if not topic_events:
                self.logger.info(f"No events found for topic {topic.name}, using fallback...")
                
                # Fallback to articles-based approach for this topic
                fallback_articles = self.content_selector.get_topic_articles_for_fallback_digest(
                    topic=topic,
                    target_date=digest.date,
                    max_articles=max_events_per_topic,
                    user=digest.user,
                    user_preferences=preferences
                )
                
                if not fallback_articles:
                    self.logger.info(f"No articles found for topic {topic.name} in fallback mode")
                    continue
                
                metrics['total_articles_processed'] += len(fallback_articles)
                metrics['fallback_topics'] += 1
                
                selected_topics_data.append({
                    'topic': topic,
                    'articles': fallback_articles,
                    'fallback_mode': True
                })
                continue
            
            # Collect articles for topic-level summary
            topic_articles = []
            for event_data in topic_events:
                topic_articles.extend(event_data['articles'])
            
            if not topic_articles:
                self.logger.info(f"No articles found for topic {topic.name}")
                continue
            
            metrics['total_articles_processed'] += len(topic_articles)
            metrics['total_events_included'] += len(topic_events)
            metrics['topics_with_events'] += 1
            
            selected_topics_data.append({
                'topic': topic,
                'events': topic_events,
                'articles': topic_articles
            })
        
        if not selected_topics_data:
            raise ValueError("No content found for any followed topics")
        
        # Step 2: Generate AI-enhanced content
        self.logger.info(f"Generating AI content for {len(selected_topics_data)} topics")
        
        for order, topic_data in enumerate(selected_topics_data):
            topic = topic_data['topic']
            fallback_mode = topic_data.get('fallback_mode', False)
            
            if fallback_mode:
                # Handle fallback mode - same as articles-based strategy
                articles = topic_data['articles']
                
                digest_topic, topic_cost = self._create_digest_topic_fallback(
                    digest=digest,
                    topic=topic,
                    articles=articles,
                    order=order,
                    preferences=preferences
                )
                
                digest_story, story_cost = self._create_digest_story_fallback(
                    digest=digest,
                    digest_topic=digest_topic,
                    articles=articles,
                    order=0
                )
                
                metrics['total_cost'] += topic_cost + story_cost
                metrics['total_input_tokens'] += digest_topic.tokens_input + digest_story.tokens_input
                metrics['total_output_tokens'] += digest_topic.tokens_output + digest_story.tokens_output
            
            else:
                # Handle event-based mode
                events = topic_data.get('events', [])
                articles = topic_data['articles']
                
                # Step 1: Enhance events with related articles
                self.logger.info(f"Enhancing {len(events)} events for topic {topic.name}")
                enhanced_events = []
                enhancement_cost = 0
                
                # Get detailed event data with primary/secondary split
                event_groups = self.content_selector._group_articles_by_primary_and_secondary_events(articles)
                
                for event_data in events:
                    event = event_data['event']
                    
                    # Get the detailed event data with primary/secondary split
                    event_id = event.id
                    if event_id not in event_groups:
                        self.logger.warning(f"Event {event.title} not found in event groups, skipping enhancement")
                        # Use fallback structure
                        event_data.update({
                            'enhanced_abstract': event.abstract or event.title,
                            'enhanced_facts': [],
                            'enhanced_perspectives': [],
                            'enhancement_cost': 0,
                            'primary_articles': [],
                            'secondary_articles': event_data['articles']
                        })
                        enhanced_events.append(event_data)
                        continue
                    
                    detailed_event_data = event_groups[event_id]
                    primary_articles = detailed_event_data['primary_articles']
                    secondary_articles = detailed_event_data['secondary_articles']
                    
                    # Enhance event summary with related articles
                    enhancement_result = self.content_selector.enhance_event_with_related_articles(
                        event=event,
                        primary_articles=primary_articles,
                        secondary_articles=secondary_articles
                    )
                    
                    # Add enhancement results and detailed article breakdown to event data
                    event_data.update({
                        'enhanced_abstract': enhancement_result['enhanced_abstract'],
                        'enhanced_facts': enhancement_result['enhanced_facts'],
                        'enhanced_perspectives': enhancement_result['enhanced_perspectives'],
                        'enhancement_cost': enhancement_result['cost'],
                        'primary_articles': primary_articles,
                        'secondary_articles': secondary_articles
                    })
                    
                    enhanced_events.append(event_data)
                    enhancement_cost += float(enhancement_result['cost'])
                    
                    if enhancement_result['enhanced']:
                        self.logger.info(
                            f"Enhanced event '{event.title}': {enhancement_result['articles_used']} articles "
                            f"(P:{enhancement_result['primary_count']}, S:{enhancement_result['secondary_count']}, "
                            f"R:{enhancement_result['related_count']})"
                        )
                
                # Step 2: Create DigestTopic with enhanced event data
                digest_topic, topic_cost = self._create_digest_topic_with_events(
                    digest=digest,
                    topic=topic,
                    events=enhanced_events,
                    articles=articles,
                    order=order,
                    preferences=preferences
                )
                
                # Step 3: Create DigestStories for each enhanced event
                stories_cost = Decimal('0.00')
                for event_order, event_data in enumerate(enhanced_events):
                    digest_story, story_cost = self._create_digest_story_enhanced(
                        digest=digest,
                        digest_topic=digest_topic,
                        event_data=event_data,
                        order=event_order
                    )
                    stories_cost += story_cost
                
                # Track costs
                total_topic_cost = topic_cost + Decimal(str(enhancement_cost)) + stories_cost
                metrics['total_cost'] += total_topic_cost
                metrics['total_input_tokens'] += digest_topic.tokens_input
                metrics['total_output_tokens'] += digest_topic.tokens_output
        
        # Step 3: Generate digest introduction
        introduction_result = self.ai_generator.generate_digest_introduction(
            digest_data={
                'digest': digest,
                'topics_data': selected_topics_data,
                'strategy': 'events_based'
            }
        )
        
        # Update digest metadata
        digest.headline = introduction_result['headline']
        digest.introduction = introduction_result['introduction']
        digest.articles_processed = metrics['total_articles_processed']
        digest.events_included = metrics['total_events_included']
        digest.topics_included = len(selected_topics_data)
        digest.generation_cost_usd = metrics['total_cost'] + Decimal(str(introduction_result['cost']))
        digest.tokens_input = metrics['total_input_tokens'] + introduction_result['tokens_input']
        digest.tokens_output = metrics['total_output_tokens'] + introduction_result['tokens_output']
        digest.ai_model_used = introduction_result.get('model_used', 'gpt-4o-mini')
        digest.save()
        
        self.logger.info(
            f"Events-based digest completed for {digest.user.username}. "
            f"Topics: {digest.topics_included}, Events: {digest.events_included}, "
            f"Articles: {digest.articles_processed}, Cost: ${digest.generation_cost_usd}"
        )
        
        return {
            'success': True,
            'metrics': metrics,
            'topics_data': selected_topics_data,
            'strategy_details': {
                'approach': 'events_based',
                'topics_with_events': metrics['topics_with_events'],
                'fallback_topics': metrics['fallback_topics'],
                'total_events': metrics['total_events_included']
            }
        }
    
    def _create_digest_topic_fallback(
        self,
        digest: Digest,
        topic: Topic,
        articles: List[Article],
        order: int,
        preferences: Dict[str, Any]
    ) -> tuple[DigestTopic, Decimal]:
        """Create DigestTopic using fallback (articles-based) approach."""
        topic_content = self.ai_generator.generate_fallback_topic_summary(
            topic_data={
                'topic': topic,
                'articles': articles,
                'include_opinions': preferences.get('include_opinions', True),
                'include_impacts': preferences.get('include_impacts', True)
            }
        )
        
        digest_topic = DigestTopic.objects.create(
            digest=digest,
            topic=topic,
            topic_abstract=topic_content.get('abstract', ''),
            main_facts=topic_content.get('facts', []),
            perspectives=topic_content.get('opinions', []),
            order=order,
            event_count=0,
            article_count=len(articles),
            generation_cost_usd=Decimal(str(topic_content.get('cost', 0))),
            tokens_input=topic_content.get('tokens_input', 0),
            tokens_output=topic_content.get('tokens_output', 0)
        )
        
        return digest_topic, Decimal(str(topic_content.get('cost', 0)))
    
    def _create_digest_story_fallback(
        self,
        digest: Digest,
        digest_topic: DigestTopic,
        articles: List[Article],
        order: int
    ) -> tuple[DigestStory, Decimal]:
        """Create DigestStory using fallback (articles-based) approach."""
        recommended_articles = sorted(
            articles, 
            key=lambda a: a.published_at, 
            reverse=True
        )[:3]
        
        digest_story = DigestStory.objects.create(
            digest=digest,
            digest_topic=digest_topic,
            event=None,
            title=f"{digest_topic.topic.name} Today",
            summary=digest_topic.topic_abstract,
            enhanced_abstract=digest_topic.topic_abstract,
            key_facts=digest_topic.main_facts,
            perspectives=digest_topic.perspectives,
            article_count=len(articles),
            primary_mentions=len(articles),
            secondary_mentions=0,
            event_score=0.0,
            order=order,
            generation_cost_usd=Decimal('0.00'),
            tokens_input=0,
            tokens_output=0
        )
        
        if recommended_articles:
            digest_story.recommended_articles.set(recommended_articles)
        
        return digest_story, Decimal('0.00')
    
    def _create_digest_topic_with_events(
        self,
        digest: Digest,
        topic: Topic,
        events: List[Dict[str, Any]],
        articles: List[Article],
        order: int,
        preferences: Dict[str, Any]
    ) -> tuple[DigestTopic, Decimal]:
        """Create DigestTopic with AI-generated content from events."""
        topic_content = self.ai_generator.generate_topic_summary(
            topic_data={
                'topic': topic,
                'events': events,
                'articles': articles,
                'include_opinions': preferences.get('include_opinions', True),
                'include_impacts': preferences.get('include_impacts', True)
            }
        )
        
        digest_topic = DigestTopic.objects.create(
            digest=digest,
            topic=topic,
            topic_abstract=topic_content.get('abstract', ''),
            main_facts=topic_content.get('facts', []),
            perspectives=topic_content.get('opinions', []),
            order=order,
            event_count=len(events),
            article_count=len(articles),
            generation_cost_usd=Decimal(str(topic_content.get('cost', 0))),
            tokens_input=topic_content.get('tokens_input', 0),
            tokens_output=topic_content.get('tokens_output', 0)
        )
        
        return digest_topic, Decimal(str(topic_content.get('cost', 0)))
    
    def _create_digest_story_enhanced(
        self,
        digest: Digest,
        digest_topic: DigestTopic,
        event_data: Dict[str, Any],
        order: int
    ) -> tuple[DigestStory, Decimal]:
        """Create DigestStory with enhanced event content."""
        event = event_data['event']
        articles = event_data['articles']
        score = event_data['score']
        primary_mentions = event_data['primary_mentions']
        secondary_mentions = event_data['secondary_mentions']
        enhanced_abstract = event_data.get('enhanced_abstract', event.abstract or event.title)
        enhanced_facts = event_data.get('enhanced_facts', [])
        enhanced_perspectives = event_data.get('enhanced_perspectives', [])
        
        # Select top 3 most recent articles for recommendations
        recommended_articles = sorted(
            articles, 
            key=lambda a: a.published_at, 
            reverse=True
        )[:3]
        
        digest_story = DigestStory.objects.create(
            digest=digest,
            digest_topic=digest_topic,
            event=event,
            title=event.title,
            summary=enhanced_abstract,
            enhanced_abstract=enhanced_abstract,
            key_facts=enhanced_facts,
            perspectives=enhanced_perspectives,
            article_count=len(articles),
            primary_mentions=primary_mentions,
            secondary_mentions=secondary_mentions,
            event_score=score,
            order=order,
            generation_cost_usd=Decimal('0.00'),  # Enhancement cost tracked separately
            tokens_input=0,
            tokens_output=0
        )
        
        if recommended_articles:
            digest_story.recommended_articles.set(recommended_articles)
        
        return digest_story, Decimal('0.00') 