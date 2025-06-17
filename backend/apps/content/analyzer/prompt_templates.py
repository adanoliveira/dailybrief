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
    def event_detection_prompt(title: str, content: str) -> str:
        """
        Stage 3: Event detection and key facts extraction.
        
        Identifies all significant events mentioned in the article for clustering and deduplication.
        Returns only the fields that will be stored in the Event model.
        """
        prompt = f"""SYSTEM: You are an expert news analyst. Extract all significant events mentioned in this article. Focus on events that are newsworthy, actionable, or historically significant.

ARTICLE:
Title: {title}
Content: {content}

Extract events in this exact JSON format:
{{
    "events": [
        {{
            "title": "Apple announces iPhone 15 with USB-C",
            "abstract": "Apple unveiled its iPhone 15 lineup featuring USB-C ports, replacing Lightning connectors after regulatory pressure from the EU.",
            "facts": [
                "Apple announced iPhone 15 lineup on September 12, 2023",
                "New phones feature USB-C instead of Lightning ports",
                "Change driven by EU regulatory requirements",
                "Available in four models with different storage options"
            ]
        }},
        {{
            "title": "EU mandates USB-C for mobile devices",
            "abstract": "European Union regulation requiring USB-C as standard charging port for mobile devices takes effect, forcing Apple to abandon Lightning.",
            "facts": [
                "EU USB-C mandate became effective in 2023",
                "Regulation applies to all mobile devices sold in Europe",
                "Companies had transition period to comply",
                "Aims to reduce electronic waste and improve consumer convenience"
            ]
        }}
    ]
}}

EVENT EXTRACTION GUIDELINES:

**What constitutes an event:**
- Product launches, announcements, releases
- Policy changes, regulations, legal decisions
- Corporate actions (mergers, acquisitions, partnerships)
- Economic developments (earnings, market changes)
- Political developments (elections, legislation, diplomatic actions)
- Incidents, accidents, crises
- Scientific discoveries, research findings
- Cultural or social developments
- Conflicts, protests, social movements

**Event title requirements:**
- Concise and descriptive (≤80 characters)
- Include key actors and action taken
- Use active voice when possible
- Focus on the core newsworthy element

**Abstract requirements:**
- Comprehensive summary in 1-2 sentences (≤150 words)
- Include who, what, when, where if available
- Provide sufficient context for clustering with related articles
- Focus on impact and significance

**Facts requirements:**
- Extract 3-8 specific, verifiable facts per event
- Include dates, numbers, names, locations when available
- Prioritize facts that help identify related coverage
- Avoid opinions or speculation
- Each fact should be a complete, standalone statement

**CRITICAL INSTRUCTIONS:**
- Extract ALL significant events mentioned, not just the primary one
- Events can be current, recent, or historical if prominently discussed
- Ensure each event is distinct and newsworthy
- If an article mentions multiple related developments, extract each as separate events
- Skip minor details or background information that aren't events themselves
- Maximum 5 events per article to maintain quality and relevance"""

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
                'model_preference': 'gpt-4o-mini',
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
            Dict with 'success', 'data', and optional 'error' keys
        """
        try:
            data = json.loads(output_text.strip())
            
            # Check primary classification
            primary_key = 'primary_topic' if 'primary_topic' in output_text else 'primary_region'
            confidence_key = f"{primary_key}_confidence"
            
            if primary_key not in data:
                return {'success': False, 'error': f'Missing {primary_key} field'}
            
            # Validate primary option is in valid list
            primary_value = data[primary_key]
            if primary_value not in valid_options:
                return {'success': False, 'error': f'Invalid {primary_key}: {primary_value}'}
            
            # Validate confidence (optional field with default)
            confidence = data.get(confidence_key, 0.0)  # Default to 0.0 if missing
            if not (0.0 <= confidence <= 1.0):
                return {'success': False, 'error': f'{confidence_key} must be between 0.0 and 1.0'}
            
            # Add default confidence if missing
            if confidence_key not in data:
                data[confidence_key] = 0.0
            
            return {'success': True, 'data': data}
            
        except json.JSONDecodeError as e:
            return {'success': False, 'error': f'Invalid JSON: {str(e)}'}
        except Exception as e:
            return {'success': False, 'error': f'Validation error: {str(e)}'}
    
    @staticmethod
    def validate_event_output(output_text: str) -> Dict[str, Any]:
        """
        Validate and parse event detection output.
        
        Returns:
            Dict with 'success', 'data', and optional 'error' keys
        """
        try:
            data = json.loads(output_text.strip())
            
            if 'events' not in data:
                return {'success': False, 'error': 'Missing events field'}
            
            if not isinstance(data['events'], list):
                return {'success': False, 'error': 'events must be a list'}
            
            # Validate each event
            for i, event in enumerate(data['events']):
                if not isinstance(event, dict):
                    return {'success': False, 'error': f'Event {i} must be an object'}
                
                required_fields = ['title', 'abstract', 'facts']
                for field in required_fields:
                    if field not in event:
                        return {'success': False, 'error': f'Event {i} missing field: {field}'}
                
                # Validate title length
                if len(event['title']) > 80:
                    return {'success': False, 'error': f'Event {i} title too long (max 80 chars)'}
                
                # Validate abstract length
                if len(event['abstract']) > 500:  # More generous limit than 150 words
                    return {'success': False, 'error': f'Event {i} abstract too long (max 500 chars)'}
                
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
            
            # Limit total number of events
            if len(data['events']) > 5:
                return {'success': False, 'error': 'Too many events (max 5 per article)'}
            
            return {'success': True, 'data': data}
            
        except json.JSONDecodeError as e:
            return {'success': False, 'error': f'Invalid JSON: {str(e)}'}
        except Exception as e:
            return {'success': False, 'error': f'Validation error: {str(e)}'} 