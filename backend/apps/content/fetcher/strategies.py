import logging
import requests
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from abc import ABC, abstractmethod

# Import extraction libraries
try:
    from newspaper import Article as NewspaperArticle
    NEWSPAPER_AVAILABLE = True
except ImportError:
    NEWSPAPER_AVAILABLE = False

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

try:
    from readability import Document
    READABILITY_AVAILABLE = True
except ImportError:
    READABILITY_AVAILABLE = False

try:
    import html2text
    HTML2TEXT_AVAILABLE = True
except ImportError:
    HTML2TEXT_AVAILABLE = False

from .utils import (
    clean_extracted_text, 
    assess_content_quality, 
    detect_paywall_indicators,
    get_request_headers,
    get_html_content,
    get_html_content_with_session,
    get_stealth_headers
)

logger = logging.getLogger(__name__)


@dataclass
class ExtractionResult:
    """Result of content extraction attempt."""
    success: bool
    content: str = ""
    title: str = ""
    author: str = ""
    publish_date: Optional[str] = None
    error_message: str = ""
    strategy_used: str = ""
    paywall_detected: bool = False
    paywall_indicators: list = None
    quality_metrics: dict = None
    
    # Rich content fields
    rich_content: dict = None  # Structured content blocks
    media_assets: list = None  # Media metadata and URLs
    formatting_data: dict = None  # Typography and structure info
    content_structure: dict = None  # Article structure map
    
    def __post_init__(self):
        if self.paywall_indicators is None:
            self.paywall_indicators = []
        if self.quality_metrics is None:
            self.quality_metrics = {}
        if self.rich_content is None:
            self.rich_content = {"blocks": []}
        if self.media_assets is None:
            self.media_assets = []
        if self.formatting_data is None:
            self.formatting_data = {}
        if self.content_structure is None:
            self.content_structure = {}


