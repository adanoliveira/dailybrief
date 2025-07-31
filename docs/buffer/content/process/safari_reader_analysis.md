# Safari Reader Analysis & Python/Django Implementation Plan

## Executive Summary

Safari Reader is a sophisticated content extraction system that identifies and extracts the main article content from web pages. It uses a multi-layered approach combining visual analysis, text scoring, DOM structure evaluation, and machine learning-like heuristics to determine the primary article content while filtering out navigation, ads, and other non-essential elements.

## Core Architecture Analysis

### 1. Main Components

#### A. CandidateElement Class
**Purpose**: Represents potential article containers with scoring mechanisms
**Key Responsibilities**:
- Text node collection and analysis
- Raw score calculation based on text length and visibility
- Language score multipliers (especially for CJK languages)
- Tag/attribute score multipliers
- Score density calculations
- Element pruning logic

#### B. ReaderArticleFinder Class  
**Purpose**: Main orchestrator for article detection and extraction
**Key Responsibilities**:
- Article node detection via multiple strategies
- Visual examination using hit testing
- Content cleaning and sanitization
- Next page URL detection
- Title extraction
- Leading image identification

### 2. Detection Strategies (Priority Order)

1. **Whitelist Strategy**: Trusted selectors for known sites
2. **Visual Examination**: Hit-testing at strategic viewport positions
3. **Comprehensive Element Search**: Score-based evaluation of all elements
4. **Suggested Route**: Using pre-provided DOM paths

### 3. Scoring Algorithm

#### Text Node Scoring
```javascript
rawScore = Math.pow(textLength * visibilityMultiplier, TextNodeLengthPower)
```

#### Final Scoring
```javascript
finalScore = rawScore * tagNameMultiplier * languageMultiplier
```

#### Key Scoring Factors
- **Positive**: article, content, entry, hentry, post classes/IDs
- **Negative**: comment, footer, sidebar, advertisement classes/IDs  
- **Language Multipliers**: 3x boost for CJK languages
- **Depth Penalties**: Deeper nested elements get reduced scores

### 4. Content Cleaning Pipeline

1. **Element Pruning**: Remove scripts, styles, forms, ads
2. **Visibility Filtering**: Remove hidden/off-screen elements
3. **Link Density Analysis**: Remove high-link-density blocks
4. **Comment Block Detection**: Remove comment sections
5. **Similar Element Detection**: Remove repetitive structures
6. **Float Handling**: Process floating elements appropriately
7. **Image Processing**: Handle lazy loading, sizing, positioning

## Python/Django Implementation Structure

### App Architecture (Modular Monolith)

```
apps/
├── content_extraction/
│   ├── models.py          # Article, ExtractionResult, CandidateElement
│   ├── services/
│   │   ├── __init__.py
│   │   ├── extractor.py   # Main ReaderArticleExtractor service
│   │   ├── scorer.py      # Scoring algorithms
│   │   ├── cleaner.py     # Content cleaning pipeline
│   │   ├── detector.py    # Article detection strategies
│   │   └── analyzer.py    # Text/DOM analysis utilities
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── dom_utils.py   # DOM manipulation utilities
│   │   ├── text_utils.py  # Text processing utilities
│   │   └── constants.py   # Configuration constants
│   ├── views.py           # API endpoints
│   └── urls.py
├── rss_processing/         # RSS feed processing
└── ai_summarization/       # AI-powered summarization
```

### Core Models

```python
# apps/content_extraction/models.py
from django.db import models
import uuid

class ExtractionResult(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True)
    url = models.URLField()
    title = models.CharField(max_length=500, blank=True)
    content = models.TextField()
    cleaned_html = models.TextField()
    main_image_url = models.URLField(blank=True)
    next_page_url = models.URLField(blank=True)
    reading_time_minutes = models.IntegerField(null=True)
    language = models.CharField(max_length=10, blank=True)
    extraction_score = models.FloatField()
    extraction_method = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

class CandidateElement(models.Model):
    extraction_result = models.ForeignKey(ExtractionResult, on_delete=models.CASCADE)
    tag_name = models.CharField(max_length=50)
    class_names = models.TextField(blank=True)
    element_id = models.CharField(max_length=200, blank=True)
    raw_score = models.FloatField()
    final_score = models.FloatField()
    text_length = models.IntegerField()
    depth = models.IntegerField()
    is_selected = models.BooleanField(default=False)
```

