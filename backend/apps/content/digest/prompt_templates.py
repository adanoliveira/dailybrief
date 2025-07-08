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
        Generate friendly, personalized digest headline and introduction for daily readers.
        
        Creates a compelling headline and welcoming introduction with full context from topic abstracts,
        emphasizing the custom nature of the digest with neutral but friendly tone.
        """
        # Build comprehensive topic context with abstracts
        topics_context = []
        for topic in topic_summaries:
            # Include the topic abstract for meaningful context
            abstract = topic.get('topic_abstract', '').strip()
            story_count = topic.get('story_count', topic.get('event_count', 0))
            
            if abstract:
                topics_context.append(f"- {topic['name']}: {abstract} ({story_count} stories)")
            else:
                # Fallback if no abstract available
                events_text = f"{story_count} stor{'ies' if story_count != 1 else 'y'}"
                if topic.get('top_events'):
                    events_text += f" including {', '.join(topic['top_events'][:2])}"
                topics_context.append(f"- {topic['name']}: {events_text}")
        
        topics_preview = "\n".join(topics_context)
        
        return f"""Generate a compelling headline and friendly introduction for a custom daily news digest.

CONTEXT:
This digest is personally curated for this individual user based on their interests and preferences. Each user gets their own unique digest with different topics and stories selected specifically for them.

TODAY'S TOPICS & CONTENT:
{topics_preview}

TONE & STYLE:
- Neutral and journalistic, but warm and approachable
- Young, friendly, and conversational without being casual
- Simple language that's easy to scan quickly
- Direct and personal - speak to "you" as an individual reader
- Confident but not overwhelming

Generate exactly the following in JSON format:
{{
    "headline": "Your compelling headline here",
    "introduction": "Your introduction text here"
}}

REQUIREMENTS:
- **headline**: Compelling, engaging headline (45-60 characters max) that captures the day's major themes
- **introduction**: Concise introduction (2-3 sentences max) that acknowledges personalization and previews content
- Headline should be newsworthy and intriguing without being clickbait
- Introduction should start with a warm greeting appropriate for the time of day
- Both should make the reader want to dive into the stories
- Ensure JSON is valid and properly formatted

HEADLINE EXAMPLES (for style reference):
- "Trade Wars Heat Up as Tech Innovation Surges"
- "Breaking: Markets React to Policy Shifts" 
- "Science Breakthroughs Shape Tomorrow's World"
- "Global Events Reshape Business Landscape"

Write the JSON response:"""
    
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
        clustered_articles: List[Dict]
    ) -> str:
        """
        Generate story-driven topic summary for articles-based digests.
        
        Creates 3 top stories per topic based on:
        - Most cited events (multiple articles mentioning)
        - Broadest/widest impact stories 
        - Regional/topical significance
        
        Each story includes: headline, abstract, main points, perspectives, read more articles
        
        Args:
            topic_name: Name of the topic
            clustered_articles: List of articles with all their content clustered together
        """
        # Format clustered article data for context
        articles_context = []
        for i, article in enumerate(clustered_articles[:20], 1):  # Limit to 20 articles for prompt length
            # Build article summary with all content clustered together
            article_context = [
                f"{i}. [ID: {article['id']}] {article['source']} ({article['published']})",
                f"   Headline: {article['headline']}",
                f"   Summary: {article['longer_abstract']}"
            ]
            
            # Add facts if available
            if article.get('facts'):
                facts_text = "; ".join(article['facts'][:5])  # Limit to 5 facts per article
                article_context.append(f"   Facts: {facts_text}")
            
            # Add opinions if available
            if article.get('opinions'):
                opinions_text = "; ".join(article['opinions'][:3])  # Limit to 3 opinions per article
                article_context.append(f"   Opinions: {opinions_text}")
            
            # Add impacts if available
            if article.get('impacts'):
                impacts_text = "; ".join(article['impacts'][:3])  # Limit to 3 impacts per article
                article_context.append(f"   Impacts: {impacts_text}")
            
            articles_context.append("\n".join(article_context))
        
        return f"""You are a senior news editor creating today's top stories for the {topic_name} section of a custom daily digest.

