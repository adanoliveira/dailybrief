import logging
from datetime import datetime, timedelta
from django.utils import timezone
from django.db import transaction
import time

from apps.newsapi.models import NewsAPISyncLog
from apps.newsapi.services.newsapi_service import NewsAPIService
from apps.newsapi.services.article_processor import ArticleProcessor
from apps.feeds.models import Publication, Language

logger = logging.getLogger(__name__)

class SyncManager:
    """
    Orchestrates the synchronization of articles from NewsAPI.
    Handles backfilling historical articles and syncing recent content.
    """
    
    def __init__(self):
        self.api_service = NewsAPIService()
        self.processor = ArticleProcessor()
    
    def _create_sync_log(self, sync_type, parameters=None):
        """
        Create a sync log entry.
        
        Args:
            sync_type (str): Type of sync operation
            parameters (dict, optional): Sync parameters
            
        Returns:
            NewsAPISyncLog: The created log entry
        """
        if parameters is None:
            parameters = {}
            
        return NewsAPISyncLog.objects.create(
            sync_type=sync_type,
            status='started',
            parameters=parameters
        )
    
    def _update_sync_log(self, sync_log, status, created_count, updated_count, error=None):
        """
        Update a sync log entry with results.
        
        Args:
            sync_log (NewsAPISyncLog): The log entry to update
            status (str): New status
            created_count (int): Number of articles created
            updated_count (int): Number of articles updated
            error (Exception, optional): Any error that occurred
        """
        sync_log.status = status
        sync_log.articles_found = created_count + updated_count
        sync_log.articles_created = created_count
        sync_log.articles_updated = updated_count
        sync_log.completed_at = timezone.now()
        
        if sync_log.started_at:
            duration = sync_log.completed_at - sync_log.started_at
            sync_log.duration_seconds = duration.total_seconds()
            
        if error:
            sync_log.error_message = str(error)
            
        sync_log.save()
    
    def backfill_articles(self, days=30, chunk_size=7, language='en', **params):
        """
        Fetch and save historical articles from the past X days.
        
        Args:
            days (int): Number of days to look back
            chunk_size (int): Size of each date chunk in days
            language (str): Language code for articles
            **params: Additional parameters for the API
            
        Returns:
            tuple: (total_created, total_updated, success)
        """
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Create sync log
        sync_params = {
            'days': days,
            'chunk_size': chunk_size,
            'language': language,
            **params
        }
        sync_log = self._create_sync_log('everything', sync_params)
        
        total_created = 0
        total_updated = 0
        success = True
        
        try:
            # Split into chunks to avoid hitting API limits
            current_end = end_date
            chunk_start = end_date - timedelta(days=chunk_size)
            
            while chunk_start >= start_date:
                logger.info(f"Fetching articles from {chunk_start} to {current_end}")
                
                # Build params for this chunk
                chunk_params = {
                    'language': language,
                    **params
                }
                
                # Fetch articles for this date range
                response = self.api_service.fetch_articles_by_date_range(
                    chunk_start, 
                    current_end,
                    **chunk_params
                )
                
                # Process articles
                created, updated, _ = self.processor.process_articles(response, sync_log=sync_log)
                
                total_created += created
                total_updated += updated
                
                logger.info(f"Processed chunk: {created} created, {updated} updated")
                
                # Move to next chunk
                current_end = chunk_start
                chunk_start = chunk_start - timedelta(days=chunk_size)
                
                # Sleep to respect rate limits if needed
                # time.sleep(1)
            
            # Update sync log with success
            self._update_sync_log(sync_log, 'completed', total_created, total_updated)
            
        except Exception as e:
            logger.exception(f"Error during backfill: {e}")
            self._update_sync_log(sync_log, 'failed', total_created, total_updated, error=e)
            success = False
        
        return total_created, total_updated, success
    
    def sync_recent_articles(self, hours=1, **params):
        """
        Fetch and save articles published in the last X hours.
        
        Args:
            hours (int): Number of hours to look back
            **params: Additional parameters for the API
            
        Returns:
            tuple: (created_count, updated_count, success)
        """
        # Create sync log
        sync_params = {
            'hours': hours,
            **params
        }
        sync_log = self._create_sync_log('everything', sync_params)
        
        try:
            # Fetch recent articles
            response = self.api_service.fetch_recent_articles(hours, **params)
            
            # Process articles
            created, updated, _ = self.processor.process_articles(response, sync_log=sync_log)
            
            # Update sync log with success
            self._update_sync_log(sync_log, 'completed', created, updated)
            
            return created, updated, True
            
        except Exception as e:
            logger.exception(f"Error during recent sync: {e}")
            self._update_sync_log(sync_log, 'failed', 0, 0, error=e)
            return 0, 0, False
    
    def sync_top_headlines(self, categories=None, **params):
        """
        Fetch and save current top headlines from specific categories.
        
        Args:
            categories (list): List of categories to fetch. If None, all categories will be used.
            **params: Additional parameters for the API
            
        Returns:
            tuple: (created_count, updated_count, success)
        """
        if not categories:
            categories = ['business', 'entertainment', 'general', 'health', 'science', 'sports', 'technology']
            
        # Create sync log
        sync_params = {
            'categories': categories,
            **params
        }
        sync_log = self._create_sync_log('top_headlines', sync_params)
        
        total_created = 0
        total_updated = 0
        success = True
        
        try:
            for category in categories:
                logger.info(f"Fetching headlines for category: {category}")
                
                # Build params for this request
                headline_params = {
                    'category': category,
                    **params
                }
                
                # Fetch headlines
                response = self.api_service.get_top_headlines(**headline_params)
                
                # Check for pagination
                total_results = response.get('totalResults', 0)
                page_size = 100  # Max page size for NewsAPI
                total_pages = (total_results + page_size - 1) // page_size
                
                # Process first page
                created, updated, _ = self.processor.process_articles(
                    response, 
                    is_top_headline=True,
                    sync_log=sync_log,
                    category=category  # Pass category for topic mapping
                )
                
                total_created += created
                total_updated += updated
                
                logger.info(f"Processed {category} page 1: {created} created, {updated} updated")
                
                # Process additional pages if needed
                for page in range(2, min(total_pages + 1, 5)):  # Limit to 5 pages (safety)
                    # Build params with page number
                    paged_params = {
                        'category': category,
                        'page': page,
                        **params
                    }
                    
                    # Fetch next page
                    try:
                        page_response = self.api_service.get_top_headlines(**paged_params)
                        
                        # Process page
                        created, updated, _ = self.processor.process_articles(
                            page_response, 
                            is_top_headline=True,
                            sync_log=sync_log,
                            category=category  # Pass category for topic mapping
                        )
                        
                        total_created += created
                        total_updated += updated
                        
                        logger.info(f"Processed {category} page {page}: {created} created, {updated} updated")
                        
                    except Exception as e:
                        logger.error(f"Error processing page {page} for {category}: {e}")
                
                # Sleep to respect rate limits
                time.sleep(1)
            
            # Update sync log with success
            self._update_sync_log(sync_log, 'completed', total_created, total_updated)
            
        except Exception as e:
            logger.exception(f"Error during headlines sync: {e}")
            self._update_sync_log(sync_log, 'failed', total_created, total_updated, error=e)
            success = False
        
        return total_created, total_updated, success
        
    def sync_everything_by_publication(self, days=1, **params):
        """
        Fetch articles from specific publications.
        
        Args:
            days (int): Number of days to look back
            **params: Additional parameters for the API
            
        Returns:
            tuple: (created_count, updated_count, success)
        """
        # Create sync log
        sync_params = {
            'days': days,
            **params
        }
        sync_log = self._create_sync_log('everything_by_publication', sync_params)
        
        total_created = 0
        total_updated = 0
        success = True
        
        try:
            # Get publications with news_api_id
            publications = Publication.objects.filter(news_api_id__isnull=False).exclude(news_api_id='')
            
            for publication in publications:
                logger.info(f"Fetching articles for {publication.name}")
                
                # Build params for this publication
                pub_params = {
                    'sources': publication.news_api_id,
                    **params
                }
                
                # Calculate date range
                end_date = timezone.now()
                start_date = end_date - timedelta(days=days)
                
                # Fetch articles
                response = self.api_service.fetch_articles_by_date_range(
                    start_date,
                    end_date,
                    **pub_params
                )
                
                # Process articles
                created, updated, _ = self.processor.process_articles(
                    response,
                    sync_log=sync_log
                )
                
                total_created += created
                total_updated += updated
                
                logger.info(f"Processed {publication.name}: {created} created, {updated} updated")
                
                # Sleep to respect rate limits if needed
                # time.sleep(1)
            
            # Update sync log with success
            self._update_sync_log(sync_log, 'completed', total_created, total_updated)
            
        except Exception as e:
            logger.exception(f"Error during publication sync: {e}")
            self._update_sync_log(sync_log, 'failed', total_created, total_updated, error=e)
            success = False
        
        return total_created, total_updated, success
    
    def sync_recent_by_sources_batched(self, hours=24, batch_size=20, **params):
        """
        Fetch and save articles from specific sources published in the last X hours.
        Groups sources into batches to respect the NewsAPI limit of 20 sources per request.
        
        Args:
            hours (int): Number of hours to look back (defaults to 24 hours to cover previous day)
            batch_size (int): Maximum number of sources per request (max 20 for NewsAPI)
            **params: Additional parameters for the API
            
        Returns:
            tuple: (created_count, updated_count, success)
        """
        # Create sync log
        sync_params = {
            'hours': hours,
            'batch_size': batch_size,
            **params
        }
        sync_log = self._create_sync_log('everything_by_sources_batched', sync_params)
        
        total_created = 0
        total_updated = 0
        success = True
        
        try:
            # Get all publications with NewsAPI IDs, ordered by authority
            publications = Publication.objects.filter(
                news_api_id__isnull=False
            ).exclude(
                news_api_id=''
            ).order_by('-authority')
            
            if not publications.exists():
                logger.warning("No publications with NewsAPI IDs found")
                self._update_sync_log(sync_log, 'completed', 0, 0)
                return 0, 0, True
            
            # Group publications into batches of batch_size
            source_batches = []
            current_batch = []
            
            for pub in publications:
                if len(current_batch) >= batch_size:
                    source_batches.append(current_batch)
                    current_batch = []
                current_batch.append(pub.news_api_id)
            
            # Add the last batch if it has any items
            if current_batch:
                source_batches.append(current_batch)
            
            logger.info(f"Processing {len(publications)} publications in {len(source_batches)} batches")
            
            # Process each batch
            for batch_index, sources_batch in enumerate(source_batches):
                logger.info(f"Processing batch {batch_index + 1}/{len(source_batches)} with {len(sources_batch)} sources")
                
                # Build params for this batch
                batch_params = {
                    'sources': ','.join(sources_batch),
                    **params
                }
                
                # Calculate end date for "yesterday" if not provided
                # NewsAPI /everything endpoint typically has a 24-hour delay
                if 'to' not in batch_params and 'from_param' not in batch_params:
                    # Calculate dates for the previous day (yesterday)
                    today = timezone.now()
                    yesterday_end = (today - timedelta(days=1)).replace(hour=23, minute=59, second=59)
                    day_before_yesterday = (today - timedelta(days=2)).replace(hour=23, minute=59, second=59)
                    
                    logger.info(f"Fetching articles from {day_before_yesterday} to {yesterday_end}")
                    
                    # Use fetch_articles_by_date_range which handles date formatting properly
                    response = self.api_service.fetch_articles_by_date_range(
                        day_before_yesterday, 
                        yesterday_end,
                        **batch_params
                    )
                else:
                    # If dates are explicitly provided, use them
                    response = self.api_service.fetch_recent_articles(hours, **batch_params)
                
                # Check for pagination
                total_results = response.get('totalResults', 0)
                page_size = 100  # Max page size for NewsAPI
                total_pages = (total_results + page_size - 1) // page_size
                
                logger.info(f"Found {total_results} articles for batch {batch_index + 1}")
                
                # Process first page
                created, updated, _ = self.processor.process_articles(response, sync_log=sync_log)
                
                total_created += created
                total_updated += updated
                
                logger.info(f"Processed batch {batch_index + 1} page 1: {created} created, {updated} updated")
                
                # Process additional pages if needed
                for page in range(2, min(total_pages + 1, 5)):  # Limit to 5 pages (safety)
                    # Build params with page number
                    paged_params = batch_params.copy()
                    paged_params['page'] = page
                    
                    # Fetch next page (use the same date range method if we used it above)
                    try:
                        if 'to' not in batch_params and 'from_param' not in batch_params:
                            page_response = self.api_service.fetch_articles_by_date_range(
                                day_before_yesterday,
                                yesterday_end,
                                **paged_params
                            )
                        else:
                            page_response = self.api_service.fetch_recent_articles(hours, **paged_params)
                        
                        # Process page
                        created, updated, _ = self.processor.process_articles(page_response, sync_log=sync_log)
                        
                        total_created += created
                        total_updated += updated
                        
                        logger.info(f"Processed batch {batch_index + 1} page {page}: {created} created, {updated} updated")
                        
                    except Exception as e:
                        logger.error(f"Error processing page {page} for batch {batch_index + 1}: {e}")
                
                # Sleep to respect rate limits
                time.sleep(1)
            
            # Update sync log with success
            self._update_sync_log(sync_log, 'completed', total_created, total_updated)
            
        except Exception as e:
            logger.exception(f"Error during recent by sources sync: {e}")
            self._update_sync_log(sync_log, 'failed', total_created, total_updated, error=e)
            success = False
        
        return total_created, total_updated, success 