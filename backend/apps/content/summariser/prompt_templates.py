"""
Prompt Templates for Content Summarization.

Domain-specific prompt templates for the 4-stage summarization pipeline.
Following established pattern from content/quality/prompt_templates.py

Stage 1: Rich Bullet Compression (RBC)
Stage 2: Skeleton Summary Generation
Stage 3: Critic Review (Conditional)
Stage 4: Summary Repair (If needed)
"""
import json
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class SummarizationPrompts:
    """
    Domain-specific prompt templates for article summarization.
    
    Follows established DailyBrief patterns for prompt management
    and maintains consistency with existing content processing services.
    """
    
    # Template version for tracking and A/B testing
    TEMPLATE_VERSION = "v1.0"
    
    @staticmethod
    def rbc_compression_prompt(article_text: str) -> str:
        """
        Stage 1: Rich Bullet Compression prompt.
        
        Converts article content into ≤25 labeled bullet points for lossless compression.
        """
        prompt = f"""SYSTEM: You are BulletCompressor-GPT. Summarize the article into EXACTLY 25 or fewer compact bullets.

        CRITICAL: Maximum 25 bullets total. Count carefully and stop at 25.

        LABEL each bullet with one of: [FACT] [STAT] [QUOTE] [OPINION] [CONTEXT].

        RULES:
        • Keep numbers, names, dates verbatim from the original text
        • One clause per bullet - be concise but complete
        • Preserve key information without interpretation
        • Use the exact labels: [FACT], [STAT], [QUOTE], [OPINION], [CONTEXT]
        • Return valid JSON with "bullets" array
        • STOP at 25 bullets maximum - quality over quantity

        OUTPUT FORMAT:
        {{"bullets": ["[FACT] ...", "[STAT] ...", "[QUOTE] ..."]}}

        ARTICLE TEXT:
        {article_text}"""

        return prompt
    
    @staticmethod
    def skeleton_summary_prompt(rbc_json: str) -> str:
        """
        Stage 2: Skeleton summary generation prompt.
        
        Creates structured summary using ONLY the provided RBC bullets as source.
        """
        prompt = f"""SYSTEM: You are NewsDigest-GPT. Using ONLY the bullets below, create a structured summary.

        INSTRUCTIONS:
        1. Copy 3-6 most important [FACT] or [STAT] bullets verbatim into "facts"
        2. Write a headline (≤15 words) and abstract (≤60 words) in neutral tone
        3. Write a longer abstract (≤200 words) that comprehensively covers the key information
        4. Extract up to 5 "opinions" in format: "Speaker: statement"
        5. Create up to 3 "impact" bullets

        CONSTRAINTS:
        • Use ONLY information from the provided bullets
        • No external knowledge or interpretation
        • Facts must be copied verbatim from bullets
        • Abstract must be ≤60 words exactly
        • Longer abstract must be ≤200 words, more comprehensive but still concise
        • Longer abstract should include more facts, events and entities than the short abstract

        OUTPUT FORMAT:
        {{
        "headline": "...",
        "abstract": "...",
        "longer_abstract": "...",
        "facts": ["...", "..."],
        "opinions": ["Speaker: ...", "..."],
        "impact": ["...", "..."]
        }}

        SOURCE BULLETS:
        {rbc_json}"""

        return prompt
    
    @staticmethod
    def critic_review_prompt(rbc_json: str, summary_json: str) -> str:
        """
        Stage 3: Summary critique prompt.
        
        Detects hallucinations and verifies faithfulness to source bullets.
        """
        prompt = f"""SYSTEM: You are SummaryGuard. Audit the draft summary for hallucinations and errors.

        CHECK FOR:
        • Every number/date in abstract and longer_abstract appears verbatim in source bullets
        • Abstract is ≤60 words
        • Longer abstract is ≤200 words
        • Facts are copied exactly from source bullets
        • No information added beyond source bullets
        • Longer abstract should be more comprehensive than short abstract but still faithful to source
        • If source has >25 bullets, assess if summary captures the most important information

        GRACEFUL DEGRADATION:
        • If source bullets are excessive (>25), focus on core information quality
        • Prioritize factual accuracy over completeness
        • Flag if critical information is missing due to bullet overflow

        RETURN JSON:
        {{
        "faithful": true/false,
        "issues": ["specific issue descriptions"],
        "confidence": 0.0-1.0
        }}

        SOURCE BULLETS:
        {rbc_json}

        DRAFT SUMMARY:
        {summary_json}"""

        return prompt
    
    @staticmethod
    def repair_summary_prompt(summary_json: str, issues: List[str]) -> str:
        """
        Stage 4: Summary repair prompt.
        
        Fixes identified issues while preserving JSON structure.
        """
        issues_text = "\n".join(f"• {issue}" for issue in issues)
        
        prompt = f"""SYSTEM: Revise the draft summary to fix the issues below. Keep the same JSON structure and field names.

        ISSUES TO FIX:
        {issues_text}

        INSTRUCTIONS:
        • Fix only the identified issues
        • Maintain the exact JSON structure
        • Do not add new information beyond what's in the original draft
        • Ensure abstract remains ≤60 words
        • Ensure longer abstract remains ≤200 words
        • Longer abstract should be more comprehensive than the short abstract

        DRAFT TO REVISE:
        {summary_json}"""

        return prompt
    
    @staticmethod
    def get_prompt_metadata(stage: str) -> Dict[str, Any]:
        """
        Get prompt configuration metadata for AI provider service.
        
        Returns standardized configuration for each stage following
        the established aiproviders service patterns.
        """
        configs = {
            'rbc_compression': {
                'operation': 'rbc_compression',
                'temperature': 0.3,
                'max_tokens': 10000,  # Increased from 8192 to handle larger articles
                'model_preference': 'gpt-4o-mini',
                'template_version': f'{SummarizationPrompts.TEMPLATE_VERSION}_rbc',
                'description': 'Rich Bullet Compression for lossless content encoding'
            },
            'skeleton_summary': {
                'operation': 'skeleton_summary', 
                'temperature': 0.25,
                'max_tokens': 8192,  # Increased from 6144 for longer_abstract
                'model_preference': 'gpt-4o-mini',
                'template_version': f'{SummarizationPrompts.TEMPLATE_VERSION}_skeleton',
                'description': 'Structured summary generation from RBC bullets'
            },
            'summary_critique': {
                'operation': 'summary_critique',
                'temperature': 0.0,
                'max_tokens': 6144,  # Increased from 4096
                'model_preference': 'gpt-4o-mini',
                'template_version': f'{SummarizationPrompts.TEMPLATE_VERSION}_critic',
                'description': 'Summary faithfulness verification and critique'
            },
            'summary_repair': {
                'operation': 'summary_repair',
                'temperature': 0.2,
                'max_tokens': 10000,  # Significantly increased from 6144 to fix JSON parse errors
                'model_preference': 'gpt-4o-mini',
                'template_version': f'{SummarizationPrompts.TEMPLATE_VERSION}_repair',
                'description': 'Summary repair based on critic feedback'
            }
        }
        
        return configs.get(stage, {})
    
    @staticmethod
    def validate_rbc_output(output_text: str) -> Dict[str, Any]:
        """
        Validate RBC output format and content.
        
        Returns validation result with success flag and parsed data.
        """
        # Try direct JSON parsing first
        try:
            data = json.loads(output_text)
        except json.JSONDecodeError as e:
            # Attempt JSON repair if direct parsing fails
            success, repaired_json, data = JSONRepairUtils.attempt_json_repair(output_text)
            
            if not success:
                return {'valid': False, 'error': 'JSON parse error: Unable to repair malformed JSON', 'data': None}
        
        # Validate the parsed data
        if 'bullets' not in data:
            return {'valid': False, 'error': 'Missing bullets field', 'data': None}
        
        bullets = data['bullets']
        if not isinstance(bullets, list):
            return {'valid': False, 'error': 'Bullets must be a list', 'data': None}
        
        # Be lenient with bullet count - let critic review handle quality issues
        if len(bullets) > 40:  # Only fail on extreme cases
            return {'valid': False, 'error': f'Excessive bullets: {len(bullets)} > 40 (too many to process)', 'data': None}
        elif len(bullets) > 30:
            logger.warning(f"Bullet count {len(bullets)} exceeds target of 25 - critic review will assess quality")
        
        # Check bullet labeling
        valid_labels = ['[FACT]', '[STAT]', '[QUOTE]', '[OPINION]', '[CONTEXT]']
        unlabeled_bullets = []
        
        for bullet in bullets:
            if not any(bullet.startswith(label) for label in valid_labels):
                unlabeled_bullets.append(bullet)
        
        if unlabeled_bullets:
            return {
                'valid': False, 
                'error': f'Unlabeled bullets: {unlabeled_bullets[:3]}...', 
                'data': None
            }
        
        return {'valid': True, 'error': None, 'data': data}
    
    @staticmethod
    def validate_summary_output(output_text: str) -> Dict[str, Any]:
        """
        Validate summary output format and constraints.
        
        Returns validation result with success flag and parsed data.
        """
        # First attempt JSON repair if needed
        success, repaired_json, data = JSONRepairUtils.attempt_json_repair(output_text)
        
        if not success:
            return {'valid': False, 'error': 'JSON parse error: Unable to repair malformed JSON', 'data': None}
        
        # Validate the parsed data
        required_fields = ['headline', 'abstract', 'longer_abstract', 'facts', 'opinions', 'impact']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            return {'valid': False, 'error': f'Missing fields: {missing_fields}', 'data': None}
        
        # Validate field types
        if not isinstance(data['facts'], list):
            return {'valid': False, 'error': 'Facts must be a list', 'data': None}
        
        if not isinstance(data['opinions'], list):
            return {'valid': False, 'error': 'Opinions must be a list', 'data': None}
        
        if not isinstance(data['impact'], list):
            return {'valid': False, 'error': 'Impact must be a list', 'data': None}
        
        # Validate constraints
        headline_words = len(data['headline'].split()) if data['headline'] else 0
        abstract_words = len(data['abstract'].split()) if data['abstract'] else 0
        longer_abstract_words = len(data['longer_abstract'].split()) if data['longer_abstract'] else 0
        
        if headline_words > 15:
            return {'valid': False, 'error': f'Headline too long: {headline_words} > 15 words', 'data': None}
        
        # Be more lenient with abstract length - let critic review handle quality
        if abstract_words > 80:  # Only fail on extreme cases
            return {'valid': False, 'error': f'Abstract excessively long: {abstract_words} > 80 words', 'data': None}
        elif abstract_words > 60:
            logger.warning(f"Abstract length {abstract_words} exceeds target of 60 words - critic review will assess quality")
            
        # Validate longer abstract length
        if longer_abstract_words > 250:  # Only fail on extreme cases
            return {'valid': False, 'error': f'Longer abstract excessively long: {longer_abstract_words} > 250 words', 'data': None}
        elif longer_abstract_words > 200:
            logger.warning(f"Longer abstract length {longer_abstract_words} exceeds target of 200 words - critic review will assess quality")
        
        # Be more lenient with facts count - allow graceful degradation
        if len(data['facts']) < 1:
            return {'valid': False, 'error': f'No facts provided: {len(data["facts"])} < 1', 'data': None}
        elif len(data['facts']) < 3:
            logger.warning(f"Facts count {len(data['facts'])} below target of 3 - critic review will assess quality")
        
        if len(data['impact']) > 3:
            return {'valid': False, 'error': f'Too many impact bullets: {len(data["impact"])} > 3', 'data': None}
        
        return {'valid': True, 'error': None, 'data': data}
    
    @staticmethod
    def validate_critic_output(output_text: str) -> Dict[str, Any]:
        """
        Validate critic review output format.
        
        Returns validation result with success flag and parsed data.
        """
        # First attempt JSON repair if needed
        success, repaired_json, data = JSONRepairUtils.attempt_json_repair(output_text)
        
        if not success:
            return {'valid': False, 'error': 'JSON parse error: Unable to repair malformed JSON', 'data': None}
        
        # Validate the parsed data
        required_fields = ['faithful', 'issues']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            return {'valid': False, 'error': f'Missing fields: {missing_fields}', 'data': None}
        
        if not isinstance(data['faithful'], bool):
            return {'valid': False, 'error': 'Faithful must be boolean', 'data': None}
        
        if not isinstance(data['issues'], list):
            return {'valid': False, 'error': 'Issues must be a list', 'data': None}
        
        return {'valid': True, 'error': None, 'data': data}
    
    @staticmethod
    def should_trigger_critic(summary_data: Dict[str, Any], rbc_data: Dict[str, Any] = None) -> tuple[bool, List[str]]:
        """
        Determine if critic review should be triggered based on summary characteristics.
        
        Returns (should_trigger, reasons) tuple.
        """
        triggers = []
        
        # Check abstract length
        abstract_words = len(summary_data.get('abstract', '').split())
        if abstract_words > 60:
            triggers.append(f'Abstract too long: {abstract_words} words > 60')
            
        # Check longer abstract length
        longer_abstract_words = len(summary_data.get('longer_abstract', '').split())
        if longer_abstract_words > 200:
            triggers.append(f'Longer abstract too long: {longer_abstract_words} words > 200')
        
        # Check facts count
        facts_count = len(summary_data.get('facts', []))
        if facts_count < 3:
            triggers.append(f'Too few facts: {facts_count} < 3')
        
        # Check for uncertainty markers
        abstract = summary_data.get('abstract', '').lower()
        longer_abstract = summary_data.get('longer_abstract', '').lower()
        uncertainty_markers = ['uncertain', 'unclear', 'possibly', 'might be', 'appears to', 'seems to']
        
        for marker in uncertainty_markers:
            if marker in abstract:
                triggers.append(f'Uncertainty marker detected in abstract: "{marker}"')
                break
                
        for marker in uncertainty_markers:
            if marker in longer_abstract:
                triggers.append(f'Uncertainty marker detected in longer abstract: "{marker}"')
                break
        
        # Check for empty required fields
        if not summary_data.get('headline'):
            triggers.append('Empty headline')
        
        if not summary_data.get('abstract'):
            triggers.append('Empty abstract')
            
        if not summary_data.get('longer_abstract'):
            triggers.append('Empty longer abstract')
        
        # Check RBC bullet count if provided (graceful degradation)
        # Increased threshold from 25 to 30 to avoid unnecessary critic reviews
        if rbc_data:
            bullets = rbc_data.get('bullets', [])
            if len(bullets) > 30:
                triggers.append(f'Excessive RBC bullets: {len(bullets)} > 30 - may need consolidation')
        
        should_trigger = len(triggers) > 0
        return should_trigger, triggers


