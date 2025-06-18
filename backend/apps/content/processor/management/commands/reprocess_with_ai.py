"""
Management command to reprocess articles with AI processor.
Resets articles processed with algorithmic processor or failed processing back to pending status.
"""

import logging
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta

from apps.articles.models import Article, ProcessingStatus

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Reset articles to pending processing status for AI reprocessing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )
        parser.add_argument(
            '--hours',
            type=int,
            default=72,
            help='Hours back to look for articles (default: 72)',
        )
        parser.add_argument(
            '--include-algorithmic',
            action='store_true',
            help='Include articles processed with algorithmic/safari mode',
        )
        parser.add_argument(
            '--include-failed',
            action='store_true',
            help='Include articles that failed processing',
        )
        parser.add_argument(
            '--top-headlines-only',
            action='store_true',
            help='Only process top headlines',
        )
        parser.add_argument(
            '--limit',
            type=int,
            help='Limit number of articles to reprocess',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        hours = options['hours']
        include_algorithmic = options['include_algorithmic']
        include_failed = options['include_failed']
        top_headlines_only = options['top_headlines_only']
        limit = options['limit']
        
        if not include_algorithmic and not include_failed:
            self.stdout.write(
                self.style.ERROR("Must specify --include-algorithmic and/or --include-failed")
            )
            return
        
        cutoff_time = timezone.now() - timedelta(hours=hours)
        
        self.stdout.write(f"🔍 Looking for articles to reprocess...")
        self.stdout.write(f"   Time window: {hours} hours")
        self.stdout.write(f"   Include algorithmic: {include_algorithmic}")
        self.stdout.write(f"   Include failed: {include_failed}")
        self.stdout.write(f"   Top headlines only: {top_headlines_only}")
        self.stdout.write(f"   Dry run: {dry_run}")
        
        # Build base query
        base_query = Article.objects.filter(
            published_at__gte=cutoff_time
        )
        
        if top_headlines_only:
            base_query = base_query.filter(is_top_headline=True)
        
        # Build conditions
        conditions = Q()
        
        if include_algorithmic:
            # Articles processed with algorithmic/safari mode
            algorithmic_condition = Q(
                process_status=ProcessingStatus.COMPLETED,
                process_route__in=['safari_mode', 'algorithmic']
            )
            conditions |= algorithmic_condition
        
        if include_failed:
            # Articles that failed processing
            failed_condition = Q(process_status=ProcessingStatus.FAILED)
            conditions |= failed_condition
        
        # Get articles to reprocess
        articles_to_reprocess = base_query.filter(conditions)
        
        if limit:
            articles_to_reprocess = articles_to_reprocess[:limit]
        
        total_count = articles_to_reprocess.count()
        
        if total_count == 0:
            self.stdout.write(self.style.SUCCESS("✅ No articles found to reprocess!"))
            return
        
        # Analyze what we're about to reprocess
        self.stdout.write(f"\n📊 Found {total_count} articles to reprocess:")
        
        if include_algorithmic:
            algorithmic_count = base_query.filter(
                process_status=ProcessingStatus.COMPLETED,
                process_route__in=['safari_mode', 'algorithmic']
            ).count()
            self.stdout.write(f"   📱 Algorithmic processed: {algorithmic_count}")
        
        if include_failed:
            failed_count = base_query.filter(
                process_status=ProcessingStatus.FAILED
            ).count()
            self.stdout.write(f"   ❌ Failed processing: {failed_count}")
        
        # Show sample articles
        self.stdout.write("\n🔍 Sample Articles:")
        for article in articles_to_reprocess[:5]:
            self.stdout.write(f"   Article {article.id}: {article.title[:60]}...")
            self.stdout.write(f"      Current status: {article.process_status}")
            self.stdout.write(f"      Current route: {article.process_route or 'None'}")
            self.stdout.write(f"      Source: {article.source_name}")
            self.stdout.write("")
        
        if total_count > 5:
            self.stdout.write(f"   ... and {total_count - 5} more")
        
        # Take action if not dry run
        if dry_run:
            self.stdout.write(f"\n🔮 Would reset {total_count} articles to pending processing status")
        else:
            self.stdout.write(f"\n⚡ Resetting {total_count} articles to pending processing...")
            
            # Reset articles to pending processing
            updated = articles_to_reprocess.update(
                process_status=ProcessingStatus.PENDING,
                process_route=None,
                process_attempts=0,
                process_error_message='',
                clean_content='',
                content_blocks=[],  # Empty list instead of None
                extracted_metadata={},  # Empty dict instead of None
                content_quality_metrics={},  # Empty dict instead of None
                process_duration_ms=0,
                process_cost_usd=0.0
            )
            
            self.stdout.write(self.style.SUCCESS(f"✅ Reset {updated} articles for AI reprocessing"))
        
        # Next steps
        self.stdout.write("\n💡 Next Steps:")
        self.stdout.write("   1. Run the content enrichment pipeline to process with AI:")
        self.stdout.write("      ./docker.sh django test_pipeline --run-stage-2")
        self.stdout.write("   2. Monitor progress with:")
        self.stdout.write("      ./docker.sh django test_pipeline --status")
        self.stdout.write("   3. Check processing statistics:")
        self.stdout.write("      ./docker.sh django shell -c \"from apps.content.processor.services import ContentProcessor; print(ContentProcessor().get_processing_statistics())\"")
        
        self.stdout.write(f"\n🎯 Command completed. {total_count} articles ready for AI reprocessing.") 