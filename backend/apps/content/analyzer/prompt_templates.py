"""
Prompt Templates for Content Analysis.

Domain-specific prompt templates for the 5-stage analysis pipeline.
Following established pattern from content/summariser/prompt_templates.py

Stage 1: Linguistic Analysis (language, style, readability)
Stage 2: Entity Extraction and Linking
Stage 3: Event Detection and Clustering  
Stage 4: Topic Classification
Stage 5: Region Classification
"""
import json
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class AnalyzerPrompts:
    """
    Domain-specific prompt templates for article analysis.
    
    Follows established DailyBrief patterns for prompt management
    and maintains consistency with existing content processing services.
    """
    
    # Template version for tracking and A/B testing
    TEMPLATE_VERSION = "v1.0"
    
    @staticmethod
    def linguistic_analysis_prompt(title: str, content: str) -> str:
        """
        Stage 2: Style and tone analysis prompt (COST-OPTIMIZED).
        
        Only analyzes style_tone via LLM. Other metrics (language, readability, 
        word count, reading time) are calculated using free tools.
        """
        prompt = f"""SYSTEM: You are a writing style expert. Analyze ONLY the style and tone of this article.

ARTICLE:
Title: {title}
Content: {content}

Provide analysis in this exact JSON format:
{{
    "style_tone": "factual|opinion|narrative|analytical|satirical|sensational"
}}

Style and tone definitions:

| Style         | Definition / Scope                                                                 | Example Context                                      |
|---------------|-----------------------------------------------------------------------------------|-----------------------------------------------------|
| factual       | Objective reporting of events or facts with minimal interpretation.                | Breaking news, event summaries, data-driven reports. |
| opinion       | Editorial or commentary expressing subjective views or arguments.                 | Op-eds, columns, letters to the editor.             |
| narrative     | Storytelling or personal accounts focusing on human experiences, without sensationalism. | Feature stories, profiles, long-form journalism.    |
| analytical    | In-depth analysis or forecasting based on evidence and trends.                    | Market analysis, policy evaluations, predictions.   |
| satirical     | Humorous or ironic content aiming to critique or entertain.                       | Satire pieces, parody articles.                     |
| sensational   | Dramatic, emotionally charged, or celebrity-focused content with a gossipy or exaggerated tone. | Tabloid stories, celebrity gossip, scandal reports. |

INSTRUCTIONS:
- Classify the writing style and tone ONLY
- Use exact style_tone options: factual, opinion, narrative, analytical, satirical, sensational
- Focus on the overall approach and presentation style

"""

        return prompt
    
    @staticmethod
    def entity_extraction_prompt(title: str, content: str) -> str:
        """
        Stage 2: Entity extraction and classification prompt.
        
        Extracts named entities with types, confidence scores, and aliases.
        """
        prompt = f"""SYSTEM: You are an expert in named entity recognition. Extract and classify the 5-15 most important entities in the article.

ARTICLE:
Title: {title}
Content: {content}

Identify entities in this JSON format:
{{
    "entities": [
        {{
            "name": "Apple Inc.",
            "type": "ORGANIZATION",
            "confidence": 0.95,
            "mentions": 3,
            "context": "Technology company mentioned as iPhone maker",
            "aliases": ["Apple", "AAPL"]
        }},
        {{
            "name": "Tim Cook",
            "type": "PERSON",
            "confidence": 0.98,
            "mentions": 1,
            "context": "CEO of Apple Inc.",
            "aliases": ["Cook"]
        }}
    ]
}}

ENTITY TYPES AND TAXONOMY:

| Code              | Label                     | Definition / Scope                                                                                                         | Maps to spaCy / Wikidata         |
|-------------------|---------------------------|---------------------------------------------------------------------------------------------------------------------------|----------------------------------|
| `PERSON`          | Person                    | Individual human beings, or clearly-named multi-person stage names (e.g., *Daft Punk*).                                    | `PERSON`, `Q5`                   |
| `ORGANIZATION`    | Organization              | Companies, NGOs, government agencies, sports teams, universities.                                                          | `ORG`, `Q43229` / `Q79913`       |
| `LOCATION`        | Location                  | Geographical regions, countries, cities, physical landmarks when location is primary identity.                             | `GPE` + `LOC`, `Q2221906`        |
| `FACILITY`        | Facility / Infrastructure | Man-made physical structures: airports, bridges, factories, power plants.                                                  | `FAC`, `Q13226383`               |
| `EVENT`           | Event                     | Named historical or scheduled happenings (elections, conferences, wars, sports tournaments).                               | `EVENT`, `Q1190554`              |
| `WORK`            | Creative Work             | Books, movies, music albums, artworks, software titles.                                                                    | `WORK_OF_ART`, `Q838948`         |
| `PRODUCT`         | Product / Tech            | Consumer goods, devices, vehicles, weapon systems, pharmaceuticals, software products where commercial identity dominates. | subset of `PRODUCT`, `Q2424752`  |
| `FINANCIAL_ASSET` | Financial Asset           | Currencies, stocks, commodities, crypto tokens.                                                                            | (custom), `Q8142`, `Q388`        |
| `LAW`             | Law / Regulation          | Bills, acts, treaties, court cases, constitutions, official resolutions.                                                   | `LAW`, `Q820655`                 |
| `PROGRAM`         | Program / Policy          | Named government or corporate initiatives, missions, schemes (e.g., *Green New Deal*, *Apollo Program*).                   | `PROGRAM` (custom), `Q14204246`  |
| `OTHER`           | Other                     | Entities not fitting above but surfaced by NER; placeholder until taxonomy expansion.                                      | —                                |

INSTRUCTIONS:
- Extract 5-15 most important entities central to the story
- Provide confidence scores (0.0-1.0) based on context clarity
- Count total mentions throughout the article
- Include brief context explaining the entity's role, based on the article content
- List common aliases, abbreviations, or alternative names
- Focus on entities that readers need to understand the story
- Use exact entity type options provided"""

        return prompt
    
    @staticmethod
    def event_detection_prompt(title: str, content: str, published_at: str = None) -> str:
        """
        Stage 3: Event detection and key facts extraction.
        
        Identifies all significant events mentioned in the article for clustering and deduplication.
        Returns only the fields that will be stored in the Event model.
        """
        # Format published date if provided
        published_info = f"\nPublished: {published_at}" if published_at else ""
        
        prompt = f"""# REASONING TASK: Event Extraction & Analysis

You are an expert news analyst using advanced reasoning to extract and categorize events. Think step-by-step through this process.

## INPUT ARTICLE
**Title:** {title}{published_info}
**Content:** {content}

## REASONING PROCESS

### STEP 1: Article Comprehension
First, analyze what this article is fundamentally about:
- What is the ONE core event or story this article covers?
- What broader ongoing story does this belong to?
- What specific recent developments are being reported?

### STEP 2: Event Identification Strategy
Extract events at TWO levels:
1. **BROAD ONGOING EVENT** (if applicable): The major ongoing story/situation this belongs to
2. **SPECIFIC DEVELOPMENTS** (1-3): Recent specific events, announcements, or incidents

**Examples:**
- Russia-Ukraine War article → "Russia-Ukraine War" (broad) + "June 2025 Russia-Ukraine War Developments" (specific)
- Sports game article → "NBA 2025 Season" (broad) + "Lakers vs Warriors Game 7 Victory" (specific)
- Company earnings → "Tech Earnings Q2 2025" (broad) + "Apple Q2 2025 Earnings Report" (specific)

### STEP 3: Event Naming Protocol
**CRITICAL RULE:** Always name events as NOUNS (what happened), never as ACTIONS (who did what)

**❌ FORBIDDEN PATTERNS:**
- "[Person] launches [thing]" → ✅ "[Date] [Thing] Launch"
- "[Person] announces [thing]" → ✅ "[Date] [Thing] Announcement"  
- "[Person] dies at [age]" → ✅ "[Date] Death of [Person]"
- "[Company] reports [results]" → ✅ "[Date] [Company] [Results] Report"

**✅ CORRECT PATTERNS:**
- "Russia-Ukraine War" (broad ongoing)
- "June 2025 Russia-Ukraine War Developments" (specific)
- "NBA 2025 Season" (broad ongoing)
- "Lakers vs Warriors Game 7 Victory" (specific)

### STEP 4: Relevance Scoring Rubric
Use this precise scoring system:

**1.0 - Central/Primary Event**
- The main reason this article was written
- Core newsworthy development being reported
- Article would not exist without this event

**0.9 - Highly Relevant Context**
- Major ongoing story this article belongs to
- Essential background for understanding the main event
- Significant portion of article discusses this

**0.8 - Important Supporting Event**
- Substantial separate development mentioned
- Adds significant newsworthy information
- Could be its own news story

**0.7 - Relevant Background**
- Important context or related development
- Mentioned prominently but not central
- Helps explain the main story

**0.6 and below - Exclude**
- Minor mentions, general trends, or background information
- Not substantial enough for separate tracking

### STEP 5: Quality Filter for Events
Include events that meet ALL criteria:
1. **Relevance Score ≥ 0.7** (using rubric above)
2. **Distinctiveness**: Describes genuinely different occurrence
3. **Newsworthiness**: Significant enough to warrant tracking
4. **Specificity**: Concrete event, not vague trends

### STEP 6: Self-Correction Check
Before finalizing, verify:
1. Are ALL event titles nouns describing events (not actions)?
2. Do all events have relevance_score ≥ 0.7?
3. Are there any duplicates or near-duplicates?
4. Is exactly one event marked as primary (highest relevance)?
5. Do I have both broad and specific events where applicable?

## EVENT TYPE CLASSIFICATION

| Type | Definition | Examples |
|------|------------|----------|
| `conflict` | Wars, military actions, diplomatic tensions | Ukraine War, Gaza Conflict, Trade War |
| `sports` | Athletic competitions, games, tournaments | NBA Finals, World Cup, Olympics |
| `policy_change` | Government regulations, law changes | Fed Rate Decision, New Tax Law, Sanctions |
| `product_launch` | Product announcements, releases | iPhone Launch, Tesla Model, Software Release |
| `earnings` | Financial results, revenue reports | Q4 Earnings, Profit Report, Revenue Beat |
| `incident` | Accidents, crises, emergencies, breaches | Data Breach, Natural Disaster, System Outage |
| `meeting` | Conferences, summits, official gatherings | G7 Summit, Board Meeting, Peace Talks |
| `acquisition` | Mergers, takeovers, buyouts | Company Merger, Acquisition Deal, Buyout |
| `partnership` | Business collaborations, joint ventures | Strategic Partnership, Joint Venture, Alliance |
| `research` | Scientific discoveries, studies | Medical Study, Research Findings, Discovery |
| `legal` | Court decisions, lawsuits, proceedings | Supreme Court Ruling, Lawsuit, Legal Settlement |
| `election` | Elections, campaigns, voting events | Presidential Election, Primary Vote, Referendum |
| `natural_disaster` | Earthquakes, hurricanes, floods | Hurricane, Earthquake, Wildfire, Flood |
| `cultural` | Social movements, entertainment news | Social Movement, Celebrity News, Cultural Event |
| `other` | Events not fitting above categories | Miscellaneous events requiring classification |

## REASONING EXAMPLE

**Given article about:** "Russia-Ukraine war: List of key events, day 1,195"

**Step 1 - Comprehension:**
- Core story: Daily update on Russia-Ukraine war developments
- Broader context: Ongoing Russia-Ukraine War
- Specific developments: Day 1,195 specific events

**Step 2 - Event Levels:**
- BROAD: "Russia-Ukraine War" (ongoing conflict)
- SPECIFIC: "June 2025 Russia-Ukraine War Developments" (this day's events)

**Step 3 - Naming Check:**
- ✅ "Russia-Ukraine War" (event noun)
- ✅ "June 2025 Russia-Ukraine War Developments" (event noun)

**Step 4 - Relevance Scoring:**
- "Russia-Ukraine War": 0.9 (highly relevant context, ongoing story)
- "June 2025 Russia-Ukraine War Developments": 1.0 (primary, main reason for article)

**Step 5 - Quality Filter:**
- Both events ≥ 0.8 relevance ✓
- Distinct (broad vs specific) ✓
- Newsworthy ✓

## OUTPUT FORMAT

Respond with ONLY this exact JSON structure:

```json
{{
    "events": [
        {{
            "title": "Russia-Ukraine War",
            "abstract": "Ongoing military conflict between Russia and Ukraine that began in February 2022, involving territorial disputes, international sanctions, and humanitarian concerns.",
            "event_type": "conflict",
            "relevance_score": 0.9,
            "is_primary": false,
            "facts": [
                "Conflict began with Russian invasion in February 2022",
                "Ongoing military operations and territorial disputes",
                "International sanctions and humanitarian crisis",
                "Multiple countries providing aid to Ukraine"
            ]
        }},
        {{
            "title": "June 2025 Russia-Ukraine War Developments",
            "abstract": "Specific developments on Day 1,195 of the Russia-Ukraine war, including fighting updates, diplomatic talks, and casualty reports from June 3, 2025.",
            "event_type": "conflict",
            "relevance_score": 1.0,
            "is_primary": true,
            "facts": [
                "Day 1,195 of the war occurred on June 3, 2025",
                "At least five people killed in eastern Ukraine fighting",
                "Diplomatic talks in Istanbul regarding prisoner swaps",
                "Russia proposed new memorandum for ending the war"
            ]
        }}
    ]
}}
```

## CRITICAL CONSTRAINTS
- Extract both BROAD ongoing events (0.7-0.9 relevance) and SPECIFIC developments (0.9-1.0 relevance)
- All events MUST have relevance_score ≥ 0.7 (use scoring rubric)
- ALWAYS use event nouns, never action verbs in titles
- Use article publication date as temporal reference (don't hallucinate dates)
- MUST respond with valid JSON only - no reasoning text in output
- Exactly ONE event must have `is_primary: true` (highest relevance score)
- Include both generic ongoing stories AND specific developments where applicable

## FINAL INSTRUCTION
Think through each step carefully, then provide only the final JSON output. Look for both the broad ongoing story AND the specific developments being reported. Use the relevance scoring rubric precisely. Your reasoning process should ensure perfect adherence to the event naming protocol and eliminate all action-based titles."""

        return prompt
    
    @staticmethod
    def topic_classification_prompt(title: str, content: str, available_topics: List[Dict[str, str]]) -> str:
        """
        Stage 4: Topic classification prompt.
        
        Classifies article into available topic categories with confidence scores.
        """
        # Format available topics - only show description if it adds value beyond the name
        topic_options = "\n".join([
            f"- {t['slug']}: {t['name']}" + 
            (f" - {t['description']}" if t.get('description') and not t['description'].lower().startswith(t['name'].lower()) else "")
            for t in available_topics[:20]  # Limit to first 20 topics
        ])
        
        prompt = f"""SYSTEM: You are an expert content classifier. Categorize this article into the most relevant topics.

ARTICLE:
Title: {title}
Content: {content}

AVAILABLE TOPICS:
{topic_options}

Classify into topics using this JSON format:
{{
    "primary_topic": "technology",
    "primary_confidence": 0.85,
    "secondary_topics": ["business", "innovation"],
    "topic_relevance": {{
        "technology": 0.85,
        "business": 0.65,
        "innovation": 0.45
    }}
}}

INSTRUCTIONS:
- Select the ONE most relevant primary topic from available options
- Provide confidence score (0.0-1.0) for primary topic assignment
- List 0-3 secondary topics that are also relevant
- Provide relevance scores for all mentioned topics
- Only include topics that are genuinely relevant to the article content
- Use exact topic slugs from the available options
- Focus on the main subject matter, not tangential mentions"""

        return prompt
    
    @staticmethod
    def region_classification_prompt(title: str, content: str, available_regions: List[Dict[str, str]]) -> str:
        """
        Stage 5: Region classification prompt.
        
        Identifies geographic regions relevant to the article.
        """
        # Format available regions - only show description for compound/non-obvious regions
        region_options = "\n".join([
            f"- {r['code']}: {r['name']}" + 
            (f" - {r['description']}" if r.get('description') and (
                'and' in r['description'].lower() or  # For compound regions
                not r['description'].lower().startswith(r['name'].lower())  # For non-obvious descriptions
            ) else "")
            for r in available_regions[:30]  # Limit to first 30 regions
        ])
        
        prompt = f"""SYSTEM: You are an expert in geographic content analysis. Identify regions relevant to this news story.

ARTICLE:
Title: {title}
Content: {content}

AVAILABLE REGIONS:
{region_options}

Classify geographic relevance using this JSON format:
{{
    "primary_region": "US",
    "primary_confidence": 0.90,
    "secondary_regions": ["NA", "GLOBAL"],
    "region_relevance": {{
        "US": 0.90,
        "NA": 0.70,
        "GLOBAL": 0.40
    }}
}}

INSTRUCTIONS:
- Identify the ONE primary region where the main story takes place
- Provide confidence score (0.0-1.0) for primary region assignment
- List 0-3 secondary regions that are also relevant
- Consider: location of events, people involved, companies mentioned
- If story has global implications, use "GLOBAL" as appropriate
- Use exact region codes from the available options
- Focus on where the story's impact is most significant"""

        return prompt
    
    @staticmethod
    def get_prompt_metadata(stage: str) -> Dict[str, Any]:
        """
        Get prompt configuration metadata for AI provider service.
        
        Returns standardized configuration for each stage following
        the established aiproviders service patterns.
        """
        configs = {
            'linguistic_analysis': {
                'operation': 'linguistic_analysis',
                'temperature': 0.1,
                'max_tokens': 500,
                'model_preference': 'gpt-4o-mini',
                'template_version': f'{AnalyzerPrompts.TEMPLATE_VERSION}_linguistic',
                'description': 'Language detection, style analysis, and readability metrics'
            },
            'entity_extraction': {
                'operation': 'entity_extraction',
                'temperature': 0.2,
                'max_tokens': 1000,
                'model_preference': 'gpt-4o-mini',
                'template_version': f'{AnalyzerPrompts.TEMPLATE_VERSION}_entities',
                'description': 'Named entity recognition and classification'
            },
            'event_detection': {
                'operation': 'event_detection',
                'temperature': 0.1,
                'max_tokens': 600,
                'model_preference': 'gpt-4.1-mini',
                'template_version': f'{AnalyzerPrompts.TEMPLATE_VERSION}_events',
                'description': 'Main event identification and fact extraction'
            },
            'topic_classification': {
                'operation': 'topic_classification',
                'temperature': 0.1,
                'max_tokens': 400,
                'model_preference': 'gpt-4o-mini',
                'template_version': f'{AnalyzerPrompts.TEMPLATE_VERSION}_topics',
                'description': 'Article topic classification and categorization'
            },
            'region_classification': {
                'operation': 'region_classification',
                'temperature': 0.1,
                'max_tokens': 300,
                'model_preference': 'gpt-4o-mini',
                'template_version': f'{AnalyzerPrompts.TEMPLATE_VERSION}_regions',
                'description': 'Geographic region identification and classification'
            }
        }
        
        return configs.get(stage, {})
    
    @staticmethod
    def validate_linguistic_output(output_text: str) -> Dict[str, Any]:
        """
        Validate and parse style/tone analysis output (COST-OPTIMIZED).
        
        Returns:
            Dict with 'success', 'data', and optional 'error' keys
        """
        try:
            data = json.loads(output_text.strip())
            
            # Validate required fields (only style_tone now)
            if 'style_tone' not in data:
                return {'success': False, 'error': 'Missing required field: style_tone'}
            
            # Validate style_tone value
            valid_styles = ['factual', 'opinion', 'narrative', 'analytical', 'satirical', 'sensational']
            if data['style_tone'] not in valid_styles:
                return {'success': False, 'error': f'Invalid style_tone: {data["style_tone"]}. Must be one of: {valid_styles}'}
            
            return {'success': True, 'data': data}
            
        except json.JSONDecodeError as e:
            return {'success': False, 'error': f'Invalid JSON: {str(e)}'}
        except Exception as e:
            return {'success': False, 'error': f'Validation error: {str(e)}'}
    
    @staticmethod
    def validate_entity_output(output_text: str) -> Dict[str, Any]:
        """
        Validate and parse entity extraction output.
        
        Returns:
            Dict with 'success', 'data', and optional 'error' keys
        """
        try:
            data = json.loads(output_text.strip())
            
            if 'entities' not in data:
                return {'success': False, 'error': 'Missing entities field'}
            
            if not isinstance(data['entities'], list):
                return {'success': False, 'error': 'entities must be a list'}
            
            # Validate each entity
            valid_types = ['PERSON', 'ORGANIZATION', 'LOCATION', 'FACILITY', 'EVENT', 'WORK', 'PRODUCT', 'FINANCIAL_ASSET', 'LAW', 'PROGRAM', 'OTHER']
            for i, entity in enumerate(data['entities']):
                if not isinstance(entity, dict):
                    return {'success': False, 'error': f'Entity {i} must be an object'}
                
                required_fields = ['name', 'type', 'confidence']
                for field in required_fields:
                    if field not in entity:
                        return {'success': False, 'error': f'Entity {i} missing field: {field}'}
                
                if entity['type'] not in valid_types:
                    return {'success': False, 'error': f'Entity {i} has invalid type: {entity["type"]}'}
                
                if not (0.0 <= entity['confidence'] <= 1.0):
                    return {'success': False, 'error': f'Entity {i} confidence must be between 0.0 and 1.0'}
            
            return {'success': True, 'data': data}
            
        except json.JSONDecodeError as e:
            return {'success': False, 'error': f'Invalid JSON: {str(e)}'}
        except Exception as e:
            return {'success': False, 'error': f'Validation error: {str(e)}'}
    
    @staticmethod
    def validate_classification_output(output_text: str, valid_options: List[str]) -> Dict[str, Any]:
        """
        Validate topic or region classification output.
        
        Args:
            output_text: JSON output from AI
            valid_options: List of valid topic slugs or region codes
            
        Returns:
            Dict with classification data (directly returns the parsed and validated data)
        """
        try:
            # Clean and parse JSON
            clean_text = output_text.strip()
            if clean_text.startswith('```json'):
                clean_text = clean_text[7:]
            if clean_text.startswith('```'):
                clean_text = clean_text[3:]
            if clean_text.endswith('```'):
                clean_text = clean_text[:-3]
            clean_text = clean_text.strip()
            
            data = json.loads(clean_text)
            
            # Determine if this is topic or region classification based on the parsed data
            is_topic = 'primary_topic' in data
            is_region = 'primary_region' in data
            
            if not is_topic and not is_region:
                # Try to determine from valid_options format
                # Topic slugs are typically lower_case, region codes are typically UPPER or mixed
                sample_option = valid_options[0] if valid_options else ""
                if len(sample_option) <= 3 and sample_option.isupper():
                    is_region = True
                    primary_key = 'primary_region'
                else:
                    is_topic = True
                    primary_key = 'primary_topic'
                
                # Add missing field with None if not present
                if primary_key not in data:
                    data[primary_key] = None
            else:
                primary_key = 'primary_topic' if is_topic else 'primary_region'
            
            confidence_key = f"{primary_key}_confidence"
            
            # Get and validate primary value
            primary_value = data.get(primary_key)
            
            # Validate primary option is in valid list (only if not None)
            if primary_value is not None and primary_value not in valid_options:
                logger.warning(f"Invalid {primary_key}: {primary_value}, valid options: {valid_options}")
                # Set to None instead of failing, with very low confidence
                data[primary_key] = None
                data[confidence_key] = 0.1
            
            # Validate and set confidence
            confidence = data.get(confidence_key, 0.7)  # Default to 0.7 if missing
            if not isinstance(confidence, (int, float)) or not (0.0 <= confidence <= 1.0):
                confidence = 0.7  # Default fallback
            data[confidence_key] = confidence
            
            # Ensure secondary fields exist
            secondary_key = 'secondary_topics' if is_topic else 'secondary_regions'
            relevance_key = 'topic_relevance' if is_topic else 'region_relevance'
            
            if secondary_key not in data:
                data[secondary_key] = []
            if relevance_key not in data:
                data[relevance_key] = {}
            
            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in classification output: {str(e)}")
            logger.error(f"Raw output: {output_text[:500]}...")
            # Return empty result with default confidence
            return {
                'primary_topic': None,
                'primary_topic_confidence': 0.0,
                'secondary_topics': [],
                'topic_relevance': {},
                'primary_region': None, 
                'primary_region_confidence': 0.0,
                'secondary_regions': [],
                'region_relevance': {}
            }
        except Exception as e:
            logger.error(f"Classification validation error: {str(e)}")
            logger.error(f"Raw output: {output_text[:500]}...")
            # Return empty result with default confidence
            return {
                'primary_topic': None,
                'primary_topic_confidence': 0.0,
                'secondary_topics': [],
                'topic_relevance': {},
                'primary_region': None,
                'primary_region_confidence': 0.0,
                'secondary_regions': [],
                'region_relevance': {}
            }
    
    @staticmethod
    def validate_event_output(output_text: str) -> Dict[str, Any]:
        """
        Validate and parse event detection output.
        
        Returns:
            Dict with 'success', 'data', and optional 'error' keys
        """
        try:
            # Debug log the raw output to see what GPT-4o is returning
            logger.debug(f"Raw event output for validation: {output_text[:500]}...")
            
            # Try to extract JSON from the response (sometimes models wrap it in backticks)
            clean_text = output_text.strip()
            if clean_text.startswith('```json'):
                clean_text = clean_text[7:]  # Remove ```json
            if clean_text.startswith('```'):
                clean_text = clean_text[3:]  # Remove ```
            if clean_text.endswith('```'):
                clean_text = clean_text[:-3]  # Remove closing ```
            clean_text = clean_text.strip()
            
            data = json.loads(clean_text)
            
            if 'events' not in data:
                return {'success': False, 'error': 'Missing events field'}
            
            if not isinstance(data['events'], list):
                return {'success': False, 'error': 'events must be a list'}
            
            # Validate each event
            for i, event in enumerate(data['events']):
                if not isinstance(event, dict):
                    return {'success': False, 'error': f'Event {i} must be an object'}
                
                required_fields = ['title', 'abstract', 'event_type', 'facts', 'relevance_score', 'is_primary']
                for field in required_fields:
                    if field not in event:
                        return {'success': False, 'error': f'Event {i} missing field: {field}'}
                
                # Validate title length
                if len(event['title']) > 80:
                    return {'success': False, 'error': f'Event {i} title too long (max 80 chars)'}
                
                # Prevent using article title as event title (indicates lazy extraction)
                event_title_lower = event['title'].lower().strip()
                if event_title_lower in output_text.lower() and len(event_title_lower) > 30:
                    # Check if this looks like an article title (contains source, publication info, etc.)
                    article_title_indicators = ['- the', '| the', 'washington post', 'new york times', 'cnn', 'bbc', 'reuters']
                    if any(indicator in event_title_lower for indicator in article_title_indicators):
                        return {'success': False, 'error': f'Event {i} appears to use article title instead of event name: "{event["title"]}"'}
                
                # Validate abstract length
                if len(event['abstract']) > 500:  # More generous limit than 150 words
                    return {'success': False, 'error': f'Event {i} abstract too long (max 500 chars)'}
                
                # Validate event_type
                valid_event_types = [
                    'product_launch', 'earnings', 'policy_change', 'policy_debate', 'economic_crisis', 'incident', 'meeting',
                    'acquisition', 'partnership', 'research', 'legal', 'election',
                    'conflict', 'natural_disaster', 'cultural', 'sports', 'other'
                ]
                if event['event_type'] not in valid_event_types:
                    return {'success': False, 'error': f'Event {i} has invalid event_type: {event["event_type"]}. Must be one of: {valid_event_types}'}
                
                # Validate facts
                if not isinstance(event['facts'], list):
                    return {'success': False, 'error': f'Event {i} facts must be a list'}
                
                if len(event['facts']) < 2:
                    return {'success': False, 'error': f'Event {i} must have at least 2 facts'}
                
                if len(event['facts']) > 8:
                    return {'success': False, 'error': f'Event {i} too many facts (max 8)'}
                
                # Validate each fact
                for j, fact in enumerate(event['facts']):
                    if not isinstance(fact, str) or len(fact.strip()) < 10:
                        return {'success': False, 'error': f'Event {i} fact {j} must be a meaningful string (min 10 chars)'}
                
                # Validate relevance_score
                if not isinstance(event['relevance_score'], (int, float)):
                    return {'success': False, 'error': f'Event {i} relevance_score must be a number'}
                if not (0.0 <= event['relevance_score'] <= 1.0):
                    return {'success': False, 'error': f'Event {i} relevance_score must be between 0.0 and 1.0'}
                
                # Validate is_primary
                if not isinstance(event['is_primary'], bool):
                    return {'success': False, 'error': f'Event {i} is_primary must be a boolean'}
                
            
            # Validate exactly one primary event
            primary_events = [event for event in data['events'] if event.get('is_primary', False)]
            if len(primary_events) != 1:
                return {'success': False, 'error': f'Must have exactly 1 primary event, found {len(primary_events)}'}
            
            # Check for duplicate or very similar events
            event_titles = [event['title'].lower().strip() for event in data['events']]
            if len(event_titles) != len(set(event_titles)):
                return {'success': False, 'error': 'Duplicate event titles detected'}
            
            # Check for very similar events (titles, abstracts, and semantic content)
            import difflib
            import re
            
            def extract_key_entities(text):
                """Extract potential key entities/names from text"""
                # Simple extraction of capitalized words and phrases
                words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
                return set(word.lower() for word in words if len(word) > 2)
            
            for i, event1 in enumerate(data['events']):
                for j, event2 in enumerate(data['events'][i+1:], i+1):
                    # Check title similarity
                    title_similarity = difflib.SequenceMatcher(None, event1['title'].lower(), event2['title'].lower()).ratio()
                    
                    # Check abstract similarity
                    abstract_similarity = difflib.SequenceMatcher(None, event1['abstract'].lower(), event2['abstract'].lower()).ratio()
                    
                    # Extract key entities from both events
                    entities1 = extract_key_entities(event1['title'] + ' ' + event1['abstract'])
                    entities2 = extract_key_entities(event2['title'] + ' ' + event2['abstract'])
                    
                    # Calculate entity overlap
                    if entities1 and entities2:
                        entity_overlap = len(entities1.intersection(entities2)) / len(entities1.union(entities2))
                    else:
                        entity_overlap = 0
                    
                    # Flag as duplicate based on multiple criteria
                    is_duplicate = (
                        title_similarity > 0.85 or  # Very similar titles
                        (title_similarity > 0.6 and abstract_similarity > 0.7) or  # Moderately similar titles + abstracts
                        (entity_overlap > 0.7 and (title_similarity > 0.4 or abstract_similarity > 0.5))  # High entity overlap + some text similarity
                    )
                    
                    if is_duplicate:
                        return {'success': False, 'error': f'Events {i} and {j} appear to describe the same occurrence:\n  Event {i}: "{event1["title"]}" \n  Event {j}: "{event2["title"]}" \n  (Title sim: {title_similarity:.2f}, Abstract sim: {abstract_similarity:.2f}, Entity overlap: {entity_overlap:.2f})'}
            
            # Limit total number of events
            if len(data['events']) > 5:
                return {'success': False, 'error': 'Too many events (max 5 per article)'}
            
            return {'success': True, 'data': data}
            
        except json.JSONDecodeError as e:
            return {'success': False, 'error': f'Invalid JSON: {str(e)}'}
        except Exception as e:
            return {'success': False, 'error': f'Validation error: {str(e)}'} 