class EmbeddingPrompts:
    """
    Utilities for embedding generation text preparation.
    
    Not actual prompts since embeddings don't use LLM prompts,
    but text preparation functions for consistency.
    """
    
    @staticmethod
    def prepare_embedding_text(headline: str, abstract: str, longer_abstract: str = None) -> str:
        """
        Prepare text for embedding generation.
        
        Combines headline, abstract, and longer_abstract in optimal format for semantic search.
        Prioritizes longer_abstract if available for richer semantic context.
        """
        # Clean and prepare text
        clean_headline = headline.strip() if headline else ""
        clean_abstract = abstract.strip() if abstract else ""
        clean_longer_abstract = longer_abstract.strip() if longer_abstract else ""
        
        # Prefer longer abstract for richer semantic context if available
        if clean_headline and clean_longer_abstract:
            return f"{clean_headline} - {clean_longer_abstract}"
        elif clean_headline and clean_abstract:
            return f"{clean_headline} - {clean_abstract}"
        elif clean_headline:
            return clean_headline
        elif clean_longer_abstract:
            return clean_longer_abstract
        elif clean_abstract:
            return clean_abstract
        else:
            return ""
    
    @staticmethod
    def get_embedding_metadata() -> Dict[str, Any]:
        """
        Get embedding configuration metadata.
        
        Returns standardized configuration for embedding generation.
        """
        return {
            'model': 'text-embedding-3-small',  # Note: will upgrade to text-embedding-4-small when available
            'dimensions': 1536,
            'batch_size': 50,  # Process up to 50 embeddings per API call
            'operation': 'embedding_generation',
            'description': 'Semantic embedding generation for article similarity search'
        }


