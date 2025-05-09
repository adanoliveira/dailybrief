import logging
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

from apps.newsapi.services.sync_manager import SyncManager
from apps.newsapi.models import SyncLog

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Backfills articles from NewsAPI using a chunked approach'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days to look back for articles',
        )
        
        parser.add_argument(
            '--chunk-size',
            type=int,
            default=2,
            help='Number of days per chunk to process',
        )
        
        parser.add_argument(
            '--language',
            type=str,
            default='en',
            help='Language code for articles',
        )
        
        parser.add_argument(
            '--query',
            type=str,
            help='Search query to filter articles',
        )
        
        parser.add_argument(
            '--sources',
            type=str,
            help='Comma-separated list of source IDs to fetch articles from',
        )
        
        parser.add_argument(
            '--use-batched-sources',
            action='store_true',
            help='Use batched sources strategy instead of everything endpoint',
        )

    def handle(self, *args, **options):
        days = options['days']
        chunk_size = options['chunk_size']
        language = options['language']
        query = options.get('query')
        sources = options.get('sources')
        use_batched_sources = options.get('use_batched_sources')
        
        # Initialize params
        params = {'language': language}
        if query:
            params['q'] = query
        
        # Initialize sync manager
        sync_manager = SyncManager()
        
        # Show current status
        self.stdout.write(self.style.SUCCESS(f'Starting backfill for the last {days} days...'))
        self.stdout.write(f'Chunk size: {chunk_size} days')
        self.stdout.write(f'Language: {language}')
        if query:
            self.stdout.write(f'Query: {query}')
        if sources:
            self.stdout.write(f'Sources: {sources}')
        
        # Get recent sync logs
        recent_logs = SyncLog.objects.filter(
            status='completed',
            created_at__gt=timezone.now() - timezone.timedelta(hours=24)
        ).order_by('-created_at')[:5]
        
        if recent_logs.exists():
            self.stdout.write('\nRecent successful syncs:')
            for log in recent_logs:
                self.stdout.write(f'- {log.created_at}: {log.created_count} created, {log.updated_count} updated')
        
        # Determine backfill strategy
        if use_batched_sources and sources:
            self.backfill_by_sources(sync_manager, days, chunk_size, sources, params)
        else:
            self.backfill_everything(sync_manager, days, chunk_size, params)
    
    def backfill_everything(self, sync_manager, days, chunk_size, params):
        """
        Backfill using the 'everything' endpoint with date range chunks
        """
        total_created = 0
        total_updated = 0
        success = True
        
        try:
            # Execute backfill
            created, updated, op_success = sync_manager.backfill_articles(
                days=days,
                chunk_size=chunk_size,
                **params
            )
            
            total_created += created
            total_updated += updated
            success = success and op_success
            
            if success:
                self.stdout.write(self.style.SUCCESS(
                    f'Successfully backfilled articles: {total_created} created, {total_updated} updated'))
            else:
                self.stdout.write(self.style.ERROR(
                    f'Backfill completed with errors: {total_created} created, {total_updated} updated'))
                
        except Exception as e:
            raise CommandError(f'Error during backfill: {str(e)}')
    
    def backfill_by_sources(self, sync_manager, days, chunk_size, sources, params):
        """
        Backfill using the sources-based approach with date range chunks
        """
        # Parse source list
        source_list = [s.strip() for s in sources.split(',')]
        
        # Calculate date ranges
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        total_created = 0
        total_updated = 0
        overall_success = True
        
        self.stdout.write(f'Backfilling by sources from {start_date.date()} to {end_date.date()}')
        
        # Process each chunk
        current_start = start_date
        while current_start < end_date:
            chunk_end = min(current_start + timedelta(days=chunk_size), end_date)
            
            self.stdout.write(f'\nProcessing chunk: {current_start.date()} to {chunk_end.date()}')
            
            # Process sources in batches of 20 (API limit)
            for i in range(0, len(source_list), 20):
                batch = source_list[i:i+20]
                
                self.stdout.write(f'Processing sources batch {i//20 + 1}/{(len(source_list) + 19)//20}')
                
                # Build source param
                batch_params = {
                    **params,
                    'sources': ','.join(batch)
                }
                
                try:
                    # Fetch articles for this chunk and source batch
                    response = sync_manager.api_service.fetch_articles_by_date_range(
                        current_start, 
                        chunk_end,
                        **batch_params
                    )
                    
                    # Process articles
                    created, updated, _ = sync_manager.processor.process_articles(response)
                    
                    total_created += created
                    total_updated += updated
                    
                    self.stdout.write(f'  - Processed: {created} created, {updated} updated')
                    
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'  - Error: {str(e)}'))
                    overall_success = False
            
            # Move to next chunk
            current_start = chunk_end
        
        # Final results
        if overall_success:
            self.stdout.write(self.style.SUCCESS(
                f'Successfully backfilled articles by sources: {total_created} created, {total_updated} updated'))
        else:
            self.stdout.write(self.style.ERROR(
                f'Backfill by sources completed with errors: {total_created} created, {total_updated} updated')) 