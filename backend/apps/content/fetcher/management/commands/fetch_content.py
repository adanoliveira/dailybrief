from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from apps.articles.models import Article, FetchStatus
from apps.content.fetcher.fetcher import ContentFetcher, FetchManager
from apps.content.fetcher.tasks import fetch_article_content, fetch_batch_articles


class Command(BaseCommand):
    """Management command to fetch content for articles using Step 1 architecture."""
    
    help = 'Fetch content for articles (Step 1 only - fast extraction)'
    
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
            help='Article fetch status to process (default: pending)'
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
            task = fetch_article_content.delay(article_id)
            self.stdout.write(
                self.style.SUCCESS(f'Queued content fetch task {task.id} for article {article_id}')
            )
        else:
            # Process synchronously
            fetcher = ContentFetcher()
            result = fetcher.fetch_article_content(article)
            
            if result.success:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully fetched content for article {article_id} '
                        f'using {result.strategy_used} in {result.duration_ms}ms'
                    )
                )
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f'Failed to fetch content for article {article_id}: {result.error_message}'
                    )
                )
    
    def process_multiple_articles(self, options):
        """Process multiple articles."""
        # Build query based on status
        if options['status'] == 'pending':
            query = Q(fetch_status=FetchStatus.PENDING)
        elif options['status'] == 'failed':
            query = Q(fetch_status=FetchStatus.FAILED)
        else:  # all
            query = Q(fetch_status__in=[FetchStatus.PENDING, FetchStatus.FAILED])
        
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
                self.stdout.write(f'  - {article.id}: {article.title[:50]}... ({article.fetch_status})')
            return
        
        if options['async']:
            # Queue batch task
            article_ids = [article.id for article in articles]
            task = fetch_batch_articles.delay(article_ids)
            self.stdout.write(
                self.style.SUCCESS(f'Queued batch fetch task {task.id} for {len(article_ids)} articles')
            )
        else:
            # Process synchronously using FetchManager
            manager = FetchManager()
            result = manager.fetch_pending_articles(limit=len(articles))
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Completed processing: {result["successful"]} successful, '
                    f'{result["failed"]} failed out of {result["processed"]} total'
                )
            ) 