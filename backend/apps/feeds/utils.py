"""
Utility functions for the feeds app.
"""
from urllib.parse import urlparse
import re

def extract_domain(url):
    """
    Extract a normalized domain from a URL.
    
    Examples:
        - https://www.nytimes.com/article/123 -> nytimes.com
        - http://bbc.co.uk/news -> bbc.co.uk
        - www.techcrunch.com/news/ai -> techcrunch.com
    
    Args:
        url (str): The URL to extract domain from
        
    Returns:
        str: Normalized domain or None if parsing fails
    """
    if not url:
        return None
        
    try:
        # Parse the URL
        parsed_url = urlparse(url)
        
        # If there's no netloc, the URL might be missing the protocol
        if not parsed_url.netloc:
            # Try adding 'http://' and reparsing
            parsed_url = urlparse(f"http://{url}")
            
        # Get the netloc (domain with potential subdomains)
        netloc = parsed_url.netloc.lower()
        
        # Remove port number if present
        netloc = netloc.split(':')[0]
        
        # Remove 'www.' prefix if present
        netloc = re.sub(r'^www\.', '', netloc)
        
        # Return normalized domain
        return netloc if netloc else None
    except Exception:
        return None

def generate_logo_url(domain):
    """
    Generate a logo URL for a publication based on its domain.
    Uses Google's favicon service for best quality.
    
    Args:
        domain (str): The domain name (e.g., nytimes.com)
        
    Returns:
        str: URL to the publication's logo
    """
    if not domain:
        return None
    
    # Google's favicon service provides higher quality icons (128px)
    return f"https://www.google.com/s2/favicons?domain={domain}&sz=128" 