"""
Digest Generation Prompt Templates.

This module provides prompt templates for AI-powered digest generation,
following the established template architecture from analyzer and processor services.
These templates power the digest routing system with both event-based and articles-based strategies.

Template Features:
- Clear system prompts with role definition
- Structured JSON output specifications
- Comprehensive validation and error handling
- Strategy-specific prompt optimization
- Robust fallback mechanisms
"""
import json
import re
import logging
from typing import Dict, List, Optional, Any
from decimal import Decimal

logger = logging.getLogger(__name__)


class DigestPrompts:
    """
    Domain-specific prompt templates for digest generation.
    
    Follows established DailyBrief patterns for prompt management
    and maintains consistency with analyzer/processor content processing services.
    """
    
    # Template version for tracking and A/B testing
    TEMPLATE_VERSION = "v1.0"
    
    @staticmethod
    def digest_introduction_prompt(topic_summaries: List[Dict], total_events: int) -> str:
        """
        Generate friendly, personalized digest introduction for daily readers.
        
        Creates a welcoming introduction focused on the individual user
        with a 1-to-1 personalized perspective.
        """
        topics_preview = []
        for topic in topic_summaries:
            events_text = f"{topic['event_count']} story{'ies' if topic['event_count'] != 1 else 'y'}"
            if topic['top_events']:
                events_text += f" including {', '.join(topic['top_events'][:2])}"
            topics_preview.append(f"- {topic['name']}: {events_text}")
        
        return f"""Write a friendly, personalized introduction for a daily news digest aimed directly at the individual reader.

Today's digest covers {len(topic_summaries)} topics with key developments:
{chr(10).join(topics_preview)}

Write a 2-3 sentence introduction that:
1. Personally welcomes the individual reader back to their daily brief (use "you" and "your")
2. Acts as a friendly, personalized preview of what they'll find in their digest today
3. Highlights the most significant developments that matter to them
4. Uses a conversational, one-on-one tone as if speaking directly to this specific reader

Keep it concise, warm, and personally focused on the individual reader who relies on this daily digest. Start with "Good morning" or similar personal greeting."""
    
    @staticmethod
    def topic_summary_prompt(
        topic_name: str,
        event_abstracts: List[str], 
        facts: List[str], 
        opinions: List[str]
    ) -> str:
        """
        Generate comprehensive topic summary for event-based digests.
        
        Synthesizes multiple event abstracts and extracted content into
        a cohesive topic overview with structured output.
        """
        return f"""Generate a comprehensive summary for the topic: {topic_name}

Event Information:
{chr(10).join(event_abstracts) if event_abstracts else "No event abstracts available"}

Available Facts:
{chr(10).join(f"• {fact}" for fact in facts[:15]) if facts else "No facts available"}

Available Opinions/Perspectives:
{chr(10).join(f"• {opinion}" for opinion in opinions[:10]) if opinions else "No opinions available"}

Generate exactly the following in JSON format:
{{
    "topic_abstract": "2-3 sentence overview of the main developments in {topic_name}",
    "main_facts": ["fact 1", "fact 2", "fact 3", "fact 4", "fact 5"],
    "perspectives": ["perspective 1", "perspective 2", "perspective 3", "perspective 4"]
}}

Requirements:
- topic_abstract: 2-3 sentences summarizing key developments
- main_facts: Up to 5 most important factual points (no opinions)
- perspectives: Up to 4 different viewpoints or opinions expressed
- Focus on synthesizing information across multiple sources
- Ensure JSON is valid and properly formatted"""
    
    @staticmethod
    def event_enhancement_prompt(
        event_title: str,
        event_abstract: str,
        article_summaries: List[Dict], 
        facts: List[str], 
        opinions: List[str]
    ) -> str:
        """
        Enhance event summary by synthesizing multiple article perspectives.
        
        Takes an existing event and enriches it with content from
        related articles to provide comprehensive coverage.
        """
        sources_text = chr(10).join(
            f"• {summary['source']}: {summary['headline']}" 
            for summary in article_summaries
        )
        
        abstracts_text = chr(10).join(
            f"• {summary['abstract']}" 
            for summary in article_summaries
        )
        
        return f"""Enhance this event summary by synthesizing multiple article perspectives:

Event: {event_title}
Original Abstract: {event_abstract or "No original abstract"}

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
    
    @staticmethod
    def event_enhancement_with_weighting_prompt(
        event_title: str,
        event_abstract: str,
        article_summaries: List[Dict], 
        facts: List[str], 
        opinions: List[str]
    ) -> str:
        """
        Enhanced event summary with article importance weighting.
        
        Provides more sophisticated event enhancement by considering
        the relative importance of articles (PRIMARY, SECONDARY, RELATED).
        """
        # Group articles by importance for better prompt structure
        primary_articles = [a for a in article_summaries if a['importance'] == 'PRIMARY']
        secondary_articles = [a for a in article_summaries if a['importance'] == 'SECONDARY']
        related_articles = [a for a in article_summaries if a['importance'] == 'RELATED']
        
        # Build structured article context
        article_context = []
        
        if primary_articles:
            article_context.append("PRIMARY COVERAGE (Core event articles):")
            for i, summary in enumerate(primary_articles, 1):
                article_context.append(
                    f"  {i}. {summary['source']}: {summary['headline']}\n"
                    f"     {summary['abstract'][:150]}{'...' if len(summary['abstract']) > 150 else ''}"
                )
        
        if secondary_articles:
            article_context.append("\nSECONDARY MENTIONS (Event mentioned in broader context):")
            for i, summary in enumerate(secondary_articles, 1):
                article_context.append(
                    f"  {i}. {summary['source']}: {summary['headline']}\n"
                    f"     {summary['abstract'][:120]}{'...' if len(summary['abstract']) > 120 else ''}"
                )
        
        if related_articles:
            article_context.append("\nRELATED STORIES (Providing additional context):")
            for i, summary in enumerate(related_articles, 1):
                article_context.append(
                    f"  {i}. {summary['source']}: {summary['headline']}\n"
                    f"     {summary['abstract'][:100]}{'...' if len(summary['abstract']) > 100 else ''}"
                )
        
        return f"""Enhance this event summary by synthesizing multiple article perspectives with importance weighting:

