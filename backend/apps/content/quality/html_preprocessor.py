"""
HTML Preprocessor for Content Quality Evaluation

Implements "just enough" preprocessing following Microsoft's approach:
- Remove boilerplate that never helps evaluation (scripts, styles)
- Preserve semantic structure and content hierarchy
- Smart truncation keeping dense content + noise samples
- Preserve evidence for completeness, purity, structure, readability

Key principle: Optimize for LLM analysis while preserving quality assessment signals.
"""
import re
import logging
from html import unescape
from typing import Dict, List, Optional
from dataclasses import dataclass

# Conditional lxml import with graceful fallback
try:
    from lxml import html as lxml_html, etree
    LXML_AVAILABLE = True
except ImportError:
    LXML_AVAILABLE = False
    
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


@dataclass
class PreprocessedHTML:
    """
    Result of "just enough" HTML preprocessing for LLM evaluation.
    
    Balances token reduction with preservation of quality assessment signals.
    """
    cleaned_html: str                    # Optimized HTML for LLM
    original_size: int                   # Original HTML size in chars
    cleaned_size: int                    # Cleaned HTML size in chars
    compression_ratio: float             # Size reduction percentage
    processing_method: str               # Method used (lxml vs beautifulsoup)
    removed_elements: List[str]          # Types of boilerplate removed
    preserved_structure: List[str]       # Key structure elements kept
    content_density_info: Dict           # Content density analysis