### Main Service Classes

#### 1. ReaderArticleExtractor Service

```python
# apps/content_extraction/services/extractor.py
from typing import Optional, Dict, Any
from bs4 import BeautifulSoup
import requests
from .detector import ArticleDetector
from .cleaner import ContentCleaner
from .analyzer import ContentAnalyzer

class ReaderArticleExtractor:
    """Main service for extracting article content from web pages"""
    
    def __init__(self):
        self.detector = ArticleDetector()
        self.cleaner = ContentCleaner()
        self.analyzer = ContentAnalyzer()
        
    def extract_article(self, url: str) -> Dict[str, Any]:
        """Extract article content from URL"""
        # Fetch page content
        response = requests.get(url, headers=self._get_headers())
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Detect article element
        article_element = self.detector.find_article_element(soup)
        if not article_element:
            raise ValueError("No article content found")
            
        # Clean and process content
        cleaned_content = self.cleaner.clean_article_content(
            article_element, soup
        )
        
        # Extract metadata
        metadata = self.analyzer.extract_metadata(soup, article_element)
        
        return {
            'content': cleaned_content,
            'title': metadata['title'],
            'main_image': metadata['main_image'],
            'next_page_url': metadata['next_page_url'],
            'reading_time': metadata['reading_time'],
            'language': metadata['language'],
            'extraction_score': metadata['score']
        }
```

#### 2. Article Detection Service

```python
# apps/content_extraction/services/detector.py
from typing import Optional, List
from bs4 import BeautifulSoup, Tag
from .scorer import ElementScorer
from ..utils.constants import TRUSTED_SELECTORS, CANDIDATE_TAG_NAMES

class ArticleDetector:
    """Detects main article content using multiple strategies"""
    
    def __init__(self):
        self.scorer = ElementScorer()
        
    def find_article_element(self, soup: BeautifulSoup) -> Optional[Tag]:
        """Find the main article element using priority strategies"""
        
        # Strategy 1: Whitelist for trusted sites
        article = self._find_by_whitelist(soup)
        if article:
            return article
            
        # Strategy 2: Visual examination simulation
        article = self._find_by_visual_examination(soup)
        if article:
            return article
            
        # Strategy 3: Comprehensive element scoring
        article = self._find_by_comprehensive_search(soup)
        if article:
            return article
            
        return None
        
    def _find_by_whitelist(self, soup: BeautifulSoup) -> Optional[Tag]:
        """Find article using trusted selectors for known sites"""
        hostname = self._get_hostname(soup)
        
        for pattern, selector in TRUSTED_SELECTORS.items():
            if pattern.match(hostname):
                element = soup.select_one(selector)
                if element:
                    return element
        return None
        
    def _find_by_comprehensive_search(self, soup: BeautifulSoup) -> Optional[Tag]:
        """Find article by scoring all viable candidate elements"""
        candidates = self._find_candidate_elements(soup)
        if not candidates:
            return None
            
        # Score all candidates
        scored_candidates = []
        for candidate in candidates:
            score = self.scorer.calculate_final_score(candidate, soup)
            scored_candidates.append((candidate, score))
            
        # Return highest scoring candidate
        best_candidate = max(scored_candidates, key=lambda x: x[1])
        return best_candidate[0] if best_candidate[1] > self.scorer.MINIMUM_SCORE else None
```

#### 3. Content Scoring Service

