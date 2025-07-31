# Domain-Based Publication Matching

This document explains our approach to matching articles to publications using domain extraction and normalization.

## The Problem

NewsAPI provides article data with source information, but this information has limitations:

1. Some articles have `source_id` values, but these are inconsistent across API endpoints
2. Many articles only have `source_name` values, which can vary in format
3. No standardized identifier exists to reliably match articles to our publications

These limitations make it difficult to automatically associate articles with the correct publication, which is essential for proper categorization and filtering.

## Our Solution: Domain-Based Matching

We implemented a domain-based publication matching system that:

1. Extracts normalized domains from article URLs
2. Uses these domains as reliable identifiers for publications
3. Automatically creates new publications when encountering unknown domains
4. Adds logo URLs for visual identification

This approach provides a robust, self-healing system for article categorization.

## Domain Extraction Process

When an article is processed, we:

1. Extract the domain from its URL
2. Normalize the domain (remove `www.`, protocols, etc.)
3. Use the domain to find a matching publication
4. Create a new publication if no match is found

### Example Transformations

| Input URL | Extracted Domain |
|-----------|------------------|
| `https://www.nytimes.com/article/123` | `nytimes.com` |
| `http://bbc.co.uk/news` | `bbc.co.uk` |
| `www.techcrunch.com/news/ai` | `techcrunch.com` |
| `finance.yahoo.com/news` | `finance.yahoo.com` |

## Technical Implementation

### Domain Extraction Function

```python
def extract_domain(url):
    """Extract a normalized domain from a URL."""
    if not url:
        return None
        
    try:
        # Parse the URL
        parsed_url = urlparse(url)
        
        # If there's no netloc, try adding protocol and reparsing
        if not parsed_url.netloc:
            parsed_url = urlparse(f"http://{url}")
            
        # Get the netloc (domain with potential subdomains)
        netloc = parsed_url.netloc.lower()
        
        # Remove port number if present
        netloc = netloc.split(':')[0]
        
        # Remove 'www.' prefix if present
        netloc = re.sub(r'^www\.', '', netloc)
        
        return netloc if netloc else None
    except Exception:
        return None
```

### Publication Search Process

The `_get_or_create_publication` method in `ArticleProcessor` implements the matching logic:

1. Try to find a publication using the source ID from NewsAPI
2. If no match is found, try to find a publication using the domain
3. If still no match is found, create a new publication

```python
# Example logic (simplified)
# Try by NewsAPI ID first
if source_id and source_id in publication_mapping:
    return publication_mapping[source_id]
    
# Try by domain second
if domain and domain in domain_mapping:
    return domain_mapping[domain]
    
# Create new publication if needed
if source_name and domain:
    publication = Publication(
        name=source_name,
        domain=domain,
        website_url=f"https://{domain}",
        logo_url=generate_logo_url(domain)
    )
    publication.save()
    return publication
```

## Automatic Logo Generation

For visual identification, we automatically generate logo URLs using Google's favicon service:

```python
def generate_logo_url(domain):
    """Generate a logo URL for a publication domain."""
    if not domain:
        return None
    
    return f"https://www.google.com/s2/favicons?domain={domain}&sz=128"
```

This provides consistent, high-quality icons for all publications.

## Management Commands

Several management commands support the domain-based matching system:

1. `backfill_domains` - Update domain fields for existing data
2. `create_missing_publications` - Create publications for unique domains
3. `link_articles_to_publications` - Connect articles to publications
4. `add_publication_logos` - Add logo URLs to publications

See [commands.md](commands.md) for detailed usage instructions.

## Benefits

This domain-based approach provides several advantages:

1. **Reliability**: Domains are inherently unique to publications
2. **Consistency**: Normalized domains provide consistent matching
3. **Self-healing**: The system creates new publications automatically
4. **Visual identity**: Automatic logo generation enhances the UI
5. **Independence**: We're not reliant on NewsAPI's inconsistent identifiers

## Edge Cases

The system handles several edge cases:

1. **Subdomains**: Currently treated as separate publications (`news.bbc.co.uk` vs `bbc.co.uk`)
2. **Missing domains**: If the URL is malformed, we fall back to source name matching
3. **Duplicate publications**: Checked during creation to prevent duplicates
4. **Logo availability**: If Google's service doesn't have a logo, the UI handles the fallback 