Event: {event_title}
Original Abstract: {event_abstract or "No original abstract"}

ARTICLE SOURCES (by importance):
{chr(10).join(article_context)}

AVAILABLE FACTS (from all sources):
{chr(10).join(f"• {fact}" for fact in facts[:12]) if facts else "• No facts available"}

AVAILABLE OPINIONS (from all sources):
{chr(10).join(f"• {opinion}" for opinion in opinions[:10]) if opinions else "• No opinions available"}

Generate exactly the following in JSON format:
{{
    "enhanced_abstract": "4-5 sentence comprehensive event overview",
    "key_facts": ["fact 1", "fact 2", "fact 3", "fact 4", "fact 5"],
    "perspectives": ["perspective 1", "perspective 2", "perspective 3", "perspective 4"]
}}

REQUIREMENTS:
- enhanced_abstract: 4-5 sentences providing comprehensive overview that synthesizes all perspectives
- key_facts: 4-5 most important factual points, prioritizing PRIMARY sources but incorporating all perspectives
- perspectives: 3-4 different viewpoints from various sources, showing the range of opinions
- Weight PRIMARY articles most heavily, then SECONDARY, then RELATED for context
- Focus on accuracy and representing multiple perspectives fairly
- Synthesize information rather than just listing facts from individual articles
- Ensure JSON is valid and properly formatted"""
    
    @staticmethod
    def comprehensive_topic_summary_prompt(
        topic_name: str,
        article_summaries: List[Dict], 
        facts: List[str], 
        opinions: List[str],
        impacts: List[str]
    ) -> str:
        """
        Generate story-driven topic summary for articles-based digests.
        
        Creates 3 top stories per topic based on:
        - Most cited events (multiple articles mentioning)
        - Broadest/widest impact stories 
        - Regional/topical significance
        
        Each story includes: headline, abstract, main points, perspectives, read more articles
        """
        # Format article summaries for context with IDs
        articles_context = []
        for i, summary in enumerate(article_summaries[:20], 1):  # Increased to 20 articles for richer context
            articles_context.append(
                f"{i}. [ID: {summary['id']}] {summary['source']} ({summary['published']}): {summary['headline']}\n"
                f"   Summary: {summary['longer_abstract']}"  # No truncation - feed full summary
            )
        
        # Format extracted content for reference (but don't use directly in stories)
        facts_context = "\n".join(f"- {fact}" for fact in facts[:50]) if facts else "No facts extracted"
        opinions_context = "\n".join(f"- {opinion}" for opinion in opinions[:40]) if opinions else "No opinions extracted"
        impacts_context = "\n".join(f"- {impact}" for impact in impacts[:30]) if impacts else "No impacts extracted"
        
        return f"""You are a senior news editor creating today's top stories for the {topic_name} section of a daily digest.

