"""
Reset Failed Articles to Fetch Pending

This command resets articles with failed processing status back to fetch pending,
allowing them to be re-fetched and re-processed with the new AI-only pipeline.
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from datetime import timedelta

from apps.articles.models import Article, ProcessingStatus, FetchStatus


class Command(BaseCommand):
    help = 'Reset failed processing articles to fetch pending status for retry'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be reset without making changes'
        )
        parser.add_argument(
            '--hours',
            type=int,
            default=72,
            help='Reset articles from the last N hours (default: 72)'
        )
        parser.add_argument(
            '--max-attempts',
            type=int,
            default=3,
            help='Only reset articles with fewer than N processing attempts (default: 3)'
        )
        parser.add_argument(
            '--article-ids',
            type=str,
            help='Comma-separated list of specific article IDs to reset'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        hours = options['hours']
        max_attempts = options['max_attempts']
        article_ids = options.get('article_ids')

        self.stdout.write("🔄 Resetting Failed Processing Articles to Fetch Pending")
        self.stdout.write(f"   Dry run: {dry_run}")
        
        # Build query
        if article_ids:
            # Parse specific article IDs
            try:
                id_list = [int(x.strip()) for x in article_ids.split(',')]
                articles_query = Article.objects.filter(id__in=id_list)
                self.stdout.write(f"   Target: Specific articles ({len(id_list)} IDs)")
            except ValueError:
                self.stdout.write(self.style.ERROR("Invalid article IDs format. Use comma-separated integers."))
                return
        else:
            # Time-based query - include articles with null timestamps for failed articles
            cutoff_time = timezone.now() - timedelta(hours=hours)
            from django.db.models import Q
            articles_query = Article.objects.filter(
                Q(last_process_attempt__gte=cutoff_time) | 
                Q(last_process_attempt__isnull=True, process_status=ProcessingStatus.FAILED)
            )
            self.stdout.write(f"   Time window: Last {hours} hours (including failed articles with null timestamps)")

        # Filter for failed processing articles that haven't exceeded max attempts
        failed_articles = articles_query.filter(
            process_status=ProcessingStatus.FAILED,
            process_attempts__lt=max_attempts
        ).select_related().order_by('-last_process_attempt')

        if not failed_articles.exists():
            self.stdout.write(self.style.WARNING("No failed articles found to reset"))
            return

        # Show summary
        total_count = failed_articles.count()
        self.stdout.write(f"   Found: {total_count} failed articles to reset")
        self.stdout.write(f"   Max attempts filter: < {max_attempts}")

        # Group by attempt count for reporting
        attempt_breakdown = {}
        for article in failed_articles:
            attempts = article.process_attempts
            if attempts not in attempt_breakdown:
                attempt_breakdown[attempts] = []
            attempt_breakdown[attempts].append(article)

        self.stdout.write("   Breakdown by attempts:")
        for attempts in sorted(attempt_breakdown.keys()):
            count = len(attempt_breakdown[attempts])
            self.stdout.write(f"     {attempts} attempts: {count} articles")

        if dry_run:
            self.stdout.write(self.style.WARNING("\n🔍 DRY RUN - No changes will be made"))
            self.stdout.write("Sample articles that would be reset:")
            for i, article in enumerate(failed_articles[:5]):
                self.stdout.write(f"   {i+1}. [{article.id}] {article.title[:60]}...")
                self.stdout.write(f"      Attempts: {article.process_attempts}, Status: {article.process_status}")
                self.stdout.write(f"      Last attempt: {article.last_process_attempt}")
                if article.process_error_message:
                    error_preview = article.process_error_message[:100]
                    self.stdout.write(f"      Error: {error_preview}...")
            
            if total_count > 5:
                self.stdout.write(f"   ... and {total_count - 5} more articles")
            return

        # Confirm before proceeding
        if not article_ids:  # Only ask for confirmation for bulk operations
            confirm = input(f"\nProceed to reset {total_count} articles? [y/N]: ")
            if confirm.lower() != 'y':
                self.stdout.write("Operation cancelled")
                return

        # Reset articles to fetch pending
        self.stdout.write(f"\n🔄 Resetting {total_count} articles to fetch pending...")
        
        reset_count = 0
        with transaction.atomic():
            for article in failed_articles:
                try:
                    # Store original status for logging
                    original_process_status = article.process_status
                    original_fetch_status = article.fetch_status
                    original_process_attempts = article.process_attempts
                    
                    # Reset to fetch pending
                    article.fetch_status = FetchStatus.PENDING
                    article.fetch_attempts = 0  # Reset fetch attempts
                    article.fetch_error_message = ""  # Clear fetch errors
                    article.process_status = ProcessingStatus.PENDING  # Reset process status too
                    # Keep process_attempts and process_error_message for tracking
                    
                    article.save(update_fields=[
                        'fetch_status',
                        'fetch_attempts', 
                        'fetch_error_message',
                        'process_status'
                    ])
                    
                    reset_count += 1
                    
                    self.stdout.write(
                        f"   ✅ [{article.id}] Reset to fetch pending "
                        f"(was: process={original_process_status}, fetch={original_fetch_status}, "
                        f"attempts={original_process_attempts})"
                    )
                    
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"   ❌ [{article.id}] Failed to reset: {e}")
                    )

        # Summary
        self.stdout.write(f"\n✅ Reset complete!")
        self.stdout.write(f"   Successfully reset: {reset_count} articles")
        self.stdout.write(f"   Articles are now in fetch_status='pending' and will be re-fetched and re-processed")
        
        if reset_count > 0:
            self.stdout.write(f"\n💡 Next steps:")
            self.stdout.write(f"   1. Run fetch pipeline: ./docker.sh django run_pipeline_stage1 --limit={min(reset_count, 50)}")
            self.stdout.write(f"   2. Run process pipeline: ./docker.sh django run_pipeline_stage2 --limit={min(reset_count, 50)}")
            self.stdout.write(f"   3. Monitor with: ./docker.sh django check_pipeline_status") 