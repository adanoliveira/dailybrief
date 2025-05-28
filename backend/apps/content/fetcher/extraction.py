"""
Content Extraction Data Structures and Strategies for Step 1
Fast extraction focused on speed over processing quality.
"""

import time
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
from django.conf import settings

logger = logging.getLogger(__name__)


@dataclass
class ExtractionResult:
    """Result of Step 1 content extraction."""
    success: bool
    raw_html: str = ""
    basic_content: str = ""
    title: str = ""
    author: str = ""
    publish_date: Optional[str] = None
    extraction_metadata: Dict[str, Any] = field(default_factory=dict)
    paywall_detected: bool = False
    paywall_indicators: List[str] = field(default_factory=list)
    error_message: str = ""
    duration_ms: int = 0
    strategy_used: str = ""
    
    def __post_init__(self):
        """Validate extraction result after initialization."""
        if self.success and not self.raw_html:
            self.success = False
            self.error_message = "No raw HTML content extracted"


class ExtractionStrategy(ABC):
    """Abstract base class for content extraction strategies."""
    
    def __init__(self):
        self.name = self.__class__.__name__
        self.timeout = getattr(settings, 'EXTRACTION_TIMEOUT', 10)
        self.user_agent = getattr(settings, 'EXTRACTION_USER_AGENT', 
                                'Mozilla/5.0 (compatible; DailyBrief/1.0)')
    
    @property
    @abstractmethod
    def available(self) -> bool:
        """Check if this strategy is available for use."""
        pass
    
    @abstractmethod
    def extract(self, url: str) -> ExtractionResult:
        """Extract content from the given URL."""
        pass