```python
# apps/content_extraction/services/scorer.py
import re
import math
from typing import List
from bs4 import Tag, NavigableString
from ..utils.constants import *

class ElementScorer:
    """Calculates scores for potential article elements"""
    
    MINIMUM_SCORE = 1600
    TEXT_NODE_LENGTH_POWER = 1.25
    ARTICLE_MATCH_BONUS = 0.5
    COMMENT_MATCH_PENALTY = 0.75
    
    def calculate_final_score(self, element: Tag, soup) -> float:
        """Calculate final score for an element"""
        raw_score = self._calculate_raw_score(element)
        tag_multiplier = self._calculate_tag_multiplier(element)
        language_multiplier = self._calculate_language_multiplier(element)
        
        return raw_score * tag_multiplier * language_multiplier
        
    def _calculate_raw_score(self, element: Tag) -> float:
        """Calculate raw score based on text content"""
        text_nodes = self._get_text_nodes(element)
        total_score = 0
        
        for text_node in text_nodes:
            if self._is_visible_text(text_node):
                length = len(text_node.strip())
                if length >= 20:  # Minimum text length
                    depth_multiplier = self._calculate_depth_multiplier(text_node, element)
                    total_score += math.pow(length * depth_multiplier, self.TEXT_NODE_LENGTH_POWER)
                    
        return total_score
        
    def _calculate_tag_multiplier(self, element: Tag) -> float:
        """Calculate multiplier based on tag names and attributes"""
        multiplier = 1.0
        
        # Check element and its ancestors
        current = element
        while current and current.name:
            # Check ID attribute
            element_id = current.get('id', '')
            if ARTICLE_REGEX.search(element_id):
                multiplier += self.ARTICLE_MATCH_BONUS
            if COMMENT_REGEX.search(element_id):
                multiplier -= self.COMMENT_MATCH_PENALTY
                
            # Check class attribute
            class_names = ' '.join(current.get('class', []))
            if ARTICLE_REGEX.search(class_names):
                multiplier += self.ARTICLE_MATCH_BONUS
            if COMMENT_REGEX.search(class_names):
                multiplier -= self.COMMENT_MATCH_PENALTY
                
            # Article tag bonus
            if current.name == 'article':
                multiplier += self.ARTICLE_MATCH_BONUS
                
            current = current.parent
            
        return max(0, multiplier)
```

#### 4. Content Cleaning Service

```python
# apps/content_extraction/services/cleaner.py
import re
from typing import Set
from bs4 import Tag, Comment, NavigableString
from ..utils.constants import PRUNING_SELECTORS

class ContentCleaner:
    """Cleans and sanitizes extracted article content"""
    
    def clean_article_content(self, article: Tag, soup) -> str:
        """Clean article content removing unwanted elements"""
        # Clone the article to avoid modifying original
        cleaned_article = article.__copy__()
        
        # Cleaning pipeline
        self._remove_unwanted_elements(cleaned_article)
        self._process_images(cleaned_article)
        self._process_links(cleaned_article)
        self._remove_empty_elements(cleaned_article)
        self._normalize_structure(cleaned_article)
        
        return str(cleaned_article)
        
    def _remove_unwanted_elements(self, article: Tag):
        """Remove scripts, styles, ads, comments, etc."""
        # Remove by tag name
        for tag_name in ['script', 'style', 'noscript', 'iframe']:
            for element in article.find_all(tag_name):
                element.decompose()
                
        # Remove by selectors
        for selector in PRUNING_SELECTORS:
            for element in article.select(selector):
                element.decompose()
                
        # Remove comments
        for comment in article.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()
            
    def _should_prune_element(self, element: Tag) -> bool:
        """Determine if element should be pruned"""
        # Check link density
        if self._calculate_link_density(element) > 0.33:
            return True
            
        # Check for negative class names
        class_names = ' '.join(element.get('class', []))
        if NEGATIVE_REGEX.search(class_names):
            return True
            
        # Check text content length
        text_content = element.get_text(strip=True)
        if len(text_content) < 25 and not element.find('img'):
            return True
            
        return False
```

### Configuration Constants

