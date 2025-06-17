"""
Management command to run article analysis.

Usage:
    python manage.py run_analyzer                    # Analyze pending articles
    python manage.py run_analyzer --all              # Analyze all articles
    python manage.py run_analyzer --limit 10         # Analyze up to 10 articles
    python manage.py run_analyzer --article-id 123   # Analyze specific article
    python manage.py run_analyzer --force            # Force re-analysis
"""
import logging
from typing import List

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from django.utils import timezone

from apps.articles.models import Article, AnalyzerStatus
from apps.content.analyzer.services import AnalyzerService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Run article analysis on pending articles'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Analyze all articles regardless of status'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Limit number of articles to analyze'
        )
        parser.add_argument(
            '--article-id',
            type=int,
            help='Analyze specific article by ID'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force re-analysis of already analyzed articles'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be analyzed without actually running'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output'
        )
    
    def handle(self, *args, **options):
        """Main command handler."""
        self.verbosity = options.get('verbosity', 1)
        self.verbose = options.get('verbose', False)
        dry_run = options.get('dry_run', False)
        force = options.get('force', False)
        
        # Initialize analyzer service
        analyzer = AnalyzerService()
        
        # Get articles to analyze
        articles = self._get_articles_to_analyze(options)
        
        if not articles:
            self.stdout.write(
                self.style.WARNING('No articles found to analyze.')
            )
            return
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Found {len(articles)} articles to analyze.'
            )
        )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN - No actual analysis will be performed.')
            )
            for article in articles:
                self.stdout.write(f'  - {article.id}: {article.title[:60]}...')
            return
        
        # Analyze articles
        self._analyze_articles(articles, analyzer, force)
    
    def _get_articles_to_analyze(self, options) -> List[Article]:
        """Get list of articles to analyze based on options."""
        # Specific article
        if options.get('article_id'):
            try:
                article = Article.objects.get(id=options['article_id'])
                return [article]
            except Article.DoesNotExist:
                raise CommandError(f"Article with ID {options['article_id']} not found")
        
        from apps.articles.models import SummarizationStatus
        
        # Base query with required pipeline order: summarization must be completed first
        queryset = Article.objects.filter(
            summarization_status=SummarizationStatus.COMPLETED  # Pipeline requirement
        ).filter(
            Q(clean_content__isnull=False) | Q(basic_content__isnull=False)
        ).filter(
            Q(clean_content__regex=r'.{100,}') | Q(basic_content__regex=r'.{100,}')
        ).select_related('language', 'primary_topic', 'primary_region')
        
        # Filter by status
        if not options.get('all') and not options.get('force'):
            # Only pending articles that need analysis
            queryset = queryset.filter(
                analyzer_status=AnalyzerStatus.PENDING,
                analyzer_attempts__lt=3  # Don't retry failed articles too many times
            )
        elif options.get('all'):
            # All articles with completed summarization
            pass
        
        # Order by priority (most recent first)
        queryset = queryset.order_by('-published_at')
        
        # Apply limit after ordering
        if options.get('limit'):
            queryset = queryset[:options['limit']]
        
        return list(queryset)
    
    def _analyze_articles(self, articles: List[Article], analyzer: AnalyzerService, force: bool):
        """Analyze the list of articles."""
        successful = 0
        failed = 0
        skipped = 0
        
        for i, article in enumerate(articles, 1):
            self.stdout.write(
                f'\n[{i}/{len(articles)}] Analyzing: {article.title[:60]}...'
            )
            
            if self.verbose:
                self.stdout.write(f'  Article ID: {article.id}')
                self.stdout.write(f'  Published: {article.published_at}')
                self.stdout.write(f'  Current status: {article.analyzer_status}')
                self.stdout.write(f'  Content length: {len(article.best_content_for_analysis or "")} chars')
            
            try:
                # Run analysis
                result = analyzer.analyze_article(article, force=force)
                
                if result['success']:
                    successful += 1
                    duration = result.get('duration_ms', 0)
                    cost = result.get('cost_usd', 0)
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  ✓ Completed in {duration}ms for ${cost:.6f}'
                        )
                    )
                    
                    if self.verbose and 'results' in result:
                        results = result['results']
                        self.stdout.write(f'  - Linguistic: {results.get("linguistic", {}).get("success", False)}')
                        self.stdout.write(f'  - Entities: {results.get("entities", {}).get("entities_processed", 0)} processed')
                        self.stdout.write(f'  - Events: {results.get("events", {}).get("event_created", False)}')
                        self.stdout.write(f'  - Topics: {results.get("topics", {}).get("primary_topic", "None")}')
                        self.stdout.write(f'  - Regions: {results.get("regions", {}).get("primary_region", "None")}')
                
                else:
                    if result.get('reason') == 'Article does not need analysis':
                        skipped += 1
                        self.stdout.write(
                            self.style.WARNING(f'  - Skipped: {result["reason"]}')
                        )
                    else:
                        failed += 1
                        error = result.get('error', result.get('reason', 'Unknown error'))
                        self.stdout.write(
                            self.style.ERROR(f'  ✗ Failed: {error}')
                        )
                
            except Exception as e:
                failed += 1
                self.stdout.write(
                    self.style.ERROR(f'  ✗ Exception: {str(e)}')
                )
                
                if self.verbose:
                    import traceback
                    self.stdout.write(traceback.format_exc())
        
        # Summary
        self.stdout.write('\n' + '='*50)
        self.stdout.write(f'Analysis Summary:')
        self.stdout.write(f'  Successful: {successful}')
        self.stdout.write(f'  Failed: {failed}')
        self.stdout.write(f'  Skipped: {skipped}')
        self.stdout.write(f'  Total: {len(articles)}')
        
        if successful > 0:
            self.stdout.write(
                self.style.SUCCESS(f'\n✓ Successfully analyzed {successful} articles!')
            )
        
        if failed > 0:
            self.stdout.write(
                self.style.ERROR(f'\n✗ {failed} articles failed analysis.')
            ) 