class JSONRepairUtils:
    """Utilities for repairing common JSON parsing issues."""
    
    @staticmethod
    def attempt_json_repair(json_text: str) -> tuple[bool, str, Dict[str, Any] | None]:
        """
        Attempt to repair common JSON issues.
        
        Returns (success, repaired_json, parsed_data)
        """
        original_text = json_text.strip()
        
        # Try original first
        try:
            data = json.loads(original_text)
            return True, original_text, data
        except json.JSONDecodeError:
            pass
        
        # Common repair strategies
        repair_strategies = [
            JSONRepairUtils._fix_truncated_json,
            JSONRepairUtils._fix_nested_quotes,
            JSONRepairUtils._fix_trailing_comma,
            JSONRepairUtils._fix_unclosed_brackets,
            JSONRepairUtils._extract_json_from_text,  # New strategy
            JSONRepairUtils._fix_missing_quotes,      # New strategy
            JSONRepairUtils._aggressive_json_extraction,  # New aggressive strategy
        ]
        
        for strategy in repair_strategies:
            try:
                repaired = strategy(original_text)
                if repaired != original_text:
                    data = json.loads(repaired)
                    logger.info(f"JSON repaired using {strategy.__name__}")
                    return True, repaired, data
            except (json.JSONDecodeError, Exception):
                continue
        
        return False, original_text, None
    
    @staticmethod
    def _fix_truncated_json(json_text: str) -> str:
        """Fix JSON that was truncated mid-string or mid-array."""
        text = json_text.strip()
        
        # If it ends with incomplete string, try to close it
        if text.endswith('"[FACT]') or text.endswith('"[STAT]') or text.endswith('"[QUOTE]') or text.endswith('"[OPINION]') or text.endswith('"[CONTEXT]'):
            # Remove the incomplete bullet
            last_complete_quote = text.rfind('", "')
            if last_complete_quote > 0:
                text = text[:last_complete_quote + 1] + ']}'
        elif text.count('"') % 2 == 1:  # Odd number of quotes - incomplete string
            # Check if it's truncated mid-sentence (no closing quote)
            if not text.endswith('"'):
                # Find the last complete bullet and truncate there
                last_complete_bullet = text.rfind('", "[')
                if last_complete_bullet > 0:
                    # Find the end of that bullet
                    next_quote = text.find('"', last_complete_bullet + 3)
                    if next_quote > 0:
                        text = text[:next_quote + 1] + ']}'
                    else:
                        # Fallback: just add closing quote and brackets
                        text += '"]}'
                else:
                    # Fallback: just add closing quote and brackets
                    text += '"]}'
            else:
                # Find the last complete bullet point
                last_complete = text.rfind('", "')
                if last_complete > 0:
                    text = text[:last_complete + 1] + ']}'
        
        # If missing closing brackets
        if not text.endswith(']}') and not text.endswith('}'):
            if text.endswith('"'):
                text += ']}'
            elif text.endswith(']'):
                text += '}'
        
        return text
    
    @staticmethod
    def _fix_nested_quotes(json_text: str) -> str:
        """Fix issues with nested quotes in JSON strings."""
        import re
        
        # Very simple approach: just escape all unescaped quotes within QUOTE bullets
        # Pattern: "[QUOTE] "content with "quotes" in it"
        # Replace with: "[QUOTE] \"content with \\\"quotes\\\" in it\""
        
        # Find QUOTE patterns and fix them
        pattern = r'"(\[QUOTE\] [^"]*)"([^"]*)"([^"]*)"'
        
        def fix_quotes(match):
            start = match.group(1)  # "[QUOTE] content before first quote
            middle = match.group(2)  # content between quotes
            end = match.group(3)  # content after last quote
            
            # Escape the inner quotes
            return f'"{start}\\"{middle}\\"{end}"'
        
        # Apply the fix multiple times to handle multiple quotes
        text = json_text
        for _ in range(5):  # max 5 iterations to avoid infinite loops
            new_text = re.sub(pattern, fix_quotes, text)
            if new_text == text:
                break  # no more changes
            text = new_text
        
        return text
    
    @staticmethod
    def _fix_trailing_comma(json_text: str) -> str:
        """Fix trailing commas in JSON."""
        import re
        # Remove trailing comma before closing bracket
        text = re.sub(r',(\s*[}\]])', r'\1', json_text)
        return text
    
    @staticmethod
    def _fix_unclosed_brackets(json_text: str) -> str:
        """Fix unclosed brackets and braces."""
        text = json_text.strip()
        
        # Count brackets and braces
        open_braces = text.count('{')
        close_braces = text.count('}')
        open_brackets = text.count('[')
        close_brackets = text.count(']')
        
        # Add missing closing characters
        missing_brackets = open_brackets - close_brackets
        missing_braces = open_braces - close_braces
        
        for _ in range(missing_brackets):
            text += ']'
        for _ in range(missing_braces):
            text += '}'
        
        return text

    @staticmethod
    def _extract_json_from_text(json_text: str) -> str:
        """Extract JSON object from text that might contain non-JSON content."""
        import re
        
        # Look for a complete JSON object pattern
        json_pattern = r'({[\s\S]*})'
        match = re.search(json_pattern, json_text)
        
        if match:
            potential_json = match.group(1)
            # Verify it's valid JSON before returning
            try:
                json.loads(potential_json)
                return potential_json
            except json.JSONDecodeError:
                pass
        
        return json_text

    @staticmethod
    def _fix_missing_quotes(json_text: str) -> str:
        """Fix missing quotes around field names and string values."""
        import re
        
        # Fix unquoted field names (e.g., {headline: "text"} -> {"headline": "text"})
        text = re.sub(r'([{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', json_text)
        
        return text
        
    @staticmethod
    def _aggressive_json_extraction(json_text: str) -> str:
        """
        Aggressively attempt to extract and reconstruct a valid JSON object.
        This is a last-resort strategy for heavily corrupted JSON.
        """
        import re
        
        # Try to find the required fields for our summary structure
        headline_match = re.search(r'"headline"\s*:\s*"([^"]*)"', json_text)
        abstract_match = re.search(r'"abstract"\s*:\s*"([^"]*)"', json_text)
        longer_abstract_match = re.search(r'"longer_abstract"\s*:\s*"([^"]*)"', json_text)
        
        # If we found the key fields, reconstruct a minimal valid JSON
        if headline_match and abstract_match:
            headline = headline_match.group(1)
            abstract = abstract_match.group(1)
            longer_abstract = longer_abstract_match.group(1) if longer_abstract_match else abstract
            
            # Extract facts, opinions, and impact if available
            facts = []
            opinions = []
            impact = []
            
            # Look for facts array
            facts_match = re.search(r'"facts"\s*:\s*\[(.*?)\]', json_text, re.DOTALL)
            if facts_match:
                # Extract individual facts
                fact_items = re.findall(r'"([^"]*)"', facts_match.group(1))
                facts = fact_items[:5]  # Limit to 5 facts
            
            # Look for opinions array
            opinions_match = re.search(r'"opinions"\s*:\s*\[(.*?)\]', json_text, re.DOTALL)
            if opinions_match:
                # Extract individual opinions
                opinion_items = re.findall(r'"([^"]*)"', opinions_match.group(1))
                opinions = opinion_items[:5]  # Limit to 5 opinions
            
            # Look for impact array
            impact_match = re.search(r'"impact"\s*:\s*\[(.*?)\]', json_text, re.DOTALL)
            if impact_match:
                # Extract individual impact items
                impact_items = re.findall(r'"([^"]*)"', impact_match.group(1))
                impact = impact_items[:3]  # Limit to 3 impact items
            
            # Construct a valid JSON object with the extracted fields
            reconstructed_json = {
                "headline": headline,
                "abstract": abstract,
                "longer_abstract": longer_abstract,
                "facts": facts if facts else ["No facts extracted"],
                "opinions": opinions if opinions else [],
                "impact": impact if impact else []
            }
            
            return json.dumps(reconstructed_json)
        
        return json_text 