ARTICLES AVAILABLE:
{chr(10).join(articles_context)}

EXTRACTED CONTENT FOR REFERENCE:
Facts: {facts_context}
Opinions: {opinions_context}  
Impacts: {impacts_context}

TASK: Analyze all articles and create exactly 3 top stories that represent the most important developments in {topic_name} today.

STORY SELECTION CRITERIA:
1. **Most Cited Events**: Stories mentioned across multiple articles (cross-reference coverage)
2. **Broadest Impact**: Stories affecting the most people, regions, or having systemic implications
3. **Significance**: Federal/national issues > local issues, major corporations > small companies, policy changes > individual incidents

For each story, provide:
- **headline**: Compelling, specific headline (8-12 words)
- **abstract**: Engaging 60-word summary explaining what happened and why it matters
- **main_points**: 3-5 key facts or developments (each 15-25 words)
- **perspectives**: 0-3 key viewpoints from stakeholders, experts, or officials (verbatim quotes preferred)
- **read_more**: 1-3 most relevant article IDs that best cover this story

Also provide:
- **topic_abstract**: 120-word overview presenting all 3 stories in a cohesive narrative

RESPONSE FORMAT (JSON):
{{
    "topic_abstract": "120-word overview of all stories...",
    "stories": [
        {{
            "headline": "Compelling headline for story 1",
            "abstract": "60-word engaging summary explaining what happened and significance...",
            "main_points": [
                "Key fact or development 1 (15-25 words)",
                "Key fact or development 2 (15-25 words)", 
                "Key fact or development 3 (15-25 words)"
            ],
            "perspectives": [
                "Direct quote or viewpoint from stakeholder/expert (if available)",
                "Another relevant perspective (if available)"
            ],
            "read_more": [
                {{"article_id": "ID", "title": "Article Title", "source": "Source", "reason": "Why this article is essential for this story"}}
            ]
        }},
        {{
            "headline": "Compelling headline for story 2",
            "abstract": "60-word engaging summary...",
            "main_points": [...],
            "perspectives": [...],
            "read_more": [...]
        }},
        {{
            "headline": "Compelling headline for story 3", 
            "abstract": "60-word engaging summary...",
            "main_points": [...],
            "perspectives": [...],
            "read_more": [...]
        }}
    ]
}}

GUIDELINES:
- Prioritize stories with multiple article coverage over single-article events
- Focus on systemic impact over isolated incidents  
- Use engaging, specific headlines that capture the essence
- Make abstracts compelling and accessible to general readers
- Ensure main_points are factual developments, not opinions
- Include diverse perspectives when available
- Select read_more articles that provide the best coverage/analysis
- Make topic_abstract flow naturally, connecting the stories thematically

Generate stories that inform and engage readers about the most significant {topic_name} developments today."""
    
    @staticmethod
    def digest_conclusion_prompt(topic_summaries: List[Dict]) -> str:
        """
        Generate brief digest conclusion summarizing main topics.
        
        Creates a concise wrap-up that recaps the main topic summaries
        for daily digest readers.
        """
        topics_recap = []
        for topic in topic_summaries:
            key_point = topic.get('key_point', topic.get('name', 'developments'))
            topics_recap.append(f"- {topic['name']}: {key_point}")
        
        return f"""Write a brief, friendly conclusion for a daily news digest that wraps up the main topic summaries.

