"""
Content Extraction Data Structures and Strategies for Step 1
Fast extraction focused on speed over processing quality.
Enhanced with advanced bypass techniques to avoid 403 Forbidden errors.
"""

import time
import logging
import random
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from urllib.parse import urljoin, urlparse
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
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
        self.timeout = getattr(settings, 'EXTRACTION_TIMEOUT', 15)
        self.user_agent = getattr(settings, 'DEFAULT_USER_AGENT', 
                                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
    
    @property
    @abstractmethod
    def available(self) -> bool:
        """Check if this strategy is available."""
        pass
    
    @abstractmethod
    def extract(self, url: str) -> ExtractionResult:
        """Extract content from URL."""
        pass


class BrowserSimulationStrategy(ExtractionStrategy):
    """
    Advanced browser simulation strategy to bypass 403 Forbidden errors.
    Mimics real human browsing behavior with realistic headers, sessions, and timing.
    """
    
    def __init__(self):
        super().__init__()
        self.name = "BrowserSimulation"
        
        # Real browser User-Agent strings (updated 2024)
        self.realistic_user_agents = [
            # Chrome on macOS
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            # Chrome on Windows
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            # Firefox on macOS
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0',
            # Firefox on Windows
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            # Safari on macOS
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
            # Edge on Windows
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0'
        ]
        
        # Common referers to make requests look organic
        self.common_referers = [
            'https://www.google.com/',
            'https://news.google.com/',
            'https://www.bing.com/',
            'https://duckduckgo.com/',
            'https://twitter.com/',
            'https://www.reddit.com/',
            'https://www.facebook.com/',
        ]
        
        # Session for connection pooling and cookie persistence
        self.session = None
        self._setup_session()
    
    def _setup_session(self):
        """Setup requests session with realistic configuration."""
        self.session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
    
    @property
    def available(self) -> bool:
        """Browser simulation is always available."""
        return True
    
    def extract(self, url: str) -> ExtractionResult:
        """Extract content using advanced browser simulation."""
        start_time = time.time()
        
        try:
            # Try multiple realistic browser configurations
            strategies = [
                self._try_chrome_simulation,
                self._try_firefox_simulation,
                self._try_safari_simulation,
                self._try_mobile_simulation,
            ]
            
            for strategy_func in strategies:
                result = strategy_func(url)
                if result.success and not result.paywall_detected:
                    result.duration_ms = int((time.time() - start_time) * 1000)
                    result.strategy_used = f"{self.name}_{strategy_func.__name__}"
                    return result
                
                # Small delay between attempts to avoid detection
                time.sleep(random.uniform(0.5, 1.5))
            
            # Return best result if all failed
            result.duration_ms = int((time.time() - start_time) * 1000)
            result.strategy_used = self.name
            return result
            
        except Exception as e:
            logger.exception(f"Browser simulation failed for {url}: {str(e)}")
            return ExtractionResult(
                success=False,
                error_message=f"Browser simulation error: {str(e)}",
                duration_ms=int((time.time() - start_time) * 1000),
                strategy_used=self.name
            )
    
    def _try_chrome_simulation(self, url: str) -> ExtractionResult:
        """Simulate Chrome browser."""
        headers = self._get_chrome_headers(url)
        return self._make_request_with_headers(url, headers)
    
    def _try_firefox_simulation(self, url: str) -> ExtractionResult:
        """Simulate Firefox browser."""
        headers = self._get_firefox_headers(url)
        return self._make_request_with_headers(url, headers)
    
    def _try_safari_simulation(self, url: str) -> ExtractionResult:
        """Simulate Safari browser."""
        headers = self._get_safari_headers(url)
        return self._make_request_with_headers(url, headers)
    
    def _try_mobile_simulation(self, url: str) -> ExtractionResult:
        """Simulate mobile browser."""
        headers = self._get_mobile_headers(url)
        return self._make_request_with_headers(url, headers)
    
    def _get_chrome_headers(self, url: str) -> Dict[str, str]:
        """Get realistic Chrome browser headers."""
        parsed_url = urlparse(url)
        
        return {
            'User-Agent': random.choice([ua for ua in self.realistic_user_agents if 'Chrome' in ua]),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
        }
    
    def _get_firefox_headers(self, url: str) -> Dict[str, str]:
        """Get realistic Firefox browser headers."""
        return {
            'User-Agent': random.choice([ua for ua in self.realistic_user_agents if 'Firefox' in ua]),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        }
    
    def _get_safari_headers(self, url: str) -> Dict[str, str]:
        """Get realistic Safari browser headers."""
        return {
            'User-Agent': random.choice([ua for ua in self.realistic_user_agents if 'Safari' in ua and 'Chrome' not in ua]),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
        }
    
    def _get_mobile_headers(self, url: str) -> Dict[str, str]:
        """Get realistic mobile browser headers."""
        mobile_user_agents = [
            'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (Linux; Android 14; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
            'Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36'
        ]
        
        return {
            'User-Agent': random.choice(mobile_user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
        }
    
    def _make_request_with_headers(self, url: str, headers: Dict[str, str]) -> ExtractionResult:
        """Make HTTP request with specified headers."""
        try:
            # Add random referer to make request look organic
            if random.random() < 0.7:  # 70% chance of having referer
                headers['Referer'] = random.choice(self.common_referers)
            
            # Make request with session for cookie persistence
            response = self.session.get(
                url,
                headers=headers,
                timeout=self.timeout,
                allow_redirects=True,
                verify=False  # Skip SSL verification for problematic sites
            )
            
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract content and metadata
            extraction_data = self._extract_content_data(soup, url)
            
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
    
    def _extract_content_data(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Extract content and metadata from parsed HTML."""
        
        # Extract title with multiple fallbacks
        title = self._extract_title(soup)
        
        # Extract author
        author = self._extract_author(soup)
        
        # Extract publish date
        publish_date = self._extract_publish_date(soup)
        
        # Extract main content
        content = self._extract_content(soup)
        
        # Extract metadata
        metadata = {
            'url': url,
            'content_length': len(content),
            'title_length': len(title),
            'has_author': bool(author),
            'has_date': bool(publish_date),
            'extraction_method': 'browser_simulation'
        }
        
        return {
            'content': content,
            'title': title,
            'author': author,
            'publish_date': publish_date,
            'metadata': metadata
        }
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract article title with multiple strategies."""
        title_selectors = [
            'h1.headline',
            'h1.title',
            'h1.entry-title',
            'h1.post-title',
            'h1.article-title',
            '[data-testid="headline"]',
            '.headline h1',
            '.title h1',
            'h1',
            'title',
            '[property="og:title"]',
            '[name="twitter:title"]',
            '[itemprop="headline"]',
        ]
        
        for selector in title_selectors:
            element = soup.select_one(selector)
            if element:
                title = element.get_text(strip=True) or element.get('content', '')
                if title and len(title) > 10:  # Reasonable title length
                    return title[:200]  # Limit title length
        
        return ""
    
    def _extract_author(self, soup: BeautifulSoup) -> str:
        """Extract article author with multiple strategies."""
        author_selectors = [
            '[rel="author"]',
            '[property="article:author"]',
            '[name="author"]',
            '[itemprop="author"]',
            '.author-name',
            '.byline-author',
            '.article-author',
            '.post-author',
            '.author',
            '.byline',
            '[data-testid="author"]',
        ]
        
        for selector in author_selectors:
            element = soup.select_one(selector)
            if element:
                author = element.get_text(strip=True) or element.get('content', '')
                if author and len(author) < 100:  # Reasonable author length
                    return author
        
        return ""
    
    def _extract_publish_date(self, soup: BeautifulSoup) -> str:
        """Extract publish date with multiple strategies."""
        date_selectors = [
            '[property="article:published_time"]',
            '[name="publish_date"]',
            '[itemprop="datePublished"]',
            'time[datetime]',
            '.publish-date',
            '.publication-date',
            '.article-date',
            '.post-date',
            '.date',
            '[data-testid="timestamp"]',
        ]
        
        for selector in date_selectors:
            element = soup.select_one(selector)
            if element:
                date = element.get('datetime') or element.get('content') or element.get_text(strip=True)
                if date:
                    return date
        
        return ""
    
    def _extract_content(self, soup: BeautifulSoup) -> str:
        """Extract main article content with multiple strategies."""
        
        # Remove unwanted elements first
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'menu']):
            element.decompose()
        
        content_selectors = [
            # Common article selectors
            'article .content',
            'article .entry-content',
            'article .post-content',
            '[data-testid="article-body"]',
            '.article-body',
            '.story-body',
            '.entry-content',
            '.post-content',
            '.content-body',
            '.article-content',
            # Fallback selectors
            'article',
            '[role="main"]',
            '.content',
            'main',
        ]
        
        for selector in content_selectors:
            element = soup.select_one(selector)
            if element:
                # Remove advertisements, social widgets, etc.
                for unwanted in element(['aside', '.ad', '.advertisement', '.social-share', '.related-articles']):
                    unwanted.decompose()
                
                content = element.get_text(strip=True)
                if len(content) > 500:  # Minimum meaningful content length
                    return ' '.join(content.split())  # Normalize whitespace
        
        # Ultimate fallback: extract from body
        body = soup.find('body')
        if body:
            # Remove navigation, header, footer, sidebar
            for element in body(['nav', 'header', 'footer', 'aside', '.sidebar', '.navigation']):
                element.decompose()
            
            content = body.get_text(strip=True)
            return ' '.join(content.split())
        
        return ""
    
    def _detect_paywall(self, soup: BeautifulSoup, html_content: str) -> tuple[bool, List[str]]:
        """Detect if content is behind a paywall."""
        
        detected_indicators = []
        html_lower = html_content.lower()
        
        # Enhanced paywall indicators
        paywall_patterns = [
            # Text patterns
            'subscribe to continue reading',
            'subscription required',
            'premium content',
            'subscriber only',
            'subscribers only',
            'paywall',
            'sign in to read',
            'become a member',
            'unlock this article',
            'continue reading',
            'read the full story',
            'free trial',
            'limited time offer',
            'register to read',
            'login to continue',
            
            # CSS class patterns
            'paywall',
            'subscription',
            'premium',
            'subscriber-only',
            'locked-content',
            'auth-required',
            'registration-wall',
            
            # Common paywall services
            'piano.io',
            'tinypass',
            'cleeng',
            'zuora',
            'recurly',
            'stripe',
            'chargebee',
        ]
        
        # Check for paywall indicators
        for indicator in paywall_patterns:
            if indicator in html_lower:
                detected_indicators.append(indicator)
        
        # Check for paywall-related elements
        paywall_selectors = [
            '.paywall',
            '.subscription',
            '.premium',
            '[data-paywall]',
            '.auth-required',
            '.subscriber-only',
            '.registration-wall',
            '.meter-limit',
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
            'subscribe to',
            'view more',
        ]
        
        text_content = soup.get_text().lower()
        for pattern in truncation_patterns:
            if pattern in text_content:
                detected_indicators.append(f"truncation_{pattern}")
        
        # Determine if paywall is detected (require multiple strong indicators)
        paywall_detected = len(detected_indicators) >= 2
        
        return paywall_detected, detected_indicators


class PaywallBypassStrategy(ExtractionStrategy):
    """
    Enhanced strategy for bypassing paywalls and extracting content.
    Uses various techniques including bot crawlers and archive services.
    """
    
    def __init__(self):
        super().__init__()
        self.name = "PaywallBypass"
        
        # Enhanced bypass techniques with updated crawlers
        self.bypass_methods = [
            # Search engine crawlers (most effective)
            {
                'name': 'googlebot',
                'headers': {
                    'User-Agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate',
                    'Connection': 'keep-alive',
                }
            },
            {
                'name': 'bingbot',
                'headers': {
                    'User-Agent': 'Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)',
                    'Accept': '*/*',
                    'Accept-Encoding': 'gzip, deflate',
                }
            },
            # Social media crawlers
            {
                'name': 'facebookbot',
                'headers': {
                    'User-Agent': 'facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)',
                    'Accept': '*/*',
                    'Accept-Encoding': 'gzip, deflate'
                }
            },
            {
                'name': 'twitterbot',
                'headers': {
                    'User-Agent': 'Twitterbot/1.0',
                    'Accept': '*/*',
                    'Accept-Encoding': 'gzip, deflate'
                }
            },
            # Archive crawlers
            {
                'name': 'archivebot',
                'headers': {
                    'User-Agent': 'Mozilla/5.0 (compatible; archive.org_bot +http://www.archive.org/details/archive.org_bot)',
                    'Accept': '*/*'
                }
            },
            # Academic/research crawlers
            {
                'name': 'academic',
                'headers': {
                    'User-Agent': 'Mozilla/5.0 (compatible; semanticscholar.org +https://www.semanticscholar.org/crawler)',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                }
            }
        ]
    
    @property
    def available(self) -> bool:
        """Paywall bypass is always available."""
        return True
    
    def extract(self, url: str) -> ExtractionResult:
        """Extract content using paywall bypass techniques."""
        start_time = time.time()
        
        try:
            # Try each bypass method
            for method in self.bypass_methods:
                logger.info(f"Trying {method['name']} bypass for {url}")
                
                result = self._try_bypass_method(url, method['headers'])
                
                if result.success and not result.paywall_detected:
                    result.duration_ms = int((time.time() - start_time) * 1000)
                    result.strategy_used = f"{self.name}_{method['name']}"
                    return result
                
                # Small delay between attempts
                time.sleep(random.uniform(0.3, 0.8))
            
            # Return best available result
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
        paywall_indicators = [
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
        
        for indicator in paywall_indicators:
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
            # Make HTTP request with realistic browser headers
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0'
            }
            
            response = requests.get(
                url,
                headers=headers,
                timeout=self.timeout,
                allow_redirects=True,
                verify=False  # Skip SSL verification for problematic sites
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


class AdvancedBypassStrategy(ExtractionStrategy):
    """
    Advanced bypass strategy for the most restrictive sites.
    Uses sophisticated techniques like proxy rotation, IP masking, and alternative access methods.
    """
    
    def __init__(self):
        super().__init__()
        self.name = "AdvancedBypass"
        
        # Advanced bypass techniques
        self.advanced_methods = [
            # Method 1: Tor-like headers
            {
                'name': 'tor_simulation',
                'headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Sec-Fetch-User': '?1',
                    'Cache-Control': 'no-cache',
                    'Pragma': 'no-cache',
                }
            },
            # Method 2: Old browser simulation (sometimes bypasses modern protections)
            {
                'name': 'old_browser',
                'headers': {
                    'User-Agent': 'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/6.0)',
                    'Accept': 'text/html, application/xhtml+xml, */*',
                    'Accept-Language': 'en-US',
                    'Accept-Encoding': 'gzip, deflate',
                    'Connection': 'Keep-Alive',
                }
            },
            # Method 3: Mobile browser with different characteristics
            {
                'name': 'advanced_mobile',
                'headers': {
                    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-us',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                }
            },
            # Method 4: Academic/research access
            {
                'name': 'research_access',
                'headers': {
                    'User-Agent': 'Mozilla/5.0 (compatible; ResearchBot/1.0; +https://example.edu/bot)',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate',
                    'Connection': 'keep-alive',
                    'From': 'research@example.edu',
                }
            },
            # Method 5: Bypass with library/institutional headers
            {
                'name': 'institutional',
                'headers': {
                    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'cross-site',
                    'Sec-Fetch-User': '?1',
                    'X-Forwarded-For': '8.8.8.8',  # Google DNS
                    'X-Real-IP': '8.8.8.8',
                }
            }
        ]
        
        # Alternative access patterns
        self.alternative_access_patterns = [
            # Pattern 1: RSS/Feed access
            lambda url: url.replace('/news/', '/rss/').replace('/tech/', '/feeds/tech/') if '/news/' in url or '/tech/' in url else None,
            # Pattern 2: AMP version
            lambda url: url.replace('https://', 'https://amp.') if 'amp.' not in url else None,
            # Pattern 3: Mobile version
            lambda url: url.replace('https://', 'https://m.') if 'm.' not in url else None,
            # Pattern 4: Archive access (Wayback Machine)
            lambda url: f'https://web.archive.org/web/{url}',
            # Pattern 5: Outline.com proxy
            lambda url: f'https://outline.com/{url}',
        ]
    
    @property
    def available(self) -> bool:
        """Advanced bypass is always available."""
        return True
    
    def extract(self, url: str) -> ExtractionResult:
        """Extract content using advanced bypass techniques."""
        start_time = time.time()
        
        try:
            # Try direct access with advanced methods first
            for method in self.advanced_methods:
                logger.info(f"Trying {method['name']} advanced bypass for {url}")
                
                result = self._try_advanced_method(url, method['headers'])
                
                if result.success and not result.paywall_detected:
                    result.duration_ms = int((time.time() - start_time) * 1000)
                    result.strategy_used = f"{self.name}_{method['name']}"
                    return result
                
                # Small delay between attempts
                time.sleep(random.uniform(0.2, 0.5))
            
            # Try alternative access patterns if direct methods failed
            for i, pattern_func in enumerate(self.alternative_access_patterns):
                try:
                    alternative_url = pattern_func(url)
                    if alternative_url and alternative_url != url:
                        logger.info(f"Trying alternative access pattern {i+1}: {alternative_url}")
                        
                        # Use a simple method for alternative URLs
                        result = self._try_alternative_url(alternative_url)
                        
                        if result.success and not result.paywall_detected:
                            result.duration_ms = int((time.time() - start_time) * 1000)
                            result.strategy_used = f"{self.name}_alt_pattern_{i+1}"
                            return result
                            
                        time.sleep(random.uniform(0.2, 0.5))
                        
                except Exception as e:
                    logger.debug(f"Alternative access pattern {i+1} failed: {str(e)}")
                    continue
            
            # Return failure result
            return ExtractionResult(
                success=False,
                error_message="All advanced bypass methods failed",
                duration_ms=int((time.time() - start_time) * 1000),
                strategy_used=self.name
            )
            
        except Exception as e:
            logger.exception(f"Advanced bypass failed for {url}: {str(e)}")
            return ExtractionResult(
                success=False,
                error_message=f"Advanced bypass error: {str(e)}",
                duration_ms=int((time.time() - start_time) * 1000),
                strategy_used=self.name
            )
    
    def _try_advanced_method(self, url: str, headers: Dict[str, str]) -> ExtractionResult:
        """Try an advanced bypass method with specific headers."""
        
        try:
            # Create session with specific configuration
            session = requests.Session()
            
            # Configure session for stealth
            session.headers.update(headers)
            
            # Add some randomness to timing
            time.sleep(random.uniform(0.1, 0.3))
            
            # Make request
            response = session.get(
                url,
                timeout=self.timeout,
                allow_redirects=True,
                verify=False,
                stream=True  # Stream to handle large responses better
            )
            
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract content and metadata
            extraction_data = self._extract_advanced_content(soup, url)
            
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
    
    def _try_alternative_url(self, alternative_url: str) -> ExtractionResult:
        """Try accessing content through an alternative URL."""
        
        try:
            # Use simple headers for alternative URLs
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
            }
            
            response = requests.get(
                alternative_url,
                headers=headers,
                timeout=self.timeout,
                allow_redirects=True,
                verify=False
            )
            
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract content and metadata
            extraction_data = self._extract_advanced_content(soup, alternative_url)
            
            # Check for paywall (less strict for alternative URLs)
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
                error_message=f"Alternative URL request failed: {str(e)}"
            )
        except Exception as e:
            return ExtractionResult(
                success=False,
                error_message=f"Alternative URL extraction failed: {str(e)}"
            )
    
    def _extract_advanced_content(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Extract content with advanced techniques for difficult sites."""
        
        # Remove unwanted elements aggressively
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'menu', 'noscript']):
            element.decompose()
        
        # Enhanced title extraction
        title = self._extract_advanced_title(soup)
        
        # Enhanced author extraction  
        author = self._extract_advanced_author(soup)
        
        # Enhanced date extraction
        publish_date = self._extract_advanced_date(soup)
        
        # Enhanced content extraction
        content = self._extract_advanced_main_content(soup)
        
        metadata = {
            'url': url,
            'content_length': len(content),
            'title_length': len(title),
            'has_author': bool(author),
            'has_date': bool(publish_date),
            'extraction_method': 'advanced_bypass'
        }
        
        return {
            'content': content,
            'title': title,
            'author': author,
            'publish_date': publish_date,
            'metadata': metadata
        }
    
    def _extract_advanced_title(self, soup: BeautifulSoup) -> str:
        """Extract title with advanced techniques."""
        title_selectors = [
            # News-specific selectors
            '[data-testid="headline"]',
            '[data-module="ArticleHeader"] h1',
            '.headline__text',
            '.entry-title',
            '.article-headline',
            '.story-headline',
            # Meta tags
            '[property="og:title"]',
            '[name="twitter:title"]',
            '[itemprop="headline"]',
            # Generic selectors
            'h1.title',
            'h1.headline',
            'h1',
            'title'
        ]
        
        for selector in title_selectors:
            element = soup.select_one(selector)
            if element:
                title = element.get_text(strip=True) or element.get('content', '')
                if title and len(title) > 5:
                    # Clean title
                    title = re.sub(r'\s+', ' ', title)
                    return title[:300]  # Limit length
        
        return ""
    
    def _extract_advanced_author(self, soup: BeautifulSoup) -> str:
        """Extract author with advanced techniques."""
        author_selectors = [
            '[data-testid="byline"]',
            '[data-module="Byline"]',
            '.byline__author',
            '.author-name',
            '.article-byline',
            '[rel="author"]',
            '[property="article:author"]',
            '[name="author"]',
            '[itemprop="author"]',
            '.author',
            '.byline'
        ]
        
        for selector in author_selectors:
            element = soup.select_one(selector)
            if element:
                author = element.get_text(strip=True) or element.get('content', '')
                if author and len(author) < 150:
                    # Clean author name
                    author = re.sub(r'\s+', ' ', author)
                    return author
        
        return ""
    
    def _extract_advanced_date(self, soup: BeautifulSoup) -> str:
        """Extract date with advanced techniques."""
        date_selectors = [
            '[data-testid="timestamp"]',
            '[data-module="Timestamp"]',
            '.timestamp',
            '.publish-date',
            '.article-date',
            '[property="article:published_time"]',
            '[name="publish_date"]',
            '[itemprop="datePublished"]',
            'time[datetime]',
            '.date'
        ]
        
        for selector in date_selectors:
            element = soup.select_one(selector)
            if element:
                date = element.get('datetime') or element.get('content') or element.get_text(strip=True)
                if date:
                    return date
        
        return ""
    
    def _extract_advanced_main_content(self, soup: BeautifulSoup) -> str:
        """Extract main content with advanced techniques."""
        
        content_selectors = [
            # News-specific content selectors
            '[data-testid="article-body"]',
            '[data-module="ArticleBody"]',
            '.article-content__body',
            '.story-body__inner',
            '.entry-content',
            '.post-content',
            '.article-text',
            '.story-text',
            # Generic content selectors
            'article .content',
            'article',
            '[role="main"]',
            '.content',
            'main'
        ]
        
        for selector in content_selectors:
            element = soup.select_one(selector)
            if element:
                # Remove unwanted sub-elements
                for unwanted in element(['aside', '.ad', '.advertisement', '.social-share', 
                                       '.related-articles', '.newsletter-signup', '.subscription-banner']):
                    unwanted.decompose()
                
                content = element.get_text(strip=True)
                if len(content) > 300:  # Minimum meaningful content
                    # Clean and normalize content
                    content = re.sub(r'\s+', ' ', content)
                    return content
        
        # Fallback: extract from body with aggressive cleaning
        body = soup.find('body')
        if body:
            # Remove all navigation, headers, footers, etc.
            for element in body(['nav', 'header', 'footer', 'aside', '.navigation', 
                               '.sidebar', '.menu', '.ad', '.advertisement']):
                element.decompose()
            
            content = body.get_text(strip=True)
            content = re.sub(r'\s+', ' ', content)
            return content
        
        return ""
    
    def _detect_paywall(self, soup: BeautifulSoup, html_content: str) -> tuple[bool, List[str]]:
        """Detect paywall with advanced techniques."""
        
        detected_indicators = []
        html_lower = html_content.lower()
        
        # Advanced paywall patterns
        paywall_patterns = [
            'subscriber exclusive',
            'premium subscriber',
            'unlimited access',
            'subscription required',
            'sign up to continue',
            'register to continue',
            'paywall',
            'subscribe now',
            'limited free articles',
            'free trial',
            'become a member',
            'premium content'
        ]
        
        for pattern in paywall_patterns:
            if pattern in html_lower:
                detected_indicators.append(pattern)
        
        # Check for paywall elements
        paywall_selectors = [
            '.paywall',
            '.subscription-barrier',
            '.premium-gate',
            '[data-paywall]',
            '.meter-limit',
            '.registration-wall'
        ]
        
        for selector in paywall_selectors:
            if soup.select(selector):
                detected_indicators.append(f"element_{selector}")
        
        # Less strict paywall detection for alternative access methods
        paywall_detected = len(detected_indicators) >= 3
        
        return paywall_detected, detected_indicators 