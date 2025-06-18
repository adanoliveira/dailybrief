"""
Management command to test and monitor the content enrichment pipeline.

Usage:
  python manage.py test_pipeline --status  # Show pipeline status
  python manage.py test_pipeline --run     # Run pipeline once
  python manage.py test_pipeline --cleanup # Clean up failed articles
"""

from django.core.management.base import BaseCommand
import json
from apps.content.tasks import (
    process_top_headlines_pipeline,
    get_pipeline_status, 
    cleanup_failed_pipeline_articles,
    retry_failed_pipeline_stages
)


class Command(BaseCommand):
    help = 'Test and monitor the content enrichment pipeline'

    def add_arguments(self, parser):
        parser.add_argument(
            '--status',
            action='store_true',
            help='Show current pipeline status',
        )
        parser.add_argument(
            '--run',
            action='store_true', 
            help='Run the pipeline once',
        )
        parser.add_argument(
            '--cleanup',
            action='store_true',
            help='Clean up failed pipeline articles',
        )
        parser.add_argument(
            '--retry',
            type=str,
            choices=['fetch', 'process', 'summarize', 'analyze', 'all'],
            help='Retry failed articles for specific stage',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=20,
            help='Limit number of articles to process (default: 20)',
        )

    def handle(self, *args, **options):
        if options['status']:
            self.show_pipeline_status()
        elif options['run']:
            self.run_pipeline(options['limit'])
        elif options['cleanup']:
            self.cleanup_failed_articles()
        elif options['retry']:
            self.retry_failed_stages(options['retry'], options['limit'])
        else:
            self.stdout.write(
                self.style.WARNING('Please specify an action: --status, --run, --cleanup, or --retry')
            )

    def show_pipeline_status(self):
        """Display comprehensive pipeline status."""
        self.stdout.write(self.style.SUCCESS('📊 Content Enrichment Pipeline Status'))
        self.stdout.write('=' * 60)
        
        try:
            status = get_pipeline_status.delay()
            result = status.get()
            
            if 'error' in result:
                self.stdout.write(self.style.ERROR(f'❌ Error: {result["error"]}'))
                return
            
            # Display overview
            self.stdout.write(f'📰 Total Top Headlines: {result["top_headlines_total"]}')
            self.stdout.write(f'✅ Fully Processed: {result["fully_processed"]} ({result["completion_rate"]:.1f}%)')
            self.stdout.write('')
            
            # Stage 1: Fetch
            self.stdout.write(self.style.HTTP_INFO('🔄 Stage 1: Content Fetching'))
            self.stdout.write(f'  • Pending: {result["stage_1_pending"]}')
            self.stdout.write(f'  • Processing: {result["stage_1_processing"]}')
            self.stdout.write(f'  • Completed: {result["stage_1_completed"]}')
            self.stdout.write(f'  • Failed: {result["stage_1_failed"]}')
            self.stdout.write('')
            
            # Stage 2: Process
            self.stdout.write(self.style.HTTP_INFO('🧠 Stage 2: AI Processing'))
            self.stdout.write(f'  • Pending: {result["stage_2_pending"]}')
            self.stdout.write(f'  • Processing: {result["stage_2_processing"]}')
            self.stdout.write(f'  • Completed: {result["stage_2_completed"]}')
            self.stdout.write(f'  • Failed: {result["stage_2_failed"]}')
            self.stdout.write('')
            
            # Stage 3: Summarize
            self.stdout.write(self.style.HTTP_INFO('📝 Stage 3: Summarization'))
            self.stdout.write(f'  • Pending: {result["stage_3_pending"]}')
            self.stdout.write(f'  • Processing: {result["stage_3_processing"]}')
            self.stdout.write(f'  • Completed: {result["stage_3_completed"]}')
            self.stdout.write(f'  • Failed: {result["stage_3_failed"]}')
            self.stdout.write('')
            
            # Stage 4: Analyze
            self.stdout.write(self.style.HTTP_INFO('🔍 Stage 4: Analysis'))
            self.stdout.write(f'  • Pending: {result["stage_4_pending"]}')
            self.stdout.write(f'  • Processing: {result["stage_4_processing"]}')
            self.stdout.write(f'  • Completed: {result["stage_4_completed"]}')
            self.stdout.write(f'  • Failed: {result["stage_4_failed"]}')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Failed to get status: {str(e)}'))

    def run_pipeline(self, limit):
        """Run the pipeline once."""
        self.stdout.write(self.style.SUCCESS(f'🚀 Running Content Enrichment Pipeline (limit: {limit})'))
        self.stdout.write('=' * 60)
        
        try:
            # Run the pipeline
            task = process_top_headlines_pipeline.delay(limit=limit)
            self.stdout.write('⏳ Pipeline task started, waiting for completion...')
            
            result = task.get()  # Wait for completion
            
            if 'pipeline_error' in result:
                self.stdout.write(self.style.ERROR(f'❌ Pipeline failed: {result["pipeline_error"]}'))
                return
            
            # Display results
            summary = result['pipeline_summary']
            self.stdout.write(self.style.SUCCESS('✅ Pipeline completed!'))
            self.stdout.write('')
            self.stdout.write(f'📊 Summary:')
            self.stdout.write(f'  • Total articles processed: {summary["total_articles_processed"]}')
            self.stdout.write(f'  • Successful completions: {summary["successful_completions"]}')
            self.stdout.write(f'  • Duration: {summary["pipeline_duration_ms"]}ms')
            self.stdout.write('')
            
            # Show stage results
            for stage_name, stage_key in [
                ('Fetch', 'stage_1_fetch'),
                ('Process', 'stage_2_process'), 
                ('Summarize', 'stage_3_summarize'),
                ('Analyze', 'stage_4_analyze')
            ]:
                stage_result = result[stage_key]
                if stage_result:
                    self.stdout.write(f'{stage_name}: {stage_result.get("processed", 0)} processed, '
                                    f'{stage_result.get("successful", 0)} successful, '
                                    f'{stage_result.get("failed", 0)} failed')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Pipeline execution failed: {str(e)}'))

    def cleanup_failed_articles(self):
        """Clean up articles that exceeded max retry attempts."""
        self.stdout.write(self.style.SUCCESS('🧹 Cleaning up failed pipeline articles'))
        self.stdout.write('=' * 60)
        
        try:
            task = cleanup_failed_pipeline_articles.delay(max_attempts=3)
            result = task.get()
            
            if 'error' in result:
                self.stdout.write(self.style.ERROR(f'❌ Cleanup failed: {result["error"]}'))
                return
            
            self.stdout.write(self.style.SUCCESS('✅ Cleanup completed!'))
            self.stdout.write('')
            self.stdout.write(f'📊 Articles marked as failed:')
            self.stdout.write(f'  • Fetch failures: {result["fetch_failures"]}')
            self.stdout.write(f'  • Process failures: {result["process_failures"]}')
            self.stdout.write(f'  • Summarization failures: {result["summarization_failures"]}')
            self.stdout.write(f'  • Analyzer failures: {result["analyzer_failures"]}')
            self.stdout.write(f'  • Total cleaned: {result["total_cleaned"]}')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Cleanup failed: {str(e)}'))

    def retry_failed_stages(self, stage, limit):
        """Retry failed articles for specific stages."""
        self.stdout.write(self.style.SUCCESS(f'🔄 Retrying failed {stage} articles (limit: {limit})'))
        self.stdout.write('=' * 60)
        
        try:
            task = retry_failed_pipeline_stages.delay(stage=stage, limit=limit)
            result = task.get()
            
            if 'error' in result:
                self.stdout.write(self.style.ERROR(f'❌ Retry failed: {result["error"]}'))
                return
            
            self.stdout.write(self.style.SUCCESS('✅ Retry completed!'))
            self.stdout.write('')
            self.stdout.write(f'📊 Results:')
            self.stdout.write(f'  • Articles retried: {result["retried"]}')
            self.stdout.write(f'  • Stage: {result["stage"]}')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Retry failed: {str(e)}')) 