"""
Comprehensive stuck article cleanup and monitoring command.

This command provides manual control over stuck article cleanup with detailed reporting.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q

from apps.articles.models import Article, ProcessingStatus, FetchStatus
from apps.content.processor.tasks import cleanup_processing_data
from apps.content.fetcher.tasks import cleanup_old_fetch_attempts


class Command(BaseCommand):
    help = 'Cleanup stuck articles and monitor pipeline health'

    def add_arguments(self, parser):
        parser.add_argument(
            '--check-only',
            action='store_true',
            help='Only check status without making any changes'
        )
        parser.add_argument(
            '--processing-timeout',
            type=int,
            default=2,
            help='Hours after which processing articles are considered stuck (default: 2)'
        )
        parser.add_argument(
            '--fetching-timeout',
            type=int,
            default=1,
            help='Hours after which fetching articles are considered stuck (default: 1)'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed information about stuck articles'
        )

    def handle(self, *args, **options):
        check_only = options['check_only']
        processing_timeout = options['processing_timeout']
        fetching_timeout = options['fetching_timeout']
        verbose = options['verbose']

        self.stdout.write("🔍 STUCK ARTICLE CLEANUP & MONITORING")
        self.stdout.write("=" * 50)

        # Check current status
        stuck_processing, stuck_fetching = self._analyze_stuck_articles(
            processing_timeout, fetching_timeout, verbose
        )

        if check_only:
            self.stdout.write(self.style.WARNING("\n🔍 CHECK-ONLY MODE - No changes made"))
            return

        if stuck_processing == 0 and stuck_fetching == 0:
            self.stdout.write(self.style.SUCCESS("\n✅ No stuck articles found - pipeline is healthy!"))
            return

        # Cleanup stuck articles
        self.stdout.write(f"\n🧹 CLEANING UP STUCK ARTICLES")
        self.stdout.write("-" * 30)

        # Run cleanup tasks
        if stuck_processing > 0:
            self.stdout.write(f"🔄 Running processing cleanup...")
            proc_result = cleanup_processing_data()
            reset_count = proc_result.get('stuck_articles_reset', 0)
            self.stdout.write(f"   ✅ Reset {reset_count} stuck processing articles")

        if stuck_fetching > 0:
            self.stdout.write(f"🔄 Running fetching cleanup...")
            fetch_result = cleanup_old_fetch_attempts()
            reset_count = fetch_result.get('stuck_articles_reset', 0)
            self.stdout.write(f"   ✅ Reset {reset_count} stuck fetching articles")

        # Verify cleanup
        self.stdout.write(f"\n🔍 POST-CLEANUP VERIFICATION")
        self.stdout.write("-" * 30)
        self._analyze_stuck_articles(processing_timeout, fetching_timeout, False)
        
        self.stdout.write(f"\n💡 RECOMMENDATIONS")
        self.stdout.write("-" * 20)
        self.stdout.write("• Cleanup tasks now run automatically every hour")
        self.stdout.write("• Processing timeout: 10 minutes soft / 15 minutes hard")
        self.stdout.write("• Fetching timeout: 5 minutes soft / 7.5 minutes hard")
        self.stdout.write("• Monitor Celery worker health in production")

    def _analyze_stuck_articles(self, processing_timeout: int, fetching_timeout: int, verbose: bool):
        """Analyze and report stuck articles."""
        
        # Current stuck counts
        current_stuck_processing = Article.objects.filter(
            process_status=ProcessingStatus.PROCESSING
        ).count()
        
        current_stuck_fetching = Article.objects.filter(
            fetch_status=FetchStatus.FETCHING
        ).count()

        self.stdout.write(f"📊 CURRENT STATUS")
        self.stdout.write(f"   Processing: {current_stuck_processing} stuck")
        self.stdout.write(f"   Fetching: {current_stuck_fetching} stuck")

        if verbose and (current_stuck_processing > 0 or current_stuck_fetching > 0):
            self._show_detailed_analysis(processing_timeout, fetching_timeout)

        return current_stuck_processing, current_stuck_fetching

    def _show_detailed_analysis(self, processing_timeout: int, fetching_timeout: int):
        """Show detailed analysis of stuck articles."""
        
        processing_threshold = timezone.now() - timedelta(hours=processing_timeout)
        fetching_threshold = timezone.now() - timedelta(hours=fetching_timeout)

        # Detailed processing analysis
        stuck_processing = Article.objects.filter(process_status=ProcessingStatus.PROCESSING)
        if stuck_processing.exists():
            self.stdout.write(f"\n🔍 STUCK PROCESSING ARTICLES:")
            
            # Articles with null timestamps (the bug we fixed)
            null_timestamp = stuck_processing.filter(last_process_attempt__isnull=True)
            if null_timestamp.exists():
                self.stdout.write(f"   ⚠️  {null_timestamp.count()} articles with NULL timestamps (likely from old bug)")
                for article in null_timestamp[:3]:
                    self.stdout.write(f"      ID: {article.id}, attempts: {article.process_attempts}")

            # Articles with old timestamps
            old_timestamp = stuck_processing.filter(last_process_attempt__lt=processing_threshold)
            if old_timestamp.exists():
                self.stdout.write(f"   ⏰ {old_timestamp.count()} articles stuck > {processing_timeout}h")
                for article in old_timestamp[:3]:
                    self.stdout.write(f"      ID: {article.id}, last: {article.last_process_attempt}")

            # Articles with recent timestamps (might be actively processing)
            recent_timestamp = stuck_processing.filter(
                last_process_attempt__gte=processing_threshold,
                last_process_attempt__isnull=False
            )
            if recent_timestamp.exists():
                self.stdout.write(f"   🟡 {recent_timestamp.count()} articles processing < {processing_timeout}h (might be active)")

        # Detailed fetching analysis
        stuck_fetching = Article.objects.filter(fetch_status=FetchStatus.FETCHING)
        if stuck_fetching.exists():
            self.stdout.write(f"\n🔍 STUCK FETCHING ARTICLES:")
            
            # Articles with null timestamps
            null_timestamp = stuck_fetching.filter(last_fetch_attempt__isnull=True)
            if null_timestamp.exists():
                self.stdout.write(f"   ⚠️  {null_timestamp.count()} articles with NULL timestamps")
                for article in null_timestamp[:3]:
                    self.stdout.write(f"      ID: {article.id}, attempts: {article.fetch_attempts}")

            # Articles with old timestamps
            old_timestamp = stuck_fetching.filter(last_fetch_attempt__lt=fetching_threshold)
            if old_timestamp.exists():
                self.stdout.write(f"   ⏰ {old_timestamp.count()} articles stuck > {fetching_timeout}h")
                for article in old_timestamp[:3]:
                    self.stdout.write(f"      ID: {article.id}, last: {article.last_fetch_attempt}")

            # Articles with recent timestamps
            recent_timestamp = stuck_fetching.filter(
                last_fetch_attempt__gte=fetching_threshold,
                last_fetch_attempt__isnull=False
            )
            if recent_timestamp.exists():
                self.stdout.write(f"   🟡 {recent_timestamp.count()} articles fetching < {fetching_timeout}h (might be active)") 