"""
Content Quality Assessment Service
Centralized quality evaluation for processed articles across all processing routes.
Implements progressive content rendering strategy quality metrics.
"""

import re
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class QualityMetrics:
    """Comprehensive quality assessment results."""
    # Overall scores (0.0-1.0)
    quality_score: float
    content_case: str  # 'full', 'partial', 'minimal', 'failed'
    estimated_completeness: int  # 0-100%
    
    # Detailed metrics
    content_length: int
    paragraph_count: int
    heading_count: int
    block_count: int
    word_count: int
    
    # Structure quality indicators
    structure_score: float
    readability_score: float
    noise_removal_score: float
    
    # Missing content indicators
    missing_elements: List[str]
    paywall_indicators: List[str]
    
    # Processing metadata
    processing_route: str
    assessment_timestamp: datetime
    
    # Quality breakdown for debugging
    score_breakdown: Dict[str, float]


@dataclass
class ContentBlock:
    """Content block for quality assessment (simplified version)."""
    type: str
    content: str
    metadata: Dict[str, Any] = None


class QualityAssessmentService:
    """
    Centralized quality assessment service for all content processing routes.
    Used by algorithmic, LLM, and hybrid processors.
    """
    
    # Quality thresholds for progressive rendering
    FULL_CONTENT_THRESHOLD = 0.9      # ≥90% = complete article
    PARTIAL_CONTENT_THRESHOLD = 0.5   # 50-89% = partial content  
    MINIMAL_CONTENT_THRESHOLD = 0.3   # 30-49% = minimal content
    # <30% = failed (don't list)
    
    # Content analysis patterns
    PAYWALL_INDICATORS = [
        'subscribe', 'subscription', 'premium', 'member', 'paywall',
        'login required', 'continue reading', 'full article',
        'register to read', 'unlock story', 'subscriber'
    ]
    
    NOISE_PATTERNS = re.compile(
        r'advertisement|newsletter|signup|cookie|gdpr|privacy|'
        r'social.*media|follow.*us|share.*story|related.*articles',
        re.IGNORECASE
    )
    
    def __init__(self):
        self.assessment_cache = {}
    
    def assess_content_quality(
        self, 
        clean_content: str,
        content_blocks: List[ContentBlock],
        raw_html: str = "",
        processing_route: str = "unknown",
        article_metadata: Dict[str, Any] = None
    ) -> QualityMetrics:
        """
        Comprehensive quality assessment for processed content.
        Used by all processing routes (algorithmic, LLM, hybrid).
        """
        
        article_metadata = article_metadata or {}
        
        # Core content metrics
        content_length = len(clean_content.strip())
        word_count = len(clean_content.split())
        paragraph_count = len([b for b in content_blocks if b.type == 'paragraph'])
        heading_count = len([b for b in content_blocks if b.type == 'heading'])
        block_count = len(content_blocks)
        
        # Calculate component scores
        completeness_score = self._assess_content_completeness(
            clean_content, content_blocks, raw_html
        )
        structure_score = self._assess_content_structure(
            content_blocks, paragraph_count, heading_count
        )
        readability_score = self._assess_readability(clean_content)
        noise_removal_score = self._assess_noise_removal(clean_content, raw_html)
        
        # Identify missing elements and paywall indicators
        missing_elements = self._identify_missing_elements(content_blocks, clean_content)
        paywall_indicators = self._detect_paywall_indicators(raw_html, clean_content)
        
        # Calculate overall quality score with weighted components
        score_breakdown = {
            'completeness': completeness_score * 0.4,  # 40% weight
            'structure': structure_score * 0.25,       # 25% weight  
            'readability': readability_score * 0.2,    # 20% weight
            'noise_removal': noise_removal_score * 0.15  # 15% weight
        }
        
        # Apply penalties for significant issues
        penalty = 0.0
        if len(paywall_indicators) > 2:
            penalty += 0.1
        if word_count < 100:
            penalty += 0.15
        if len(missing_elements) > 3:
            penalty += 0.05
            
        overall_score = max(0.0, min(1.0, sum(score_breakdown.values()) - penalty))
        
        # Determine content case for progressive rendering
        content_case = self._determine_content_case(overall_score)
        estimated_completeness = min(100, int(overall_score * 100))
        
        return QualityMetrics(
            quality_score=round(overall_score, 3),
            content_case=content_case,
            estimated_completeness=estimated_completeness,
            content_length=content_length,
            paragraph_count=paragraph_count,
            heading_count=heading_count,
            block_count=block_count,
            word_count=word_count,
            structure_score=round(structure_score, 3),
            readability_score=round(readability_score, 3),
            noise_removal_score=round(noise_removal_score, 3),
            missing_elements=missing_elements,
            paywall_indicators=paywall_indicators,
            processing_route=processing_route,
            assessment_timestamp=datetime.now(),
            score_breakdown=score_breakdown
        )
    
    def _assess_content_completeness(
        self, 
        clean_content: str, 
        content_blocks: List[ContentBlock],
        raw_html: str
    ) -> float:
        """
        Assess how complete the extracted content appears to be.
        """
        
        content_length = len(clean_content.strip())
        block_diversity = len(set(b.type for b in content_blocks))
        
        # Length-based scoring (logarithmic scale)
        if content_length >= 3000:  # Long-form article
            length_score = 1.0
        elif content_length >= 1500:  # Medium article  
            length_score = 0.8
        elif content_length >= 500:   # Short article
            length_score = 0.6
        elif content_length >= 200:   # Very short
            length_score = 0.4
        else:
            length_score = 0.2
        
        # Diversity bonus (different content types indicate completeness)
        diversity_bonus = min(0.2, block_diversity * 0.05)
        
        # Truncation detection
        truncation_penalty = 0.0
        if any(indicator in clean_content.lower() for indicator in [
            'continue reading', 'read more', 'full story', '...'
        ]):
            truncation_penalty = 0.15
        
        return max(0.0, min(1.0, length_score + diversity_bonus - truncation_penalty))
    
    def _assess_content_structure(
        self, 
        content_blocks: List[ContentBlock],
        paragraph_count: int,
        heading_count: int
    ) -> float:
        """
        Assess the structural quality of the content.
        """
        
        structure_score = 0.0
        
        # Paragraph structure (40% of structure score)
        if paragraph_count >= 5:
            structure_score += 0.4
        elif paragraph_count >= 3:
            structure_score += 0.3
        elif paragraph_count >= 1:
            structure_score += 0.2
        
        # Heading structure (30% of structure score)
        if heading_count >= 3:
            structure_score += 0.3
        elif heading_count >= 1:
            structure_score += 0.2
        
        # Content diversity (30% of structure score)
        block_types = set(b.type for b in content_blocks)
        diversity_score = min(0.3, len(block_types) * 0.1)
        structure_score += diversity_score
        
        return min(1.0, structure_score)
    
    def _assess_readability(self, clean_content: str) -> float:
        """
        Assess content readability using simple heuristics.
        """
        
        if not clean_content.strip():
            return 0.0
        
        words = clean_content.split()
        sentences = re.split(r'[.!?]+', clean_content)
        
        if not words or not sentences:
            return 0.0
        
        # Average sentence length (ideal: 15-20 words)
        avg_sentence_length = len(words) / len(sentences)
        sentence_score = max(0.0, 1.0 - abs(avg_sentence_length - 17.5) / 25)
        
        # Paragraph breaks (good readability has regular breaks)
        paragraph_breaks = clean_content.count('\n\n')
        text_length = len(clean_content)
        break_density = paragraph_breaks / (text_length / 500) if text_length > 0 else 0
        break_score = min(1.0, break_density)
        
        # Excessive capitalization penalty
        caps_ratio = sum(1 for c in clean_content if c.isupper()) / len(clean_content)
        caps_penalty = max(0.0, (caps_ratio - 0.05) * 2) if caps_ratio > 0.05 else 0.0
        
        readability = (sentence_score * 0.6 + break_score * 0.4) - caps_penalty
        return max(0.0, min(1.0, readability))
    
    def _assess_noise_removal(self, clean_content: str, raw_html: str) -> float:
        """
        Assess how well noise was removed from the content.
        """
        
        if not clean_content or not raw_html:
            return 0.5  # Default score when can't assess
        
        # Check for remaining noise patterns in clean content
        noise_matches = len(self.NOISE_PATTERNS.findall(clean_content))
        content_words = len(clean_content.split())
        
        if content_words == 0:
            return 0.0
        
        noise_ratio = noise_matches / content_words
        noise_score = max(0.0, 1.0 - (noise_ratio * 10))  # Penalize noise heavily
        
        # Bonus for good content-to-HTML ratio
        html_size = len(raw_html)
        content_size = len(clean_content)
        
        if html_size > 0:
            extraction_ratio = content_size / html_size
            # Good extraction ratios are typically 0.05-0.15 for news articles
            if 0.05 <= extraction_ratio <= 0.15:
                ratio_bonus = 0.1
            else:
                ratio_bonus = 0.0
        else:
            ratio_bonus = 0.0
        
        return min(1.0, noise_score + ratio_bonus)
    
    def _identify_missing_elements(
        self, 
        content_blocks: List[ContentBlock], 
        clean_content: str
    ) -> List[str]:
        """
        Identify types of content that might be missing.
        """
        
        missing = []
        
        # Check for content types present
        block_types = set(b.type for b in content_blocks)
        content_lower = clean_content.lower()
        
        # Missing media
        if 'image' not in block_types and any(word in content_lower for word in [
            'photo', 'picture', 'image', 'chart', 'graph', 'illustration'
        ]):
            missing.append('images')
        
        if 'video' not in block_types and any(word in content_lower for word in [
            'video', 'watch', 'footage', 'clip'
        ]):
            missing.append('videos')
        
        # Missing social media embeds
        if any(platform in content_lower for platform in ['twitter', 'tweet', 'instagram']):
            if not any('twitter' in str(b.metadata) for b in content_blocks):
                missing.append('social_media_embeds')
        
        # Missing quotes/interviews
        if any(word in content_lower for word in ['said', 'told', 'according to', 'interview']):
            if 'quote' not in block_types:
                missing.append('quotes')
        
        # Very short content suggests missing sections
        if len(content_blocks) < 5:
            missing.append('full_content')
        
        return missing
    
    def _detect_paywall_indicators(self, raw_html: str, clean_content: str) -> List[str]:
        """
        Detect indicators that content might be behind a paywall.
        """
        
        indicators = []
        combined_text = (raw_html + ' ' + clean_content).lower()
        
        for indicator in self.PAYWALL_INDICATORS:
            if indicator in combined_text:
                indicators.append(indicator)
        
        # Additional paywall detection patterns
        if re.search(r'continue.*reading|read.*more|unlock.*story', combined_text):
            indicators.append('continuation_required')
        
        if re.search(r'\$\d+|\d+.*month|subscription.*\$', combined_text):
            indicators.append('pricing_mentioned')
        
        return list(set(indicators))  # Remove duplicates
    
    def _determine_content_case(self, quality_score: float) -> str:
        """
        Determine progressive rendering case based on quality score.
        """
        
        if quality_score >= self.FULL_CONTENT_THRESHOLD:
            return 'full'
        elif quality_score >= self.PARTIAL_CONTENT_THRESHOLD:
            return 'partial'
        elif quality_score >= self.MINIMAL_CONTENT_THRESHOLD:
            return 'minimal'
        else:
            return 'failed'
    
    def get_quality_summary(self, metrics: QualityMetrics) -> str:
        """
        Generate human-readable quality summary.
        """
        
        case_descriptions = {
            'full': f"✅ Complete article (~{metrics.estimated_completeness}% captured)",
            'partial': f"📖 Article preview (~{metrics.estimated_completeness}% captured)", 
            'minimal': f"🔗 Limited content available",
            'failed': f"❌ Insufficient content quality"
        }
        
        description = case_descriptions.get(metrics.content_case, "Unknown quality")
        
        issues = []
        if metrics.missing_elements:
            issues.append(f"Missing: {', '.join(metrics.missing_elements[:3])}")
        if metrics.paywall_indicators:
            issues.append("Paywall detected")
        if metrics.word_count < 200:
            issues.append("Very short content")
        
        if issues:
            description += f" • Issues: {'; '.join(issues)}"
        
        return description 