class HTMLPreprocessor:
    """
    "Just enough" HTML preprocessor for LLM quality evaluation.
    
    Implements Microsoft's recommended approach:
    1. Remove boilerplate that never helps evaluation (scripts, styles)
    2. Collapse tags into layout-aware tokens with indentation  
    3. Smart truncation keeping dense content + noise samples
    4. Preserve evidence for completeness, purity, structure, readability
    """
    
    # Boilerplate elements that never help quality evaluation
    BOILERPLATE_ELEMENTS = [
        'script', 'style', 'noscript', 'svg', 'canvas', 'map'
    ]
    
    # Link types to remove
    BOILERPLATE_LINKS = [
        'stylesheet', 'preload', 'prefetch', 'dns-prefetch', 'preconnect'
    ]
    
    # Attributes to keep for specific tags (minimal allow-list)
    KEEP_ATTRIBUTES = {
        "img": ["src", "alt", "data-src", "title", "width", "height"],
        "iframe": ["src", "title", "data-src"],
        "video": ["src", "poster", "data-src"],
        "audio": ["src", "data-src"],
        "blockquote": ["cite"],
        "article": ["id", "class"],
        "main": ["id", "class", "role"],
        "section": ["id", "class"],
        "div": ["id", "class"],  # Limited to high-signal attributes
    }
    
    # Block tags that become \n\n
    BLOCK_TAGS = {
        'p', 'div', 'section', 'article', 'main', 'header', 'footer', 'nav',
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol', 'li', 'blockquote',
        'pre', 'figure', 'figcaption', 'aside', 'address'
    }
    
    # Inline tags that become single space
    INLINE_TAGS = {
        'span', 'em', 'strong', 'b', 'i', 'u', 'a', 'code', 'small', 
        'mark', 'del', 'ins', 'sub', 'sup', 'time'
    }
    
    # Tags to keep verbatim (with limited attributes)
    PRESERVE_VERBATIM = {'img', 'video', 'iframe', 'audio', 'blockquote'}
    
    # Sentinel patterns that should always be preserved for purity assessment
    NOISE_SENTINELS = re.compile(
        r'(related|comments?|advertisement|ads?|paywall|subscription|newsletter|social|share|menu|navigation|footer|header)',
        re.IGNORECASE
    )
    
    def __init__(self):
        """Initialize HTML preprocessor without caching."""
        pass
    
    def preprocess_for_evaluation(
        self,
        raw_html: str,
        max_tokens: int = 12000,
        preserve_html_structure: bool = True
    ) -> PreprocessedHTML:
        """
        Preprocess raw HTML using "just enough" approach.
        
        Args:
            raw_html: Original HTML content
            max_tokens: Maximum tokens in output
            preserve_html_structure: Whether to preserve HTML tags for quality evaluation
            
        Returns:
            PreprocessedHTML with optimized content and metadata
        """
        if not raw_html:
            return self._empty_result()
        
        original_size = len(raw_html)
        
        try:
            if LXML_AVAILABLE:
                result = self._preprocess_with_lxml(raw_html, max_tokens, preserve_html_structure)
                result.processing_method = "lxml"
            else:
                result = self._preprocess_with_beautifulsoup(raw_html, max_tokens, preserve_html_structure)
                result.processing_method = "beautifulsoup_fallback"
            
            result.original_size = original_size
            result.compression_ratio = ((original_size - result.cleaned_size) / original_size) * 100
            
            return result
            
        except Exception as e:
            logger.error(f"HTML preprocessing failed: {e}")
            return self._fallback_result(raw_html, max_tokens, original_size)
    
    def _preprocess_with_lxml(self, raw_html: str, max_tokens: int, preserve_html_structure: bool) -> PreprocessedHTML:
        """Preprocess using lxml (preferred method) with robust error handling."""
        try:
            # Step 1: Parse and normalize - try multiple parsing approaches
            doc = None
            parsing_errors = []
            
            # Try fromstring first (strict parsing)
            try:
                doc = lxml_html.fromstring(raw_html.encode('utf-8', 'replace'))
            except Exception as e:
                parsing_errors.append(f"fromstring: {e}")
                
            # Fallback to document_fromstring (more lenient)
            if doc is None:
                try:
                    doc = lxml_html.document_fromstring(raw_html.encode('utf-8', 'replace'))
                except Exception as e:
                    parsing_errors.append(f"document_fromstring: {e}")
            
            # If lxml parsing completely fails, fall back to BeautifulSoup
            if doc is None:
                logger.warning(f"lxml parsing failed: {parsing_errors}. Falling back to BeautifulSoup.")
                return self._preprocess_with_beautifulsoup(raw_html, max_tokens, preserve_html_structure)
            
            # Step 2: Remove boilerplate (safely)
            removed_elements = self._remove_boilerplate_lxml_safe(doc)
            
            # Step 3: Scrub attributes (safely)
            self._scrub_attributes_lxml_safe(doc)
            
            # Step 4: Convert to outline format with indentation (safely)
            if preserve_html_structure:
                # For quality evaluation: preserve key HTML structure
                outline_str = self._create_html_structure_lxml_safe(doc)
            else:
                # For content processing: create text outline
                outline_str = self._create_outline_lxml_safe(doc)
            
            # If outline creation failed, fall back to simple text extraction
            if not outline_str:
                logger.warning("lxml outline creation failed. Using simple text extraction.")
                outline_str = self._extract_simple_text_lxml(doc)
            
            # Step 5: Analyze content density
            density_info = self._analyze_content_density(outline_str)
            
            # Step 6: Smart truncation preserving noise
            final_html = self._smart_truncate(outline_str, max_tokens, density_info, preserve_html_structure)
            
            return PreprocessedHTML(
                cleaned_html=final_html,
                original_size=0,  # Will be set by caller
                cleaned_size=len(final_html),
                compression_ratio=0.0,  # Will be calculated by caller
                processing_method="lxml",
                removed_elements=removed_elements,
                preserved_structure=self._get_preserved_structure_lxml_safe(doc),
                content_density_info=density_info
            )
            
        except Exception as e:
            logger.error(f"lxml preprocessing completely failed: {e}. Falling back to BeautifulSoup.")
            return self._preprocess_with_beautifulsoup(raw_html, max_tokens, preserve_html_structure)
    
    def _remove_boilerplate_lxml_safe(self, doc) -> List[str]:
        """Safely remove boilerplate elements."""
        removed_elements = []
        
        try:
            # Remove scripts, styles, etc.
            for tag_name in self.BOILERPLATE_ELEMENTS:
                try:
                    elements = doc.xpath(f'//{tag_name}')
                    if elements:
                        removed_elements.append(f"{tag_name}({len(elements)})")
                        for element in elements:
                            try:
                                element.drop_tree()
                            except:
                                try:
                                    element.getparent().remove(element)
                                except:
                                    pass  # Skip if removal fails
                except Exception as e:
                    logger.debug(f"Failed to remove {tag_name}: {e}")
            
            # Remove stylesheet links
            try:
                for link in doc.xpath('//link[@rel]'):
                    try:
                        rel = link.get('rel', '').lower()
                        if any(bt in rel for bt in self.BOILERPLATE_LINKS):
                            removed_elements.append(f"link[{rel}]")
                            link.drop_tree()
                    except:
                        pass
            except Exception as e:
                logger.debug(f"Failed to remove links: {e}")
                
        except Exception as e:
            logger.warning(f"Boilerplate removal failed: {e}")
        
        return removed_elements
    
    def _scrub_attributes_lxml_safe(self, doc):
        """Safely scrub attributes."""
        try:
            for element in doc.iter():
                try:
                    if (element.tag is None or 
                        not hasattr(element, 'attrib') or
                        not element.attrib):
                        continue
                    
                    # Convert tag to string safely
                    tag_str = str(element.tag).lower()
                    
                    if tag_str not in self.KEEP_ATTRIBUTES:
                        # Clear all attributes if tag not in allowlist
                        element.attrib.clear()
                    else:
                        # Keep only allowed attributes
                        allowed = self.KEEP_ATTRIBUTES[tag_str]
                        attrs_to_remove = [
                            attr for attr in element.attrib 
                            if attr not in allowed
                        ]
                        
                        for attr in attrs_to_remove:
                            del element.attrib[attr]
                            
                except Exception as e:
                    logger.debug(f"Failed to scrub element attributes: {e}")
                    continue
                    
        except Exception as e:
            logger.warning(f"Attribute scrubbing failed: {e}")
    
    def _create_html_structure_lxml_safe(self, doc) -> str:
        """
        Create readable HTML structure preserving actual tags with indentation.
        
        This approach:
        - Keeps actual HTML tags (semantic information preserved)
        - Adds proper indentation for readability
        - Preserves attributes for key tags per allow-list
        - Makes HTML structure clear for LLM analysis
        """
        from html import unescape
        
        try:
            body = doc.find('.//body')
            root_element = body if body is not None else doc
            
            def format_html_element(element, depth=0):
                if element.tag is None:
                    return ""
                
                tag = str(element.tag).lower()
                indent = "  " * min(depth, 8)  # 2-space indentation, max 8 levels
                
                # Skip script/style tags (already removed but double-check)
                if tag in self.BOILERPLATE_ELEMENTS:
                    return ""
                
                # Get element attributes (cleaned according to allow-list)
                attrs_str = ""
                if hasattr(element, 'attrib') and element.attrib:
                    if tag in self.KEEP_ATTRIBUTES:
                        allowed_attrs = self.KEEP_ATTRIBUTES[tag]
                        attrs = []
                        for attr in allowed_attrs:
                            if attr in element.attrib:
                                value = str(element.attrib[attr])
                                # Truncate very long URLs but keep them readable
                                if len(value) > 100:
                                    value = value[:100] + "..."
                                attrs.append(f'{attr}="{value}"')
                        if attrs:
                            attrs_str = " " + " ".join(attrs)
                
                # Get text content
                text_content = ""
                if hasattr(element, 'text') and element.text:
                    text_content = unescape(str(element.text)).strip()
                
                # Process children
                children_html = []
                for child in element:
                    child_html = format_html_element(child, depth + 1)
                    if child_html.strip():
                        children_html.append(child_html)
                    
                    # Add tail text after child
                    if hasattr(child, 'tail') and child.tail:
                        tail_text = unescape(str(child.tail)).strip()
                        if tail_text:
                            # Add tail text with proper indentation
                            tail_lines = tail_text.split('\n')
                            for i, line in enumerate(tail_lines):
                                if line.strip():
                                    if i == 0:
                                        children_html.append(f"{indent}  {line.strip()}")
                                    else:
                                        children_html.append(f"{indent}  {line.strip()}")
                
                # Self-closing tags (img, video, iframe, etc.)
                if tag in {"img", "video", "iframe", "audio", "br", "hr", "input", "meta", "link"}:
                    return f"{indent}<{tag}{attrs_str}>\n"
                
                # Format the element
                children_content = "\n".join(children_html) if children_html else ""
                
                # Handle different formatting based on content
                if not text_content and not children_content:
                    # Empty element
                    return f"{indent}<{tag}{attrs_str}></{tag}>\n"
                elif text_content and not children_content:
                    # Element with only text content
                    if len(text_content) < 80:  # Short text - keep on same line
                        return f"{indent}<{tag}{attrs_str}>{text_content}</{tag}>\n"
                    else:  # Long text - multiline format
                        return f"{indent}<{tag}{attrs_str}>\n{indent}  {text_content}\n{indent}</{tag}>\n"
                elif not text_content and children_content:
                    # Element with only children
                    return f"{indent}<{tag}{attrs_str}>\n{children_content}{indent}</{tag}>\n"
                else:
                    # Element with both text and children
                    result = f"{indent}<{tag}{attrs_str}>\n"
                    if text_content:
                        result += f"{indent}  {text_content}\n"
                    if children_content:
                        result += children_content
                    result += f"{indent}</{tag}>\n"
                    return result
            
            # Generate the formatted HTML
            formatted_html = format_html_element(root_element)
            
            # Clean up excessive blank lines while preserving structure
            import re
            # Remove more than 2 consecutive blank lines
            formatted_html = re.sub(r'\n\s*\n\s*\n+', '\n\n', formatted_html)
            
            return formatted_html.strip()
            
        except Exception as e:
            logger.error(f"HTML formatting failed: {e}")
            return ""
    
    def _create_outline_lxml_safe(self, doc) -> str:
        """Safely create outline with comprehensive error handling."""
        try:
            body = doc.find('.//body')
            root_element = body if body is not None else doc
            
            def safe_outline_element(element, depth=0):
                try:
                    if element.tag is None:
                        return ""
                    
                    tag = str(element.tag).lower()
                    indent = "  " * min(depth, 10)  # Limit depth to prevent excessive indentation
                    
                    # Get text content safely
                    text_parts = []
                    if hasattr(element, 'text') and element.text:
                        try:
                            text_parts.append(str(element.text).strip())
                        except:
                            pass
                    
                    # Process children safely
                    child_content = []
                    try:
                        for child in element:
                            child_result = safe_outline_element(child, depth + 1)
                            if child_result:
                                child_content.append(child_result)
                            
                            # Add tail text safely
                            if hasattr(child, 'tail') and child.tail:
                                try:
                                    tail_text = str(child.tail).strip()
                                    if tail_text:
                                        text_parts.append(tail_text)
                                except:
                                    pass
                    except:
                        pass
                    
                    # Combine text
                    text = ' '.join(filter(None, text_parts)).strip()
                    
                    # Format output
                    result = ""
                    if text and len(text) > 3:  # Only include meaningful text
                        if tag in self.BLOCK_TAGS:
                            result = f"{indent}{text}\n\n"
                        elif tag in self.INLINE_TAGS:
                            result = f"{text} "
                        else:
                            result = f"{indent}{text}\n"
                    
                    # Add children
                    result += ''.join(child_content)
                    
                    return result
                    
                except Exception as e:
                    logger.debug(f"Failed to process element in outline: {e}")
                    return ""
            
            return safe_outline_element(root_element)
            
        except Exception as e:
            logger.error(f"Outline creation failed: {e}")
            return ""
    
    def _extract_simple_text_lxml(self, doc) -> str:
        """Simple text extraction as fallback."""
        try:
            # Get all text content
            text_content = []
            for element in doc.iter():
                try:
                    if element.text:
                        text_content.append(str(element.text).strip())
                    if hasattr(element, 'tail') and element.tail:
                        text_content.append(str(element.tail).strip())
                except:
                    continue
            
            # Join and clean up
            full_text = ' '.join(filter(None, text_content))
            
            # Split into paragraphs
            paragraphs = [p.strip() for p in full_text.split('\n') if p.strip()]
            
            return '\n\n'.join(paragraphs)
            
        except Exception as e:
            logger.error(f"Simple text extraction failed: {e}")
            return ""
    
    def _get_preserved_structure_lxml_safe(self, doc) -> List[str]:
        """Safely get preserved structure elements."""
        preserved = []
        try:
            for element in doc.iter():
                try:
                    if (element.tag and 
                        hasattr(element, 'attrib') and 
                        element.attrib):
                        tag_str = str(element.tag)
                        attrs = list(element.attrib.keys())
                        if attrs:
                            preserved.append(f"{tag_str}[{attrs[:3]}]")  # Limit attrs shown
                except:
                    continue
        except:
            pass
        
        return list(set(preserved))[:15]  # Limit for readability
    
    def _preprocess_with_beautifulsoup(self, raw_html: str, max_tokens: int, preserve_html_structure: bool) -> PreprocessedHTML:
        """Fallback preprocessing using BeautifulSoup."""
        soup = BeautifulSoup(raw_html, 'html.parser')
        
        # Simple boilerplate removal
        removed_elements = []
        for tag_name in self.BOILERPLATE_ELEMENTS:
            elements = soup.find_all(tag_name)
            if elements:
                removed_elements.append(f"{tag_name}({len(elements)})")
                for element in elements:
                    element.decompose()
        
        # Simple outline creation
        outline_str = self._create_simple_outline(soup)
        
        # Basic truncation
        if len(outline_str) > max_tokens * 4:  # Rough token estimation
            outline_str = outline_str[:max_tokens * 4] + "\n... [truncated] ..."
        
        return PreprocessedHTML(
            cleaned_html=outline_str,
            original_size=0,
            cleaned_size=len(outline_str),
            compression_ratio=0.0,
            processing_method="beautifulsoup_fallback",
            removed_elements=removed_elements,
            preserved_structure=[],
            content_density_info={}
        )
    
    def _create_simple_outline(self, soup) -> str:
        """Simple outline creation for BeautifulSoup fallback."""
        # Extract text with basic structure preservation
        text_parts = []
        for element in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'div', 'article', 'main']):
            text = element.get_text(strip=True)
            if text and len(text) > 10:
                text_parts.append(text)
        
        return '\n\n'.join(text_parts)
    
    def _analyze_content_density(self, text: str) -> Dict:
        """Analyze content density for smart truncation."""
        segments = [s.strip() for s in text.split('\n\n') if len(s.strip()) > 60]
        
        if not segments:
            return {"total_segments": 0, "avg_density": 0, "dense_segments": []}
        
        # Calculate density (chars per segment)
        densities = [(i, len(seg)) for i, seg in enumerate(segments)]
        densities.sort(key=lambda x: x[1], reverse=True)
        
        avg_density = sum(d[1] for d in densities) / len(densities)
        
        # Keep top 20 densest segments
        dense_segments = [d[0] for d in densities[:20]]
        
        return {
            "total_segments": len(segments),
            "avg_density": avg_density,
            "dense_segments": dense_segments,
            "segments": segments
        }
    
    def _smart_truncate(self, text: str, max_tokens: int, density_info: Dict, preserve_html_structure: bool = True) -> str:
        """Smart truncation that preserves both content and noise while maintaining HTML structure."""
        # Rough token estimation: 4 chars ≈ 1 token
        max_chars = max_tokens * 4
        
        if len(text) <= max_chars:
            return text
        
        if preserve_html_structure:
            # HTML-structure aware truncation
            return self._html_aware_truncate(text, max_chars, density_info)
        else:
            # Original text-based truncation for non-HTML modes
            return self._text_based_truncate(text, max_chars, density_info)
    
    def _html_aware_truncate(self, html_text: str, max_chars: int, density_info: Dict) -> str:
        """HTML-structure aware truncation that preserves tags and formatting."""
        lines = html_text.split('\n')
        
        # Preserve sentinel lines for purity assessment (in HTML format)
        sentinel_lines = []
        for i, line in enumerate(lines):
            if self.NOISE_SENTINELS.search(line):
                sentinel_lines.append((i, line))
        
        # Simple proportional truncation that preserves HTML structure
        if len(html_text) <= max_chars:
            return html_text
        
        # Calculate where to cut while trying to preserve HTML structure
        target_length = max_chars - 200  # Reserve space for truncation markers
        
        # Find a good breaking point (end of a tag or line)
        cut_point = target_length
        
        # Look for a good breaking point (end of tag or line)
        for i in range(target_length - 100, min(len(html_text), target_length + 100)):
            if i < len(html_text) and html_text[i] in ['\n', '>']:
                cut_point = i + 1
                break
        
        truncated_html = html_text[:cut_point]
        
        # Add noise samples if available (preserve HTML formatting)
        if sentinel_lines:
            sentinel_html = '\n'.join(line for _, line in sentinel_lines[:3])
            truncated_html += f"\n\n... [noise samples] ...\n{sentinel_html}"
        
        # Final length check
        if len(truncated_html) > max_chars:
            # More aggressive truncation if still too long
            final_cut = max_chars - 50
            for i in range(final_cut - 50, final_cut):
                if i < len(truncated_html) and truncated_html[i] in ['\n', '>']:
                    final_cut = i + 1
                    break
            truncated_html = truncated_html[:final_cut] + "\n... [truncated] ..."
        
        return truncated_html
    
    def _text_based_truncate(self, text: str, max_chars: int, density_info: Dict) -> str:
        """Original text-based truncation for non-HTML content."""
        lines = text.split('\n')
        
        # Preserve sentinel lines for purity assessment
        sentinel_lines = []
        for i, line in enumerate(lines):
            if self.NOISE_SENTINELS.search(line):
                sentinel_lines.append((i, line))
        
        # Window allocation strategy
        first_window = max_chars // 8    # 12.5% for start (nav, header)
        dense_window = max_chars * 6 // 8  # 75% for dense content
        last_window = max_chars // 8     # 12.5% for end (footer, comments)
        
        result_parts = []
        
        # First window (navigation, header noise)
        first_text = '\n'.join(lines[:len(lines)//20])  # First 5% of lines
        if len(first_text) > first_window:
            first_text = first_text[:first_window] + "\n... [header truncated] ..."
        result_parts.append(first_text)
        
        # Dense content from middle
        if 'segments' in density_info and density_info['dense_segments']:
            segments = density_info['segments']
            dense_content = []
            
            for seg_idx in density_info['dense_segments']:
                if seg_idx < len(segments):
                    dense_content.append(segments[seg_idx])
            
            dense_text = '\n\n'.join(dense_content)
            if len(dense_text) > dense_window:
                dense_text = dense_text[:dense_window] + "\n... [content truncated] ..."
            result_parts.append(dense_text)
        
        # Last window (footer, comments)
        last_text = '\n'.join(lines[-len(lines)//20:])  # Last 5% of lines
        if len(last_text) > last_window:
            last_text = "... [footer truncated] ...\n" + last_text[-last_window:]
        result_parts.append(last_text)
        
        # Always include sentinel lines for purity assessment
        if sentinel_lines:
            sentinel_text = '\n'.join(line for _, line in sentinel_lines[:5])
            result_parts.append(f"\n... [noise samples] ...\n{sentinel_text}")
        
        final_result = '\n\n'.join(filter(None, result_parts))
        
        # Final size check
        if len(final_result) > max_chars:
            final_result = final_result[:max_chars] + "\n... [truncated] ..."
        
        return final_result
    
    def _empty_result(self) -> PreprocessedHTML:
        """Return empty result for null input."""
        return PreprocessedHTML(
            cleaned_html="",
            original_size=0,
            cleaned_size=0,
            compression_ratio=0.0,
            processing_method="empty",
            removed_elements=[],
            preserved_structure=[],
            content_density_info={}
        )
    
    def _fallback_result(self, raw_html: str, max_tokens: int, original_size: int) -> PreprocessedHTML:
        """Fallback result for error cases."""
        # Ultra-simple fallback: just truncate
        max_chars = max_tokens * 4
        fallback_html = raw_html[:max_chars] + "..." if len(raw_html) > max_chars else raw_html
        
        return PreprocessedHTML(
            cleaned_html=fallback_html,
            original_size=original_size,
            cleaned_size=len(fallback_html),
            compression_ratio=0.0,
            processing_method="fallback_truncation",
            removed_elements=["preprocessing_error"],
            preserved_structure=[],
            content_density_info={}
        )
    
    def get_preprocessing_summary(self, result: PreprocessedHTML) -> str:
        """Generate human-readable summary of preprocessing results."""
        if result.compression_ratio > 0:
            method_info = f"[{result.processing_method}]"
            
            return (
                f"HTML optimized {method_info}: {result.compression_ratio:.1f}% reduction "
                f"({result.original_size:,} → {result.cleaned_size:,} chars). "
                f"Removed: {', '.join(result.removed_elements[:3])}{'...' if len(result.removed_elements) > 3 else ''}. "
                f"Preserved structure + noise samples for quality assessment."
            )
        else:
            return f"HTML preprocessing failed - using {result.processing_method}" 
    