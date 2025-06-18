"""
DigestService

Main orchestrator for digest generation that coordinates content selection,
AI enhancement, and digest creation.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone

from ..models import Digest, DigestTopic, DigestStory
from .content_selector import DigestContentSelector
from .ai_generator import DigestAIGenerator

logger = logging.getLogger(__name__)


class DigestService:
    """
    Main orchestrator service for digest generation.
    
    Coordinates the complete digest creation process:
    1. Content selection and filtering (DigestContentSelector)
    2. AI enhancement and synthesis (DigestAIGenerator)
    3. Data persistence and HTML formatting
    4. Error handling and performance tracking
    """
    
    def __init__(self):
        self.content_selector = DigestContentSelector()
        self.ai_generator = DigestAIGenerator()
        self.logger = logger
    
    def generate_digest(
        self, 
        user: User, 
        target_date: Optional[datetime] = None, 
        regenerate: bool = False
    ) -> Dict[str, Any]:
        """
        Generate a complete daily digest for a user.
        
        Main orchestration method that coordinates the entire digest generation process.
        
        Args:
            user: User to generate digest for
            target_date: Date to generate digest for (defaults to today)
            regenerate: Whether to regenerate existing digest
            
        Returns:
            Dict containing digest data and metrics
        """
        if target_date is None:
            target_date = timezone.now()
        
        self.logger.info(f"Starting digest generation for user {user.id} on {target_date.date()}")
        
        # Check for existing digest
        if not regenerate:
            existing_digest = self._get_existing_digest(user, target_date)
            if existing_digest:
                self.logger.info(f"Found existing digest {existing_digest.public_id} for user {user.id}")
                return {
                    'digest': existing_digest,
                    'content': self._extract_digest_content(existing_digest),
                    'success': True,
                    'regenerated': False
                }
        
        start_time = timezone.now()
        
        try:
            # Get user preferences
            user_preferences = user.profile.get_digest_preferences()
            
            # Calculate date range
            date_range = self.content_selector.get_date_range_for_digest(
                target_date, user.profile.timezone
            )
            
            # Step 1: Content Selection
            self.logger.info("Step 1: Selecting content...")
            articles = self.content_selector.get_user_articles(user, date_range)
            
            if not articles.exists():
                self.logger.info(f"No articles found for user {user.id} in date range")
                return self._create_empty_digest_response(user, target_date, "No articles found")
            
            # Group articles by topic and event
            grouped_data = self.content_selector.group_articles_by_topic_and_event(articles)
            
            if not grouped_data:
                self.logger.info(f"No events found in articles for user {user.id}")
                return self._create_empty_digest_response(user, target_date, "No events found")
            
            # Select final content for digest
            digest_content = self.content_selector.select_digest_content(grouped_data, user_preferences)
            
            if not digest_content:
                self.logger.info(f"No content selected for digest for user {user.id}")
                return self._create_empty_digest_response(user, target_date, "No content selected")
            
            # Step 2: AI Enhancement
            self.logger.info("Step 2: Enhancing content with AI...")
            enhanced_content = self._enhance_content_with_ai(digest_content)
            
            # Step 3: Create Digest Record
            self.logger.info("Step 3: Creating digest record...")
            digest = self._create_digest_record(
                user, target_date, enhanced_content, user_preferences
            )
            
            # Calculate metrics
            generation_time = (timezone.now() - start_time).total_seconds()
            ai_metrics = self.ai_generator.get_generation_metrics()
            
            metrics = {
                'generation_time_seconds': generation_time,
                'topics_included': len(digest_content),
                'total_events': sum(len(topic_data['events']) for topic_data in digest_content.values()),
                'articles_processed': articles.count(),
                **ai_metrics
            }
            
            self.logger.info(
                f"Digest generation completed for user {user.id}: "
                f"{metrics['topics_included']} topics, "
                f"{metrics['total_events']} events in {generation_time:.2f}s"
            )
            
            return {
                'digest': digest,
                'content': enhanced_content,
                'metrics': metrics,
                'success': True,
                'regenerated': regenerate
            }
            
        except Exception as e:
            self.logger.error(f"Digest generation failed for user {user.id}: {e}", exc_info=True)
            
            # Create error digest record
            error_digest = self._create_error_digest_record(user, target_date, str(e))
            
            return {
                'digest': error_digest,
                'content': {},
                'metrics': {'generation_time_seconds': (timezone.now() - start_time).total_seconds()},
                'success': False,
                'error': str(e)
            }
    
    def _enhance_content_with_ai(self, digest_content: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance digest content using AI services."""
        enhanced_content = {
            'topics': {},
            'total_cost': Decimal('0.0'),
            'total_tokens': 0
        }
        
        # Generate digest introduction
        intro_data = self.ai_generator.generate_digest_introduction(digest_content)
        enhanced_content['introduction'] = intro_data['introduction']
        enhanced_content['total_cost'] += intro_data['cost']
        enhanced_content['total_tokens'] += intro_data['tokens_input'] + intro_data['tokens_output']
        
        # Process each topic
        for topic_id, topic_data in digest_content.items():
            self.logger.info(f"Enhancing topic: {topic_data['topic'].name}")
            
            # Generate topic summary
            topic_summary = self.ai_generator.generate_topic_summary(topic_data)
            enhanced_content['total_cost'] += topic_summary['cost']
            enhanced_content['total_tokens'] += topic_summary['tokens_input'] + topic_summary['tokens_output']
            
            # Enhance individual events
            enhanced_events = []
            for event_data in topic_data['events']:
                event_enhancement = self.ai_generator.enhance_event_summary(event_data)
                enhanced_content['total_cost'] += event_enhancement['cost']
                enhanced_content['total_tokens'] += event_enhancement['tokens_input'] + event_enhancement['tokens_output']
                
                enhanced_events.append({
                    'event': event_data['event'],
                    'score': event_data['score'],
                    'recommended_articles': event_data['recommended_articles'],
                    'enhanced_abstract': event_enhancement['enhanced_abstract'],
                    'key_facts': event_enhancement['key_facts'],
                    'perspectives': event_enhancement['perspectives'],
                    'article_count': len(event_data['primary_articles']) + len(event_data['secondary_articles'])
                })
            
            enhanced_content['topics'][topic_id] = {
                'topic': topic_data['topic'],
                'total_score': topic_data['total_score'],
                'topic_abstract': topic_summary['topic_abstract'],
                'main_facts': topic_summary['main_facts'],
                'perspectives': topic_summary['perspectives'],
                'events': enhanced_events
            }
        
        self.logger.info(
            f"AI enhancement completed: "
            f"${enhanced_content['total_cost']:.4f} cost, "
            f"{enhanced_content['total_tokens']} tokens"
        )
        
        return enhanced_content
    
    def _create_digest_record(
        self, 
        user: User, 
        target_date: datetime, 
        enhanced_content: Dict[str, Any],
        user_preferences: Dict[str, Any]
    ) -> Digest:
        """
        Create and save digest record to database.
        
        Creates the main Digest record along with related DigestTopic and
        DigestStory records in a single database transaction.
        
        Args:
            user: User the digest is for
            target_date: Date the digest covers
            enhanced_content: AI-enhanced content structure
            user_preferences: User's digest preferences
            
        Returns:
            Created Digest instance
        """
        with transaction.atomic():
            # Create main digest record
            digest = Digest.objects.create(
                user=user,
                date=target_date.date(),
                title=self._generate_digest_title(target_date, enhanced_content),
                introduction=enhanced_content.get('introduction', ''),
                html_content=self._format_digest_html(enhanced_content),
                generation_status='COMPLETED',
                articles_processed=sum(
                    sum(len(event['recommended_articles']) for event in topic_data['events'])
                    for topic_data in enhanced_content['topics'].values()
                ),
                events_included=sum(
                    len(topic_data['events']) 
                    for topic_data in enhanced_content['topics'].values()
                ),
                topics_included=len(enhanced_content['topics']),
                generation_cost_usd=enhanced_content.get('total_cost', Decimal('0.0')),
                generation_tokens_total=enhanced_content.get('total_tokens', 0),
                user_preferences=user_preferences
            )
            
            # Create topic records
            for topic_id, topic_data in enhanced_content['topics'].items():
                digest_topic = DigestTopic.objects.create(
                    digest=digest,
                    topic=topic_data['topic'],
                    abstract=topic_data['topic_abstract'],
                    main_facts=topic_data['main_facts'],
                    perspectives=topic_data['perspectives'],
                    event_count=len(topic_data['events']),
                    topic_score=float(topic_data['total_score'])
                )
                
                # Create story records for each event
                for event_data in topic_data['events']:
                    DigestStory.objects.create(
                        digest=digest,
                        digest_topic=digest_topic,
                        event=event_data['event'],
                        title=event_data['event'].title,
                        enhanced_abstract=event_data['enhanced_abstract'],
                        key_facts=event_data['key_facts'],
                        perspectives=event_data['perspectives'],
                        article_count=event_data['article_count'],
                        event_score=event_data['score'],
                        recommended_articles=[
                            {
                                'id': article.id,
                                'public_id': str(article.public_id),
                                'headline': article.headline,
                                'source': article.publication.name if article.publication else article.source_name,
                                'published_at': article.published_at.isoformat(),
                                'url': article.url
                            }
                            for article in event_data['recommended_articles']
                        ]
                    )
            
            self.logger.info(f"Created digest record {digest.public_id} for user {user.id}")
            return digest
    
    def _create_empty_digest_response(self, user: User, target_date: datetime, reason: str) -> Dict[str, Any]:
        """Create response for when no digest content is available."""
        digest = Digest.objects.create(
            user=user,
            date=target_date.date(),
            title=f"Daily Brief - {target_date.strftime('%B %d, %Y')}",
            introduction=f"No news found for your followed topics on {target_date.strftime('%B %d, %Y')}. Check back tomorrow for your personalized digest!",
            html_content="<p>No content available for this date.</p>",
            generation_status='COMPLETED',
            articles_processed=0,
            events_included=0,
            topics_included=0,
            generation_cost_usd=Decimal('0.0'),
            generation_tokens_total=0,
            error_message=reason
        )
        
        return {
            'digest': digest,
            'content': {},
            'success': True,
            'empty': True,
            'reason': reason
        }
    
    def _create_error_digest_record(self, user: User, target_date: datetime, error: str) -> Digest:
        """Create digest record for failed generation."""
        return Digest.objects.create(
            user=user,
            date=target_date.date(),
            title=f"Daily Brief - {target_date.strftime('%B %d, %Y')} (Error)",
            introduction="We encountered an issue generating your digest. Please try again later.",
            html_content="<p>Error generating digest content.</p>",
            generation_status='FAILED',
            articles_processed=0,
            events_included=0,
            topics_included=0,
            generation_cost_usd=Decimal('0.0'),
            generation_tokens_total=0,
            error_message=error
        )
    
    def _get_existing_digest(self, user: User, target_date: datetime) -> Optional[Digest]:
        """Check for existing digest for user and date."""
        return Digest.objects.filter(
            user=user,
            date=target_date.date()
        ).first()
    
    def _extract_digest_content(self, digest: Digest) -> Dict[str, Any]:
        """Extract structured content from existing digest."""
        content = {
            'introduction': digest.introduction,
            'topics': {}
        }
        
        # Get related topic and story data
        for digest_topic in digest.digest_topics.all():
            topic_id = digest_topic.topic_id
            
            events = []
            for story in digest_topic.stories.all():
                events.append({
                    'event': story.event,
                    'enhanced_abstract': story.enhanced_abstract,
                    'key_facts': story.key_facts,
                    'perspectives': story.perspectives,
                    'recommended_articles': story.recommended_articles,
                    'score': story.event_score,
                    'article_count': story.article_count
                })
            
            content['topics'][topic_id] = {
                'topic': digest_topic.topic,
                'topic_abstract': digest_topic.abstract,
                'main_facts': digest_topic.main_facts,
                'perspectives': digest_topic.perspectives,
                'events': events,
                'total_score': digest_topic.topic_score
            }
        
        return content
    
    def _generate_digest_title(self, target_date: datetime, enhanced_content: Dict[str, Any]) -> str:
        """
        Generate a descriptive title for the digest.
        
        Args:
            target_date: Date the digest covers
            enhanced_content: Enhanced content structure
            
        Returns:
            Generated digest title
        """
        date_str = target_date.strftime('%B %d, %Y')
        
        if not enhanced_content.get('topics'):
            return f"Daily Brief - {date_str}"
        
        # Get top topic name for more descriptive title
        topics = list(enhanced_content['topics'].values())
        if topics:
            top_topic = max(topics, key=lambda t: t['total_score'])
            return f"Daily Brief - {date_str} (featuring {top_topic['topic'].name})"
        
        return f"Daily Brief - {date_str}"
    
    def _format_digest_html(self, enhanced_content: Dict[str, Any]) -> str:
        """
        Format enhanced content as HTML for storage and display.
        
        Args:
            enhanced_content: Enhanced content structure
            
        Returns:
            Formatted HTML string
        """
        html_parts = []
        
        # Introduction
        introduction = enhanced_content.get('introduction', '')
        if introduction:
            html_parts.append(f'<div class="digest-introduction">{introduction}</div>')
        
        # Topics
        for topic_data in enhanced_content.get('topics', {}).values():
            topic = topic_data['topic']
            
            html_parts.append(f'<section class="digest-topic" data-topic-id="{topic.id}">')
            html_parts.append(f'<h2>{topic.name}</h2>')
            
            # Topic abstract
            if topic_data.get('topic_abstract'):
                html_parts.append(f'<p class="topic-abstract">{topic_data["topic_abstract"]}</p>')
            
            # Main facts
            if topic_data.get('main_facts'):
                html_parts.append('<div class="main-facts">')
                html_parts.append('<h3>Key Facts</h3>')
                html_parts.append('<ul>')
                for fact in topic_data['main_facts']:
                    html_parts.append(f'<li>{fact}</li>')
                html_parts.append('</ul>')
                html_parts.append('</div>')
            
            # Perspectives
            if topic_data.get('perspectives'):
                html_parts.append('<div class="perspectives">')
                html_parts.append('<h3>Perspectives</h3>')
                html_parts.append('<ul>')
                for perspective in topic_data['perspectives']:
                    html_parts.append(f'<li>{perspective}</li>')
                html_parts.append('</ul>')
                html_parts.append('</div>')
            
            # Events/Stories
            for event_data in topic_data.get('events', []):
                event = event_data['event']
                
                html_parts.append(f'<article class="digest-story" data-event-id="{event.id}">')
                html_parts.append(f'<h4>{event.title}</h4>')
                
                if event_data.get('enhanced_abstract'):
                    html_parts.append(f'<p class="story-abstract">{event_data["enhanced_abstract"]}</p>')
                
                # Key facts for event
                if event_data.get('key_facts'):
                    html_parts.append('<div class="event-facts">')
                    html_parts.append('<h5>Key Facts</h5>')
                    html_parts.append('<ul>')
                    for fact in event_data['key_facts']:
                        html_parts.append(f'<li>{fact}</li>')
                    html_parts.append('</ul>')
                    html_parts.append('</div>')
                
                # Recommended articles
                if event_data.get('recommended_articles'):
                    html_parts.append('<div class="recommended-articles">')
                    html_parts.append('<h5>Read More</h5>')
                    html_parts.append('<ul>')
                    for article_data in event_data['recommended_articles']:
                        html_parts.append(
                            f'<li><a href="{article_data["url"]}" data-article-id="{article_data["public_id"]}">' +
                            f'{article_data["headline"]} - {article_data["source"]}</a></li>'
                        )
                    html_parts.append('</ul>')
                    html_parts.append('</div>')
                
                html_parts.append('</article>')
            
            html_parts.append('</section>')
        
        return '\n'.join(html_parts) 