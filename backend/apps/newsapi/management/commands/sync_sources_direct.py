import logging
import requests
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone

from apps.feeds.models import Publication, Region, Language, Topic
from apps.newsapi.models import NewsAPIRequest

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Sync news sources from NewsAPI directly (without language restriction)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--countries',
            type=str,
            help='Comma-separated list of country codes to fetch sources for',
        )
        
        parser.add_argument(
            '--update-existing',
            action='store_true',
            help='Update existing publications with new data',
        )

    def handle(self, *args, **options):
        countries_str = options.get('countries')
        update_existing = options['update_existing']
        
        # Default countries if not specified
        countries = countries_str.split(',') if countries_str else [
            'ae', 'ar', 'at', 'au', 'be', 'bg', 'br', 'ca', 'ch', 
            'cn', 'co', 'cu', 'cz', 'de', 'eg', 'fr', 'gb', 'gr', 
            'hk', 'hu', 'id', 'ie', 'il', 'in', 'it', 'jp', 'kr', 
            'lt', 'lv', 'ma', 'mx', 'my', 'ng', 'nl', 'no', 'nz', 
            'ph', 'pl', 'pt', 'ro', 'rs', 'ru', 'sa', 'se', 'sg', 
            'si', 'sk', 'th', 'tr', 'tw', 'ua', 'us', 've', 'za'
        ]
        
        # API key
        api_key = settings.NEWSAPI_API_KEY
        
        self.stdout.write(self.style.SUCCESS(f'Starting news sources direct sync...'))
        self.stdout.write(f'Countries: {", ".join(countries)}')
        self.stdout.write(f'Update existing: {update_existing}')
        
        # Track results
        total_sources = 0
        created_count = 0
        updated_count = 0
        
        # Cache existing publications, regions, languages, and topics
        existing_publications = {p.news_api_id: p for p in Publication.objects.filter(news_api_id__isnull=False)}
        regions = {r.code: r for r in Region.objects.all()}
        languages = {l.iso_code: l for l in Language.objects.all()}
        topics = {t.slug: t for t in Topic.objects.all()}
        
        # Process each country
        for country in countries:
            self.stdout.write(f'\nProcessing sources for country: {country}')
            
            try:
                # Direct API call without language parameter
                url = f"https://newsapi.org/v2/top-headlines/sources"
                params = {
                    'country': country,
                    'apiKey': api_key
                }
                
                response = requests.get(url, params=params)
                response_data = response.json()
                
                # Track the request
                self._track_request('sources', url, {'country': country}, response_data)
                
                if response.status_code != 200 or response_data.get('status') != 'ok':
                    error_msg = response_data.get('message', 'Unknown error')
                    self.stdout.write(self.style.ERROR(f"API error: {error_msg}"))
                    continue
                
                if not response_data or 'sources' not in response_data:
                    self.stdout.write(self.style.WARNING(f'No sources found for {country}'))
                    continue
                
                sources = response_data['sources']
                total_sources += len(sources)
                
                self.stdout.write(f'Found {len(sources)} sources for {country}')
                
                # Process each source
                for source in sources:
                    source_id = source.get('id')
                    if not source_id:
                        continue
                    
                    name = source.get('name', '')
                    description = source.get('description', '')
                    url = source.get('url', '')
                    category = source.get('category', '')
                    language_code = source.get('language', '')
                    country_code = source.get('country', '')
                    
                    # Check if publication already exists
                    if source_id in existing_publications:
                        if update_existing:
                            # Update existing publication
                            pub = existing_publications[source_id]
                            pub.name = name
                            pub.description = description
                            pub.website_url = url
                            pub.save()
                            
                            # Add or update relationships
                            self._update_publication_relationships(
                                pub, category, language_code, country_code, 
                                topics, languages, regions
                            )
                            
                            updated_count += 1
                            self.stdout.write(f'Updated: {name}')
                        else:
                            self.stdout.write(f'Skipped existing: {name}')
                    else:
                        # Create new publication
                        pub = Publication(
                            name=name,
                            news_api_id=source_id,
                            website_url=url,
                            description=description,
                        )
                        pub.save()
                        
                        # Add relationships
                        self._update_publication_relationships(
                            pub, category, language_code, country_code, 
                            topics, languages, regions
                        )
                        
                        # Add to cache
                        existing_publications[source_id] = pub
                        
                        created_count += 1
                        self.stdout.write(f'Created: {name}')
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error processing country {country}: {str(e)}'))
        
        # Final summary
        self.stdout.write('\n' + self.style.SUCCESS(
            f'Sync completed: {total_sources} sources found, {created_count} created, {updated_count} updated'
        ))
    
    def _update_publication_relationships(self, publication, category, language_code, country_code, 
                                          topics_cache, languages_cache, regions_cache):
        """
        Update the relationships for a publication.
        
        Args:
            publication: The Publication model instance
            category: Category from the API
            language_code: Language code from the API
            country_code: Country code from the API
            topics_cache: Dictionary of topics
            languages_cache: Dictionary of languages
            regions_cache: Dictionary of regions
        """
        # Add topic if it exists
        if category and category in topics_cache:
            publication.topics.add(topics_cache[category])
        
        # Add language if it exists
        if language_code and language_code in languages_cache:
            publication.languages.add(languages_cache[language_code])
        
        # Add region if it exists
        if country_code and country_code in regions_cache:
            publication.regions.add(regions_cache[country_code])
    
    def _track_request(self, request_type, endpoint, params, response=None, error=None):
        """
        Track an API request in the database.
        """
        success = error is None and response is not None
        
        status_code = 200 if success else 0
        total_results = len(response.get('sources', [])) if success else 0
        
        request = NewsAPIRequest(
            request_type=request_type,
            endpoint=endpoint,
            params=params,
            success=success,
            status_code=status_code,
            error_message=str(error) if error else '',
            total_results=total_results,
            results_fetched=total_results
        )
        request.save()
        return request 