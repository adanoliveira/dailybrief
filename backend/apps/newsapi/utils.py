import re
from urllib.parse import urlparse
from apps.feeds.utils import extract_domain, generate_logo_url

# Re-export the feeds utility functions for backward compatibility
__all__ = ['extract_domain', 'generate_logo_url', 'update_publication_domain', 'update_newsapi_article_domain']

def update_publication_domain(publication):
    """
    Update a publication's domain based on its website_url.
    
    Args:
        publication: A Publication model instance
        
    Returns:
        bool: True if domain was updated, False otherwise
    """
    if not publication.website_url:
        return False
        
    domain = extract_domain(publication.website_url)
    if domain and (not publication.domain or publication.domain != domain):
        publication.domain = domain
        publication.save(update_fields=['domain'])
        return True
    return False

def update_newsapi_article_domain(newsapi_article):
    """
    Update a NewsAPIArticle's domain based on its article's URL.
    
    Args:
        newsapi_article: A NewsAPIArticle model instance
        
    Returns:
        bool: True if domain was updated, False otherwise
    """
    if not newsapi_article.article or not newsapi_article.article.url:
        return False
        
    domain = extract_domain(newsapi_article.article.url)
    if domain and (not newsapi_article.domain or newsapi_article.domain != domain):
        newsapi_article.domain = domain
        newsapi_article.save(update_fields=['domain'])
        return True
    return False

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
    
    # Fallbacks if needed:
    # 1. Direct favicon: f"https://{domain}/favicon.ico"
    # 2. Apple touch icon: f"https://{domain}/apple-touch-icon.png"
    # 3. DuckDuckGo service: f"https://icons.duckduckgo.com/ip3/{domain}.ico" 