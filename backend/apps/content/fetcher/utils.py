"""
Essential utilities for Step 1 content fetching.
Minimal, focused utilities for URL handling and HTTP requests.
"""

import re
import requests
from urllib.parse import urlparse, urljoin
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


def validate_url(url: str) -> bool:
    """
    Validate if a URL is properly formatted.
    
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
        # Handle Unicode escape sequences
        try:
            if '\\\\u' in url:
                url = url.replace('\\\\u', '\\u')
                url = url.encode().decode('unicode_escape')
            elif '\\u' in url:
                url = url.encode().decode('unicode_escape')
        except (UnicodeDecodeError, UnicodeEncodeError):
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
    Get a list of realistic user agents for web scraping.
    
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
        # Chrome on Linux
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
    ]


def get_request_headers(user_agent: str = None, referer: str = None) -> Dict[str, str]:
    """
    Get standard HTTP headers for requests.
    
    Args:
        user_agent (str, optional): Custom user agent
        referer (str, optional): Referer header
        
    Returns:
        Dict[str, str]: HTTP headers
    """
    if not user_agent:
        user_agent = get_user_agents()[0]  # Use first (most recent) user agent
    
    headers = {
        'User-Agent': user_agent,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Cache-Control': 'max-age=0'
    }
    
    if referer:
        headers['Referer'] = referer
    
    return headers


def clean_extracted_text(text: str) -> str:
    """
    Basic text cleaning for extracted content.
    
    Args:
        text (str): Raw extracted text
        
    Returns:
        str: Cleaned text
    """
    if not text:
        return ""
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    # Remove common artifacts
    text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)  # Multiple newlines
    text = re.sub(r'[\r\n\t]+', ' ', text)  # Replace line breaks with spaces
    
    return text


def make_http_request(url: str, headers: Dict[str, str] = None, timeout: int = 10) -> requests.Response:
    """
    Make a simple HTTP request with error handling.
    
    Args:
        url (str): URL to request
        headers (Dict[str, str], optional): HTTP headers
        timeout (int): Request timeout in seconds
        
    Returns:
        requests.Response: HTTP response
        
    Raises:
        requests.RequestException: If request fails
    """
    if not headers:
        headers = get_request_headers()
    
    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=timeout,
            allow_redirects=True,
            verify=True
        )
        response.raise_for_status()
        return response
        
    except requests.RequestException as e:
        logger.error(f"HTTP request failed for {url}: {str(e)}")
        raise 