class ExtractionStrategy(ABC):
    """Abstract base class for content extraction strategies."""
    
    @abstractmethod
    def extract(self, url: str, html: str = None, headers: dict = None) -> ExtractionResult:
        """Extract content from URL or HTML."""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Strategy name."""
        pass
    
    @property
    @abstractmethod
    def available(self) -> bool:
        """Whether this strategy is available (dependencies installed)."""
        pass


class NewspaperStrategy(ExtractionStrategy):
    """Content extraction using newspaper3k library."""
    
    @property
    def name(self) -> str:
        return "newspaper3k"
    
    @property
    def available(self) -> bool:
        return NEWSPAPER_AVAILABLE
    
    def extract(self, url: str, html: str = None, headers: dict = None) -> ExtractionResult:
        """Extract content using newspaper3k."""
        if not self.available:
            return ExtractionResult(
                success=False,
                error_message="newspaper3k library not available",
                strategy_used=self.name
            )
        
        try:
            article = NewspaperArticle(url)
            
            # Download and parse
            if html:
                article.set_html(html)
                article.parse()
            else:
                # Download with custom headers if provided
                if headers:
                    import requests
                    response = requests.get(url, headers=headers, timeout=30)
                    response.raise_for_status()
                    article.set_html(response.text)
                    article.parse()
                else:
                    article.download()
                    article.parse()
            
            # Check for paywall indicators
            paywall_detected, paywall_indicators = detect_paywall_indicators(
                article.html if article.html else "", url
            )
            
            if paywall_detected:
                return ExtractionResult(
                    success=False,
                    error_message="Paywall detected",
                    strategy_used=self.name,
                    paywall_detected=True,
                    paywall_indicators=paywall_indicators
                )
            
            # Extract content
            content = clean_extracted_text(article.text)
            title = article.title or ""
            author = ", ".join(article.authors) if article.authors else ""
            
            # Assess quality
            quality_metrics = assess_content_quality(content, title)
            
            return ExtractionResult(
                success=bool(content),
                content=content,
                title=title,
                author=author,
                publish_date=article.publish_date.isoformat() if article.publish_date else None,
                strategy_used=self.name,
                quality_metrics=quality_metrics
            )
            
        except Exception as e:
            logger.error(f"Newspaper extraction failed for {url}: {str(e)}")
            return ExtractionResult(
                success=False,
                error_message=str(e),
                strategy_used=self.name
            )


class BeautifulSoupStrategy(ExtractionStrategy):
    """Content extraction using BeautifulSoup with heuristics."""
    
    @property
    def name(self) -> str:
        return "beautifulsoup"
    
    @property
    def available(self) -> bool:
        return BS4_AVAILABLE
    
    def extract(self, url: str, html: str = None, headers: dict = None) -> ExtractionResult:
        """Extract content using BeautifulSoup."""
        if not self.available:
            return ExtractionResult(
                success=False,
                error_message="BeautifulSoup library not available",
                strategy_used=self.name
            )
        
        try:
            # Get HTML if not provided
            if not html:
                # First try with enhanced session-based approach for anti-bot detection
                try:
                    html = get_html_content_with_session(url, headers, use_session=True)
                except requests.exceptions.HTTPError as e:
                    if e.response.status_code == 403:
                        # If 403, try with different approach
                        logger.info(f"403 error, trying alternative headers for {url}")
                        # Try with a different user agent and referer
                        from urllib.parse import urlparse
                        domain = urlparse(url).netloc
                        alt_headers = get_request_headers(referer=f"https://{domain}")
                        html = get_html_content_with_session(url, alt_headers, use_session=False, delay=1.0)
                    else:
                        raise
            
            # Check for paywall indicators
            paywall_detected, paywall_indicators = detect_paywall_indicators(html, url)
            
            if paywall_detected:
                return ExtractionResult(
                    success=False,
                    error_message="Paywall detected",
                    strategy_used=self.name,
                    paywall_detected=True,
                    paywall_indicators=paywall_indicators
                )
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract rich content
            rich_extractor = RichContentExtractor()
            rich_content, media_assets, formatting_data = rich_extractor.extract_rich_content(soup, url)
            
            # Extract title
            title = ""
            title_selectors = ['h1', 'title', '[property="og:title"]', '[name="title"]']
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    break
            
            # Extract author
            author = ""
            author_selectors = [
                '[rel="author"]', '[class*="author"]', '[class*="byline"]',
                '[property="article:author"]', '[name="author"]'
            ]
            for selector in author_selectors:
                author_elem = soup.select_one(selector)
                if author_elem:
                    author = author_elem.get_text(strip=True)
                    break
            
            # Extract main content using common patterns
            content_selectors = [
                'article', '[role="main"]', '.article-content', '.post-content',
                '.entry-content', '.content', '#content', '.article-body',
                '.story-body', '.post-body', 'main'
            ]
            
            content_text = ""
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    # Remove unwanted elements
                    for unwanted in content_elem.select('script, style, nav, footer, aside, .advertisement, .ad'):
                        unwanted.decompose()
                    
                    content_text = content_elem.get_text(separator='\n', strip=True)
                    if len(content_text) > 200:  # Minimum content length
                        break
            
            # Fallback: extract all paragraphs
            if not content_text or len(content_text) < 200:
                paragraphs = soup.find_all('p')
                content_text = '\n\n'.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
            
            # Clean content
            content = clean_extracted_text(content_text)
            
            # Assess quality
            quality_metrics = assess_content_quality(content, title)
            
            return ExtractionResult(
                success=bool(content),
                content=content,
                title=title,
                author=author,
                strategy_used=self.name,
                quality_metrics=quality_metrics,
                rich_content=rich_content,
                media_assets=media_assets,
                formatting_data=formatting_data
            )
            
        except Exception as e:
            logger.error(f"BeautifulSoup extraction failed for {url}: {str(e)}")
            return ExtractionResult(
                success=False,
                error_message=str(e),
                strategy_used=self.name
            )


class ReadabilityStrategy(ExtractionStrategy):
    """Content extraction using readability-lxml."""
    
    @property
    def name(self) -> str:
        return "readability"
    
    @property
    def available(self) -> bool:
        return READABILITY_AVAILABLE and HTML2TEXT_AVAILABLE
    
    def extract(self, url: str, html: str = None, headers: dict = None) -> ExtractionResult:
        """Extract content using readability."""
        if not self.available:
            return ExtractionResult(
                success=False,
                error_message="readability or html2text library not available",
                strategy_used=self.name
            )
        
        try:
            # Get HTML if not provided
            if not html:
                # First try with enhanced session-based approach for anti-bot detection
                try:
                    html = get_html_content_with_session(url, headers, use_session=True)
                except requests.exceptions.HTTPError as e:
                    if e.response.status_code == 403:
                        # If 403, try with different approach
                        logger.info(f"403 error, trying alternative headers for {url}")
                        # Try with a different user agent and referer
                        from urllib.parse import urlparse
                        domain = urlparse(url).netloc
                        alt_headers = get_request_headers(referer=f"https://{domain}")
                        html = get_html_content_with_session(url, alt_headers, use_session=False, delay=1.0)
                    else:
                        raise
            
            # Check for paywall indicators
            paywall_detected, paywall_indicators = detect_paywall_indicators(html, url)
            
            if paywall_detected:
                return ExtractionResult(
                    success=False,
                    error_message="Paywall detected",
                    strategy_used=self.name,
                    paywall_detected=True,
                    paywall_indicators=paywall_indicators
                )
            
            # Extract readable content
            doc = Document(html)
            readable_html = doc.summary()
            title = doc.title()
            
            # Convert HTML to text
            h = html2text.HTML2Text()
            h.ignore_links = True
            h.ignore_images = True
            h.body_width = 0  # Don't wrap lines
            h.unicode_snob = True  # Handle unicode properly
            
            try:
                content_text = h.handle(readable_html)
            except (UnicodeDecodeError, UnicodeEncodeError, TypeError) as e:
                logger.warning(f"Encoding issue in readability for {url}: {str(e)}")
                # Try to fix encoding issues
                try:
                    if isinstance(readable_html, bytes):
                        readable_html = readable_html.decode('utf-8', errors='ignore')
                    else:
                        readable_html = str(readable_html).encode('utf-8', errors='ignore').decode('utf-8')
                    content_text = h.handle(readable_html)
                except Exception as e2:
                    logger.error(f"Failed to fix encoding for {url}: {str(e2)}")
                    return ExtractionResult(
                        success=False,
                        error_message=f"Encoding error: {str(e)}",
                        strategy_used=self.name
                    )
            
            # Clean content
            content = clean_extracted_text(content_text)
            
            # Log extraction results
            logger.info(f"Stealth extraction results for {url}: title='{title[:50]}...', content_length={len(content)}")
            
            # Assess quality
            quality_metrics = assess_content_quality(content, title)
            
            if content:
                logger.info(f"Successfully extracted content using stealth strategy for {url}")
                return ExtractionResult(
                    success=True,
                    content=content,
                    title=title,
                    strategy_used=self.name,
                    quality_metrics=quality_metrics
                )
            else:
                logger.warning(f"Stealth strategy extracted no content for {url}")
                return ExtractionResult(
                    success=False,
                    error_message="No content extracted despite successful fetch",
                    strategy_used=self.name
                )
            
        except Exception as e:
            logger.error(f"Readability extraction failed for {url}: {str(e)}")
            return ExtractionResult(
                success=False,
                error_message=str(e),
                strategy_used=self.name
            )


class StealthStrategy(ExtractionStrategy):
    """Content extraction using stealth techniques for blocked sites."""
    
    @property
    def name(self) -> str:
        return "stealth"
    
    @property
    def available(self) -> bool:
        return True  # Always available as it uses basic requests
    
    def extract(self, url: str, html: str = None, headers: dict = None) -> ExtractionResult:
        """Extract content using stealth techniques."""
        try:
            if html:
                # If HTML is provided, use it
                response_html = html
            else:
                # Use stealth fetching
                import time
                import random
                
                logger.info(f"Attempting stealth extraction for {url}")
                time.sleep(random.uniform(2.0, 4.0))
                
                session = requests.Session()
                stealth_headers = get_stealth_headers(url)
                session.headers.update(stealth_headers)
                response = session.get(url, timeout=30)
                
                # Handle different response scenarios
                if response.status_code == 403:
                    if len(response.content) > 1000:
                        logger.info(f"Got 403 but with substantial content ({len(response.content)} bytes) for {url}")
                        response_html = response.text
                        logger.info(f"HTML preview: {response_html[:500]}...")
                        
                        # Check if this 403 is actually a challenge page
                        if self._is_bot_challenge_page(response_html):
                            logger.info(f"Challenge page detected in 403 response for {url}")
                            # Try to bypass the challenge
                            bypassed_html = self._attempt_challenge_bypass(url, session)
                            if bypassed_html:
                                response_html = bypassed_html
                                logger.info(f"Challenge bypass successful for {url}")
                            # If bypass fails, we'll continue with the challenge page and let detection handle it
                    else:
                        logger.warning(f"Got 403 with minimal content ({len(response.content)} bytes) for {url}")
                        raise requests.exceptions.HTTPError(f"403 Client Error: Forbidden for url: {url}")
                elif response.status_code == 200:
                    response_html = response.text
                    # Check if this is a challenge page despite 200 status
                    if self._is_bot_challenge_page(response_html):
                        logger.info(f"Challenge page detected despite 200 status for {url}")
                        # Try to bypass the challenge
                        bypassed_html = self._attempt_challenge_bypass(url, session)
                        if bypassed_html:
                            response_html = bypassed_html
                        # If bypass fails, we'll continue with the challenge page and let detection handle it
                else:
                    response.raise_for_status()
                    response_html = response.text
            
            # Check for bot detection/challenge pages
            if self._is_bot_challenge_page(response_html):
                logger.warning(f"Bot challenge page detected for {url}")
                return ExtractionResult(
                    success=False,
                    error_message="Bot challenge page detected (Cloudflare, etc.)",
                    strategy_used=self.name
                )
            
            # Check for paywall indicators
            paywall_detected, paywall_indicators = detect_paywall_indicators(response_html, url)
            
            if paywall_detected:
                return ExtractionResult(
                    success=False,
                    error_message="Paywall detected",
                    strategy_used=self.name,
                    paywall_detected=True,
                    paywall_indicators=paywall_indicators
                )
            
            # Use BeautifulSoup for extraction
            if not response_html:
                return ExtractionResult(
                    success=False,
                    error_message="No HTML content received",
                    strategy_used=self.name
                )
            
            if not BS4_AVAILABLE:
                return ExtractionResult(
                    success=False,
                    error_message="BeautifulSoup library not available",
                    strategy_used=self.name
                )
            
            soup = BeautifulSoup(response_html, 'html.parser')
            
            # Extract title
            title = ""
            title_selectors = ['h1', 'title', '[property="og:title"]', '[name="title"]']
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    break
            
            # Extract main content using common patterns
            content_selectors = [
                'article', '[role="main"]', '.article-content', '.post-content',
                '.entry-content', '.content', '#content', '.article-body',
                '.story-body', '.post-body', 'main', '.article-text'
            ]
            
            content_text = ""
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    # Remove unwanted elements
                    for unwanted in content_elem.select('script, style, nav, footer, aside, .advertisement, .ad'):
                        unwanted.decompose()
                    
                    content_text = content_elem.get_text(separator='\n', strip=True)
                    if len(content_text) > 200:  # Minimum content length
                        break
            
            # Fallback: extract all paragraphs
            if not content_text or len(content_text) < 200:
                paragraphs = soup.find_all('p')
                content_text = '\n\n'.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
            
            # Clean content
            content = clean_extracted_text(content_text)
            
            # Assess quality
            quality_metrics = assess_content_quality(content, title)
            
            return ExtractionResult(
                success=bool(content),
                content=content,
                title=title,
                strategy_used=self.name,
                quality_metrics=quality_metrics
            )
            
        except Exception as e:
            import traceback
            error_msg = str(e) if str(e) else "Unknown error"
            logger.error(f"Stealth extraction failed for {url}: {error_msg}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return ExtractionResult(
                success=False,
                error_message=error_msg,
                strategy_used=self.name
            )
    
    def _is_bot_challenge_page(self, html: str) -> bool:
        """Check if the HTML is a bot challenge/detection page."""
        if not html:
            return False
        
        html_lower = html.lower()
        
        # Common bot challenge indicators
        challenge_indicators = [
            'just a moment',
            'checking your browser',
            'cloudflare',
            'ddos protection',
            'security check',
            'please wait while we verify',
            'browser verification',
            'challenge-platform',
            'cf-browser-verification',
            'ray id:',  # Cloudflare Ray ID
            'enable javascript and cookies',
            'javascript is required',
            'please enable cookies'
        ]
        
        # Check for multiple indicators (more reliable)
        matches = sum(1 for indicator in challenge_indicators if indicator in html_lower)
        
        # If we have multiple indicators or specific strong ones, it's likely a challenge page
        if matches >= 2:
            return True
        
        # Check for specific strong indicators
        strong_indicators = [
            'just a moment',
            'cf-browser-verification',
            'challenge-platform'
        ]
        
        for indicator in strong_indicators:
            if indicator in html_lower:
                return True
        
        return False
    
    def _attempt_challenge_bypass(self, url: str, session: requests.Session) -> Optional[str]:
        """
        Attempt to bypass challenge pages using various techniques.
        
        Args:
            url (str): Target URL
            session (requests.Session): Session to use for requests
            
        Returns:
            Optional[str]: HTML content if bypass successful, None otherwise
        """
        import time
        import random
        from urllib.parse import urlparse, urljoin
        
        logger.info(f"Attempting challenge bypass for {url}")
        
        # Strategy 1: Wait and retry (some challenges are time-based)
        try:
            logger.info("Strategy 1: Time-based bypass - waiting 5-10 seconds")
            time.sleep(random.uniform(5.0, 10.0))
            
            # Use different headers for retry
            retry_headers = self._get_bypass_headers(url)
            session.headers.update(retry_headers)
            
            response = session.get(url, timeout=30)
            if response.status_code == 200 and not self._is_bot_challenge_page(response.text):
                logger.info("Time-based bypass successful!")
                return response.text
                
        except Exception as e:
            logger.warning(f"Time-based bypass failed: {e}")
        
        # Strategy 2: Try accessing through different entry points
        try:
            logger.info("Strategy 2: Alternative entry point bypass")
            domain = urlparse(url).netloc
            
            # Try accessing homepage first to establish session
            homepage_url = f"https://{domain}/"
            time.sleep(random.uniform(2.0, 4.0))
            
            homepage_response = session.get(homepage_url, timeout=30)
            if homepage_response.status_code == 200:
                logger.info("Homepage access successful, retrying target URL")
                time.sleep(random.uniform(3.0, 6.0))
                
                # Now try the original URL
                response = session.get(url, timeout=30)
                if response.status_code == 200 and not self._is_bot_challenge_page(response.text):
                    logger.info("Alternative entry point bypass successful!")
                    return response.text
                    
        except Exception as e:
            logger.warning(f"Alternative entry point bypass failed: {e}")
        
        # Strategy 3: Try with minimal, older browser headers
        try:
            logger.info("Strategy 3: Legacy browser bypass")
            time.sleep(random.uniform(3.0, 5.0))
            
            legacy_headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            # Create new session for legacy attempt
            legacy_session = requests.Session()
            legacy_session.headers.update(legacy_headers)
            
            response = legacy_session.get(url, timeout=30)
            if response.status_code == 200 and not self._is_bot_challenge_page(response.text):
                logger.info("Legacy browser bypass successful!")
                return response.text
                
        except Exception as e:
            logger.warning(f"Legacy browser bypass failed: {e}")
        
        # Strategy 4: Try with mobile user agent
        try:
            logger.info("Strategy 4: Mobile user agent bypass")
            time.sleep(random.uniform(2.0, 4.0))
            
            mobile_headers = {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            }
            
            mobile_session = requests.Session()
            mobile_session.headers.update(mobile_headers)
            
            response = mobile_session.get(url, timeout=30)
            if response.status_code == 200 and not self._is_bot_challenge_page(response.text):
                logger.info("Mobile user agent bypass successful!")
                return response.text
                
        except Exception as e:
            logger.warning(f"Mobile user agent bypass failed: {e}")
        
        # Strategy 5: Session warming with multiple requests
        try:
            logger.info("Strategy 5: Session warming bypass")
            time.sleep(random.uniform(3.0, 5.0))
            
            # Create a fresh session and warm it up
            warm_session = requests.Session()
            warm_headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            }
            warm_session.headers.update(warm_headers)
            
            domain = urlparse(url).netloc
            
            # Step 1: Visit a simple page first (robots.txt or favicon)
            try:
                robots_url = f"https://{domain}/robots.txt"
                warm_session.get(robots_url, timeout=10)
                time.sleep(random.uniform(1.0, 3.0))
            except:
                pass
            
            # Step 2: Visit homepage
            try:
                homepage_url = f"https://{domain}/"
                warm_session.get(homepage_url, timeout=15)
                time.sleep(random.uniform(2.0, 4.0))
            except:
                pass
            
            # Step 3: Now try the target URL
            response = warm_session.get(url, timeout=30)
            if response.status_code == 200 and not self._is_bot_challenge_page(response.text):
                logger.info("Session warming bypass successful!")
                return response.text
                
        except Exception as e:
            logger.warning(f"Session warming bypass failed: {e}")
        
        logger.warning(f"All challenge bypass strategies failed for {url}")
        return None
    
    def _get_bypass_headers(self, url: str) -> Dict[str, str]:
        """Get specialized headers for challenge bypass."""
        import random
        from urllib.parse import urlparse
        
        domain = urlparse(url).netloc
        
        # More conservative headers that might bypass detection
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
        }
        
        # Add a realistic referer
        referers = [
            f"https://www.google.com/search?q={domain}",
            f"https://{domain}/",
            "https://www.google.com/",
        ]
        headers['Referer'] = random.choice(referers)
        
        return headers


class RSSEnhancedStrategy(ExtractionStrategy):
    """Enhanced RSS content strategy that maximizes value from feed data."""
    
    @property
    def name(self) -> str:
        return "rss_enhanced"
    
    @property
    def available(self) -> bool:
        return True  # Always available
    
    def extract(self, url: str, html: str = None, headers: dict = None) -> ExtractionResult:
        """Extract and enhance content from RSS feed data."""
        try:
            # This strategy works with the article's existing RSS data
            # We'll enhance it in the ContentFetcher service
            return ExtractionResult(
                success=False,
                error_message="RSS Enhanced strategy requires article context",
                strategy_used=self.name
            )
        except Exception as e:
            return ExtractionResult(
                success=False,
                error_message=str(e),
                strategy_used=self.name
            )
    
    def extract_from_article(self, article) -> ExtractionResult:
        """Extract enhanced content from article's RSS data."""
        try:
            # Start with description
            content_parts = []
            
            if article.description:
                content_parts.append(article.description)
            
            # Add any additional RSS content fields
            if hasattr(article, 'content') and article.content and len(article.content) > len(article.description or ""):
                # Sometimes RSS feeds include partial content
                content_parts.append(article.content)
            
            # Enhance with metadata
            metadata_parts = []
            if article.author:
                metadata_parts.append(f"By {article.author}")
            
            if article.published_at:
                from django.utils import timezone
                pub_date = article.published_at.strftime("%B %d, %Y")
                metadata_parts.append(f"Published {pub_date}")
            
            if article.source_name:
                metadata_parts.append(f"Source: {article.source_name}")
            
            # Combine content
            enhanced_content = "\n\n".join(content_parts)
            if metadata_parts:
                enhanced_content += f"\n\n{' | '.join(metadata_parts)}"
            
            # Add topics/categories if available
            if hasattr(article, 'topics') and article.topics.exists():
                topics = [topic.name for topic in article.topics.all()]
                enhanced_content += f"\n\nTopics: {', '.join(topics)}"
            
            # Clean and assess quality
            content = clean_extracted_text(enhanced_content)
            quality_metrics = assess_content_quality(content, article.title, article.description)
            
            # Boost quality score for good RSS descriptions
            if article.description and len(article.description.split()) > 30:
                quality_metrics['completeness'] = min(1.0, quality_metrics['completeness'] + 0.2)
                quality_metrics['quality'] = min(1.0, quality_metrics['quality'] + 0.1)
            
            return ExtractionResult(
                success=bool(content),
                content=content,
                title=article.title,
                author=article.author or "",
                strategy_used=self.name,
                quality_metrics=quality_metrics
            )
            
        except Exception as e:
            logger.error(f"RSS Enhanced extraction failed for article {article.id}: {str(e)}")
            return ExtractionResult(
                success=False,
                error_message=str(e),
                strategy_used=self.name
            )


