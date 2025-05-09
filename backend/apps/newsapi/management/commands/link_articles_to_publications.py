import logging
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import F, Count
from apps.feeds.models import Publication
from apps.articles.models import Article
from apps.newsapi.models import NewsAPIArticle
from apps.newsapi.utils import extract_domain

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Link articles to publications based on matching domains'

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Number of records to process in each batch'
        )
        
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would happen without making changes'
        )
        
        parser.add_argument(
            '--create-missing',
            action='store_true',
            help='Create publications for sources without domain matches'
        )
        
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed diagnostics for unmatched articles'
        )

    def handle(self, *args, **options):
        batch_size = options['batch_size']
        dry_run = options['dry_run']
        create_missing = options['create_missing']
        verbose = options['verbose']
        
        mode = "DRY RUN" if dry_run else "LIVE"
        self.stdout.write(self.style.SUCCESS(f'Starting article-publication linking ({mode})...'))
        
        # Count articles without publications
        unlinked_count = Article.objects.filter(publication__isnull=True).count()
        self.stdout.write(f'Found {unlinked_count} articles without linked publications')
        
        # Get publication domain mapping
        publications_by_domain = {}
        publications_by_name = {}
        
        for pub in Publication.objects.all():
            # Map by domain if available
            if pub.domain:
                publications_by_domain[pub.domain.lower()] = pub
            
            # Map by name for fallback matching
            if pub.name:
                publications_by_name[pub.name.lower()] = pub
        
        self.stdout.write(f'Loaded {len(publications_by_domain)} publications with domains')
        self.stdout.write(f'Loaded {len(publications_by_name)} publications with names')
        
        # Process missing links with domain matching
        total_linked = 0
        total_created = 0
        
        # PHASE 1: Link by exact domain match
        linked_by_domain = self._link_by_domain(
            publications_by_domain, batch_size, dry_run, verbose
        )
        total_linked += linked_by_domain
        
        # PHASE 2: Create missing publications if requested
        if create_missing and not dry_run:
            created = self._create_missing_publications(publications_by_domain, publications_by_name)
            total_created = created
            
            # Refresh publication mappings
            publications_by_domain = {}
            for pub in Publication.objects.filter(domain__isnull=False):
                if pub.domain:
                    publications_by_domain[pub.domain.lower()] = pub
            
            # Link with the new publications
            linked_after_create = self._link_by_domain(
                publications_by_domain, batch_size, dry_run, verbose
            )
            total_linked += linked_after_create
            
            self.stdout.write(f'Linked {linked_after_create} additional articles after creating publications')
        
        # Summary
        if dry_run:
            self.stdout.write(self.style.SUCCESS(
                f'DRY RUN: Would link {total_linked} articles to publications based on matching domains'
            ))
        else:
            # Count remaining unlinked
            remaining = Article.objects.filter(publication__isnull=True).count()
            self.stdout.write(self.style.SUCCESS(
                f'Linked {total_linked} articles to publications. {remaining} articles remain unlinked.'
            ))
            
            # Stats by publication
            self.stdout.write("\nArticles by publication:")
            pub_stats = Article.objects.filter(publication__isnull=False).values(
                'publication__name', 'publication__domain'
            ).annotate(count=Count('id')).order_by('-count')[:20]
            
            for stat in pub_stats:
                self.stdout.write(f"  {stat['publication__name']} ({stat['publication__domain']}): {stat['count']} articles")
    
    def _link_by_domain(self, publications_by_domain, batch_size, dry_run, verbose):
        """Link articles to publications by matching domains"""
        total_linked = 0
        
        # Get NewsAPIArticles with domain but no publication link
        offset = 0
        while True:
            # Get a batch of NewsAPIArticles
            query = NewsAPIArticle.objects.select_related('article').filter(
                domain__isnull=False,
                article__publication__isnull=True
            ).order_by('id')
            
            newsapi_articles = query[offset:offset+batch_size]
            
            if not newsapi_articles:
                break
                
            # Process each article
            with transaction.atomic():
                for newsapi_article in newsapi_articles:
                    if not newsapi_article.domain or not newsapi_article.article:
                        continue
                    
                    domain = newsapi_article.domain.lower()
                    
                    # Find matching publication
                    if domain in publications_by_domain:
                        publication = publications_by_domain[domain]
                        
                        if not dry_run:
                            article = newsapi_article.article
                            article.publication = publication
                            article.save(update_fields=['publication'])
                            
                        total_linked += 1
                        
                        # Log progress
                        if total_linked % 100 == 0 or total_linked == 1:
                            self.stdout.write(f'  Linked {total_linked} articles to publications')
                    elif verbose:
                        self.stdout.write(f'  No domain match for: {domain} (source: {newsapi_article.source_name})')
            
            # Move to next batch if not in dry run
            if not dry_run:
                offset += batch_size
            else:
                # In dry run, we just process the first batch
                break
        
        return total_linked
    
    def _create_missing_publications(self, existing_domains, existing_names):
        """Create publications for common sources without domain matches"""
        # Get source name counts for articles without matched publications
        source_counts = NewsAPIArticle.objects.filter(
            article__publication__isnull=True
        ).values('source_name').annotate(
            count=Count('id')
        ).order_by('-count')
        
        self.stdout.write(f'Found {len(source_counts)} unique source names without publication matches')
        
        # Track created publications
        created_count = 0
        
        with transaction.atomic():
            for source_info in source_counts:
                source_name = source_info['source_name']
                count = source_info['count']
                
                if not source_name:
                    continue
                
                # Skip if we already have a publication with this name
                if source_name.lower() in existing_names:
                    self.stdout.write(f'  Skipping existing publication name: {source_name}')
                    continue
                
                # Get a sample article to extract domain
                sample_article = NewsAPIArticle.objects.filter(
                    source_name=source_name,
                    article__publication__isnull=True
                ).select_related('article').first()
                
                if not sample_article:
                    continue
                
                # Extract domain from URL if possible
                domain = sample_article.domain
                if not domain and sample_article.article and sample_article.article.url:
                    domain = extract_domain(sample_article.article.url)
                
                # Skip if domain already exists
                if domain and domain.lower() in existing_domains:
                    self.stdout.write(f'  Skipping existing domain: {domain} for {source_name}')
                    continue
                
                # Create publication
                publication = Publication(
                    name=source_name,
                    domain=domain,
                    website_url=f"https://{domain}" if domain else "",
                    authority=1.0
                )
                publication.save()
                created_count += 1
                
                # Add to existing maps to prevent duplicates
                if domain:
                    existing_domains[domain.lower()] = publication
                if source_name:
                    existing_names[source_name.lower()] = publication
                
                self.stdout.write(f'  Created publication: {source_name} ({domain}) - {count} articles')
        
        self.stdout.write(self.style.SUCCESS(f'Created {created_count} new publications from source names'))
        return created_count 