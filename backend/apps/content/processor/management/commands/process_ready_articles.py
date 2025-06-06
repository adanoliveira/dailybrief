"""
Django management command to process articles that already have content.
This script can run continuously to process articles from the "ready queue".
"""
import time
from datetime import datetime, date
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q

from apps.articles.models import Article
from apps.content.processor.ai_processor import AIContentProcessor
from apps.content.processor.algorithmic_processor import AlgorithmicProcessor
from ...models import serialize_content_blocks


class Command(BaseCommand):
    help = 'Process articles that already have content and are ready for processing'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--processor',
            choices=['algorithmic', 'ai'],
            default='ai',
            help='Processor type to use (default: ai)'
        )
        parser.add_argument(
            '--template',
            type=str,
            default='algorithmic_extraction_v3',
            help='AI template to use for extraction (default: algorithmic_extraction_v3)'
        )
        parser.add_argument(
            '--date',
            type=str,
            help='Date to filter articles (YYYY-MM-DD format, e.g., 2025-06-05)'
        )
        parser.add_argument(
            '--date-from',
            type=str,
            help='Start date for date range (YYYY-MM-DD format)'
        )
        parser.add_argument(
            '--date-to',
            type=str,
            help='End date for date range (YYYY-MM-DD format)'
        )
        parser.add_argument(
            '--regions',
            type=str,
            help='Comma-separated region codes (e.g., us,ca,uk,br)'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=50,
            help='Number of articles to process per batch (default: 50)'
        )
        parser.add_argument(
            '--min-html-length',
            type=int,
            default=1000,
            help='Minimum HTML length to consider (default: 1000)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Reprocess articles that already have been processed'
        )
        parser.add_argument(
            '--continuous',
            action='store_true',
            help='Run continuously, processing in batches with delays'
        )
        parser.add_argument(
            '--delay',
            type=int,
            default=60,
            help='Delay between batches in continuous mode (seconds, default: 60)'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed processing information'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be processed without actually processing'
        )
    
    def handle(self, *args, **options):
        # Parse date options
        target_date = None
        date_from = None
        date_to = None
        
        if options.get('date'):
            try:
                target_date = datetime.strptime(options['date'], '%Y-%m-%d').date()
            except ValueError:
                self.stdout.write(
                    self.style.ERROR(f"❌ Invalid date format. Use YYYY-MM-DD")
                )
                return
        
        if options.get('date_from'):
            try:
                date_from = datetime.strptime(options['date_from'], '%Y-%m-%d').date()
            except ValueError:
                self.stdout.write(
                    self.style.ERROR(f"❌ Invalid date-from format. Use YYYY-MM-DD")
                )
                return
        
        if options.get('date_to'):
            try:
                date_to = datetime.strptime(options['date_to'], '%Y-%m-%d').date()
            except ValueError:
                self.stdout.write(
                    self.style.ERROR(f"❌ Invalid date-to format. Use YYYY-MM-DD")
                )
                return
        
        # Parse other options
        processor_type = options['processor']
        template = options['template']
        region_codes = [r.strip() for r in options['regions'].split(',')] if options.get('regions') else None
        limit = options['limit']
        min_html_length = options['min_html_length']
        force = options['force']
        continuous = options['continuous']
        delay = options['delay']
        verbose = options['verbose']
        dry_run = options['dry_run']
        
        # Show configuration
        self.stdout.write("=" * 80)
        processor_emoji = "🤖" if processor_type == 'ai' else "🧠"
        processor_name = "AI PROCESSOR" if processor_type == 'ai' else "ALGORITHMIC PROCESSOR"
        self.stdout.write(
            self.style.SUCCESS(f"{processor_emoji} {processor_name} - READY ARTICLES")
        )
        self.stdout.write("=" * 80)
        
        if target_date:
            self.stdout.write(f"📅 Target date: {target_date}")
        elif date_from or date_to:
            self.stdout.write(f"📅 Date range: {date_from or 'any'} to {date_to or 'any'}")
        else:
            self.stdout.write("📅 Date filter: None (all dates)")
        
        if region_codes:
            self.stdout.write(f"🌍 Regions: {', '.join(region_codes)}")
        else:
            self.stdout.write("🌍 Regions: All regions")
        
        self.stdout.write(f"🔧 Processor: {processor_type.upper()}")
        if processor_type == 'ai':
            self.stdout.write(f"📋 Template: {template}")
        self.stdout.write(f"📊 Batch limit: {limit}")
        self.stdout.write(f"📏 Min HTML length: {min_html_length:,}")
        self.stdout.write(f"🔄 Force reprocess: {'Yes' if force else 'No'}")
        self.stdout.write(f"🔄 Continuous mode: {'Yes' if continuous else 'No'}")
        if continuous:
            self.stdout.write(f"⏱️  Batch delay: {delay}s")
        if dry_run:
            self.stdout.write(self.style.WARNING("🧪 DRY RUN MODE - No changes will be made"))
        
        # Initialize processor
        if processor_type == 'ai':
            processor = AIContentProcessor(template)
        else:
            processor = AlgorithmicProcessor()
        
        batch_count = 0
        total_processed = 0
        total_successful = 0
        total_cost = 0.0
        
        try:
            while True:
                batch_count += 1
                batch_start_time = time.time()
                
                self.stdout.write(f"\n" + "=" * 60)
                if continuous:
                    self.stdout.write(f"🔄 BATCH {batch_count} - {datetime.now().strftime('%H:%M:%S')}")
                else:
                    self.stdout.write(f"🔄 PROCESSING READY ARTICLES")
                self.stdout.write("=" * 60)
                
                # Build the query for articles ready to process
                articles_query = Article.objects.filter(
                    raw_html__isnull=False
                ).exclude(
                    raw_html=''
                ).exclude(
                    raw_html__exact=''
                ).extra(
                    where=["CHAR_LENGTH(raw_html) > %s"],
                    params=[min_html_length]
                )
                
                # Apply date filters
                if target_date:
                    articles_query = articles_query.filter(published_at__date=target_date)
                elif date_from or date_to:
                    if date_from:
                        articles_query = articles_query.filter(published_at__date__gte=date_from)
                    if date_to:
                        articles_query = articles_query.filter(published_at__date__lte=date_to)
                
                # Apply region filter
                if region_codes:
                    articles_query = articles_query.filter(
                        regions__code__in=region_codes
                    ).distinct()
                
                # Filter out already processed articles (unless force)
                if not force:
                    if processor_type == 'ai':
                        # Include articles that need AI processing:
                        # 1. Never attempted (no ai_extraction metadata)
                        # 2. Failed but should be retried (process_attempts < 3 and not permanently failed)
                        from apps.articles.models import ProcessingStatus
                        articles_query = articles_query.filter(
                            Q(
                                # Never attempted AI processing
                                Q(extracted_metadata__isnull=True) |
                                ~Q(extracted_metadata__has_key='ai_extraction') |
                                Q(extracted_metadata__ai_extraction=False)
                            ) |
                            Q(
                                # Failed but eligible for retry
                                process_status__in=[ProcessingStatus.PENDING, ProcessingStatus.PROCESSING],
                                process_attempts__lt=3
                            )
                        )
                    else:
                        # Exclude articles already processed algorithmically
                        articles_query = articles_query.exclude(
                            content_blocks__isnull=False,
                            process_status='processed'
                        ).exclude(
                            extracted_metadata__ai_extraction=True  # Don't downgrade from AI to algorithmic
                        )
                
                # Order and limit
                articles = list(
                    articles_query.order_by('-published_at')[:limit]
                )
                
                if not articles:
                    self.stdout.write("✅ No articles found ready for processing")
                    if not continuous:
                        break
                    else:
                        self.stdout.write(f"⏳ Waiting {delay}s before next batch...")
                        time.sleep(delay)
                        continue
                
                # Show batch info
                self.stdout.write(f"📰 Found {len(articles)} articles ready for processing")
                
                if verbose:
                    date_range = f"{articles[-1].published_at.date()} to {articles[0].published_at.date()}"
                    self.stdout.write(f"📅 Date range: {date_range}")
                    
                    # Content statistics
                    total_html_length = sum(len(art.raw_html) for art in articles)
                    avg_html_length = total_html_length / len(articles)
                    self.stdout.write(f"📊 Avg HTML length: {avg_html_length:.0f} chars")
                    
                    # Sample articles
                    self.stdout.write(f"\n📋 Sample articles:")
                    for i, article in enumerate(articles[:3], 1):
                        regions = ', '.join([r.code for r in article.regions.all()]) if region_codes else 'N/A'
                        self.stdout.write(f"   {i}. ID:{article.id} - {article.title[:50]}... ({len(article.raw_html):,} chars)")
                    if len(articles) > 3:
                        self.stdout.write(f"   ... and {len(articles) - 3} more articles")
                
                if dry_run:
                    self.stdout.write(f"🧪 DRY RUN: Would process {len(articles)} articles with {processor_type}")
                    if not continuous:
                        break
                    else:
                        self.stdout.write(f"⏳ Waiting {delay}s before next batch...")
                        time.sleep(delay)
                        continue
                
                # Process articles
                batch_successful = 0
                batch_failed = 0
                batch_cost = 0.0
                
                for i, article in enumerate(articles, 1):
                    if verbose:
                        self.stdout.write(f"[{i:3d}/{len(articles)}] Processing: {article.title[:50]}...")
                    elif i % 5 == 0:
                        self.stdout.write(f"Progress: {i}/{len(articles)} articles...")
                    
                    try:
                        if processor_type == 'ai':
                            success, cost = self._process_with_ai(article, processor, verbose)
                            batch_cost += cost
                        else:
                            success = self._process_with_algorithmic(article, processor, verbose)
                        
                        if success:
                            batch_successful += 1
                        else:
                            batch_failed += 1
                            
                    except Exception as e:
                        batch_failed += 1
                        if verbose:
                            self.stdout.write(f"   💥 Exception: {str(e)[:50]}")
                
                # Batch results
                batch_time = time.time() - batch_start_time
                total_processed += len(articles)
                total_successful += batch_successful
                total_cost += batch_cost
                
                self.stdout.write(f"\n📊 Batch {batch_count} Results:")
                self.stdout.write(f"   ✅ Successful: {batch_successful}")
                self.stdout.write(f"   ❌ Failed: {batch_failed}")
                self.stdout.write(f"   ⏱️  Time: {batch_time:.1f}s")
                if processor_type == 'ai' and batch_cost > 0:
                    self.stdout.write(f"   💰 Cost: ${batch_cost:.3f}")
                self.stdout.write(f"   📈 Total successful: {total_successful}")
                
                if not continuous:
                    break
                
                # Wait before next batch
                self.stdout.write(f"⏳ Waiting {delay}s before next batch...")
                time.sleep(delay)
                
        except KeyboardInterrupt:
            self.stdout.write(f"\n🛑 Interrupted by user")
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Fatal error: {str(e)}")
            )
        
        # Final summary
        self.stdout.write(f"\n" + "=" * 80)
        self.stdout.write(self.style.SUCCESS("📋 FINAL SUMMARY"))
        self.stdout.write("=" * 80)
        self.stdout.write(f"🔄 Total batches: {batch_count}")
        self.stdout.write(f"📰 Total articles processed: {total_processed}")
        self.stdout.write(f"✅ Total successful: {total_successful}")
        if total_processed > 0:
            success_rate = (total_successful / total_processed) * 100
            self.stdout.write(f"📈 Success rate: {success_rate:.1f}%")
        if processor_type == 'ai' and total_cost > 0:
            self.stdout.write(f"💰 Total cost: ${total_cost:.3f}")
            if total_successful > 0:
                avg_cost = total_cost / total_successful
                self.stdout.write(f"💰 Avg cost per article: ${avg_cost:.3f}")
        self.stdout.write(f"⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.stdout.write("=" * 80)
    
    def _process_with_ai(self, article, processor, verbose):
        """Process article with AI processor with smart retry logic. Returns (success, cost)."""
        try:
            result = processor.process_content(
                article.raw_html,
                {
                    'title': article.title,
                    'url': article.url,
                    'source': article.source_name
                },
                base_url=article.url
            )
            
            # Calculate cost
            cost = 0.0
            if result.extracted_metadata:
                token_usage = result.extracted_metadata.get('token_usage', 0)
                cost = token_usage * 0.00001  # Rough estimate
            
            if result.success:
                # Save the results
                article.clean_content = result.clean_content
                article.content_blocks = serialize_content_blocks(result.content_blocks)
                
                # Update with AI extraction metadata
                if not article.extracted_metadata:
                    article.extracted_metadata = {}
                
                ai_metadata = result.extracted_metadata or {}
                article.extracted_metadata.update({
                    'ai_extraction': True,
                    'template_used': processor.template_id,
                    'processing_time_ms': result.processing_time_ms,
                    'token_usage': ai_metadata.get('token_usage', 0),
                    'visual_title': ai_metadata.get('visual_title'),
                    'extraction_timestamp': datetime.now().isoformat()
                })
                
                article.process_status = 'completed'
                article.process_route = 'llm_enhanced'
                article.process_duration_ms = result.processing_time_ms
                article.save()
                
                if verbose:
                    blocks = len(result.content_blocks)
                    quality = result.quality_score
                    tokens = ai_metadata.get('token_usage', 0)
                    self.stdout.write(f"   ✅ Success: Q:{quality:.3f}, {blocks}b, {tokens}t, ${cost:.3f}")
                
                return True, cost
            else:
                # Determine if this is a retryable failure
                should_retry = self._should_retry_ai_failure(result, article)
                
                if should_retry:
                    # Update retry tracking but don't mark as failed yet
                    article.process_attempts += 1
                    article.last_process_attempt = datetime.now()
                    article.process_error_message = result.error_message[:500]
                    article.save()
                    
                    if verbose:
                        error_msg = result.error_message[:50] if result.error_message else "Unknown error"
                        self.stdout.write(f"   🔄 Will retry ({article.process_attempts}/3): {error_msg}")
                else:
                    # Mark as permanently failed
                    article.process_status = 'failed'
                    article.process_attempts += 1
                    article.last_process_attempt = datetime.now()
                    article.process_error_message = result.error_message[:500]
                    article.save()
                    
                    if verbose:
                        error_msg = result.error_message[:50] if result.error_message else "Unknown error"
                        self.stdout.write(f"   ❌ Failed permanently: {error_msg}")
                
                return False, cost
                
        except Exception as e:
            # Handle processing exceptions with retry logic
            should_retry = self._should_retry_exception(e, article)
            
            if should_retry:
                article.process_attempts += 1
                article.last_process_attempt = datetime.now()
                article.process_error_message = str(e)[:500]
                article.save()
                
                if verbose:
                    self.stdout.write(f"   🔄 Will retry ({article.process_attempts}/3): {str(e)[:50]}")
            else:
                article.process_status = 'failed'
                article.process_attempts += 1
                article.last_process_attempt = datetime.now()
                article.process_error_message = str(e)[:500]
                article.save()
                
                if verbose:
                    self.stdout.write(f"   ❌ Failed permanently: {str(e)[:50]}")
            
            return False, 0.0
    
    def _should_retry_ai_failure(self, result, article):
        """Determine if an AI processing failure should be retried."""
        if article.process_attempts >= 3:
            return False
        
        error_message = result.error_message.lower() if result.error_message else ""
        
        # Retry for transient issues
        retryable_errors = [
            "timeout", "rate limit", "network", "connection",
            "internal server error", "service unavailable",
            "too many requests", "throttle", "quota exceeded"
        ]
        
        for error_type in retryable_errors:
            if error_type in error_message:
                return True
        
        # Don't retry for permanent issues
        permanent_errors = [
            "invalid api key", "unauthorized", "forbidden",
            "no valid content blocks", "html preprocessing failed",
            "content too short", "no extractable content"
        ]
        
        for error_type in permanent_errors:
            if error_type in error_message:
                return False
        
        # Default to retry for unknown errors (could be transient)
        return True
    
    def _should_retry_exception(self, exception, article):
        """Determine if a processing exception should be retried."""
        if article.process_attempts >= 3:
            return False
        
        exception_str = str(exception).lower()
        
        # Retry for network/API issues
        retryable_exceptions = [
            "timeout", "connection", "network", "dns",
            "httperror", "requests", "urllib", "ssl"
        ]
        
        for error_type in retryable_exceptions:
            if error_type in exception_str:
                return True
        
        # Don't retry for code errors
        permanent_exceptions = [
            "keyerror", "attributeerror", "valueerror",
            "typeerror", "indexerror", "nameerror"
        ]
        
        for error_type in permanent_exceptions:
            if error_type in exception_str:
                return False
        
        # Default to retry for unknown exceptions
        return True
    
    def _process_with_algorithmic(self, article, processor, verbose):
        """Process article with algorithmic processor. Returns success."""
        try:
            result = processor.process_article(article)
            
            if result and result.get('success'):
                if verbose:
                    blocks = len(result.get('content_blocks', []))
                    quality = result.get('quality_score', 0.0)
                    self.stdout.write(f"   ✅ Success: Q:{quality:.3f}, {blocks} blocks")
                return True
            else:
                if verbose:
                    error_msg = result.get('error', 'Unknown error') if result else 'No result'
                    self.stdout.write(f"   ❌ Failed: {error_msg}")
                return False
                
        except Exception as e:
            if verbose:
                self.stdout.write(f"   💥 Exception: {str(e)[:50]}")
            return False 