"""
Management command to identify and clean up articles stuck in processing.

Handles articles stuck in PROCESSING status across all pipeline stages:
- Fetching
- Processing 
- Summarization
- Analysis

Articles stuck for more than the specified timeout are reset to PENDING status.
"""

import logging
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Q
from apps.articles.models import Article, FetchStatus, ProcessingStatus, SummarizationStatus, AnalyzerStatus

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Clean up articles stuck in processing status across all pipeline stages'

    def add_arguments(self, parser):
        parser.add_argument(
            '--check-only',
            action='store_true',
            help='Only check for stuck articles without fixing them',
        )
        
        # Global timeout options (convenience)
        parser.add_argument(
            '--timeout',
            type=int,
            help='Set timeout for all stages (hours). Overrides individual timeouts.',
        )
        parser.add_argument(
            '--timeout-minutes',
            type=int,
            help='Set timeout for all stages (minutes). Overrides individual timeouts.',
        )
        
        # Individual stage timeouts (hours)
        parser.add_argument(
            '--fetch-timeout',
            type=int,
            default=2,
            help='Hours after which fetching articles are considered stuck (default: 2)',
        )
        parser.add_argument(
            '--process-timeout',
            type=int,
            default=2,
            help='Hours after which processing articles are considered stuck (default: 2)',
        )
        parser.add_argument(
            '--summarization-timeout',
            type=int,
            default=2,
            help='Hours after which summarization articles are considered stuck (default: 2)',
        )
        parser.add_argument(
            '--analysis-timeout',
            type=int,
            default=2,
            help='Hours after which analysis articles are considered stuck (default: 2)',
        )
        
        # Individual stage timeouts (minutes for finer control)
        parser.add_argument(
            '--fetch-timeout-minutes',
            type=int,
            help='Minutes after which fetching articles are considered stuck (overrides --fetch-timeout)',
        )
        parser.add_argument(
            '--process-timeout-minutes',
            type=int,
            help='Minutes after which processing articles are considered stuck (overrides --process-timeout)',
        )
        parser.add_argument(
            '--summarization-timeout-minutes',
            type=int,
            help='Minutes after which summarization articles are considered stuck (overrides --summarization-timeout)',
        )
        parser.add_argument(
            '--analysis-timeout-minutes',
            type=int,
            help='Minutes after which analysis articles are considered stuck (overrides --analysis-timeout)',
        )
        
        # Convenience presets
        parser.add_argument(
            '--aggressive',
            action='store_true',
            help='Use aggressive timeouts (30 minutes for all stages)',
        )
        parser.add_argument(
            '--conservative',
            action='store_true',
            help='Use conservative timeouts (6 hours for all stages)',
        )
        
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed information about stuck articles',
        )

    def handle(self, *args, **options):
        check_only = options['check_only']
        verbose = options['verbose']

        # Calculate timeouts with precedence: minutes > global > individual > defaults
        timeouts = self._calculate_timeouts(options)
        
        self.stdout.write(
            self.style.SUCCESS(
                f"\n🔍 {'Checking' if check_only else 'Cleaning up'} stuck articles across all pipeline stages..."
            )
        )
        
        # Show timeout configuration
        self.stdout.write(f"⏱️  Timeout Configuration:")
        self.stdout.write(f"   • Fetch: {timeouts['fetch']:.1f}h")
        self.stdout.write(f"   • Process: {timeouts['process']:.1f}h") 
        self.stdout.write(f"   • Summarization: {timeouts['summarization']:.1f}h")
        self.stdout.write(f"   • Analysis: {timeouts['analysis']:.1f}h")
        self.stdout.write("")

        total_stuck = 0

        # 1. Check fetching stuck articles
        stuck_fetching = self._check_stuck_articles(
            status_field='fetch_status',
            status_value=FetchStatus.FETCHING,
            timestamp_field='last_fetch_attempt',
            timeout_hours=timeouts['fetch'],
            stage_name='Fetching'
        )
        total_stuck += len(stuck_fetching)

        if verbose and stuck_fetching:
            self._show_stuck_details(stuck_fetching, 'Fetching', 'last_fetch_attempt', 'fetch_attempts')

        if not check_only and stuck_fetching:
            reset_count = self._reset_stuck_articles(
                stuck_fetching,
                'fetch_status',
                FetchStatus.PENDING,
                'fetch_error_message',
                'Reset from stuck FETCHING status'
            )
            self.stdout.write(f"   ✅ Reset {reset_count} stuck fetching articles")

        # 2. Check processing stuck articles
        stuck_processing = self._check_stuck_articles(
            status_field='process_status',
            status_value=ProcessingStatus.PROCESSING,
            timestamp_field='last_process_attempt',
            timeout_hours=timeouts['process'],
            stage_name='Processing'
        )
        total_stuck += len(stuck_processing)

        if verbose and stuck_processing:
            self._show_stuck_details(stuck_processing, 'Processing', 'last_process_attempt', 'process_attempts')

        if not check_only and stuck_processing:
            reset_count = self._reset_stuck_articles(
                stuck_processing,
                'process_status',
                ProcessingStatus.PENDING,
                'process_error_message',
                'Reset from stuck PROCESSING status'
            )
            self.stdout.write(f"   ✅ Reset {reset_count} stuck processing articles")

        # 3. Check summarization stuck articles  
        stuck_summarization = self._check_stuck_articles(
            status_field='summarization_status',
            status_value=SummarizationStatus.PROCESSING,
            timestamp_field='last_summarization_attempt',
            timeout_hours=timeouts['summarization'],
            stage_name='Summarization'
        )
        total_stuck += len(stuck_summarization)

        if verbose and stuck_summarization:
            self._show_stuck_details(stuck_summarization, 'Summarization', 'last_summarization_attempt', 'summarization_attempts')

        if not check_only and stuck_summarization:
            reset_count = self._reset_stuck_articles(
                stuck_summarization,
                'summarization_status',
                SummarizationStatus.PENDING,
                'summarization_error_message',
                'Reset from stuck PROCESSING status'
            )
            self.stdout.write(f"   ✅ Reset {reset_count} stuck summarization articles")

        # 4. Check analysis stuck articles
        stuck_analysis = self._check_stuck_articles(
            status_field='analyzer_status',
            status_value=AnalyzerStatus.PROCESSING,
            timestamp_field='last_analyzer_attempt',
            timeout_hours=timeouts['analysis'],
            stage_name='Analysis'
        )
        total_stuck += len(stuck_analysis)

        if verbose and stuck_analysis:
            self._show_stuck_details(stuck_analysis, 'Analysis', 'last_analyzer_attempt', 'analyzer_attempts')

        if not check_only and stuck_analysis:
            reset_count = self._reset_stuck_articles(
                stuck_analysis,
                'analyzer_status',
                AnalyzerStatus.PENDING,
                'analyzer_error_message',
                'Reset from stuck PROCESSING status'
            )
            self.stdout.write(f"   ✅ Reset {reset_count} stuck analysis articles")

        # Summary
        if total_stuck == 0:
            self.stdout.write(self.style.SUCCESS("\n✅ No stuck articles found across all pipeline stages!"))
        else:
            action = "would be reset" if check_only else "were reset"
            self.stdout.write(
                self.style.WARNING(f"\n📊 Summary: {total_stuck} stuck articles {action} across all stages")
            )

            if check_only:
                self.stdout.write(
                    self.style.WARNING("   💡 Run without --check-only to actually reset these articles")
                )

    def _calculate_timeouts(self, options):
        """Calculate timeout values with proper precedence."""
        # Start with defaults
        timeouts = {
            'fetch': 2.0,
            'process': 2.0,
            'summarization': 2.0,
            'analysis': 2.0
        }
        
        # Apply individual hour timeouts (only if explicitly set and no preset)
        if not options['aggressive'] and not options['conservative']:
            if options['fetch_timeout'] is not None:
                timeouts['fetch'] = float(options['fetch_timeout'])
            if options['process_timeout'] is not None:
                timeouts['process'] = float(options['process_timeout'])
            if options['summarization_timeout'] is not None:
                timeouts['summarization'] = float(options['summarization_timeout'])
            if options['analysis_timeout'] is not None:
                timeouts['analysis'] = float(options['analysis_timeout'])
        
        # Apply preset configurations (overrides defaults and individual hour timeouts)
        if options['aggressive']:
            timeouts = {k: 0.5 for k in timeouts}  # 30 minutes
        elif options['conservative']:
            timeouts = {k: 6.0 for k in timeouts}  # 6 hours
        
        # Apply global timeout (overrides presets and individual)
        if options['timeout']:
            global_timeout = float(options['timeout'])
            timeouts = {k: global_timeout for k in timeouts}
        elif options['timeout_minutes']:
            global_timeout = float(options['timeout_minutes']) / 60.0
            timeouts = {k: global_timeout for k in timeouts}
        
        # Apply individual minute timeouts (highest precedence)
        if options['fetch_timeout_minutes']:
            timeouts['fetch'] = float(options['fetch_timeout_minutes']) / 60.0
        if options['process_timeout_minutes']:
            timeouts['process'] = float(options['process_timeout_minutes']) / 60.0
        if options['summarization_timeout_minutes']:
            timeouts['summarization'] = float(options['summarization_timeout_minutes']) / 60.0
        if options['analysis_timeout_minutes']:
            timeouts['analysis'] = float(options['analysis_timeout_minutes']) / 60.0
        
        return timeouts

    def _check_stuck_articles(self, status_field, status_value, timestamp_field, timeout_hours, stage_name):
        """Check for articles stuck in a specific status."""
        stuck_threshold = timezone.now() - timedelta(hours=timeout_hours)

        # Find articles stuck in the specified status
        # Include both articles with old timestamps AND articles with null timestamps (stuck without proper tracking)
        stuck_query = Q(**{status_field: status_value}) & (
            Q(**{f'{timestamp_field}__lt': stuck_threshold}) |
            Q(**{f'{timestamp_field}__isnull': True})
        )

        stuck_articles = list(Article.objects.filter(stuck_query))

        count = len(stuck_articles)
        if count > 0:
            self.stdout.write(
                self.style.WARNING(f"   ⚠️  Found {count} articles stuck in {stage_name} status")
            )
        else:
            self.stdout.write(f"   ✅ No articles stuck in {stage_name} status")

        return stuck_articles

    def _show_stuck_details(self, stuck_articles, stage_name, timestamp_field, attempts_field):
        """Show detailed information about stuck articles."""
        self.stdout.write(f"\n   📋 Stuck {stage_name} Articles Details:")
        
        for article in stuck_articles[:5]:  # Show first 5
            timestamp = getattr(article, timestamp_field)
            attempts = getattr(article, attempts_field)
            timestamp_str = timestamp.strftime('%Y-%m-%d %H:%M:%S') if timestamp else 'None'
            
            self.stdout.write(
                f"      • ID: {article.id}, Attempts: {attempts}, Last: {timestamp_str}"
            )
        
        if len(stuck_articles) > 5:
            self.stdout.write(f"      ... and {len(stuck_articles) - 5} more")

    def _reset_stuck_articles(self, stuck_articles, status_field, pending_status, error_field, error_message):
        """Reset stuck articles to pending status."""
        reset_count = 0
        
        for article in stuck_articles:
            setattr(article, status_field, pending_status)
            setattr(article, error_field, error_message)
            article.save(update_fields=[status_field, error_field])
            reset_count += 1
        
        return reset_count 