Today's digest covered {len(topic_summaries)} key topics:
{chr(10).join(topics_recap)}

Write a 2-3 sentence conclusion that:
1. Briefly recaps the main themes from today's topic summaries
2. Provides a sense of closure for daily readers
3. Uses a warm, professional tone
4. Encourages readers to return tomorrow

Keep it concise and focused on the key themes that emerged across topics. End with a forward-looking statement about staying informed."""
    
    @staticmethod
    def fallback_topic_summary_prompt(
        topic_name: str,
        article_summaries: List[Dict], 
        facts: List[str], 
        opinions: List[str],
        impacts: List[str]
    ) -> str:
        """
        Generate simple topic summary for fallback cases (legacy compatibility).
        
        Creates basic topic summaries when comprehensive format is not needed.
        """
        # Format article summaries for context
        articles_context = []
        for i, summary in enumerate(article_summaries[:5], 1):  # Limit to 5 for prompt length
            articles_context.append(
                f"{i}. {summary['source']} ({summary['published']}): {summary['headline']}\n"
                f"   Summary: {summary['longer_abstract'][:200]}{'...' if len(summary['longer_abstract']) > 200 else ''}"
            )
        
        return f"""You are a news analyst creating a comprehensive topic summary from multiple article summaries.

TOPIC: {topic_name}

ARTICLE SUMMARIES:
{chr(10).join(articles_context)}

AVAILABLE FACTS (from all articles):
{chr(10).join(f"• {fact}" for fact in facts) if facts else "• No facts available"}

AVAILABLE OPINIONS (from all articles):
{chr(10).join(f"• {opinion}" for opinion in opinions) if opinions else "• No opinions available"}

AVAILABLE IMPACTS (from all articles):
{chr(10).join(f"• {impact}" for impact in impacts) if impacts else "• No impacts available"}

Create a comprehensive topic summary that synthesizes information from all articles. Generate exactly the following JSON format:

