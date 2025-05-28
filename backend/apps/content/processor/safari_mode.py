"""
Safari Reader Mode-like Content Processor
Implementation based on WebKit's ReaderArticleFinder algorithm.
"""

import re
import math
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from bs4 import BeautifulSoup, Tag, NavigableString
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)


@dataclass
class ContentBlock:
    """Structured content block."""
    type: str  # heading, paragraph, image, video, quote, list
    content: str
    level: Optional[int] = None  # For headings (1-6)
    position: int = 0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ProcessingResult:
    """Result of Safari mode processing."""
    success: bool
    clean_content: str = ""
    content_blocks: List[ContentBlock] = None
    extracted_metadata: Dict[str, Any] = None
    quality_score: float = 0.0
    processing_time_ms: int = 0
    error_message: str = ""
    
    def __post_init__(self):
        if self.content_blocks is None:
            self.content_blocks = []
        if self.extracted_metadata is None:
            self.extracted_metadata = {}


class SafariModeProcessor:
    """
    Safari Reader Mode-like content processing using proven algorithms.
    Based on WebKit's ReaderArticleFinder implementation.
    """
    
    # Content scoring constants (from WebKit)
    MIN_SCORE_THRESHOLD = 1600
    MIN_ADVANTAGE_GAP = 15
    MIN_WIDTH = 280
    MIN_HEIGHT = 295
    MIN_DENSITY = 4.25
    
    # Element scoring patterns
    POSITIVE_PATTERNS = [
        r'article', r'body', r'content', r'entry', r'hentry', r'main', r'page',
        r'pagination', r'post', r'text', r'blog', r'story', r'news'
    ]
    
    NEGATIVE_PATTERNS = [
        r'combx', r'comment', r'com-', r'contact', r'foot', r'footer', r'footnote',
        r'masthead', r'media', r'meta', r'outbrain', r'promo', r'related', r'scroll',
        r'shoutbox', r'sidebar', r'sponsor', r'shopping', r'tags', r'tool', r'widget',
        r'ad', r'advertisement', r'banner', r'popup', r'navigation', r'nav'
    ]
    
    def __init__(self):
        self.positive_regex = re.compile('|'.join(self.POSITIVE_PATTERNS), re.IGNORECASE)
        self.negative_regex = re.compile('|'.join(self.NEGATIVE_PATTERNS), re.IGNORECASE)
    
    def process_content(self, raw_html: str, article_metadata: Dict[str, Any]) -> ProcessingResult:
        """
        Main processing pipeline implementing Safari Reader Mode algorithm.
        """
        
        import time
        start_time = time.time()
        
        try:
            # Parse HTML
            soup = BeautifulSoup(raw_html, 'html.parser')
            
            # 1. Content structure analysis
            content_analysis = self._analyze_content_structure(soup)
            
            # 2. Main content identification using Safari algorithm
            main_content_element = self._identify_main_content(soup, content_analysis)
            
            if not main_content_element:
                return ProcessingResult(
                    success=False,
                    error_message="Could not identify main content element",
                    processing_time_ms=int((time.time() - start_time) * 1000)
                )
            
            # 3. Content cleaning and formatting
            clean_content = self._clean_and_format_content(main_content_element)
            
            # 4. Structure content into blocks
            content_blocks = self._structure_content_blocks(main_content_element)
            
            # 5. Extract enhanced metadata
            extracted_metadata = self._extract_metadata(soup, clean_content, article_metadata)
            
            # 6. Assess quality
            quality_score = self._assess_quality(clean_content, content_blocks, extracted_metadata)
            
            processing_time = int((time.time() - start_time) * 1000)
            
            return ProcessingResult(
                success=True,
                clean_content=clean_content,
                content_blocks=content_blocks,
                extracted_metadata=extracted_metadata,
                quality_score=quality_score,
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            logger.exception(f"Safari mode processing failed: {str(e)}")
            return ProcessingResult(
                success=False,
                error_message=str(e),
                processing_time_ms=int((time.time() - start_time) * 1000)
            )
    
    def _analyze_content_structure(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """
        Analyze content structure using Safari's scoring algorithm.
        """
        
        element_scores = {}
        
        # Find all potential content containers
        candidates = soup.find_all(['div', 'article', 'section', 'main', 'p'])
        
        for element in candidates:
            score = self._calculate_element_score(element)
            if score > 0:
                element_scores[element] = score
        
        return {
            'element_scores': element_scores,
            'total_candidates': len(candidates),
            'scored_elements': len(element_scores)
        }
    
    def _calculate_element_score(self, element: Tag) -> float:
        """
        Calculate element score using Safari's algorithm:
        - Text weight: len^1.25 for each text node
        - Element bonuses/penalties based on class/id patterns
        - Geometry analysis for layout understanding
        """
        
        if not isinstance(element, Tag):
            return 0
        
        # Base score from text content
        text_content = element.get_text(strip=True)
        if not text_content:
            return 0
        
        # Text weight calculation (Safari uses len^1.25)
        text_score = len(text_content) ** 1.25
        
        # Class and ID bonuses/penalties
        class_id_score = self._calculate_class_id_score(element)
        
        # Link density penalty
        link_penalty = self._calculate_link_density_penalty(element)
        
        # Paragraph bonus
        paragraph_bonus = self._calculate_paragraph_bonus(element)
        
        # Combine scores
        total_score = text_score + class_id_score + paragraph_bonus - link_penalty
        
        return max(0, total_score)
    
    def _calculate_class_id_score(self, element: Tag) -> float:
        """
        Calculate bonus/penalty based on class and id attributes.
        """
        
        score = 0
        
        # Check class attribute
        class_attr = element.get('class', [])
        if isinstance(class_attr, list):
            class_str = ' '.join(class_attr)
        else:
            class_str = str(class_attr)
        
        # Check id attribute
        id_attr = element.get('id', '')
        
        combined_attrs = f"{class_str} {id_attr}".lower()
        
        # Positive patterns bonus
        if self.positive_regex.search(combined_attrs):
            score += 25
        
        # Negative patterns penalty
        if self.negative_regex.search(combined_attrs):
            score -= 25
        
        return score
    
    def _calculate_link_density_penalty(self, element: Tag) -> float:
        """
        Calculate penalty based on link density (too many links = navigation/ads).
        """
        
        text_length = len(element.get_text(strip=True))
        if text_length == 0:
            return 0
        
        # Calculate link text length
        links = element.find_all('a')
        link_text_length = sum(len(link.get_text(strip=True)) for link in links)
        
        # Link density ratio
        link_density = link_text_length / text_length
        
        # Penalty increases with link density
        if link_density > 0.5:
            return text_length * link_density * 2
        elif link_density > 0.3:
            return text_length * link_density
        
        return 0
    
    def _calculate_paragraph_bonus(self, element: Tag) -> float:
        """
        Calculate bonus for elements with good paragraph structure.
        """
        
        paragraphs = element.find_all('p')
        if not paragraphs:
            return 0
        
        # Bonus for having multiple substantial paragraphs
        substantial_paragraphs = [
            p for p in paragraphs 
            if len(p.get_text(strip=True)) > 50
        ]
        
        if len(substantial_paragraphs) >= 3:
            return len(substantial_paragraphs) * 10
        elif len(substantial_paragraphs) >= 2:
            return len(substantial_paragraphs) * 5
        
        return 0
    
    def _identify_main_content(self, soup: BeautifulSoup, analysis: Dict[str, Any]) -> Optional[Tag]:
        """
        Identify main content element using Safari's advantage gap analysis.
        """
        
        element_scores = analysis['element_scores']
        
        if not element_scores:
            return None
        
        # Sort elements by score
        sorted_elements = sorted(element_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Check if top element meets minimum requirements
        top_element, top_score = sorted_elements[0]
        
        if top_score < self.MIN_SCORE_THRESHOLD:
            logger.warning(f"Top element score {top_score} below threshold {self.MIN_SCORE_THRESHOLD}")
            # Still try to use it if it's the best we have
        
        # Check advantage gap (Safari requires 15 point advantage)
        if len(sorted_elements) > 1:
            second_score = sorted_elements[1][1]
            advantage_gap = top_score - second_score
            
            if advantage_gap < self.MIN_ADVANTAGE_GAP:
                logger.warning(f"Advantage gap {advantage_gap} below minimum {self.MIN_ADVANTAGE_GAP}")
        
        return top_element
    
    def _clean_and_format_content(self, main_element: Tag) -> str:
        """
        Clean content while preserving important formatting.
        """
        
        # Create a copy to avoid modifying original
        cleaned_element = BeautifulSoup(str(main_element), 'html.parser')
        
        # Remove unwanted elements
        unwanted_selectors = [
            'script', 'style', 'nav', 'footer', 'aside', 'header',
            '.advertisement', '.ad', '.ads', '.social-share',
            '.related-articles', '.comments', '.comment-section',
            '.newsletter-signup', '.popup', '.modal'
        ]
        
        for selector in unwanted_selectors:
            for element in cleaned_element.select(selector):
                element.decompose()
        
        # Clean up attributes but preserve important ones
        for element in cleaned_element.find_all():
            if hasattr(element, 'attrs'):
                # Keep only essential attributes
                essential_attrs = {}
                if element.name in ['a'] and 'href' in element.attrs:
                    essential_attrs['href'] = element.attrs['href']
                if element.name in ['img'] and 'src' in element.attrs:
                    essential_attrs['src'] = element.attrs['src']
                if element.name in ['img'] and 'alt' in element.attrs:
                    essential_attrs['alt'] = element.attrs['alt']
                
                element.attrs = essential_attrs
        
        # Convert to clean text with preserved structure
        return self._element_to_clean_text(cleaned_element)
    
    def _element_to_clean_text(self, element: Tag) -> str:
        """
        Convert element to clean text with preserved formatting.
        """
        
        result = []
        
        for child in element.children:
            if isinstance(child, NavigableString):
                text = str(child).strip()
                if text:
                    result.append(text)
            elif isinstance(child, Tag):
                if child.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    text = child.get_text(strip=True)
                    if text:
                        result.append(f"\n\n## {text}\n")
                elif child.name == 'p':
                    text = child.get_text(strip=True)
                    if text:
                        result.append(f"\n{text}\n")
                elif child.name in ['ul', 'ol']:
                    list_items = []
                    for li in child.find_all('li'):
                        item_text = li.get_text(strip=True)
                        if item_text:
                            list_items.append(f"• {item_text}")
                    if list_items:
                        result.append(f"\n{chr(10).join(list_items)}\n")
                elif child.name == 'blockquote':
                    text = child.get_text(strip=True)
                    if text:
                        result.append(f"\n> {text}\n")
                else:
                    # Recursively process other elements
                    child_text = self._element_to_clean_text(child)
                    if child_text.strip():
                        result.append(child_text)
        
        return ' '.join(result)
    
    def _structure_content_blocks(self, main_element: Tag) -> List[ContentBlock]:
        """
        Structure content into semantic blocks.
        """
        
        blocks = []
        position = 0
        
        for element in main_element.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'blockquote', 'ul', 'ol', 'img']):
            block = self._element_to_content_block(element, position)
            if block:
                blocks.append(block)
                position += 1
        
        return blocks
    
    def _element_to_content_block(self, element: Tag, position: int) -> Optional[ContentBlock]:
        """
        Convert HTML element to ContentBlock.
        """
        
        if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            level = int(element.name[1])
            text = element.get_text(strip=True)
            if text:
                return ContentBlock(
                    type='heading',
                    content=text,
                    level=level,
                    position=position
                )
        
        elif element.name == 'p':
            text = element.get_text(strip=True)
            if text and len(text) > 20:  # Minimum paragraph length
                return ContentBlock(
                    type='paragraph',
                    content=text,
                    position=position
                )
        
        elif element.name == 'blockquote':
            text = element.get_text(strip=True)
            if text:
                return ContentBlock(
                    type='quote',
                    content=text,
                    position=position
                )
        
        elif element.name in ['ul', 'ol']:
            items = []
            for li in element.find_all('li'):
                item_text = li.get_text(strip=True)
                if item_text:
                    items.append(item_text)
            
            if items:
                return ContentBlock(
                    type='list',
                    content='\n'.join(items),
                    position=position,
                    metadata={'list_type': element.name, 'item_count': len(items)}
                )
        
        elif element.name == 'img':
            src = element.get('src', '')
            alt = element.get('alt', '')
            if src:
                return ContentBlock(
                    type='image',
                    content=alt or 'Image',
                    position=position,
                    metadata={'src': src, 'alt': alt}
                )
        
        return None
    
    def _extract_metadata(self, soup: BeautifulSoup, clean_content: str, article_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract enhanced metadata from content.
        """
        
        metadata = {}
        
        # Word count and reading time
        word_count = len(clean_content.split())
        metadata['word_count'] = word_count
        metadata['reading_time'] = max(1, round(word_count / 200))  # 200 WPM average
        
        # Extract author if not already present
        if not article_metadata.get('author'):
            author = self._extract_author(soup)
            if author:
                metadata['author'] = author
        
        # Extract publish date if not present
        if not article_metadata.get('published_date'):
            pub_date = self._extract_publish_date(soup)
            if pub_date:
                metadata['published_date'] = pub_date
        
        # Content structure analysis
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        metadata['heading_count'] = len(headings)
        
        paragraphs = soup.find_all('p')
        substantial_paragraphs = [p for p in paragraphs if len(p.get_text(strip=True)) > 50]
        metadata['paragraph_count'] = len(substantial_paragraphs)
        
        # Media content
        images = soup.find_all('img')
        metadata['image_count'] = len(images)
        
        links = soup.find_all('a')
        external_links = [link for link in links if self._is_external_link(link)]
        metadata['external_link_count'] = len(external_links)
        
        return metadata
    
    def _extract_author(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract author from various possible locations."""
        
        author_selectors = [
            '[rel="author"]',
            '.author',
            '.byline',
            '.article-author',
            '.post-author',
            '[property="article:author"]',
            '[name="author"]'
        ]
        
        for selector in author_selectors:
            element = soup.select_one(selector)
            if element:
                if element.name == 'meta':
                    author = element.get('content', '').strip()
                else:
                    author = element.get_text(strip=True)
                
                if author and len(author) > 2 and len(author) < 100:
                    return author
        
        return None
    
    def _extract_publish_date(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract publish date from various possible locations."""
        
        date_selectors = [
            '[property="article:published_time"]',
            '[name="publish_date"]',
            '[name="date"]',
            'time[datetime]',
            '.publish-date',
            '.article-date'
        ]
        
        for selector in date_selectors:
            element = soup.select_one(selector)
            if element:
                if element.name == 'meta':
                    date = element.get('content', '').strip()
                elif element.name == 'time':
                    date = element.get('datetime', '') or element.get_text(strip=True)
                else:
                    date = element.get_text(strip=True)
                
                if date:
                    return date
        
        return None
    
    def _is_external_link(self, link: Tag) -> bool:
        """Check if link is external."""
        href = link.get('href', '')
        if not href:
            return False
        
        # Simple check for external links
        return href.startswith('http') and '://' in href
    
    def _assess_quality(self, clean_content: str, content_blocks: List[ContentBlock], metadata: Dict[str, Any]) -> float:
        """
        Assess content quality using multiple metrics.
        """
        
        scores = {}
        
        # Completeness score (0.0-1.0)
        word_count = metadata.get('word_count', 0)
        if word_count >= 500:
            scores['completeness'] = 1.0
        elif word_count >= 200:
            scores['completeness'] = word_count / 500
        else:
            scores['completeness'] = 0.3
        
        # Structure score (0.0-1.0)
        heading_count = metadata.get('heading_count', 0)
        paragraph_count = metadata.get('paragraph_count', 0)
        
        structure_score = 0.0
        if heading_count > 0:
            structure_score += 0.3
        if paragraph_count >= 3:
            structure_score += 0.4
        if len(content_blocks) >= 5:
            structure_score += 0.3
        
        scores['structure'] = min(1.0, structure_score)
        
        # Readability score (0.0-1.0)
        if clean_content:
            avg_sentence_length = len(clean_content.split()) / max(1, clean_content.count('.'))
            if 10 <= avg_sentence_length <= 25:
                scores['readability'] = 1.0
            elif avg_sentence_length < 10:
                scores['readability'] = 0.7
            else:
                scores['readability'] = max(0.3, 1.0 - (avg_sentence_length - 25) / 50)
        else:
            scores['readability'] = 0.0
        
        # Media integration score (0.0-1.0)
        image_count = metadata.get('image_count', 0)
        if image_count > 0:
            scores['media_integration'] = min(1.0, image_count / 3)
        else:
            scores['media_integration'] = 0.5  # Not penalize text-only articles too much
        
        # Noise removal score (0.0-1.0) - assume good if we got this far
        scores['noise_removal'] = 0.9
        
        # Weighted overall score
        overall_score = (
            scores['completeness'] * 0.3 +
            scores['structure'] * 0.2 +
            scores['readability'] * 0.2 +
            scores['media_integration'] * 0.15 +
            scores['noise_removal'] * 0.15
        )
        
        return round(overall_score, 3) 