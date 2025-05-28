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
    """Result of algorithmic processing."""
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
            
            # Store article metadata for title comparison
            self._current_article_metadata = article_metadata or {}
            
            if len(raw_html.strip()) < 100:
                return ProcessingResult(
                    success=False,
                    error_message="HTML content too short for processing",
                    processing_time_ms=int((time.time() - start_time) * 1000)
                )
            
            # Parse HTML with error handling
            try:
                soup = BeautifulSoup(raw_html, 'html.parser')
                if not soup or not soup.find():
                    return ProcessingResult(
                        success=False,
                        error_message="Failed to parse HTML content",
                        processing_time_ms=int((time.time() - start_time) * 1000)
                    )
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
        
        # Process elements in order, but exclude recommendation/widget sections
        for element in main_element.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'blockquote', 'ul', 'ol', 'img', 'video', 'figure', 'div', 'section', 'article']):
            
            # Skip if this element or its parents should be excluded
            if self._should_skip_element_for_content_blocks(element):
                continue
            
            # Only process content-relevant elements
            if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'blockquote', 'ul', 'ol', 'img', 'video', 'figure']:
                block = self._element_to_content_block(element, position)
                if block and self._is_unique_content_block(block, seen_content, seen_images):
                    blocks.append(block)
                    position += 1
        
        return blocks
    
    def _should_skip_element_for_content_blocks(self, element: Tag) -> bool:
        """
        Determine if an element should be skipped when creating content blocks.
        Check both the element itself and its ancestors to ensure elements within
        excluded sections (like Page-below) are properly filtered out.
        """
        
        # Check the element itself
        if self._should_exclude_section(element):
            return True
        
        # Check all ancestors up to reasonable depth to catch elements within excluded sections
        current = element.parent
        depth = 0
        max_depth = 10  # Go deeper to catch elements within excluded sections
        
        while current and current.name not in ['body', 'html'] and depth < max_depth:
            if self._should_exclude_section(current):
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
        
        # Handle different element types
        if block_type in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
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
            metadata['alt'] = element.get('alt', '')
            metadata['caption'] = element.get('title') or element.get('alt', '')
            content = metadata['alt'] or "Image"
            
        elif block_type == 'figure':
            block_type = 'figure' 
            # Extract image and caption from figure
            img = element.find('img')
            if img and self._is_content_image(img):
                metadata['src'] = self._extract_image_url(img)
                metadata['alt'] = img.get('alt', '')
                
                # Look for figcaption
                figcaption = element.find('figcaption')
                if figcaption:
                    metadata['caption'] = figcaption.get_text(strip=True)
                    content = metadata['caption']
                else:
                    metadata['caption'] = img.get('alt', '')
                    content = metadata['alt'] or "Figure"
            else:
                return None  # Figure without valid image
                
        elif block_type == 'video':
            block_type = 'video'
            metadata['src'] = element.get('src')
            content = "Video content"
            
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
        Assess content quality using Safari-inspired metrics.
        """
        
        scores = {}
        
        # Safari score-based quality (0.0-1.0)
        if candidate.final_score >= self.MIN_SCORE_THRESHOLD * 2:
            scores['safari_score'] = 1.0
        elif candidate.final_score >= self.MIN_SCORE_THRESHOLD:
            scores['safari_score'] = 0.8
        else:
            scores['safari_score'] = 0.6
        
        # Score density quality (0.0-1.0)
        if candidate.score_density >= self.MIN_SCORE_DENSITY * 2:
            scores['density'] = 1.0
        elif candidate.score_density >= self.MIN_SCORE_DENSITY:
            scores['density'] = 0.8
        else:
            scores['density'] = 0.6
        
        # Content completeness (0.0-1.0)
        word_count = metadata.get('word_count', 0)
        if word_count >= 500:
            scores['completeness'] = 1.0
        elif word_count >= 200:
            scores['completeness'] = word_count / 500
        else:
            scores['completeness'] = 0.4
        
        # Structure quality (0.0-1.0)
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
        
        # Weighted overall score
        overall_score = (
            scores['safari_score'] * 0.3 +
            scores['density'] * 0.25 +
            scores['completeness'] * 0.25 +
            scores['structure'] * 0.2
        )
        
        return round(overall_score, 3)

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
        
        # Process prepended elements first
        for sibling in prepended_elements:
            for element in sibling.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'blockquote', 'ul', 'ol', 'img', 'video', 'figure']):
                # Skip if this element or its parents should be excluded
                if self._should_skip_element_for_content_blocks(element):
                    continue
                    
                block = self._element_to_content_block(element, position)
                if block and self._is_unique_content_block(block, seen_content, seen_images):
                    blocks.append(block)
                    position += 1
        
        # Process main content
        for element in main_element.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'blockquote', 'ul', 'ol', 'img', 'video', 'figure']):
            # Skip if this element or its parents should be excluded
            if self._should_skip_element_for_content_blocks(element):
                continue
                
            block = self._element_to_content_block(element, position)
            if block and self._is_unique_content_block(block, seen_content, seen_images):
                blocks.append(block)
                position += 1
        
        # Process appended elements
        for sibling in appended_elements:
            for element in sibling.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'blockquote', 'ul', 'ol', 'img', 'video', 'figure']):
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
        Determine if an image is content-relevant (not decoration/icon).
        Based on Safari's image filtering logic but more inclusive.
        Focus on basic filtering since section-level filtering should handle most cases.
        Enhanced to handle modern responsive images using srcset.
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
            'footer', 'header', 'nav', 'sidebar', 'widget'
        ]
        
        if any(pattern in image_url for pattern in non_content_patterns):
            return False
        
        # Check for specific problematic paths
        if any(path in image_url for path in ['/dr/resources/', '/assets/icons/', '/static/icons/']):
            return False
        
        # Check alt text for basic content indicators
        alt = img_element.get('alt', '').lower()
        
        # If alt text is substantial, likely content
        if len(alt) > 10:
            return True
        
        # Check for decorative alt patterns
        if alt in ['', 'image', 'photo', 'picture'] or any(pattern in alt for pattern in ['icon', 'logo']):
            # Don't immediately exclude - check other factors for modern images
            pass
        
        # Check dimensions if available
        width = img_element.get('width')
        height = img_element.get('height')
        if width and height:
            try:
                w, h = int(width), int(height)
                # Skip very small images (likely icons)
                if w < 30 or h < 30:
                    return False
                # Content images are usually reasonably sized
                if w > 80 and h > 80:
                    return True
            except ValueError:
                pass
        
        # Enhanced: Check for modern responsive image attributes
        # Images with srcset and proper dimensions are likely content
        if srcset and width and height:
            try:
                w, h = int(width), int(height)
                if w >= 300 and h >= 200:  # Reasonable content image size
                    return True
            except ValueError:
                pass
        
        # Check for loading attributes (modern content images often have these)
        loading = img_element.get('loading', '').lower()
        fetchpriority = img_element.get('fetchpriority', '').lower()
        if loading in ['eager', 'lazy'] or fetchpriority in ['high']:
            # These are typically used for content images
            return True
        
        # Check CSS classes for content indicators
        img_classes = ' '.join(img_element.get('class', [])).lower()
        if any(pattern in img_classes for pattern in ['content', 'article', 'story', 'featured', 'main']):
            return True
        if any(pattern in img_classes for pattern in ['icon', 'logo', 'avatar', 'sprite', 'newsletter', 'signup']):
            return False
        
        # Check parent context
        parent = img_element.parent
        if parent:
            parent_class = ' '.join(parent.get('class', [])).lower()
            if any(pattern in parent_class for pattern in ['content', 'article', 'story', 'figure', 'main']):
                return True
            if any(pattern in parent_class for pattern in ['nav', 'header', 'footer', 'sidebar', 'ad', 'menu', 'newsletter', 'signup']):
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
        
        # Enhanced: For modern responsive images, be more inclusive
        # If image has proper dimensions and isn't obviously decorative, include it
        if srcset and width and height:
            try:
                w, h = int(width), int(height)
                if w >= 200 and h >= 150:  # Lower threshold for responsive images
                    return True
            except ValueError:
                pass
        
        # Default to include if uncertain - section filtering should handle the rest
        return True
    
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
                        # Store link metadata for frontend processing
                        if href.startswith('http'):
                            links_metadata.append({
                                'text': link_text,
                                'href': href
                            })
                            # Add placeholder text and URL for frontend to process
                            result.append(f"{link_text} [{href}]")
                        else:
                            result.append(link_text)  # Relative links without URL
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
        Enhanced to catch images with different type classifications.
        """
        
        # Create a normalized content fingerprint for all blocks
        content_text = block.content.strip().lower()
        content_fingerprint = re.sub(r'\s+', ' ', content_text)  # Normalize whitespace
        content_fingerprint = re.sub(r'[^\w\s]', '', content_fingerprint)  # Remove punctuation
        
        # For image/media content with src, prioritize URL-based deduplication
        if block.metadata and block.metadata.get('src'):
            image_src = block.metadata.get('src', '')
            # Normalize the image URL (remove query parameters)
            normalized_src = re.sub(r'\?.*$', '', image_src)
            if normalized_src in seen_images:
                return False
            seen_images.add(normalized_src)
        
        # For all content, check text-based similarity
        # Use first 100 characters as fingerprint
        text_fingerprint = content_fingerprint[:100]
        
        if text_fingerprint in seen_content:
            return False
        seen_content.add(text_fingerprint)
        
        return True
    
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
        """Check if the heading is a duplicate of the article title."""
        # Remove common publication name patterns
        heading = re.sub(r'\s*[-|–—]\s*.+(?:Post|Times|News|CNN|BBC|Reuters|AP|NPR|Fox|NBC|CBS|ABC).*$', '', heading, flags=re.IGNORECASE)
        article_title = re.sub(r'\s*[-|–—]\s*.+(?:Post|Times|News|CNN|BBC|Reuters|AP|NPR|Fox|NBC|CBS|ABC).*$', '', article_title, flags=re.IGNORECASE)
        return heading.strip().lower() == article_title.strip().lower()

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