{{
    "title": "Engaging headline for {topic_name} topic (max 15 words)",
    "abstract": "Concise overview of key developments in {topic_name} (max 60 words)",
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
    
    @staticmethod
    def get_prompt_metadata(operation: str) -> Dict[str, Any]:
        """
        Get prompt configuration metadata for AI provider service.
        
        Returns standardized configuration for each digest operation following
        the established aiproviders service patterns.
        """
        configs = {
            'digest_introduction': {
                'operation': 'digest_introduction',
                'temperature': 0.4,
                'max_tokens': 300,
                'model_preference': 'gpt-4o-mini',
                'template_version': f'{DigestPrompts.TEMPLATE_VERSION}_introduction',
                'description': 'Friendly digest introduction and welcome message'
            },
            'digest_topic_summary': {
                'operation': 'digest_topic_summary',
                'temperature': 0.3,
                'max_tokens': 800,
                'model_preference': 'gpt-4o-mini',
                'template_version': f'{DigestPrompts.TEMPLATE_VERSION}_topic_summary',
                'description': 'Event-based topic synthesis and summarization'
            },
            'digest_event_enhancement': {
                'operation': 'digest_event_enhancement',
                'temperature': 0.2,
                'max_tokens': 600,
                'model_preference': 'gpt-4o-mini',
                'template_version': f'{DigestPrompts.TEMPLATE_VERSION}_event_enhancement',
                'description': 'Multi-article event perspective synthesis'
            },
            'digest_comprehensive_topic': {
                'operation': 'digest_comprehensive_topic',
                'temperature': 0.2,
                'max_tokens': 1200,
                'model_preference': 'gpt-4.1-mini',
                'template_version': f'{DigestPrompts.TEMPLATE_VERSION}_comprehensive_topic',
                'description': 'Comprehensive articles-based topic summary with events, perspectives, and recommendations'
            },
            'digest_fallback_topic': {
                'operation': 'digest_fallback_topic',
                'temperature': 0.25,
                'max_tokens': 800,
                'model_preference': 'gpt-4o-mini',
                'template_version': f'{DigestPrompts.TEMPLATE_VERSION}_fallback_topic',
                'description': 'Simple articles-based topic summary generation'
            },
            'digest_conclusion': {
                'operation': 'digest_conclusion',
                'temperature': 0.3,
                'max_tokens': 400,
                'model_preference': 'gpt-4o-mini',
                'template_version': f'{DigestPrompts.TEMPLATE_VERSION}_conclusion',
                'description': 'Brief digest conclusion summarizing main topics'
            }
        }
        
        return configs.get(operation, {})
    
    @staticmethod
    def validate_comprehensive_topic_output(output_text: str) -> Dict[str, Any]:
        """
        Validate and parse comprehensive topic summary output.
        
        Args:
            output_text: JSON output from AI
            
        Returns:
            Dict with 'success', 'data', and optional 'error' keys
        """
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', output_text, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
                
                # Validate required fields
                required_fields = ['abstract', 'main_events', 'key_perspectives', 'read_more']
                for field in required_fields:
                    if field not in parsed:
                        return {'success': False, 'error': f'Missing required field: {field}'}
                
                # Validate abstract word count (60-120 words)
                abstract_words = len(parsed['abstract'].split())
                if not (60 <= abstract_words <= 120):
                    return {'success': False, 'error': f'Abstract must be 60-120 words, got {abstract_words}'}
                
                # Validate main_events (up to 5, each max 60 words)
                if len(parsed['main_events']) > 5:
                    return {'success': False, 'error': f'Too many main_events: {len(parsed["main_events"])}, max 5'}
                
                for i, event in enumerate(parsed['main_events']):
                    event_words = len(event.split())
                    if event_words > 60:
                        return {'success': False, 'error': f'Main event {i+1} too long: {event_words} words, max 60'}
                
                # Validate key_perspectives (up to 3)
                if len(parsed['key_perspectives']) > 3:
                    return {'success': False, 'error': f'Too many key_perspectives: {len(parsed["key_perspectives"])}, max 3'}
                
                # Validate read_more (exactly 3)
                if len(parsed['read_more']) != 3:
                    return {'success': False, 'error': f'Must have exactly 3 read_more articles, got {len(parsed["read_more"])}'}
                
                for i, article in enumerate(parsed['read_more']):
                    required_article_fields = ['article_id', 'title', 'source', 'reason']
                    for field in required_article_fields:
                        if field not in article:
                            return {'success': False, 'error': f'Read more article {i+1} missing field: {field}'}
                
                return {'success': True, 'data': parsed}
            else:
                return {'success': False, 'error': 'No JSON found in response'}
                
        except json.JSONDecodeError as e:
            return {'success': False, 'error': f'Invalid JSON: {str(e)}'}
        except Exception as e:
            return {'success': False, 'error': f'Validation error: {str(e)}'}
    
    @staticmethod
    def validate_topic_summary_output(output_text: str) -> Dict[str, Any]:
        """
        Validate and parse topic summary output.
        
        Args:
            output_text: JSON output from AI
            
        Returns:
            Dict with 'success', 'data', and optional 'error' keys
        """
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', output_text, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
                
                return {
                    'success': True,
                    'data': {
                        'topic_abstract': parsed.get('topic_abstract', ''),
                        'main_facts': parsed.get('main_facts', [])[:5],  # Limit to 5
                        'perspectives': parsed.get('perspectives', [])[:5]  # Limit to 5
                    }
                }
            else:
                logger.warning("No JSON found in topic summary response")
                return {'success': False, 'error': 'No JSON found in response'}
                
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse topic summary JSON: {e}")
            return {'success': False, 'error': f'Invalid JSON: {str(e)}'}
        except Exception as e:
            return {'success': False, 'error': f'Validation error: {str(e)}'}
    
    @staticmethod
    def validate_event_enhancement_output(output_text: str) -> Dict[str, Any]:
        """
        Validate and parse event enhancement output.
        
        Args:
            output_text: JSON output from AI
            
        Returns:
            Dict with 'success', 'data', and optional 'error' keys
        """
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', output_text, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
                
                return {
                    'success': True,
                    'data': {
                        'enhanced_abstract': parsed.get('enhanced_abstract', ''),
                        'key_facts': parsed.get('key_facts', [])[:5],  # Limit to 5
                        'perspectives': parsed.get('perspectives', [])[:4]  # Limit to 4
                    }
                }
            else:
                logger.warning("No JSON found in event enhancement response")
                return {'success': False, 'error': 'No JSON found in response'}
                
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse event enhancement JSON: {e}")
            return {'success': False, 'error': f'Invalid JSON: {str(e)}'}
        except Exception as e:
            return {'success': False, 'error': f'Validation error: {str(e)}'}
    
    @staticmethod
    def validate_fallback_topic_output(output_text: str) -> Dict[str, Any]:
        """
        Validate and parse fallback topic summary output.
        
        Args:
            output_text: JSON output from AI
            
        Returns:
            Dict with structured topic data or fallback content
        """
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', output_text, re.DOTALL)
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
                    logger.warning(f"Truncated abstract from {len(parsed.get('abstract', '').split())} to 60 words")
                
                return {
                    'success': True,
                    'data': {
                        'title': title,
                        'abstract': abstract,
                        'facts': facts,
                        'opinions': opinions,
                        'impacts': impacts
                    }
                }
            else:
                logger.warning("No JSON found in fallback topic summary response")
                return {'success': False, 'error': 'No JSON found in response'}
                
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse fallback topic summary JSON: {e}")
            return {'success': False, 'error': f'Invalid JSON: {str(e)}'}
        except Exception as e:
            return {'success': False, 'error': f'Validation error: {str(e)}'}
    
    @staticmethod
    def parse_response_with_fallback(response_content: str) -> Dict[str, Any]:
        """
        Parse response when JSON parsing fails - provides fallback parsing.
        
        Args:
            response_content: Raw AI response text
            
        Returns:
            Dict with extracted content using simple heuristics
        """
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
    
    @staticmethod
    def parse_fallback_topic_with_heuristics(response_content: str) -> Dict[str, Any]:
        """
        Parse fallback topic response when JSON parsing fails.
        
        Args:
            response_content: Raw AI response text
            
        Returns:
            Dict with extracted topic content using heuristics
        """
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


class DigestFallbacks:
    """
    Fallback content generators for when AI processing fails.
    
    Provides deterministic fallback content to ensure digest generation
    never completely fails due to AI unavailability or errors.
    """
    
    @staticmethod
    def get_fallback_introduction(topic_summaries: List[Dict], total_events: int) -> str:
        """Generate fallback introduction when AI fails."""
        topics_text = ", ".join([topic['name'] for topic in topic_summaries])
        return (
            f"Good morning! Your daily brief covers {len(topic_summaries)} topics "
            f"including {topics_text}. We've identified {total_events} key developments "
            f"from your followed topics to keep you informed."
        )
    
    @staticmethod
    def get_fallback_topic_abstract(topic_name: str, event_abstracts: List[str]) -> str:
        """Generate fallback topic abstract when AI fails."""
        if event_abstracts:
            return f"Key developments in {topic_name} include {len(event_abstracts)} major events."
        return f"Recent developments in {topic_name} from your personalized news sources."
    
    @staticmethod
    def get_fallback_event_summary(
        event_title: str,
        event_abstract: str,
        facts: List[str] = None, 
        opinions: List[str] = None,
        error: str = None
    ) -> Dict[str, Any]:
        """Generate fallback event summary when AI fails."""
        return {
            'enhanced_abstract': event_abstract or f"Key developments in {event_title}.",
            'key_facts': (facts or [])[:3],
            'perspectives': (opinions or [])[:2],
            'cost': Decimal('0.0'),
            'tokens_input': 0,
            'tokens_output': 0,
            'error': error
        }
    
    @staticmethod
    def get_fallback_topic_summary_response(
        topic_name: str,
        facts: List[str] = None, 
        opinions: List[str] = None,
        impacts: List[str] = None,
        error: str = None
    ) -> Dict[str, Any]:
        """Generate fallback topic summary response when AI fails."""
        return {
            'title': f"Recent Developments in {topic_name}",
            'abstract': f"Multiple recent developments in {topic_name} from various news sources.",
            'facts': (facts or [])[:5],
            'opinions': (opinions or [])[:4], 
            'impacts': (impacts or [])[:3],
            'cost': Decimal('0.0'),
            'tokens_input': 0,
            'tokens_output': 0,
            'model_used': 'fallback-mode',
            'error': error
        }
    
    @staticmethod
    def get_fallback_conclusion(topic_summaries: List[Dict]) -> str:
        """Generate fallback conclusion when AI fails."""
        topics_text = ", ".join([topic['name'] for topic in topic_summaries])
        return (
            f"That wraps up today's key developments across {len(topic_summaries)} topics: "
            f"{topics_text}. Stay informed and check back tomorrow for your next daily brief."
        )


# Template registry for easy access
DIGEST_OPERATIONS = {
    'digest_introduction': DigestPrompts.digest_introduction_prompt,
    'digest_topic_summary': DigestPrompts.topic_summary_prompt,
    'digest_event_enhancement': DigestPrompts.event_enhancement_prompt,
    'digest_event_enhancement_weighted': DigestPrompts.event_enhancement_with_weighting_prompt,
    'digest_comprehensive_topic': DigestPrompts.comprehensive_topic_summary_prompt,
    'digest_fallback_topic': DigestPrompts.fallback_topic_summary_prompt,
    'digest_conclusion': DigestPrompts.digest_conclusion_prompt,
}

# Validation functions registry
DIGEST_VALIDATORS = {
    'digest_topic_summary': DigestPrompts.validate_topic_summary_output,
    'digest_event_enhancement': DigestPrompts.validate_event_enhancement_output,
    'digest_comprehensive_topic': DigestPrompts.validate_comprehensive_topic_output,
    'digest_fallback_topic': DigestPrompts.validate_fallback_topic_output,
}


def get_digest_prompt(operation: str) -> callable:
    """
    Get prompt template function for specified operation.
    
    Args:
        operation: Digest operation name
        
    Returns:
        Prompt template function
        
    Raises:
        ValueError: If operation is not found
    """
    if operation not in DIGEST_OPERATIONS:
        available = ", ".join(DIGEST_OPERATIONS.keys())
        raise ValueError(f"Unknown digest operation '{operation}'. Available: {available}")
    
    return DIGEST_OPERATIONS[operation]


def get_digest_validator(operation: str) -> Optional[callable]:
    """
    Get validation function for specified operation.
    
    Args:
        operation: Digest operation name
        
    Returns:
        Validation function or None if not available
    """
    return DIGEST_VALIDATORS.get(operation)


def get_available_operations() -> List[str]:
    """
    Get list of available digest operations.
    
    Returns:
        List of operation names
    """
    return list(DIGEST_OPERATIONS.keys())


def get_operation_info(operation: str) -> Dict[str, Any]:
    """
    Get operation metadata and configuration.
    
    Args:
        operation: Digest operation name
        
    Returns:
        Dictionary with operation metadata
        
    Raises:
        ValueError: If operation is not found
    """
    if operation not in DIGEST_OPERATIONS:
        available = ", ".join(DIGEST_OPERATIONS.keys())
        raise ValueError(f"Unknown digest operation '{operation}'. Available: {available}")
    
    metadata = DigestPrompts.get_prompt_metadata(operation)
    metadata.update({
        'template_version': DigestPrompts.TEMPLATE_VERSION,
        'has_validator': operation in DIGEST_VALIDATORS,
        'prompt_function': DIGEST_OPERATIONS[operation].__name__
    })
    
    return metadata 