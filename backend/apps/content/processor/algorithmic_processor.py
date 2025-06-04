"""
Algorithmic Content Processor
Implementation based on WebKit's ReaderArticleFinder algorithm.
Provides Safari Reader Mode-like content extraction without LLM dependency.
"""

import re
import math
import logging
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass
from bs4 import BeautifulSoup, Tag, NavigableString, Comment
from urllib.parse import urljoin, urlparse, parse_qs
from difflib import SequenceMatcher
import html

from .models import ContentBlock, ProcessingResult

logger = logging.getLogger(__name__)


@dataclass
class CandidateElement:
    """Candidate element for main content with Safari-like scoring."""
    element: Tag
    raw_score: float = 0.0
    tag_score_multiplier: float = 1.0
    language_score_multiplier: float = 1.0
    final_score: float = 0.0
    score_density: float = 0.0
    text_nodes: List = None
    
    def __post_init__(self):
        if self.text_nodes is None:
            self.text_nodes = []


class AlgorithmicProcessor:
    """
    Algorithmic content processing using Safari Reader Mode algorithm.
    Based on WebKit's ReaderArticleFinder implementation with improvements.
    """
    
    # Safari Reader Mode constants (from WebKit source)
    MIN_SCORE_THRESHOLD = 1600  # Restored to original Safari value
    MIN_ADVANTAGE_GAP = 15
    MIN_SCORE_DENSITY = 4.25
    MIN_WIDTH = 280
    MIN_HEIGHT = 295
    MIN_AREA = 170000  # MIN_WIDTH * MIN_HEIGHT * some factor
    
    # Additional Safari constants
    MAX_TOP_POSITION = 1300  # CandidateMaximumTop
    MIN_WIDTH_PORTION_FOR_INDICATORS = 0.5  # CandidateMinimumWidthPortionForIndicatorElements
    MIN_LIST_ITEM_LINE_COUNT = 4  # CandidateMinumumListItemLineCount
    
    # Text node scoring
    TEXT_NODE_LENGTH_POWER = 1.25
    MIN_TEXT_NODE_LENGTH = 20
    
    # Element scoring bonuses/penalties
    ARTICLE_MATCH_BONUS = 0.5
    COMMENT_MATCH_PENALTY = 0.75
    
    # Language multipliers
    CJK_SCORE_MULTIPLIER = 3.0
    MIN_CJK_RATIO = 0.5
    
    # Link density thresholds
    MAX_LINK_DENSITY = 0.33
    HIGH_LINK_DENSITY = 0.5
    
    # Media content constants
    MIN_CONTENT_MEDIA_HEIGHT = 150
    MIN_CONTENT_MEDIA_WIDTH_RATIO = 0.25
    MAX_CONTENT_MEDIA_AREA_RATIO = 0.2
    
    # Content patterns (from WebKit - enhanced)
    POSITIVE_PATTERNS = re.compile(
        r'(?:(?:^|\s)(?:(post|hentry|entry)[-_]?(?:content|text|body)?|'
        r'article[-_]?(?:content|text|body|page)?)(?:\s|$))', 
        re.IGNORECASE
    )
    
    NEGATIVE_PATTERNS = re.compile(
        r'advertisement|breadcrumb|combx|comment|contact|disqus|footer|link|meta|'
        r'mod-conversations|promo|related|scroll|share|shoutbox|sidebar|social|'
        r'sponsor|subscribe|tags|toolbox|widget|_ad$|navigation|nav-|menu-', 
        re.IGNORECASE
    )
    
    VERY_POSITIVE_PATTERNS = re.compile(r'instapaper_body', re.IGNORECASE)
    VERY_NEGATIVE_PATTERNS = re.compile(r'instapaper_ignore', re.IGNORECASE)
    
    # Elements to ignore for candidates
    IGNORE_TAGS = {
        'A', 'EMBED', 'FORM', 'HTML', 'IFRAME', 'OBJECT', 'OL', 'OPTION',
        'SCRIPT', 'STYLE', 'SVG', 'UL'
    }
    
    # Elements to remove during cleaning
    REMOVE_TAGS = {
        'SCRIPT', 'STYLE', 'LINK', 'FORM', 'NOSCRIPT'
    }
    
    def __init__(self):
        self.candidates = []
        self.best_candidate = None
    
    def process_content(self, raw_html: str, article_metadata: Dict[str, Any]) -> ProcessingResult:
        """
        Main processing pipeline implementing Safari Reader Mode algorithm.
        Enhanced with better error handling and validation.
        """
        
        import time
        start_time = time.time()
        
        try:
            # Validate inputs
            if not raw_html or not isinstance(raw_html, str):
                return ProcessingResult(
                    success=False,
                    error_message="Invalid HTML input",
                    processing_time_ms=int((time.time() - start_time) * 1000)
                )
            
            # Store raw HTML for quality assessment access
            self._current_raw_html = raw_html
            
            # Store article metadata for title comparison
            self._current_article_metadata = article_metadata or {}
            
            # Initialize author information storage
            self._extracted_author_info = []
            
            # Clear section delimiter cache for fresh detection
            self._section_delimiters_cache = None
            
            if len(raw_html.strip()) < 100:
                return ProcessingResult(
                    success=False,
                    error_message="HTML content too short for processing",
                    processing_time_ms=int((time.time() - start_time) * 1000)
                )
            
            # Parse HTML with error handling
            try:
                # Enhanced: Decode HTML entities before parsing to handle encoded Twitter embeds
                # The Verge (and other sites) sometimes double-encode Twitter content
                
                # First, try to decode HTML entities that might be present
                decoded_html = html.unescape(raw_html)
                
                # Also handle Unicode escape sequences that are common in JSON-embedded HTML
                # Replace common Unicode escapes
                decoded_html = decoded_html.replace('\\u003c', '<')
                decoded_html = decoded_html.replace('\\u003e', '>')
                decoded_html = decoded_html.replace('\\u0026', '&')
                decoded_html = decoded_html.replace('\\"', '"')
                decoded_html = decoded_html.replace('\\/', '/')
                
                # Parse the decoded HTML
                soup = BeautifulSoup(decoded_html, 'html.parser')
                if not soup or not soup.find():
                    # Fallback to original HTML if decoding caused issues
                    logger.warning("Decoded HTML parsing failed, falling back to original")
                    soup = BeautifulSoup(raw_html, 'html.parser')
                    if not soup or not soup.find():
                        return ProcessingResult(
                            success=False,
                            error_message="Failed to parse HTML content",
                            processing_time_ms=int((time.time() - start_time) * 1000)
                        )
                else:
                    logger.info("Successfully decoded and parsed HTML with entity decoding")
                
                # Store soup reference for section delimiter detection
                self._current_soup = soup
                
            except Exception as e:
                return ProcessingResult(
                    success=False,
                    error_message=f"HTML parsing error: {str(e)}",
                    processing_time_ms=int((time.time() - start_time) * 1000)
                )
            
            # 1. Find candidate elements using Safari algorithm
            candidates = self._find_candidate_elements(soup)
            
            if not candidates:
                return ProcessingResult(
                    success=False,
                    error_message="No viable candidate elements found",
                    processing_time_ms=int((time.time() - start_time) * 1000)
                )
            
            # 2. Score candidates using Safari's scoring system
            scored_candidates = self._score_candidates(candidates, soup)
            
            # 3. Select best candidate using advantage gap analysis
            best_candidate = self._select_best_candidate(scored_candidates)
            
            if not best_candidate:
                return ProcessingResult(
                    success=False,
                    error_message="No candidate met minimum score requirements",
                    processing_time_ms=int((time.time() - start_time) * 1000)
                )
            
            # 4. Find prepended/appended content (Safari's approach)
            try:
                prepended_elements, appended_elements = self._find_prepended_appended_content(best_candidate.element)
            except Exception as e:
                logger.warning(f"Error finding prepended/appended content: {e}")
                prepended_elements, appended_elements = [], []
            
            # 5. Clean and format content (including prepended/appended)
            try:
                clean_content = self._clean_and_format_content_with_siblings(
                    best_candidate.element, prepended_elements, appended_elements, soup
                )
                
                # If content is too short, try alternative extraction methods
                if not clean_content or len(clean_content.strip()) < 100:
                    logger.warning("Primary content extraction produced insufficient content, trying fallbacks")
                    clean_content = self._extract_content_with_fallbacks(best_candidate.element, soup)
                    
            except Exception as e:
                logger.warning(f"Error cleaning content: {e}")
                # Fallback to basic cleaning
                clean_content = self._extract_content_with_fallbacks(best_candidate.element, soup)
            
            # 6. Structure content into blocks
            try:
                content_blocks = self._structure_content_blocks_with_siblings(
                    best_candidate.element, prepended_elements, appended_elements
                )
            except Exception as e:
                logger.warning(f"Error structuring content blocks: {e}")
                # Fallback to basic structure
                content_blocks = self._structure_content_blocks(best_candidate.element)
            
            # 7. Extract enhanced metadata (including visual title)
            try:
                extracted_metadata = self._extract_metadata(soup, clean_content, article_metadata or {})
                
                # Add visual title extraction
                visual_title = self._extract_visual_title(soup)
                if visual_title:
                    extracted_metadata['visual_title'] = visual_title
                    # Store for title duplication prevention
                    self._current_visual_title = visual_title
            except Exception as e:
                logger.warning(f"Error extracting metadata: {e}")
                extracted_metadata = {'error': 'Metadata extraction failed'}
            
            # 8. Assess quality
            try:
                quality_score = self._assess_quality(best_candidate, clean_content, content_blocks, extracted_metadata)
            except Exception as e:
                logger.warning(f"Error assessing quality: {e}")
                quality_score = 0.5  # Default moderate quality
            
            processing_time = int((time.time() - start_time) * 1000)
            
            # Final validation
            if not clean_content or len(clean_content.strip()) < 30:
                return ProcessingResult(
                    success=False,
                    error_message="Extracted content too short or empty",
                    processing_time_ms=processing_time
                )
            
            return ProcessingResult(
                success=True,
                clean_content=clean_content,
                content_blocks=content_blocks or [],
                extracted_metadata=extracted_metadata or {},
                quality_score=quality_score,
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            logger.exception(f"Algorithmic processing failed: {str(e)}")
            return ProcessingResult(
                success=False,
                error_message=str(e),
                processing_time_ms=int((time.time() - start_time) * 1000)
            )
    
    def _find_candidate_elements(self, soup: BeautifulSoup) -> List[Tag]:
        """
        Find candidate elements that could contain the main content.
        Uses Safari's candidate selection criteria.
        """
        
        candidates = []
        
        # Find all potential content containers
        all_elements = soup.find_all()
        
        for element in all_elements:
            if not isinstance(element, Tag):
                continue
                
            # Skip ignored tags
            if element.name.upper() in self.IGNORE_TAGS:
                continue
            
            # Check if element is viable candidate
            if self._is_viable_candidate(element):
                candidates.append(element)
        
        logger.info(f"Found {len(candidates)} candidate elements")
        return candidates
    
    def _is_viable_candidate(self, element: Tag) -> bool:
        """
        Check if element meets Safari's viability criteria.
        Uses Safari's candidateIfElementIsViable logic.
        """
        
        # Must have some text content
        text_content = element.get_text(strip=True)
        if not text_content or len(text_content) < 100:
            return False
        
        # Check for very negative patterns first
        class_id = f"{' '.join(element.get('class', []))} {element.get('id', '')}".lower()
        if self.VERY_NEGATIVE_PATTERNS.search(class_id):
            return False
        
        # Estimate element dimensions (Safari uses actual bounding rects)
        estimated_width = max(self.MIN_WIDTH, len(text_content) / 10)
        estimated_height = max(self.MIN_HEIGHT, len(text_content) / 20)
        
        # Safari's dimension checks
        if estimated_width < self.MIN_WIDTH or estimated_height < self.MIN_HEIGHT:
            return False
        
        if estimated_width * estimated_height < self.MIN_AREA:
            return False
        
        # Safari's top position check (simplified - we don't have actual position)
        # Skip this check for now as we don't have layout information
        
        # Safari's adjusted height check
        adjusted_height = self._calculate_candidate_adjusted_height(element)
        if adjusted_height < self.MIN_HEIGHT:
            return False
        
        # Element should have reasonable structure for content
        if element.name.upper() in ['DIV', 'ARTICLE', 'SECTION', 'MAIN', 'P', 'TD']:
            return True
        
        # Check for very positive patterns
        if self.VERY_POSITIVE_PATTERNS.search(class_id):
            return True
        
        return False
    
    def _score_candidates(self, candidates: List[Tag], soup: BeautifulSoup) -> List[CandidateElement]:
        """
        Score candidates using Safari's algorithm.
        """
        
        scored_candidates = []
        
        for element in candidates:
            candidate = CandidateElement(element=element)
            
            # 1. Find and score text nodes (Safari's core algorithm)
            candidate.text_nodes = self._find_usable_text_nodes(element)
            candidate.raw_score = self._calculate_raw_score(candidate.text_nodes)
            
            # 2. Calculate tag and attribute score multiplier
            candidate.tag_score_multiplier = self._calculate_tag_score_multiplier(element)
            
            # 3. Calculate language score multiplier
            candidate.language_score_multiplier = self._calculate_language_multiplier(candidate.text_nodes)
            
            # 4. Calculate final score
            candidate.final_score = (
                candidate.raw_score * 
                candidate.tag_score_multiplier * 
                candidate.language_score_multiplier
            )
            
            # 5. Calculate score density (Safari's key metric)
            candidate.score_density = self._calculate_score_density(candidate, element)
            
            # Only keep candidates that meet minimum requirements
            if candidate.final_score >= self.MIN_SCORE_THRESHOLD:
                scored_candidates.append(candidate)
        
        # Sort by final score
        scored_candidates.sort(key=lambda x: x.final_score, reverse=True)
        
        logger.info(f"Scored {len(scored_candidates)} viable candidates")
        return scored_candidates
    
    def _find_usable_text_nodes(self, element: Tag) -> List[str]:
        """
        Find usable text nodes within element using Safari's XPath-like approach.
        Simplified to be less aggressive with filtering.
        """
        
        text_nodes = []
        
        # Safari's excluded parent tags (reduced set)
        excluded_parent_tags = {
            'SCRIPT', 'STYLE', 'NOSCRIPT'
        }
        
        def collect_text_nodes(elem, depth=0):
            """Collect text nodes with simplified filtering."""
            if depth > 8:  # Prevent infinite recursion
                return
                
            try:
                for child in elem.descendants:
                    if isinstance(child, NavigableString) and not isinstance(child, Comment):
                        text = str(child).strip()
                        if not text or len(text) < self.MIN_TEXT_NODE_LENGTH:
                            continue
                            
                        parent = child.parent
                        if not parent:
                            continue
                            
                        # Skip only the most obvious non-content parents
                        if parent.name.upper() in excluded_parent_tags:
                            continue
                            
                        # Check for very obvious negative patterns in immediate parent only
                        parent_class_id = f"{' '.join(parent.get('class', []))} {parent.get('id', '')}".lower()
                        if any(pattern in parent_class_id for pattern in ['script', 'style', 'advertisement', 'ad-']):
                            continue
                        
                        # Accept the text node
                        text_nodes.append(text)
                        
                        # Limit for performance
                        if len(text_nodes) > 500:
                            break
                            
            except Exception as e:
                logger.warning(f"Error collecting text nodes: {e}")
        
        collect_text_nodes(element)
        
        return text_nodes
    
    def _find_children_with_parallel_structure(self, element: Tag) -> List[Tag]:
        """
        Find children with parallel structure (Safari's childrenWithParallelStructure).
        Identifies elements with similar class patterns.
        """
        
        children = element.find_all(recursive=False)
        if not children:
            return []
        
        class_groups = {}
        
        for child in children:
            if child.name.upper() in self.IGNORE_TAGS:
                continue
                
            if not child.get('class'):
                continue
                
            classes = child.get('class', [])
            for class_name in classes:
                if class_name not in class_groups:
                    class_groups[class_name] = []
                class_groups[class_name].append(child)
        
        # Return the largest group that represents more than half the children
        min_threshold = len(children) // 2
        
        for class_name, elements in class_groups.items():
            if len(elements) > min_threshold:
                return elements
        
        return []
    
    def _calculate_raw_score(self, text_nodes: List[str]) -> float:
        """
        Calculate raw score using Safari's text node scoring.
        """
        
        total_score = 0.0
        
        for text in text_nodes:
            # Safari uses len^1.25 for each text node
            node_score = len(text) ** self.TEXT_NODE_LENGTH_POWER
            total_score += node_score
        
        return total_score
    
    def _calculate_tag_score_multiplier(self, element: Tag) -> float:
        """
        Calculate tag and attribute score multiplier (Safari's approach).
        """
        
        multiplier = 1.0
        
        # Check element and all ancestors
        current = element
        while current and isinstance(current, Tag):
            # Check ID attribute
            element_id = current.get('id', '')
            if element_id:
                if self.POSITIVE_PATTERNS.search(element_id):
                    multiplier += self.ARTICLE_MATCH_BONUS
                if self.NEGATIVE_PATTERNS.search(element_id):
                    multiplier -= self.COMMENT_MATCH_PENALTY
            
            # Check class attribute
            element_class = ' '.join(current.get('class', []))
            if element_class:
                if self.POSITIVE_PATTERNS.search(element_class):
                    multiplier += self.ARTICLE_MATCH_BONUS
                if self.NEGATIVE_PATTERNS.search(element_class):
                    multiplier -= self.COMMENT_MATCH_PENALTY
                    
            # Enhanced: Give bonus for semantic content elements
            if self._is_content_related_element(current):
                multiplier += self.ARTICLE_MATCH_BONUS * 1.5
                
            # Enhanced: Heavy penalty for navigation elements
            if current.name in ['nav', 'aside', 'header', 'footer']:
                multiplier -= self.COMMENT_MATCH_PENALTY
                
            # Safari's article tag bonus
            if current.name == 'ARTICLE':
                multiplier += self.ARTICLE_MATCH_BONUS
            
            current = current.parent
        
        return max(0.1, multiplier)  # Ensure minimum positive multiplier
    
    def _calculate_language_multiplier(self, text_nodes: List[str]) -> float:
        """
        Calculate language score multiplier for CJK languages (Safari feature).
        Enhanced based on Ctrl.blog research on internationalization issues.
        """
        
        if not text_nodes:
            return 1.0
        
        # Sample first few text nodes for language detection
        sample_nodes = text_nodes[:3]
        total_chars = 0
        cjk_chars = 0
        
        # Enhanced comma detection for different languages (from Ctrl.blog research)
        comma_variants = 0
        comma_patterns = [
            ',',    # Most European (U+2C)
            '،',    # Arabic (U+60C)
            '、',   # Chinese and Japanese (U+3001)
            '，',   # Full-width comma (U+FF0C)
        ]
        
        for text in sample_nodes:
            sample_text = text[:120]  # First 120 chars
            for char in sample_text:
                total_chars += 1
                if self._is_cjk_character(char):
                    cjk_chars += 1
                
                # Count comma variants for language detection
                if char in comma_patterns:
                    comma_variants += 1
        
        if total_chars == 0:
            return 1.0
        
        cjk_ratio = cjk_chars / total_chars
        
        # Enhanced CJK detection based on research
        if cjk_ratio >= self.MIN_CJK_RATIO:
            # Additional boost for high CJK content (Maxthon approach)
            if cjk_ratio >= 0.8:
                return self.CJK_SCORE_MULTIPLIER * 1.2  # Extra boost for pure CJK
            return self.CJK_SCORE_MULTIPLIER
        
        # Moderate boost for mixed content with CJK elements
        if cjk_ratio >= 0.2:
            return 1.5
        
        return 1.0
    
    def _is_cjk_character(self, char: str) -> bool:
        """
        Check if character is CJK (Chinese, Japanese, Korean).
        Based on Safari's character ranges.
        """
        
        code = ord(char)
        
        # Safari's CJK ranges
        cjk_ranges = [
            (0x2E80, 0x2EFF),   # CJK Radicals Supplement
            (0x3040, 0x309F),   # Hiragana
            (0x30A0, 0x30FF),   # Katakana
            (0x3100, 0x312F),   # Bopomofo
            (0x3200, 0x32FF),   # Enclosed CJK Letters and Months
            (0x3400, 0x4DBF),   # CJK Extension A
            (0x4E00, 0x9FFF),   # CJK Unified Ideographs
            (0xAC00, 0xD7AF),   # Hangul Syllables
            (0xF900, 0xFAFF),   # CJK Compatibility Ideographs
            (0x20000, 0x2A6DF), # CJK Extension B
            (0x2F800, 0x2FA1F)  # CJK Compatibility Supplement
        ]
        
        for start, end in cjk_ranges:
            if start <= code <= end:
                return True
        
        return False
    
    def _calculate_score_density(self, candidate: CandidateElement, element: Tag) -> float:
        """
        Calculate score density using Safari's sophisticated algorithm.
        Formula: score / effectiveArea * 1000 * (avgFontSize / baseFontSize) * languageMultiplier
        """
        
        # Start with element area estimation
        estimated_area = max(self.MIN_AREA, len(element.get_text(strip=True)) * 10)
        excluded_area = 0
        
        # 1. Exclude comment blocks and specific selectors (Safari's DensityExcludedElementSelector)
        # "#disqus_thread, #comments, .userComments"
        excluded_selectors = [
            '#disqus_thread', '#comments', '.userComments'
        ]
        
        for selector in excluded_selectors:
            try:
                excluded_elements = element.select(selector)
                for excluded in excluded_elements:
                    # Estimate excluded area
                    excluded_text = excluded.get_text(strip=True)
                    excluded_area += len(excluded_text) * 10
            except Exception:
                continue
        
        # 2. Exclude comment blocks by class/id patterns
        for child in element.find_all():
            if isinstance(child, Tag):
                class_id = f"{' '.join(child.get('class', []))} {child.get('id', '')}".lower()
                if 'comment' in class_id:
                    comment_text = child.get_text(strip=True)
                    excluded_area += len(comment_text) * 10
        
        # 3. Account for media content area ratios (Safari's logic)
        total_element_area = estimated_area
        max_media_area = total_element_area * 0.2  # MaximumContentMediaAreaToArticleAreaRatio = 0.2
        min_media_width_ratio = 0.25  # MinimumContentMediaWidthToArticleWidthRatio = 0.25
        min_media_height = 150  # MinimumContentMediaHeight = 150
        
        estimated_element_width = math.sqrt(estimated_area * 1.5)  # Rough width estimation
        min_media_width = estimated_element_width * min_media_width_ratio
        
        media_elements = element.find_all(['img', 'object', 'video'])
        for media in media_elements:
            # Estimate media dimensions (Safari uses actual bounding rects)
            media_text = media.get('alt', '') or media.get('title', '') or 'media'
            estimated_media_width = max(min_media_width, len(media_text) * 8)
            estimated_media_height = max(min_media_height, 200)
            
            if estimated_media_width >= min_media_width and estimated_media_height > min_media_height:
                media_area = estimated_media_width * estimated_media_height
                if media_area < max_media_area:
                    excluded_area += media_area
        
        # 4. Calculate effective area
        effective_area = max(1, total_element_area - excluded_area)
        
        # 5. Calculate average font size from text nodes (Safari's approach)
        total_font_size = 0
        font_size_count = 0
        base_font_size = 16  # Safari's BaseFontSize = 16
        
        for text_node in candidate.text_nodes:
            # Simplified font size calculation (Safari uses actual computed styles)
            # Assume standard font size for now
            total_font_size += base_font_size
            font_size_count += 1
        
        avg_font_size = base_font_size
        if font_size_count > 0:
            avg_font_size = total_font_size / font_size_count
        
        font_size_multiplier = avg_font_size / base_font_size
        
        # 6. Calculate final density using Safari's formula
        # density = basicScore / effectiveArea * 1000 * fontSizeMultiplier * languageMultiplier
        basic_score = candidate.raw_score * candidate.tag_score_multiplier
        
        density = (basic_score / effective_area * 1000 * 
                  font_size_multiplier * 
                  candidate.language_score_multiplier)
        
        logger.debug(f"Score density calculation: score={basic_score}, area={effective_area}, "
                    f"font_mult={font_size_multiplier}, lang_mult={candidate.language_score_multiplier}, "
                    f"density={density}")
        
        return density
    
    def _select_best_candidate(self, candidates: List[CandidateElement]) -> Optional[CandidateElement]:
        """
        Select best candidate using Safari's advantage gap analysis and disqualification rules.
        """
        
        if not candidates:
            return None
        
        # Sort by final score
        candidates.sort(key=lambda x: x.final_score, reverse=True)
        
        # Apply Safari's disqualification rules to each candidate
        qualified_candidates = []
        
        for candidate in candidates:
            # Check minimum score threshold
            if candidate.final_score < self.MIN_SCORE_THRESHOLD:
                logger.debug(f"Candidate disqualified: score {candidate.final_score} below threshold {self.MIN_SCORE_THRESHOLD}")
                continue
            
            # Check score density
            if candidate.score_density < self.MIN_SCORE_DENSITY:
                logger.debug(f"Candidate disqualified: density {candidate.score_density} below minimum {self.MIN_SCORE_DENSITY}")
                continue
            
            # Safari's disqualification methods
            if self._should_disqualify_due_to_horizontal_rule_density(candidate):
                continue
            
            if self._should_disqualify_due_to_header_density(candidate):
                continue
            
            if self._should_disqualify_due_to_similar_elements(candidate, candidates):
                continue
            
            if self._should_disqualify_for_deep_linking(candidate):
                continue
            
            # Candidate passed all disqualification tests
            qualified_candidates.append(candidate)
        
        if not qualified_candidates:
            logger.warning("No candidates passed disqualification tests")
            # Fall back to best scoring candidate if none qualify (Safari's approach)
            if candidates:
                best = candidates[0]
                # If we have very few candidates, be more lenient with score threshold
                if len(candidates) <= 3 and best.final_score >= self.MIN_SCORE_THRESHOLD * 0.4:
                    logger.warning(f"Using best candidate with relaxed threshold: score={best.final_score}")
                    return best
                elif len(candidates) <= 5 and best.final_score >= self.MIN_SCORE_THRESHOLD * 0.6:
                    logger.warning(f"Using best candidate with relaxed threshold: score={best.final_score}")
                    return best
                elif best.final_score >= self.MIN_SCORE_THRESHOLD * 0.75:
                    logger.warning(f"Using best candidate despite disqualification: score={best.final_score}")
                    return best
            return None
        
        # Select best qualified candidate
        best = qualified_candidates[0]
        
        # Check advantage gap (Safari requires 15 point advantage)
        if len(qualified_candidates) > 1:
            second_best = qualified_candidates[1]
            advantage_gap = best.final_score - second_best.final_score
            
            if advantage_gap < self.MIN_ADVANTAGE_GAP:
                logger.warning(f"Advantage gap {advantage_gap} below minimum {self.MIN_ADVANTAGE_GAP}")
                # Still use the best candidate but log the warning
        
        logger.info(f"Selected candidate with score {best.final_score}, density {best.score_density}")
        return best
    
    def _clean_and_format_content(self, main_element: Tag, soup: BeautifulSoup) -> str:
        """
        Clean content using Safari's cleaning algorithm.
        """
        
        # Create a copy to avoid modifying original
        cleaned_element = BeautifulSoup(str(main_element), 'html.parser')
        
        # Remove unwanted elements (Safari's approach)
        self._remove_unwanted_elements(cleaned_element)
        
        # Clean attributes
        self._clean_attributes(cleaned_element)
        
        # Remove elements that should be pruned
        self._prune_elements(cleaned_element)
        
        # Convert to clean text with preserved structure
        return self._element_to_clean_text(cleaned_element)
    
    def _remove_unwanted_elements(self, element: Tag):
        """
        Remove unwanted elements (Safari's cleaning).
        """
        
        # Remove script, style, etc.
        for tag_name in self.REMOVE_TAGS:
            for tag in element.find_all(tag_name):
                tag.decompose()
        
        # Remove elements with very negative patterns
        for elem in element.find_all():
            if isinstance(elem, Tag):
                class_id = f"{' '.join(elem.get('class', []))} {elem.get('id', '')}".lower()
                if self.VERY_NEGATIVE_PATTERNS.search(class_id):
                    elem.decompose()
    
    def _clean_attributes(self, element: Tag):
        """
        Clean attributes keeping only essential ones (Safari approach).
        """
        
        for elem in element.find_all():
            if isinstance(elem, Tag):
                # Keep only essential attributes
                essential_attrs = {}
                
                if elem.name == 'a' and 'href' in elem.attrs:
                    essential_attrs['href'] = elem.attrs['href']
                
                if elem.name == 'img':
                    if 'src' in elem.attrs:
                        essential_attrs['src'] = elem.attrs['src']
                    if 'alt' in elem.attrs:
                        essential_attrs['alt'] = elem.attrs['alt']
                
                elem.attrs = essential_attrs
    
    def _prune_elements(self, element: Tag):
        """
        Prune elements that should be removed (Safari's pruning logic).
        """
        
        elements_to_remove = []
        
        for elem in element.find_all():
            if isinstance(elem, Tag) and self._should_prune_element(elem):
                elements_to_remove.append(elem)
        
        for elem in elements_to_remove:
            if elem.parent:
                elem.decompose()
    
    def _should_prune_element(self, element: Tag) -> bool:
        """
        Determine if element should be pruned (Safari's logic).
        """
        
        # Check link density
        text_length = len(element.get_text(strip=True))
        if text_length == 0:
            return True
        
        links = element.find_all('a')
        link_text_length = sum(len(link.get_text(strip=True)) for link in links)
        
        if text_length > 0:
            link_density = link_text_length / text_length
            if link_density > self.HIGH_LINK_DENSITY:
                return True
        
        # Check for comment blocks
        class_id = f"{' '.join(element.get('class', []))} {element.get('id', '')}".lower()
        if 'comment' in class_id:
            return True
        
        # Check for very short content
        if text_length < 25 and element.name not in ['img', 'video', 'audio']:
            return True
        
        return False
    
    def _element_to_clean_text(self, element: Tag) -> str:
        """
        Convert element to clean text with preserved formatting.
        """
        
        result = []
        
        for child in element.descendants:
            if isinstance(child, NavigableString) and not isinstance(child, Comment):
                text = str(child).strip()
                if text:
                    # Add appropriate spacing based on parent element
                    parent = child.parent
                    if parent:
                        if parent.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                            result.append(f"\n\n## {text}\n")
                        elif parent.name == 'p':
                            result.append(f"\n{text}\n")
                        elif parent.name == 'blockquote':
                            result.append(f"\n> {text}\n")
                        elif parent.name == 'li':
                            result.append(f"• {text}\n")
                        else:
                            result.append(text)
        
        return ' '.join(result)
    
    def _structure_content_blocks(self, main_element: Tag) -> List[ContentBlock]:
        """
        Convert the main content element into structured blocks.
        Enhanced with section-level filtering to exclude recommendation widgets.
        """
        blocks = []
        position = 0
        
        # Track seen content to avoid duplicates
        seen_content = set()
        seen_images = set()
        
        # Back to original element types - removing 'div' to prevent duplicates
        content_element_types = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'blockquote', 'ul', 'ol', 'img', 'video', 'figure']
        
        # Process elements in order, but exclude recommendation/widget sections
        for element in main_element.find_all(content_element_types):
            
            # Skip if this element or its parents should be excluded
            if self._should_skip_element_for_content_blocks(element):
                continue
            
            # Only process content-relevant elements
            if element.name in content_element_types:
                block = self._element_to_content_block(element, position)
                if block and self._is_unique_content_block(block, seen_content, seen_images):
                    blocks.append(block)
                    position += 1
        
        return blocks
    
    def _should_skip_element_for_content_blocks(self, element: Tag) -> bool:
        """
        Determine if an element should be skipped when creating content blocks.
        Enhanced with Safari-like section filtering that stops processing after
        encountering section delimiters like "Related Content", "Latest News", etc.
        """
        
        # Check the element itself
        if self._should_exclude_section(element):
            return True
        
        # Enhanced: Check if this element IS a section delimiter heading
        if self._is_section_delimiter(element):
            return True
        
        # Enhanced: Check if this element comes after a section delimiter
        if self._is_after_section_delimiter(element):
            return True
        
        # Check all ancestors up to reasonable depth to catch elements within excluded sections
        current = element.parent
        depth = 0
        max_depth = 10  # Go deeper to catch elements within excluded sections
        
        while current and current.name not in ['body', 'html'] and depth < max_depth:
            if self._should_exclude_section(current):
                return True
                
            # Check if ancestor comes after section delimiter
            if self._is_after_section_delimiter(current):
                return True
                
            current = current.parent
            depth += 1
        
        return False
    
    def _element_to_content_block(self, element: Tag, position: int) -> Optional[ContentBlock]:
        """
        Convert an element to a content block.
        Returns None if the element should be excluded or cannot be processed.
        """
        
        # First check: should this element be skipped due to section-level filtering?
        if self._should_skip_element_for_content_blocks(element):
            return None

        block_type = element.name.lower()
        content = ""
        level = None
        block_id = element.get('id')
        classes = element.get('class', [])
        metadata = {}
        
        # Enhanced: Check for byline/author elements first (highest priority)
        if self._is_byline_element(element):
            # Extract byline information for metadata but don't create a content block
            # The frontend can use this information in the page header instead of duplicating it in the body
            author_info = self._extract_author_from_byline(element)
            
            # Store the author information in the article metadata if we have a reference
            if hasattr(self, '_extracted_author_info'):
                if not self._extracted_author_info:
                    self._extracted_author_info = []
                self._extracted_author_info.append(author_info)
            else:
                self._extracted_author_info = [author_info]
            
            # Don't create a content block for bylines - they should appear in page header
            return None
        
        # Handle different element types
        elif block_type in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            block_type = 'heading'
            level = int(element.name[1])  # Extract number from h1, h2, etc.
            content = element.get_text(strip=True)
            
            # Check for title duplication - skip if heading matches article title
            if hasattr(self, '_current_article_metadata') and self._current_article_metadata:
                article_title = self._current_article_metadata.get('title', '')
                if article_title and self._is_duplicate_title(content, article_title):
                    # Skip this heading as it duplicates the article title
                    return None
            
            # Check if this should be a title instead of regular heading
            if position == 0 or level == 1:
                # Check if this heading matches or is very similar to article title
                def clean_title_for_comparison(title):
                    """Clean title for comparison by removing publication names."""
                    import re
                    # Remove common publication name patterns
                    title = re.sub(r'\s*[-|–—]\s*.+(?:Post|Times|News|CNN|BBC|Reuters|AP|NPR|Fox|NBC|CBS|ABC).*$', '', title, flags=re.IGNORECASE)
                    return title.strip()
                
                # For now, we'll treat h1 as regular heading since we don't have article title here
                # This logic could be enhanced by passing article metadata to this method
        
        elif block_type == 'p':
            # Enhanced debug logging for paragraphs containing "by"
            p_text = element.get_text(strip=True)
            if 'by ' in p_text.lower() and len(p_text) < 100:
                logger.info(f"PROCESSING PARAGRAPH: '{p_text}' - checking if byline...")
            
            # Enhanced: Check if this paragraph is inside a pullquote container
            if self._is_pullquote_paragraph(element):
                block_type = 'pullquote'
                content, links_metadata = self._extract_paragraph_with_links(element)
                # Store links metadata for frontend processing
                if links_metadata:
                    metadata['links'] = links_metadata
            
            # Enhanced: Check for Twitter embeds first (some sites render Twitter content as paragraphs)
            elif self._is_twitter_embed(element):
                block_type = 'twitter_embed'
                twitter_data = self._extract_twitter_embed_data(element)
                
                if twitter_data['tweet_id']:
                    metadata.update(twitter_data)
                    content = f"Twitter embed: {twitter_data['tweet_id']}"
                else:
                    # Fallback to regular paragraph processing
                    if self._is_subtitle_paragraph(element, position):
                        block_type = 'subtitle'
                    else:
                        block_type = 'paragraph'
                    content, links_metadata = self._extract_paragraph_with_links(element)
                    # Store links metadata for frontend processing
                    if links_metadata:
                        metadata['links'] = links_metadata
            else:
                # Check if this paragraph should be treated as a subtitle
                if self._is_subtitle_paragraph(element, position):
                    block_type = 'subtitle'
                else:
                    block_type = 'paragraph'
                content, links_metadata = self._extract_paragraph_with_links(element)
                # Store links metadata for frontend processing
                if links_metadata:
                    metadata['links'] = links_metadata
        
        elif block_type == 'blockquote':
            # Enhanced: Check for Twitter embeds first (Twitter often uses blockquote with twitter-tweet class)
            if self._is_twitter_embed(element):
                block_type = 'twitter_embed'
                twitter_data = self._extract_twitter_embed_data(element)
                
                if twitter_data['tweet_id']:
                    metadata.update(twitter_data)
                    content = f"Twitter embed: {twitter_data['tweet_id']}"
                else:
                    # Fallback to regular blockquote processing
                    block_type = 'quote'
                    content = element.get_text(strip=True)
                    # Look for citation
                    cite_elem = element.find('cite')
                    if cite_elem:
                        metadata['cite'] = cite_elem.get_text(strip=True)
            else:
                block_type = 'quote'
                content = element.get_text(strip=True)
                # Look for citation
                cite_elem = element.find('cite')
                if cite_elem:
                    metadata['cite'] = cite_elem.get_text(strip=True)
        
        elif block_type in ['ul', 'ol']:
            block_type = 'list'
            metadata['listType'] = block_type
            items = []
            for li in element.find_all('li', recursive=False):
                items.append(li.get_text(strip=True))
            metadata['items'] = items
            content = f"{len(items)} items"
            
        elif block_type == 'img':
            # Additional check: is this a content image?
            if not self._is_content_image(element):
                return None
                
            block_type = 'img'
            metadata['src'] = self._extract_image_url(element)
            metadata['alt'] = element.get('alt', '')  # Keep for accessibility
            
            # Enhanced: Only use meaningful captions, reject filenames
            potential_caption = element.get('title') or element.get('alt', '')
            if potential_caption and self._is_meaningful_caption(potential_caption):
                metadata['caption'] = potential_caption
                content = potential_caption
            else:
                metadata['caption'] = ''  # Empty caption instead of filename
                content = ''  # No caption content - frontend can handle this
            
        elif block_type == 'figure':
            block_type = 'figure' 
            # Extract image and caption from figure
            img = element.find('img')
            if img and self._is_content_image(img):
                metadata['src'] = self._extract_image_url(img)
                metadata['alt'] = img.get('alt', '')  # Keep for accessibility
                
                # Enhanced: Safari-like visible caption extraction with meaningful caption filtering
                visible_caption = self._extract_visible_figure_caption(element)
                if visible_caption:
                    metadata['caption'] = visible_caption
                    content = visible_caption
                else:
                    # Fallback to basic caption extraction with meaningful filtering
                    figcaption = element.find('figcaption')
                    if figcaption:
                        caption_text = figcaption.get_text(strip=True)
                        if caption_text and self._is_meaningful_caption(caption_text):
                            metadata['caption'] = caption_text
                            content = caption_text
                        else:
                            # No meaningful caption found
                            metadata['caption'] = ''
                            content = ''  # No caption content
                    else:
                        # Try alt text only if meaningful
                        raw_alt = img.get('alt', '')
                        if raw_alt and self._is_meaningful_caption(raw_alt):
                            metadata['caption'] = raw_alt
                            content = raw_alt
                        else:
                            # No meaningful caption found
                            metadata['caption'] = ''
                            content = ''  # No caption content
            else:
                return None  # Figure without valid image
                
        elif block_type == 'video':
            block_type = 'video'
            metadata['src'] = element.get('src')
            content = "Video content"
            
        else:
            # Enhanced: Check for Twitter embeds first (highest priority for divs)
            if element.name == 'div' and self._is_twitter_embed(element):
                block_type = 'twitter_embed'
                twitter_data = self._extract_twitter_embed_data(element)
                
                if twitter_data['tweet_id']:
                    metadata.update(twitter_data)
                    content = f"Twitter embed: {twitter_data['tweet_id']}"
                else:
                    return None  # Skip if we can't extract tweet ID
                    
            # Enhanced: Check if this is a byline element even if it's a div/span
            elif self._is_byline_element(element):
                # Extract byline information for metadata but don't create a content block
                # The frontend can use this information in the page header instead of duplicating it in the body
                author_info = self._extract_author_from_byline(element)
                
                # Store the author information in the article metadata
                if not self._extracted_author_info:
                    self._extracted_author_info = []
                self._extracted_author_info.append(author_info)
                
                # Don't create a content block for bylines - they should appear in page header
                return None
            elif element.name == 'div' and self._is_semantic_div(element):
                # Only process divs that are semantic content, not containers
                text_content = element.get_text(strip=True)
                if len(text_content) > 20:  # Only include if substantial content
                    block_type = 'paragraph'
                    content = text_content
                else:
                    return None  # Skip short divs
            else:
                # For other elements, try to extract meaningful content
                text_content = element.get_text(strip=True)
                if len(text_content) > 20:  # Only include if substantial content
                    block_type = 'paragraph'
                    content = text_content
                else:
                    return None  # Skip elements without substantial content
        
        # Create the content block
        return ContentBlock(
            type=block_type,
            content=content,
            level=level,
            position=position,
            metadata=metadata
        )
    
    def _extract_metadata(self, soup: BeautifulSoup, clean_content: str, article_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract enhanced metadata from content.
        Now includes microformat and Schema.org support as mentioned in Ctrl.blog research.
        """
        
        metadata = {}
        
        # Word count and reading time
        word_count = len(clean_content.split())
        metadata['word_count'] = word_count
        metadata['reading_time'] = max(1, round(word_count / 200))  # 200 WPM average
        
        # Content structure analysis
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        metadata['heading_count'] = len(headings)
        
        paragraphs = soup.find_all('p')
        substantial_paragraphs = [p for p in paragraphs if len(p.get_text(strip=True)) > 50]
        metadata['paragraph_count'] = len(substantial_paragraphs)
        
        # Media content
        images = soup.find_all('img')
        metadata['image_count'] = len(images)
        
        videos = soup.find_all('video')
        metadata['video_count'] = len(videos)
        
        # Link analysis
        links = soup.find_all('a')
        external_links = [link for link in links if self._is_external_link(link)]
        metadata['external_link_count'] = len(external_links)
        
        # Enhanced metadata extraction using microformats and Schema.org
        # As mentioned in Ctrl.blog research, h-entry microformat is widely supported
        enhanced_metadata = self._extract_structured_metadata(soup)
        metadata.update(enhanced_metadata)
        
        # Add extracted author information from bylines to metadata
        if hasattr(self, '_extracted_author_info') and self._extracted_author_info:
            # Use the first (primary) author for the main author field
            primary_author = self._extracted_author_info[0]
            metadata['extracted_author'] = primary_author.get('metadata', {}).get('author_name', '')
            metadata['extracted_author_role'] = primary_author.get('metadata', {}).get('author_role', '')
            metadata['extracted_byline'] = primary_author.get('display_text', '')
            
            # If there are multiple authors, store them all
            if len(self._extracted_author_info) > 1:
                metadata['all_extracted_authors'] = self._extracted_author_info
        
        return metadata
    
    def _extract_structured_metadata(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """
        Extract structured metadata using microformats and Schema.org.
        Based on Ctrl.blog research showing wide adoption of h-entry and Schema.org.
        """
        
        structured_metadata = {}
        
        # 1. h-entry microformat support (widely adopted according to Ctrl.blog)
        h_entry = soup.find(class_='h-entry')
        if h_entry:
            # Extract h-entry title
            p_name = h_entry.find(class_='p-name')
            if p_name:
                structured_metadata['microformat_title'] = p_name.get_text(strip=True)
            
            # Extract h-entry author
            p_author = h_entry.find(class_='p-author')
            if p_author:
                structured_metadata['microformat_author'] = p_author.get_text(strip=True)
            
            # Extract h-entry published date
            dt_published = h_entry.find(class_='dt-published')
            if dt_published:
                structured_metadata['microformat_published'] = dt_published.get('datetime') or dt_published.get_text(strip=True)
        
        # 2. Schema.org JSON-LD support
        json_ld_scripts = soup.find_all('script', type='application/ld+json')
        for script in json_ld_scripts:
            try:
                import json
                data = json.loads(script.string)
                if isinstance(data, dict):
                    if data.get('@type') in ['Article', 'NewsArticle', 'BlogPosting']:
                        structured_metadata['schema_title'] = data.get('headline')
                        structured_metadata['schema_author'] = self._extract_schema_author(data.get('author'))
                        structured_metadata['schema_published'] = data.get('datePublished')
                        structured_metadata['schema_description'] = data.get('description')
            except (json.JSONDecodeError, AttributeError):
                continue
        
        # 3. Open Graph Protocol (used by Instaparser according to research)
        og_title = soup.find('meta', property='og:title')
        if og_title:
            structured_metadata['og_title'] = og_title.get('content')
        
        og_description = soup.find('meta', property='og:description')
        if og_description:
            structured_metadata['og_description'] = og_description.get('content')
        
        # Article-specific Open Graph
        article_author = soup.find('meta', property='article:author')
        if article_author:
            structured_metadata['og_author'] = article_author.get('content')
        
        article_published = soup.find('meta', property='article:published_time')
        if article_published:
            structured_metadata['og_published'] = article_published.get('content')
        
        # 4. Standard meta tags (Mozilla Readability approach)
        meta_author = soup.find('meta', attrs={'name': 'author'})
        if meta_author:
            structured_metadata['meta_author'] = meta_author.get('content')
        
        meta_description = soup.find('meta', attrs={'name': 'description'})
        if meta_description:
            structured_metadata['meta_description'] = meta_description.get('content')
        
        # 5. Microsoft Edge specific (documented approach)
        meta_title = soup.find('meta', attrs={'name': 'title'})
        if meta_title:
            structured_metadata['edge_title'] = meta_title.get('content')
        
        return structured_metadata
    
    def _extract_schema_author(self, author_data) -> str:
        """Extract author name from Schema.org author data."""
        if not author_data:
            return None
        
        if isinstance(author_data, str):
            return author_data
        elif isinstance(author_data, dict):
            return author_data.get('name')
        elif isinstance(author_data, list) and author_data:
            first_author = author_data[0]
            if isinstance(first_author, dict):
                return first_author.get('name')
            return str(first_author)
        
        return None
    
    def _is_external_link(self, link: Tag) -> bool:
        """Check if link is external."""
        href = link.get('href', '')
        if not href:
            return False
        
        return href.startswith('http') and '://' in href
    
    def _assess_quality(self, candidate: CandidateElement, clean_content: str, 
                       content_blocks: List[ContentBlock], metadata: Dict[str, Any]) -> float:
        """
        Assess content quality using simplified scoring.
        Focuses on Safari-specific candidate scoring and basic content analysis.
        """
        
        # Calculate basic quality metrics
        word_count = len(clean_content.split()) if clean_content else 0
        block_count = len(content_blocks)
        
        # Content type diversity
        content_types = set(block.type for block in content_blocks)
        type_diversity = len(content_types)
        
        # Basic quality scoring
        length_score = min(1.0, word_count / 500)  # 500+ words = good
        structure_score = min(1.0, block_count / 10)  # 10+ blocks = good
        diversity_score = min(1.0, type_diversity / 4)  # 4+ types = good
        
        # Weighted combination
        basic_quality = (
            length_score * 0.4 +
            structure_score * 0.3 +
            diversity_score * 0.3
        )
        
        # Store quality metrics in metadata for API response
        metadata['content_quality_metrics'] = {
            'quality_score': basic_quality,
            'word_count': word_count,
            'block_count': block_count,
            'content_types': list(content_types),
            'type_diversity': type_diversity,
            'length_score': length_score,
            'structure_score': structure_score,
            'diversity_score': diversity_score,
            'evaluation_route': 'algorithmic_basic',
            # Safari-specific metrics
            'safari_score': candidate.final_score,
            'score_density': candidate.score_density,
            'safari_threshold_met': candidate.final_score >= self.MIN_SCORE_THRESHOLD
        }
        
        return basic_quality

    def _calculate_candidate_adjusted_height(self, element: Tag) -> float:
        """
        Calculate adjusted height using Safari's candidateElementAdjustedHeight algorithm.
        Subtracts forms and inappropriate lists from total height.
        """
        
        # Get element dimensions (simplified - Safari uses actual layout)
        total_height = 1000  # Estimated base height
        
        # Subtract form heights (Safari logic)
        forms = element.find_all('form')
        for form in forms:
            # Estimate form area impact
            total_height -= 100  # Simplified
        
        # Subtract inappropriate list heights (Safari's complex logic)
        lists = element.find_all(['ol', 'ul'])
        excluded_list = None
        
        for list_elem in lists:
            # Skip if contained in already excluded list
            if excluded_list and self._is_contained_in(list_elem, excluded_list):
                continue
                
            list_items = list_elem.find_all('li')
            if not list_items:
                total_height -= 50  # Remove empty lists
                continue
            
            # Calculate average line height per item
            avg_height_per_item = 100 / len(list_items) if list_items else 0
            
            # Safari's line height calculation (simplified)
            estimated_line_height = 20  # Base line height
            
            # Check if list items are too short (Safari's CandidateMinumumListItemLineCount = 4)
            if avg_height_per_item / estimated_line_height < 4:
                total_height -= 200  # Remove short lists
                excluded_list = list_elem
        
        return max(self.MIN_HEIGHT, total_height)
    
    def _is_contained_in(self, child: Tag, parent: Tag) -> bool:
        """Check if child element is contained within parent element."""
        current = child.parent
        while current:
            if current == parent:
                return True
            current = current.parent
        return False
    
    def _should_disqualify_due_to_horizontal_rule_density(self, candidate: CandidateElement) -> bool:
        """
        Safari's shouldDisqualifyDueToHorizontalRuleDensity method.
        Checks if there are too many horizontal rules relative to content height.
        """
        
        hr_elements = candidate.element.find_all('hr')
        if not hr_elements:
            return False
        
        # Estimate element dimensions
        element_width = 800  # Simplified estimation
        element_height = 1000  # Simplified estimation
        
        # Count significant HR elements (Safari uses 70% width threshold)
        significant_hrs = 0
        width_threshold = element_width * 0.7
        
        for hr in hr_elements:
            # Simplified width check (Safari uses actual clientWidth)
            if True:  # Assume all HRs are significant for now
                significant_hrs += 1
        
        if significant_hrs > 0:
            # Safari's MinimumAverageDistanceBetweenHRElements = 400
            avg_distance = element_height / significant_hrs
            if avg_distance < 400:
                logger.warning(f"Disqualifying due to HR density: {avg_distance} < 400")
                return True
        
        return False
    
    def _should_disqualify_due_to_header_density(self, candidate: CandidateElement) -> bool:
        """
        Safari's shouldDisqualifyDueToHeaderDensity method.
        Checks if there are too many headers with links relative to content height.
        """
        
        # Find headers with links (Safari's XPath: "(h1|h2|h3|h4|h5|h6|*/h1|*/h2|*/h3|*/h4|*/h5|*/h6)[a[@href]]")
        headers_with_links = []
        
        for header_tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            headers = candidate.element.find_all(header_tag)
            for header in headers:
                if header.find('a', href=True):
                    headers_with_links.append(header)
        
        if len(headers_with_links) <= 2:
            return False
        
        # Estimate element dimensions
        element_height = 1000  # Simplified estimation
        
        # Safari's PortionOfCandidateHeightToIgnoreForHeaderCheck = 0.1
        ignore_height = element_height * 0.1
        
        # Count headers in the middle section (Safari logic)
        middle_headers = 0
        for header in headers_with_links:
            # Simplified position check (Safari uses actual bounding rects)
            # Assume headers are in middle section for now
            middle_headers += 1
        
        if middle_headers > 0:
            # Safari's MinimumAverageDistanceBetweenHeaderElements = 400
            avg_distance = element_height / middle_headers
            if avg_distance < 400:
                logger.warning(f"Disqualifying due to header density: {avg_distance} < 400")
                return True
        
        return False
    
    def _should_disqualify_due_to_similar_elements(self, candidate: CandidateElement, all_candidates: List[CandidateElement] = None) -> bool:
        """
        Safari's shouldDisqualifyDueToSimilarElements method.
        Complex algorithm to detect if this element is part of a repetitive pattern.
        """
        
        element = candidate.element
        
        # Check if element is LI or DD with similar siblings
        if element.name.upper() in ['LI', 'DD']:
            parent = element.parent
            if parent:
                siblings = parent.find_all(element.name, recursive=False)
                for sibling in siblings:
                    if (sibling != element and 
                        sibling.get('class') == element.get('class')):
                        logger.warning(f"Disqualifying {element.name} due to similar siblings")
                        return True
        
        # Check class-based similarity (simplified version of Safari's complex logic)
        element_classes = element.get('class', [])
        if not element_classes:
            # Try parent classes
            if element.parent:
                element_classes = element.parent.get('class', [])
                if not element_classes and element.parent.parent:
                    element_classes = element.parent.parent.get('class', [])
        
        if element_classes:
            class_selector = '.' + '.'.join(element_classes)
            try:
                # Find similar elements with same classes
                similar_elements = candidate.element.parent.select(class_selector) if candidate.element.parent else []
                
                # Safari's complex scoring comparison (simplified)
                for similar in similar_elements:
                    if similar == element:
                        continue
                    
                    # Check if similar element has significantly higher score
                    # This is a simplified version of Safari's complex comparison
                    similar_text_length = len(similar.get_text(strip=True))
                    element_text_length = len(element.get_text(strip=True))
                    
                    if similar_text_length > element_text_length * 1.5:
                        logger.warning(f"Disqualifying due to similar element with higher score")
                        return True
                        
            except Exception:
                # Invalid selector, skip
                pass
        
        return False
    
    def _should_disqualify_for_deep_linking(self, candidate: CandidateElement) -> bool:
        """
        Safari's shouldDisqualifyForDeepLinking method.
        Checks if element contains too many deep links early in the content.
        Enhanced with better failure handling.
        """
        
        element = candidate.element
        
        # Safari's logic: find links that go deeper than current page
        current_path_segments = 5  # Increased from 4 to be even less aggressive
        deep_links = []
        
        try:
            links = element.find_all('a', href=True)
            for link in links:
                href = link.get('href', '')
                
                # Skip non-HTTP links
                if not href.startswith('http'):
                    continue
                
                # Count path segments (simplified)
                try:
                    path_segments = len([seg for seg in href.split('/') if seg and seg != 'http:' and seg != 'https:'])
                except:
                    continue
                
                if path_segments > current_path_segments:
                    # Check if it's not an attachment
                    rel = link.get('rel', '')
                    if isinstance(rel, list):
                        rel = ' '.join(rel)
                    if 'attachment' not in rel.lower():
                        deep_links.append(link)
        except Exception as e:
            logger.warning(f"Error analyzing deep links: {e}")
            return False  # Don't disqualify on error
        
        # Increased threshold from 8 to 12 to be less aggressive
        if len(deep_links) >= 12:
            # Check if they appear early in content (Safari's logic)
            # Simplified: assume first 20% of element height
            early_threshold = 0.2  # 20% of content
            
            # For simplicity, consider first few links as "early"
            # Increased from 5 to 8 to be less aggressive
            early_deep_links = deep_links[:8]
            
            # Only disqualify if we have a LOT of early deep links AND the content score is low
            if len(early_deep_links) >= 8 and candidate.final_score < self.MIN_SCORE_THRESHOLD * 2:
                logger.warning(f"Disqualifying due to deep linking: {len(early_deep_links)} early deep links with low score")
                return True
        
        return False
    
    def _extract_visual_title(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Extract title using Safari's visual-based approach.
        Uses Levenshtein distance from document.title and visual positioning.
        """
        
        document_title = soup.title.get_text(strip=True) if soup.title else ""
        if not document_title:
            return None
        
        # Find all heading candidates (h1-h6)
        heading_candidates = []
        
        for level in range(1, 7):  # h1 to h6
            headings = soup.find_all(f'h{level}')
            for heading in headings:
                text = heading.get_text(strip=True)
                if text and len(text) >= 4:  # Maxthon's minimum length
                    # Estimate visual position (simplified - Safari uses actual layout)
                    visual_position = self._estimate_visual_position(heading)
                    
                    heading_candidates.append({
                        'element': heading,
                        'text': text,
                        'level': level,
                        'visual_position': visual_position,
                        'levenshtein_distance': self._levenshtein_distance(text, document_title)
                    })
        
        if not heading_candidates:
            return document_title
        
        # Score candidates using Safari's approach
        best_candidate = None
        best_score = float('inf')
        
        for candidate in heading_candidates:
            # Safari's scoring: visual position + Levenshtein distance + heading level
            position_score = candidate['visual_position'] / 1000  # Normalize
            distance_score = candidate['levenshtein_distance'] / len(document_title) if document_title else 1
            level_score = candidate['level'] * 0.1  # Prefer h1 over h6
            
            # Combined score (lower is better)
            total_score = position_score + distance_score + level_score
            
            if total_score < best_score:
                best_score = total_score
                best_candidate = candidate
        
        # Return best candidate if it's reasonable, otherwise use document.title
        if best_candidate and best_candidate['levenshtein_distance'] <= len(document_title) * 0.7:
            return best_candidate['text']
        
        return document_title
    
    def _estimate_visual_position(self, element: Tag) -> float:
        """
        Estimate visual position of element (simplified version of Safari's layout analysis).
        Safari uses actual bounding rectangles - we approximate based on DOM position.
        """
        
        # Count elements before this one (rough approximation of visual position)
        position = 0
        current = element
        
        # Walk up to find position in document
        while current.parent:
            # Count preceding siblings
            for sibling in current.parent.children:
                if sibling == current:
                    break
                if hasattr(sibling, 'name'):  # Is a tag
                    position += 1
            current = current.parent
        
        # Estimate pixel position (very rough approximation)
        estimated_position = position * 50  # Assume ~50px per element
        
        return min(estimated_position, 1300)  # Safari's MAX_TOP_POSITION
    
    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """
        Calculate Levenshtein distance between two strings.
        Used by Safari for title matching.
        """
        
        if not s1:
            return len(s2)
        if not s2:
            return len(s1)
        
        # Normalize strings for comparison
        s1 = s1.lower().strip()
        s2 = s2.lower().strip()
        
        if s1 == s2:
            return 0
        
        # Create matrix
        rows = len(s1) + 1
        cols = len(s2) + 1
        matrix = [[0] * cols for _ in range(rows)]
        
        # Initialize first row and column
        for i in range(rows):
            matrix[i][0] = i
        for j in range(cols):
            matrix[0][j] = j
        
        # Fill matrix
        for i in range(1, rows):
            for j in range(1, cols):
                if s1[i-1] == s2[j-1]:
                    cost = 0
                else:
                    cost = 1
                
                matrix[i][j] = min(
                    matrix[i-1][j] + 1,      # deletion
                    matrix[i][j-1] + 1,      # insertion
                    matrix[i-1][j-1] + cost  # substitution
                )
        
        return matrix[rows-1][cols-1]
    
    def _find_prepended_appended_content(self, main_element: Tag) -> Tuple[List[Tag], List[Tag]]:
        """
        Find prepended and appended content using Safari's algorithm.
        Checks immediate siblings above (≥50px) and below (≥200px) main content.
        """
        
        prepended_elements = []
        appended_elements = []
        
        if not main_element.parent:
            return prepended_elements, appended_elements
        
        # Get all siblings
        siblings = [sibling for sibling in main_element.parent.children 
                   if hasattr(sibling, 'name') and sibling != main_element]
        
        main_position = list(main_element.parent.children).index(main_element)
        
        # Check preceding siblings (prepended content)
        for i in range(main_position - 1, -1, -1):
            sibling = list(main_element.parent.children)[i]
            if not hasattr(sibling, 'name'):
                continue
            
            # Skip if not a Tag element
            if not isinstance(sibling, Tag):
                continue
            
            # Estimate height (Safari uses actual bounding rect height)
            estimated_height = self._estimate_element_height(sibling)
            
            # Safari's minimum height for prepended content: 50px
            if estimated_height >= 50:
                # Check if it's within tight vertical window (simplified)
                if self._is_content_related(sibling, main_element):
                    prepended_elements.insert(0, sibling)  # Insert at beginning to maintain order
                else:
                    break  # Stop if we hit unrelated content
            else:
                break  # Stop if element is too small
        
        # Check following siblings (appended content)
        for i in range(main_position + 1, len(list(main_element.parent.children))):
            sibling = list(main_element.parent.children)[i]
            if not hasattr(sibling, 'name'):
                continue
            
            # Skip if not a Tag element
            if not isinstance(sibling, Tag):
                continue
            
            # Estimate height
            estimated_height = self._estimate_element_height(sibling)
            
            # Safari's minimum height for appended content: 200px
            if estimated_height >= 200:
                if self._is_content_related(sibling, main_element):
                    appended_elements.append(sibling)
                else:
                    break  # Stop if we hit unrelated content
            else:
                # For appended content, continue checking even if one element is small
                # (might be a short paragraph followed by a large image)
                if self._is_content_related(sibling, main_element):
                    appended_elements.append(sibling)
        
        logger.debug(f"Found {len(prepended_elements)} prepended and {len(appended_elements)} appended elements")
        return prepended_elements, appended_elements
    
    def _estimate_element_height(self, element: Tag) -> float:
        """
        Estimate element height (Safari uses actual layout measurements).
        """
        
        # Skip if not a Tag element
        if not isinstance(element, Tag):
            return 20  # Minimum height for text nodes
        
        # Count text content and child elements to estimate height
        text_content = element.get_text(strip=True)
        text_lines = len(text_content) / 80 if text_content else 0  # ~80 chars per line
        
        # Count block-level children
        block_children = len(element.find_all(['div', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol', 'blockquote']))
        
        # Count images and videos (they add significant height)
        media_elements = len(element.find_all(['img', 'video', 'iframe']))
        
        # Estimate total height
        estimated_height = (
            text_lines * 20 +           # ~20px per line of text
            block_children * 30 +       # ~30px per block element
            media_elements * 200        # ~200px per media element
        )
        
        return max(estimated_height, 20)  # Minimum 20px
    
    def _is_content_related(self, sibling: Tag, main_element: Tag) -> bool:
        """
        Check if sibling element is content-related to main element.
        Uses Safari's "tight vertical window" concept.
        """
        
        # Skip if not a Tag element
        if not isinstance(sibling, Tag):
            return False
        
        # Check for obvious non-content patterns
        sibling_class_id = f"{' '.join(sibling.get('class', []))} {sibling.get('id', '')}".lower()
        
        # Skip navigation, ads, etc.
        if self.NEGATIVE_PATTERNS.search(sibling_class_id):
            return False
        
        # Check for content indicators
        if self.POSITIVE_PATTERNS.search(sibling_class_id):
            return True
        
        # Check if it contains substantial text content
        text_content = sibling.get_text(strip=True)
        if len(text_content) < 50:
            # Small elements might still be related (captions, etc.)
            return len(text_content) > 10
        
        # Check for similar structure/styling (simplified)
        main_classes = set(main_element.get('class', []))
        sibling_classes = set(sibling.get('class', []))
        
        # If they share classes, likely related
        if main_classes & sibling_classes:
            return True
        
        # Check for content-like elements
        if sibling.name in ['p', 'div', 'section', 'article', 'figure', 'img']:
            return True
        
        return False
    
    def _clean_and_format_content_with_siblings(self, main_element: Tag, prepended_elements: List[Tag], appended_elements: List[Tag], soup: BeautifulSoup) -> str:
        """
        Clean content using Safari's cleaning algorithm and include prepended/appended content.
        """
        
        # Create a copy to avoid modifying original
        cleaned_element = BeautifulSoup(str(main_element), 'html.parser')
        
        # Remove unwanted elements (Safari's approach)
        self._remove_unwanted_elements(cleaned_element)
        
        # Clean attributes
        self._clean_attributes(cleaned_element)
        
        # Remove elements that should be pruned
        self._prune_elements(cleaned_element)
        
        # Convert to clean text with preserved structure
        clean_text = self._element_to_clean_text(cleaned_element)
        
        # Include prepended and appended content
        for sibling in prepended_elements:
            clean_text = self._element_to_clean_text(sibling) + "\n" + clean_text
        
        for sibling in appended_elements:
            clean_text += "\n" + self._element_to_clean_text(sibling)
        
        return clean_text
    
    def _structure_content_blocks_with_siblings(self, main_element: Tag, prepended_elements: List[Tag], appended_elements: List[Tag]) -> List[ContentBlock]:
        """
        Structure content into semantic blocks including prepended and appended elements.
        Enhanced with section-level filtering to exclude recommendation widgets.
        """
        blocks = []
        position = 0
        
        # Track seen content to avoid duplicates
        seen_content = set()
        seen_images = set()
        
        # Back to original element types - adding 'div' temporarily for Twitter embeds
        content_element_types = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'blockquote', 'ul', 'ol', 'img', 'video', 'figure', 'div']
        
        # Process prepended elements first
        for sibling in prepended_elements:
            for element in sibling.find_all(content_element_types):
                # Skip if this element or its parents should be excluded
                if self._should_skip_element_for_content_blocks(element):
                    continue
                    
                block = self._element_to_content_block(element, position)
                if block and self._is_unique_content_block(block, seen_content, seen_images):
                    blocks.append(block)
                    position += 1
        
        # Process main content
        for element in main_element.find_all(content_element_types):
            # Skip if this element or its parents should be excluded
            if self._should_skip_element_for_content_blocks(element):
                continue
                
            block = self._element_to_content_block(element, position)
            if block and self._is_unique_content_block(block, seen_content, seen_images):
                blocks.append(block)
                position += 1
        
        # Process appended elements
        for sibling in appended_elements:
            for element in sibling.find_all(content_element_types):
                # Skip if this element or its parents should be excluded
                if self._should_skip_element_for_content_blocks(element):
                    continue
                    
                block = self._element_to_content_block(element, position)
                if block and self._is_unique_content_block(block, seen_content, seen_images):
                    blocks.append(block)
                    position += 1
        
        return blocks
    
    def _is_content_image(self, img_element: Tag) -> bool:
        """
        Determine if an image is content-relevant (not decoration/icon/profile).
        Based on Safari's image filtering logic but more inclusive.
        Focus on basic filtering since section-level filtering should handle most cases.
        Enhanced to handle modern responsive images using srcset and filter out profiles/avatars.
        """
        
        # Get image source from src or srcset (modern responsive images)
        src = img_element.get('src', '').lower()
        srcset = img_element.get('srcset', '').lower()
        
        # Use srcset if src is empty (modern responsive images)
        image_url = src if src else srcset
        
        # Check image URL for obvious non-content patterns
        non_content_patterns = [
            '/ad/', '/ads/', '_ad.', '_ads.', 'advertisement', 'promo', 'marketing',
            'icon', 'logo', 'avatar', 'badge', 'button', 'arrow', 'sprite',
            'newsletter', 'signup', 'subscribe', 'generic', 'placeholder',
            'banner', 'social', 'share', 'facebook', 'twitter', 'linkedin',
            'footer', 'header', 'nav', 'sidebar', 'widget',
            # Enhanced: Profile/author image patterns
            'headshot', 'profile', 'author', 'byline', 'contributor', 'staff'
        ]
        
        if any(pattern in image_url for pattern in non_content_patterns):
            return False
        
        # Check for specific problematic paths
        if any(path in image_url for path in ['/dr/resources/', '/assets/icons/', '/static/icons/']):
            return False
        
        # Enhanced: Check alt text for author/profile indicators
        alt = img_element.get('alt', '').lower()
        
        # Check for author/profile patterns in alt text
        author_profile_patterns = [
            'headshot', 'profile', 'avatar', 'author', 'byline', 'contributor', 
            'staff', 'writer', 'journalist', 'reporter', 'editor'
        ]
        
        if any(pattern in alt for pattern in author_profile_patterns):
            return False
        
        # Enhanced: Check if alt text looks like a person's name (likely author photo)
        # Simple heuristic: if alt text is 2-3 words and doesn't contain common article words
        alt_words = alt.split()
        if len(alt_words) == 2 or len(alt_words) == 3:
            # Check if it looks like a name (no common article words)
            article_words = ['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']
            if not any(word in alt_words for word in article_words):
                # Could be a name, check if context suggests it's an author
                # Look at parent elements for author/byline context
                parent = img_element.parent
                while parent and parent.name not in ['body', 'html']:
                    parent_class = ' '.join(parent.get('class', [])).lower()
                    parent_id = parent.get('id', '').lower()
                    if any(pattern in parent_class or pattern in parent_id for pattern in author_profile_patterns):
                        return False
                    parent = parent.parent
        
        # Enhanced: Stricter dimension checking for small images
        width = img_element.get('width')
        height = img_element.get('height')
        if width and height:
            try:
                w, h = int(width), int(height)
                # Enhanced: Skip small images (increased from 30 to 60 to catch 36x36 profile pics)
                if w < 60 or h < 60:
                    return False
                # Enhanced: Skip very small images that might be icons/avatars
                if w <= 100 and h <= 100:
                    # Allow only if the image has clear content indicators
                    if not any(indicator in alt for indicator in ['photo', 'image', 'picture', 'screenshot']):
                        return False
                # Content images are usually reasonably sized
                if w > 150 and h > 150:
                    return True
            except ValueError:
                pass
        
        # If alt text is substantial, likely content (but check for profile patterns first)
        if len(alt) > 15 and not any(pattern in alt for pattern in author_profile_patterns):
            return True
        
        # Check for decorative alt patterns
        if alt in ['', 'image', 'photo', 'picture'] or any(pattern in alt for pattern in ['icon', 'logo']):
            # Don't immediately exclude - check other factors for modern images
            pass
        
        # Enhanced: Check for modern responsive image attributes
        # Images with srcset and proper dimensions are likely content
        if srcset and width and height:
            try:
                w, h = int(width), int(height)
                # Only accept larger responsive images
                if w >= 200 and h >= 150:  # Increased minimum size for responsive images
                    return True
            except ValueError:
                pass
        
        # Check for loading attributes (modern content images often have these)
        loading = img_element.get('loading', '').lower()
        fetchpriority = img_element.get('fetchpriority', '').lower()
        if loading in ['eager', 'lazy'] or fetchpriority in ['high']:
            # These are typically used for content images, but check size
            if width and height:
                try:
                    w, h = int(width), int(height)
                    if w >= 60 and h >= 60:  # Only larger images with loading attributes
                        return True
                except ValueError:
                    pass
        
        # Check CSS classes for content indicators
        img_classes = ' '.join(img_element.get('class', [])).lower()
        if any(pattern in img_classes for pattern in ['content', 'article', 'story', 'featured', 'main']):
            return True
        if any(pattern in img_classes for pattern in ['icon', 'logo', 'avatar', 'sprite', 'newsletter', 'signup', 'profile', 'headshot']):
            return False
        
        # Check parent context
        parent = img_element.parent
        if parent:
            parent_class = ' '.join(parent.get('class', [])).lower()
            if any(pattern in parent_class for pattern in ['content', 'article', 'story', 'figure', 'main']):
                return True
            if any(pattern in parent_class for pattern in ['nav', 'header', 'footer', 'sidebar', 'ad', 'menu', 'newsletter', 'signup', 'author', 'byline', 'profile']):
                return False
        
        # Check if image is inside a link (often decorative)
        link_parent = img_element.find_parent('a')
        if link_parent:
            link_text = link_parent.get_text(strip=True)
            # If link has substantial text, image might be decorative
            if len(link_text) > 20:
                return False
        
        # Enhanced check: if image URL is relative and contains generic patterns, likely not content
        if not image_url.startswith('http') and any(pattern in image_url for pattern in ['generic', 'default', 'placeholder']):
            return False
        
        # Enhanced: For modern responsive images, be more inclusive but check size
        # If image has proper dimensions and isn't obviously decorative, include it
        if srcset and width and height:
            try:
                w, h = int(width), int(height)
                if w >= 150 and h >= 100:  # Reasonable content image size
                    return True
            except ValueError:
                pass
        
        # Default to exclude if uncertain - be more conservative about small images
        return False
    
    def _extract_content_with_fallbacks(self, element: Tag, soup: BeautifulSoup) -> str:
        """
        Extract content using multiple fallback strategies when primary extraction fails.
        """
        
        fallback_content = ""
        
        try:
            # Fallback 1: Try basic cleaning without aggressive pruning
            logger.info("Trying fallback 1: Basic cleaning without aggressive pruning")
            cleaned_element = BeautifulSoup(str(element), 'html.parser')
            self._remove_unwanted_elements(cleaned_element)
            self._clean_attributes(cleaned_element)
            # Skip aggressive pruning
            fallback_content = self._element_to_clean_text(cleaned_element)
            
            if fallback_content and len(fallback_content.strip()) >= 100:
                logger.info(f"Fallback 1 successful: {len(fallback_content)} chars")
                return fallback_content
        except Exception as e:
            logger.warning(f"Fallback 1 failed: {e}")
        
        try:
            # Fallback 2: Extract all paragraph content from the element
            logger.info("Trying fallback 2: Extract all paragraphs")
            paragraphs = element.find_all('p')
            paragraph_texts = []
            for p in paragraphs:
                text = p.get_text(strip=True)
                if text and len(text) > 20:
                    paragraph_texts.append(text)
            
            if paragraph_texts:
                fallback_content = '\n\n'.join(paragraph_texts)
                if len(fallback_content.strip()) >= 100:
                    logger.info(f"Fallback 2 successful: {len(fallback_content)} chars")
                    return fallback_content
        except Exception as e:
            logger.warning(f"Fallback 2 failed: {e}")
        
        try:
            # Fallback 3: Extract all text content with minimal filtering
            logger.info("Trying fallback 3: Minimal filtering extraction")
            all_text = element.get_text(separator=' ', strip=True)
            
            # Basic cleanup - remove excessive whitespace
            import re
            cleaned_text = re.sub(r'\s+', ' ', all_text)
            cleaned_text = re.sub(r'\n\s*\n', '\n\n', cleaned_text)
            
            if cleaned_text and len(cleaned_text.strip()) >= 50:  # Lower threshold for this fallback
                logger.info(f"Fallback 3 successful: {len(cleaned_text)} chars")
                return cleaned_text
        except Exception as e:
            logger.warning(f"Fallback 3 failed: {e}")
        
        try:
            # Fallback 4: Look for article/main/content elements in the page
            logger.info("Trying fallback 4: Look for semantic content elements")
            semantic_elements = soup.find_all(['article', 'main', '[role="main"]'])
            
            for semantic_elem in semantic_elements:
                if semantic_elem != element:  # Don't reprocess the same element
                    text = semantic_elem.get_text(separator=' ', strip=True)
                    if text and len(text.strip()) >= 100:
                        logger.info(f"Fallback 4 successful with {semantic_elem.name}: {len(text)} chars")
                        return text
        except Exception as e:
            logger.warning(f"Fallback 4 failed: {e}")
        
        try:
            # Fallback 5: Find the largest text block in the page
            logger.info("Trying fallback 5: Find largest text block")
            all_elements = soup.find_all(['div', 'section', 'article', 'main'])
            
            best_text = ""
            best_length = 0
            
            for elem in all_elements:
                try:
                    text = elem.get_text(separator=' ', strip=True)
                    if len(text) > best_length and len(text) >= 100:
                        best_text = text
                        best_length = len(text)
                except:
                    continue
            
            if best_text:
                logger.info(f"Fallback 5 successful: {len(best_text)} chars")
                return best_text
        except Exception as e:
            logger.warning(f"Fallback 5 failed: {e}")
        
        # Final fallback: return whatever we have, even if short
        logger.warning("All fallbacks failed, returning minimal content")
        try:
            final_text = element.get_text(strip=True)
            return final_text if final_text else "Content extraction failed"
        except:
            return "Content extraction failed" 
    
    def _extract_paragraph_with_links(self, paragraph: Tag) -> Tuple[str, List[Dict[str, str]]]:
        """
        Extract paragraph content while preserving link information.
        Returns (content_with_placeholders, links_metadata) for frontend processing.
        """
        
        result = []
        links_metadata = []
        
        for element in paragraph.children:
            if isinstance(element, NavigableString):
                text = str(element).strip()
                if text:
                    result.append(text)
            elif isinstance(element, Tag):
                if element.name == 'a' and element.get('href'):
                    link_text = element.get_text(strip=True)
                    href = element.get('href')
                    if link_text and href:
                        # Enhanced: Handle both absolute and relative links
                        should_include_link = False
                        final_href = href
                        
                        if href.startswith('http'):
                            # Absolute HTTP/HTTPS links
                            should_include_link = True
                            final_href = href
                        elif href.startswith('/'):
                            # Relative links starting with / (site-relative)
                            should_include_link = True
                            # Convert to absolute URL if we have article metadata with URL
                            if hasattr(self, '_current_article_metadata') and self._current_article_metadata.get('url'):
                                from urllib.parse import urljoin, urlparse
                                base_url = self._current_article_metadata['url']
                                parsed_base = urlparse(base_url)
                                base_domain = f"{parsed_base.scheme}://{parsed_base.netloc}"
                                final_href = urljoin(base_domain, href)
                            else:
                                # Keep as relative if we don't have base URL
                                final_href = href
                        elif href.startswith('#'):
                            # Fragment links (hashtags) - only include if they're external (like Twitter hashtags)
                            if any(domain in href for domain in ['twitter.com', 'instagram.com', 'facebook.com']):
                                should_include_link = True
                                final_href = href
                            # Skip internal page fragments
                        # Skip other types of links (javascript:, mailto:, etc.)
                        
                        if should_include_link:
                            links_metadata.append({
                                'text': link_text,
                                'href': final_href
                            })
                            # Add text with link indicator for content
                            result.append(f"{link_text}")  # Just the text, frontend will handle linking
                        else:
                            result.append(link_text)  # Just the text for non-included links
                    elif link_text:
                        result.append(link_text)
                elif element.name == 'strong' or element.name == 'b':
                    text = element.get_text(strip=True)
                    if text:
                        result.append(f"<strong>{text}</strong>")  # Frontend expects HTML tags
                elif element.name == 'em' or element.name == 'i':
                    text = element.get_text(strip=True)
                    if text:
                        result.append(f"<em>{text}</em>")  # Frontend expects HTML tags
                else:
                    # For other elements, just get the text
                    text = element.get_text(strip=True)
                    if text:
                        result.append(text)
        
        return ' '.join(result), links_metadata
    
    def _is_subtitle_paragraph(self, paragraph: Tag, position: int) -> bool:
        """
        Detect if a paragraph is a subtitle/lead paragraph.
        Uses semantic data attributes, styling, position, and content characteristics.
        Prioritizes explicit semantic indicators over heuristics.
        """
        
        # PRIORITY 1: Check for explicit semantic data attributes (most reliable)
        # These are used by professional news sites for testing and content management
        data_qa = paragraph.get('data-qa', '').lower()
        data_testid = paragraph.get('data-testid', '').lower()
        data_role = paragraph.get('data-role', '').lower()
        
        # Definitive subtitle indicators
        subtitle_data_patterns = ['subheadline', 'subtitle', 'sub-title', 'lead', 'deck', 'standfirst', 'summary', 'intro']
        
        if any(pattern in data_qa for pattern in subtitle_data_patterns):
            return True
        if any(pattern in data_testid for pattern in subtitle_data_patterns):
            return True
        if any(pattern in data_role for pattern in subtitle_data_patterns):
            return True
        
        # PRIORITY 2: Check for subtitle-like CSS classes (reliable)
        classes = paragraph.get('class', [])
        class_text = ' '.join(classes).lower()
        class_patterns = ['lead', 'subtitle', 'sub-title', 'deck', 'standfirst', 'summary', 'intro', 'subheadline']
        if any(pattern in class_text for pattern in class_patterns):
            return True
        
        # PRIORITY 3: Check parent container styling (moderately reliable)
        parent = paragraph.parent
        if parent:
            parent_classes = ' '.join(parent.get('class', [])).lower()
            if any(pattern in parent_classes for pattern in class_patterns):
                return True
            
            # Check parent data attributes too
            parent_data_qa = parent.get('data-qa', '').lower()
            parent_data_testid = parent.get('data-testid', '').lower()
            if any(pattern in parent_data_qa for pattern in subtitle_data_patterns):
                return True
            if any(pattern in parent_data_testid for pattern in subtitle_data_patterns):
                return True
        
        # PRIORITY 4: Positional and content heuristics (fallback for less semantic markup)
        # Only check these if no explicit semantic indicators were found
        
        # Must be in first few paragraphs to be considered
        if position > 2:
            return False
        
        # Check text characteristics
        text = paragraph.get_text(strip=True)
        
        # Subtitles are usually shorter (under 200 chars) and descriptive
        if len(text) < 200 and position <= 1:
            # Check if it contains typical subtitle language patterns
            subtitle_content_patterns = [
                'if ', 'when ', 'after ', 'before ', 'while ', 'as ',
                'parents of', 'relatives of', 'people who', 'those who',
                'restrictions', 'concerns', 'worries', 'face'
            ]
            if any(pattern in text.lower() for pattern in subtitle_content_patterns):
                return True
        
        return False
    
    def _is_content_related_element(self, element: Tag) -> bool:
        """
        Check if element is content-related using Safari's semantic analysis.
        """
        
        # Check for article semantic markers (HTML5 semantic elements)
        if element.name in ['article', 'main', 'section']:
            return True
            
        # Check for main content indicators
        element_id = element.get('id', '').lower()
        if element_id in ['main', 'content', 'article', 'post', 'entry']:
            return True
            
        # Check for role attributes
        role = element.get('role', '').lower()
        if role in ['main', 'article']:
            return True
            
        # Check for microdata
        itemtype = element.get('itemtype', '').lower()
        if 'article' in itemtype or 'newsarticle' in itemtype:
            return True
            
        # Check for positive class patterns
        classes = ' '.join(element.get('class', []))
        if self.POSITIVE_PATTERNS.search(classes):
            return True
            
        return False
    
    def _is_unique_content_block(self, block: ContentBlock, seen_content: set, seen_images: set) -> bool:
        """
        Check if a content block is unique to prevent duplicates.
        Enhanced to catch images with different type classifications, photo credit duplication,
        container divs that duplicate their children's content, and Twitter link paragraphs/quotes
        that are duplicated by proper Twitter embeds.
        
        Special handling: Allows intentional pullquote duplicates (pullquote + paragraph).
        """
        
        # Enhanced debug logging for byline blocks
        if 'by ' in block.content.lower() and len(block.content) < 100:
            logger.info(f"UNIQUENESS CHECK: {block.type} block with content: '{block.content}'")
        
        # Enhanced: Check for newsletter content (The Verge specific)
        if block.type == 'paragraph' and self._is_newsletter_content(block.content):
            # Newsletter descriptions should be filtered out as they're not article content
            return False
        
        # Enhanced: Check for byline content that might have slipped through the main detection
        if block.type == 'paragraph' and self._is_byline_content(block.content):
            logger.info(f"FILTERING OUT BYLINE PARAGRAPH: '{block.content}'")
            return False
        
        # Enhanced: Check for photo credit paragraphs that duplicate figure captions
        if block.type == 'paragraph' and self._is_photo_credit_paragraph(block.content):
            # Photo credit paragraphs should be filtered out as they're captured in figure captions
            return False
        
        # Enhanced: Check if this paragraph block contains Twitter content that's been properly embedded
        if block.type == 'paragraph' and self._is_twitter_paragraph_duplicate(block):
            # Skip paragraph blocks that contain tweet content when we have proper Twitter embeds
            return False
        
        # Enhanced: Check if this quote block contains Twitter content that's been properly embedded
        # Original Twitter blockquotes often get processed as quote blocks before JS transformation
        if block.type == 'quote' and self._is_twitter_quote_duplicate(block):
            # Skip quote blocks that contain tweet content when we have proper Twitter embeds
            return False
        
        # Enhanced: More aggressive duplicate detection for overly long content
        content_text = block.content.strip()
        
        # Skip extremely long content that might be container divs
        if len(content_text) > 2000:
            return False
        
        # Create a normalized content fingerprint for duplicate detection
        content_fingerprint = re.sub(r'\s+', ' ', content_text.lower())  # Normalize whitespace
        content_fingerprint = re.sub(r'[^\w\s]', '', content_fingerprint)  # Remove punctuation
        
        # Enhanced: Special handling for pullquotes - allow intentional duplicates
        # Pullquotes are editorial highlights of key statements and should coexist with main text
        if block.type == 'pullquote':
            # For pullquotes, track separately to allow one pullquote + one paragraph of same content
            pullquote_fingerprint = f"pullquote:{content_fingerprint[:150]}"
            
            # Check if we already have this pullquote
            if pullquote_fingerprint in seen_content:
                return False  # Already have this pullquote
            
            # Add this pullquote to seen content
            seen_content.add(pullquote_fingerprint)
            return True
        
        # Enhanced: For paragraphs, check if this might contain a pullquote excerpt
        # Allow paragraphs that contain pullquote content (they're the full context)
        if block.type == 'paragraph':
            # Check if any existing pullquote is contained within this paragraph
            paragraph_content = content_fingerprint
            
            # Look for pullquote entries that might be excerpts of this paragraph
            for existing_entry in seen_content:
                if existing_entry.startswith('pullquote:'):
                    pullquote_content = existing_entry[10:]  # Remove "pullquote:" prefix
                    
                    # If this paragraph contains a pullquote (pullquote is excerpt of paragraph)
                    if pullquote_content and pullquote_content in paragraph_content:
                        # This is the full paragraph that contains the pullquote excerpt - allow it
                        seen_content.add(content_fingerprint[:150])
                        return True
            
            # Continue with normal duplicate detection for paragraphs
        
        # Enhanced: Check if this content is a significant subset of existing content
        # This catches cases where a div contains the same text as its children
        for existing_content in seen_content:
            # Skip pullquote entries for this comparison
            if existing_content.startswith('pullquote:'):
                continue
                
            # Check if current content is contained within existing content (80% overlap)
            if len(content_text) > 100:  # Only for substantial content
                # Check if this content is mostly contained in existing content
                if content_fingerprint.lower() in existing_content.lower():
                    return False
                # Check if existing content is mostly contained in this content  
                if existing_content.lower() in content_fingerprint.lower() and len(existing_content) > 50:
                    return False
        
        # For image/media content with src, prioritize URL-based deduplication
        if block.metadata and block.metadata.get('src'):
            image_src = block.metadata.get('src', '')
            # Normalize the image URL (remove query parameters)
            normalized_src = re.sub(r'\?.*$', '', image_src)
            if normalized_src in seen_images:
                return False
            seen_images.add(normalized_src)
        
        # For all other content types, check text-based similarity
        # Use first 150 characters as fingerprint (increased from 100)
        text_fingerprint = content_fingerprint[:150]
        
        # For non-pullquote content, check normal duplicate detection
        if text_fingerprint in seen_content:
            return False
        
        seen_content.add(text_fingerprint)
        
        # Also add the full content fingerprint for container detection
        if len(content_fingerprint) > 150:
            seen_content.add(content_fingerprint)
        
        return True
    
    def _is_photo_credit_paragraph(self, content: str) -> bool:
        """
        Detect if a paragraph contains only photo credit information that would
        duplicate figure captions. Based on Safari Reader Mode patterns.
        """
        
        if not content or len(content) > 300:  # Photo credits are typically short
            return False
        
        content_lower = content.strip().lower()
        
        # Pattern 1: Standard photo credit format 
        photo_credit_patterns = [
            r'^\s*©?\s*\(\s*photo\s+by\s+[^)]+\)\s*\([^)]+\)\s*$',  # (Photo by X)(Agency)
            r'^\s*©\s*\(\s*photo\s+by\s+[^)]+\)\s*\([^)]+\)\s*$',   # © (Photo by X)(Agency)
            r'^\s*photo:\s*[^.]+(?:ap\s+images?|reuters|getty|sipa|afp)',  # Photo: X AP Images
            r'^\s*credit:\s*[^.]+(?:ap\s+images?|reuters|getty|sipa|afp)',  # Credit: X Reuters
            r'^\s*image:\s*[^.]+(?:ap\s+images?|reuters|getty|sipa|afp)',   # Image: X Getty
        ]
        
        for pattern in photo_credit_patterns:
            if re.match(pattern, content_lower):
                return True
        
        # Pattern 2: Check for typical photo credit agencies/sources
        photo_agencies = [
            'ap images', 'reuters', 'getty images', 'sipa usa', 'afp', 'bloomberg',
            'bildbyran', 'maxim thore', 'associated press', 'press association'
        ]
        
        # If content is short and contains photo agencies, likely a photo credit
        if len(content) < 150 and any(agency in content_lower for agency in photo_agencies):
            # Additional checks to ensure it's really just a photo credit
            # Look for typical photo credit words
            credit_indicators = ['photo', 'image', 'credit', '©', 'via', 'courtesy']
            if any(indicator in content_lower for indicator in credit_indicators):
                # And check it doesn't contain substantial article content
                if not any(article_word in content_lower for article_word in [
                    'said', 'according', 'reported', 'announced', 'told', 'explained',
                    'the', 'and', 'but', 'however', 'therefore', 'meanwhile'
                ]):
                    return True
        
        return False
    
    def _should_exclude_section(self, element: Tag) -> bool:
        """
        Identify sections that should be excluded entirely (recommendations, ads, etc.).
        Made more conservative to avoid filtering out legitimate article content.
        """
        
        # Check element classes and IDs for recommendation/widget patterns
        classes = ' '.join(element.get('class', [])).lower()
        element_id = element.get('id', '').lower()
        
        # Be very specific about recommendation widget services (high confidence patterns)
        widget_service_patterns = [
            'taboola', 'outbrain', 'revcontent', 'mgid', 'zergnet', 'adblade',
            'sharethrough', 'content-ad', 'native-ad'
        ]
        
        # Check for specific widget service indicators (high confidence)
        if any(service in classes or service in element_id for service in widget_service_patterns):
            return True
        
        # Specific structural patterns that clearly indicate non-content sections
        # These are very specific and unlikely to catch legitimate article content
        clear_non_content_patterns = [
            'page-below', 'below-article', 'post-article', 'after-content',
            'article-footer', 'content-footer', 'story-footer',
            'page-aside', 'content-aside', 'article-sidebar'
        ]
        
        if any(pattern in classes or pattern in element_id for pattern in clear_non_content_patterns):
            return True
        
        # Enhanced: More precise Related Stories detection
        # Only exclude if multiple specific criteria are met (not just individual patterns)
        data_parsely_title = element.get('data-parsely-title', '').lower()
        has_hub_peek = element.get('data-is-hub-peek') is not None
        
        # Very specific: Related Stories section detection
        if data_parsely_title == 'related stories' and has_hub_peek:
            return True
        
        # Alternative specific pattern: PageListEnhancementGeneric AND Enhancement together
        # This is more precise than just Enhancement-item alone
        if ('pagelistenhancementgeneric' in classes and 'enhancement' in classes):
            return True
        
        # Enhanced: Very specific Hub Peek sections with certain class combinations
        if has_hub_peek and any(pattern in classes for pattern in [
            'pageliststandard', 'pagepromo', 'pagelist-items'
        ]):
            return True
        
        # Check data attributes for widget-specific patterns (high confidence)
        data_attrs = []
        for attr_name in element.attrs:
            if attr_name.startswith('data-'):
                data_attrs.append(attr_name.lower())
                data_attrs.append(str(element.attrs[attr_name]).lower())
        
        data_attr_text = ' '.join(data_attrs)
        if any(pattern in data_attr_text for pattern in [
            'taboola', 'outbrain', 'mgid', 'zergnet',
            'item-id', 'item-title', 'item-thumb'  # Very specific to recommendation widgets
        ]):
            return True
        
        # Video recommendation widget patterns (very specific)
        video_widget_patterns = [
            'videocube', 'video-cube', 'trc_spotlight', 'trc_rbox', 'trc_'
        ]
        
        if any(pattern in classes for pattern in video_widget_patterns):
            return True
        
        # Only exclude very specific recommendation-related patterns
        specific_recommendation_patterns = [
            'taboola-container', 'outbrain-container', 'recommended-articles-widget',
            'content-recommendations', 'more-from-section', 'you-might-also-like'
        ]
        
        if any(pattern in classes or pattern in element_id for pattern in specific_recommendation_patterns):
            return True
        
        # Check for high density of external links (typical in recommendation widgets)
        # But only if element is small and has many links
        links = element.find_all('a', href=True)
        if len(links) > 8:  # Increased threshold
            text_content = element.get_text(strip=True)
            if len(text_content) < 500:  # Only for small sections with many links
                external_domains = set()
                for link in links:
                    href = link.get('href', '')
                    if href.startswith('http'):
                        try:
                            from urllib.parse import urlparse
                            domain = urlparse(href).netloc
                            if domain:
                                external_domains.add(domain)
                        except:
                            pass
                
                # If many links point to the same external domain, likely recommendations
                if len(external_domains) == 1 and len(links) > 10:
                    return True
        
        return False

    def _estimate_element_area(self, element: Tag) -> float:
        """Rough estimate of element area for density calculations."""
        # Simple heuristic based on content length and number of children
        text_length = len(element.get_text(strip=True))
        child_count = len(element.find_all())
        return max(text_length / 10, child_count * 50)  # Rough area estimate

    def _is_duplicate_title(self, heading: str, article_title: str) -> bool:
        """
        Check if the heading is a duplicate of the article title.
        Enhanced to handle publication names, punctuation variations, and perspective changes.
        """
        if not heading or not article_title:
            return False
        
        # Normalize both titles for comparison
        def normalize_title(title):
            """Clean title for comparison by removing publication names and normalizing text."""
            import re
            
            # Remove common publication name patterns at the end
            title = re.sub(r'\s*[-|–—]\s*(?:.*?(?:Post|Times|News|CNN|BBC|Reuters|AP|NPR|Fox|NBC|CBS|ABC|The Verge|Verge|TechCrunch|Wired|Ars Technica).*?)$', '', title, flags=re.IGNORECASE)
            
            # Normalize punctuation - convert all dashes to regular dash
            title = re.sub(r'[–—]', '-', title)
            
            # Normalize quotes and apostrophes
            title = re.sub(r'[""''`]', '"', title)
            title = re.sub(r"['`]", "'", title)
            
            # Remove extra whitespace and normalize
            title = re.sub(r'\s+', ' ', title.strip())
            
            # Convert to lowercase for comparison
            return title.lower()
        
        def normalize_perspective(title):
            """Normalize first/third person perspective differences."""
            import re
            
            # Common first/third person substitutions
            substitutions = [
                (r'\bi\s+', 'crypto bro '),
                (r'\bmy\s+', 'the '),
                (r'\bme\s+', 'him '),
                (r'\bme$', 'him'),
                (r'\bus\s+', 'them '),
                (r'\bour\s+', 'their '),
                (r'\bwe\s+', 'they '),
                (r'\bhow\s+i\s+', 'how a crypto bro '),
                (r'\bhow\s+we\s+', 'how they '),
            ]
            
            for pattern, replacement in substitutions:
                title = re.sub(pattern, replacement, title, flags=re.IGNORECASE)
            
            return title
        
        normalized_heading = normalize_title(heading)
        normalized_article_title = normalize_title(article_title)
        
        # Also try perspective normalization
        perspective_heading = normalize_perspective(normalized_heading)
        perspective_article_title = normalize_perspective(normalized_article_title)
        
        # Check exact match after normalization
        if normalized_heading == normalized_article_title:
            return True
        
        # Check perspective-normalized match
        if perspective_heading == perspective_article_title or perspective_heading == normalized_article_title:
            return True
        
        # Check if heading is substantially contained in article title (80% match)
        if len(normalized_heading) > 20:  # Only for substantial headings
            # Check if heading is a substring of article title
            if normalized_heading in normalized_article_title or normalized_article_title in normalized_heading:
                return True
            
            # Check similarity ratio with both normalized versions
            from difflib import SequenceMatcher
            similarity1 = SequenceMatcher(None, normalized_heading, normalized_article_title).ratio()
            similarity2 = SequenceMatcher(None, perspective_heading, normalized_article_title).ratio()
            
            # Use the higher similarity score
            max_similarity = max(similarity1, similarity2)
            
            if max_similarity >= 0.75:  # 75% similarity threshold (more lenient)
                return True
        
        # Check word overlap for catching paraphrased titles
        if len(normalized_heading) > 20 and len(normalized_article_title) > 20:
            heading_words = set(normalized_heading.split())
            title_words = set(normalized_article_title.split())
            
            # Remove common stop words for better comparison
            stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'how', 'i', 'he', 'she', 'they'}
            heading_words -= stop_words
            title_words -= stop_words
            
            if len(heading_words) > 3 and len(title_words) > 3:
                # Calculate word overlap ratio
                overlap = len(heading_words & title_words)
                min_words = min(len(heading_words), len(title_words))
                
                if overlap / min_words >= 0.7:  # 70% word overlap
                    return True
        
        return False

    def _extract_image_url(self, img_element: Tag) -> str:
        """
        Extract the best image URL from src or srcset attributes.
        Handles modern responsive images that use srcset instead of src.
        """
        # Try src first
        src = img_element.get('src', '').strip()
        if src:
            return src
        
        # Try srcset
        srcset = img_element.get('srcset', '').strip()
        if srcset:
            # Parse srcset to get the largest image
            # srcset format: "url1 width1, url2 width2, ..."
            try:
                entries = []
                for entry in srcset.split(','):
                    entry = entry.strip()
                    if not entry:
                        continue
                    
                    parts = entry.split()
                    if len(parts) >= 1:
                        url = parts[0]
                        # Extract width if present (e.g., "800w")
                        width = 0
                        if len(parts) >= 2 and parts[1].endswith('w'):
                            try:
                                width = int(parts[1][:-1])
                            except ValueError:
                                width = 0
                        entries.append((url, width))
                
                if entries:
                    # Return the largest image URL, or first if no widths
                    if any(width > 0 for url, width in entries):
                        best_entry = max(entries, key=lambda x: x[1])
                        return best_entry[0]
                    else:
                        return entries[0][0]
            except Exception:
                # If parsing fails, try to get first URL from srcset
                first_url = srcset.split(',')[0].strip().split()[0]
                return first_url
        
        return ''
    
    def _is_after_section_delimiter(self, element: Tag) -> bool:
        """
        Check if element comes after a section delimiter that indicates the end of main content.
        Safari Reader Mode stops processing after encountering headers like "Related Content",
        "Latest News", "More Stories", etc.
        
        Enhanced: Only apply delimiter filtering if delimiters appear in the final portion of content
        to avoid cutting off legitimate mid-article content.
        """
        
        # Don't apply delimiter filtering if we don't have a main document context
        if not hasattr(self, '_section_delimiters_cache'):
            self._section_delimiters_cache = None
        
        # Find section delimiters in the document (cache for performance)
        if self._section_delimiters_cache is None:
            self._section_delimiters_cache = self._find_section_delimiters()
        
        # If no section delimiters found, don't filter
        if not self._section_delimiters_cache:
            return False
        
        # Enhanced: Only apply section delimiter filtering if the delimiter appears
        # in the final portion of the content (like Safari Reader Mode intended)
        
        # Get the main content container to calculate position
        try:
            # Find the root content container
            content_root = element
            while content_root.parent and content_root.parent.name not in ['body', 'html', '[document]']:
                content_root = content_root.parent
            
            # Get all content elements to calculate position percentages
            content_element_types = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'blockquote', 'ul', 'ol', 'img', 'video', 'figure', 'div']
            all_content_elements = content_root.find_all(content_element_types)
            
            if len(all_content_elements) < 20:  # Too few elements to apply percentage logic
                return False
            
            # Check if any section delimiter appears in the final 25% of content
            final_portion_threshold = int(len(all_content_elements) * 0.75)  # Final 25%
            
            valid_delimiters = []
            for delimiter in self._section_delimiters_cache:
                try:
                    delimiter_position = all_content_elements.index(delimiter)
                    if delimiter_position >= final_portion_threshold:
                        valid_delimiters.append(delimiter)
                        logger.debug(f"Valid delimiter '{delimiter.get_text(strip=True)}' at position {delimiter_position}/{len(all_content_elements)} (final 25%)")
                    else:
                        logger.debug(f"Ignoring mid-article delimiter '{delimiter.get_text(strip=True)}' at position {delimiter_position}/{len(all_content_elements)} (not in final 25%)")
                except ValueError:
                    # Delimiter not in the main content elements list
                    continue
            
            # Only filter if we have valid delimiters in the final portion
            if not valid_delimiters:
                return False
            
            # Check if element comes after any valid delimiter in document order
            for delimiter in valid_delimiters:
                if self._element_comes_after(element, delimiter):
                    return True
            
            return False
            
        except Exception as e:
            logger.warning(f"Error in enhanced section delimiter filtering: {e}")
            # Fallback to original logic but be more conservative
            return False
    
    def _find_section_delimiters(self) -> List[Tag]:
        """
        Find section delimiter headings that indicate the end of main content.
        These are patterns Safari Reader Mode uses to stop content extraction.
        """
        
        if not hasattr(self, '_current_soup') or not self._current_soup:
            return []
        
        delimiters = []
        
        # Section delimiter patterns (case-insensitive)
        delimiter_patterns = [
            # Primary delimiters (very strong indicators)
            r'^related\s+content$',
            r'^related\s+articles?$', 
            r'^related\s+stories$',
            r'^related$',  # Enhanced: Just "Related" by itself (common in The Verge)
            r'^latest\s+news$',
            r'^more\s+stories$',
            r'^more\s+news$',
            r'^more\s+from\s+',
            r'^you\s+might\s+also\s+like$',
            r'^recommended\s+for\s+you$',
            r'^trending\s+now$',
            r'^popular\s+stories$',
            r'^most\s+popular$',  # Enhanced: "Most Popular" (common in The Verge)
            
            # Secondary delimiters (contextual)
            r'^also\s+read$',
            r'^see\s+also$',
            r'^what\s+to\s+read\s+next$',
            r'^don\'t\s+miss$',
            r'^top\s+stories$',
            
            # The Verge specific delimiters
            r'^installer$',  # Enhanced: The Verge's "Installer" newsletter section
            r'^the\s+vergecast$',  # The Verge's podcast section
            r'^command\s+line$',  # The Verge's Command Line newsletter
            r'^decoder$',  # The Verge's Decoder podcast section
            
            # Sport-specific delimiters (for NHL.com and similar)
            r'^more\s+nhl\s+news$',
            r'^around\s+the\s+league$',
            r'^other\s+news$',
        ]
        
        # Find headings that match delimiter patterns
        headings = self._current_soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        
        for heading in headings:
            heading_text = heading.get_text(strip=True).lower()
            
            # Check each pattern
            for pattern in delimiter_patterns:
                if re.match(pattern, heading_text):
                    delimiters.append(heading)
                    break  # One match per heading is enough
        
        return delimiters
    
    def _element_comes_after(self, element: Tag, delimiter: Tag) -> bool:
        """
        Check if element comes after delimiter in document order.
        Uses a more robust approach to determine document position.
        """
        
        try:
            # Get the root document
            root = delimiter
            while root.parent and root.parent.name not in ['html', '[document]']:
                root = root.parent
            
            # Get all elements in document order by walking the tree
            all_elements = []
            
            def collect_elements(node):
                if hasattr(node, 'name') and node.name:  # Is a Tag
                    all_elements.append(node)
                # Recurse into children
                if hasattr(node, 'children'):
                    for child in node.children:
                        collect_elements(child)
            
            collect_elements(root)
            
            # Find positions of delimiter and element
            delimiter_pos = -1
            element_pos = -1
            
            for i, elem in enumerate(all_elements):
                if elem == delimiter:
                    delimiter_pos = i
                if elem == element:
                    element_pos = i
            
            # Only filter if element clearly comes after delimiter
            if delimiter_pos >= 0 and element_pos >= 0:
                return element_pos > delimiter_pos
            
            # Fallback: check if element is a descendant of something after delimiter
            # This is more conservative
            element_ancestors = []
            current = element
            while current and current.parent:
                element_ancestors.append(current.parent)
                current = current.parent
            
            # Check if any ancestor comes after delimiter
            for ancestor in element_ancestors:
                for i, elem in enumerate(all_elements):
                    if elem == delimiter:
                        delimiter_pos = i
                    if elem == ancestor:
                        ancestor_pos = i
                        if delimiter_pos >= 0 and ancestor_pos > delimiter_pos:
                            return True
            
            return False
            
        except Exception as e:
            # If position detection fails, don't filter (conservative approach)
            return False
    
    def _is_section_delimiter(self, element: Tag) -> bool:
        """
        Check if element is itself a section delimiter heading.
        These headings should be excluded from the final content.
        """
        
        # Only check heading elements
        if not element.name or element.name.lower() not in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            return False
        
        # Get heading text
        heading_text = element.get_text(strip=True).lower()
        
        # Section delimiter patterns (same as in _find_section_delimiters)
        delimiter_patterns = [
            # Primary delimiters (very strong indicators)
            r'^related\s+content$',
            r'^related\s+articles?$', 
            r'^related\s+stories$',
            r'^related$',  # Enhanced: Just "Related" by itself (common in The Verge)
            r'^latest\s+news$',
            r'^more\s+stories$',
            r'^more\s+news$',
            r'^more\s+from\s+',
            r'^you\s+might\s+also\s+like$',
            r'^recommended\s+for\s+you$',
            r'^trending\s+now$',
            r'^popular\s+stories$',
            r'^most\s+popular$',  # Enhanced: "Most Popular" (common in The Verge)
            
            # Secondary delimiters (contextual)
            r'^also\s+read$',
            r'^see\s+also$',
            r'^what\s+to\s+read\s+next$',
            r'^don\'t\s+miss$',
            r'^top\s+stories$',
            
            # The Verge specific delimiters
            r'^installer$',  # Enhanced: The Verge's "Installer" newsletter section
            r'^the\s+vergecast$',  # The Verge's podcast section
            r'^command\s+line$',  # The Verge's Command Line newsletter
            r'^decoder$',  # The Verge's Decoder podcast section
            
            # Sport-specific delimiters (for NHL.com and similar)
            r'^more\s+nhl\s+news$',
            r'^around\s+the\s+league$',
            r'^other\s+news$',
        ]
        
        # Check if heading matches any delimiter pattern
        for pattern in delimiter_patterns:
            if re.match(pattern, heading_text):
                return True
        
        return False

    def _extract_visible_figure_caption(self, element: Tag) -> Optional[str]:
        """
        Extract visible caption from a figure element using Safari Reader Mode logic.
        Focus on what's actually visible to users, not hidden metadata.
        Enhanced to reject filename-like captions and technical metadata.
        """
        
        # Safari Rule 1: Skip figures marked as hidden
        if element.get('aria-hidden') == 'true':
            return None
        
        # Safari Rule 2: Check for actual figcaption (highest priority)
        figcaption = element.find('figcaption')
        if figcaption:
            # Apply visibility filtering to figcaption content
            visible_caption = self._extract_visible_caption_text(figcaption)
            if visible_caption and self._is_meaningful_caption(visible_caption):
                return visible_caption
        
        # Safari Rule 3: Look for separate caption elements near the figure
        # Check next sibling for caption-like content
        next_sibling = element.find_next_sibling()
        if next_sibling and next_sibling.name in ['p', 'div', 'span']:
            sibling_text = next_sibling.get_text(strip=True)
            # Check if it looks like a photo caption and is meaningful
            if (len(sibling_text) < 200 and 
                any(indicator in sibling_text.lower() for indicator in 
                    ['photo', '©', 'credit', 'image', 'getty', 'reuters', 'ap images', 'sipa']) and
                self._is_meaningful_caption(sibling_text)):
                return sibling_text
        
        # Safari Rule 4: Look in the figure's parent container for caption elements
        parent = element.parent
        if parent:
            # Look for elements with caption-related classes or IDs
            caption_elements = parent.find_all(['p', 'div', 'span'], class_=lambda x: x and any(
                caption_class in ' '.join(x).lower() for caption_class in 
                ['caption', 'credit', 'photo-credit', 'image-credit']
            ))
            
            for caption_elem in caption_elements:
                caption_text = caption_elem.get_text(strip=True)
                if caption_text and len(caption_text) < 300 and self._is_meaningful_caption(caption_text):
                    return caption_text
        
        # Safari Rule 5: As last resort, check alt text only if it's clearly meaningful
        # DON'T fall back to filename-like alt text
        img = element.find('img')
        if img:
            alt_text = img.get('alt', '')
            if alt_text and self._is_meaningful_caption(alt_text):
                # Only use alt text if it's clearly descriptive, not a filename
                clean_caption = self._extract_clean_caption_from_alt(alt_text)
                if clean_caption and clean_caption != alt_text:  # Only if we actually cleaned it
                    return clean_caption
        
        # Enhanced: Don't return filename-like captions - better to show nothing
        return None
    
    def _is_meaningful_caption(self, caption: str) -> bool:
        """
        Check if a caption is meaningful to users (not just technical metadata).
        Rejects filenames, URLs, and other technical artifacts.
        """
        
        if not caption or len(caption.strip()) < 3:
            return False
        
        caption = caption.strip()
        
        # Reject obvious filenames
        filename_patterns = [
            r'^\d+_[A-Za-z_]+$',  # Pattern like "257774_Shorted_Trump_Coin_CVirginia"
            r'^[A-Za-z0-9_-]+\.(jpg|jpeg|png|gif|webp|svg)$',  # Image filenames
            r'^IMG_\d+',  # Camera filenames like IMG_1234
            r'^DSC\d+',   # Camera filenames like DSC0123
            r'^[A-Z0-9_]{10,}$',  # Long uppercase/underscore strings (likely IDs)
            r'^\w{8,}-\w{4,}-\w{4,}-\w{4,}-\w{12,}$',  # UUIDs
        ]
        
        for pattern in filename_patterns:
            if re.match(pattern, caption, re.IGNORECASE):
                return False
        
        # Reject URLs
        if caption.startswith(('http://', 'https://', 'www.', '//')):
            return False
        
        # Reject very short technical-looking strings
        if len(caption) < 10 and re.match(r'^[A-Z0-9_-]+$', caption):
            return False
        
        # Reject if it's mostly underscores or hyphens (technical naming)
        underscore_ratio = caption.count('_') / len(caption)
        if underscore_ratio > 0.3:  # More than 30% underscores
            return False
        
        # Reject if it's all uppercase and has no spaces (likely an ID)
        if caption.isupper() and ' ' not in caption and len(caption) > 8:
            return False
        
        # Require some meaningful content indicators for very short captions
        if len(caption) < 20:
            # Must contain some descriptive words or photo credit indicators
            meaningful_indicators = [
                'photo', 'image', 'picture', 'credit', '©', 'getty', 'reuters', 
                'ap images', 'afp', 'via', 'courtesy', 'by', 'from', 'the verge'
            ]
            
            if not any(indicator in caption.lower() for indicator in meaningful_indicators):
                # For short captions, also accept if they contain common words
                common_words = [
                    'the', 'a', 'an', 'and', 'or', 'in', 'on', 'at', 'with', 'for', 'of'
                ]
                if not any(word in caption.lower().split() for word in common_words):
                    return False
        
        # If it passes all checks, it's likely meaningful
        return True
    
    def _extract_visible_caption_text(self, figcaption: Tag) -> Optional[str]:
        """
        Extract visible text from figcaption, filtering out hidden elements.
        Based on Safari Reader Mode visibility logic.
        """
        
        visible_parts = []
        
        # Process each child node to check visibility
        for content in figcaption.contents:
            if hasattr(content, 'strip'):  # Text node
                text = content.strip()
                if text and len(text) > 2:
                    visible_parts.append(text)
            elif hasattr(content, 'name'):  # Element node
                # Skip if element is hidden
                if self._is_element_hidden(content):
                    continue
                    
                text = content.get_text(strip=True)
                if text and len(text) > 2:
                    visible_parts.append(text)
        
        if visible_parts:
            combined = ' '.join(visible_parts).strip()
            # Clean up excessive whitespace
            combined = re.sub(r'\s+', ' ', combined)
            return combined if len(combined) > 5 else None
        
        return None
    
    def _is_element_hidden(self, element: Tag) -> bool:
        """
        Check if element is hidden using Safari Reader Mode visibility logic.
        """
        
        if not element or not hasattr(element, 'name'):
            return False
        
        # Check aria-hidden
        if element.get('aria-hidden') == 'true':
            return True
        
        # Check style attribute for hiding
        style = element.get('style', '').lower()
        if any(hidden_style in style for hidden_style in [
            'display:none', 'display: none',
            'visibility:hidden', 'visibility: hidden',
            'opacity:0', 'opacity: 0'
        ]):
            return True
        
        # Check classes for hiding (common patterns)
        classes = ' '.join(element.get('class', [])).lower()
        if any(hidden_class in classes for hidden_class in [
            'hidden', 'sr-only', 'screen-reader-only', 'visually-hidden',
            'invisible', 'hide', 'off-screen', 'hide-text'
        ]):
            return True
        
        return False
    
    def _extract_clean_caption_from_alt(self, alt_text: str) -> Optional[str]:
        """
        Extract clean caption from verbose alt text using Safari-like patterns.
        Only extracts if we can significantly clean/shorten the text.
        """
        
        if not alt_text or len(alt_text) < 20:
            return None
        
        # Safari Pattern 1: Extract photo credit at the end
        photo_credit_match = re.search(r'\(Photo by [^)]+\)\([^)]+\)$', alt_text)
        if photo_credit_match:
            return photo_credit_match.group(0)
        
        # Safari Pattern 2: Extract copyright notice
        copyright_match = re.search(r'©[^.]*(?:AP Images?|Reuters|Getty|Sipa|AFP)[^.]*$', alt_text, re.IGNORECASE)
        if copyright_match:
            return copyright_match.group(0)
        
        # Safari Pattern 3: If alt text is very long, try to extract essential photo info
        if len(alt_text) > 150:
            # Look for photo credit indicators
            credit_patterns = [
                r'Photo:\s*[^.]+(?:AP Images?|Reuters|Getty|Sipa|AFP)',
                r'Credit:\s*[^.]+(?:AP Images?|Reuters|Getty|Sipa|AFP)',
                r'Image:\s*[^.]+(?:AP Images?|Reuters|Getty|Sipa|AFP)'
            ]
            
            for pattern in credit_patterns:
                match = re.search(pattern, alt_text, re.IGNORECASE)
                if match:
                    return match.group(0).strip()
        
        # Don't return the original verbose alt text
        return None
    
    def _is_byline_element(self, element: Tag) -> bool:
        """
        Detect if an element is a byline/author element.
        Uses Safari Reader Mode patterns and semantic indicators.
        Enhanced to detect simple paragraph-based bylines.
        """
        
        if not element or not hasattr(element, 'name'):
            return False
        
        # Get text content for debugging
        text_content = element.get_text(strip=True)
        
        # Enhanced debug logging for "by " containing elements
        if 'by ' in text_content.lower() and len(text_content) < 100:
            logger.info(f"CHECKING BYLINE: {element.name} element with text: '{text_content}'")
            logger.info(f"  Classes: {element.get('class', [])}")
            logger.info(f"  ID: {element.get('id', '')}")
        
        # Check element classes for author/byline indicators
        classes = ' '.join(element.get('class', [])).lower()
        author_class_patterns = [
            'author', 'byline', 'writer', 'correspondent', 'journalist',
            'credit', 'attribution', 'created-by', 'written-by'
        ]
        
        if any(pattern in classes for pattern in author_class_patterns):
            logger.info(f"  MATCHED class pattern: {classes}")
            return True
        
        # Check element ID for author patterns
        element_id = element.get('id', '').lower()
        if any(pattern in element_id for pattern in author_class_patterns):
            logger.info(f"  MATCHED ID pattern: {element_id}")
            return True
        
        # Check data attributes for author information
        data_attrs = []
        for attr_name in element.attrs:
            if attr_name.startswith('data-'):
                data_attrs.append(attr_name.lower())
                data_attrs.append(str(element.attrs[attr_name]).lower())
        
        data_attr_text = ' '.join(data_attrs)
        if any(pattern in data_attr_text for pattern in author_class_patterns):
            logger.info(f"  MATCHED data attribute pattern: {data_attr_text}")
            return True
        
        # Check text content for byline patterns (but only for small elements)
        if len(text_content) < 200:  # Bylines are typically short
            # Enhanced: Check paragraph elements for simple byline patterns
            if element.name == 'p':
                # Pattern 1: Simple "by Author Name" format (exactly what we found)
                if re.match(r'^by\s+[a-z]+(?:\s+[a-z]+)*$', text_content.lower()):
                    logger.info(f"  MATCHED p tag pattern 1: '{text_content}'")
                    return True
                
                # Pattern 2: "by Author Name" with role/publication
                if re.match(r'^by\s+[a-z]+\s+[a-z]+(?:\s+(?:correspondent|reporter|editor|writer|journalist))?', text_content.lower()):
                    logger.info(f"  MATCHED p tag pattern 2: '{text_content}'")
                    return True
            
            # Enhanced: Check for simple "by Author Name" patterns in ANY element type
            # This catches cases where bylines appear in unexpected element types
            if re.match(r'^by\s+[a-z]+(?:\s+[a-z]+)*$', text_content.lower()):
                # Additional validation: ensure it looks like a real name (not just random words)
                words = text_content.lower().split()[1:]  # Skip "by"
                if len(words) >= 1 and len(words) <= 3:  # 1-3 name parts
                    # Check if words look like names (start with capital, reasonable length)
                    original_words = text_content.split()[1:]  # Get original case
                    if all(word[0].isupper() and 2 <= len(word) <= 20 for word in original_words):
                        logger.info(f"  MATCHED enhanced byline pattern: '{text_content}'")
                        return True
            
            # Look for "By [Name]" patterns (general case)
            if re.match(r'^by\s+[a-z]+\s+[a-z]+', text_content.lower()):
                logger.info(f"  MATCHED general pattern: '{text_content}'")
                return True
            
            # Look for author name patterns with role/affiliation
            byline_content_patterns = [
                r'by\s+[\w\s]+(?:correspondent|reporter|editor|writer)',
                r'[\w\s]+\s+(?:correspondent|reporter|editor|writer)',
                r'by\s+[\w\s]+\s+[\w\s]+\.com',  # "By Name Publication.com"
            ]
            
            for pattern in byline_content_patterns:
                if re.search(pattern, text_content.lower()):
                    logger.info(f"  MATCHED role pattern: '{text_content}' with pattern: {pattern}")
                    return True
        
        # Debug log for cases that don't match
        if 'by ' in text_content.lower() and len(text_content) < 100:
            logger.info(f"  NO MATCH for byline candidate: '{text_content}'")
        
        return False
    
    def _extract_author_from_byline(self, element: Tag) -> Dict[str, Any]:
        """
        Extract clean author information from a byline element.
        Returns dict with display_text and metadata.
        """
        
        full_text = element.get_text(strip=True)
        
        # Initialize result
        result = {
            'display_text': full_text,
            'metadata': {
                'raw_byline': full_text
            }
        }
        
        # Try to extract structured information from child elements
        # Pattern 1: Separate <span> elements (like NHL.com structure)
        spans = element.find_all('span')
        if len(spans) >= 2:
            # First span might be "By", second might be author name
            potential_by = spans[0].get_text(strip=True).lower()
            if potential_by in ['by', 'written by', 'author']:
                author_name = spans[1].get_text(strip=True)
                if author_name:
                    result['metadata']['author_name'] = author_name
                    
                    # Look for role/affiliation in remaining spans or child elements
                    role_elements = element.find_all(['span', 'div'])[2:]  # Skip first two spans
                    if role_elements:
                        role = ' '.join(elem.get_text(strip=True) for elem in role_elements)
                        if role:
                            result['metadata']['author_role'] = role
                            result['display_text'] = f"By {author_name}"
                    else:
                        result['display_text'] = f"By {author_name}"
        
        # Pattern 2: Parse from full text if structured extraction failed
        if 'author_name' not in result['metadata']:
            # Try to extract author name from text patterns
            author_match = re.search(r'^by\s+([\w\s]+?)(?:\s+(?:correspondent|reporter|editor|writer|\.com))', full_text.lower())
            if author_match:
                author_name = author_match.group(1).strip().title()
                result['metadata']['author_name'] = author_name
                result['display_text'] = f"By {author_name}"
            else:
                # Try simpler "By Name Name" pattern
                simple_match = re.search(r'^by\s+([\w\s]+?)(?:\s|$)', full_text.lower())
                if simple_match:
                    potential_name = simple_match.group(1).strip()
                    # Ensure it looks like a name (at least first and last)
                    name_parts = potential_name.split()
                    if len(name_parts) >= 2:
                        author_name = ' '.join(name_parts[:2]).title()  # First two words
                        result['metadata']['author_name'] = author_name
                        result['display_text'] = f"By {author_name}"
        
        # If we still don't have a clean author name, try to clean up the display text
        if 'author_name' not in result['metadata']:
            # Remove common suffixes
            clean_text = re.sub(r'\s+(?:correspondent|reporter|editor|writer).*$', '', full_text, flags=re.IGNORECASE)
            if clean_text != full_text and len(clean_text) < len(full_text):
                result['display_text'] = clean_text.strip()
        
        return result

    def _is_semantic_div(self, element: Tag) -> bool:
        """
        Check if a div element represents semantic content rather than just a container.
        Uses multiple heuristics to avoid processing wrapper divs that would create duplicates.
        """
        
        if not element or element.name != 'div':
            return False
        
        # Rule 1: Skip if this div's content is mostly contained in child elements
        # This prevents processing wrapper divs
        div_text = element.get_text(strip=True)
        
        # Get text from direct content vs. child elements
        child_elements = element.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'span', 'strong', 'em'])
        child_text = ' '.join([child.get_text(strip=True) for child in child_elements])
        
        # If div is very large (>1000 chars), likely a container
        if len(div_text) > 1000:
            return False
        
        # If most content comes from children, this is likely a wrapper
        if len(child_text) > len(div_text) * 0.8:
            return False
        
        # Rule 2: Check for semantic classes/attributes that indicate content
        classes = ' '.join(element.get('class', [])).lower()
        semantic_indicators = [
            'content', 'body', 'text', 'excerpt', 'summary', 'lead',
            'intro', 'description', 'caption', 'note', 'highlight',
            'callout', 'quote', 'aside', 'sidebar-content'
        ]
        
        # Positive indicators
        if any(indicator in classes for indicator in semantic_indicators):
            return True
        
        # Rule 3: Skip container-like classes
        container_indicators = [
            'container', 'wrapper', 'layout', 'grid', 'row', 'col',
            'section', 'main', 'page', 'article-wrapper', 'content-wrapper',
            'inner', 'outer', 'header', 'footer', 'nav', 'sidebar'
        ]
        
        if any(indicator in classes for indicator in container_indicators):
            return False
        
        # Rule 4: Check element attributes for semantic meaning
        element_id = element.get('id', '').lower()
        if any(indicator in element_id for indicator in semantic_indicators):
            return True
        
        # Rule 5: Content length and structure heuristics
        # Very short content is usually not worth a separate block
        if len(div_text) < 30:
            return False
        
        # Very long content with many children is usually a container
        if len(div_text) > 500 and len(element.find_all()) > 10:
            return False
        
        # Rule 6: Check if this div has mostly text content vs. nested elements
        # Count direct text vs. nested element content
        direct_text = []
        for content in element.contents:
            if hasattr(content, 'strip') and content and content.strip():  # Text node
                direct_text.append(content.strip())
        
        direct_text_length = sum(len(text) for text in direct_text)
        
        # If there's substantial direct text content, likely semantic
        if direct_text_length > 50:
            return True
        
        # Rule 7: Default to False for safety (be conservative)
        # Only process divs that clearly pass our semantic tests
        return False

    def _is_twitter_embed(self, element: Tag) -> bool:
        """
        Detect if an element is a Twitter embed.
        Handles both rendered iframes AND original blockquote patterns before JS transformation.
        """
        
        if not element or not hasattr(element, 'name'):
            return False
        
        # Pattern 1: NHL.com style with oc-c-body-part--twitter class (rendered)
        classes = ' '.join(element.get('class', [])).lower()
        if 'twitter' in classes and ('oembed' in classes or 'body-part' in classes):
            return True
        
        # Pattern 2: Direct twitter-tweet container (rendered)
        if 'twitter-tweet' in classes:
            return True
        
        # Pattern 3: Original blockquote with twitter-tweet class (before JS transformation)
        if element.name == 'blockquote' and 'twitter-tweet' in classes:
            return True
        
        # Pattern 4: Check if contains Twitter iframe (fully rendered)
        if element.find('iframe', src=lambda x: x and 'platform.twitter.com/embed' in x):
            return True
        
        # Pattern 5: Check for Twitter embed indicators in children (rendered)
        twitter_indicators = element.find_all(['div', 'iframe'], class_=lambda x: x and any(
            indicator in ' '.join(x).lower() for indicator in ['twitter-tweet', 'twitter-embed']
        ))
        
        if twitter_indicators:
            return True
        
        # Pattern 6: Check if element contains tweet URLs (original state)
        tweet_links = element.find_all('a', href=lambda x: x and (
            'twitter.com/status/' in x or 
            'twitter.com/' in x and '/status/' in x or
            't.co/' in x
        ))
        
        if tweet_links and element.name in ['blockquote', 'div', 'p']:
            # Additional check: ensure it's actually a tweet embed, not just a link
            # Look for Twitter widgets script in the page or tweet-like structure
            if element.name == 'blockquote':
                return True  # Blockquotes with tweet links are likely embeds
            
            # For other elements, be more selective
            if len(tweet_links) == 1 and len(element.get_text(strip=True)) < 300:
                return True  # Short elements with single tweet link
        
        return False
    
    def _extract_twitter_embed_data(self, element: Tag) -> dict:
        """
        Extract Twitter embed metadata from the element.
        Handles both rendered iframes AND original blockquote patterns before JS transformation.
        Returns dict with tweet_id, embed_url, and other metadata.
        """
        
        metadata = {
            'tweet_id': None,
            'embed_url': None,
            'width': None,
            'height': None,
            'embed_type': 'unknown'
        }
        
        # Method 1: Look for iframe with Twitter embed (fully rendered)
        iframe = element.find('iframe', src=lambda x: x and 'platform.twitter.com/embed' in x)
        
        if iframe:
            src = iframe.get('src', '')
            metadata['embed_url'] = src
            metadata['embed_type'] = 'iframe'
            
            # Extract tweet ID from data-tweet-id attribute
            tweet_id = iframe.get('data-tweet-id')
            if tweet_id:
                metadata['tweet_id'] = tweet_id
            else:
                # Fallback: extract tweet ID from URL parameters
                import re
                from urllib.parse import urlparse, parse_qs
                
                try:
                    parsed_url = urlparse(src)
                    query_params = parse_qs(parsed_url.query)
                    if 'id' in query_params:
                        metadata['tweet_id'] = query_params['id'][0]
                except:
                    # If URL parsing fails, try regex
                    tweet_id_match = re.search(r'[&?]id=(\d+)', src)
                    if tweet_id_match:
                        metadata['tweet_id'] = tweet_id_match.group(1)
            
            # Extract dimensions if available
            width = iframe.get('width') or iframe.get('style', '')
            height = iframe.get('height') or iframe.get('style', '')
            
            # Parse width/height from style if present
            if 'width:' in width:
                width_match = re.search(r'width:\s*(\d+)px', width)
                if width_match:
                    metadata['width'] = int(width_match.group(1))
            elif width.replace('px', '').isdigit():
                metadata['width'] = int(width.replace('px', ''))
            
            if 'height:' in height:
                height_match = re.search(r'height:\s*(\d+)px', height)
                if height_match:
                    metadata['height'] = int(height_match.group(1))
            elif height.replace('px', '').isdigit():
                metadata['height'] = int(height.replace('px', ''))
        
        # Method 2: Look for tweet URLs in links (original blockquote pattern)
        else:
            tweet_links = element.find_all('a', href=lambda x: x and (
                'twitter.com/status/' in x or 
                'twitter.com/' in x and '/status/' in x
            ))
            
            if tweet_links:
                # Get the first status link
                status_link = tweet_links[0]
                href = status_link.get('href', '')
                metadata['embed_url'] = href
                metadata['embed_type'] = 'blockquote'
                
                # Extract tweet ID from URL
                import re
                tweet_id_match = re.search(r'twitter\.com/\w+/status/(\d+)', href)
                if tweet_id_match:
                    metadata['tweet_id'] = tweet_id_match.group(1)
                
                # For blockquotes, set default dimensions
                metadata['width'] = 550  # Standard Twitter embed width
                metadata['height'] = 400  # Estimated height
            
            # Method 3: Look for t.co short URLs as fallback
            else:
                tco_links = element.find_all('a', href=lambda x: x and 't.co/' in x)
                if tco_links:
                    tco_link = tco_links[0]
                    href = tco_link.get('href', '')
                    metadata['embed_url'] = href
                    metadata['embed_type'] = 'tco_link'
                    
                    # Can't extract tweet ID from t.co URL, but preserve the link
                    # Tweet ID might be available in other attributes or surrounding context
                    
                    # Look for tweet ID in surrounding context
                    parent_text = element.get_text()
                    tweet_id_match = re.search(r'(\d{15,})', parent_text)  # Tweet IDs are ~19 digits
                    if tweet_id_match:
                        metadata['tweet_id'] = tweet_id_match.group(1)
        
        return metadata

    def _is_twitter_paragraph_duplicate(self, block: ContentBlock) -> bool:
        """
        Check if a paragraph block contains Twitter content that's already been
        properly detected as a Twitter embed block.
        """
        
        content = block.content.lower()
        
        # Pattern 1: Check for Twitter handles and hashtags that suggest this is tweet content
        twitter_indicators = ['@', '#', 'twitter.com', 't.co']
        twitter_count = sum(1 for indicator in twitter_indicators if indicator in content)
        
        # If this paragraph has multiple Twitter indicators, it's likely tweet content
        if twitter_count >= 2:
            return True
        
        # Pattern 2: Check for specific tweet-like content patterns
        tweet_patterns = [
            r'@\w+',  # Twitter handles
            r'#\w+',  # Hashtags
            r'pic\.twitter\.com',  # Twitter image links
            r'twitter\.com/\w+/status',  # Tweet status links
        ]
        
        pattern_matches = 0
        for pattern in tweet_patterns:
            if re.search(pattern, content):
                pattern_matches += 1
        
        # If this paragraph contains multiple tweet patterns, likely duplicate
        if pattern_matches >= 2:
            return True
        
        # Pattern 3: Check for very short paragraphs with Twitter links
        # These are often just the link text without substantial content
        if len(block.content.strip()) < 200 and any(indicator in content for indicator in twitter_indicators):
            # Check if it's mostly just Twitter handles and hashtags
            words = block.content.split()
            twitter_words = [word for word in words if word.startswith('@') or word.startswith('#') or 'twitter' in word.lower()]
            
            # If more than 30% of words are Twitter-related, likely duplicate
            if len(words) > 0 and (len(twitter_words) / len(words)) > 0.3:
                return True
        
        # Pattern 4: Check for paragraphs that are all caps with Twitter handles (likely tweet text)
        # This catches the specific case: "TAGE THOMPSON SCORES THE GOLDEN GOAL AND IS THE HERO FOR TEAM USA!!! @usahockey | @BuffaloSabres"
        if content.isupper() and '@' in content:
            # Count non-whitespace/punctuation characters that are uppercase
            uppercase_chars = sum(1 for char in content if char.isupper())
            total_alpha_chars = sum(1 for char in content if char.isalpha())
            
            # If most alphabetic characters are uppercase AND it contains Twitter handles
            if total_alpha_chars > 0 and (uppercase_chars / total_alpha_chars) > 0.8:
                return True
        
        return False

    def _is_twitter_quote_duplicate(self, block: ContentBlock) -> bool:
        """
        Check if a quote block contains Twitter content that's already been
        properly detected as a Twitter embed block.
        """
        
        content = block.content.lower()
        
        # Pattern 1: Check for Twitter handles and hashtags that suggest this is tweet content
        twitter_indicators = ['@', '#', 'twitter.com', 't.co']
        twitter_count = sum(1 for indicator in twitter_indicators if indicator in content)
        
        # If this quote has multiple Twitter indicators, it's likely tweet content
        if twitter_count >= 2:
            return True
        
        # Pattern 2: Check for specific tweet-like content patterns
        tweet_patterns = [
            r'@\w+',  # Twitter handles
            r'#\w+',  # Hashtags
            r'pic\.twitter\.com',  # Twitter image links
            r'twitter\.com/\w+/status',  # Tweet status links
        ]
        
        pattern_matches = 0
        for pattern in tweet_patterns:
            if re.search(pattern, content):
                pattern_matches += 1
        
        # If this quote contains multiple tweet patterns, likely duplicate
        if pattern_matches >= 2:
            return True
        
        # Pattern 3: Check for very short quotes with Twitter links
        # These are often just the link text without substantial content
        if len(block.content.strip()) < 200 and any(indicator in content for indicator in twitter_indicators):
            # Check if it's mostly just Twitter handles and hashtags
            words = block.content.split()
            twitter_words = [word for word in words if word.startswith('@') or word.startswith('#') or 'twitter' in word.lower()]
            
            # If more than 30% of words are Twitter-related, likely duplicate
            if len(words) > 0 and (len(twitter_words) / len(words)) > 0.3:
                return True
        
        # Pattern 4: Check for quotes that are all caps with Twitter handles (likely tweet text)
        # This catches the specific case: "TAGE THOMPSON SCORES THE GOLDEN GOAL AND IS THE HERO FOR TEAM USA!!! @usahockey | @BuffaloSabres"
        if content.isupper() and '@' in content:
            # Count non-whitespace/punctuation characters that are uppercase
            uppercase_chars = sum(1 for char in content if char.isupper())
            total_alpha_chars = sum(1 for char in content if char.isalpha())
            
            # If most alphabetic characters are uppercase AND it contains Twitter handles
            if total_alpha_chars > 0 and (uppercase_chars / total_alpha_chars) > 0.8:
                return True
        
        return False
    
    def _is_byline_content(self, content: str) -> bool:
        """
        Check if content text matches byline patterns.
        This is a fallback to catch bylines that slipped through element-based detection.
        """
        
        if not content or len(content) > 200:  # Bylines are typically short
            return False
        
        content_lower = content.strip().lower()
        
        # Pattern 1: Simple "by Author Name" format
        if re.match(r'^by\s+[a-z]+(?:\s+[a-z]+)*$', content_lower):
            # Additional validation: ensure it looks like a real name
            words = content.strip().split()[1:]  # Skip "by"
            if len(words) >= 1 and len(words) <= 3:  # 1-3 name parts
                # Check if words look like names (start with capital, reasonable length)
                if all(word[0].isupper() and 2 <= len(word) <= 20 for word in words):
                    return True
        
        # Pattern 2: "by Author Name" with role/publication
        if re.match(r'^by\s+[a-z]+\s+[a-z]+(?:\s+(?:correspondent|reporter|editor|writer|journalist))?', content_lower):
            return True
        
        # Pattern 3: Author name patterns with role/affiliation
        byline_patterns = [
            r'^by\s+[\w\s]+(?:correspondent|reporter|editor|writer)',
            r'^[\w\s]+\s+(?:correspondent|reporter|editor|writer)',
            r'^by\s+[\w\s]+\s+[\w\s]+\.com$',  # "By Name Publication.com"
        ]
        
        for pattern in byline_patterns:
            if re.match(pattern, content_lower):
                return True
        
        return False

    def _is_newsletter_content(self, content: str) -> bool:
        """
        Check if content is a newsletter description that should be filtered out.
        Specifically targets The Verge newsletter descriptions.
        """
        
        if not content or len(content) < 50:  # Newsletter descriptions are usually substantial
            return False
        
        content_lower = content.strip().lower()
        
        # Pattern 1: The Verge "Installer" newsletter specific description
        if ('david pierce' in content_lower and 
            'newsletter' in content_lower and 
            any(keyword in content_lower for keyword in ['download', 'watch', 'read', 'listen', 'explore'])):
            return True
        
        # Pattern 2: General newsletter signup/description patterns
        newsletter_patterns = [
            r'weekly newsletter.*designed to tell you',
            r'newsletter.*everything you need to.*download.*watch.*read',
            r'subscribe.*newsletter.*get.*latest',
            r'newsletter.*deliver.*inbox.*every',
        ]
        
        for pattern in newsletter_patterns:
            if re.search(pattern, content_lower):
                return True
        
        # Pattern 3: The Verge specific newsletter names
        verge_newsletters = [
            'installer', 'command line', 'vergecast', 'decoder', 'hot pod'
        ]
        
        if ('newsletter' in content_lower and 
            any(newsletter in content_lower for newsletter in verge_newsletters) and
            len(content) > 100):  # Substantial newsletter description
            return True
        
        # Pattern 4: Generic newsletter signup language
        newsletter_indicators = [
            'weekly newsletter', 'daily newsletter', 'subscribe', 'unsubscribe',
            'email list', 'mailing list', 'inbox', 'sign up'
        ]
        
        # If content has multiple newsletter indicators and is substantial, likely newsletter content
        indicator_count = sum(1 for indicator in newsletter_indicators if indicator in content_lower)
        if indicator_count >= 2 and len(content) > 150:
            return True
        
        return False

    def _is_pullquote_paragraph(self, paragraph: Tag) -> bool:
        """
        Check if a paragraph is inside a pullquote container.
        Handles The Verge-style pullquotes and other common journalistic patterns.
        """
        
        if not paragraph or paragraph.name != 'p':
            return False
        
        # Method 1: Check if paragraph itself has pullquote classes
        p_classes = ' '.join(paragraph.get('class', [])).lower()
        if 'pullquote' in p_classes or 'pull-quote' in p_classes:
            return True
        
        # Method 2: Check if paragraph is inside a pullquote container (The Verge pattern)
        parent = paragraph.parent
        if parent:
            parent_classes = ' '.join(parent.get('class', [])).lower()
            # The Verge uses "duet--article--article-pullquote" class
            if ('pullquote' in parent_classes or 'pull-quote' in parent_classes or
                'article-pullquote' in parent_classes):
                return True
        
        # Method 3: Check grandparent (sometimes there's a wrapper div)
        grandparent = parent.parent if parent else None
        if grandparent:
            grandparent_classes = ' '.join(grandparent.get('class', [])).lower()
            if ('pullquote' in grandparent_classes or 'pull-quote' in grandparent_classes or
                'article-pullquote' in grandparent_classes):
                return True
        
        # Method 4: Check for semantic attributes that indicate pullquotes
        # Some sites use data attributes or role attributes
        if paragraph.get('role') == 'quote' or paragraph.get('role') == 'pullquote':
            return True
        
        if parent:
            if (parent.get('role') == 'quote' or parent.get('role') == 'pullquote' or
                parent.get('data-type') == 'pullquote' or parent.get('data-component') == 'pullquote'):
                return True
        
        # Method 5: Check for common CSS class patterns used by different news sites
        pullquote_class_patterns = [
            'quote-highlight', 'highlight-quote', 'featured-quote', 'emphasis-quote',
            'callout-quote', 'blockquote-highlight', 'quote-callout', 'standout-quote'
        ]
        
        # Check paragraph classes
        for pattern in pullquote_class_patterns:
            if pattern in p_classes:
                return True
        
        # Check parent classes
        if parent:
            for pattern in pullquote_class_patterns:
                if pattern in parent_classes:
                    return True
        
        return False

    def _is_carousel_container(self, element: Tag) -> bool:
        """
        Check if an element is a carousel container.
        Simplified implementation - currently disabled for complexity reasons.
        """
        return False  # Disabled for now - carousel content is extracted as regular blocks

    def _has_carousel_in_json(self, script_element: Tag) -> bool:
        """
        Check if a JSON script tag contains carousel data.
        Currently disabled.
        """
        return False

    def _process_carousel_content(self, element: Tag, position: int) -> Optional[ContentBlock]:
        """
        Extract and structure carousel content.
        Currently disabled - returns None.
        """
        return None