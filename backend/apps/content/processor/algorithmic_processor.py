"""
Algorithmic Content Processor
Implementation based on WebKit's ReaderArticleFinder algorithm.
Provides Safari Reader Mode-like content extraction without LLM dependency.
"""

import re
import logging
from typing import Any, Dict

from bs4 import BeautifulSoup
import html

from .algorithmic_methods import AlgorithmicProcessorMethods
from .models import ProcessingResult

logger = logging.getLogger(__name__)


class AlgorithmicProcessor(AlgorithmicProcessorMethods):
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
                    processing_time_ms=int((time.time() - start_time) * 1000),
                    route_used="safari_mode_failed"
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
                    processing_time_ms=int((time.time() - start_time) * 1000),
                    route_used="safari_mode_failed"
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
                            processing_time_ms=int((time.time() - start_time) * 1000),
                            route_used="safari_mode_failed"
                        )
                else:
                    logger.info("Successfully decoded and parsed HTML with entity decoding")
                
                # Store soup reference for section delimiter detection
                self._current_soup = soup
                
            except Exception as e:
                return ProcessingResult(
                    success=False,
                    error_message=f"HTML parsing error: {str(e)}",
                    processing_time_ms=int((time.time() - start_time) * 1000),
                    route_used="safari_mode_failed"
                )
            
            # 1. Find candidate elements using Safari algorithm
            candidates = self._find_candidate_elements(soup)
            
            if not candidates:
                return ProcessingResult(
                    success=False,
                    error_message="No viable candidate elements found",
                    processing_time_ms=int((time.time() - start_time) * 1000),
                    route_used="safari_mode_failed"
                )
            
            # 2. Score candidates using Safari's scoring system
            scored_candidates = self._score_candidates(candidates, soup)
            
            # 3. Select best candidate using advantage gap analysis
            best_candidate = self._select_best_candidate(scored_candidates)
            
            if not best_candidate:
                return ProcessingResult(
                    success=False,
                    error_message="No candidate met minimum score requirements",
                    processing_time_ms=int((time.time() - start_time) * 1000),
                    route_used="safari_mode_failed"
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
                    processing_time_ms=processing_time,
                    route_used="safari_mode_failed"
                )
            
            return ProcessingResult(
                success=True,
                clean_content=clean_content,
                content_blocks=content_blocks or [],
                extracted_metadata=extracted_metadata or {},
                quality_score=quality_score,
                processing_time_ms=processing_time,
                route_used="safari_mode"
            )
            
        except Exception as e:
            logger.exception(f"Algorithmic processing failed: {str(e)}")
            return ProcessingResult(
                success=False,
                error_message=str(e),
                processing_time_ms=int((time.time() - start_time) * 1000),
                route_used="safari_mode_failed"
            )
    
