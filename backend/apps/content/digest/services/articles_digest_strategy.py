"""
Articles-Based Digest Strategy.

This strategy generates digests by directly processing articles grouped by topic,
without relying on complex event detection and clustering. This provides a more
reliable and predictable digest generation approach.

Key features:
- Direct article-to-topic mapping
- AI-powered comprehensive topic summaries from multiple article abstracts
- Structured digest format with introduction, topic summaries, and conclusion
- Simple, reliable content selection
- Fallback-friendly approach
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


class ArticlesDigestStrategy(DigestStrategy):
    """
    Articles-based digest generation strategy.
    
    This strategy focuses on processing articles directly grouped by topic,
    using AI to synthesize comprehensive topic summaries with:
    1. Introduction focused on daily readers
    2. Topic summaries with abstract, key events, perspectives, and recommendations
    3. Conclusion wrapping up the digest
    """
    
    def __init__(self):
        self.content_selector = DigestContentSelector()
        self.ai_generator = DigestAIGenerator()
        self.logger = logger
    
    def get_strategy_name(self) -> str:
        """Get human-readable name for this strategy."""
        return "Articles-Based Digest"
    
    def generate_digest_content(
        self,
        digest: Digest,
        followed_topics: List[Topic],
        preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate digest content using comprehensive articles-based approach.
        
        Creates a structured digest with:
        1. Introduction for daily readers
        2. Comprehensive topic summaries (60-120w abstract, key events, perspectives, recommendations)
        3. Conclusion summarizing main themes
        
        Args:
            digest: Digest instance to populate
            followed_topics: Topics the user follows
            preferences: User's digest preferences
            
        Returns:
            Dictionary with generation metrics and results
        """
        self.logger.info(f"Starting comprehensive articles-based digest generation for {digest.user.username}")
        
        # Clear existing content for regeneration
        DigestTopic.objects.filter(digest=digest).delete()
        DigestStory.objects.filter(digest=digest).delete()
        
        # Configuration
        max_topics = min(preferences.get('max_topics', 6), len(followed_topics))
        max_articles_per_topic = preferences.get('max_articles_per_topic', 30)  # Feed all available articles to LLM (up to 30)
        
        # Metrics tracking
        metrics = {
            'total_articles_processed': 0,
            'total_stories_created': 0,
            'total_cost': Decimal('0.00'),
            'total_input_tokens': 0,
            'total_output_tokens': 0,
            'topics_processed': 0,
            'topics_with_content': 0
        }
        
        selected_topics_data = []
        topic_summaries_for_conclusion = []
        
        # Step 1: Collect articles for each topic
        for topic in followed_topics[:max_topics]:
            self.logger.info(f"Processing topic: {topic.name}")
            metrics['topics_processed'] += 1
            
            # Get articles for this topic
            topic_articles = self.content_selector.get_topic_articles_for_fallback_digest(
                topic=topic,
                target_date=digest.date,
                max_articles=max_articles_per_topic,
                user=digest.user,
                user_preferences=preferences
            )
            
            if not topic_articles:
                self.logger.info(f"No articles found for topic {topic.name}")
                continue
            
            metrics['total_articles_processed'] += len(topic_articles)
            metrics['topics_with_content'] += 1
            
            selected_topics_data.append({
                'topic': topic,
                'articles': topic_articles,
                'article_count': len(topic_articles)
            })
            
            self.logger.info(f"Topic {topic.name}: {len(topic_articles)} articles collected")
        
        if not selected_topics_data:
            raise ValueError("No content found for any followed topics")
        
        # Step 2: Generate comprehensive AI-enhanced content for each topic
        self.logger.info(f"Generating comprehensive AI content for {len(selected_topics_data)} topics")
        
        for order, topic_data in enumerate(selected_topics_data):
            topic = topic_data['topic']
            articles = topic_data['articles']
            
            # Create DigestTopic with comprehensive AI-generated content
            digest_topic, topic_cost, topic_content = self._create_comprehensive_digest_topic(
                digest=digest,
                topic=topic,
                articles=articles,
                order=order,
                preferences=preferences
            )
            
            # Create DigestStory from comprehensive topic content with AI recommendations
            digest_stories, story_cost = self._create_digest_story_from_comprehensive_topic(
                digest=digest,
                digest_topic=digest_topic,
                articles=articles,
                order=0,
                topic_content=topic_content  # Pass AI content with read_more recommendations
            )
            
            # Collect summary for conclusion
            topic_summaries_for_conclusion.append({
                'name': topic.name,
                'key_point': digest_topic.topic_abstract[:100] + "..." if len(digest_topic.topic_abstract) > 100 else digest_topic.topic_abstract
            })
            
            # Update metrics
            metrics['total_cost'] += topic_cost + story_cost
            metrics['total_input_tokens'] += digest_topic.tokens_input + sum(story.tokens_input for story in digest_stories)
            metrics['total_output_tokens'] += digest_topic.tokens_output + sum(story.tokens_output for story in digest_stories)
            metrics['total_stories_created'] += len(digest_stories)
            
            self.logger.info(
                f"Topic {topic.name} processed: "
                f"${topic_cost + story_cost:.4f}, "
                f"{digest_topic.tokens_input + sum(story.tokens_input for story in digest_stories)} input tokens"
            )
        
        # Step 3: Generate digest introduction for daily readers
        introduction = self.ai_generator.generate_digest_introduction(
            digest_data={
                'digest': digest,
                'topics_data': selected_topics_data,
                'strategy': 'articles_based_comprehensive'
            }
        )
        
        # Step 4: Generate digest conclusion
        conclusion = self.ai_generator.generate_digest_conclusion(topic_summaries_for_conclusion)
        
        # Update digest metadata
        digest.introduction = introduction['content']
        digest.conclusion = conclusion['content']
        digest.articles_processed = metrics['total_articles_processed']
        digest.events_included = 0  # No events in articles-based approach
        digest.topics_included = metrics['topics_with_content']
        digest.generation_cost_usd = metrics['total_cost'] + Decimal(str(introduction['cost'])) + Decimal(str(conclusion['cost']))
        digest.tokens_input = metrics['total_input_tokens'] + introduction['tokens_input'] + conclusion['tokens_input']
        digest.tokens_output = metrics['total_output_tokens'] + introduction['tokens_output'] + conclusion['tokens_output']
        digest.ai_model_used = introduction.get('model_used', 'gpt-4.1-mini')
        digest.save()
        
        self.logger.info(
            f"Comprehensive articles-based digest completed for {digest.user.username}. "
            f"Topics: {digest.topics_included}, Articles: {digest.articles_processed}, "
            f"Stories: {metrics['total_stories_created']}, Cost: ${digest.generation_cost_usd}"
        )
        
        return {
            'success': True,
            'metrics': metrics,
            'topics_data': selected_topics_data,
            'strategy_details': {
                'approach': 'articles_based_comprehensive',
                'topics_processed': metrics['topics_processed'],
                'topics_with_content': metrics['topics_with_content'],
                'format': 'introduction + comprehensive_topic_summaries + conclusion'
            }
        }
    
    def _create_comprehensive_digest_topic(
        self,
        digest: Digest,
        topic: Topic,
        articles: List[Article],
        order: int,
        preferences: Dict[str, Any]
    ) -> tuple[DigestTopic, Decimal, Dict[str, Any]]:
        """
        Create a DigestTopic with comprehensive AI-generated content.
        
        Uses the new comprehensive format with:
        - 60-120 word abstract
        - Up to 5 key events (60 words max each)
        - Up to 3 key perspectives
        - Exactly 3 recommended articles
        
        Args:
            digest: Digest instance
            topic: Topic to create content for
            articles: Articles to synthesize
            order: Display order
            preferences: User preferences
            
        Returns:
            Tuple of (DigestTopic, cost_in_usd, topic_content)
        """
        # Generate comprehensive AI topic summary from articles
        topic_content = self.ai_generator.generate_comprehensive_topic_summary(
            topic_data={
                'topic': topic,
                'articles': articles,
                'include_opinions': preferences.get('include_opinions', True),
                'include_impacts': preferences.get('include_impacts', True)
            }
        )
        
        # Store comprehensive content in DigestTopic
        # Map the comprehensive format to existing fields and add new structured data
        digest_topic = DigestTopic.objects.create(
            digest=digest,
            topic=topic,
            topic_abstract=topic_content.get('topic_abstract', ''),
            main_facts=topic_content.get('stories', []),  # Store stories array in main_facts for now
            perspectives=[],  # Will be populated from individual stories
            order=order,
            event_count=0,  # No events in articles-based approach
            article_count=len(articles),
            generation_cost_usd=Decimal(str(topic_content.get('cost', 0))),
            tokens_input=topic_content.get('tokens_input', 0),
            tokens_output=topic_content.get('tokens_output', 0),
        )
        
        # Store recommended articles info for later use
        if 'read_more' in topic_content:
            self.logger.info(f"Read more articles for {topic.name}: {topic_content['read_more']}")
            # Store the read_more data temporarily in the topic_content for the story creation
            topic_content['_digest_topic'] = digest_topic
        
        return digest_topic, Decimal(str(topic_content.get('cost', 0))), topic_content
    
    def _create_digest_story_from_comprehensive_topic(
        self,
        digest: Digest,
        digest_topic: DigestTopic,
        articles: List[Article],
        order: int,
        topic_content: Dict[str, Any] = None
    ) -> tuple[List[DigestStory], Decimal]:
        """
        Create DigestStory objects from the comprehensive topic's AI-generated stories.
        
        In the new story-based approach, we create multiple stories per topic
        based on the AI-generated stories array.
        
        Args:
            digest: Digest instance
            digest_topic: Parent topic with comprehensive content
            articles: Source articles
            order: Display order
            topic_content: AI-generated content with stories array
            
        Returns:
            Tuple of (List of DigestStory objects, total_cost_in_usd)
        """
        stories_created = []
        total_cost = Decimal('0.00')
        
        # Get stories from AI-generated content
        ai_stories = topic_content.get('stories', []) if topic_content else []
        
        if not ai_stories:
            # Fallback: create single story if no AI stories available
            self.logger.warning(f"No AI stories found for {digest_topic.topic.name}, creating fallback story")
            fallback_story = DigestStory.objects.create(
                digest=digest,
                digest_topic=digest_topic,
                event=None,
                title=f"Today in {digest_topic.topic.name}",
                summary=digest_topic.topic_abstract,
                enhanced_abstract=digest_topic.topic_abstract,
                key_facts=[f"Recent {digest_topic.topic.name} developments"],
                perspectives=[],
                article_count=len(articles),
                primary_mentions=len(articles),
                secondary_mentions=0,
                event_score=0.0,
                order=0,
                generation_cost_usd=Decimal('0.00'),
                tokens_input=0,
                tokens_output=0
            )
            
            # Add most recent articles as recommendations
            recent_articles = sorted(articles, key=lambda a: a.published_at or a.created_at, reverse=True)[:3]
            fallback_story.recommended_articles.set(recent_articles)
            
            return [fallback_story], total_cost
        
        # Create DigestStory for each AI-generated story
        articles_by_id = {article.id: article for article in articles}
        
        for story_index, story_data in enumerate(ai_stories[:3]):  # Limit to 3 stories
            # Map AI-recommended articles for this story
            recommended_articles = []
            story_read_more = story_data.get('read_more', [])
            
            for recommendation in story_read_more:
                article_id = recommendation.get('article_id')
                if article_id and str(article_id) in map(str, articles_by_id.keys()):
                    # Find article by ID (handle both int and string IDs)
                    for aid, article in articles_by_id.items():
                        if str(aid) == str(article_id):
                            recommended_articles.append(article)
                            self.logger.info(
                                f"Mapped AI recommendation for story '{story_data.get('headline', '')}': {recommendation.get('title', '')} -> Article {article.id}"
                            )
                            break
                else:
                    if article_id:  # Only warn if there was an actual ID provided
                        self.logger.warning(
                            f"Could not find article ID {article_id} for story recommendation: {recommendation.get('title', 'Unknown')}"
                        )
            
            # Ensure we have at least 1 article per story
            if not recommended_articles:
                # Use remaining articles not already used in other stories
                used_articles = {article.id for story in stories_created for article in story.recommended_articles.all()}
                available_articles = [a for a in articles if a.id not in used_articles]
                if available_articles:
                    recommended_articles = [available_articles[0]]
                else:
                    # Fall back to any article if all are used
                    recommended_articles = articles[:1]
            
            digest_story = DigestStory.objects.create(
                digest=digest,
                digest_topic=digest_topic,
                event=None,
                title=story_data.get('headline', f"Story {story_index + 1} in {digest_topic.topic.name}"),
                summary=story_data.get('abstract', ''),
                enhanced_abstract=story_data.get('abstract', ''),
                key_facts=story_data.get('main_points', []),
                perspectives=story_data.get('perspectives', []),
                article_count=len(recommended_articles),
                primary_mentions=len(recommended_articles),
                secondary_mentions=0,
                event_score=float(3 - story_index),  # Higher score for first stories
                order=story_index,
                generation_cost_usd=Decimal('0.00'),  # No additional AI cost
                tokens_input=0,
                tokens_output=0
            )
            
            # Associate recommended articles for this story
            if recommended_articles:
                digest_story.recommended_articles.set(recommended_articles[:3])  # Max 3 per story
                self.logger.info(
                    f"Associated {len(recommended_articles[:3])} recommended articles for story '{story_data.get('headline', '')}'"
                )
            
            stories_created.append(digest_story)
        
        return stories_created, Decimal('0.00')
    
    def _create_digest_topic_with_ai(
        self,
        digest: Digest,
        topic: Topic,
        articles: List[Article],
        order: int,
        preferences: Dict[str, Any]
    ) -> tuple[DigestTopic, Decimal]:
        """
        Create a DigestTopic with AI-generated content from articles (legacy method).
        
        This method is kept for backward compatibility but the comprehensive version
        should be used for new implementations.
        
        Args:
            digest: Digest instance
            topic: Topic to create content for
            articles: Articles to synthesize
            order: Display order
            preferences: User preferences
            
        Returns:
            Tuple of (DigestTopic, cost_in_usd)
        """
        # Generate AI topic summary from articles
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
            event_count=0,  # No events in articles-based approach
            article_count=len(articles),
            generation_cost_usd=Decimal(str(topic_content.get('cost', 0))),
            tokens_input=topic_content.get('tokens_input', 0),
            tokens_output=topic_content.get('tokens_output', 0)
        )
        
        return digest_topic, Decimal(str(topic_content.get('cost', 0)))
    
    def _create_digest_story_from_topic(
        self,
        digest: Digest,
        digest_topic: DigestTopic,
        articles: List[Article],
        order: int
    ) -> tuple[DigestStory, Decimal]:
        """
        Create a DigestStory from the topic's AI-generated content (legacy method).
        
        This method is kept for backward compatibility but the comprehensive version
        should be used for new implementations.
        
        Args:
            digest: Digest instance
            digest_topic: Parent topic
            articles: Source articles
            order: Display order
            
        Returns:
            Tuple of (DigestStory, cost_in_usd)
        """
        # Use the topic's AI-generated content for the story
        # This approach treats the topic summary as the main "story"
        
        # Select top 3 most recent articles for recommendations
        recommended_articles = sorted(
            articles, 
            key=lambda a: a.published_at, 
            reverse=True
        )[:3]
        
        digest_story = DigestStory.objects.create(
            digest=digest,
            digest_topic=digest_topic,
            event=None,  # No specific event in articles-based approach
            title=f"{digest_topic.topic.name} Today",
            summary=digest_topic.topic_abstract,
            enhanced_abstract=digest_topic.topic_abstract,
            key_facts=digest_topic.main_facts,
            perspectives=digest_topic.perspectives,
            article_count=len(articles),
            primary_mentions=len(articles),  # All articles are "primary" in this approach
            secondary_mentions=0,
            event_score=0.0,  # No event scoring
            order=order,
            generation_cost_usd=Decimal('0.00'),  # No additional AI cost (content from topic)
            tokens_input=0,
            tokens_output=0
        )
        
        # Associate recommended articles
        if recommended_articles:
            digest_story.recommended_articles.set(recommended_articles)
        
        return digest_story, Decimal('0.00')
    
    def get_articles_for_topic(
        self,
        topic: Topic,
        digest: Digest,
        preferences: Dict[str, Any],
        max_articles: int = 30  # Feed all available articles to LLM (up to 30)
    ) -> List[Article]:
        """
        Get articles for a specific topic using the content selector.
        
        Args:
            topic: Topic to get articles for
            digest: Digest being generated
            preferences: User preferences
            max_articles: Maximum articles to return (increased for richer AI context)
            
        Returns:
            List of articles for the topic
        """
        return self.content_selector.get_topic_articles_for_fallback_digest(
            topic=topic,
            target_date=digest.date,
            max_articles=max_articles,
            user=digest.user,
            user_preferences=preferences
        ) 