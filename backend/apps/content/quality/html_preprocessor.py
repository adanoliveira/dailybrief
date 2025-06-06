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
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import json
from urllib.parse import urlparse, urljoin

# Conditional lxml import with graceful fallback
try:
    from lxml import html as lxml_html, etree
    LXML_AVAILABLE = True
except ImportError:
    LXML_AVAILABLE = False
    
from bs4 import BeautifulSoup, Tag

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
        "img": ["src", "alt", "data-src", "title", "width", "height", "srcset", "srcSet", "sizes", "data-image-container"],
        "source": ["srcset", "srcSet", "data-srcset", "media", "type", "sizes"],
        "iframe": ["src", "title", "data-src"],
        "video": ["src", "poster", "data-src"],
        "audio": ["src", "data-src"],
        "a": ["href", "title"],  # Keep href for link extraction
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
        preserve_html_structure: bool = True,
        base_url: Optional[str] = None
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
        
        # Store base_url for URL conversion
        self.base_url = base_url
        
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
            # Step 0: Decode HTML entities early in the pipeline
            from html import unescape
            decoded_html = unescape(raw_html)
            
            # Step 1: Parse and normalize - try multiple parsing approaches
            doc = None
            parsing_errors = []
            
            # Try fromstring first (strict parsing) with decoded HTML
            try:
                doc = lxml_html.fromstring(decoded_html.encode('utf-8', 'replace'))
            except Exception as e:
                parsing_errors.append(f"fromstring: {e}")
                
            # Fallback to document_fromstring (more lenient)
            if doc is None:
                try:
                    doc = lxml_html.document_fromstring(decoded_html.encode('utf-8', 'replace'))
                except Exception as e:
                    parsing_errors.append(f"document_fromstring: {e}")
            
            # If lxml parsing completely fails, fall back to BeautifulSoup with decoded HTML
            if doc is None:
                logger.warning(f"lxml parsing failed: {parsing_errors}. Falling back to BeautifulSoup.")
                return self._preprocess_with_beautifulsoup(decoded_html, max_tokens, preserve_html_structure)

            # Step 1.5: Extract Next.js images BEFORE removing scripts (Washington Post style)
            nextjs_images = []
            try:
                nextjs_images = self._extract_nextjs_images_lxml(doc)
            except Exception as e:
                logger.debug(f"Next.js image extraction failed: {e}")
            
            # Step 2: Remove boilerplate (safely)
            removed_elements = self._remove_boilerplate_lxml_safe(doc)
            
            # Step 2.1: Inject Next.js images after boilerplate removal (Washington Post style)
            injected_count = 0
            try:
                if nextjs_images:
                    injected_count = self._inject_missing_images_lxml(doc, nextjs_images)
                    if injected_count > 0:
                        removed_elements.append(f"injected_nextjs_images({injected_count})")
            except Exception as e:
                logger.debug(f"Next.js image injection failed: {e}")
            
            # Step 2.5: Enhance responsive images (ESPN-style) - but avoid overwriting Next.js injected images
            try:
                enhanced_count = self._enhance_responsive_images_lxml(doc, skip_nextjs_injected=injected_count > 0)
                if enhanced_count > 0:
                    removed_elements.append(f"enhanced_responsive_images({enhanced_count})")
            except Exception as e:
                logger.debug(f"Responsive image enhancement failed: {e}")
            
            # Step 2.7: Extract main content area (same logic as BeautifulSoup fix)
            try:
                main_content_doc = self._extract_main_content_lxml(doc)
                if main_content_doc is not None:
                    doc = main_content_doc
                    removed_elements.append("extracted_main_content")
            except Exception as e:
                logger.debug(f"Main content extraction failed: {e}")
            
            # Step 2.8: Convert relative URLs to absolute URLs
            try:
                converted_urls = self._convert_relative_urls_to_absolute(doc, is_lxml=True)
                if converted_urls > 0:
                    removed_elements.append(f"converted_relative_urls({converted_urls})")
            except Exception as e:
                logger.debug(f"URL conversion failed: {e}")
            
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
                
            # Remove small images (author profiles, newsletter imgs, icons)
            try:
                small_images_removed = 0
                for img in doc.xpath('//img'):
                    try:
                        if self._is_small_image(img):
                            img.drop_tree()
                            small_images_removed += 1
                    except:
                        pass
                if small_images_removed > 0:
                    removed_elements.append(f"small_images({small_images_removed})")
            except Exception as e:
                logger.debug(f"Failed to remove small images: {e}")
                
        except Exception as e:
            logger.debug(f"Boilerplate removal failed: {e}")
        
        return removed_elements
    
    def _is_small_image(self, img_element) -> bool:
        """
        Check if an image is small (likely a profile pic, icon, or newsletter image).
        Returns True if the image should be filtered out.
        """
        try:
            # Get width and height attributes
            width_str = img_element.get('width', '').strip()
            height_str = img_element.get('height', '').strip()
            
            # Parse dimensions
            width = height = None
            try:
                if width_str:
                    width = int(float(width_str))  # Handle both "200" and "200.0"
                if height_str:
                    height = int(float(height_str))
            except (ValueError, TypeError):
                pass
            
            # Filter by dimensions if available
            if width is not None and height is not None:
                # Remove images smaller than 100px in either dimension (likely separators/thin elements)
                if width < 100 or height < 100:
                    return True
                # Remove all small images smaller than 200x200 (rarely relevant content)
                if width < 200 and height < 200:
                    return True
            
            # Filter by common small image indicators in attributes
            alt_text = (img_element.get('alt', '') or '').lower()
            class_attr = (img_element.get('class', '') or '').lower()
            
            # Only check alt text and class attributes for semantic indicators
            # Avoid checking URLs which can have false positives
            all_text = f"{alt_text} {class_attr}"
            
            # Common patterns for small/unwanted images (more specific)
            small_image_indicators = [
                'profile pic', 'profile image', 'avatar', 'author photo', 'headshot', 'byline photo',
                'newsletter', 'signup', 'subscribe',
                'icon-', 'logo-', 'badge-', 'btn-', 'button-',  # With separators to be more specific
                'social icon', 'facebook icon', 'twitter icon', 'linkedin icon', 'instagram icon',
                'advertisement', 'sponsor logo',  # More specific than just 'ad'
                'menu icon', 'navigation icon', 'nav-',
                'thumbnail small', 'thumb-'  # More specific
            ]
            
            # Check if any indicators are present (whole word matches for better precision)
            for indicator in small_image_indicators:
                if indicator in all_text:
                    return True
            
            # Additional check: very generic alt text often indicates UI elements
            if alt_text in ['', 'no alt', 'image', 'photo', 'picture']:
                # Only filter if we also have small dimensions (same threshold as main filter)
                if width is not None and height is not None and (width < 50 or height < 50):
                    return True
            
            # If no clear indicators and not small dimensions, keep the image
            return False
            
        except Exception:
            # If we can't determine, err on the side of keeping the image
            return False
    
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
                                # Don't truncate critical URL attributes - they're needed for content extraction
                                if attr in ["href", "src", "data-src", "poster", "srcset", "srcSet", "data-srcset"]:
                                    attrs.append(f'{attr}=\"{value}\"')
                                # Don't truncate alt text and title - they're crucial for accessibility and content understanding
                                elif attr in ["alt", "title"]:
                                    attrs.append(f'{attr}="{value}"')
                                # Truncate very long non-critical values but keep them readable
                                elif len(value) > 200:
                                    value = value[:200] + "..."
                                    attrs.append(f'{attr}="{value}"')
                                else:
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
        # Decode HTML entities if not already done
        from html import unescape
        if not hasattr(raw_html, '_entities_decoded'):
            decoded_html = unescape(raw_html)
        else:
            decoded_html = raw_html
            
        soup = BeautifulSoup(decoded_html, 'html.parser')
        
        # Extract Next.js images before any processing
        nextjs_images = self._extract_nextjs_images(soup)
        
        # Remove boilerplate elements
        removed_elements = self._remove_boilerplate_beautifulsoup(soup)
        
        # Inject missing images from Next.js data first (before responsive enhancement)
        injected_count = 0
        if nextjs_images:
            injected_count = self._inject_missing_images(soup, nextjs_images)
            if injected_count > 0:
                removed_elements.append(f"injected_nextjs_images({injected_count})")
        
        # Enhance responsive images (ESPN-style) - but avoid overwriting Next.js injected images
        enhanced_count = self._enhance_responsive_images(soup, skip_nextjs_injected=injected_count > 0)
        if enhanced_count > 0:
            removed_elements.append(f"enhanced_responsive_images({enhanced_count})")
        
        # Remove small images (like profile pics)
        removed_elements.extend(self._remove_small_images_beautifulsoup(soup))
        
        # Get main content if preserving structure
        main_content = soup
        if preserve_html_structure:
            main_content = self._extract_main_content_beautifulsoup(soup)
        
        # Convert relative URLs to absolute URLs
        try:
            converted_urls = self._convert_relative_urls_to_absolute(main_content, is_lxml=False)
            if converted_urls > 0:
                removed_elements.append(f"converted_relative_urls({converted_urls})")
        except Exception as e:
            logger.debug(f"URL conversion failed: {e}")
        
        # Format and clean the HTML
        cleaned_html = self._format_html_beautifulsoup(main_content)
        
        # Ensure we're within token limits
        if max_tokens > 0:
            cleaned_html = self._truncate_to_tokens(cleaned_html, max_tokens)
        
        removed_summary = f"Removed: {', '.join(removed_elements[:3])}{'...' if len(removed_elements) > 3 else ''}"
        if injected_count > 0:
            removed_summary += f", Injected {injected_count} Next.js images"
        
        return PreprocessedHTML(
            cleaned_html=cleaned_html,
            original_size=0,
            cleaned_size=len(cleaned_html),
            compression_ratio=0.0,
            processing_method="beautifulsoup_fallback",
            removed_elements=removed_elements,
            preserved_structure=[],
            content_density_info={}
        )
    
    def _extract_nextjs_images(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract image data from Next.js __NEXT_DATA__ script blocks."""
        images = []
        
        try:
            # Find the __NEXT_DATA__ script
            next_data_script = soup.find('script', {'id': '__NEXT_DATA__'})
            if not next_data_script or not next_data_script.string:
                return images
            
            # Parse the JSON data
            data = json.loads(next_data_script.string)
            
            # Navigate to content_elements in the nested structure
            props = data.get('props', {})
            page_props = props.get('pageProps', {})
            global_content = page_props.get('globalContent', {})
            content_elements = global_content.get('content_elements', [])
            
            # Extract image elements
            for element in content_elements:
                if element.get('type') == 'image':
                    image_data = {
                        'id': element.get('_id', ''),
                        'url': element.get('url', ''),
                        'alt_text': element.get('alt_text', ''),
                        'width': element.get('width', 0),
                        'height': element.get('height', 0),
                        'caption': element.get('credits_caption_display', ''),
                        'subtype': element.get('subtype', '')
                    }
                    if image_data['url']:  # Only include if we have a URL
                        images.append(image_data)
                        
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            # Log but don't fail - just continue without enhanced images
            pass
            
        return images

    def _inject_missing_images(self, soup: BeautifulSoup, images: List[Dict]) -> int:
        """Inject missing images into placeholder divs and figure elements with intelligent matching."""
        injected_count = 0
        
        try:
            if not images:
                return 0
                
            # Find all image containers that need images, in DOM order
            image_containers = []
            
            # Add figure elements that have img tags without src (these come first in article layout)
            figures = soup.find_all('figure')
            for figure in figures:
                img_in_figure = figure.find('img')
                if img_in_figure and not img_in_figure.get('src'):
                    image_containers.append(('figure', figure, img_in_figure))
            
            # Add type-image div containers (these come after in article body)
            type_image_divs = soup.find_all('div', class_=lambda x: x and 'type-image' in x)
            for div in type_image_divs:
                existing_img = div.find('img')
                if not (existing_img and existing_img.get('src')):
                    image_containers.append(('type-image', div, existing_img))
            
            # Smart matching: assign images to containers in the order they appear in content
            # The first image (Hero) goes to the first figure
            # Subsequent images go to type-image containers in order
            
            image_assignments = []
            available_images = images.copy()
            
            for i, (container_type, container, existing_img) in enumerate(image_containers):
                if not available_images:
                    break
                    
                if container_type == 'figure' and i == 0:
                    # First figure gets the first/hero image
                    image_data = available_images.pop(0)
                    image_assignments.append((container_type, container, existing_img, image_data))
                elif container_type == 'type-image':
                    # type-image containers get remaining images in order
                    if available_images:
                        image_data = available_images.pop(0)
                        image_assignments.append((container_type, container, existing_img, image_data))
            
            # Execute the assignments
            for container_type, container, existing_img, image_data in image_assignments:
                if container_type == 'figure':
                    # Handle figure elements - inject src into existing img
                    if existing_img:
                        existing_img['src'] = image_data['url']
                        existing_img['alt'] = image_data['alt_text']
                        
                        if image_data['width'] > 0:
                            existing_img['width'] = str(image_data['width'])
                        if image_data['height'] > 0:
                            existing_img['height'] = str(image_data['height'])
                        
                        injected_count += 1
                        
                else:  # type-image
                    # Handle type-image div containers - create new img element
                    img_tag = soup.new_tag('img')
                    img_tag['src'] = image_data['url']
                    img_tag['alt'] = image_data['alt_text']
                    
                    if image_data['width'] > 0:
                        img_tag['width'] = str(image_data['width'])
                    if image_data['height'] > 0:
                        img_tag['height'] = str(image_data['height'])
                    
                    # Insert into the container
                    inner_div = container.find('div', class_=lambda x: x and any(cls in x for cls in ['PJLV', 'hide-for-print']))
                    if inner_div:
                        # Clear existing content and add our image
                        inner_div.clear()
                        inner_div.append(img_tag)
                        
                        # Add caption if available
                        if image_data['caption']:
                            caption_tag = soup.new_tag('figcaption')
                            caption_tag.string = image_data['caption']
                            inner_div.append(caption_tag)
                        
                        injected_count += 1
                    
        except Exception as e:
            # Log but don't fail
            pass
            
        return injected_count
    
    def _remove_boilerplate_beautifulsoup(self, soup) -> List[str]:
        """Remove boilerplate elements using BeautifulSoup."""
        removed_elements = []
        
        for tag_name in self.BOILERPLATE_ELEMENTS:
            elements = soup.find_all(tag_name)
            if elements:
                removed_elements.append(f"{tag_name}({len(elements)})")
                for element in elements:
                    element.decompose()
        
        return removed_elements
    
    def _remove_small_images_beautifulsoup(self, soup) -> List[str]:
        """Remove small images using BeautifulSoup."""
        removed_small_images = []
        
        for img in soup.find_all('img'):
            if self._is_small_image(img):
                # Get src before decomposing the element
                src = img.get('src', 'unknown')
                img.decompose()
                removed_small_images.append(f"small_image({src})")
        
        return removed_small_images
    
    def _format_html_beautifulsoup(self, soup) -> str:
        """Format HTML using BeautifulSoup."""
        return soup.prettify()
    
    def _truncate_to_tokens(self, html_content: str, max_tokens: int) -> str:
        """Truncate HTML content to a specified number of tokens."""
        # This method needs to be implemented based on your tokenization logic
        # For now, we'll use a placeholder implementation
        return html_content[:max_tokens * 4]  # Placeholder implementation
    
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
    
    def _extract_main_content_beautifulsoup(self, soup) -> BeautifulSoup:
        """Extract main content using BeautifulSoup, preserving article body while removing navigation."""
        
        # Strategy: Keep main article content areas while removing navigation/sidebar boilerplate
        main_content_selectors = [
            # Content-specific selectors for common news sites (prioritize these)
            '.RichTextStoryBody',  # AP News main content
            '.RichTextBody',       # AP News article body
            '.article-body',       # Generic article body
            '.post-content',       # Blog posts
            '.entry-content',      # WordPress
            '.story-body',         # News sites
            '.content-body',       # Generic content
            # Standard semantic tags (fallback)
            'main', 'article', '[role="main"]',
        ]
        
        # Try to find main content area
        main_content = None
        for selector in main_content_selectors:
            if '.' in selector:  # Class selector
                class_name = selector[1:]  # Remove the '.' prefix
                # Search for any element (not just div) with this class
                element = soup.find(class_=lambda x: x and class_name in (x if isinstance(x, list) else x.split()))
            elif '[' in selector:  # Attribute selector
                if 'role="main"' in selector:
                    element = soup.find(attrs={'role': 'main'})
                else:
                    element = None
            else:  # Tag selector
                element = soup.find(selector)
            
            if element:
                main_content = element
                break
        
        # Fallback: if no specific content area found, clean up the full soup
        if not main_content:
            main_content = soup
            
            # Remove navigation and other boilerplate from full document
            for selector in ['nav', 'header', 'footer', '.navigation', '.nav-menu', 
                           '.sidebar', '.menu', '.topbar', '.subheader']:
                if '.' in selector:  # Class selector
                    elements = soup.find_all('div', class_=lambda x: x and selector[1:] in x)
                else:  # Tag selector
                    elements = soup.find_all(selector)
                
                for elem in elements:
                    elem.decompose()
        
        # Post-processing: Handle carousel and media container duplication
        self._deduplicate_media_containers(main_content)
        
        return main_content

    def _deduplicate_media_containers(self, soup):
        """Remove duplicate carousel and media containers to prevent content duplication."""
        try:
            # Remove duplicate carousel slides that contain identical content
            carousel_containers = soup.find_all('div', class_=lambda x: x and any(
                cls in x for cls in ['Carousel', 'carousel', 'slide', 'media-container']
            ))
            
            seen_images = set()
            seen_captions = set()
            
            for container in carousel_containers:
                # Check for duplicate images by src
                images = container.find_all('img')
                container_has_duplicate = False
                
                for img in images:
                    src = img.get('src', '')
                    if src and src in seen_images:
                        container_has_duplicate = True
                        break
                    elif src:
                        seen_images.add(src)
                
                # Check for duplicate captions
                if not container_has_duplicate:
                    caption_text = container.get_text(strip=True)
                    if caption_text and len(caption_text) > 20:  # Only check substantial captions
                        if caption_text in seen_captions:
                            container_has_duplicate = True
                        else:
                            seen_captions.add(caption_text)
                
                # Remove duplicate container
                if container_has_duplicate:
                    container.decompose()
                    
        except Exception as e:
            # Don't fail processing if deduplication has issues
            pass
    
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
    
    def _enhance_responsive_images(self, soup: BeautifulSoup, skip_nextjs_injected: bool = False) -> int:
        """
        Extract primary image URLs from responsive image sources and populate missing img src attributes.
        Handles ESPN-style and other responsive image patterns.
        
        Args:
            soup: BeautifulSoup document
            skip_nextjs_injected: If True, be extra cautious to avoid overwriting Next.js injected images
        """
        enhanced_count = 0
        
        try:
            # Find picture elements with missing img src
            pictures = soup.find_all('picture')
            
            for picture in pictures:
                img = picture.find('img')
                if not img or img.get('src'):
                    continue  # Skip if no img or already has src
                
                # Extra safety: if Next.js injection happened, be more selective  
                if skip_nextjs_injected:
                    # Check if this img is in a type-image container (Next.js territory)
                    parent_container = img.find_parent('div', class_=lambda x: x and 'type-image' in x)
                    if parent_container:
                        # This is likely a Next.js injected area, skip to avoid conflicts
                        continue
                
                # Look for sources with image URLs
                sources = picture.find_all('source')
                primary_url = None
                
                for source in sources:
                    # Check different srcset attribute variations
                    srcset_value = (source.get('srcset') or 
                                  source.get('srcSet') or 
                                  source.get('data-srcset'))
                    
                    if srcset_value:
                        # Extract the first (usually highest quality) URL from srcset
                        # Format: "url1 1x, url2 2x" or "url1 500w, url2 1000w"
                        urls = [url.strip().split()[0] for url in srcset_value.split(',')]
                        if urls and urls[0]:
                            primary_url = urls[0]
                            break
                
                # Set the primary URL as img src
                if primary_url:
                    img['src'] = primary_url
                    enhanced_count += 1
                    
        except Exception as e:
            # Log but don't fail
            pass
            
        return enhanced_count
    
    def _enhance_responsive_images_lxml(self, doc, skip_nextjs_injected: bool = False) -> int:
        """
        Extract primary image URLs from responsive image sources and populate missing img src attributes.
        Handles ESPN-style and other responsive image patterns. (lxml version)
        
        Args:
            doc: The lxml document
            skip_nextjs_injected: If True, be extra cautious to avoid overwriting Next.js injected images
        """
        enhanced_count = 0
        
        try:
            # Find picture elements with missing img src
            pictures = doc.xpath('//picture')
            
            for picture in pictures:
                # Find img within this picture
                imgs = picture.xpath('.//img')
                if not imgs:
                    continue
                    
                img = imgs[0]  # Take the first img
                
                # Enhanced check: skip if already has src or if we're being cautious about Next.js images
                if img.get('src'):
                    continue  # Skip if already has src
                
                # Extra safety: if Next.js injection happened, be more selective
                if skip_nextjs_injected:
                    # Check if this img is in a type-image container (Next.js territory)
                    parent_containers = img.xpath('./ancestor::div[contains(@class, "type-image")]')
                    if parent_containers:
                        # This is likely a Next.js injected area, skip to avoid conflicts
                        continue
                
                # Look for sources with image URLs
                sources = picture.xpath('.//source')
                primary_url = None
                
                for source in sources:
                    # Check different srcset attribute variations
                    srcset_value = (source.get('srcset') or 
                                  source.get('srcSet') or 
                                  source.get('data-srcset'))
                    
                    if srcset_value:
                        # Extract the first (usually highest quality) URL from srcset
                        # Format: "url1 1x, url2 2x" or "url1 500w, url2 1000w"
                        try:
                            urls = [url.strip().split()[0] for url in srcset_value.split(',')]
                            if urls and urls[0]:
                                primary_url = urls[0]
                                break
                        except (IndexError, AttributeError):
                            continue
                
                # Set the primary URL as img src
                if primary_url:
                    img.set('src', primary_url)
                    enhanced_count += 1
                    
        except Exception as e:
            # Log but don't fail
            pass
            
        return enhanced_count
    
    def _extract_nextjs_images_lxml(self, doc) -> List[Dict]:
        """Extract image data from Next.js __NEXT_DATA__ script blocks. (lxml version)"""
        images = []
        
        try:
            # Find the __NEXT_DATA__ script using xpath
            scripts = doc.xpath('//script[@id="__NEXT_DATA__"]')
            if not scripts:
                return images
            
            next_data_script = scripts[0]
            script_text = next_data_script.text
            if not script_text:
                return images
            
            # Parse the JSON data
            data = json.loads(script_text)
            
            # Navigate to content_elements in the Next.js data structure
            props = data.get('props', {})
            page_props = props.get('pageProps', {})
            global_content = page_props.get('globalContent', {})
            content_elements = global_content.get('content_elements', [])
            
            # Extract image information
            for element in content_elements:
                if element.get('type') == 'image':
                    # Extract image data
                    image_data = {
                        'url': element.get('url', ''),
                        'alt_text': element.get('alt_text', ''),
                        'width': element.get('width', 0),
                        'height': element.get('height', 0),
                        'caption': element.get('credits_caption_display', ''),
                        'subtype': element.get('subtype', '')
                    }
                    if image_data['url']:  # Only include if we have a URL
                        images.append(image_data)
                        
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            # Log but don't fail - just continue without enhanced images
            pass
            
        return images

    def _inject_missing_images_lxml(self, doc, images: List[Dict]) -> int:
        """Inject missing images into placeholder divs and figure elements with intelligent matching. (lxml version)"""
        injected_count = 0
        
        try:
            if not images:
                return 0
                
            # Find all image containers that need images, in DOM order
            image_containers = []
            
            # Add figure elements that have img tags without src (these come first in article layout)
            figures = doc.xpath('//figure')
            for figure in figures:
                imgs_in_figure = figure.xpath('.//img[not(@src)]')
                if imgs_in_figure:
                    image_containers.append(('figure', figure, imgs_in_figure[0]))
            
            # Add type-image div containers (these come after in article body)
            type_image_divs = doc.xpath('//div[contains(@class, "type-image")]')
            for div in type_image_divs:
                existing_imgs = div.xpath('.//img[@src]')
                if not existing_imgs:
                    # No img with src, so it needs one
                    existing_img_no_src = div.xpath('.//img[not(@src)]')
                    existing_img = existing_img_no_src[0] if existing_img_no_src else None
                    image_containers.append(('type-image', div, existing_img))
            
            # Smart matching: assign images to containers in the order they appear in content
            # The first image (Hero) goes to the first figure
            # Subsequent images go to type-image containers in order
            
            image_assignments = []
            available_images = images.copy()
            
            for i, (container_type, container, existing_img) in enumerate(image_containers):
                if not available_images:
                    break
                    
                if container_type == 'figure' and i == 0:
                    # First figure gets the first/hero image
                    image_data = available_images.pop(0)
                    image_assignments.append((container_type, container, existing_img, image_data))
                elif container_type == 'type-image':
                    # type-image containers get remaining images in order
                    if available_images:
                        image_data = available_images.pop(0)
                        image_assignments.append((container_type, container, existing_img, image_data))
            
            # Execute the assignments
            for container_type, container, existing_img, image_data in image_assignments:
                if container_type == 'figure':
                    # Handle figure elements - inject src into existing img
                    if existing_img is not None:
                        existing_img.set('src', image_data['url'])
                        existing_img.set('alt', image_data['alt_text'])
                        
                        if image_data['width'] > 0:
                            existing_img.set('width', str(image_data['width']))
                        if image_data['height'] > 0:
                            existing_img.set('height', str(image_data['height']))
                        
                        injected_count += 1
                        
                else:  # type-image
                    # Handle type-image div containers - create new img element
                    # Find the inner div to inject into
                    inner_divs = container.xpath('.//div[contains(@class, "PJLV") or contains(@class, "hide-for-print")]')
                    if inner_divs:
                        inner_div = inner_divs[0]
                        
                        # Clear existing content
                        inner_div.clear()
                        
                        # Create new img element
                        img_element = lxml_html.Element('img')
                        img_element.set('src', image_data['url'])
                        img_element.set('alt', image_data['alt_text'])
                        
                        if image_data['width'] > 0:
                            img_element.set('width', str(image_data['width']))
                        if image_data['height'] > 0:
                            img_element.set('height', str(image_data['height']))
                        
                        # Insert into the container
                        inner_div.append(img_element)
                        
                        # Add caption if available
                        if image_data['caption']:
                            caption_element = lxml_html.Element('figcaption')
                            caption_element.text = image_data['caption']
                            inner_div.append(caption_element)
                        
                        injected_count += 1
                    
        except Exception as e:
            # Log but don't fail
            pass
            
        return injected_count
    
    def _extract_main_content_lxml(self, doc):
        """Extract main content using lxml, preserving article body while removing navigation."""
        
        # Strategy: Keep main article content areas while removing navigation/sidebar boilerplate
        main_content_selectors = [
            # Content-specific selectors for common news sites (prioritize these)
            '.RichTextStoryBody',  # AP News main content
            '.RichTextBody',       # AP News article body
            '.article-body',       # Generic article body
            '.post-content',       # Blog posts
            '.entry-content',      # WordPress
            '.story-body',         # News sites
            '.content-body',       # Generic content
            # Standard semantic tags (fallback)
            'main', 'article', '[role="main"]',
        ]
        
        # Try to find main content area
        main_content = None
        for selector in main_content_selectors:
            if '.' in selector:  # Class selector
                class_name = selector[1:]  # Remove the '.' prefix
                # Use XPath to search for elements with this class
                xpath_query = f"//*[contains(concat(' ', @class, ' '), ' {class_name} ')]"
                elements = doc.xpath(xpath_query)
                if elements:
                    element = elements[0]  # Take the first match
            elif '[' in selector:  # Attribute selector
                if 'role="main"' in selector:
                    elements = doc.xpath("//*[@role='main']")
                    element = elements[0] if elements else None
            else:  # Tag selector
                elements = doc.xpath(f"//{selector}")
                element = elements[0] if elements else None
            
            if element is not None:
                main_content = element
                break
        
        # Fallback: if no specific content area found, clean up the full document
        if main_content is None:
            main_content = doc
            
            # Remove navigation and other boilerplate from full document
            for selector in ['nav', 'header', 'footer', '.navigation', '.nav-menu', 
                           '.sidebar', '.menu', '.topbar', '.subheader']:
                if '.' in selector:  # Class selector
                    class_name = selector[1:]
                    xpath_query = f"//*[contains(concat(' ', @class, ' '), ' {class_name} ')]"
                    elements = doc.xpath(xpath_query)
                else:  # Tag selector
                    elements = doc.xpath(f"//{selector}")
                
                for elem in elements:
                    try:
                        elem.drop_tree()
                    except:
                        try:
                            elem.getparent().remove(elem)
                        except:
                            pass
        
        # Post-processing: Handle carousel and media container duplication
        self._deduplicate_media_containers_lxml(main_content)
        
        return main_content

    def _deduplicate_media_containers_lxml(self, doc):
        """Remove duplicate carousel and media containers to prevent content duplication (lxml version)."""
        try:
            # Remove duplicate carousel slides that contain identical content
            carousel_xpath = "//*[contains(concat(' ', @class, ' '), ' Carousel ') or contains(concat(' ', @class, ' '), ' carousel ') or contains(concat(' ', @class, ' '), ' slide ') or contains(concat(' ', @class, ' '), ' media-container ')]"
            carousel_containers = doc.xpath(carousel_xpath)
            
            seen_images = set()
            seen_captions = set()
            
            for container in carousel_containers:
                # Check for duplicate images by src
                images = container.xpath(".//img")
                container_has_duplicate = False
                
                for img in images:
                    src = img.get('src', '')
                    if src and src in seen_images:
                        container_has_duplicate = True
                        break
                    elif src:
                        seen_images.add(src)
                
                # Check for duplicate captions
                if not container_has_duplicate:
                    caption_text = container.text_content().strip()
                    if caption_text and len(caption_text) > 20:  # Only check substantial captions
                        if caption_text in seen_captions:
                            container_has_duplicate = True
                        else:
                            seen_captions.add(caption_text)
                
                # Remove duplicate container
                if container_has_duplicate:
                    try:
                        container.drop_tree()
                    except:
                        try:
                            container.getparent().remove(container)
                        except:
                            pass
                    
        except Exception as e:
            # Don't fail processing if deduplication has issues
            pass
    
    def _convert_relative_urls_to_absolute(self, doc, is_lxml: bool = True) -> int:
        """
        Convert relative URLs to absolute URLs for better AI processing.
        
        Args:
            doc: lxml or BeautifulSoup document
            is_lxml: Whether this is an lxml document (vs BeautifulSoup)
            
        Returns:
            int: Number of URLs converted
        """
        if not self.base_url:
            return 0
            
        converted_count = 0
        
        # Parse base URL to ensure it's valid
        try:
            parsed_base = urlparse(self.base_url)
            if not parsed_base.scheme or not parsed_base.netloc:
                logger.debug(f"Invalid base URL: {self.base_url}")
                return 0
                
            base_domain = f"{parsed_base.scheme}://{parsed_base.netloc}"
            
        except Exception as e:
            logger.debug(f"Failed to parse base URL {self.base_url}: {e}")
            return 0
        
        # URL attributes to convert
        url_attributes = ['src', 'href', 'data-src', 'poster', 'srcset', 'data-srcset']
        
        try:
            if is_lxml:
                # lxml processing
                for attr in url_attributes:
                    elements = doc.xpath(f'//*[@{attr}]')
                    for element in elements:
                        try:
                            current_value = element.get(attr, '').strip()
                            if current_value and current_value.startswith('/') and not current_value.startswith('//'):
                                # This is a relative URL starting with /
                                absolute_url = urljoin(base_domain, current_value)
                                element.set(attr, absolute_url)
                                converted_count += 1
                        except Exception as e:
                            logger.debug(f"Failed to convert URL in {attr}: {e}")
                            continue
            else:
                # BeautifulSoup processing
                for attr in url_attributes:
                    elements = doc.find_all(attrs={attr: True})
                    for element in elements:
                        try:
                            current_value = element.get(attr, '').strip()
                            if current_value and current_value.startswith('/') and not current_value.startswith('//'):
                                # This is a relative URL starting with /
                                absolute_url = urljoin(base_domain, current_value)
                                element[attr] = absolute_url
                                converted_count += 1
                        except Exception as e:
                            logger.debug(f"Failed to convert URL in {attr}: {e}")
                            continue
                            
        except Exception as e:
            logger.debug(f"URL conversion failed: {e}")
            
        return converted_count
    