ARTICLES AVAILABLE (with content clustered by source):
{chr(10).join(articles_context)}

TASK: Analyze all articles and create exactly 3 top stories that represent the most important developments in {topic_name} today.

STORY CLUSTERING & ANALYSIS:
1. **Identify Common Themes**: Look for articles mentioning the same events, people, companies, or geographical regions
2. **Group Related Coverage**: Cluster articles that cover the same story from different angles or perspectives
3. **Find Connected Stories**: Link articles on related topics (e.g., multiple Middle East developments, related tech company moves, connected health studies)
4. **Measure Story Significance**: Prioritize stories with the most article coverage and cross-source validation

STORY SELECTION CRITERIA:
1. **Cross-Article Coverage**: Prioritize stories mentioned across multiple sources (indicates significance)
2. **Impact Scale**: Stories with the highest economic, social, political, or environmental impact, affecting the most people, regions, or having systemic implications  
3. **News Hierarchy**: Federal/national > regional > local; policy changes > market moves > individual incidents

TONE & STYLE:
- Neutral and journalistic, but engaging and accessible
- Professional yet approachable for general readers
- Clear, direct language that's easy to scan quickly
- Confident reporting without sensationalism
- Focus on facts while acknowledging diverse perspectives

For each story, provide:
- **headline**: Compelling, specific headline (8-12 words) that captures the unified story theme
- **abstract**: Engaging 60-word summary explaining what happened and why it matters, synthesizing multiple article perspectives
- **main_points**: 3-5 key facts or developments (each 15-25 words) that combine facts mentioned in articles that compose the story
- **perspectives**: 0-3 key viewpoints for story understading and reflection, expressed by stakeholders, experts, officials and other people features in the articles, taken from the opinions bullets from the articles that compose the story (verbatim quotes preferred)
- **read_more**: 1-3 most relevant article IDs that best cover this story (choose articles that provide complementary angles or comprehensive coverage)

Also provide:
- **topic_abstract**: Concise 25-30 word introduction to the topic that sets context for the stories below (avoid restating story details)

RESPONSE FORMAT (JSON):
{{
    "topic_abstract": "A concise 25-30 word introduction to {topic_name} that provides relevant context for today's stories without summarizing them. Focus on the broader theme or significance.",
    "stories": [
        {{
            "headline": "Compelling 8-12 word headline capturing unified story theme",
            "abstract": "Engaging 60-word summary explaining what happened and why it matters",
            "main_points": [
                "Key fact 1 (15-25 words combining insights from related articles)",
                "Key fact 2 (15-25 words combining insights from related articles)",
                "Key fact 3 (15-25 words combining insights from related articles)"
            ],
            "perspectives": [
                "Verbatim quote or paraphrased opinion from stakeholder/expert in the articles",
                "Different viewpoint from another source in the articles"
            ],
            "read_more": [12345, 67890]
        }},
        {{
            "headline": "Second story headline",
            "abstract": "Second story 60-word abstract",
            "main_points": ["Fact 1", "Fact 2", "Fact 3"],
            "perspectives": ["Perspective 1", "Perspective 2"],
            "read_more": [11111, 22222]
        }},
        {{
            "headline": "Third story headline", 
            "abstract": "Third story 60-word abstract",
            "main_points": ["Fact 1", "Fact 2", "Fact 3"],
            "perspectives": ["Perspective 1"],
            "read_more": [33333, 44444]
        }}
    ]
}}

