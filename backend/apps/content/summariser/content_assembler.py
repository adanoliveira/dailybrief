"""
Content Assembler for DailyBrief Summarization.

Converts structured content blocks to markdown format while preserving semantic 
formatting and metadata. Implements intelligent truncation based on journalism 
principles and information density.
"""
import re
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ContentSection:
    """Represents a semantic section of content with priority."""
    content: str
    priority: int  # 1=highest (lead), 2=medium (body), 3=low (filler)
    section_type: str  # 'lead', 'body', 'quote', 'conclusion', 'metadata'
    original_length: int
    is_truncatable: bool = True


class MarkdownContentAssembler:
    """
    Assembles content blocks into well-formatted markdown for AI processing.
    
    Key features:
    - Preserves semantic formatting (headers, quotes, lists)
    - Includes metadata as text (image captions, link context)
    - Intelligent truncation based on information density
    - Respects journalistic content structure
    """
    
    def __init__(self, max_chars: int = 25000):
        """
        Initialize assembler with character limit.
        
        Args:
            max_chars: Maximum characters for assembled content
        """
        self.max_chars = max_chars
        
        # Information density priorities (1=highest, 3=lowest)
        self.block_priorities = {
            'subtitle': 1,      # Lead/subtitle - highest density
            'quote': 1,         # Direct quotes - very important
            'list': 1,          # Structured info - high density
            'heading': 1,       # Section headers - structural importance
            'paragraph': 2,     # Body content - medium density
            'image': 2,         # Visual context - medium priority
            'divider': 3,       # Low priority - mainly formatting
        }
    
    def assemble_content(self, content_blocks: List[Dict[str, Any]]) -> str:
        """
        Convert content blocks to markdown with intelligent truncation.
        
        Args:
            content_blocks: List of structured content blocks
            
        Returns:
            Markdown-formatted content optimized for summarization
        """
        if not content_blocks:
            return ""
        
        logger.info(f"Assembling {len(content_blocks)} content blocks into markdown")
        
        # Convert blocks to markdown sections
        sections = self._convert_blocks_to_sections(content_blocks)
        
        # Calculate if truncation is needed
        total_length = sum(section.original_length for section in sections)
        
        if total_length <= self.max_chars:
            # No truncation needed
            logger.info(f"No truncation needed: {total_length} chars <= {self.max_chars}")
            return self._assemble_sections(sections)
        
        # Apply intelligent truncation
        logger.info(f"Truncation needed: {total_length} chars > {self.max_chars}")
        truncated_sections = self._intelligent_truncation(sections)
        
        return self._assemble_sections(truncated_sections)
    
    def _convert_blocks_to_sections(self, blocks: List[Dict[str, Any]]) -> List[ContentSection]:
        """Convert content blocks to markdown sections with priorities."""
        sections = []
        
        for i, block in enumerate(blocks):
            block_type = block.get('type', 'paragraph')
            content = block.get('content', '')
            metadata = block.get('metadata', {})
            position = block.get('position', i + 1)
            
            # Convert to markdown
            markdown_content = self._block_to_markdown(block)
            
            if not markdown_content.strip():
                continue
            
            # Determine priority and section type
            priority = self.block_priorities.get(block_type, 2)
            section_type = self._determine_section_type(block, position, len(blocks))
            
            # Adjust priority based on position and content
            if position <= 3:  # Lead content
                priority = min(priority, 1)
            elif position >= len(blocks) - 3:  # Conclusion content
                priority = min(priority, 2)
            
            sections.append(ContentSection(
                content=markdown_content,
                priority=priority,
                section_type=section_type,
                original_length=len(markdown_content),
                is_truncatable=block_type not in ['quote', 'subtitle', 'heading']
            ))
        
        return sections
    
    def _block_to_markdown(self, block: Dict[str, Any]) -> str:
        """Convert a single content block to markdown format."""
        block_type = block.get('type', 'paragraph')
        content = block.get('content', '').strip()
        metadata = block.get('metadata', {})
        
        # Early return for empty content, except for list blocks which may have items in metadata
        if not content and block_type != 'list':
            return ""
        
        # Clean HTML from content
        clean_content = self._clean_html(content)
        
        if block_type == 'subtitle':
            return f"## {clean_content}\n\n"
        
        elif block_type == 'heading':
            level = metadata.get('level', 3)
            hashes = '#' * min(level + 2, 6)  # H3-H6 for article headings
            return f"{hashes} {clean_content}\n\n"
        
        elif block_type == 'quote':
            quote_type = metadata.get('type', 'quote')
            if quote_type == 'pullquote':
                return f"> **{clean_content}**\n\n"
            else:
                return f"> {clean_content}\n\n"
        
        elif block_type == 'list':
            # Handle both ordered and unordered lists
            items = metadata.get('items', [])
            
            if not items and content:
                # Parse HTML lists from content
                items = self._parse_html_list(content)
            
            if not items:
                # Final fallback: split content by common delimiters
                items = [item.strip() for item in re.split(r'[•\n\r\-\*]+', content) if item.strip()]
            
            if not items:
                # If still no items, treat as regular paragraph
                return f"{self._clean_html(content)}\n\n"
            
            # Determine if it's an ordered list
            is_ordered = self._is_ordered_list(content, metadata)
            
            list_md = ""
            for i, item in enumerate(items):
                clean_item = self._clean_html(item).strip()
                if clean_item:
                    if is_ordered:
                        list_md += f"{i + 1}. {clean_item}\n"
                    else:
                        list_md += f"- {clean_item}\n"
            
            return f"{list_md}\n" if list_md else ""
        
        elif block_type == 'image':
            # Include image context as metadata
            alt_text = metadata.get('alt', '')
            caption = metadata.get('caption', clean_content)
            src = metadata.get('src', '')
            
            image_context = f"*[Image: {caption}]*"
            if alt_text and alt_text != caption:
                image_context += f" *(Alt: {alt_text})*"
            
            return f"{image_context}\n\n"
        
        elif block_type == 'divider':
            return "---\n\n"
        
        else:  # paragraph and other text blocks
            # Add link context if available
            links = metadata.get('links', [])
            if links:
                link_context = " ".join([f"[{link.get('text', 'link')}]" for link in links[:2]])
                clean_content = f"{clean_content} {link_context}"
            
            return f"{clean_content}\n\n"
    
    def _clean_html(self, content: str) -> str:
        """Clean HTML tags while preserving important formatting cues."""
        if not content:
            return ""
        
        # Preserve important formatting with markdown equivalents
        content = re.sub(r'<strong[^>]*>(.*?)</strong>', r'**\1**', content, flags=re.IGNORECASE)
        content = re.sub(r'<b[^>]*>(.*?)</b>', r'**\1**', content, flags=re.IGNORECASE)
        content = re.sub(r'<em[^>]*>(.*?)</em>', r'*\1*', content, flags=re.IGNORECASE)
        content = re.sub(r'<i[^>]*>(.*?)</i>', r'*\1*', content, flags=re.IGNORECASE)
        
        # Extract link text (already handled in metadata, so just clean)
        content = re.sub(r'<a[^>]*>(.*?)</a>', r'\1', content, flags=re.IGNORECASE)
        
        # Handle line breaks and paragraphs
        content = re.sub(r'<br[^>]*>', ' ', content, flags=re.IGNORECASE)
        content = re.sub(r'</p>\s*<p[^>]*>', ' ', content, flags=re.IGNORECASE)
        
        # Remove remaining HTML tags
        content = re.sub(r'<[^>]+>', '', content)
        
        # Decode common HTML entities
        content = content.replace('&nbsp;', ' ')
        content = content.replace('&amp;', '&')
        content = content.replace('&lt;', '<')
        content = content.replace('&gt;', '>')
        content = content.replace('&quot;', '"')
        content = content.replace('&#39;', "'")
        content = content.replace('&rsquo;', "'")
        content = content.replace('&lsquo;', "'")
        content = content.replace('&rdquo;', '"')
        content = content.replace('&ldquo;', '"')
        
        # Clean up whitespace
        content = re.sub(r'\s+', ' ', content).strip()
        
        return content
    
    def _parse_html_list(self, content: str) -> List[str]:
        """
        Parse HTML ul/ol elements and extract list items.
        
        Args:
            content: HTML content containing list elements
            
        Returns:
            List of item texts
        """
        if not content:
            return []
        
        items = []
        
        # Match both <ul> and <ol> lists
        list_pattern = r'<(?:ul|ol)[^>]*>(.*?)</(?:ul|ol)>'
        list_matches = re.findall(list_pattern, content, re.DOTALL | re.IGNORECASE)
        
        for list_content in list_matches:
            # Extract <li> items from the list
            item_pattern = r'<li[^>]*>(.*?)</li>'
            item_matches = re.findall(item_pattern, list_content, re.DOTALL | re.IGNORECASE)
            
            for item_html in item_matches:
                # Clean the item text
                clean_item = self._clean_html(item_html).strip()
                if clean_item:
                    items.append(clean_item)
        
        return items
    
    def _is_ordered_list(self, content: str, metadata: Dict[str, Any]) -> bool:
        """
        Determine if a list should be rendered as ordered (numbered).
        
        Args:
            content: HTML content
            metadata: Block metadata
            
        Returns:
            True if list should be ordered
        """
        # Check metadata first
        list_type = metadata.get('list_type', '').lower()
        if list_type in ['ordered', 'ol', 'numbered']:
            return True
        elif list_type in ['unordered', 'ul', 'bulleted']:
            return False
        
        # Check HTML content for <ol> tags
        if re.search(r'<ol[^>]*>', content, re.IGNORECASE):
            return True
        
        # Default to unordered
        return False
    
    def _determine_section_type(self, block: Dict[str, Any], position: int, total_blocks: int) -> str:
        """Determine the semantic section type of a block."""
        block_type = block.get('type', 'paragraph')
        metadata = block.get('metadata', {})
        
        # Lead section (first few blocks)
        if position <= 3 or metadata.get('is_lead', False):
            return 'lead'
        
        # Conclusion section (last few blocks)
        elif position >= total_blocks - 2:
            return 'conclusion'
        
        # Special content types
        elif block_type in ['quote', 'list']:
            return 'highlight'
        
        elif block_type in ['image', 'divider']:
            return 'metadata'
        
        # Default body content
        else:
            return 'body'
    
    def _intelligent_truncation(self, sections: List[ContentSection]) -> List[ContentSection]:
        """
        Apply intelligent truncation based on journalism and information density principles.
        
        Strategy:
        1. Always keep lead and conclusion sections
        2. Keep all quotes and structured content (lists)
        3. For body paragraphs: keep beginning and end, truncate middle
        4. Remove low-priority metadata sections if needed
        """
        target_length = self.max_chars
        current_length = sum(s.original_length for s in sections)
        
        if current_length <= target_length:
            return sections
        
        # Sort by priority (1=highest priority)
        priority_sections = {1: [], 2: [], 3: []}
        for section in sections:
            priority_sections[section.priority].append(section)
        
        result_sections = []
        remaining_chars = target_length
        
        # Step 1: Include all priority 1 content (lead, quotes, structure)
        for section in priority_sections[1]:
            if section.original_length <= remaining_chars:
                result_sections.append(section)
                remaining_chars -= section.original_length
            elif section.section_type in ['lead', 'highlight']:
                # Force include critical content, truncate if needed
                truncated = self._truncate_section(section, remaining_chars)
                result_sections.append(truncated)
                remaining_chars = 0
                break
        
        # Step 2: Include priority 2 content (body paragraphs) with smart truncation
        if remaining_chars > 0:
            for section in priority_sections[2]:
                if section.original_length <= remaining_chars:
                    result_sections.append(section)
                    remaining_chars -= section.original_length
                elif section.is_truncatable and remaining_chars > 100:
                    # Apply paragraph-level smart truncation
                    truncated = self._truncate_paragraph(section, remaining_chars)
                    result_sections.append(truncated)
                    remaining_chars -= truncated.original_length
                    if remaining_chars <= 100:
                        break
        
        # Step 3: Include priority 3 content only if space allows
        if remaining_chars > 200:
            for section in priority_sections[3]:
                if section.original_length <= remaining_chars:
                    result_sections.append(section)
                    remaining_chars -= section.original_length
        
        # Sort back to original order for readability
        result_sections.sort(key=lambda s: sections.index(s) if s in sections else len(sections))
        
        final_length = sum(s.original_length for s in result_sections)
        logger.info(f"Truncation complete: {current_length} -> {final_length} chars")
        
        return result_sections
    
    def _truncate_paragraph(self, section: ContentSection, max_chars: int) -> ContentSection:
        """
        Truncate a paragraph by keeping beginning and end, removing middle.
        
        This preserves the most information-dense parts of paragraphs.
        """
        content = section.content.strip()
        
        if len(content) <= max_chars:
            return section
        
        # Split into sentences
        sentences = re.split(r'[.!?]+\s+', content)
        
        if len(sentences) <= 2:
            # Short paragraph, just truncate
            return self._truncate_section(section, max_chars)
        
        # Keep first and last sentences, truncate middle
        first_sentence = sentences[0] + '.'
        last_sentence = sentences[-1]
        
        available = max_chars - len(first_sentence) - len(last_sentence) - 10  # buffer for " [...] "
        
        if available > 0:
            # Try to include some middle content
            middle_content = " ".join(sentences[1:-1])
            if len(middle_content) <= available:
                truncated_content = f"{first_sentence} {middle_content} {last_sentence}"
            else:
                truncated_content = f"{first_sentence} [...] {last_sentence}"
        else:
            truncated_content = f"{first_sentence} [...] {last_sentence}"
        
        return ContentSection(
            content=truncated_content,
            priority=section.priority,
            section_type=section.section_type,
            original_length=len(truncated_content),
            is_truncatable=section.is_truncatable
        )
    
    def _truncate_section(self, section: ContentSection, max_chars: int) -> ContentSection:
        """Simple truncation for critical content."""
        if len(section.content) <= max_chars:
            return section
        
        truncated = section.content[:max_chars - 4] + "..."
        
        return ContentSection(
            content=truncated,
            priority=section.priority,
            section_type=section.section_type,
            original_length=len(truncated),
            is_truncatable=section.is_truncatable
        )
    
    def _assemble_sections(self, sections: List[ContentSection]) -> str:
        """Assemble sections into final markdown content."""
        return "".join(section.content for section in sections).strip()


def get_markdown_assembler(max_chars: int = 25000) -> MarkdownContentAssembler:
    """Get content assembler instance."""
    return MarkdownContentAssembler(max_chars=max_chars) 