class PaywallBypassStrategy(ExtractionStrategy):
    """
    Strategy for bypassing paywalls and extracting content.
    Uses various techniques to access content behind paywalls.
    """
    
    def __init__(self):
        super().__init__()
        self.name = "PaywallBypass"
        
        # Paywall bypass techniques
        self.bypass_headers = {
            'User-Agent': 'Googlebot/2.1 (+http://www.google.com/bot.html)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # Alternative headers for different bypass methods
        self.alternative_headers = [
            # Facebook crawler
            {
                'User-Agent': 'facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)',
                'Accept': '*/*',
                'Accept-Encoding': 'gzip, deflate'
            },
            # Twitter crawler
            {
                'User-Agent': 'Twitterbot/1.0',
                'Accept': '*/*',
                'Accept-Encoding': 'gzip, deflate'
            },
            # Archive.org
            {
                'User-Agent': 'Mozilla/5.0 (compatible; archive.org_bot +http://www.archive.org/details/archive.org_bot)',
                'Accept': '*/*'
            }
        ]
        
        # Paywall detection patterns
        self.paywall_indicators = [
            # Text patterns
            'subscribe to continue reading',
            'subscription required',
            'premium content',
            'subscriber only',
            'paywall',
            'sign in to read',
            'become a member',
            'unlock this article',
            'continue reading',
            'read the full story',
            
            # CSS class patterns
            'paywall',
            'subscription',
            'premium',
            'subscriber-only',
            'locked-content',
            'auth-required',
            
            # Common paywall services
            'piano.io',
            'tinypass',
            'cleeng',
            'zuora',
            'recurly'
        ]
    
    @property
    def available(self) -> bool:
        """Paywall bypass is always available."""
        return True
    
    def extract(self, url: str) -> ExtractionResult:
        """
        Extract content using paywall bypass techniques.
        """
        start_time = time.time()
        
        try:
            # Try primary bypass method first
            result = self._try_bypass_method(url, self.bypass_headers)
            
            if result.success and not result.paywall_detected:
                result.duration_ms = int((time.time() - start_time) * 1000)
                result.strategy_used = self.name
                return result
            
            # Try alternative methods if primary failed or paywall detected
            for i, headers in enumerate(self.alternative_headers):
                logger.info(f"Trying alternative bypass method {i+1} for {url}")
                
                result = self._try_bypass_method(url, headers)
                
                if result.success and not result.paywall_detected:
                    result.duration_ms = int((time.time() - start_time) * 1000)
                    result.strategy_used = f"{self.name}_alt_{i+1}"
                    return result
            
            # If all methods failed or detected paywall, return best result
            result.duration_ms = int((time.time() - start_time) * 1000)
            result.strategy_used = self.name
            return result
            
        except Exception as e:
            logger.exception(f"Paywall bypass failed for {url}: {str(e)}")
            return ExtractionResult(
                success=False,
                error_message=f"Paywall bypass error: {str(e)}",
                duration_ms=int((time.time() - start_time) * 1000),
                strategy_used=self.name
            )
    
    def _try_bypass_method(self, url: str, headers: Dict[str, str]) -> ExtractionResult:
        """Try a specific bypass method with given headers."""
        
        try:
            # Make request with bypass headers
            response = requests.get(
                url, 
                headers=headers, 
                timeout=self.timeout,
                allow_redirects=True,
                verify=False  # Skip SSL verification for speed
            )
            
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract basic content and metadata
            extraction_data = self._extract_basic_data(soup, url)
            
            # Check for paywall
            paywall_detected, paywall_indicators = self._detect_paywall(soup, response.text)
            
            return ExtractionResult(
                success=True,
                raw_html=response.text,
                basic_content=extraction_data['content'],
                title=extraction_data['title'],
                author=extraction_data['author'],
                publish_date=extraction_data['publish_date'],
                extraction_metadata=extraction_data['metadata'],
                paywall_detected=paywall_detected,
                paywall_indicators=paywall_indicators
            )
            
        except requests.RequestException as e:
            return ExtractionResult(
                success=False,
                error_message=f"Request failed: {str(e)}"
            )
        except Exception as e:
            return ExtractionResult(
                success=False,
                error_message=f"Extraction failed: {str(e)}"
            )
    
    def _extract_basic_data(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Extract basic content and metadata from parsed HTML."""
        
        # Extract title
        title = ""
        title_selectors = [
            'h1',
            'title',
            '[property="og:title"]',
            '[name="twitter:title"]',
            '.headline',
            '.title',
            '.article-title'
        ]
        
        for selector in title_selectors:
            element = soup.select_one(selector)
            if element:
                title = element.get_text(strip=True) or element.get('content', '')
                if title:
                    break
        
        # Extract author
        author = ""
        author_selectors = [
            '[rel="author"]',
            '[property="article:author"]',
            '[name="author"]',
            '.author',
            '.byline',
            '.article-author'
        ]
        
        for selector in author_selectors:
            element = soup.select_one(selector)
            if element:
                author = element.get_text(strip=True) or element.get('content', '')
                if author:
                    break
        
        # Extract publish date
        publish_date = ""
        date_selectors = [
            '[property="article:published_time"]',
            '[name="publish_date"]',
            'time[datetime]',
            '.publish-date',
            '.date'
        ]
        
        for selector in date_selectors:
            element = soup.select_one(selector)
            if element:
                publish_date = element.get('datetime') or element.get('content') or element.get_text(strip=True)
                if publish_date:
                    break
        
        # Extract basic content (fast method)
        content = ""
        content_selectors = [
            'article',
            '[role="main"]',
            '.content',
            '.article-content',
            '.post-content',
            '.entry-content',
            'main'
        ]
        
        for selector in content_selectors:
            element = soup.select_one(selector)
            if element:
                # Remove script and style elements
                for script in element(["script", "style"]):
                    script.decompose()
                
                content = element.get_text(strip=True)
                if len(content) > 200:  # Minimum content length
                    break
        
        # Fallback: extract from body
        if not content:
            body = soup.find('body')
            if body:
                # Remove navigation, header, footer, sidebar
                for element in body(['nav', 'header', 'footer', 'aside']):
                    element.decompose()
                
                content = body.get_text(strip=True)
        
        # Extract metadata
        metadata = {
            'url': url,
            'content_length': len(content),
            'title_length': len(title),
            'has_author': bool(author),
            'has_date': bool(publish_date),
            'extraction_method': 'paywall_bypass'
        }
        
        return {
            'content': content,
            'title': title,
            'author': author,
            'publish_date': publish_date,
            'metadata': metadata
        }
    
    def _detect_paywall(self, soup: BeautifulSoup, html_content: str) -> tuple[bool, List[str]]:
        """Detect if content is behind a paywall."""
        
        detected_indicators = []
        html_lower = html_content.lower()
        
        # Check for paywall indicators in text and HTML
        for indicator in self.paywall_indicators:
            if indicator in html_lower:
                detected_indicators.append(indicator)
        
        # Check for paywall-related elements
        paywall_selectors = [
            '.paywall',
            '.subscription',
            '.premium',
            '[data-paywall]',
            '.auth-required',
            '.subscriber-only'
        ]
        
        for selector in paywall_selectors:
            elements = soup.select(selector)
            if elements:
                detected_indicators.append(f"paywall_element_{selector}")
        
        # Check for truncated content indicators
        truncation_patterns = [
            '...',
            'continue reading',
            'read more',
            'full article',
            'subscribe to'
        ]
        
        text_content = soup.get_text().lower()
        for pattern in truncation_patterns:
            if pattern in text_content:
                detected_indicators.append(f"truncation_{pattern}")
        
        # Determine if paywall is detected
        paywall_detected = len(detected_indicators) >= 2  # Require multiple indicators
        
        return paywall_detected, detected_indicators


class BeautifulSoupStrategy(ExtractionStrategy):
    """
    Basic content extraction using BeautifulSoup.
    Fast and reliable fallback strategy.
    """
    
    def __init__(self):
        super().__init__()
        self.name = "BeautifulSoup"
    
    @property
    def available(self) -> bool:
        """BeautifulSoup is always available."""
        return True
    
    def extract(self, url: str) -> ExtractionResult:
        """
        Extract content using basic BeautifulSoup parsing.
        """
        start_time = time.time()
        
        try:
            # Make simple HTTP request
            headers = {
                'User-Agent': self.user_agent,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive'
            }
            
            response = requests.get(
                url,
                headers=headers,
                timeout=self.timeout,
                allow_redirects=True
            )
            
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract content and metadata
            extraction_data = self._extract_content(soup, url)
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            return ExtractionResult(
                success=True,
                raw_html=response.text,
                basic_content=extraction_data['content'],
                title=extraction_data['title'],
                author=extraction_data['author'],
                publish_date=extraction_data['publish_date'],
                extraction_metadata=extraction_data['metadata'],
                duration_ms=duration_ms,
                strategy_used=self.name
            )
            
        except Exception as e:
            logger.exception(f"BeautifulSoup extraction failed for {url}: {str(e)}")
            return ExtractionResult(
                success=False,
                error_message=f"BeautifulSoup extraction error: {str(e)}",
                duration_ms=int((time.time() - start_time) * 1000),
                strategy_used=self.name
            )
    
    def _extract_content(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Extract content using BeautifulSoup selectors."""
        
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
            element.decompose()
        
        # Extract title
        title = ""
        title_element = soup.find('title')
        if title_element:
            title = title_element.get_text(strip=True)
        
        # Try h1 if title is empty or too long
        if not title or len(title) > 200:
            h1 = soup.find('h1')
            if h1:
                title = h1.get_text(strip=True)
        
        # Extract author
        author = ""
        author_selectors = ['[rel="author"]', '.author', '.byline']
        for selector in author_selectors:
            element = soup.select_one(selector)
            if element:
                author = element.get_text(strip=True)
                break
        
        # Extract publish date
        publish_date = ""
        time_element = soup.find('time')
        if time_element:
            publish_date = time_element.get('datetime') or time_element.get_text(strip=True)
        
        # Extract main content
        content = ""
        content_selectors = [
            'article',
            '[role="main"]',
            '.content',
            '.post-content',
            '.entry-content',
            'main'
        ]
        
        for selector in content_selectors:
            element = soup.select_one(selector)
            if element:
                content = element.get_text(strip=True)
                if len(content) > 100:
                    break
        
        # Fallback to body content
        if not content:
            body = soup.find('body')
            if body:
                content = body.get_text(strip=True)
        
        # Clean up content
        content = ' '.join(content.split())  # Normalize whitespace
        
        metadata = {
            'url': url,
            'content_length': len(content),
            'title_length': len(title),
            'has_author': bool(author),
            'has_date': bool(publish_date),
            'extraction_method': 'beautifulsoup'
        }
        
        return {
            'content': content,
            'title': title,
            'author': author,
            'publish_date': publish_date,
            'metadata': metadata
        } 