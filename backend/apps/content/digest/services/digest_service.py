"""
Main Digest Service for orchestrating personalized daily digest generation.

This service coordinates the entire digest creation process:
1. Content filtering and selection based on user preferences
2. AI-powered content synthesis and enhancement
3. Digest model creation and persistence
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any, Tuple
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import transaction

from apps.content.digest.models import Digest, DigestTopic, DigestStory
from apps.content.digest.services.content_selector import DigestContentSelector
from apps.content.digest.services.ai_generator import DigestAIGenerator
from apps.feeds.models import Topic, UserTopic
from apps.articles.models import Article


logger = logging.getLogger(__name__)


class DigestService:
    """
    Main service for generating personalized daily digests.
    
    Orchestrates the entire digest generation pipeline:
    - Content filtering based on user preferences
    - Event scoring and ranking
    - AI-powered content synthesis
    - Digest model creation and persistence
    """
    
    def __init__(self):
        self.content_selector = DigestContentSelector()
        self.ai_generator = DigestAIGenerator()
    
    def generate_user_digest(
        self, 
        user: User, 
        date: datetime.date,
        force_regenerate: bool = False
    ) -> Digest:
        """
        Generate a personalized digest for a user on a specific date.
        
        Args:
            user: User to generate digest for
            date: Date to generate digest for
            force_regenerate: Whether to regenerate if digest already exists
            
        Returns:
            Digest: The generated or existing digest
            
        Raises:
            ValueError: If user has no followed topics or insufficient content
        """
        logger.info(f"Starting digest generation for user {user.username} on {date}")
        
        # Check if digest already exists
        try:
            existing_digest = Digest.objects.get(user=user, date=date)
            if not force_regenerate:
                logger.info(f"Digest already exists for {user.username} on {date}")
                return existing_digest
            logger.info(f"Force regenerating existing digest for {user.username} on {date}")
        except Digest.DoesNotExist:
            pass
        
        # Get user's digest preferences with defaults
        digest_preferences = user.profile.get_digest_preferences()
        
        # Get user's followed topics
        followed_topics = self._get_user_followed_topics(user)
        if not followed_topics:
            raise ValueError(f"User {user.username} has no followed topics")
        
        # Start generation process
        start_time = timezone.now()
        
        try:
            with transaction.atomic():
                # Create or update digest record
                digest, created = Digest.objects.get_or_create(
                    user=user,
                    date=date,
                    defaults={
                        'title': f"Your Daily Brief for {date.strftime('%B %d, %Y')}",
                        'generation_status': 'processing',
                        'user_timezone': user.profile.timezone,
                        'digest_preferences': digest_preferences,
                    }
                )
                
                if not created:
                    # Update existing digest for regeneration
                    digest.generation_status = 'processing'
                    digest.error_message = ''
                    digest.save()
                
                # Generate digest content
                self._generate_digest_content(digest, followed_topics, digest_preferences)
                
                # Mark as completed
                end_time = timezone.now()
                duration_ms = int((end_time - start_time).total_seconds() * 1000)
                
                digest.generation_status = 'completed'
                digest.generation_duration_ms = duration_ms
                digest.is_published = True
                digest.save()
                
                logger.info(f"Successfully generated digest for {user.username} on {date} in {duration_ms}ms")
                return digest
                
        except Exception as e:
            logger.error(f"Failed to generate digest for {user.username} on {date}: {str(e)}")
            
            # Update digest with error status
            if 'digest' in locals():
                digest.generation_status = 'failed'
                digest.error_message = str(e)
                digest.save()
            
            raise
    
    def _get_user_followed_topics(self, user: User) -> List[Topic]:
        """Get list of topics the user follows."""
        return [
            user_topic.topic 
            for user_topic in UserTopic.objects.filter(user=user).select_related('topic')
        ]
    
    def _generate_digest_content(
        self,
        digest: Digest,
        followed_topics: List[Topic],
        preferences: Dict[str, Any]
    ) -> None:
        """
        Generate the main digest content including topics and stories.
        
        Args:
            digest: Digest instance to populate
            followed_topics: Topics the user follows
            preferences: User's digest preferences
        """
        logger.info(f"Generating content for digest {digest.id}")
        
        # Clear existing content for regeneration
        DigestTopic.objects.filter(digest=digest).delete()
        DigestStory.objects.filter(digest=digest).delete()
        
        # Step 1: Get content for each topic
        max_topics = min(preferences.get('max_topics', 6), len(followed_topics))
        max_events_per_topic = preferences.get('max_events_per_topic', 3)
        
        total_articles_processed = 0
        total_events_included = 0
        total_cost = Decimal('0.00')
        total_input_tokens = 0
        total_output_tokens = 0
        
        selected_topics_data = []
        
        for topic in followed_topics[:max_topics]:
            logger.info(f"Processing topic: {topic.name}")
            
            # Get top events for this topic
            topic_events = self.content_selector.get_top_events_for_topic(
                topic=topic,
                target_date=digest.date,
                max_events=max_events_per_topic,
                user=digest.user,
                user_preferences=preferences
            )
            
            # If no events found, try fallback with article summaries
            if not topic_events:
                logger.info(f"No events found for topic {topic.name}, trying fallback...")
                fallback_articles = self.content_selector.get_topic_articles_for_fallback_digest(
                    topic=topic,
                    target_date=digest.date,
                    max_articles=max_events_per_topic,
                    user=digest.user,
                    user_preferences=preferences
                )
                
                if not fallback_articles:
                    logger.info(f"No articles found for topic {topic.name} in fallback mode")
                    continue
                    
                # Process fallback articles
                total_articles_processed += len(fallback_articles)
                total_events_included += 1  # Count as one "event" per topic in fallback
                
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
                logger.info(f"No articles found for topic {topic.name}")
                continue
            
            total_articles_processed += len(topic_articles)
            total_events_included += len(topic_events)
            
            selected_topics_data.append({
                'topic': topic,
                'events': topic_events,
                'articles': topic_articles
            })
        
        if not selected_topics_data:
            raise ValueError("No content found for any followed topics")
        
        # Step 2: Generate AI-enhanced content
        logger.info(f"Generating AI content for {len(selected_topics_data)} topics")
        
        for order, topic_data in enumerate(selected_topics_data):
            topic = topic_data['topic']
            fallback_mode = topic_data.get('fallback_mode', False)
            
            if fallback_mode:
                # Handle fallback mode - create digest from article summaries with AI synthesis
                articles = topic_data['articles']
                
                # Create DigestTopic with AI-generated fallback content
                digest_topic = self._create_digest_topic_fallback(
                    digest=digest,
                    topic=topic,
                    articles=articles,
                    order=order
                )
                
                # Create a single DigestStory from the AI-generated content
                digest_story = self._create_digest_story_fallback(
                    digest=digest,
                    digest_topic=digest_topic,
                    articles=articles,
                    order=0
                )
                
                # Track costs from AI-powered fallback generation
                total_cost += digest_topic.generation_cost_usd + digest_story.generation_cost_usd
                total_input_tokens += digest_topic.tokens_input + digest_story.tokens_input
                total_output_tokens += digest_topic.tokens_output + digest_story.tokens_output
            
            else:
                # Handle event-based mode
                events = topic_data.get('events', [])
                articles = topic_data['articles']
                
                # If no events available, fall back to article summary mode
                if not events:
                    logger.info(f"No events found for topic {topic.name}, using fallback mode")
                    
                    # Create DigestTopic with AI-generated fallback content
                    digest_topic = self._create_digest_topic_fallback(
                        digest=digest,
                        topic=topic,
                        articles=articles,
                        order=order
                    )
                    
                    # Create a single DigestStory from the AI-generated content
                    digest_story = self._create_digest_story_fallback(
                        digest=digest,
                        digest_topic=digest_topic,
                        articles=articles,
                        order=0
                    )
                    
                    # Track costs from AI-powered fallback generation
                    total_cost += digest_topic.generation_cost_usd + digest_story.generation_cost_usd
                    total_input_tokens += digest_topic.tokens_input + digest_story.tokens_input
                    total_output_tokens += digest_topic.tokens_output + digest_story.tokens_output
                    continue
                
                # Step 1: Enhance events with related articles
                logger.info(f"Enhancing {len(events)} events for topic {topic.name}")
                enhanced_events = []
                enhancement_cost = 0
                
                # First, we need to get the detailed event data with primary/secondary split
                # Since get_top_events_for_topic only returns combined articles, we need to re-fetch
                event_groups = self.content_selector._group_articles_by_primary_and_secondary_events(articles)
                
                for event_data in events:
                    event = event_data['event']
                    
                    # Get the detailed event data with primary/secondary split
                    event_id = event.id
                    if event_id not in event_groups:
                        logger.warning(f"Event {event.title} not found in event groups, skipping enhancement")
                        # Use fallback structure
                        event_data.update({
                            'enhanced_abstract': event.abstract or event.title,
                            'enhanced_facts': [],
                            'enhanced_perspectives': [],
                            'enhancement_cost': 0,
                            'primary_articles': [],
                            'secondary_articles': event_data['articles']  # Treat all as secondary
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
                        logger.info(
                            f"Enhanced event '{event.title}': {enhancement_result['articles_used']} articles "
                            f"(P:{enhancement_result['primary_count']}, S:{enhancement_result['secondary_count']}, "
                            f"R:{enhancement_result['related_count']})"
                        )
                
                # Step 2: Create DigestTopic with enhanced event data
                digest_topic = self._create_digest_topic_with_events(
                    digest=digest,
                    topic=topic,
                    events=enhanced_events,
                    articles=articles,
                    order=order
                )
                
                # Step 3: Create DigestStories for each enhanced event
                for event_order, event_data in enumerate(enhanced_events):
                    digest_story = self._create_digest_story_enhanced(
                        digest=digest,
                        digest_topic=digest_topic,
                        event_data=event_data,
                        order=event_order
                    )
                    
                    # Track costs (no additional AI cost since we use cached enhanced summaries)
                    total_cost += digest_story.generation_cost_usd
                    total_input_tokens += digest_story.tokens_input
                    total_output_tokens += digest_story.tokens_output
                
                # Track topic and enhancement costs
                total_cost += digest_topic.generation_cost_usd + Decimal(str(enhancement_cost))
                total_input_tokens += digest_topic.tokens_input
                total_output_tokens += digest_topic.tokens_output
        
        # Step 3: Generate digest introduction
        introduction = self.ai_generator.generate_digest_introduction(
            digest_data={
                'digest': digest,
                'topics_data': selected_topics_data
            }
        )
        
        # Update digest metadata
        digest.introduction = introduction['content']
        digest.articles_processed = total_articles_processed
        digest.events_included = total_events_included
        digest.topics_included = len(selected_topics_data)
        digest.generation_cost_usd = total_cost + Decimal(str(introduction['cost']))
        digest.tokens_input = total_input_tokens + introduction['tokens_input']
        digest.tokens_output = total_output_tokens + introduction['tokens_output']
        digest.ai_model_used = introduction.get('model_used', 'gpt-4o-mini')
        digest.save()
        
        logger.info(f"Digest content generated successfully. "
                   f"Topics: {digest.topics_included}, Events: {digest.events_included}, "
                   f"Articles: {digest.articles_processed}, Cost: ${digest.generation_cost_usd}")
    
    def _create_digest_topic(
        self,
        digest: Digest,
        topic: Topic,
        articles: List[Article],
        order: int
    ) -> DigestTopic:
        """Create a DigestTopic with AI-generated content."""
        
        # Generate AI content for topic
        topic_content = self.ai_generator.generate_topic_summary(
            topic_data={
                'topic': topic,
                'articles': articles,
                'include_opinions': digest.digest_preferences.get('include_opinions', True)
            }
        )
        
        digest_topic = DigestTopic.objects.create(
            digest=digest,
            topic=topic,
            topic_abstract=topic_content.get('abstract', ''),
            main_facts=topic_content.get('facts', []),
            perspectives=topic_content.get('perspectives', topic_content.get('opinions', [])),
            order=order,
            event_count=0,  # Will be updated when stories are added
            article_count=len(articles),
            generation_cost_usd=Decimal(str(topic_content.get('cost', 0))),
            tokens_input=topic_content.get('tokens_input', 0),
            tokens_output=topic_content.get('tokens_output', 0)
        )
        
        return digest_topic
    
    def _create_digest_story(
        self,
        digest: Digest,
        digest_topic: DigestTopic,
        event_data: Dict[str, Any],
        order: int
    ) -> DigestStory:
        """Create a DigestStory with AI-enhanced content."""
        
        event = event_data['event']
        articles = event_data['articles']
        score = event_data['score']
        primary_mentions = event_data['primary_mentions']
        secondary_mentions = event_data['secondary_mentions']
        
        # For now, use existing event data instead of AI generation
        # This is a temporary solution until generate_story_summary is implemented
        story_content = {
            'enhanced_abstract': event.abstract if hasattr(event, 'abstract') else event.title,
            'facts': [],
            'perspectives': [],
            'cost': 0.0,
            'tokens_input': 0,
            'tokens_output': 0
        }
        
        # Extract facts and perspectives from article summaries
        for article in articles:
            try:
                if hasattr(article, 'structured_summary') and article.structured_summary:
                    summary = article.structured_summary
                    if summary.facts:
                        story_content['facts'].extend(summary.facts[:2])  # Limit per article
                    if summary.opinions:
                        story_content['perspectives'].extend(summary.opinions[:2])  # Limit per article
            except Exception:
                continue
        
        # Limit total facts and perspectives
        story_content['facts'] = story_content['facts'][:6]
        story_content['perspectives'] = story_content['perspectives'][:4]
        
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
            generation_cost_usd=Decimal(str(enhancement_cost)),
            tokens_input=0,  # Enhancement tokens tracked separately
            tokens_output=0
        )
        
        # Add recommended articles
        digest_story.recommended_articles.set(recommended_articles)
        
        # Update digest topic event count
        digest_topic.event_count += 1
        digest_topic.save()
        
        return digest_story
    
    def _create_digest_topic_fallback(
        self,
        digest: Digest,
        topic: Topic,
        articles: List[Article],
        order: int
    ) -> DigestTopic:
        """
        Create a DigestTopic using AI-powered topic summary from article summaries.
        
        This method uses AI to synthesize article summaries into a comprehensive
        topic summary with the same structure as article summaries.
        """
        from apps.content.summariser.models import ArticleSummary
        
        logger.info(f"Creating AI-powered fallback digest topic for {topic.name} with {len(articles)} articles")
        
        # Generate AI-powered topic summary
        topic_content = self.ai_generator.generate_fallback_topic_summary(
            topic_data={
                'topic': topic,
                'articles': articles
            }
        )
        
        # Create the DigestTopic with AI-generated content
        digest_topic = DigestTopic.objects.create(
            digest=digest,
            topic=topic,
            topic_abstract=topic_content.get('abstract', f"Key developments in {topic.name} based on recent articles."),
            main_facts=topic_content.get('facts', []),
            perspectives=topic_content.get('opinions', []),
            order=order,
            article_count=len(articles),
            # AI generation costs
            generation_cost_usd=topic_content.get('cost', Decimal('0.00')),
            tokens_input=topic_content.get('tokens_input', 0),
            tokens_output=topic_content.get('tokens_output', 0)
        )
        
        logger.info(f"Created AI-powered fallback digest topic {digest_topic.id} for {topic.name}")
        return digest_topic
    
    def _create_digest_story_fallback(
        self,
        digest: Digest,
        digest_topic: DigestTopic,
        articles: List[Article],
        order: int
    ) -> DigestStory:
        """
        Create a DigestStory using AI-generated content from article summaries.
        
        This creates a single story per topic containing the most important articles
        and their AI-synthesized information.
        """
        logger.info(f"Creating AI-powered fallback digest story for {digest_topic.topic.name} with {len(articles)} articles")
        
        # Generate AI-powered story content using the same method as topic summary
        # but focused on story-level information
        story_content = self.ai_generator.generate_fallback_topic_summary(
            topic_data={
                'topic': digest_topic.topic,
                'articles': articles
            }
        )
        
        # Use AI-generated content for the story
        story_title = story_content.get('title', f"Recent developments in {digest_topic.topic.name}")
        story_summary = story_content.get('abstract', f"Multiple recent developments in {digest_topic.topic.name}.")
        
        # Create the DigestStory with AI-generated content
        digest_story = DigestStory.objects.create(
            digest=digest,
            digest_topic=digest_topic,
            title=story_title,
            summary=story_summary,
            enhanced_abstract=story_summary,  # Use AI-generated abstract
            key_facts=story_content.get('facts', [])[:6],  # Limit to 6 facts
            perspectives=story_content.get('opinions', [])[:4],  # Limit to 4 perspectives
            order=order,
            article_count=len(articles),
            primary_mentions=len(articles),  # All articles are "primary" in fallback mode
            # AI generation costs
            generation_cost_usd=story_content.get('cost', Decimal('0.00')),
            tokens_input=story_content.get('tokens_input', 0),
            tokens_output=story_content.get('tokens_output', 0)
        )
        
        # Add articles as recommendations (all of them since we only have 3 max)
        digest_story.recommended_articles.set(articles)
        
        logger.info(f"Created AI-powered fallback digest story {digest_story.id} for {digest_topic.topic.name}")
        return digest_story
    
    def _create_digest_topic_with_events(
        self,
        digest: Digest,
        topic: Topic,
        events: List[Dict[str, Any]],
        articles: List[Article],
        order: int
    ) -> DigestTopic:
        """Create a DigestTopic with AI-generated content using enhanced events."""
        
        # Generate AI content for topic using enhanced events
        topic_content = self.ai_generator.generate_topic_summary(
            topic_data={
                'topic': topic,
                'events': events,  # Pass enhanced events data
                'articles': articles,
                'include_opinions': digest.digest_preferences.get('include_opinions', True)
            }
        )
        
        digest_topic = DigestTopic.objects.create(
            digest=digest,
            topic=topic,
            topic_abstract=topic_content.get('abstract', ''),
            main_facts=topic_content.get('facts', []),
            perspectives=topic_content.get('perspectives', topic_content.get('opinions', [])),
            order=order,
            event_count=0,  # Will be updated when stories are added
            article_count=len(articles),
            generation_cost_usd=Decimal(str(topic_content.get('cost', 0))),
            tokens_input=topic_content.get('tokens_input', 0),
            tokens_output=topic_content.get('tokens_output', 0)
        )
        
        return digest_topic
    
    def _create_digest_story_enhanced(
        self,
        digest: Digest,
        digest_topic: DigestTopic,
        event_data: Dict[str, Any],
        order: int
    ) -> DigestStory:
        """Create a DigestStory using enhanced event content."""
        
        event = event_data['event']
        articles = event_data['articles']
        score = event_data['score']
        primary_mentions = event_data['primary_mentions']
        secondary_mentions = event_data['secondary_mentions']
        
        # Use enhanced content from event enhancement
        enhanced_abstract = event_data.get('enhanced_abstract', event.enhanced_abstract or event.abstract or event.title)
        enhanced_facts = event_data.get('enhanced_facts', event.enhanced_facts or [])
        enhanced_perspectives = event_data.get('enhanced_perspectives', event.enhanced_perspectives or [])
        enhancement_cost = event_data.get('enhancement_cost', 0)
        
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
            generation_cost_usd=Decimal(str(enhancement_cost)),
            tokens_input=0,  # Enhancement tokens tracked separately
            tokens_output=0
        )
        
        # Add recommended articles
        digest_story.recommended_articles.set(recommended_articles)
        
        # Update digest topic event count
        digest_topic.event_count += 1
        digest_topic.save()
        
        return digest_story
    
    def get_user_digest(self, user: User, date: datetime.date) -> Optional[Digest]:
        """Get existing digest for user and date."""
        try:
            return Digest.objects.get(user=user, date=date)
        except Digest.DoesNotExist:
            return None
    
    def get_recent_digests(self, user: User, limit: int = 7) -> List[Digest]:
        """Get recent digests for a user."""
        return list(
            Digest.objects.filter(user=user, generation_status='completed')
            .order_by('-date')[:limit]
        ) 