"""
Intelligent Content Processing Router
Determines optimal processing route based on content complexity analysis.
"""

import re
import logging
from typing import Dict, Any, Tuple
from dataclasses import dataclass
from bs4 import BeautifulSoup
from django.conf import settings

logger = logging.getLogger(__name__)


@dataclass
class ComplexityAnalysis:
    """Content complexity analysis result."""
    overall_score: float  # 0.0-1.0, higher = more complex
    indicators: Dict[str, float]
    recommended_route: str  # 'safari_mode', 'llm_enhanced', 'hybrid'
    confidence: float  # 0.0-1.0, confidence in recommendation
    reasoning: str


class ProcessingRouter:
    """
    Intelligent router for determining optimal content processing strategy.
    """
    
    # Routing thresholds (configurable via settings)
    DEFAULT_LLM_THRESHOLD = 0.6
    DEFAULT_HYBRID_THRESHOLD = 0.8
    
    # Complexity indicators and weights
    COMPLEXITY_INDICATORS = {
        'paywall_content': 0.25,
        'multi_column_layout': 0.20,
        'embedded_media': 0.15,
        'dynamic_content': 0.15,
        'content_noise_ratio': 0.15,
        'source_complexity': 0.10
    }
    
    def __init__(self):
        self.llm_threshold = getattr(settings, 'LLM_ROUTING_THRESHOLD', self.DEFAULT_LLM_THRESHOLD)
        self.hybrid_threshold = getattr(settings, 'HYBRID_ROUTING_THRESHOLD', self.DEFAULT_HYBRID_THRESHOLD)
        
        # Known complex sources (can be configured via settings)
        self.complex_sources = getattr(settings, 'COMPLEX_SOURCES', [
            'wsj.com', 'ft.com', 'economist.com', 'newyorker.com',
            'theatlantic.com', 'harpers.org', 'lrb.co.uk'
        ])
        
        # Known simple sources
        self.simple_sources = getattr(settings, 'SIMPLE_SOURCES', [
            'reuters.com', 'apnews.com', 'bbc.com', 'cnn.com'
        ])
    
    def determine_route(self, article) -> str:
        """
        Determine optimal processing route for an article.
        
        Args:
            article: Article model instance with raw_html
            
        Returns:
            str: 'safari_mode', 'llm_enhanced', or 'hybrid'
        """
        
        if not article.has_raw_content:
            logger.warning(f"Article {article.id} has no raw content for routing analysis")
            return 'safari_mode'  # Default fallback
        
        try:
            # Perform complexity analysis
            analysis = self.analyze_content_complexity(article.raw_html, article)
            
            # Log routing decision
            logger.info(f"Article {article.id} complexity: {analysis.overall_score:.3f}, "
                       f"route: {analysis.recommended_route}, confidence: {analysis.confidence:.3f}")
            
            return analysis.recommended_route
            
        except Exception as e:
            logger.exception(f"Routing analysis failed for article {article.id}: {str(e)}")
            return 'safari_mode'  # Safe fallback
    
    def analyze_content_complexity(self, raw_html: str, article) -> ComplexityAnalysis:
        """
        Analyze content complexity using multiple indicators.
        """
        
        soup = BeautifulSoup(raw_html, 'html.parser')
        indicators = {}
        
        # 1. Paywall content analysis
        indicators['paywall_content'] = self._analyze_paywall_content(raw_html, article)
        
        # 2. Multi-column layout detection
        indicators['multi_column_layout'] = self._detect_complex_layout(soup)
        
        # 3. Embedded media complexity
        indicators['embedded_media'] = self._analyze_embedded_media(soup)
        
        # 4. Dynamic content assessment
        indicators['dynamic_content'] = self._assess_dynamic_content(soup, raw_html)
        
        # 5. Content noise ratio
        indicators['content_noise_ratio'] = self._calculate_noise_ratio(soup)
        
        # 6. Source complexity score
        indicators['source_complexity'] = self._get_source_complexity_score(article)
        
        # Calculate weighted overall score
        overall_score = sum(
            indicators[key] * self.COMPLEXITY_INDICATORS[key]
            for key in self.COMPLEXITY_INDICATORS
        )
        
        # Determine recommended route
        route, confidence, reasoning = self._determine_route_from_score(overall_score, indicators)
        
        return ComplexityAnalysis(
            overall_score=overall_score,
            indicators=indicators,
            recommended_route=route,
            confidence=confidence,
            reasoning=reasoning
        )
    
    def _analyze_paywall_content(self, raw_html: str, article) -> float:
        """
        Analyze paywall-related complexity (0.0-1.0).
        Higher score = more likely to need LLM processing.
        """
        
        score = 0.0
        
        # Check if paywall was detected in Step 1
        if hasattr(article, 'paywall_detected') and article.paywall_detected:
            score += 0.4
            
            # Check number of paywall indicators
            if hasattr(article, 'paywall_indicators'):
                indicator_count = len(article.paywall_indicators)
                score += min(0.3, indicator_count * 0.1)
        
        # Check for paywall-specific content patterns
        html_lower = raw_html.lower()
        paywall_patterns = [
            r'subscription.*required',
            r'premium.*content',
            r'subscriber.*only',
            r'continue.*reading',
            r'unlock.*full.*article',
            r'sign.*in.*to.*read',
            r'become.*a.*member'
        ]
        
        for pattern in paywall_patterns:
            if re.search(pattern, html_lower):
                score += 0.1
        
        # Check for truncated content indicators
        truncation_patterns = [
            r'\.{3,}',  # Multiple dots
            r'read.*more',
            r'continue.*below',
            r'\[.*continued.*\]'
        ]
        
        for pattern in truncation_patterns:
            if re.search(pattern, html_lower):
                score += 0.05
        
        return min(1.0, score)
    
    def _detect_complex_layout(self, soup: BeautifulSoup) -> float:
        """
        Detect complex multi-column or dynamic layouts (0.0-1.0).
        """
        
        score = 0.0
        
        # Check for CSS Grid/Flexbox indicators
        grid_indicators = soup.find_all(attrs={'class': re.compile(r'grid|flex|column', re.I)})
        if len(grid_indicators) > 5:
            score += 0.3
        
        # Check for multiple content sections
        content_sections = soup.find_all(['section', 'article', 'div'], 
                                       attrs={'class': re.compile(r'content|article|main', re.I)})
        if len(content_sections) > 3:
            score += 0.2
        
        # Check for sidebar/aside elements
        sidebars = soup.find_all(['aside', 'div'], 
                                attrs={'class': re.compile(r'sidebar|aside|related', re.I)})
        if len(sidebars) > 2:
            score += 0.2
        
        # Check for complex navigation
        nav_elements = soup.find_all(['nav', 'div'], 
                                   attrs={'class': re.compile(r'nav|menu|breadcrumb', re.I)})
        if len(nav_elements) > 3:
            score += 0.1
        
        # Check for overlay/modal content
        overlays = soup.find_all(attrs={'class': re.compile(r'modal|overlay|popup|lightbox', re.I)})
        if len(overlays) > 0:
            score += 0.2
        
        return min(1.0, score)
    
    def _analyze_embedded_media(self, soup: BeautifulSoup) -> float:
        """
        Analyze embedded media complexity (0.0-1.0).
        """
        
        score = 0.0
        
        # Count different types of embedded content
        iframes = soup.find_all('iframe')
        videos = soup.find_all('video')
        embeds = soup.find_all('embed')
        objects = soup.find_all('object')
        
        total_embeds = len(iframes) + len(videos) + len(embeds) + len(objects)
        
        if total_embeds > 0:
            score += min(0.4, total_embeds * 0.1)
        
        # Check for social media embeds
        social_patterns = [
            r'twitter\.com',
            r'instagram\.com',
            r'facebook\.com',
            r'youtube\.com',
            r'vimeo\.com',
            r'tiktok\.com'
        ]
        
        for iframe in iframes:
            src = iframe.get('src', '')
            for pattern in social_patterns:
                if re.search(pattern, src, re.I):
                    score += 0.1
                    break
        
        # Check for interactive content
        interactive_elements = soup.find_all(attrs={'class': re.compile(r'interactive|chart|graph|widget', re.I)})
        if len(interactive_elements) > 0:
            score += min(0.3, len(interactive_elements) * 0.1)
        
        return min(1.0, score)
    
    def _assess_dynamic_content(self, soup: BeautifulSoup, raw_html: str) -> float:
        """
        Assess dynamic/JavaScript-dependent content (0.0-1.0).
        """
        
        score = 0.0
        
        # Count script tags
        scripts = soup.find_all('script')
        if len(scripts) > 10:
            score += 0.3
        elif len(scripts) > 5:
            score += 0.2
        
        # Check for JavaScript frameworks
        js_frameworks = [
            r'react', r'angular', r'vue', r'ember',
            r'backbone', r'knockout', r'jquery'
        ]
        
        html_lower = raw_html.lower()
        for framework in js_frameworks:
            if re.search(framework, html_lower):
                score += 0.1
        
        # Check for AJAX/dynamic loading indicators
        dynamic_patterns = [
            r'data-.*url',
            r'lazy.*load',
            r'infinite.*scroll',
            r'load.*more',
            r'ajax'
        ]
        
        for pattern in dynamic_patterns:
            if re.search(pattern, html_lower):
                score += 0.05
        
        # Check for empty content containers (likely filled by JS)
        empty_containers = soup.find_all(['div', 'section'], 
                                       attrs={'class': re.compile(r'content|article|main', re.I)})
        empty_count = sum(1 for container in empty_containers if len(container.get_text(strip=True)) < 50)
        
        if empty_count > 2:
            score += 0.2
        
        return min(1.0, score)
    
    def _calculate_noise_ratio(self, soup: BeautifulSoup) -> float:
        """
        Calculate content-to-noise ratio (0.0-1.0).
        Higher score = more noise, needs better processing.
        """
        
        # Get total text content
        total_text = soup.get_text(strip=True)
        total_length = len(total_text)
        
        if total_length == 0:
            return 1.0  # All noise, no content
        
        # Calculate noise from various sources
        noise_length = 0
        
        # Navigation noise
        nav_elements = soup.find_all(['nav', 'header', 'footer'])
        for element in nav_elements:
            noise_length += len(element.get_text(strip=True))
        
        # Advertisement noise
        ad_elements = soup.find_all(attrs={'class': re.compile(r'ad|advertisement|banner|promo', re.I)})
        for element in ad_elements:
            noise_length += len(element.get_text(strip=True))
        
        # Social/sharing noise
        social_elements = soup.find_all(attrs={'class': re.compile(r'social|share|follow', re.I)})
        for element in social_elements:
            noise_length += len(element.get_text(strip=True))
        
        # Comment noise
        comment_elements = soup.find_all(attrs={'class': re.compile(r'comment|discussion', re.I)})
        for element in comment_elements:
            noise_length += len(element.get_text(strip=True))
        
        # Calculate noise ratio
        noise_ratio = noise_length / total_length
        
        return min(1.0, noise_ratio)
    
    def _get_source_complexity_score(self, article) -> float:
        """
        Get complexity score based on known source characteristics (0.0-1.0).
        """
        
        if not hasattr(article, 'source_name') or not article.source_name:
            return 0.5  # Unknown source, medium complexity
        
        source_name = article.source_name.lower()
        
        # Check against known complex sources
        for complex_source in self.complex_sources:
            if complex_source.lower() in source_name:
                return 0.8
        
        # Check against known simple sources
        for simple_source in self.simple_sources:
            if simple_source.lower() in source_name:
                return 0.2
        
        # Default for unknown sources
        return 0.5
    
    def _determine_route_from_score(self, overall_score: float, indicators: Dict[str, float]) -> Tuple[str, float, str]:
        """
        Determine processing route from complexity score.
        
        Returns:
            Tuple of (route, confidence, reasoning)
        """
        
        # Determine route based on thresholds
        if overall_score >= self.hybrid_threshold:
            route = 'hybrid'
            confidence = min(1.0, (overall_score - self.hybrid_threshold) / (1.0 - self.hybrid_threshold))
        elif overall_score >= self.llm_threshold:
            route = 'llm_enhanced'
            confidence = min(1.0, (overall_score - self.llm_threshold) / (self.hybrid_threshold - self.llm_threshold))
        else:
            route = 'algorithmic'
            confidence = min(1.0, (self.llm_threshold - overall_score) / self.llm_threshold)
        
        # Generate reasoning
        top_indicators = sorted(indicators.items(), key=lambda x: x[1], reverse=True)[:3]
        reasoning_parts = []
        
        for indicator, score in top_indicators:
            if score > 0.3:
                reasoning_parts.append(f"{indicator}: {score:.2f}")
        
        reasoning = f"Score: {overall_score:.3f}. Top factors: {', '.join(reasoning_parts)}"
        
        return route, confidence, reasoning
    
    def update_thresholds(self, llm_threshold: float = None, hybrid_threshold: float = None):
        """
        Update routing thresholds for dynamic optimization.
        """
        
        if llm_threshold is not None:
            self.llm_threshold = max(0.0, min(1.0, llm_threshold))
            logger.info(f"Updated LLM threshold to {self.llm_threshold}")
        
        if hybrid_threshold is not None:
            self.hybrid_threshold = max(0.0, min(1.0, hybrid_threshold))
            logger.info(f"Updated hybrid threshold to {self.hybrid_threshold}")
    
    def get_routing_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about routing decisions for optimization.
        """
        
        from apps.articles.models import Article
        from django.db.models import Count, Avg, Q
        from datetime import timedelta
        from django.utils import timezone
        
        # Get stats for last 24 hours
        since = timezone.now() - timedelta(hours=24)
        
        stats = Article.objects.filter(
            last_process_attempt__gte=since,
            process_route__isnull=False
        ).aggregate(
            total_processed=Count('id'),
            safari_mode_count=Count('id', filter=Q(process_route='safari_mode')),
            llm_enhanced_count=Count('id', filter=Q(process_route='llm_enhanced')),
            hybrid_count=Count('id', filter=Q(process_route='hybrid')),
            avg_quality_safari=Avg('content_quality_metrics__overall_score', 
                                 filter=Q(process_route='safari_mode')),
            avg_quality_llm=Avg('content_quality_metrics__overall_score', 
                              filter=Q(process_route='llm_enhanced')),
            avg_quality_hybrid=Avg('content_quality_metrics__overall_score', 
                                 filter=Q(process_route='hybrid'))
        )
        
        # Calculate percentages
        total = stats['total_processed'] or 0
        if total > 0:
            stats['safari_mode_percentage'] = (stats['safari_mode_count'] / total) * 100
            stats['llm_enhanced_percentage'] = (stats['llm_enhanced_count'] / total) * 100
            stats['hybrid_percentage'] = (stats['hybrid_count'] / total) * 100
        
        stats['current_thresholds'] = {
            'llm_threshold': self.llm_threshold,
            'hybrid_threshold': self.hybrid_threshold
        }
        
        return stats 