CRITICAL JSON REQUIREMENTS:
- Use double quotes for all strings
- No trailing commas after last array/object elements
- Escape any quotes within text with backslash (\")
- Ensure proper nesting and bracket matching
- Test JSON validity mentally before output

EDITORIAL GUIDELINES:
- **Article Clustering**: Group articles covering the same events, companies, or regions into unified stories rather than treating them separately
- **Story Synthesis**: Combine facts, opinions, and impacts from multiple related articles to create richer, more comprehensive stories
- **Avoid Redundancy**: Don't create separate stories for closely related developments—merge them into broader, more meaningful narratives
- **Maintain Focus**: While clustering related content, ensure each story has a clear, specific theme and doesn't become too broad or vague
- **Source Diversity**: When multiple articles cover the same story, select read_more articles that provide different angles, sources, or depth of coverage
- **Content Integration**: Use the clustered article data to understand which facts/opinions come from which sources and synthesize them appropriately
- **Regional/Thematic Connections**: Link articles on related geographical regions (e.g., Middle East developments) or thematic areas (e.g., AI regulation, health studies) when they strengthen the story narrative

EXAMPLE CLUSTERING:
- Multiple articles about different companies in the same sector → "Tech Sector Faces New Regulatory Challenges"
- Various Middle East developments → "Escalating Tensions Reshape Middle East Dynamics"  
- Related health studies → "New Research Reveals Hidden Factors in Public Health"

Generate stories that inform and engage readers about the most significant {topic_name} developments today."""
    
    @staticmethod
    def digest_conclusion_prompt(
        topic_summaries: List[Dict], 
        introduction: str = None,
        topic_abstracts: List[Dict] = None
    ) -> str:
        """
        Generate compelling digest conclusion for daily readers.
        
        Creates an engaging wrap-up that synthesizes the main themes from today's
        digest while maintaining the neutral but friendly journalistic tone.
        
        Args:
            topic_summaries: Topic summaries with key points
            introduction: The digest introduction for context
            topic_abstracts: Full topic abstracts for deeper understanding
        """
        # Build comprehensive topic context
        topics_context = []
        for topic in topic_summaries:
            key_point = topic.get('key_point', topic.get('name', 'developments'))
            # Extract meaningful themes from the key points
            theme_preview = key_point[:80] + "..." if len(key_point) > 80 else key_point
            topics_context.append(f"• **{topic['name']}**: {theme_preview}")
        
        # Include topic abstracts if available for deeper context
        abstracts_context = ""
        if topic_abstracts:
            abstracts_context = "\\n\\nTOPIC ABSTRACTS FOR DEEPER CONTEXT:\\n"
            for abstract_data in topic_abstracts:
                topic_name = abstract_data.get('topic_name', 'Unknown')
                abstract_text = abstract_data.get('abstract', '')[:150] + "..." if len(abstract_data.get('abstract', '')) > 150 else abstract_data.get('abstract', '')
                abstracts_context += f"• **{topic_name}**: {abstract_text}\\n"
        
        # Include introduction if available for tone and theme continuity
        intro_context = ""
        if introduction:
            intro_context = f"\\n\\nDIGEST INTRODUCTION (for tone and theme continuity):\\n{introduction[:200]}{'...' if len(introduction) > 200 else ''}\\n"
        
        return f"""You are writing the conclusion for a personalized daily news digest.

DIGEST CONTEXT:
Today's digest covered {len(topic_summaries)} key topics with their main themes:
{chr(10).join(topics_context)}{abstracts_context}{intro_context}

TASK: Write a brief, direct wrap-up of today's digest for daily readers.

TONE & STYLE:
- Conversational and natural
- Direct and concise - avoid explaining why stories matter
- Professional but not formal or authoritative
- Like closing a conversation with a colleague, not delivering a lecture

REQUIREMENTS:
1. **Brief summary**: Quickly recap the main topics covered (1-2 sentences)
2. **Simple close**: Natural, friendly sign-off
3. **Length**: Exactly 25-35 words total
4. **Avoid**: Explanations about significance, "why this matters", forward-looking statements about staying informed

EXAMPLE STYLES:
"From tech breakthroughs to market shifts, today brought notable developments across business and science. That's your digest for today—see you tomorrow."

"Today covered major moves in politics, technology, and global markets. Thanks for reading, and we'll be back tomorrow with the latest."

Write a natural, brief conclusion that simply wraps up the day without lecturing or explaining importance."""
    
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
        
        Validates the new story-driven format with topic_abstract and stories array.
        Uses lenient validation that only catches corner cases indicating errors.
        
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
                
                # Validate required fields for new story-driven format
                required_fields = ['topic_abstract', 'stories']
                for field in required_fields:
                    if field not in parsed:
                        return {'success': False, 'error': f'Missing required field: {field}'}
                
                # Lenient topic_abstract validation - only catch real errors
                abstract_words = len(parsed['topic_abstract'].split())
                if abstract_words < 10:  # Too short - likely an error
                    return {'success': False, 'error': f'Topic abstract too short (got {abstract_words} words, minimum 10)'}
                if abstract_words > 80:  # Way too long - over 120% of max requested
                    return {'success': False, 'error': f'Topic abstract too long (got {abstract_words} words, maximum 80)'}
                
                # Validate stories array (exactly 3 stories)
                stories = parsed['stories']
                if len(stories) != 3:
                    return {'success': False, 'error': f'Must have exactly 3 stories, got {len(stories)}'}
                
                # Validate each story structure
                for i, story in enumerate(stories):
                    required_story_fields = ['headline', 'abstract', 'main_points', 'perspectives', 'read_more']
                    for field in required_story_fields:
                        if field not in story:
                            return {'success': False, 'error': f'Story {i+1} missing field: {field}'}
                    
                    # Lenient story abstract validation - only catch real errors
                    story_abstract_words = len(story['abstract'].split())
                    if story_abstract_words < 15:  # Too short - likely an error
                        return {'success': False, 'error': f'Story {i+1} abstract too short (got {story_abstract_words} words, minimum 15)'}
                    if story_abstract_words > 120:  # Way too long - over 120% of max requested
                        return {'success': False, 'error': f'Story {i+1} abstract too long (got {story_abstract_words} words, maximum 120)'}
                    
                    # Validate main_points count only
                    main_points = story['main_points']
                    if not (1 <= len(main_points) <= 8):  # More lenient range
                        return {'success': False, 'error': f'Story {i+1} must have 1-8 main points, got {len(main_points)}'}
                    
                    # Only validate that main_points aren't empty or extremely long
                    for j, point in enumerate(main_points):
                        point_words = len(point.split())
                        if point_words < 3:  # Too short - likely an error
                            return {'success': False, 'error': f'Story {i+1} point {j+1} too short (got {point_words} words, minimum 3)'}
                        if point_words > 60:  # Way too long - over 120% of max requested
                            return {'success': False, 'error': f'Story {i+1} point {j+1} too long (got {point_words} words, maximum 60)'}
                    
                    # Validate perspectives count only - content length is flexible
                    perspectives = story['perspectives']
                    if len(perspectives) > 5:  # More lenient
                        return {'success': False, 'error': f'Story {i+1} has too many perspectives: {len(perspectives)}, max 5'}
                    
                    # Validate read_more articles
                    read_more = story['read_more']
                    if not (1 <= len(read_more) <= 3):
                        return {'success': False, 'error': f'Story {i+1} must have 1-3 read_more articles, got {len(read_more)}'}
                    
                    # Validate each read_more article has required fields
                    for k, article in enumerate(read_more):
                        if isinstance(article, (int, str)):
                            # Just article ID - this is valid
                            continue
                        elif isinstance(article, dict):
                            # Full article object - validate required fields exist
                            if 'article_id' not in article:
                                return {'success': False, 'error': f'Story {i+1} read_more article {k+1} missing article_id'}
                        else:
                            return {'success': False, 'error': f'Story {i+1} read_more article {k+1} has invalid format'}
                
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
        
        Uses lenient validation to accept reasonable variations in content length.
        
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
                
                # Lenient abstract length validation - only warn for extreme cases
                abstract_words = len(abstract.split()) if abstract else 0
                if abstract_words > 120:  # Only truncate if way too long (120+ words vs 60 target)
                    # Truncate to 100 words if extremely long
                    abstract_words_list = abstract.split()[:100]
                    abstract = ' '.join(abstract_words_list)
                    logger.warning(f"Truncated abstract from {len(parsed.get('abstract', '').split())} to 100 words")
                
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