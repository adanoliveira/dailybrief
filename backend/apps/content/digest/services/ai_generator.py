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

logger = logging.getLogger(__name__)


class DigestAIGenerator:
    """
    Service for AI-powered content synthesis in digest generation.
    
    This service handles all AI interactions for creating enhanced digest content:
    - Overall digest introductions that summarize the day's news
    - Topic-level abstracts synthesizing multiple events
    - Event summaries that combine perspectives from multiple articles
    - Fact and opinion extraction and synthesis
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
        Generate overall digest introduction summarizing the day's news.
        
        Creates a friendly, informative introduction that gives users a preview
        of what's in their personalized digest.
        
        Args:
            digest_data: Complete digest content structure from content selector
            
        Returns:
            Dict with:
            - introduction: Generated introduction text
            - cost: Cost of AI generation
            - tokens_input/output: Token usage
        """
        self.logger.info("Generating digest introduction")
        
        # Extract topic summaries for the introduction
        topic_summaries = []
        total_events = 0
        
        for topic_id, topic_content in digest_data.items():
            topic = topic_content['topic']
            events = topic_content['events']
            total_events += len(events)
            
            # Create brief topic preview
            event_titles = [event['event'].title for event in events[:2]]  # Top 2 events
            topic_summaries.append({
                'name': topic.name,
                'event_count': len(events),
                'top_events': event_titles
            })
        
        # Create structured prompt
        prompt = self._build_introduction_prompt(topic_summaries, total_events)
        
        try:
            response = self.ai_service.generate_completion(
                operation='digest_generation',
                prompt=prompt,
                max_tokens=300,
                temperature=0.4  # Slightly creative but consistent
            )
            
            # Track costs
            cost = response.usage.get('total_cost', 0)
            tokens_in = response.usage.get('prompt_tokens', 0)
            tokens_out = response.usage.get('completion_tokens', 0)
            
            self._update_costs(cost, tokens_in, tokens_out)
            
            introduction = response.content.strip()
            
            self.logger.info(f"Generated digest introduction ({len(introduction)} chars)")
            
            return {
                'introduction': introduction,
                'cost': Decimal(str(cost)),
                'tokens_input': tokens_in,
                'tokens_output': tokens_out
            }
            
        except Exception as e:
            self.logger.error(f"Failed to generate digest introduction: {e}")
            return {
                'introduction': self._get_fallback_introduction(topic_summaries, total_events),
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
        events = topic_data['events']
        
        self.logger.info(f"Generating summary for topic '{topic.name}' with {len(events)} events")
        
        # Collect all facts and opinions from article summaries
        all_facts = []
        all_opinions = []
        event_abstracts = []
        
        for event_info in events:
            event = event_info['event']
            articles = event_info['primary_articles'] + event_info['secondary_articles']
            
            # Add event abstract
            if event.abstract:
                event_abstracts.append(f"Event: {event.title} - {event.abstract}")
            
            # Collect facts and opinions from article summaries
            for article in articles:
                if hasattr(article, 'structured_summary') and article.structured_summary:
                    summary = article.structured_summary
                    if summary.facts:
                        all_facts.extend(summary.facts)
                    if summary.opinions:
                        all_opinions.extend(summary.opinions)
        
        # Deduplicate and limit content for prompt
        unique_facts = list(dict.fromkeys(all_facts))[:20]  # Remove duplicates, limit to 20
        unique_opinions = list(dict.fromkeys(all_opinions))[:15]  # Remove duplicates, limit to 15
        
        # Create AI prompt
        prompt = self._build_topic_summary_prompt(
            topic, event_abstracts, unique_facts, unique_opinions
        )
        
        try:
            response = self.ai_service.generate_completion(
                operation='digest_generation',
                prompt=prompt,
                max_tokens=800,
                temperature=0.3
            )
            
            # Track costs
            cost = response.usage.get('total_cost', 0)
            tokens_in = response.usage.get('prompt_tokens', 0)
            tokens_out = response.usage.get('completion_tokens', 0)
            
            self._update_costs(cost, tokens_in, tokens_out)
            
            # Parse structured response
            parsed_content = self._parse_topic_summary_response(response.content)
            
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
                'topic_abstract': self._get_fallback_topic_abstract(topic, event_abstracts),
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
            return self._get_fallback_event_summary(event)
        
        # Deduplicate content
        unique_facts = list(dict.fromkeys(facts))
        unique_opinions = list(dict.fromkeys(opinions))
        
        # Create AI prompt
        prompt = self._build_event_enhancement_prompt(
            event, article_summaries, unique_facts, unique_opinions
        )
        
        try:
            response = self.ai_service.generate_completion(
                operation='digest_generation',
                prompt=prompt,
                max_tokens=600,
                temperature=0.2  # More factual, less creative
            )
            
            # Track costs
            cost = response.usage.get('total_cost', 0)
            tokens_in = response.usage.get('prompt_tokens', 0)
            tokens_out = response.usage.get('completion_tokens', 0)
            
            self._update_costs(cost, tokens_in, tokens_out)
            
            # Parse structured response
            parsed_content = self._parse_event_summary_response(response.content)
            
            self.logger.info(f"Enhanced event summary for '{event.title}'")
            
            return {
                **parsed_content,
                'cost': Decimal(str(cost)),
                'tokens_input': tokens_in,
                'tokens_output': tokens_out
            }
            
        except Exception as e:
            self.logger.error(f"Failed to enhance event summary for '{event.title}': {e}")
            return self._get_fallback_event_summary(event, unique_facts, unique_opinions, str(e))
    
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
    
    def _build_introduction_prompt(self, topic_summaries: List[Dict], total_events: int) -> str:
        """Build prompt for digest introduction generation."""
        topics_preview = []
        for topic in topic_summaries:
            events_text = f"{topic['event_count']} event{'s' if topic['event_count'] != 1 else ''}"
            if topic['top_events']:
                events_text += f" including {', '.join(topic['top_events'][:2])}"
            topics_preview.append(f"- {topic['name']}: {events_text}")
        
        return f"""Write a friendly, informative introduction for a personalized daily news digest.

Today's digest covers {len(topic_summaries)} topics with {total_events} major events:
{chr(10).join(topics_preview)}

Write a 2-3 sentence introduction that:
1. Welcomes the reader to their daily brief
2. Highlights the main topics they'll find
3. Uses a warm, professional tone

Keep it concise and engaging. Start with "Good morning" or similar greeting."""
    
    def _build_topic_summary_prompt(
        self, 
        topic: Topic, 
        event_abstracts: List[str], 
        facts: List[str], 
        opinions: List[str]
    ) -> str:
        """Build prompt for topic summary generation."""
        return f"""Generate a comprehensive summary for the topic: {topic.name}

Event Information:
{chr(10).join(event_abstracts) if event_abstracts else "No event abstracts available"}

Available Facts:
{chr(10).join(f"• {fact}" for fact in facts[:15]) if facts else "No facts available"}

Available Opinions/Perspectives:
{chr(10).join(f"• {opinion}" for opinion in opinions[:10]) if opinions else "No opinions available"}

Generate exactly the following in JSON format:
{{
    "topic_abstract": "2-3 sentence overview of the main developments in {topic.name}",
    "main_facts": ["fact 1", "fact 2", "fact 3", "fact 4", "fact 5"],
    "perspectives": ["perspective 1", "perspective 2", "perspective 3", "perspective 4"]
}}

Requirements:
- topic_abstract: 2-3 sentences summarizing key developments
- main_facts: Up to 5 most important factual points (no opinions)
- perspectives: Up to 4 different viewpoints or opinions expressed
- Focus on synthesizing information across multiple sources
- Ensure JSON is valid and properly formatted"""
    
    def _build_event_enhancement_prompt(
        self, 
        event: Event, 
        article_summaries: List[Dict], 
        facts: List[str], 
        opinions: List[str]
    ) -> str:
        """Build prompt for event enhancement."""
        sources_text = chr(10).join(
            f"• {summary['source']}: {summary['headline']}" 
            for summary in article_summaries
        )
        
        abstracts_text = chr(10).join(
            f"• {summary['abstract']}" 
            for summary in article_summaries
        )
        
        return f"""Enhance this event summary by synthesizing multiple article perspectives:

Event: {event.title}
Original Abstract: {event.abstract or "No original abstract"}

Article Sources:
{sources_text}

Article Abstracts:
{abstracts_text}

Available Facts:
{chr(10).join(f"• {fact}" for fact in facts[:10]) if facts else "No facts available"}

Available Opinions:
{chr(10).join(f"• {opinion}" for opinion in opinions[:8]) if opinions else "No opinions available"}

Generate exactly the following in JSON format:
{{
    "enhanced_abstract": "3-4 sentence comprehensive event overview",
    "key_facts": ["fact 1", "fact 2", "fact 3", "fact 4"],
    "perspectives": ["perspective 1", "perspective 2", "perspective 3"]
}}

Requirements:
- enhanced_abstract: 3-4 sentences providing comprehensive overview
- key_facts: 3-4 most important factual points from multiple sources
- perspectives: 2-3 different viewpoints from various sources
- Focus on accuracy and representing multiple perspectives fairly
- Ensure JSON is valid and properly formatted"""
    
    def _parse_topic_summary_response(self, response_content: str) -> Dict[str, Any]:
        """Parse AI response for topic summary into structured data."""
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
                
                return {
                    'topic_abstract': parsed.get('topic_abstract', ''),
                    'main_facts': parsed.get('main_facts', [])[:5],  # Limit to 5
                    'perspectives': parsed.get('perspectives', [])[:5]  # Limit to 5
                }
            else:
                self.logger.warning("No JSON found in topic summary response")
                return self._parse_fallback_response(response_content)
                
        except json.JSONDecodeError as e:
            self.logger.warning(f"Failed to parse topic summary JSON: {e}")
            return self._parse_fallback_response(response_content)
    
    def _parse_event_summary_response(self, response_content: str) -> Dict[str, Any]:
        """Parse AI response for event summary into structured data."""
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
                
                return {
                    'enhanced_abstract': parsed.get('enhanced_abstract', ''),
                    'key_facts': parsed.get('key_facts', [])[:5],  # Limit to 5
                    'perspectives': parsed.get('perspectives', [])[:4]  # Limit to 4
                }
            else:
                self.logger.warning("No JSON found in event summary response")
                return self._parse_fallback_response(response_content)
                
        except json.JSONDecodeError as e:
            self.logger.warning(f"Failed to parse event summary JSON: {e}")
            return self._parse_fallback_response(response_content)
    
    def _parse_fallback_response(self, response_content: str) -> Dict[str, Any]:
        """Parse response when JSON parsing fails."""
        # Simple fallback parsing
        lines = [line.strip() for line in response_content.split('\n') if line.strip()]
        
        abstract = lines[0] if lines else "Summary not available"
        facts = [line for line in lines[1:6] if line and not line.startswith('Perspective')]
        perspectives = [line for line in lines if 'perspective' in line.lower() or 'opinion' in line.lower()]
        
        return {
            'topic_abstract': abstract,
            'enhanced_abstract': abstract,
            'main_facts': facts[:5],
            'key_facts': facts[:5],
            'perspectives': perspectives[:4]
        }
    
    def _get_fallback_introduction(self, topic_summaries: List[Dict], total_events: int) -> str:
        """Generate fallback introduction when AI fails."""
        topics_text = ", ".join([topic['name'] for topic in topic_summaries])
        return (
            f"Good morning! Your daily brief covers {len(topic_summaries)} topics "
            f"including {topics_text}. We've identified {total_events} key events "
            f"from your followed topics to keep you informed."
        )
    
    def _get_fallback_topic_abstract(self, topic: Topic, event_abstracts: List[str]) -> str:
        """Generate fallback topic abstract when AI fails."""
        if event_abstracts:
            return f"Key developments in {topic.name} include {len(event_abstracts)} major events."
        return f"Recent developments in {topic.name} from your personalized news sources."
    
    def _get_fallback_event_summary(
        self, 
        event: Event, 
        facts: List[str] = None, 
        opinions: List[str] = None,
        error: str = None
    ) -> Dict[str, Any]:
        """Generate fallback event summary when AI fails."""
        return {
            'enhanced_abstract': event.abstract or f"Key developments in {event.title}.",
            'key_facts': (facts or [])[:3],
            'perspectives': (opinions or [])[:2],
            'cost': Decimal('0.0'),
            'tokens_input': 0,
            'tokens_output': 0,
            'error': error
        } 