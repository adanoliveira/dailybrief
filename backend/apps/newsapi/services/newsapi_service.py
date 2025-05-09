from datetime import datetime, timedelta
import logging
from newsapi import NewsApiClient
from django.conf import settings
from django.utils import timezone
from apps.newsapi.models import NewsAPIRequest

logger = logging.getLogger(__name__)

class NewsAPIService:
    """
    Service class to interact with the News API.
    Provides methods to fetch articles from different endpoints and handles API tracking.
    """
    
    def __init__(self, api_key=None):
        """
        Initialize the News API client with the API key.
        
        Args:
            api_key (str, optional): The News API key. Defaults to the NEWSAPI_API_KEY setting.
        """
        self.api_key = api_key or settings.NEWSAPI_API_KEY
        self.client = NewsApiClient(api_key=self.api_key)
    
    def _track_request(self, request_type, endpoint, params, response=None, error=None):
        """
        Track an API request in the database.
        
        Args:
            request_type (str): The type of request ('everything', 'top_headlines', 'sources')
            endpoint (str): The API endpoint
            params (dict): The request parameters
            response (dict, optional): The API response if successful
            error (Exception, optional): Any exception that occurred
            
        Returns:
            NewsAPIRequest: The created request record
        """
        success = error is None and response is not None
        
        # Extract rate limit info if available
        rate_limit_remaining = None
        rate_limit_reset = None
        status_code = None
        total_results = 0
        results_fetched = 0
        
        if response:
            status_code = response.get('status_code', 200)
            total_results = response.get('totalResults', 0)
            results_fetched = len(response.get('articles', []))
        
        request = NewsAPIRequest(
            request_type=request_type,
            endpoint=endpoint,
            params=params,
            success=success,
            status_code=status_code,
            error_message=str(error) if error else '',
            rate_limit_remaining=rate_limit_remaining,
            rate_limit_reset=rate_limit_reset,
            total_results=total_results,
            results_fetched=results_fetched
        )
        request.save()
        return request
    
    def get_everything(self, **params):
        """
        Fetch articles from the /everything endpoint.
        
        Args:
            **params: Parameters to pass to the News API. See the News API documentation
                     for available parameters.
                     
        Returns:
            dict: The API response with articles
        """
        endpoint = '/v2/everything'
        
        try:
            response = self.client.get_everything(**params)
            request = self._track_request('everything', endpoint, params, response)
            return response
        except Exception as e:
            logger.exception(f"Error fetching articles from News API: {e}")
            self._track_request('everything', endpoint, params, error=e)
            raise
    
    def get_top_headlines(self, **params):
        """
        Fetch articles from the /top-headlines endpoint.
        
        Args:
            **params: Parameters to pass to the News API. See the News API documentation
                     for available parameters.
                     
        Returns:
            dict: The API response with articles
        """
        endpoint = '/v2/top-headlines'
        
        try:
            response = self.client.get_top_headlines(**params)
            request = self._track_request('top_headlines', endpoint, params, response)
            return response
        except Exception as e:
            logger.exception(f"Error fetching top headlines from News API: {e}")
            self._track_request('top_headlines', endpoint, params, error=e)
            raise
    
    def get_sources(self, **params):
        """
        Fetch sources from the /top-headlines/sources endpoint.
        
        Args:
            **params: Parameters to pass to the News API. See the News API documentation
                     for available parameters.
                     
        Returns:
            dict: The API response with sources
        """
        endpoint = '/v2/top-headlines/sources'
        
        try:
            response = self.client.get_sources(**params)
            request = self._track_request('sources', endpoint, params, response)
            return response
        except Exception as e:
            logger.exception(f"Error fetching sources from News API: {e}")
            self._track_request('sources', endpoint, params, error=e)
            raise
    
    def fetch_articles_by_date_range(self, start_date, end_date, **params):
        """
        Fetch articles within a specific date range.
        
        Args:
            start_date (datetime): The start date
            end_date (datetime): The end date
            **params: Additional parameters to pass to the News API
            
        Returns:
            dict: The API response with articles
        """
        # Format dates for News API with full ISO 8601 format including time
        from_date = start_date.strftime('%Y-%m-%dT%H:%M:%S')
        to_date = end_date.strftime('%Y-%m-%dT%H:%M:%S')
        
        # Use from_param as required by the NewsApiClient library
        params.update({
            'from_param': from_date,
            'to': to_date
        })
        
        # Sort by publishedAt by default, but allow overriding
        if 'sort_by' not in params:
            params['sort_by'] = 'publishedAt'
        
        return self.get_everything(**params)
    
    def fetch_recent_articles(self, hours=1, **params):
        """
        Fetch articles published in the last X hours.
        
        Args:
            hours (int): Number of hours to look back
            **params: Additional parameters to pass to the News API
            
        Returns:
            dict: The API response with articles
        """
        end_date = timezone.now()
        start_date = end_date - timedelta(hours=hours)
        
        return self.fetch_articles_by_date_range(start_date, end_date, **params) 