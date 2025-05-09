import re
from urllib.parse import urlparse

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