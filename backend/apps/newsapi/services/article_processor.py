import logging
import hashlib
import re
from datetime import datetime
from django.utils import timezone
from django.db import transaction, models
from apps.articles.models import Article, StoryGroup
from apps.feeds.models import Publication, Language, Topic, Region
from apps.feeds.utils import generate_logo_url
from apps.newsapi.models import NewsAPIArticle
from apps.newsapi.utils import extract_domain

logger = logging.getLogger(__name__)

class ArticleProcessor:
    """
    Processes articles from NewsAPI and transforms them into Article model instances.
    Handles matching to publications, languages, topics, and regions.
    """
    
    def __init__(self):
        # Load publication mappings
        self.publication_mapping = self._get_publication_mapping()
        self.language_mapping = self._get_language_mapping()
        self.topic_mapping = self._get_topic_mapping()
    
    def _get_publication_mapping(self):
        """
        Create mapping of publications by NewsAPI ID and domain.
        
        Returns:
            dict: Mapping of source IDs and domains to Publication instances
        """
        mapping = {}
        for publication in Publication.objects.filter(
            models.Q(news_api_id__isnull=False) | models.Q(domain__isnull=False)
        ):
            # Map by NewsAPI ID if available
            if publication.news_api_id:
                mapping[f"id:{publication.news_api_id.lower()}"] = publication
            
            # Map by domain if available
            if publication.domain:
                mapping[f"domain:{publication.domain.lower()}"] = publication
                
        return mapping
    
    def _get_language_mapping(self):
        """
        Create a mapping of language codes to our Language objects.
        
        Returns:
            dict: Mapping of language codes to Language instances
        """
        return {lang.iso_code.lower(): lang for lang in Language.objects.all()}
    
    def _get_topic_mapping(self):
        """
        Create a mapping of NewsAPI categories to our Topic objects.
        
        Returns:
            dict: Mapping of category names to Topic instances
        """
        return {topic.slug.lower(): topic for topic in Topic.objects.all()}
    
    def _parse_date(self, date_str):
        """
        Parse a date string from the NewsAPI format to a datetime object.
        
        Args:
            date_str (str): Date string in NewsAPI format
            
        Returns:
            datetime: Parsed datetime object or current time if parsing fails
        """
        if not date_str:
            return timezone.now()
            
        try:
            return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            try:
                return datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                logger.warning(f"Could not parse date: {date_str}")
                return timezone.now()
    
    def _get_or_create_publication(self, source_id, source_name, article_url):
        """
        Find an existing publication or create a new one based on available information.
        
        Args:
            source_id (str): The NewsAPI source ID
            source_name (str): The source name from the API
            article_url (str): The article URL (for domain extraction)
            
        Returns:
            Publication: A Publication instance
        """
        # Extract domain from article URL
        domain = extract_domain(article_url)
        
        # Try to find publication by NewsAPI ID
        if source_id:
            source_id_key = f"id:{source_id.lower()}"
            if source_id_key in self.publication_mapping:
                publication = self.publication_mapping[source_id_key]
                
                # Update domain if missing
                if domain and not publication.domain:
                    publication.domain = domain
                    publication.save(update_fields=['domain'])
                
                # Update logo_url if missing
                if domain and not publication.logo_url:
                    logo_url = generate_logo_url(domain)
                    if logo_url:
                        publication.logo_url = logo_url
                        publication.save(update_fields=['logo_url'])
                
                return publication
        
        # Try to find publication by domain
        if domain:
            domain_key = f"domain:{domain.lower()}"
            if domain_key in self.publication_mapping:
                publication = self.publication_mapping[domain_key]
                
                # Update logo_url if missing
                if not publication.logo_url:
                    logo_url = generate_logo_url(domain)
                    if logo_url:
                        publication.logo_url = logo_url
                        publication.save(update_fields=['logo_url'])
                        
                return publication
        
        # Create new publication if not found
        if source_name and (source_id or domain):
            # Generate logo URL
            logo_url = generate_logo_url(domain) if domain else None
            
            publication = Publication(
                name=source_name,
                news_api_id=source_id,
                domain=domain,
                website_url=f"https://{domain}" if domain else "",
                logo_url=logo_url
            )
            publication.save()
            
            # Add to mapping
            if source_id:
                self.publication_mapping[f"id:{source_id.lower()}"] = publication
            if domain:
                self.publication_mapping[f"domain:{domain.lower()}"] = publication
                
            logger.info(f"Created new publication: {source_name} (domain: {domain}, id: {source_id})")
            return publication
        
        return None
    
    def _get_or_create_article(self, article_data, is_top_headline=False, sync_log=None, category=None):
        """
        Get an existing article or create a new one based on the URL.
        
        Args:
            article_data (dict): Article data from NewsAPI
            is_top_headline (bool, optional): Whether this is a top headline
            sync_log (NewsAPISyncLog, optional): The sync log this article is part of
            category (str, optional): Category from NewsAPI (for topic mapping)
            
        Returns:
            tuple: (Article, NewsAPIArticle, bool) where bool indicates if created
        """
        url = article_data.get('url')
        if not url:
            return None, None, False
            
        # Check if we already have a NewsAPIArticle with this URL
        try:
            existing_newsapi_article = NewsAPIArticle.objects.select_related('article').get(
                article__url=url
            )
            # Update is_top_headline status if needed
            if is_top_headline and not existing_newsapi_article.is_top_headline:
                existing_newsapi_article.is_top_headline = True
                existing_newsapi_article.save(update_fields=['is_top_headline'])
            
            return existing_newsapi_article.article, existing_newsapi_article, False
            
        except NewsAPIArticle.DoesNotExist:
            # Create new article and NewsAPIArticle
            article, newsapi_article = self._create_article_pair(article_data, is_top_headline, sync_log, category)
            return article, newsapi_article, True
    
    def _calculate_content_metrics(self, content, title, description):
        """
        Calculate various metrics about the article content.
        
        Args:
            content (str): The article content
            title (str): The article title
            description (str): The article description
            
        Returns:
            tuple: (word_count, read_time, content_hash, keywords)
        """
        # Combine text for analysis
        full_text = f"{title} {description} {content}".strip()
        
        # Word count
        word_count = len(re.findall(r'\w+', full_text)) if full_text else 0
        
        # Read time (average reading speed: 238 words per minute)
        read_time = round(word_count / 238, 1) if word_count > 0 else 0.5
        
        # Content hash for deduplication
        content_hash = hashlib.md5(full_text.encode('utf-8')).hexdigest() if full_text else None
        
        # Extract basic keywords (placeholder for more sophisticated NLP)
        # In a real implementation, use proper NLP for keyword extraction
        stop_words = {'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'with', 'by'}
        words = re.findall(r'\b[a-z]{3,15}\b', full_text.lower())
        keywords = list(set([w for w in words if w not in stop_words]))[:10]  # Top 10 keywords
        
        return word_count, read_time, content_hash, keywords
    
    def _create_article_pair(self, article_data, is_top_headline=False, sync_log=None, category=None):
        """
        Create a new Article and associated NewsAPIArticle.
        
        Args:
            article_data (dict): Article data from NewsAPI
            is_top_headline (bool, optional): Whether this is a top headline
            sync_log (NewsAPISyncLog, optional): The sync log this article is part of
            category (str, optional): Category from NewsAPI (for topic mapping)
            
        Returns:
            tuple: (Article, NewsAPIArticle)
        """
        # Extract source info
        source_info = article_data.get('source', {})
        source_id = source_info.get('id', '').lower() if source_info.get('id') else None
        source_name = source_info.get('name', '')
        article_url = article_data.get('url', '')
        
        # Get or create the publication
        publication = self._get_or_create_publication(source_id, source_name, article_url)
        
        # Extract domain from article URL
        domain = extract_domain(article_url)
        
        # Get the language (default to English if not specified)
        language_code = article_data.get('language', 'en').lower()
        language = self.language_mapping.get(language_code, self.language_mapping.get('en'))
        
        # Parse date
        published_at = self._parse_date(article_data.get('publishedAt'))
        
        # Extract content from API response
        title = article_data.get('title', '')
        description = article_data.get('description', '')
        content = article_data.get('content', '')
        
        # Calculate content metrics
        word_count, read_time, content_hash, keywords = self._calculate_content_metrics(
            content, title, description
        )
        
        # Create the article with enhanced fields
        article = Article(
            title=title,
            description=description,
            content=content,
            url=article_url,
            image_url=article_data.get('urlToImage'),
            source_name=source_name,
            publication=publication,
            author=article_data.get('author', ''),
            language=language,
            published_at=published_at,
            is_top_headline=is_top_headline,
            summary_ready=False,  # Will be processed by summarizer service
            # Enhanced fields
            word_count=word_count,
            read_time_minutes=read_time,
            content_hash=content_hash,
            keywords=keywords,
            # Default values for other fields
            popularity_score=0.0,
            relevance_score=0.0
        )
        
        # Save the article first to get an ID
        article.save()
        
        # Process topics
        # First try to use the provided category from the API call
        if category and category.lower() in self.topic_mapping:
            article.topics.add(self.topic_mapping[category.lower()])
        # Then add topics from the publication if available
        elif source_id and publication:
            # Add topics from the publication
            article.topics.set(publication.topics.all())
        
        # Add regions from the publication
        if publication:
            article.regions.set(publication.regions.all())
        
        # Create the NewsAPIArticle
        newsapi_article = NewsAPIArticle(
            article=article,
            source_id=source_id,
            source_name=source_name,
            domain=domain,
            # Generate a composite ID using source and URL hash
            newsapi_id=f"{source_id}:{hashlib.md5(article.url.encode()).hexdigest()[:8]}",
            category=category or article_data.get('category'),  # Use provided category or from data
            raw_data=article_data,
            is_top_headline=is_top_headline,
            sync_log=sync_log
        )
        newsapi_article.save()
        
        return article, newsapi_article
    
    def process_articles(self, api_response, is_top_headline=False, sync_log=None, category=None):
        """
        Process a batch of articles from a NewsAPI response.
        
        Args:
            api_response (dict): The response from NewsAPI
            is_top_headline (bool, optional): Whether these are top headlines
            sync_log (NewsAPISyncLog, optional): The sync log to associate with articles
            category (str, optional): Category from NewsAPI (for topic mapping)
            
        Returns:
            tuple: (created_count, updated_count, total_count)
        """
        if not api_response or 'articles' not in api_response:
            logger.warning("Invalid API response, no articles found")
            return 0, 0, 0
            
        articles_data = api_response['articles']
        created_count = 0
        updated_count = 0
        
        # Process in batches for better performance
        with transaction.atomic():
            for article_data in articles_data:
                article, newsapi_article, created = self._get_or_create_article(
                    article_data, 
                    is_top_headline,
                    sync_log,
                    category
                )
                
                if article:
                    if created:
                        created_count += 1
                    else:
                        # Update existing article with new data if needed
                        if is_top_headline and not article.is_top_headline:
                            article.is_top_headline = True
                            article.save(update_fields=['is_top_headline'])
                            updated_count += 1
                        
                        # Add topic from category if provided and not already present
                        if category and category.lower() in self.topic_mapping:
                            topic = self.topic_mapping[category.lower()]
                            if not article.topics.filter(id=topic.id).exists():
                                article.topics.add(topic)
        
        total_count = created_count + updated_count
        return created_count, updated_count, total_count 