class PublisherAPIStrategy(ExtractionStrategy):
    """Strategy for publisher-specific APIs and enhanced RSS feeds."""
    
    @property
    def name(self) -> str:
        return "publisher_api"
    
    @property
    def available(self) -> bool:
        return True
    
    def extract(self, url: str, html: str = None, headers: dict = None) -> ExtractionResult:
        """Extract content using publisher-specific APIs."""
        try:
            from urllib.parse import urlparse
            domain = urlparse(url).netloc.lower()
            
            # Publisher-specific extraction methods
            if 'nytimes.com' in domain:
                return self._extract_nytimes(url)
            elif 'washingtonpost.com' in domain:
                return self._extract_wapo(url)
            elif 'cnn.com' in domain:
                return self._extract_cnn(url)
            elif 'bbc.com' in domain or 'bbc.co.uk' in domain:
                return self._extract_bbc(url)
            elif 'reuters.com' in domain:
                return self._extract_reuters(url)
            elif 'apnews.com' in domain:
                return self._extract_ap(url)
            else:
                return ExtractionResult(
                    success=False,
                    error_message=f"No publisher-specific API available for {domain}",
                    strategy_used=self.name
                )
                
        except Exception as e:
            logger.error(f"Publisher API extraction failed for {url}: {str(e)}")
            return ExtractionResult(
                success=False,
                error_message=str(e),
                strategy_used=self.name
            )
    
    def _extract_nytimes(self, url: str) -> ExtractionResult:
        """Extract from NYTimes using their API or enhanced methods."""
        # NYTimes has a developer API that could be used
        # For now, try their RSS feeds or specific selectors
        try:
            import requests
            from bs4 import BeautifulSoup
            
            # Try NYTimes-specific headers
            headers = {
                'User-Agent': 'Mozilla/5.0 (compatible; NewsReader/1.0)',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Referer': 'https://www.nytimes.com/',
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # NYTimes-specific selectors
            content_selectors = [
                'section[name="articleBody"]',
                '.StoryBodyCompanionColumn',
                '.ArticleBody-articleBody',
                'section.meteredContent'
            ]
            
            content_text = ""
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    # Remove ads and unwanted elements
                    for unwanted in content_elem.select('.ad, .advertisement, .related-coverage'):
                        unwanted.decompose()
                    content_text = content_elem.get_text(separator='\n', strip=True)
                    break
            
            if content_text:
                title = soup.select_one('h1')
                title_text = title.get_text(strip=True) if title else ""
                
                content = clean_extracted_text(content_text)
                quality_metrics = assess_content_quality(content, title_text)
                
                return ExtractionResult(
                    success=True,
                    content=content,
                    title=title_text,
                    strategy_used=self.name,
                    quality_metrics=quality_metrics
                )
            
            return ExtractionResult(
                success=False,
                error_message="No content found with NYTimes selectors",
                strategy_used=self.name
            )
            
        except Exception as e:
            return ExtractionResult(
                success=False,
                error_message=f"NYTimes extraction failed: {str(e)}",
                strategy_used=self.name
            )
    
    def _extract_bbc(self, url: str) -> ExtractionResult:
        """Extract from BBC using their specific structure."""
        try:
            import requests
            from bs4 import BeautifulSoup
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (compatible; NewsReader/1.0)',
                'Accept': 'text/html,application/xhtml+xml',
                'Referer': 'https://www.bbc.com/',
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # BBC-specific selectors
            content_selectors = [
                '[data-component="text-block"]',
                '.story-body__inner',
                '.gel-body-copy',
                'div[data-component="text-block"] p'
            ]
            
            content_parts = []
            for selector in content_selectors:
                elements = soup.select(selector)
                for elem in elements:
                    text = elem.get_text(strip=True)
                    if text and len(text) > 20:  # Filter out short snippets
                        content_parts.append(text)
            
            if content_parts:
                title = soup.select_one('h1')
                title_text = title.get_text(strip=True) if title else ""
                
                content_text = '\n\n'.join(content_parts)
                content = clean_extracted_text(content_text)
                quality_metrics = assess_content_quality(content, title_text)
                
                return ExtractionResult(
                    success=True,
                    content=content,
                    title=title_text,
                    strategy_used=self.name,
                    quality_metrics=quality_metrics
                )
            
            return ExtractionResult(
                success=False,
                error_message="No content found with BBC selectors",
                strategy_used=self.name
            )
            
        except Exception as e:
            return ExtractionResult(
                success=False,
                error_message=f"BBC extraction failed: {str(e)}",
                strategy_used=self.name
            )
    
    def _extract_cnn(self, url: str) -> ExtractionResult:
        """Extract from CNN using their specific structure."""
        # CNN has been working well with our existing strategies
        # This could be enhanced with CNN-specific selectors
        return ExtractionResult(
            success=False,
            error_message="CNN extraction delegated to other strategies",
            strategy_used=self.name
        )
    
    def _extract_wapo(self, url: str) -> ExtractionResult:
        """Extract from Washington Post."""
        return ExtractionResult(
            success=False,
            error_message="WaPo requires subscription, using fallback",
            strategy_used=self.name
        )
    
    def _extract_reuters(self, url: str) -> ExtractionResult:
        """Extract from Reuters using their API or structure."""
        try:
            import requests
            from bs4 import BeautifulSoup
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (compatible; NewsReader/1.0)',
                'Accept': 'text/html,application/xhtml+xml',
                'Referer': 'https://www.reuters.com/',
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Reuters-specific selectors
            content_elem = soup.select_one('[data-testid="paragraph"]') or soup.select_one('.ArticleBodyWrapper')
            
            if content_elem:
                content_text = content_elem.get_text(separator='\n', strip=True)
                title = soup.select_one('h1')
                title_text = title.get_text(strip=True) if title else ""
                
                content = clean_extracted_text(content_text)
                quality_metrics = assess_content_quality(content, title_text)
                
                return ExtractionResult(
                    success=True,
                    content=content,
                    title=title_text,
                    strategy_used=self.name,
                    quality_metrics=quality_metrics
                )
            
            return ExtractionResult(
                success=False,
                error_message="No content found with Reuters selectors",
                strategy_used=self.name
            )
            
        except Exception as e:
            return ExtractionResult(
                success=False,
                error_message=f"Reuters extraction failed: {str(e)}",
                strategy_used=self.name
            )
    
    def _extract_ap(self, url: str) -> ExtractionResult:
        """Extract from Associated Press."""
        try:
            import requests
            from bs4 import BeautifulSoup
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (compatible; NewsReader/1.0)',
                'Accept': 'text/html,application/xhtml+xml',
                'Referer': 'https://apnews.com/',
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # AP-specific selectors
            content_elem = soup.select_one('.RichTextStoryBody') or soup.select_one('[data-key="article-body"]')
            
            if content_elem:
                content_text = content_elem.get_text(separator='\n', strip=True)
                title = soup.select_one('h1')
                title_text = title.get_text(strip=True) if title else ""
                
                content = clean_extracted_text(content_text)
                quality_metrics = assess_content_quality(content, title_text)
                
                return ExtractionResult(
                    success=True,
                    content=content,
                    title=title_text,
                    strategy_used=self.name,
                    quality_metrics=quality_metrics
                )
            
            return ExtractionResult(
                success=False,
                error_message="No content found with AP selectors",
                strategy_used=self.name
            )
            
        except Exception as e:
            return ExtractionResult(
                success=False,
                error_message=f"AP extraction failed: {str(e)}",
                strategy_used=self.name
            )


class PaywallBypassStrategy(ExtractionStrategy):
    """Advanced paywall bypass strategy for common paywall patterns."""
    
    @property
    def name(self) -> str:
        return "paywall_bypass"
    
    @property
    def available(self) -> bool:
        return BS4_AVAILABLE
    
    def extract(self, url: str, html: str = None, headers: dict = None) -> ExtractionResult:
        """Extract content using paywall bypass techniques."""
        if not self.available:
            return ExtractionResult(
                success=False,
                error_message="BeautifulSoup library not available",
                strategy_used=self.name
            )
        
        try:
            logger.info(f"Attempting paywall bypass extraction for {url}")
            
            # Strategy 1: Fast extraction before paywall loads
            result = self._fast_extraction(url, headers)
            if result.success:
                logger.info(f"Fast extraction successful for {url}")
                return result
            
            # Strategy 2: Extract from initial HTML before modal activation
            if html:
                result = self._extract_from_initial_html(html, url)
                if result.success:
                    logger.info(f"Initial HTML extraction successful for {url}")
                    return result
            
            # Strategy 3: Archive/cache extraction
            result = self._extract_from_archive(url, headers)
            if result.success:
                logger.info(f"Archive extraction successful for {url}")
                return result
            
            # Strategy 4: Reader mode extraction
            result = self._reader_mode_extraction(url, headers)
            if result.success:
                logger.info(f"Reader mode extraction successful for {url}")
                return result
            
            # Strategy 5: Remove paywall elements and extract
            result = self._remove_paywall_elements(url, headers)
            if result.success:
                logger.info(f"Paywall removal extraction successful for {url}")
                return result
            
            # Strategy 6: Extract from JSON-LD or structured data
            result = self._extract_from_structured_data(url, headers)
            if result.success:
                logger.info(f"Structured data extraction successful for {url}")
                return result
            
            # Strategy 7: Social media preview extraction
            result = self._extract_social_preview(url, headers)
            if result.success:
                logger.info(f"Social preview extraction successful for {url}")
                return result
            
            logger.warning(f"All paywall bypass strategies failed for {url}")
            return ExtractionResult(
                success=False,
                error_message="All paywall bypass strategies failed",
                strategy_used=self.name
            )
            
        except Exception as e:
            logger.error(f"Paywall bypass extraction failed for {url}: {str(e)}")
            return ExtractionResult(
                success=False,
                error_message=str(e),
                strategy_used=self.name
            )
    
    def _fast_extraction(self, url: str, headers: dict = None) -> ExtractionResult:
        """Extract content quickly before paywall mechanisms activate."""
        try:
            # Use minimal headers to avoid triggering paywall detection
            minimal_headers = {
                'User-Agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            # Fast request with short timeout
            response = requests.get(url, headers=minimal_headers, timeout=5)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract rich content before any JavaScript paywall can activate
            content, rich_content, media_assets, formatting_data = self._extract_rich_article_content(soup, url)
            title = self._extract_title(soup)
            author = self._extract_author(soup)
            
            if content and len(content.split()) > 50:  # Minimum viable content
                # Check if this looks like truncated content
                is_truncated = self._detect_content_truncation(content, soup)
                
                quality_metrics = assess_content_quality(content, title)
                
                return ExtractionResult(
                    success=True,
                    content=content,
                    title=title,
                    author=author,
                    strategy_used=self.name,
                    quality_metrics=quality_metrics,
                    paywall_detected=is_truncated,
                    paywall_indicators=["Content truncation detected"] if is_truncated else [],
                    rich_content=rich_content,
                    media_assets=media_assets,
                    formatting_data=formatting_data
                )
            
            return ExtractionResult(success=False, error_message="Insufficient content extracted")
            
        except Exception as e:
            return ExtractionResult(success=False, error_message=f"Fast extraction failed: {str(e)}")
    
    def _extract_from_archive(self, url: str, headers: dict = None) -> ExtractionResult:
        """Extract content from archive.org or cached versions."""
        try:
            from urllib.parse import quote
            
            # Try Internet Archive Wayback Machine
            archive_url = f"https://web.archive.org/web/timemap/link/{url}"
            
            try:
                response = requests.get(archive_url, timeout=10)
                if response.status_code == 200:
                    # Parse the timemap to find recent snapshots
                    lines = response.text.strip().split('\n')
                    snapshots = []
                    
                    for line in lines:
                        if 'memento' in line and 'datetime=' in line:
                            # Extract the snapshot URL
                            parts = line.split()
                            for part in parts:
                                if part.startswith('<') and part.endswith('>'):
                                    snapshot_url = part[1:-1]  # Remove < >
                                    if 'web.archive.org/web/' in snapshot_url:
                                        snapshots.append(snapshot_url)
                    
                    # Try the most recent snapshots
                    for snapshot_url in snapshots[-3:]:  # Try last 3 snapshots
                        try:
                            snapshot_response = requests.get(snapshot_url, timeout=15)
                            if snapshot_response.status_code == 200:
                                soup = BeautifulSoup(snapshot_response.text, 'html.parser')
                                
                                # Remove archive.org navigation elements
                                for element in soup.select('#wm-ipp-base, .wb-autocomplete-suggestions'):
                                    element.decompose()
                                
                                content = self._extract_article_content(soup)
                                title = self._extract_title(soup)
                                author = self._extract_author(soup)
                                
                                if content and len(content.split()) > 50:
                                    quality_metrics = assess_content_quality(content, title)
                                    
                                    return ExtractionResult(
                                        success=True,
                                        content=content,
                                        title=title,
                                        author=author,
                                        strategy_used=self.name,
                                        quality_metrics=quality_metrics
                                    )
                        except Exception:
                            continue
            except Exception:
                pass
            
            return ExtractionResult(success=False, error_message="No usable archive content found")
            
        except Exception as e:
            return ExtractionResult(success=False, error_message=f"Archive extraction failed: {str(e)}")
    
    def _reader_mode_extraction(self, url: str, headers: dict = None) -> ExtractionResult:
        """Extract content using reader mode techniques."""
        try:
            # Use reader-friendly headers
            reader_headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache'
            }
            
            # Try to get content with reader-mode headers
            response = requests.get(url, headers=reader_headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Apply reader mode content extraction with rich content
            content, rich_content, media_assets, formatting_data = self._extract_rich_article_content(soup, url)
            title = self._extract_title(soup)
            author = self._extract_author(soup)
            
            if content and len(content.split()) > 50:
                quality_metrics = assess_content_quality(content, title)
                
                return ExtractionResult(
                    success=True,
                    content=content,
                    title=title,
                    author=author,
                    strategy_used=self.name,
                    quality_metrics=quality_metrics,
                    rich_content=rich_content,
                    media_assets=media_assets,
                    formatting_data=formatting_data
                )
            
            return ExtractionResult(success=False, error_message="Insufficient reader mode content")
            
        except Exception as e:
            return ExtractionResult(success=False, error_message=f"Reader mode extraction failed: {str(e)}")
    
    def _extract_social_preview(self, url: str, headers: dict = None) -> ExtractionResult:
        """Extract content from social media preview metadata."""
        try:
            # Use social media bot headers
            social_headers = {
                'User-Agent': 'facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive'
            }
            
            response = requests.get(url, headers=social_headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract from Open Graph and Twitter Card metadata
            title = ""
            description = ""
            
            # Try Open Graph title
            og_title = soup.find('meta', property='og:title')
            if og_title:
                title = og_title.get('content', '')
            
            # Try Twitter title
            if not title:
                twitter_title = soup.find('meta', attrs={'name': 'twitter:title'})
                if twitter_title:
                    title = twitter_title.get('content', '')
            
            # Try Open Graph description
            og_desc = soup.find('meta', property='og:description')
            if og_desc:
                description = og_desc.get('content', '')
            
            # Try Twitter description
            if not description:
                twitter_desc = soup.find('meta', attrs={'name': 'twitter:description'})
                if twitter_desc:
                    description = twitter_desc.get('content', '')
            
            # Try standard meta description
            if not description:
                meta_desc = soup.find('meta', attrs={'name': 'description'})
                if meta_desc:
                    description = meta_desc.get('content', '')
            
            # Combine title and description as content
            content_parts = []
            if title:
                content_parts.append(title)
            if description and len(description) > 50:
                content_parts.append(description)
            
            content = '\n\n'.join(content_parts)
            
            if content and len(content.split()) > 30:
                quality_metrics = assess_content_quality(content, title, description)
                
                return ExtractionResult(
                    success=True,
                    content=content,
                    title=title,
                    strategy_used=self.name,
                    quality_metrics=quality_metrics
                )
            
            return ExtractionResult(success=False, error_message="Insufficient social preview content")
            
        except Exception as e:
            return ExtractionResult(success=False, error_message=f"Social preview extraction failed: {str(e)}")
    
    def _extract_reader_content(self, soup: BeautifulSoup) -> str:
        """Extract content using reader mode algorithms."""
        # Remove unwanted elements first
        for element in soup.select('script, style, nav, header, footer, aside, .advertisement, .ad, .sidebar, .menu, .navigation'):
            element.decompose()
        
        # Reader mode content selectors (prioritized for readability)
        reader_selectors = [
            # Main content areas
            'article', '[role="main"]', 'main', '.main-content', '.article-content',
            '.post-content', '.entry-content', '.story-body', '.article-body',
            
            # Content containers
            '.content', '#content', '.article-wrap', '.article-container',
            '.post-wrap', '.post-container', '.story-wrap', '.story-container',
            
            # Text-heavy areas
            '.text-content', '.article-text', '.story-text', '.post-text',
            '.content-body', '.article-main', '.story-main', '.post-main'
        ]
        
        best_content = ""
        best_score = 0
        
        for selector in reader_selectors:
            try:
                elements = soup.select(selector)
                for element in elements:
                    # Calculate content score based on text density and structure
                    text = element.get_text(separator=' ', strip=True)
                    if not text:
                        continue
                    
                    # Score based on text length, paragraph count, and link density
                    words = text.split()
                    paragraphs = len([p for p in text.split('\n') if p.strip()])
                    links = len(element.find_all('a'))
                    
                    # Calculate score
                    word_score = min(len(words) / 100, 10)  # Up to 10 points for word count
                    paragraph_score = min(paragraphs / 5, 5)  # Up to 5 points for paragraphs
                    link_penalty = min(links / 10, 3)  # Penalty for too many links
                    
                    score = word_score + paragraph_score - link_penalty
                    
                    if score > best_score and len(words) > 30:
                        best_score = score
                        best_content = text
            except Exception:
                continue
        
        # Fallback to paragraph extraction if no good content found
        if not best_content or len(best_content.split()) < 50:
            paragraphs = soup.find_all('p')
            paragraph_texts = []
            
            for p in paragraphs:
                text = p.get_text(strip=True)
                if len(text) > 20:  # Filter out short paragraphs
                    paragraph_texts.append(text)
            
            if paragraph_texts:
                best_content = '\n\n'.join(paragraph_texts)
        
        return clean_extracted_text(best_content)
    
    def _remove_paywall_elements(self, url: str, headers: dict = None) -> ExtractionResult:
        """Remove paywall elements and extract content."""
        try:
            # Get HTML content with multiple attempts
            html = None
            
            # Try different approaches to get content
            approaches = [
                {'use_session': False, 'delay': 0.1},
                {'use_session': True, 'delay': 0.5},
                {'use_session': False, 'delay': 1.0}
            ]
            
            for approach in approaches:
                try:
                    html = get_html_content_with_session(url, headers, **approach)
                    if html and len(html) > 1000:  # Minimum viable HTML
                        break
                except Exception as e:
                    logger.warning(f"Approach {approach} failed for {url}: {str(e)}")
                    continue
            
            if not html:
                return ExtractionResult(success=False, error_message="Failed to fetch HTML content")
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # Enhanced paywall removal
            self._remove_modal_elements(soup)
            self._remove_paywall_overlays(soup)
            self._remove_subscription_prompts(soup)
            self._remove_javascript_paywalls(soup)
            self._remove_css_paywalls(soup)
            
            # Extract rich content
            content, rich_content, media_assets, formatting_data = self._extract_rich_article_content(soup, url)
            title = self._extract_title(soup)
            author = self._extract_author(soup)
            
            if content and len(content.split()) > 50:
                quality_metrics = assess_content_quality(content, title)
                
                return ExtractionResult(
                    success=True,
                    content=content,
                    title=title,
                    author=author,
                    strategy_used=self.name,
                    quality_metrics=quality_metrics,
                    rich_content=rich_content,
                    media_assets=media_assets,
                    formatting_data=formatting_data
                )
            
            return ExtractionResult(success=False, error_message="Insufficient content after paywall removal")
            
        except Exception as e:
            return ExtractionResult(success=False, error_message=f"Paywall removal failed: {str(e)}")
    
    def _remove_javascript_paywalls(self, soup: BeautifulSoup) -> None:
        """Remove JavaScript-based paywall implementations."""
        # Remove script tags that contain paywall logic
        paywall_script_patterns = [
            'paywall', 'subscription', 'premium', 'metered', 'meter',
            'registration', 'login-wall', 'auth-wall'
        ]
        
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string:
                script_content = script.string.lower()
                if any(pattern in script_content for pattern in paywall_script_patterns):
                    script.decompose()
    
    def _remove_css_paywalls(self, soup: BeautifulSoup) -> None:
        """Remove CSS-based paywall implementations."""
        # Remove style tags that contain paywall CSS
        paywall_css_patterns = [
            'paywall', 'subscription', 'premium', 'overlay', 'modal',
            'blur', 'fade-out', 'gradient'
        ]
        
        styles = soup.find_all('style')
        for style in styles:
            if style.string:
                style_content = style.string.lower()
                if any(pattern in style_content for pattern in paywall_css_patterns):
                    style.decompose()
        
        # Remove elements with paywall-related inline styles
        for element in soup.find_all(style=True):
            style_attr = element.get('style', '').lower()
            if any(pattern in style_attr for pattern in ['blur', 'opacity: 0', 'display: none', 'visibility: hidden']):
                # Check if this might be paywall-related
                element_text = element.get_text().lower()
                if any(keyword in element_text for keyword in ['article', 'content', 'story', 'text']):
                    # Remove the style attribute to reveal hidden content
                    del element['style']

    def _extract_from_initial_html(self, html: str, url: str) -> ExtractionResult:
        """Extract content from initial HTML before modal activation."""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove paywall modal elements
            self._remove_modal_elements(soup)
            
            # Extract rich content
            content, rich_content, media_assets, formatting_data = self._extract_rich_article_content(soup, url)
            title = self._extract_title(soup)
            author = self._extract_author(soup)
            
            if content and len(content.split()) > 30:
                # Check for paywall indicators in the cleaned content
                paywall_detected, paywall_indicators = detect_paywall_indicators(str(soup), url)
                
                quality_metrics = assess_content_quality(content, title)
                
                return ExtractionResult(
                    success=True,
                    content=content,
                    title=title,
                    author=author,
                    strategy_used=self.name,
                    quality_metrics=quality_metrics,
                    paywall_detected=paywall_detected,
                    paywall_indicators=paywall_indicators,
                    rich_content=rich_content,
                    media_assets=media_assets,
                    formatting_data=formatting_data
                )
            
            return ExtractionResult(success=False, error_message="Insufficient content after modal removal")
            
        except Exception as e:
            return ExtractionResult(success=False, error_message=f"Initial HTML extraction failed: {str(e)}")
    
    def _extract_from_structured_data(self, url: str, headers: dict = None) -> ExtractionResult:
        """Extract content from JSON-LD or other structured data."""
        try:
            html = get_html_content_with_session(url, headers, use_session=False, delay=0.1)
            soup = BeautifulSoup(html, 'html.parser')
            
            # Look for JSON-LD structured data
            json_scripts = soup.find_all('script', type='application/ld+json')
            
            for script in json_scripts:
                try:
                    import json
                    data = json.loads(script.string)
                    
                    # Handle both single objects and arrays
                    if isinstance(data, list):
                        data = data[0] if data else {}
                    
                    # Look for article content in structured data
                    if data.get('@type') in ['Article', 'NewsArticle', 'BlogPosting']:
                        content = data.get('articleBody', '')
                        title = data.get('headline', data.get('name', ''))
                        author = self._extract_author_from_structured_data(data)
                        
                        if content and len(content.split()) > 50:
                            quality_metrics = assess_content_quality(content, title)
                            
                            return ExtractionResult(
                                success=True,
                                content=content,
                                title=title,
                                author=author,
                                strategy_used=self.name,
                                quality_metrics=quality_metrics
                            )
                
                except (json.JSONDecodeError, KeyError):
                    continue
            
            return ExtractionResult(success=False, error_message="No usable structured data found")
            
        except Exception as e:
            return ExtractionResult(success=False, error_message=f"Structured data extraction failed: {str(e)}")
    
    def _remove_modal_elements(self, soup: BeautifulSoup) -> None:
        """Remove paywall modal elements from soup."""
        # Common modal selectors
        modal_selectors = [
            # Generic modal classes
            '[class*="modal"]', '[class*="popup"]', '[class*="overlay"]',
            '[class*="paywall"]', '[class*="subscription"]', '[class*="premium"]',
            
            # Specific paywall modal classes
            '.paywall-modal', '.subscription-modal', '.premium-modal',
            '.paywall-overlay', '.subscription-overlay', '.premium-overlay',
            '.paywall-popup', '.subscription-popup', '.premium-popup',
            
            # Registration/login modals
            '.registration-modal', '.login-modal', '.signup-modal',
            '.register-modal', '.auth-modal',
            
            # Common modal containers
            '.modal-container', '.popup-container', '.overlay-container',
            '.modal-backdrop', '.popup-backdrop', '.overlay-backdrop',
            
            # Z-index based (often modals have high z-index)
            '[style*="z-index: 999"]', '[style*="z-index: 9999"]',
            '[style*="position: fixed"]'
        ]
        
        for selector in modal_selectors:
            try:
                elements = soup.select(selector)
                for element in elements:
                    # Check if this looks like a paywall modal
                    element_text = element.get_text().lower()
                    if any(keyword in element_text for keyword in [
                        'subscribe', 'premium', 'paywall', 'register', 'login',
                        'membership', 'subscription', 'continue reading'
                    ]):
                        element.decompose()
            except Exception:
                continue
    
    def _remove_paywall_overlays(self, soup: BeautifulSoup) -> None:
        """Remove paywall overlay elements."""
        overlay_selectors = [
            '.paywall-overlay', '.subscription-overlay', '.premium-overlay',
            '.paywall-barrier', '.subscription-barrier', '.premium-barrier',
            '.paywall-wall', '.subscription-wall', '.premium-wall',
            '[class*="paywall-"]', '[class*="subscription-"]', '[class*="premium-"]'
        ]
        
        for selector in overlay_selectors:
            try:
                elements = soup.select(selector)
                for element in elements:
                    element.decompose()
            except Exception:
                continue
    
    def _remove_subscription_prompts(self, soup: BeautifulSoup) -> None:
        """Remove subscription prompt elements."""
        # Remove elements with subscription-related text
        for element in soup.find_all(text=True):
            if isinstance(element.parent, (soup.find('script').__class__, soup.find('style').__class__)):
                continue
            
            text = element.strip().lower()
            if any(keyword in text for keyword in [
                'subscribe to continue', 'subscription required', 'premium content',
                'register to read', 'login to continue', 'become a member'
            ]):
                # Remove the parent element
                try:
                    element.parent.decompose()
                except Exception:
                    continue
    
    def _extract_article_content(self, soup: BeautifulSoup) -> str:
        """Extract main article content using multiple strategies."""
        content_selectors = [
            # Common article content selectors
            'article', '.article-content', '.article-body', '.article-text',
            '.post-content', '.post-body', '.entry-content', '.content',
            '.story-body', '.story-content', '.main-content',
            
            # Publisher-specific selectors
            '.ArticleBody', '.RichTextArticleBody', '.ArticleBodyWrapper',
            '.story-body-text', '.article-wrap', '.article-container',
            
            # Semantic HTML5
            '[role="main"]', 'main', '.main',
            
            # Paragraph-based extraction
            '.article p', 'article p', '.content p', '.story p'
        ]
        
        for selector in content_selectors:
            try:
                elements = soup.select(selector)
                if elements:
                    # Get the largest content block
                    largest_element = max(elements, key=lambda x: len(x.get_text()))
                    content = largest_element.get_text(separator=' ', strip=True)
                    
                    if len(content.split()) > 30:  # Minimum viable content
                        return clean_extracted_text(content)
            except Exception:
                continue
        
        # Fallback: extract all paragraphs
        paragraphs = soup.find_all('p')
        if paragraphs:
            content = ' '.join([p.get_text(strip=True) for p in paragraphs])
            return clean_extracted_text(content)
        
        return ""
    
    def _extract_rich_article_content(self, soup: BeautifulSoup, url: str) -> Tuple[str, dict, list, dict]:
        """Extract rich article content including media and formatting."""
        try:
            # Initialize rich content extractor
            rich_extractor = RichContentExtractor()
            
            # Extract rich content
            rich_content, media_assets, formatting_data = rich_extractor.extract_rich_content(soup, url)
            
            # Also extract plain text content for backward compatibility
            text_content = self._extract_article_content(soup)
            
            return text_content, rich_content, media_assets, formatting_data
            
        except Exception as e:
            logger.warning(f"Rich content extraction failed: {str(e)}")
            # Fallback to plain text extraction
            text_content = self._extract_article_content(soup)
            return text_content, {"blocks": []}, [], {}
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract article title."""
        title_selectors = [
            'h1', '.article-title', '.post-title', '.entry-title',
            '.headline', '.story-headline', '.article-headline',
            '[property="og:title"]', '[name="twitter:title"]'
        ]
        
        for selector in title_selectors:
            try:
                element = soup.select_one(selector)
                if element:
                    if element.name == 'meta':
                        return element.get('content', '').strip()
                    else:
                        return element.get_text(strip=True)
            except Exception:
                continue
        
        # Fallback to page title
        title_tag = soup.find('title')
        if title_tag:
            return title_tag.get_text(strip=True)
        
        return ""
    
    def _extract_author(self, soup: BeautifulSoup) -> str:
        """Extract article author."""
        author_selectors = [
            '.author', '.byline', '.article-author', '.post-author',
            '.story-author', '[rel="author"]', '.author-name',
            '[property="article:author"]', '[name="author"]'
        ]
        
        for selector in author_selectors:
            try:
                element = soup.select_one(selector)
                if element:
                    if element.name == 'meta':
                        return element.get('content', '').strip()
                    else:
                        return element.get_text(strip=True)
            except Exception:
                continue
        
        return ""
    
    def _extract_author_from_structured_data(self, data: dict) -> str:
        """Extract author from structured data."""
        author = data.get('author', {})
        if isinstance(author, dict):
            return author.get('name', '')
        elif isinstance(author, list) and author:
            first_author = author[0]
            if isinstance(first_author, dict):
                return first_author.get('name', '')
            return str(first_author)
        elif isinstance(author, str):
            return author
        return ""
    
    def _detect_content_truncation(self, content: str, soup: BeautifulSoup) -> bool:
        """Detect if content appears to be truncated by paywall."""
        # Check for truncation indicators
        truncation_indicators = [
            'continue reading', 'read more', 'subscribe to continue',
            'this article continues', 'full article available',
            'premium subscribers', 'members only'
        ]
        
        content_lower = content.lower()
        for indicator in truncation_indicators:
            if indicator in content_lower:
                return True
        
        # Check if content ends abruptly (no proper conclusion)
        sentences = content.split('.')
        if len(sentences) > 2:
            last_sentence = sentences[-2].strip()  # -1 is usually empty after split
            if len(last_sentence.split()) < 5:  # Very short last sentence
                return True
        
        # Check for paywall elements in the soup
        paywall_elements = soup.find_all(text=lambda text: text and any(
            keyword in text.lower() for keyword in truncation_indicators
        ))
        
        return len(paywall_elements) > 0


class RichContentExtractor:
    """Extracts rich content including media, formatting, and structure."""
    
    def __init__(self):
        self.position_counter = 0
    
    def extract_rich_content(self, soup: BeautifulSoup, base_url: str) -> Tuple[dict, list, dict]:
        """
        Extract rich content from BeautifulSoup object.
        
        Returns:
            Tuple[dict, list, dict]: (rich_content, media_assets, formatting_data)
        """
        self.position_counter = 0
        
        # Extract media assets
        media_assets = []
        media_assets.extend(self.extract_images(soup, base_url))
        media_assets.extend(self.extract_videos(soup, base_url))
        media_assets.extend(self.extract_audio(soup, base_url))
        
        # Build structured content blocks
        rich_content = self.build_content_structure(soup, media_assets)
        
        # Extract formatting data
        formatting_data = self.extract_formatting(soup)
        
        return rich_content, media_assets, formatting_data
    
    def extract_images(self, soup: BeautifulSoup, base_url: str) -> list:
        """Extract images with metadata."""
        images = []
        
        for img in soup.find_all('img'):
            try:
                src = img.get('src', '')
                if not src:
                    continue
                
                # Convert relative URLs to absolute
                if src.startswith('//'):
                    src = 'https:' + src
                elif src.startswith('/'):
                    from urllib.parse import urljoin
                    src = urljoin(base_url, src)
                elif not src.startswith(('http://', 'https://')):
                    from urllib.parse import urljoin
                    src = urljoin(base_url, src)
                
                # Get image metadata
                alt_text = img.get('alt', '')
                title = img.get('title', '')
                width = img.get('width')
                height = img.get('height')
                
                # Try to find caption
                caption = self._find_image_caption(img)
                
                # Get surrounding context
                context = self._get_surrounding_text(img)
                
                image_data = {
                    "type": "image",
                    "src": src,
                    "alt": alt_text,
                    "title": title,
                    "caption": caption,
                    "position": self._get_element_position(img),
                    "context": context,
                    "metadata": {
                        "width": int(width) if width and width.isdigit() else None,
                        "height": int(height) if height and height.isdigit() else None,
                        "format": self._get_image_format(src),
                        "classes": img.get('class', []),
                        "style": img.get('style', '')
                    }
                }
                
                images.append(image_data)
                
            except Exception as e:
                logger.warning(f"Error extracting image: {str(e)}")
                continue
        
        return images
    
    def extract_videos(self, soup: BeautifulSoup, base_url: str) -> list:
        """Extract videos with metadata."""
        videos = []
        
        # Extract HTML5 video elements
        for video in soup.find_all('video'):
            try:
                src = video.get('src')
                if not src:
                    # Check for source elements
                    source = video.find('source')
                    if source:
                        src = source.get('src')
                
                if src:
                    # Convert relative URLs to absolute
                    if src.startswith('/'):
                        from urllib.parse import urljoin
                        src = urljoin(base_url, src)
                    
                    video_data = {
                        "type": "video",
                        "src": src,
                        "poster": video.get('poster', ''),
                        "caption": self._find_video_caption(video),
                        "position": self._get_element_position(video),
                        "context": self._get_surrounding_text(video),
                        "metadata": {
                            "width": video.get('width'),
                            "height": video.get('height'),
                            "controls": video.has_attr('controls'),
                            "autoplay": video.has_attr('autoplay'),
                            "loop": video.has_attr('loop'),
                            "muted": video.has_attr('muted')
                        }
                    }
                    
                    videos.append(video_data)
                    
            except Exception as e:
                logger.warning(f"Error extracting video: {str(e)}")
                continue
        
        # Extract embedded videos (YouTube, Vimeo, etc.)
        for iframe in soup.find_all('iframe'):
            try:
                src = iframe.get('src', '')
                if any(domain in src for domain in ['youtube.com', 'youtu.be', 'vimeo.com', 'dailymotion.com']):
                    video_data = {
                        "type": "video_embed",
                        "src": src,
                        "platform": self._get_video_platform(src),
                        "caption": self._find_video_caption(iframe),
                        "position": self._get_element_position(iframe),
                        "context": self._get_surrounding_text(iframe),
                        "metadata": {
                            "width": iframe.get('width'),
                            "height": iframe.get('height'),
                            "frameborder": iframe.get('frameborder'),
                            "allowfullscreen": iframe.has_attr('allowfullscreen')
                        }
                    }
                    
                    videos.append(video_data)
                    
            except Exception as e:
                logger.warning(f"Error extracting embedded video: {str(e)}")
                continue
        
        return videos
    
    def extract_audio(self, soup: BeautifulSoup, base_url: str) -> list:
        """Extract audio files with metadata."""
        audio_files = []
        
        for audio in soup.find_all('audio'):
            try:
                src = audio.get('src')
                if not src:
                    # Check for source elements
                    source = audio.find('source')
                    if source:
                        src = source.get('src')
                
                if src:
                    # Convert relative URLs to absolute
                    if src.startswith('/'):
                        from urllib.parse import urljoin
                        src = urljoin(base_url, src)
                    
                    audio_data = {
                        "type": "audio",
                        "src": src,
                        "caption": self._find_audio_caption(audio),
                        "position": self._get_element_position(audio),
                        "context": self._get_surrounding_text(audio),
                        "metadata": {
                            "controls": audio.has_attr('controls'),
                            "autoplay": audio.has_attr('autoplay'),
                            "loop": audio.has_attr('loop'),
                            "muted": audio.has_attr('muted'),
                            "preload": audio.get('preload', 'metadata')
                        }
                    }
                    
                    audio_files.append(audio_data)
                    
            except Exception as e:
                logger.warning(f"Error extracting audio: {str(e)}")
                continue
        
        return audio_files
    
    def build_content_structure(self, soup: BeautifulSoup, media_assets: list) -> dict:
        """Build structured content blocks preserving order and formatting."""
        blocks = []
        self.position_counter = 0
        
        # Find main content area
        content_area = self._find_main_content_area(soup)
        if not content_area:
            content_area = soup
        
        # Process elements in order
        for element in content_area.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'blockquote', 'ul', 'ol', 'pre', 'code', 'img', 'video', 'audio', 'iframe']):
            try:
                block = self._element_to_block(element, media_assets)
                if block:
                    blocks.append(block)
            except Exception as e:
                logger.warning(f"Error processing element {element.name}: {str(e)}")
                continue
        
        return {"blocks": blocks}
    
    def extract_formatting(self, soup: BeautifulSoup) -> dict:
        """Extract formatting and typography information."""
        formatting = {
            "headings": [],
            "emphasis": [],
            "links": [],
            "lists": [],
            "quotes": [],
            "code_blocks": []
        }
        
        # Extract headings
        for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            formatting["headings"].append({
                "level": int(heading.name[1]),
                "text": heading.get_text(strip=True),
                "id": heading.get('id', ''),
                "classes": heading.get('class', [])
            })
        
        # Extract emphasis (bold, italic)
        for em in soup.find_all(['em', 'i', 'strong', 'b']):
            formatting["emphasis"].append({
                "type": em.name,
                "text": em.get_text(strip=True),
                "context": self._get_surrounding_text(em, 50)
            })
        
        # Extract links
        for link in soup.find_all('a', href=True):
            formatting["links"].append({
                "text": link.get_text(strip=True),
                "href": link['href'],
                "title": link.get('title', ''),
                "target": link.get('target', '')
            })
        
        # Extract lists
        for list_elem in soup.find_all(['ul', 'ol']):
            items = [li.get_text(strip=True) for li in list_elem.find_all('li')]
            formatting["lists"].append({
                "type": list_elem.name,
                "items": items,
                "classes": list_elem.get('class', [])
            })
        
        # Extract quotes
        for quote in soup.find_all('blockquote'):
            formatting["quotes"].append({
                "text": quote.get_text(strip=True),
                "cite": quote.get('cite', ''),
                "classes": quote.get('class', [])
            })
        
        # Extract code blocks
        for code in soup.find_all(['pre', 'code']):
            formatting["code_blocks"].append({
                "type": code.name,
                "content": code.get_text(),
                "language": self._detect_code_language(code),
                "classes": code.get('class', [])
            })
        
        return formatting
    
    # Helper methods
    def _find_image_caption(self, img) -> str:
        """Find caption for an image."""
        # Check for figcaption
        figure = img.find_parent('figure')
        if figure:
            figcaption = figure.find('figcaption')
            if figcaption:
                return figcaption.get_text(strip=True)
        
        # Check for nearby caption elements
        for sibling in [img.next_sibling, img.previous_sibling]:
            if sibling and hasattr(sibling, 'get_text'):
                text = sibling.get_text(strip=True)
                if text and len(text) < 200 and any(word in text.lower() for word in ['caption', 'photo', 'image']):
                    return text
        
        return ""
    
    def _find_video_caption(self, video) -> str:
        """Find caption for a video."""
        # Similar logic to image captions
        figure = video.find_parent('figure')
        if figure:
            figcaption = figure.find('figcaption')
            if figcaption:
                return figcaption.get_text(strip=True)
        return ""
    
    def _find_audio_caption(self, audio) -> str:
        """Find caption for an audio element."""
        figure = audio.find_parent('figure')
        if figure:
            figcaption = figure.find('figcaption')
            if figcaption:
                return figcaption.get_text(strip=True)
        return ""
    
    def _get_surrounding_text(self, element, max_length: int = 100) -> str:
        """Get surrounding text context for an element."""
        context_parts = []
        
        # Get previous text
        prev = element.previous_sibling
        while prev and len(' '.join(context_parts)) < max_length // 2:
            if hasattr(prev, 'get_text'):
                text = prev.get_text(strip=True)
                if text:
                    context_parts.insert(0, text)
            prev = prev.previous_sibling
        
        # Get next text
        next_elem = element.next_sibling
        while next_elem and len(' '.join(context_parts)) < max_length:
            if hasattr(next_elem, 'get_text'):
                text = next_elem.get_text(strip=True)
                if text:
                    context_parts.append(text)
            next_elem = next_elem.next_sibling
        
        return ' '.join(context_parts)[:max_length]
    
    def _get_element_position(self, element) -> int:
        """Get the position of an element in the document."""
        self.position_counter += 1
        return self.position_counter
    
    def _get_image_format(self, src: str) -> str:
        """Extract image format from URL."""
        import os
        _, ext = os.path.splitext(src.split('?')[0])  # Remove query params
        return ext.lower().lstrip('.')
    
    def _get_video_platform(self, src: str) -> str:
        """Identify video platform from URL."""
        if 'youtube.com' in src or 'youtu.be' in src:
            return 'youtube'
        elif 'vimeo.com' in src:
            return 'vimeo'
        elif 'dailymotion.com' in src:
            return 'dailymotion'
        else:
            return 'unknown'
    
    def _find_main_content_area(self, soup: BeautifulSoup):
        """Find the main content area of the page."""
        # Try common content selectors
        content_selectors = [
            'article', '[role="main"]', 'main', '.article-content',
            '.post-content', '.entry-content', '.story-body', '.content'
        ]
        
        for selector in content_selectors:
            content_area = soup.select_one(selector)
            if content_area:
                return content_area
        
        return None
    
    def _element_to_block(self, element, media_assets: list) -> dict:
        """Convert an HTML element to a content block."""
        tag_name = element.name.lower()
        
        if tag_name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            return {
                "type": "heading",
                "level": int(tag_name[1]),
                "content": element.get_text(strip=True),
                "position": self._get_element_position(element),
                "id": element.get('id', ''),
                "classes": element.get('class', [])
            }
        
        elif tag_name == 'p':
            text = element.get_text(strip=True)
            if text:
                return {
                    "type": "paragraph",
                    "content": str(element),  # Preserve inner HTML for formatting
                    "text": text,
                    "position": self._get_element_position(element),
                    "classes": element.get('class', [])
                }
        
        elif tag_name == 'blockquote':
            return {
                "type": "quote",
                "content": element.get_text(strip=True),
                "cite": element.get('cite', ''),
                "position": self._get_element_position(element),
                "classes": element.get('class', [])
            }
        
        elif tag_name in ['ul', 'ol']:
            items = [li.get_text(strip=True) for li in element.find_all('li')]
            return {
                "type": "list",
                "list_type": tag_name,
                "items": items,
                "position": self._get_element_position(element),
                "classes": element.get('class', [])
            }
        
        elif tag_name in ['pre', 'code']:
            return {
                "type": "code",
                "content": element.get_text(),
                "language": self._detect_code_language(element),
                "position": self._get_element_position(element),
                "classes": element.get('class', [])
            }
        
        elif tag_name in ['img', 'video', 'audio', 'iframe']:
            # Find corresponding media asset
            for asset in media_assets:
                if asset.get('position') == self._get_element_position(element):
                    return {
                        "type": asset['type'],
                        "media_id": len(media_assets),  # Reference to media asset
                        "position": asset['position'],
                        **asset
                    }
        
        return None
    
    def _detect_code_language(self, element) -> str:
        """Detect programming language from code element."""
        classes = element.get('class', [])
        for cls in classes:
            if cls.startswith('language-'):
                return cls.replace('language-', '')
            elif cls.startswith('lang-'):
                return cls.replace('lang-', '')
        return ""


class ContentExtractor:
    """Main content extractor that tries multiple strategies."""
    
    def __init__(self):
        self.strategies = [
            PublisherAPIStrategy(),  # Try publisher-specific methods first
            PaywallBypassStrategy(),  # Try paywall bypass early for paywalled content
            NewspaperStrategy(),
            ReadabilityStrategy(),
            BeautifulSoupStrategy(),
            StealthStrategy(),
            RSSEnhancedStrategy(),  # Add as fallback strategy
        ]
        
        # Filter to only available strategies
        self.strategies = [s for s in self.strategies if s.available]
        
        if not self.strategies:
            logger.warning("No content extraction strategies available!")
    
    def extract_content(self, url: str, user_agent: str = None, article=None) -> ExtractionResult:
        """
        Extract content using the best available strategy.
        
        Args:
            url (str): URL to extract content from
            user_agent (str): User agent to use for requests
            article: Article instance for RSS enhanced strategy
            
        Returns:
            ExtractionResult: Extraction result
        """
        if not self.strategies:
            return ExtractionResult(
                success=False,
                error_message="No extraction strategies available",
                strategy_used="none"
            )
        
        headers = get_request_headers(user_agent) if user_agent else {}
        
        # Try each strategy in order
        for strategy in self.strategies:
            logger.info(f"Trying {strategy.name} strategy for {url}")
            
            # Special handling for RSS Enhanced strategy
            if strategy.name == "rss_enhanced" and article:
                result = strategy.extract_from_article(article)
            else:
                result = strategy.extract(url, headers=headers)
            
            if result.success and result.content:
                # Validate content quality before accepting
                if self._is_valid_text_content(result.content):
                    logger.info(f"Successfully extracted content using {strategy.name}")
                    return result
                else:
                    logger.warning(f"{strategy.name} returned corrupted content, trying next strategy")
                    continue
            elif result.paywall_detected:
                logger.warning(f"Paywall detected by {strategy.name} for {url}")
                return result  # Don't try other strategies if paywall detected
            else:
                logger.warning(f"{strategy.name} failed: {result.error_message}")
        
        # All strategies failed
        return ExtractionResult(
            success=False,
            error_message="All extraction strategies failed",
            strategy_used="multiple_failed"
        )
    
    def _is_valid_text_content(self, content: str) -> bool:
        """Check if content is valid text (not corrupted/binary)."""
        if not content:
            return False
        
        # Check for binary/corrupted content indicators
        try:
            # Try to encode/decode to check for valid text
            content.encode('utf-8').decode('utf-8')
            
            # Check for excessive non-printable characters
            printable_chars = sum(1 for c in content if c.isprintable() or c.isspace())
            total_chars = len(content)
            
            if total_chars == 0:
                return False
            
            printable_ratio = printable_chars / total_chars
            
            # If less than 80% printable characters, likely corrupted
            if printable_ratio < 0.8:
                return False
            
            # Check for reasonable word structure
            words = content.split()
            if len(words) < 5:  # Too few words
                return False
            
            # Check average word length (should be reasonable for text)
            avg_word_length = sum(len(word) for word in words) / len(words)
            if avg_word_length > 20 or avg_word_length < 2:  # Unreasonable word lengths
                return False
            
            return True
            
        except (UnicodeDecodeError, UnicodeEncodeError):
            return False 