"""
DigestAIGenerator Service

Handles AI-powered content synthesis for digest generation.
Responsible for:
- Generating overall digest introductions
- Creating topic-level summaries with facts and perspectives
- Enhancing event summaries from multiple article sources
- Synthesizing different viewpoints and opinions
"""

import logging
import json
import re
from typing import Dict, List, Any, Optional
from decimal import Decimal

from apps.aiproviders.services import AIProviderService
from apps.articles.models import Article
from apps.content.analyzer.models import Event
from apps.feeds.models import Topic
from apps.content.digest.prompt_templates import (
    DigestPrompts, 
    DigestFallbacks,
    get_digest_prompt,
    get_digest_validator
)

logger = logging.getLogger(__name__)


class DigestAIGenerator:
    """
    Service for AI-powered content synthesis in digest generation.
    
    This service handles all AI interactions for creating enhanced digest content:
    - Overall digest introductions that summarize the day's news
    - Topic-level abstracts synthesizing multiple events
    - Event summaries that combine perspectives from multiple articles
    - Fact and opinion extraction and synthesis
    
    Uses centralized prompt templates from prompt_templates.py for consistency.
    """
    
    def __init__(self):
        self.ai_service = AIProviderService()
        self.logger = logger
        
        # Track costs and tokens for optimization
        self.total_cost = Decimal('0.0')
        self.total_tokens_input = 0
        self.total_tokens_output = 0
    
    def generate_digest_introduction(self, digest_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate overall digest headline and introduction summarizing the day's news.
        
        Creates a compelling headline and friendly, informative introduction that gives users a preview
        of what's in their personalized digest.
        
        Args:
            digest_data: Complete digest content structure from content selector
            
        Returns:
            Dict with:
            - headline: Generated headline text
            - introduction: Generated introduction text
            - cost: Cost of AI generation
            - tokens_input/output: Token usage
        """
        self.logger.info("Generating digest headline and introduction")
        
        # Extract topic summaries for the introduction
        topic_summaries = []
        total_events = 0
        total_articles = 0
        
        # Handle the new data structure with digest_topics containing abstracts
        digest_topics = digest_data.get('digest_topics', [])
        topics_data = digest_data.get('topics_data', [])
        strategy = digest_data.get('strategy', 'unknown')
        
        # Process topic summaries based on strategy
        if strategy == 'articles_based_comprehensive':
            # Handle articles-based strategy with DigestTopic objects
            for digest_topic in digest_topics:
                topic_summaries.append({
                    'name': digest_topic.topic.name,
                    'topic_abstract': digest_topic.topic_abstract,
                    'story_count': digest_topic.stories.count()
                })
                total_articles += digest_topic.stories.count()
        else:
            # Handle both old and new data structures
            for topic_data in topics_data:
                topic = topic_data.get('topic')
                
                # Handle articles-based strategy
                if strategy == 'articles_based_comprehensive' and 'articles' in topic_data:
                    articles = topic_data.get('articles', [])
                    total_articles += len(articles)
                    
                    # Create brief topic preview
                    topic_summaries.append({
                        'name': topic.name,
                        'article_count': len(articles),
                        'articles': [article.headline for article in articles[:2]]  # Top 2 articles
                    })
                
                # Handle events-based strategy
                else:
                    events = topic_data.get('events', [])
                    fallback_mode = topic_data.get('fallback_mode', False)
                    
                    if fallback_mode:
                        # For fallback mode, we don't have events but we have the topic
                        topic_summaries.append({
                            'name': topic.name,
                            'event_count': 1,  # Represent as 1 story in fallback mode
                            'top_events': ['Latest developments']
                        })
                        total_events += 1
                    else:
                        # Regular event-based mode
                        total_events += len(events)
                        
                        # Create brief topic preview
                        event_titles = [event['event'].title for event in events[:2]]  # Top 2 events
                        topic_summaries.append({
                            'name': topic.name,
                            'event_count': len(events),
                            'top_events': event_titles
                        })
        
        # Create structured prompt using centralized template
        prompt = DigestPrompts.digest_introduction_prompt(topic_summaries, total_events)
        
        try:
            response = self.ai_service.call_llm(
                operation='digest_introduction',
                prompt=prompt,
                max_tokens=300,
                temperature=0.4  # Slightly creative but consistent
            )
            
            # Track costs
            cost = response.usage.get('total_cost', 0)
            tokens_in = response.usage.get('prompt_tokens', 0)
            tokens_out = response.usage.get('completion_tokens', 0)
            
            self._update_costs(cost, tokens_in, tokens_out)
            
            # Parse the JSON response
            try:
                import json
                import re
                
                # Clean the response content - remove markdown code blocks and extra whitespace
                content = response.content.strip()
                
                # Remove markdown code blocks if present
                if content.startswith('```'):
                    # Extract content between ```json and ``` or just between ``` and ```
                    json_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', content, re.DOTALL)
                    if json_match:
                        content = json_match.group(1).strip()
                    else:
                        # Fallback: remove first and last lines if they start with ```
                        lines = content.split('\n')
                        if lines[0].startswith('```'):
                            lines = lines[1:]
                        if lines and lines[-1].startswith('```'):
                            lines = lines[:-1]
                        content = '\n'.join(lines).strip()
                
                parsed_response = json.loads(content)
                headline = parsed_response.get('headline', '').strip()
                introduction = parsed_response.get('introduction', '').strip()
                
                # Validate that we got both parts
                if not headline or not introduction:
                    raise ValueError("Missing headline or introduction in response")
                
                self.logger.info(f"Generated digest headline ({len(headline)} chars) and introduction ({len(introduction)} chars)")
                
                return {
                    'headline': headline,
                    'introduction': introduction,
                    'cost': Decimal(str(cost)),
                    'tokens_input': tokens_in,
                    'tokens_output': tokens_out
                }
                
            except (json.JSONDecodeError, ValueError, KeyError) as e:
                # Fallback: treat entire response as introduction, generate simple headline
                self.logger.warning(f"Failed to parse structured response, using fallback: {e}")
                content = response.content.strip()
                fallback_headline = f"Your Daily Brief for {total_events + total_articles} Stories"
                
                return {
                    'headline': fallback_headline,
                    'introduction': content,
                    'cost': Decimal(str(cost)),
                    'tokens_input': tokens_in,
                    'tokens_output': tokens_out,
                    'parsing_error': str(e)
                }
            
        except Exception as e:
            self.logger.error(f"Failed to generate digest introduction: {e}")
            # Generate fallback headline and introduction
            fallback_headline = f"Your Daily Brief - {len(topic_summaries)} Topics"
            fallback_intro = DigestFallbacks.get_fallback_introduction(topic_summaries, total_events)
            
            return {
                'headline': fallback_headline,
                'introduction': fallback_intro,
                'cost': Decimal('0.0'),
                'tokens_input': 0,
                'tokens_output': 0,
                'error': str(e)
            }
    
    def generate_comprehensive_topic_summary(self, topic_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate comprehensive topic summary for articles-based digests.
        
        Creates detailed topic summaries with:
        - 60-120 word abstract
        - Up to 5 key events (60 words max each)
        - Up to 3 key perspectives (verbatim quotes/opinions)
        - Exactly 3 recommended articles
        
        Args:
            topic_data: Topic data with articles containing structured summaries
            
        Returns:
            Dict with comprehensive topic content matching enhanced format
        """
        topic = topic_data['topic']
        articles = topic_data['articles']
        
        self.logger.info(f"Generating comprehensive summary for topic '{topic.name}' with {len(articles)} articles")
        
        # Collect content from article summaries - cluster everything together
        clustered_articles = []
        
        for article in articles:
            try:
                summary = article.structured_summary
                if summary:
                    article_data = {
                        'id': article.id,  # Add article ID for AI reference
                        'headline': summary.headline or article.title,
                        'longer_abstract': summary.longer_abstract or summary.abstract,
                        'source': article.publication.name if article.publication else article.source_name,
                        'published': article.published_at.strftime('%Y-%m-%d') if article.published_at else 'Recent'
                    }
                    
                    # Cluster all content with the article
                    if summary.facts:
                        article_data['facts'] = summary.facts
                    if summary.opinions:
                        article_data['opinions'] = summary.opinions
                    if summary.impact:
                        article_data['impacts'] = summary.impact
                    
                    clustered_articles.append(article_data)
            except Exception as e:
                self.logger.warning(f"Error processing summary for article {article.id}: {e}")
                continue
        
        if not clustered_articles:
            self.logger.warning(f"No article summaries available for comprehensive topic '{topic.name}'")
            return DigestFallbacks.get_fallback_topic_summary_response(topic.name)
        
        # Limit articles for large datasets to prevent AI overload
        if len(clustered_articles) > 20:
            self.logger.warning(f"Large dataset detected ({len(clustered_articles)} articles), limiting to 20 most recent")
            # Sort by published date and take most recent 20
            clustered_articles = sorted(
                clustered_articles, 
                key=lambda a: a.get('published', '2000-01-01'), 
                reverse=True
            )[:20]
        
        # Retry mechanism for AI generation with validation
        max_retries = 2
        for attempt in range(max_retries + 1):
            try:
                # Create AI prompt using clustered article data
                prompt = DigestPrompts.comprehensive_topic_summary_prompt(
                    topic.name, clustered_articles
                )
                
                response = self.ai_service.call_llm(
                    operation='digest_comprehensive_topic',
                    prompt=prompt,
                    max_tokens=1200,
                    temperature=0.2  # More factual, focused
                )
                
                # Track costs
                cost = response.usage.get('total_cost', 0)
                tokens_in = response.usage.get('prompt_tokens', 0)
                tokens_out = response.usage.get('completion_tokens', 0)
                
                self._update_costs(cost, tokens_in, tokens_out)
                
                # Parse structured response using centralized validator
                validator = get_digest_validator('digest_comprehensive_topic')
                if validator:
                    validation_result = validator(response.content)
                    if validation_result.get('success'):
                        parsed_content = validation_result['data']
                        
                        self.logger.info(
                            f"Generated comprehensive topic summary for '{topic.name}' (attempt {attempt + 1}): "
                            f"topic_abstract={len(parsed_content.get('topic_abstract', '').split())}w, "
                            f"{len(parsed_content.get('stories', []))} stories"
                        )
                        
                        return {
                            **parsed_content,
                            'cost': Decimal(str(cost)),
                            'tokens_input': tokens_in,
                            'tokens_output': tokens_out,
                            'model_used': response.model or 'gpt-4.1-mini',
                            'attempt': attempt + 1
                        }
                    else:
                        # Log validation failure and retry if attempts remaining
                        validation_error = validation_result.get('error', 'Unknown validation error')
                        self.logger.warning(
                            f"Validation failed for comprehensive topic '{topic.name}' (attempt {attempt + 1}): {validation_error}"
                        )
                        
                        if attempt < max_retries:
                            self.logger.info(f"Retrying topic '{topic.name}' generation (attempt {attempt + 2})")
                            continue
                        else:
                            # Final attempt failed, use fallback parsing
                            self.logger.error(f"All attempts failed for topic '{topic.name}', using fallback parsing")
                            parsed_content = self._parse_comprehensive_fallback(response.content, topic.name)
                            
                            return {
                                **parsed_content,
                                'cost': Decimal(str(cost)),
                                'tokens_input': tokens_in,
                                'tokens_output': tokens_out,
                                'model_used': response.model or 'gpt-4.1-mini',
                                'attempt': attempt + 1,
                                'validation_failed': True,
                                'validation_error': validation_error
                            }
                else:
                    # No validator available, use fallback parsing
                    parsed_content = self._parse_comprehensive_fallback(response.content, topic.name)
                    
                    return {
                        **parsed_content,
                        'cost': Decimal(str(cost)),
                        'tokens_input': tokens_in,
                        'tokens_output': tokens_out,
                        'model_used': response.model or 'gpt-4.1-mini',
                        'attempt': attempt + 1
                    }
                    
            except Exception as e:
                self.logger.error(f"Failed to generate comprehensive topic summary for '{topic.name}' (attempt {attempt + 1}): {e}")
                
                if attempt < max_retries:
                    self.logger.info(f"Retrying topic '{topic.name}' generation due to error (attempt {attempt + 2})")
                    continue
                else:
                    # All attempts failed, use comprehensive fallback
                    fallback_facts = []
                    fallback_opinions = []
                    for article in clustered_articles:
                        if article.get('facts'):
                            fallback_facts.extend(article['facts'])
                        if article.get('opinions'):
                            fallback_opinions.extend(article['opinions'])
                    
                    return self._get_fallback_comprehensive_summary(
                        topic.name, fallback_facts, fallback_opinions, articles, str(e)
                    )
    
    def generate_digest_conclusion(
        self, 
        topic_summaries: List[Dict],
        introduction: str = None,
        topic_abstracts: List[Dict] = None
    ) -> Dict[str, Any]:
        """
        Generate brief digest conclusion summarizing main topics.
        
        Creates a concise wrap-up that recaps the main topic summaries
        for daily digest readers, using introduction and topic abstracts
        for richer context and better tone continuity.
        
        Args:
            topic_summaries: List of topic summary data
            introduction: The digest introduction for tone consistency
            topic_abstracts: Full topic abstracts for deeper context
            
        Returns:
            Dict with conclusion content and processing metadata
        """
        self.logger.info(f"Generating digest conclusion for {len(topic_summaries)} topics")
        
        # Create structured prompt using centralized template with enhanced context
        prompt = DigestPrompts.digest_conclusion_prompt(
            topic_summaries, 
            introduction, 
            topic_abstracts
        )
        
        try:
            response = self.ai_service.call_llm(
                operation='digest_conclusion',
                prompt=prompt,
                max_tokens=400,
                temperature=0.3  # Balanced creativity
            )
            
            # Track costs
            cost = response.usage.get('total_cost', 0)
            tokens_in = response.usage.get('prompt_tokens', 0)
            tokens_out = response.usage.get('completion_tokens', 0)
            
            self._update_costs(cost, tokens_in, tokens_out)
            
            conclusion = response.content.strip()
            
            self.logger.info(f"Generated digest conclusion ({len(conclusion)} chars)")
            
            return {
                'content': conclusion,
                'cost': Decimal(str(cost)),
                'tokens_input': tokens_in,
                'tokens_output': tokens_out
            }
            
        except Exception as e:
            self.logger.error(f"Failed to generate digest conclusion: {e}")
            return {
                'content': DigestFallbacks.get_fallback_conclusion(topic_summaries),
                'cost': Decimal('0.0'),
                'tokens_input': 0,
                'tokens_output': 0,
                'error': str(e)
            }
    
    def generate_topic_summary(self, topic_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate comprehensive topic summary using AI.
        
        Synthesizes information from multiple events and articles to create:
        - Topic abstract (2-3 sentence overview)
        - Main facts (top 5 facts across all events)
        - Key perspectives (different viewpoints/opinions)
        
        Args:
            topic_data: Topic content with events and articles
            
        Returns:
            Dict with synthesized topic content and processing metadata
        """
        topic = topic_data['topic']
        events = topic_data.get('events', [])
        
        # Check if this is fallback mode (no events)
        if not events:
            self.logger.info(f"Topic '{topic.name}' has no events, using fallback mode")
            # Use the fallback topic summary generator instead
            return self.generate_fallback_topic_summary(topic_data)
        
        self.logger.info(f"Generating summary for topic '{topic.name}' with {len(events)} events")
        
        # Collect enhanced content from events and article summaries
        all_facts = []
        all_opinions = []
        event_abstracts = []
        
        for event_info in events:
            event = event_info['event']
            
            # Use enhanced content if available, otherwise fall back to original
            enhanced_abstract = event_info.get('enhanced_abstract', event.enhanced_abstract or event.abstract)
            enhanced_facts = event_info.get('enhanced_facts', event.enhanced_facts or [])
            enhanced_perspectives = event_info.get('enhanced_perspectives', event.enhanced_perspectives or [])
            
            # Add enhanced event abstract
            if enhanced_abstract:
                event_abstracts.append(f"Event: {event.title} - {enhanced_abstract}")
            
            # Use enhanced facts and perspectives
            if enhanced_facts:
                all_facts.extend(enhanced_facts)
            if enhanced_perspectives:
                all_opinions.extend(enhanced_perspectives)
            
            # Also collect from article summaries as backup
            articles = event_info['primary_articles'] + event_info['secondary_articles']
            for article in articles:
                if hasattr(article, 'structured_summary') and article.structured_summary:
                    summary = article.structured_summary
                    if summary.facts and not enhanced_facts:  # Only use if no enhanced facts
                        all_facts.extend(summary.facts)
                    if summary.opinions and not enhanced_perspectives:  # Only use if no enhanced perspectives
                        all_opinions.extend(summary.opinions)
        
        # Deduplicate and limit content for prompt
        unique_facts = list(dict.fromkeys(all_facts))[:20]  # Remove duplicates, limit to 20
        unique_opinions = list(dict.fromkeys(all_opinions))[:15]  # Remove duplicates, limit to 15
        
        # Create AI prompt using centralized template
        prompt = DigestPrompts.topic_summary_prompt(
            topic.name, event_abstracts, unique_facts, unique_opinions
        )
        
        try:
            response = self.ai_service.call_llm(
                operation='digest_topic_summary',
                prompt=prompt,
                max_tokens=800,
                temperature=0.3
            )
            
            # Track costs
            cost = response.usage.get('total_cost', 0)
            tokens_in = response.usage.get('prompt_tokens', 0)
            tokens_out = response.usage.get('completion_tokens', 0)
            
            self._update_costs(cost, tokens_in, tokens_out)
            
            # Parse structured response using centralized validator
            validator = get_digest_validator('digest_topic_summary')
            if validator:
                validation_result = validator(response.content)
                if validation_result.get('success'):
                    parsed_content = validation_result['data']
                else:
                    # Fallback to simple parsing
                    parsed_content = DigestPrompts.parse_response_with_fallback(response.content)
            else:
                parsed_content = DigestPrompts.parse_response_with_fallback(response.content)
            
            self.logger.info(
                f"Generated topic summary for '{topic.name}': "
                f"{len(parsed_content.get('main_facts', []))} facts, "
                f"{len(parsed_content.get('perspectives', []))} perspectives"
            )
            
            return {
                **parsed_content,
                'cost': Decimal(str(cost)),
                'tokens_input': tokens_in,
                'tokens_output': tokens_out
            }
            
        except Exception as e:
            self.logger.error(f"Failed to generate topic summary for '{topic.name}': {e}")
            return {
                'topic_abstract': DigestFallbacks.get_fallback_topic_abstract(topic.name, event_abstracts),
                'main_facts': unique_facts[:5],
                'perspectives': unique_opinions[:5],
                'cost': Decimal('0.0'),
                'tokens_input': 0,
                'tokens_output': 0,
                'error': str(e)
            }
    
    def enhance_event_summary(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create enhanced event summary from multiple articles.
        
        Synthesizes multiple article perspectives into a comprehensive event summary
        with enhanced abstract, key facts, and diverse perspectives.
        
        Args:
            event_data: Event data with primary and secondary articles
            
        Returns:
            Dict with enhanced event content and processing metadata
        """
        event = event_data['event']
        all_articles = event_data['primary_articles'] + event_data['secondary_articles']
        
        self.logger.info(f"Enhancing summary for event '{event.title}' with {len(all_articles)} articles")
        
        # Collect article summaries
        article_summaries = []
        facts = []
        opinions = []
        
        for article in all_articles:
            if hasattr(article, 'structured_summary') and article.structured_summary:
                summary = article.structured_summary
                article_summaries.append({
                    'headline': summary.headline,
                    'abstract': summary.abstract,
                    'source': article.publication.name if article.publication else article.source_name
                })
                
                if summary.facts:
                    facts.extend(summary.facts)
                if summary.opinions:
                    opinions.extend(summary.opinions)
        
        if not article_summaries:
            self.logger.warning(f"No article summaries available for event '{event.title}'")
            return DigestFallbacks.get_fallback_event_summary(event.title, event.abstract or '')
        
        # Deduplicate content
        unique_facts = list(dict.fromkeys(facts))
        unique_opinions = list(dict.fromkeys(opinions))
        
        # Create AI prompt using centralized template
        prompt = DigestPrompts.event_enhancement_prompt(
            event.title, event.abstract or '', article_summaries, unique_facts, unique_opinions
        )
        
        try:
            response = self.ai_service.call_llm(
                operation='digest_event_enhancement',
                prompt=prompt,
                max_tokens=600,
                temperature=0.2  # More factual, less creative
            )
            
            # Track costs
            cost = response.usage.get('total_cost', 0)
            tokens_in = response.usage.get('prompt_tokens', 0)
            tokens_out = response.usage.get('completion_tokens', 0)
            
            self._update_costs(cost, tokens_in, tokens_out)
            
            # Parse structured response using centralized validator
            validator = get_digest_validator('digest_event_enhancement')
            if validator:
                validation_result = validator(response.content)
                if validation_result.get('success'):
                    parsed_content = validation_result['data']
                else:
                    # Fallback to simple parsing
                    parsed_content = DigestPrompts.parse_response_with_fallback(response.content)
            else:
                parsed_content = DigestPrompts.parse_response_with_fallback(response.content)
            
            self.logger.info(f"Enhanced event summary for '{event.title}'")
            
            return {
                **parsed_content,
                'cost': Decimal(str(cost)),
                'tokens_input': tokens_in,
                'tokens_output': tokens_out
            }
            
        except Exception as e:
            self.logger.error(f"Failed to enhance event summary for '{event.title}': {e}")
            return DigestFallbacks.get_fallback_event_summary(event.title, event.abstract or '', unique_facts, unique_opinions, str(e))
    
    def enhance_event_summary_with_related(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create enhanced event summary from primary, secondary, and related articles.
        
        Synthesizes multiple article perspectives with importance weighting:
        - Primary articles: Core to the event (highest weight)
        - Secondary articles: Mention the event (medium weight)  
        - Related articles: From semantically similar events (lower weight)
        
        Args:
            event_data: Event data with primary, secondary, and related articles
            
        Returns:
            Dict with enhanced event content and processing metadata
        """
        event = event_data['event']
        primary_articles = event_data.get('primary_articles', [])
        secondary_articles = event_data.get('secondary_articles', [])
        related_articles = event_data.get('related_articles', [])
        
        total_articles = len(primary_articles) + len(secondary_articles) + len(related_articles)
        
        self.logger.info(
            f"Enhancing summary for event '{event.title}' with {total_articles} articles "
            f"(primary: {len(primary_articles)}, secondary: {len(secondary_articles)}, "
            f"related: {len(related_articles)})"
        )
        
        # Collect article summaries with importance weighting
        article_summaries = []
        facts = []
        opinions = []
        
        # Process primary articles (highest importance)
        for article in primary_articles:
            if hasattr(article, 'structured_summary') and article.structured_summary:
                summary = article.structured_summary
                article_summaries.append({
                    'headline': summary.headline,
                    'abstract': summary.abstract,
                    'source': article.publication.name if article.publication else article.source_name,
                    'importance': 'PRIMARY',
                    'weight_description': 'Core event coverage'
                })
                
                if summary.facts:
                    facts.extend(summary.facts)
                if summary.opinions:
                    opinions.extend(summary.opinions)
        
        # Process secondary articles (medium importance)
        for article in secondary_articles:
            if hasattr(article, 'structured_summary') and article.structured_summary:
                summary = article.structured_summary
                article_summaries.append({
                    'headline': summary.headline,
                    'abstract': summary.abstract,
                    'source': article.publication.name if article.publication else article.source_name,
                    'importance': 'SECONDARY',
                    'weight_description': 'Event mentioned in broader context'
                })
                
                if summary.facts:
                    facts.extend(summary.facts)
                if summary.opinions:
                    opinions.extend(summary.opinions)
        
        # Process related articles (lower importance)
        for article in related_articles:
            if hasattr(article, 'structured_summary') and article.structured_summary:
                summary = article.structured_summary
                article_summaries.append({
                    'headline': summary.headline,
                    'abstract': summary.abstract,
                    'source': article.publication.name if article.publication else article.source_name,
                    'importance': 'RELATED',
                    'weight_description': 'Related story providing context'
                })
                
                # Use fewer facts/opinions from related articles to avoid noise
                if summary.facts:
                    facts.extend(summary.facts[:2])  # Limit to 2 facts from related
                if summary.opinions:
                    opinions.extend(summary.opinions[:1])  # Limit to 1 opinion from related
        
        if not article_summaries:
            self.logger.warning(f"No article summaries available for event '{event.title}'")
            return DigestFallbacks.get_fallback_event_summary(event.title, event.abstract or '')
        
        # Deduplicate content
        unique_facts = list(dict.fromkeys(facts))
        unique_opinions = list(dict.fromkeys(opinions))
        
        # Create AI prompt with importance weighting using centralized template
        prompt = DigestPrompts.event_enhancement_with_weighting_prompt(
            event.title, event.abstract or '', article_summaries, unique_facts, unique_opinions
        )
        
        try:
            response = self.ai_service.call_llm(
                operation='digest_event_enhancement',
                prompt=prompt,
                max_tokens=700,  # Slightly more tokens for comprehensive summary
                temperature=0.2  # More factual, less creative
            )
            
            # Track costs
            cost = response.usage.get('total_cost', 0)
            tokens_in = response.usage.get('prompt_tokens', 0)
            tokens_out = response.usage.get('completion_tokens', 0)
            
            self._update_costs(cost, tokens_in, tokens_out)
            
            # Parse structured response using centralized validator
            validator = get_digest_validator('digest_event_enhancement')
            if validator:
                validation_result = validator(response.content)
                if validation_result.get('success'):
                    parsed_content = validation_result['data']
                else:
                    # Fallback to simple parsing
                    parsed_content = DigestPrompts.parse_response_with_fallback(response.content)
            else:
                parsed_content = DigestPrompts.parse_response_with_fallback(response.content)
            
            self.logger.info(f"Enhanced event summary for '{event.title}' with {total_articles} articles")
            
            return {
                **parsed_content,
                'cost': Decimal(str(cost)),
                'tokens_input': tokens_in,
                'tokens_output': tokens_out,
                'articles_used': total_articles,
                'primary_count': len(primary_articles),
                'secondary_count': len(secondary_articles),
                'related_count': len(related_articles)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to enhance event summary for '{event.title}': {e}")
            return DigestFallbacks.get_fallback_event_summary(event.title, event.abstract or '', unique_facts, unique_opinions, str(e))
    
    def generate_fallback_topic_summary(self, topic_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate AI-powered topic summary for fallback digest using article summaries.
        
        Creates a comprehensive topic summary with the same structure as article summaries:
        - Title (headline for the topic)
        - Abstract (≤60 words overview)
        - Key facts (synthesized from articles)
        - Opinions (synthesized viewpoints)
        - Impacts (synthesized impact points)
        
        Args:
            topic_data: Topic data with articles containing structured summaries
            
        Returns:
            Dict with synthesized topic content matching article summary structure
        """
        topic = topic_data['topic']
        articles = topic_data['articles']
        
        self.logger.info(f"Generating AI fallback summary for topic '{topic.name}' with {len(articles)} articles")
        
        # Collect content from article summaries
        article_summaries = []
        all_facts = []
        all_opinions = []
        all_impacts = []
        all_longer_abstracts = []
        
        for article in articles:
            try:
                summary = article.structured_summary
                if summary:
                    article_summaries.append({
                        'id': article.id,  # Add article ID for AI reference
                        'headline': summary.headline or article.title,
                        'longer_abstract': summary.longer_abstract,
                        'source': article.publication.name if article.publication else article.source_name,
                        'published': article.published_at.strftime('%Y-%m-%d') if article.published_at else 'Recent'
                    })
                    
                    if summary.facts:
                        all_facts.extend(summary.facts)
                    if summary.opinions:
                        all_opinions.extend(summary.opinions)
                    if summary.impact:
                        all_impacts.extend(summary.impact)
                    if summary.longer_abstract:
                        all_longer_abstracts.append(summary.longer_abstract)
            except Exception as e:
                self.logger.warning(f"Error processing summary for article {article.id}: {e}")
                continue
        
        if not article_summaries:
            self.logger.warning(f"No article summaries available for fallback topic '{topic.name}'")
            return DigestFallbacks.get_fallback_topic_summary_response(topic.name)
        
        # Deduplicate content for prompt
        unique_facts = list(dict.fromkeys(all_facts))[:40]  # Increased for 20 articles
        unique_opinions = list(dict.fromkeys(all_opinions))[:30]  # Increased for 20 articles
        unique_impacts = list(dict.fromkeys(all_impacts))[:25]  # Increased for 20 articles
        
        # Create AI prompt using centralized template
        prompt = DigestPrompts.fallback_topic_summary_prompt(
            topic.name, article_summaries, unique_facts, unique_opinions, unique_impacts
        )
        
        try:
            response = self.ai_service.call_llm(
                operation='digest_fallback_topic',
                prompt=prompt,
                max_tokens=800,
                temperature=0.25  # Balanced between consistency and synthesis
            )
            
            # Track costs
            cost = response.usage.get('total_cost', 0)
            tokens_in = response.usage.get('prompt_tokens', 0)
            tokens_out = response.usage.get('completion_tokens', 0)
            
            self._update_costs(cost, tokens_in, tokens_out)
            
            # Parse structured response using centralized validator
            validator = get_digest_validator('digest_fallback_topic')
            if validator:
                validation_result = validator(response.content)
                if validation_result.get('success'):
                    parsed_content = validation_result['data']
                else:
                    # Fallback to simple parsing
                    parsed_content = DigestPrompts.parse_fallback_topic_with_heuristics(response.content)
            else:
                parsed_content = DigestPrompts.parse_fallback_topic_with_heuristics(response.content)
            
            self.logger.info(
                f"Generated AI fallback topic summary for '{topic.name}': "
                f"title='{parsed_content.get('title', '')[:50]}...', "
                f"{len(parsed_content.get('facts', []))} facts, "
                f"{len(parsed_content.get('opinions', []))} opinions, "
                f"{len(parsed_content.get('impacts', []))} impacts"
            )
            
            return {
                **parsed_content,
                'cost': Decimal(str(cost)),
                'tokens_input': tokens_in,
                'tokens_output': tokens_out,
                'model_used': response.model or 'gpt-4o-mini'
            }
            
        except Exception as e:
            self.logger.error(f"Failed to generate AI fallback topic summary for '{topic.name}': {e}")
            return DigestFallbacks.get_fallback_topic_summary_response(topic.name, unique_facts, unique_opinions, unique_impacts, str(e))
    
    def _parse_comprehensive_fallback(self, response_content: str, topic_name: str) -> Dict[str, Any]:
        """Parse comprehensive topic response when validation fails."""
        # Try to extract sections from unstructured response
        lines = [line.strip() for line in response_content.split('\n') if line.strip()]
        
        # Try to find a JSON structure first
        try:
            json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
                # Convert new format to old format if needed for compatibility
                if 'stories' in parsed:
                    return {
                        'topic_abstract': parsed.get('topic_abstract', f"Key developments in {topic_name} from multiple news sources."),
                        'stories': parsed.get('stories', [])[:3]
                    }
                else:
                    # Legacy format fallback
                    return {
                        'topic_abstract': parsed.get('abstract', f"Key developments in {topic_name} from multiple news sources."),
                        'stories': []  # Empty stories for old format
                    }
        except:
            pass
        
        # Fallback to basic structure with story format
        return {
            'topic_abstract': f"Multiple important developments in {topic_name} across various news sources today.",
            'stories': [
                {
                    'headline': f"Key Developments in {topic_name}",
                    'abstract': f"Recent {topic_name} developments from news sources covering emerging trends and significant updates.",
                    'main_points': [
                        f"Recent {topic_name} developments from news sources",
                        f"Key {topic_name} stories reported today"
                    ],
                    'perspectives': [
                        f"Various expert opinions on {topic_name} developments"
                    ],
                    'read_more': [
                        {'article_id': '', 'title': f'Latest {topic_name} Coverage', 'source': 'Various', 'reason': 'Comprehensive coverage'}
                    ]
                }
            ]
        }
    
    def _get_fallback_comprehensive_summary(
        self,
        topic_name: str,
        facts: List[str] = None,
        opinions: List[str] = None,
        articles: List[Article] = None,
        error: str = None
    ) -> Dict[str, Any]:
        """Generate fallback comprehensive summary when AI fails."""
        
        # Try to use recent articles for recommendations
        recommended_articles = []
        if articles:
            recent_articles = sorted(articles, key=lambda a: a.published_at or a.created_at, reverse=True)[:3]
            for article in recent_articles:
                recommended_articles.append({
                    'article_id': str(article.id),
                    'title': article.title,
                    'source': article.publication.name if article.publication else article.source_name,
                    'reason': f'Recent {topic_name} coverage'
                })
        
        # Ensure we have exactly 3 recommendations
        while len(recommended_articles) < 3:
            recommended_articles.append({
                'article_id': '',
                'title': f'Latest {topic_name} News',
                'source': 'Various Sources',
                'reason': 'Comprehensive coverage'
            })
        
        return {
            'topic_abstract': f"Multiple significant developments in {topic_name} from various news sources today, covering key stories and emerging trends across different aspects of the field.",
            'stories': [
                {
                    'headline': f"Today's Key {topic_name} Developments",
                    'abstract': f"Recent {topic_name} developments from news sources covering emerging trends and significant updates across the sector.",
                    'main_points': (facts or [f"Recent {topic_name} developments", f"Key {topic_name} stories", f"Emerging {topic_name} trends"])[:5],
                    'perspectives': (opinions or [f"Expert analysis on {topic_name} trends"])[:3],
                    'read_more': recommended_articles[:3]
                }
            ],
            'cost': Decimal('0.0'),
            'tokens_input': 0,
            'tokens_output': 0,
            'model_used': 'fallback-mode',
            'error': error
        }
    
    def get_generation_metrics(self) -> Dict[str, Any]:
        """
        Get total metrics for the current generation session.
        
        Returns:
            Dict with total cost and token usage
        """
        return {
            'total_cost_usd': float(self.total_cost),
            'total_tokens_input': self.total_tokens_input,
            'total_tokens_output': self.total_tokens_output,
            'total_tokens': self.total_tokens_input + self.total_tokens_output
        }
    
    def _update_costs(self, cost: float, tokens_in: int, tokens_out: int):
        """Update running totals for cost and token tracking."""
        self.total_cost += Decimal(str(cost))
        self.total_tokens_input += tokens_in
        self.total_tokens_output += tokens_out 