import logging
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count
from apps.feeds.models import Publication
from apps.newsapi.models import NewsAPIArticle

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Create publications for unique domains in NewsAPI articles that have no matching publication'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would happen without making changes'
        )
        
        parser.add_argument(
            '--min-articles',
            type=int,
            default=1,
            help='Minimum number of articles required to create a publication for a domain'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        min_articles = options['min_articles']
        
        mode = "DRY RUN" if dry_run else "LIVE"
        self.stdout.write(self.style.SUCCESS(f'Creating missing publications ({mode})...'))
        
        # Get existing publication domains
        existing_domains = set(
            Publication.objects.filter(domain__isnull=False)
            .exclude(domain='')
            .values_list('domain', flat=True)
        )
        
        self.stdout.write(f'Found {len(existing_domains)} existing publication domains')
        
        # Find unique domains in articles without a matching publication
        domain_counts = NewsAPIArticle.objects.filter(
            domain__isnull=False
        ).exclude(
            domain=''
        ).exclude(
            domain__in=existing_domains
        ).values(
            'domain', 'source_name'
        ).annotate(
            article_count=Count('id')
        ).filter(
            article_count__gte=min_articles
        ).order_by('-article_count')
        
        self.stdout.write(f'Found {len(domain_counts)} unique domains without matching publications')
        
        # Create publications for each domain
        created_count = 0
        
        with transaction.atomic():
            for domain_info in domain_counts:
                domain = domain_info['domain']
                source_name = domain_info['source_name']
                article_count = domain_info['article_count']
                
                # Use the most common source_name for this domain if available
                if not source_name:
                    source_name = domain.split('.')[0].title()
                
                if not dry_run:
                    # Create publication
                    publication = Publication(
                        name=source_name,
                        domain=domain,
                        website_url=f"https://{domain}",
                        authority=1.0
                    )
                    publication.save()
                    created_count += 1
                
                self.stdout.write(f"  {'Would create' if dry_run else 'Created'} publication: {source_name} ({domain}) - {article_count} articles")
        
        # Summary
        if dry_run:
            self.stdout.write(self.style.SUCCESS(
                f'DRY RUN: Would create {len(domain_counts)} new publications from article domains'
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f'Created {created_count} new publications from article domains'
            ))
            
        self.stdout.write(self.style.SUCCESS(
            f'Run "link_articles_to_publications" next to connect articles to these new publications'
        )) 