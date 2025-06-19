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
                events = topic_data['events']
                articles = topic_data['articles']
                
                # Create DigestTopic with AI-generated content
                digest_topic = self._create_digest_topic(
                    digest=digest,
                    topic=topic,
                    articles=articles,
                    order=order
                )
                
                # Create DigestStories for each event
                for event_order, event_data in enumerate(events):
                    digest_story = self._create_digest_story(
                        digest=digest,
                        digest_topic=digest_topic,
                        event_data=event_data,
                        order=event_order
                    )
                    
                    # Track costs
                    total_cost += digest_story.generation_cost_usd
                    total_input_tokens += digest_story.tokens_input
                    total_output_tokens += digest_story.tokens_output
                
                # Track topic costs
                total_cost += digest_topic.generation_cost_usd
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
            topic_abstract=topic_content['abstract'],
            main_facts=topic_content['facts'],
            perspectives=topic_content['perspectives'],
            order=order,
            event_count=0,  # Will be updated when stories are added
            article_count=len(articles),
            generation_cost_usd=Decimal(str(topic_content['cost'])),
            tokens_input=topic_content['tokens_input'],
            tokens_output=topic_content['tokens_output']
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
            summary=event.abstract if hasattr(event, 'abstract') else event.title,
            enhanced_abstract=story_content['enhanced_abstract'],
            key_facts=story_content['facts'],
            perspectives=story_content['perspectives'],
            article_count=len(articles),
            primary_mentions=primary_mentions,
            secondary_mentions=secondary_mentions,
            event_score=score,
            order=order,
            generation_cost_usd=Decimal(str(story_content['cost'])),
            tokens_input=story_content['tokens_input'],
            tokens_output=story_content['tokens_output'],
            ai_model_used='basic-mode'  # Indicate no AI generation
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
            title=topic_content.get('title', f"Latest in {topic.name}"),
            topic_abstract=topic_content.get('abstract', f"Key developments in {topic.name} based on recent articles."),
            main_facts=topic_content.get('facts', []),
            perspectives=topic_content.get('opinions', []),
            order=order,
            articles_count=len(articles),
            # AI generation costs
            generation_cost_usd=topic_content.get('cost', Decimal('0.00')),
            tokens_input=topic_content.get('tokens_input', 0),
            tokens_output=topic_content.get('tokens_output', 0),
            ai_model_used=topic_content.get('model_used', 'gpt-4o-mini')
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
            tokens_output=story_content.get('tokens_output', 0),
            ai_model_used=story_content.get('model_used', 'gpt-4o-mini')
        )
        
        # Add articles as recommendations (all of them since we only have 3 max)
        digest_story.recommended_articles.set(articles)
        
        logger.info(f"Created AI-powered fallback digest story {digest_story.id} for {digest_topic.topic.name}")
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