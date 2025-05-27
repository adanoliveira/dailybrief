from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from apps.articles.models import Article, ContentStatus
from apps.content.fetcher.services import ContentFetcher
from apps.content.fetcher.tasks import queue_content_fetch, queue_batch_fetch


class Command(BaseCommand):
    """Management command to fetch content for articles."""
    
    help = 'Fetch content for articles'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--article-id',
            type=int,
            help='Fetch content for a specific article ID'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=10,
            help='Maximum number of articles to process (default: 10)'
        )
        parser.add_argument(
            '--status',
            choices=['pending', 'failed', 'all'],
            default='pending',
            help='Article status to process (default: pending)'
        )
        parser.add_argument(
            '--async',
            action='store_true',
            help='Use Celery tasks for async processing'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be processed without actually doing it'
        )
    
    def handle(self, *args, **options):
        """Handle the command execution."""
        
        if options['article_id']:
            # Process specific article
            self.process_single_article(options['article_id'], options)
        else:
            # Process multiple articles
            self.process_multiple_articles(options)
    
    def process_single_article(self, article_id, options):
        """Process a single article."""
        try:
            article = Article.objects.get(id=article_id)
        except Article.DoesNotExist:
            raise CommandError(f'Article with ID {article_id} does not exist')
        
        self.stdout.write(f'Processing article {article_id}: {article.title[:50]}...')
        
        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING(f'DRY RUN: Would fetch content for article {article_id}')
            )
            return
        
        if options['async']:
            # Queue async task
            task_id = queue_content_fetch(article_id)
            self.stdout.write(
                self.style.SUCCESS(f'Queued content fetch task {task_id} for article {article_id}')
            )
        else:
            # Process synchronously
            fetcher = ContentFetcher()
            result = fetcher.fetch_article_content(article)
            
            if result.success:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully fetched content for article {article_id}: {result.message}'
                    )
                )
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f'Failed to fetch content for article {article_id}: {result.message}'
                    )
                )
    
    def process_multiple_articles(self, options):
        """Process multiple articles."""
        # Build query based on status
        if options['status'] == 'pending':
            query = Q(content_status=ContentStatus.PENDING)
        elif options['status'] == 'failed':
            query = Q(content_status__in=[
                ContentStatus.TECHNICAL_ERROR,
                ContentStatus.TIMEOUT,
                ContentStatus.ACCESS_DENIED
            ])
        else:  # all
            query = Q()
        
        # Get articles to process
        articles = Article.objects.filter(query).order_by('-published_at')[:options['limit']]
        
        if not articles:
            self.stdout.write(
                self.style.WARNING(f'No articles found with status: {options["status"]}')
            )
            return
        
        self.stdout.write(f'Found {len(articles)} articles to process')
        
        if options['dry_run']:
            self.stdout.write(self.style.WARNING('DRY RUN: Articles that would be processed:'))
            for article in articles:
                self.stdout.write(f'  - {article.id}: {article.title[:50]}... ({article.content_status})')
            return
        
        if options['async']:
            # Queue batch task
            article_ids = [article.id for article in articles]
            task_id = queue_batch_fetch(article_ids)
            self.stdout.write(
                self.style.SUCCESS(f'Queued batch fetch task {task_id} for {len(article_ids)} articles')
            )
        else:
            # Process synchronously
            fetcher = ContentFetcher()
            successful = 0
            failed = 0
            
            for article in articles:
                self.stdout.write(f'Processing {article.id}: {article.title[:50]}...')
                
                result = fetcher.fetch_article_content(article)
                
                if result.success:
                    successful += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'  ✓ Success: {result.message}')
                    )
                else:
                    failed += 1
                    self.stdout.write(
                        self.style.ERROR(f'  ✗ Failed: {result.message}')
                    )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Completed processing: {successful} successful, {failed} failed'
                )
            ) 