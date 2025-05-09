import logging
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.feeds.models import Publication
from apps.newsapi.models import NewsAPIArticle
from apps.newsapi.utils import extract_domain, update_publication_domain, update_newsapi_article_domain

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Backfill domain field for existing publications and NewsAPI articles'

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Number of records to process in each batch'
        )
        
        parser.add_argument(
            '--only',
            type=str,
            choices=['publications', 'articles'],
            help='Only process this type of record'
        )

    def handle(self, *args, **options):
        batch_size = options['batch_size']
        only = options['only']
        
        self.stdout.write(self.style.SUCCESS(f'Starting domain backfill...'))
        
        if not only or only == 'publications':
            self._backfill_publications(batch_size)
            
        if not only or only == 'articles':
            self._backfill_articles(batch_size)
            
        self.stdout.write(self.style.SUCCESS('Domain backfill completed successfully!'))
    
    def _backfill_publications(self, batch_size):
        """Backfill domain field for all publications"""
        total_pubs = Publication.objects.filter(website_url__isnull=False).count()
        updated_pubs = 0
        
        self.stdout.write(f'Processing {total_pubs} publications...')
        
        # Process in batches
        offset = 0
        while True:
            # Get a batch of publications
            pubs_batch = Publication.objects.filter(
                website_url__isnull=False
            ).order_by('id')[offset:offset+batch_size]
            
            if not pubs_batch:
                break
                
            # Process each publication
            with transaction.atomic():
                for pub in pubs_batch:
                    if update_publication_domain(pub):
                        updated_pubs += 1
                        
                        # Log progress
                        if updated_pubs % 10 == 0:
                            self.stdout.write(f'  Updated {updated_pubs}/{total_pubs} publications')
            
            # Move to next batch
            offset += batch_size
        
        self.stdout.write(self.style.SUCCESS(f'Updated {updated_pubs} publications with domain values'))
    
    def _backfill_articles(self, batch_size):
        """Backfill domain field for all NewsAPI articles"""
        total_articles = NewsAPIArticle.objects.select_related('article').count()
        updated_articles = 0
        
        self.stdout.write(f'Processing {total_articles} NewsAPI articles...')
        
        # Process in batches
        offset = 0
        while True:
            # Get a batch of articles
            articles_batch = NewsAPIArticle.objects.select_related('article').all().order_by('id')[offset:offset+batch_size]
            
            if not articles_batch:
                break
                
            # Process each article
            with transaction.atomic():
                for article in articles_batch:
                    if update_newsapi_article_domain(article):
                        updated_articles += 1
                        
                        # Log progress
                        if updated_articles % 100 == 0:
                            self.stdout.write(f'  Updated {updated_articles}/{total_articles} articles')
            
            # Move to next batch
            offset += batch_size
        
        self.stdout.write(self.style.SUCCESS(f'Updated {updated_articles} NewsAPI articles with domain values')) 