"""
Django management command to reset article analyzer status to pending.

This command allows resetting analyzed articles back to pending status
so they can be re-analyzed with updated logic or fixes.
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q

from apps.articles.models import Article, AnalyzerStatus
from apps.content.analyzer.models import ArticleAnalysis, AnalyzerRequest


class Command(BaseCommand):
    """Management command to reset article analyzer status to pending."""
    
    help = 'Reset article analyzer status to pending for re-analysis'
    
    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument(
            '--all',
            action='store_true',
            help='Reset all analyzed articles to pending'
        )
        group.add_argument(
            '--completed-only',
            action='store_true',
            help='Reset only completed articles to pending'
        )
        group.add_argument(
            '--failed-only',
            action='store_true',
            help='Reset only failed articles to pending'
        )
        group.add_argument(
            '--missing-primary-fields',
            action='store_true',
            help='Reset only articles missing primary_topic or primary_region'
        )
        group.add_argument(
            '--article-ids',
            type=str,
            help='Comma-separated list of specific article IDs to reset'
        )
        
        parser.add_argument(
            '--clear-analysis',
            action='store_true',
            help='Also clear existing ArticleAnalysis records'
        )
        parser.add_argument(
            '--clear-requests',
            action='store_true',
            help='Also clear existing AnalyzerRequest records'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be reset without actually doing it'
        )
        parser.add_argument(
            '--limit',
            type=int,
            help='Limit number of articles to reset'
        )
    
    def handle(self, *args, **options):
        """Main command handler."""
        dry_run = options.get('dry_run', False)
        clear_analysis = options.get('clear_analysis', False)
        clear_requests = options.get('clear_requests', False)
        limit = options.get('limit')
        
        self.stdout.write(self.style.SUCCESS("=== Analyzer Status Reset Tool ==="))
        
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - No changes will be made\n"))
        
        # Get articles to reset
        articles = self._get_articles_to_reset(options)
        
        if not articles:
            self.stdout.write(self.style.WARNING('No articles found matching criteria.'))
            return
        
        self.stdout.write(f'Found {len(articles)} articles to reset.\n')
        
        # Show sample of articles
        sample_size = min(5, len(articles))
        self.stdout.write("Sample articles to reset:")
        for article in articles[:sample_size]:
            status_info = f"Status: {article.analyzer_status}"
            topic_info = f"Primary topic: {article.primary_topic or 'None'}"
            region_info = f"Primary region: {article.primary_region or 'None'}"
            self.stdout.write(f"  - Article {article.id}: '{article.title[:60]}...'")
            self.stdout.write(f"    {status_info}, {topic_info}, {region_info}")
        
        if len(articles) > sample_size:
            self.stdout.write(f"  ... and {len(articles) - sample_size} more")
        
        self.stdout.write("")
        
        if dry_run:
            self.stdout.write(self.style.SUCCESS("DRY RUN: Would reset these articles to pending status"))
            return
        
        # Confirm action (unless dry run)
        if not options.get('article_ids'):  # Skip confirmation for specific IDs
            response = input("Are you sure you want to reset these articles? (y/N): ")
            if response.lower() != 'y':
                self.stdout.write("Operation cancelled.")
                return
        
        # Reset articles
        self._reset_articles(articles, clear_analysis, clear_requests)
    
    def _get_articles_to_reset(self, options):
        """Get list of articles to reset based on options."""
        
        if options.get('article_ids'):
            # Specific article IDs
            try:
                article_ids = [int(id.strip()) for id in options['article_ids'].split(',')]
                articles = Article.objects.filter(id__in=article_ids).order_by('id')
                
                # Check for missing articles
                found_ids = set(articles.values_list('id', flat=True))
                missing_ids = set(article_ids) - found_ids
                if missing_ids:
                    self.stdout.write(
                        self.style.WARNING(f"Articles not found: {missing_ids}")
                    )
                
                return list(articles)
                
            except ValueError:
                self.stdout.write(
                    self.style.ERROR('Invalid article IDs. Use comma-separated integers.')
                )
                return []
        
        # Base queryset
        queryset = Article.objects.all()
        
        if options.get('all'):
            # All articles that have been analyzed (completed or failed)
            queryset = queryset.filter(
                analyzer_status__in=[AnalyzerStatus.COMPLETED, AnalyzerStatus.FAILED]
            )
        elif options.get('completed_only'):
            # Only completed articles
            queryset = queryset.filter(analyzer_status=AnalyzerStatus.COMPLETED)
        elif options.get('failed_only'):
            # Only failed articles
            queryset = queryset.filter(analyzer_status=AnalyzerStatus.FAILED)
        elif options.get('missing_primary_fields'):
            # Only completed articles missing primary fields
            queryset = queryset.filter(
                analyzer_status=AnalyzerStatus.COMPLETED
            ).filter(
                Q(primary_topic__isnull=True) | Q(primary_region__isnull=True)
            )
        
        # Order by published date (most recent first)
        queryset = queryset.order_by('-published_at')
        
        # Apply limit if specified
        if options.get('limit'):
            queryset = queryset[:options['limit']]
        
        return list(queryset)
    
    def _reset_articles(self, articles, clear_analysis, clear_requests):
        """Reset articles to pending status."""
        reset_count = 0
        analysis_cleared = 0
        requests_cleared = 0
        
        with transaction.atomic():
            for article in articles:
                # Reset analyzer status and related fields
                article.analyzer_status = AnalyzerStatus.PENDING
                article.analyzer_attempts = 0
                article.analyzed_at = None
                article.analyzer_duration_ms = 0
                article.analyzer_cost_usd = 0
                article.analyzer_error_message = ''
                article.last_analyzer_attempt = None
                
                # Optionally clear primary fields to force re-classification
                if clear_analysis:
                    article.primary_topic = None
                    article.primary_region = None
                
                article.save()
                reset_count += 1
                
                # Clear analysis records if requested
                if clear_analysis:
                    deleted_count, _ = ArticleAnalysis.objects.filter(article=article).delete()
                    if deleted_count:
                        analysis_cleared += deleted_count
                
                # Clear request records if requested
                if clear_requests:
                    deleted_count, _ = AnalyzerRequest.objects.filter(article=article).delete()
                    if deleted_count:
                        requests_cleared += deleted_count
        
        # Report results
        self.stdout.write(self.style.SUCCESS(f"\n✅ Reset {reset_count} articles to pending status"))
        
        if clear_analysis and analysis_cleared:
            self.stdout.write(f"   Cleared {analysis_cleared} ArticleAnalysis records")
        
        if clear_requests and requests_cleared:
            self.stdout.write(f"   Cleared {requests_cleared} AnalyzerRequest records")
        
        self.stdout.write(f"\n💡 To re-analyze these articles, run:")
        self.stdout.write(f"   ./docker.sh django run_analyzer --limit {min(reset_count, 50)}")
        
        # Show current status summary
        self._show_status_summary()
    
    def _show_status_summary(self):
        """Show current analyzer status summary."""
        self.stdout.write("\n📊 Current analyzer status summary:")
        
        statuses = [
            (AnalyzerStatus.PENDING, "Pending"),
            (AnalyzerStatus.PROCESSING, "Processing"),
            (AnalyzerStatus.COMPLETED, "Completed"),
            (AnalyzerStatus.FAILED, "Failed"),
        ]
        
        for status, label in statuses:
            count = Article.objects.filter(analyzer_status=status).count()
            self.stdout.write(f"   {label}: {count}")
        
        # Show missing primary fields count
        missing_primary = Article.objects.filter(
            analyzer_status=AnalyzerStatus.COMPLETED
        ).filter(
            Q(primary_topic__isnull=True) | Q(primary_region__isnull=True)
        ).count()
        
        if missing_primary > 0:
            self.stdout.write(f"   Missing primary fields: {missing_primary}") 