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
        
        # Handle the new data structure
        topics_data = digest_data.get('topics_data', [])
        
        for topic_data in topics_data:
            topic = topic_data['topic']
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
        
        # Create structured prompt
        prompt = self._build_introduction_prompt(topic_summaries, total_events)
        
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
            
            introduction = response.content.strip()
            
            self.logger.info(f"Generated digest introduction ({len(introduction)} chars)")
            
            return {
                'content': introduction,
                'cost': Decimal(str(cost)),
                'tokens_input': tokens_in,
                'tokens_output': tokens_out
            }
            
        except Exception as e:
            self.logger.error(f"Failed to generate digest introduction: {e}")
            return {
                'content': self._get_fallback_introduction(topic_summaries, total_events),
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
            return self._get_fallback_topic_summary_response(topic)
        
        # Deduplicate content for prompt
        unique_facts = list(dict.fromkeys(all_facts))[:20]  # Remove duplicates, limit to 20
        unique_opinions = list(dict.fromkeys(all_opinions))[:15]  # Remove duplicates, limit to 15
        unique_impacts = list(dict.fromkeys(all_impacts))[:12]  # Remove duplicates, limit to 12
        
        # Create AI prompt
        prompt = self._build_fallback_topic_summary_prompt(
            topic, article_summaries, unique_facts, unique_opinions, unique_impacts
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
            
            # Parse structured response
            parsed_content = self._parse_fallback_topic_summary_response(response.content)
            
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
            return self._get_fallback_topic_summary_response(topic, unique_facts, unique_opinions, unique_impacts, str(e))
    
    def _build_fallback_topic_summary_prompt(
        self, 
        topic: Topic, 
        article_summaries: List[Dict], 
        facts: List[str], 
        opinions: List[str],
        impacts: List[str]
    ) -> str:
        """Build prompt for AI-powered fallback topic summary generation."""
        
        # Format article summaries for context
        articles_context = []
        for i, summary in enumerate(article_summaries[:5], 1):  # Limit to 5 for prompt length
            articles_context.append(
                f"{i}. {summary['source']} ({summary['published']}): {summary['headline']}\n"
                f"   Summary: {summary['longer_abstract'][:200]}{'...' if len(summary['longer_abstract']) > 200 else ''}"
            )
        
        return f"""You are a news analyst creating a comprehensive topic summary from multiple article summaries.

TOPIC: {topic.name}

ARTICLE SUMMARIES:
{chr(10).join(articles_context)}

AVAILABLE FACTS (from all articles):
{chr(10).join(f"• {fact}" for fact in facts[:15]) if facts else "• No facts available"}

AVAILABLE OPINIONS (from all articles):
{chr(10).join(f"• {opinion}" for opinion in opinions[:10]) if opinions else "• No opinions available"}

AVAILABLE IMPACTS (from all articles):
{chr(10).join(f"• {impact}" for impact in impacts[:8]) if impacts else "• No impacts available"}

Create a comprehensive topic summary that synthesizes information from all articles. Generate exactly the following JSON format:

{{
    "title": "Engaging headline for {topic.name} topic (max 15 words)",
    "abstract": "Concise overview of key developments in {topic.name} (max 60 words)",
    "facts": ["synthesized fact 1", "synthesized fact 2", "synthesized fact 3", "synthesized fact 4", "synthesized fact 5"],
    "opinions": ["expert opinion 1", "expert opinion 2", "expert opinion 3", "expert opinion 4"],
    "impacts": ["impact statement 1", "impact statement 2", "impact statement 3"]
}}

REQUIREMENTS:
- title: Compelling headline summarizing main developments (≤15 words)
- abstract: Comprehensive but concise overview (≤60 words exactly)
- facts: 3-5 key factual points synthesized across articles (no opinions)
- opinions: 2-4 expert opinions or viewpoints from various sources  
- impacts: 2-3 impact statements describing consequences or implications
- Synthesize information from multiple sources, don't just copy
- Focus on the most significant and recent developments
- Maintain journalistic objectivity and accuracy
- Ensure JSON is valid and properly formatted"""

    def _parse_fallback_topic_summary_response(self, response_content: str) -> Dict[str, Any]:
        """Parse AI response for fallback topic summary into structured data."""
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
                
                # Validate and clean the response
                title = parsed.get('title', '').strip()
                abstract = parsed.get('abstract', '').strip()
                facts = parsed.get('facts', [])[:6]  # Limit to 6
                opinions = parsed.get('opinions', [])[:5]  # Limit to 5
                impacts = parsed.get('impacts', [])[:3]  # Limit to 3
                
                # Validate abstract length
                abstract_words = len(abstract.split()) if abstract else 0
                if abstract_words > 60:
                    # Truncate to 60 words if too long
                    abstract_words_list = abstract.split()[:60]
                    abstract = ' '.join(abstract_words_list)
                    self.logger.warning(f"Truncated abstract from {len(parsed.get('abstract', '').split())} to 60 words")
                
                return {
                    'title': title,
                    'abstract': abstract,
                    'facts': facts,
                    'opinions': opinions,
                    'impacts': impacts
                }
            else:
                self.logger.warning("No JSON found in fallback topic summary response")
                return self._parse_fallback_topic_summary_fallback(response_content)
                
        except json.JSONDecodeError as e:
            self.logger.warning(f"Failed to parse fallback topic summary JSON: {e}")
            return self._parse_fallback_topic_summary_fallback(response_content)

    def _parse_fallback_topic_summary_fallback(self, response_content: str) -> Dict[str, Any]:
        """Parse response when JSON parsing fails for fallback topic summary."""
        # Simple fallback parsing
        lines = [line.strip() for line in response_content.split('\n') if line.strip()]
        
        title = lines[0] if lines else "Recent Developments"
        abstract = lines[1] if len(lines) > 1 else "Multiple developments in this topic."
        
        # Try to extract facts and opinions from remaining lines
        facts = []
        opinions = []
        impacts = []
        
        for line in lines[2:]:
            if any(keyword in line.lower() for keyword in ['fact', 'report', 'according', 'data', 'study']):
                facts.append(line)
            elif any(keyword in line.lower() for keyword in ['opinion', 'believe', 'think', 'expert', 'analyst']):
                opinions.append(line)
            elif any(keyword in line.lower() for keyword in ['impact', 'effect', 'consequence', 'result']):
                impacts.append(line)
        
        return {
            'title': title[:100],  # Limit title length
            'abstract': ' '.join(abstract.split()[:60]),  # Limit to 60 words
            'facts': facts[:5],
            'opinions': opinions[:4],
            'impacts': impacts[:3]
        }

    def _get_fallback_topic_summary_response(
        self, 
        topic: Topic, 
        facts: List[str] = None, 
        opinions: List[str] = None,
        impacts: List[str] = None,
        error: str = None
    ) -> Dict[str, Any]:
        """Generate fallback topic summary response when AI fails."""
        return {
            'title': f"Recent Developments in {topic.name}",
            'abstract': f"Multiple recent developments in {topic.name} from various news sources.",
            'facts': (facts or [])[:5],
            'opinions': (opinions or [])[:4], 
            'impacts': (impacts or [])[:3],
            'cost': Decimal('0.0'),
            'tokens_input': 0,
            'tokens_output': 0,
            'model_used': 'fallback-mode',
            'error': error
        } 