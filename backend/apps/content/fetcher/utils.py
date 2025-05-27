import re
import requests
from urllib.parse import urlparse, urljoin
from typing import List, Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


def validate_url(url: str) -> bool:
    """
    Validate if a URL is properly formatted and accessible.
    
    Args:
        url (str): URL to validate
        
    Returns:
        bool: True if URL is valid, False otherwise
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def normalize_url(url: str) -> str:
    """
    Normalize URL by removing tracking parameters and fragments.
    
    Args:
        url (str): URL to normalize
        
    Returns:
        str: Normalized URL
    """
    try:
        # First, decode any Unicode escape sequences in the URL
        try:
            # Handle Unicode escapes like \u003d (which is =)
            # Also handle double-escaped sequences like \\u003d
            if '\\\\u' in url:
                # Double-escaped: \\u003d -> \u003d -> =
                url = url.replace('\\\\u', '\\u')
                url = url.encode().decode('unicode_escape')
            elif '\\u' in url:
                # Single-escaped: \u003d -> =
                url = url.encode().decode('unicode_escape')
        except (UnicodeDecodeError, UnicodeEncodeError):
            # If decoding fails, continue with original URL
            pass
        
        parsed = urlparse(url)
        
        # Remove common tracking parameters
        tracking_params = [
            'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
            'fbclid', 'gclid', 'ref', 'source', 'campaign'
        ]
        
        # Keep only non-tracking query parameters
        if parsed.query:
            query_params = []
            for param in parsed.query.split('&'):
                if '=' in param:
                    key, value = param.split('=', 1)
                    if key.lower() not in tracking_params:
                        query_params.append(param)
            query = '&'.join(query_params)
        else:
            query = ''
        
        # Reconstruct URL without fragment and tracking params
        normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        if query:
            normalized += f"?{query}"
            
        return normalized
    except Exception:
        return url


def get_user_agents() -> List[str]:
    """
    Get a list of realistic user agents to rotate through for web scraping.
    
    Returns:
        List[str]: List of user agent strings
    """
    return [
        # Chrome on Windows (latest versions)
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        # Chrome on macOS
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        # Firefox on Windows
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        # Firefox on macOS
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0',
        # Safari on macOS
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
        # Edge on Windows
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0',
        # Chrome on Linux (for variety)
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
    ]


def detect_paywall_indicators(html: str, url: str) -> Tuple[bool, List[str]]:
    """
    Detect paywall indicators with enhanced detection for modal and truncation patterns.
    
    Args:
        html (str): HTML content to analyze
        url (str): URL of the page
        
    Returns:
        Tuple[bool, List[str]]: (paywall_detected, list_of_indicators)
    """
    indicators = []
    html_lower = html.lower()
    
    # Strong paywall indicators (high confidence)
    strong_paywall_patterns = [
        r'subscribe to continue reading this article',
        r'subscription required to view this content',
        r'please subscribe to access this article',
        r'sign up to continue reading this story',
        r'become a member to read this article',
        r'upgrade to premium to continue reading',
        r'you have reached your free article limit',
        r'register to continue reading this article',
        r'login to continue reading this content'
    ]
    
    strong_indicators = 0
    for pattern in strong_paywall_patterns:
        if re.search(pattern, html_lower):
            indicators.append(f"Strong paywall pattern: {pattern}")
            strong_indicators += 1
    
    # Enhanced modal detection patterns
    modal_paywall_patterns = [
        r'paywall-modal', r'subscription-modal', r'premium-modal',
        r'paywall-overlay', r'subscription-overlay', r'premium-overlay',
        r'paywall-popup', r'subscription-popup', r'premium-popup',
        r'modal.*subscribe', r'modal.*premium', r'modal.*paywall',
        r'popup.*subscribe', r'popup.*premium', r'popup.*paywall',
        r'overlay.*subscribe', r'overlay.*premium', r'overlay.*paywall'
    ]
    
    modal_indicators = 0
    for pattern in modal_paywall_patterns:
        if re.search(pattern, html_lower):
            indicators.append(f"Modal paywall pattern: {pattern}")
            modal_indicators += 1
    
    # Content truncation indicators
    truncation_patterns = [
        r'continue reading to see',
        r'this article continues',
        r'read the full article',
        r'full story available to',
        r'complete article available',
        r'story continues below',
        r'article continues after',
        r'to read the rest',
        r'unlock this article',
        r'access the full story'
    ]
    
    truncation_indicators = 0
    for pattern in truncation_patterns:
        if re.search(pattern, html_lower):
            indicators.append(f"Content truncation pattern: {pattern}")
            truncation_indicators += 1
    
    # Medium confidence patterns (need context)
    medium_paywall_patterns = [
        r'subscribe to continue reading',
        r'subscription required',
        r'this article is for subscribers only',
        r'premium content ahead',
        r'members only content',
        r'exclusive to subscribers',
        r'subscriber exclusive'
    ]
    
    medium_indicators = 0
    for pattern in medium_paywall_patterns:
        if re.search(pattern, html_lower):
            indicators.append(f"Medium paywall pattern: {pattern}")
            medium_indicators += 1
    
    # Enhanced CSS/JavaScript paywall detection
    paywall_selectors = [
        'paywall-container', 'subscription-wall', 'premium-content-wall',
        'subscriber-only-content', 'registration-required', 'login-required',
        'paywall-overlay', 'subscription-barrier', 'paywall-modal',
        'subscription-modal', 'premium-modal', 'paywall-popup',
        'subscription-popup', 'premium-popup'
    ]
    
    css_indicators = 0
    for selector in paywall_selectors:
        if f'class="{selector}"' in html_lower or f'id="{selector}"' in html_lower:
            indicators.append(f"CSS selector: {selector}")
            css_indicators += 1
    
    # JavaScript paywall detection
    js_paywall_patterns = [
        r'paywall\.show\(\)', r'showPaywall\(\)', r'displayPaywall\(\)',
        r'subscription\.modal', r'premium\.modal', r'paywall\.modal',
        r'showSubscriptionModal', r'displaySubscriptionWall',
        r'paywallActivated', r'subscriptionRequired'
    ]
    
    js_indicators = 0
    for pattern in js_paywall_patterns:
        if re.search(pattern, html_lower):
            indicators.append(f"JavaScript paywall: {pattern}")
            js_indicators += 1
    
    # Check for subscription-related meta tags
    meta_patterns = [
        r'<meta[^>]*name=["\']?article:content_tier["\']?[^>]*content=["\']?premium["\']?',
        r'<meta[^>]*property=["\']?article:content_tier["\']?[^>]*content=["\']?premium["\']?',
        r'<meta[^>]*name=["\']?subscription["\']?[^>]*content=["\']?required["\']?',
        r'<meta[^>]*name=["\']?paywall["\']?[^>]*content=["\']?true["\']?'
    ]
    
    meta_indicators = 0
    for pattern in meta_patterns:
        if re.search(pattern, html_lower):
            indicators.append("Meta tag: premium/subscription content")
            meta_indicators += 1
    
    # Domain-based detection (only for known strict paywalls)
    domain = urlparse(url).netloc.lower()
    strict_paywall_domains = [
        'nytimes.com', 'wsj.com', 'ft.com', 'economist.com',
        'washingtonpost.com', 'newyorker.com', 'theatlantic.com',
        'bloomberg.com', 'reuters.com'
    ]
    
    domain_indicator = False
    for paywall_domain in strict_paywall_domains:
        if paywall_domain in domain:
            indicators.append(f"Known strict paywall domain: {paywall_domain}")
            domain_indicator = True
            break
    
    # Enhanced decision logic with modal and truncation detection
    is_paywall = False
    
    if strong_indicators >= 1:
        # One strong indicator is enough
        is_paywall = True
    elif modal_indicators >= 1 and (medium_indicators >= 1 or css_indicators >= 1):
        # Modal paywall detected with supporting evidence
        is_paywall = True
    elif truncation_indicators >= 1 and (medium_indicators >= 1 or css_indicators >= 1):
        # Content truncation detected with supporting evidence
        is_paywall = True
    elif js_indicators >= 1 and (css_indicators >= 1 or medium_indicators >= 1):
        # JavaScript paywall with supporting evidence
        is_paywall = True
    elif medium_indicators >= 2 and css_indicators >= 1:
        # Multiple medium indicators + CSS evidence
        is_paywall = True
    elif domain_indicator and (medium_indicators >= 1 or css_indicators >= 1 or modal_indicators >= 1):
        # Known paywall domain + some evidence
        is_paywall = True
    elif meta_indicators >= 1 and (medium_indicators >= 1 or css_indicators >= 1):
        # Meta tag evidence + other indicators
        is_paywall = True
    
    return is_paywall, indicators


def detect_paywall_modal_patterns(html: str) -> Tuple[bool, List[str]]:
    """
    Specifically detect paywall modal patterns in HTML.
    
    Args:
        html (str): HTML content to analyze
        
    Returns:
        Tuple[bool, List[str]]: (modal_detected, list_of_modal_indicators)
    """
    indicators = []
    html_lower = html.lower()
    
    # Modal structure patterns
    modal_structure_patterns = [
        r'<div[^>]*class="[^"]*modal[^"]*paywall[^"]*"',
        r'<div[^>]*class="[^"]*paywall[^"]*modal[^"]*"',
        r'<div[^>]*class="[^"]*subscription[^"]*modal[^"]*"',
        r'<div[^>]*class="[^"]*premium[^"]*modal[^"]*"',
        r'<div[^>]*id="[^"]*paywall[^"]*modal[^"]*"',
        r'<div[^>]*id="[^"]*subscription[^"]*modal[^"]*"'
    ]
    
    structure_indicators = 0
    for pattern in modal_structure_patterns:
        if re.search(pattern, html_lower):
            indicators.append(f"Modal structure: {pattern}")
            structure_indicators += 1
    
    # Modal content patterns
    modal_content_patterns = [
        r'subscribe to continue reading',
        r'unlock this article',
        r'become a subscriber',
        r'start your subscription',
        r'subscribe now to read',
        r'premium subscribers only',
        r'exclusive subscriber content'
    ]
    
    content_indicators = 0
    for pattern in modal_content_patterns:
        if re.search(pattern, html_lower):
            indicators.append(f"Modal content: {pattern}")
            content_indicators += 1
    
    # CSS overlay patterns
    overlay_patterns = [
        r'position:\s*fixed.*z-index:\s*\d{3,}',
        r'z-index:\s*\d{3,}.*position:\s*fixed',
        r'overlay.*paywall', r'paywall.*overlay',
        r'backdrop.*subscription', r'subscription.*backdrop'
    ]
    
    overlay_indicators = 0
    for pattern in overlay_patterns:
        if re.search(pattern, html_lower):
            indicators.append(f"CSS overlay: {pattern}")
            overlay_indicators += 1
    
    # Determine if modal paywall is detected
    modal_detected = (
        structure_indicators >= 1 or
        (content_indicators >= 1 and overlay_indicators >= 1) or
        content_indicators >= 2
    )
    
    return modal_detected, indicators


def detect_content_truncation_patterns(html: str, content: str) -> Tuple[bool, List[str]]:
    """
    Detect if content appears to be truncated by paywall mechanisms.
    
    Args:
        html (str): HTML content to analyze
        content (str): Extracted text content
        
    Returns:
        Tuple[bool, List[str]]: (truncation_detected, list_of_truncation_indicators)
    """
    indicators = []
    
    # Content-based truncation indicators
    content_lower = content.lower() if content else ""
    
    truncation_phrases = [
        'continue reading', 'read more', 'subscribe to continue',
        'this article continues', 'full article available',
        'premium subscribers', 'members only', 'exclusive content',
        'unlock the full story', 'access the complete article'
    ]
    
    phrase_indicators = 0
    for phrase in truncation_phrases:
        if phrase in content_lower:
            indicators.append(f"Truncation phrase in content: {phrase}")
            phrase_indicators += 1
    
    # HTML-based truncation indicators
    html_lower = html.lower() if html else ""
    
    html_truncation_patterns = [
        r'<div[^>]*class="[^"]*truncated[^"]*"',
        r'<div[^>]*class="[^"]*fade[^"]*out[^"]*"',
        r'<div[^>]*class="[^"]*gradient[^"]*overlay[^"]*"',
        r'style="[^"]*overflow:\s*hidden[^"]*".*paywall',
        r'style="[^"]*max-height:\s*\d+px[^"]*".*subscription'
    ]
    
    html_indicators = 0
    for pattern in html_truncation_patterns:
        if re.search(pattern, html_lower):
            indicators.append(f"HTML truncation pattern: {pattern}")
            html_indicators += 1
    
    # Content structure analysis
    if content:
        sentences = content.split('.')
        words = content.split()
        
        # Check for abrupt ending
        if len(sentences) > 2:
            last_sentence = sentences[-2].strip()
            if len(last_sentence.split()) < 5:
                indicators.append("Content ends abruptly (short last sentence)")
        
        # Check for insufficient content length
        if len(words) < 100 and any(phrase in content_lower for phrase in truncation_phrases):
            indicators.append("Short content with truncation indicators")
    
    # Determine if truncation is detected
    truncation_detected = (
        phrase_indicators >= 1 or
        html_indicators >= 1 or
        len(indicators) >= 2
    )
    
    return truncation_detected, indicators


def clean_extracted_text(text: str) -> str:
    """
    Clean and normalize extracted text content.
    
    Args:
        text (str): Raw extracted text
        
    Returns:
        str: Cleaned text
    """
    if not text:
        return ""
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove common boilerplate text
    boilerplate_patterns = [
        r'subscribe to our newsletter',
        r'follow us on social media',
        r'share this article',
        r'advertisement',
        r'sponsored content',
        r'related articles?:?',
        r'you might also like',
        r'recommended for you',
        r'trending now',
        r'most popular',
        r'cookie policy',
        r'privacy policy',
        r'terms of service'
    ]
    
    for pattern in boilerplate_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    # Remove URLs
    text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
    
    # Remove email addresses
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '', text)
    
    # Clean up whitespace again
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


def assess_content_quality(text: str, title: str = "", description: str = "") -> Dict[str, float]:
    """
    Assess the quality and completeness of extracted content.
    
    Args:
        text (str): Extracted content text
        title (str): Article title
        description (str): Article description
        
    Returns:
        Dict[str, float]: Quality metrics (0.0-1.0)
    """
    if not text:
        return {
            'completeness': 0.0,
            'quality': 0.0,
            'readability': 0.0,
            'relevance': 0.0
        }
    
    # Basic metrics
    word_count = len(text.split())
    sentence_count = len([s for s in text.split('.') if s.strip()])
    paragraph_count = len([p for p in text.split('\n\n') if p.strip()])
    
    # Completeness score based on length
    if word_count < 50:
        completeness = 0.1
    elif word_count < 200:
        completeness = 0.4
    elif word_count < 500:
        completeness = 0.7
    else:
        completeness = 1.0
    
    # Quality score based on structure
    quality = 0.0
    if sentence_count > 3:
        quality += 0.3
    if paragraph_count > 1:
        quality += 0.3
    if word_count > 100:
        quality += 0.2
    if not re.search(r'(advertisement|sponsored|cookie)', text.lower()):
        quality += 0.2
    
    # Readability score (simplified)
    avg_sentence_length = word_count / max(sentence_count, 1)
    if 10 <= avg_sentence_length <= 25:
        readability = 1.0
    elif 5 <= avg_sentence_length <= 35:
        readability = 0.7
    else:
        readability = 0.4
    
    # Relevance score (how well content matches title/description)
    relevance = 0.5  # Default
    if title:
        title_words = set(title.lower().split())
        text_words = set(text.lower().split())
        overlap = len(title_words.intersection(text_words)) / max(len(title_words), 1)
        relevance = min(1.0, overlap * 2)
    
    return {
        'completeness': completeness,
        'quality': quality,
        'readability': readability,
        'relevance': relevance
    }


def get_html_content_with_session(url: str, headers: dict = None, use_session: bool = True, delay: float = None) -> str:
    """
    Fetch HTML content using a session with anti-bot detection measures.
    
    Args:
        url (str): URL to fetch
        headers (dict): HTTP headers to use
        use_session (bool): Whether to use a session (maintains cookies)
        delay (float): Delay in seconds before request (random if None)
        
    Returns:
        str: HTML content as text
    """
    import time
    import random
    import gzip
    import zlib
    
    # Add random delay to appear more human-like
    if delay is None:
        delay = random.uniform(0.5, 2.0)  # Random delay between 0.5-2 seconds
    time.sleep(delay)
    
    # Use session for cookie persistence
    if use_session:
        session = requests.Session()
        # Set session-wide headers
        session.headers.update(headers or {})
        response = session.get(url, timeout=30)
    else:
        response = requests.get(url, headers=headers or {}, timeout=30)
    
    response.raise_for_status()
    
    # Get raw content
    content = response.content
    
    # Check if content is compressed and decompress if needed
    content_encoding = response.headers.get('content-encoding', '').lower()
    
    if content_encoding == 'gzip' or (content and content[:2] == b'\x1f\x8b'):
        try:
            content = gzip.decompress(content)
            logger.info(f"Decompressed gzip content for {url}")
        except Exception as e:
            logger.warning(f"Failed to decompress gzip content for {url}: {e}")
    elif content_encoding == 'deflate':
        try:
            content = zlib.decompress(content)
            logger.info(f"Decompressed deflate content for {url}")
        except Exception as e:
            logger.warning(f"Failed to decompress deflate content for {url}: {e}")
    elif content_encoding == 'br':
        try:
            import brotli
            content = brotli.decompress(content)
            logger.info(f"Decompressed brotli content for {url}")
        except ImportError:
            logger.warning(f"Brotli compression detected but brotli library not available for {url}")
        except Exception as e:
            logger.warning(f"Failed to decompress brotli content for {url}: {e}")
    
    # Decode to text
    try:
        # Try to detect encoding from response headers
        encoding = response.encoding or 'utf-8'
        html = content.decode(encoding, errors='ignore')
    except (UnicodeDecodeError, LookupError):
        # Fallback to UTF-8 with error handling
        html = content.decode('utf-8', errors='ignore')
    
    # Final validation - check if we got actual HTML
    if html and len(html) > 0:
        # Check for binary indicators (non-printable characters at start)
        first_char = html[0]
        if ord(first_char) < 32 and first_char not in '\t\n\r\x0c':
            logger.warning(f"Content still appears binary for {url}, may be corrupted")
            # Try one more time with different encoding
            try:
                html = content.decode('latin1', errors='ignore')
            except:
                pass
    
    return html


def get_html_content(url: str, headers: dict = None) -> str:
    """
    Fetch HTML content from URL with proper encoding and compression handling.
    
    Args:
        url (str): URL to fetch
        headers (dict): HTTP headers to use
        
    Returns:
        str: HTML content as text
    """
    import gzip
    import zlib
    
    response = requests.get(url, headers=headers or {}, timeout=30)
    response.raise_for_status()
    
    # Get raw content
    content = response.content
    
    # Check if content is compressed and decompress if needed
    content_encoding = response.headers.get('content-encoding', '').lower()
    
    if content_encoding == 'gzip' or (content and content[:2] == b'\x1f\x8b'):
        try:
            content = gzip.decompress(content)
            logger.info(f"Decompressed gzip content for {url}")
        except Exception as e:
            logger.warning(f"Failed to decompress gzip content for {url}: {e}")
    elif content_encoding == 'deflate':
        try:
            content = zlib.decompress(content)
            logger.info(f"Decompressed deflate content for {url}")
        except Exception as e:
            logger.warning(f"Failed to decompress deflate content for {url}: {e}")
    elif content_encoding == 'br':
        try:
            import brotli
            content = brotli.decompress(content)
            logger.info(f"Decompressed brotli content for {url}")
        except ImportError:
            logger.warning(f"Brotli compression detected but brotli library not available for {url}")
        except Exception as e:
            logger.warning(f"Failed to decompress brotli content for {url}: {e}")
    
    # Decode to text
    try:
        # Try to detect encoding from response headers
        encoding = response.encoding or 'utf-8'
        html = content.decode(encoding, errors='ignore')
    except (UnicodeDecodeError, LookupError):
        # Fallback to UTF-8 with error handling
        html = content.decode('utf-8', errors='ignore')
    
    # Final validation - check if we got actual HTML
    if html and len(html) > 0:
        # Check for binary indicators (non-printable characters at start)
        first_char = html[0]
        if ord(first_char) < 32 and first_char not in '\t\n\r\x0c':
            logger.warning(f"Content still appears binary for {url}, may be corrupted")
            # Try one more time with different encoding
            try:
                html = content.decode('latin1', errors='ignore')
            except:
                pass
    
    return html


def get_stealth_headers(url: str, user_agent: str = None) -> Dict[str, str]:
    """
    Get stealth headers designed to bypass bot detection.
    
    Args:
        url (str): Target URL for context-aware headers
        user_agent (str): User agent string to use (random if None)
        
    Returns:
        Dict[str, str]: Stealth HTTP headers
    """
    import random
    from urllib.parse import urlparse
    
    if not user_agent:
        user_agents = get_user_agents()
        user_agent = random.choice(user_agents)
    
    domain = urlparse(url).netloc
    
    # Base headers that mimic real browser behavior
    headers = {
        'User-Agent': user_agent,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0',
        'sec-ch-ua': '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"'
    }
    
    # Add realistic referers based on domain
    referer_options = [
        f"https://www.google.com/",
        f"https://www.google.com/search?q={domain}",
        f"https://{domain}/",
        f"https://t.co/",  # Twitter referrer
        f"https://www.facebook.com/",
    ]
    headers['Referer'] = random.choice(referer_options)
    
    # Randomly vary some headers to appear more human
    if random.random() < 0.5:
        headers['DNT'] = '1'
    
    if random.random() < 0.3:
        headers['Pragma'] = 'no-cache'
    
    # Site-specific optimizations
    if 'politico.com' in domain:
        # Politico-specific headers
        headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        headers['Accept-Language'] = 'en-US,en;q=0.5'
        # Remove some headers that might trigger detection
        headers.pop('sec-ch-ua', None)
        headers.pop('sec-ch-ua-mobile', None)
        headers.pop('sec-ch-ua-platform', None)
    
    return headers


def get_request_headers(user_agent: str = None, referer: str = None) -> Dict[str, str]:
    """
    Get realistic HTTP headers for web scraping requests.
    
    Args:
        user_agent (str): User agent string to use (random if None)
        referer (str): Referer header to use
        
    Returns:
        Dict[str, str]: HTTP headers
    """
    import random
    
    if not user_agent:
        user_agents = get_user_agents()
        user_agent = random.choice(user_agents)
    
    headers = {
        'User-Agent': user_agent,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0',
        'DNT': '1',
        'Sec-GPC': '1',
        'sec-ch-ua': '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"'
    }
    
    # Add referer if provided (helps with some sites)
    if referer:
        headers['Referer'] = referer
    
    # Randomly add some optional headers that real browsers might send
    optional_headers = [
        ('Pragma', 'no-cache'),
        ('X-Requested-With', 'XMLHttpRequest'),  # Sometimes helps
    ]
    
    # Randomly include some optional headers
    for header_name, header_value in optional_headers:
        if random.random() < 0.3:  # 30% chance to include each
            headers[header_name] = header_value
    
    return headers 