```python
# apps/content_extraction/utils/constants.py
import re

# Scoring constants
READER_MINIMUM_SCORE = 1600
READER_MINIMUM_ADVANTAGE = 15
ARTICLE_MINIMUM_SCORE_DENSITY = 4.25

# Regular expressions
ARTICLE_REGEX = re.compile(
    r'(?:(?:^|\s)(?:(post|hentry|entry)[-_]?(?:content|text|body)?|'
    r'article[-_]?(?:content|text|body|page)?)(?:\s|$))', 
    re.IGNORECASE
)

COMMENT_REGEX = re.compile(r'comment|meta|footer|footnote', re.IGNORECASE)

NEGATIVE_REGEX = re.compile(
    r'advertisement|breadcrumb|combx|comment|contact|disqus|footer|'
    r'link|meta|mod-conversations|promo|related|scroll|share|'
    r'shoutbox|sidebar|social|sponsor|subscribe|tags|toolbox|widget|_ad$',
    re.IGNORECASE
)

POSITIVE_REGEX = re.compile(
    r'article|body|content|entry|hentry|page|pagination|post|text',
    re.IGNORECASE
)

# Trusted site selectors
TRUSTED_SELECTORS = {
    re.compile(r'.*\.apple\.com$'): 'article',
    # Add more trusted selectors
}

# Element pruning selectors
PRUNING_SELECTORS = [
    '#disqus_thread',
    '#comments', 
    '.userComments',
    '.social-share',
    '.advertisement',
    '.sidebar',
    '.navigation'
]

# Minimum dimensions
CANDIDATE_MINIMUM_WIDTH = 280
CANDIDATE_MINIMUM_HEIGHT = 295
CANDIDATE_MINIMUM_AREA = 170000
```

### API Endpoints

```python
# apps/content_extraction/views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from .services.extractor import ReaderArticleExtractor
from .models import ExtractionResult

@csrf_exempt
@require_http_methods(["POST", "OPTIONS"])
def extract_article(request):
    """Extract article content from URL"""
    if request.method == "OPTIONS":
        response = JsonResponse({})
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type"
        return response
        
    try:
        data = json.loads(request.body)
        url = data.get('url')
        
        if not url:
            return JsonResponse({'error': 'URL is required'}, status=400)
            
        extractor = ReaderArticleExtractor()
        result = extractor.extract_article(url)
        
        # Save to database
        extraction_result = ExtractionResult.objects.create(
            url=url,
            title=result['title'],
            content=result['content'],
            cleaned_html=result['content'],
            main_image_url=result.get('main_image', ''),
            next_page_url=result.get('next_page_url', ''),
            reading_time_minutes=result.get('reading_time', 0),
            language=result.get('language', ''),
            extraction_score=result['extraction_score'],
            extraction_method='comprehensive'
        )
        
        response_data = {
            'id': extraction_result.public_id,
            'title': result['title'],
            'content': result['content'],
            'main_image': result.get('main_image'),
            'reading_time': result.get('reading_time'),
            'extraction_score': result['extraction_score']
        }
        
        response = JsonResponse(response_data)
        response["Access-Control-Allow-Origin"] = "*"
        return response
        
    except Exception as e:
        response = JsonResponse({'error': str(e)}, status=500)
        response["Access-Control-Allow-Origin"] = "*"
        return response
```

## Implementation Phases

### Phase 1: Core Infrastructure (Week 1-2)
- Set up Django app structure
- Implement basic models
- Create DOM utilities and text processing
- Implement basic content fetching

### Phase 2: Article Detection (Week 2-3)  
- Implement scoring algorithms
- Add whitelist/blacklist functionality
- Create candidate element detection
- Add visual examination simulation

### Phase 3: Content Cleaning (Week 3-4)
- Implement content cleaning pipeline
- Add element pruning logic
- Handle images and media
- Process links and navigation

### Phase 4: Advanced Features (Week 4-5)
- Next page detection
- Title extraction optimization
- Language detection
- Reading time estimation

### Phase 5: Integration & Testing (Week 5-6)
- API endpoints
- Database integration  
- Error handling
- Performance optimization
- Testing suite

## Key Differences from JavaScript Version

1. **Async Processing**: Use Celery for background article processing
2. **Database Storage**: Persist extraction results and metadata
3. **Caching**: Redis caching for frequently accessed articles
4. **Error Handling**: Robust error handling and logging
5. **API Design**: RESTful endpoints with proper CORS handling
6. **Testing**: Comprehensive test suite with mock data

This architecture provides a solid foundation for replicating Safari Reader's functionality while leveraging Django's strengths and following clean architecture principles. 