"""
Django management command to fetch content for articles by date and region.
This script can run continuously to keep fetching content for articles.
"""
import time
from datetime import datetime, date
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.articles.models import Article
from apps.content.fetcher.fetcher import ContentFetcher


class Command(BaseCommand):
    help = 'Fetch content for articles filtered by date and region'
    
    def add_arguments(self, parser):
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
            default='us,ca,uk,br',
            help='Comma-separated region codes (default: us,ca,uk,br)'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=100,
            help='Number of articles to process per batch (default: 100)'
        )
        parser.add_argument(
            '--status',
            choices=['pending', 'failed', 'all'],
            default='pending',
            help='Fetch status to process (default: pending)'
        )
        parser.add_argument(
            '--continuous',
            action='store_true',
            help='Run continuously, fetching in batches with delays'
        )
        parser.add_argument(
            '--delay',
            type=int,
            default=30,
            help='Delay between batches in continuous mode (seconds, default: 30)'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed processing information'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be fetched without actually fetching'
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
        region_codes = [r.strip() for r in options['regions'].split(',')]
        limit = options['limit']
        status = options['status']
        continuous = options['continuous']
        delay = options['delay']
        verbose = options['verbose']
        dry_run = options['dry_run']
        
        # Show configuration
        self.stdout.write("=" * 80)
        self.stdout.write(
            self.style.SUCCESS("📥 CONTENT FETCHER BY DATE & REGION")
        )
        self.stdout.write("=" * 80)
        
        if target_date:
            self.stdout.write(f"📅 Target date: {target_date}")
        elif date_from or date_to:
            self.stdout.write(f"📅 Date range: {date_from or 'any'} to {date_to or 'any'}")
        else:
            self.stdout.write("📅 Date filter: None (all dates)")
        
        self.stdout.write(f"🌍 Regions: {', '.join(region_codes)}")
        self.stdout.write(f"📊 Batch limit: {limit}")
        self.stdout.write(f"🏷️  Status filter: {status}")
        self.stdout.write(f"🔄 Continuous mode: {'Yes' if continuous else 'No'}")
        if continuous:
            self.stdout.write(f"⏱️  Batch delay: {delay}s")
        if dry_run:
            self.stdout.write(self.style.WARNING("🧪 DRY RUN MODE - No changes will be made"))
        
        fetcher = ContentFetcher()
        batch_count = 0
        total_fetched = 0
        
        try:
            while True:
                batch_count += 1
                batch_start_time = time.time()
                
                self.stdout.write(f"\n" + "=" * 60)
                if continuous:
                    self.stdout.write(f"🔄 BATCH {batch_count} - {datetime.now().strftime('%H:%M:%S')}")
                else:
                    self.stdout.write(f"🔄 FETCHING CONTENT")
                self.stdout.write("=" * 60)
                
                # Build the query
                articles_query = Article.objects.all()
                
                # Apply date filters
                if target_date:
                    articles_query = articles_query.filter(published_at__date=target_date)
                elif date_from or date_to:
                    if date_from:
                        articles_query = articles_query.filter(published_at__date__gte=date_from)
                    if date_to:
                        articles_query = articles_query.filter(published_at__date__lte=date_to)
                
                # Apply region filter
                articles_query = articles_query.filter(
                    regions__code__in=region_codes
                ).distinct()
                
                # Apply status filter using proper Article model logic
                if status == 'pending':
                    # Articles that need fetching (match Article.needs_fetch property)
                    from apps.articles.models import FetchStatus
                    articles_query = articles_query.filter(
                        fetch_status=FetchStatus.PENDING,
                        fetch_attempts__lt=3
                    )
                elif status == 'failed':
                    # Articles that have failed fetching
                    from apps.articles.models import FetchStatus
                    articles_query = articles_query.filter(
                        fetch_status=FetchStatus.FAILED
                    )
                # 'all' means no additional filtering
                
                # Order and limit
                articles = list(
                    articles_query.order_by('-published_at')[:limit]
                )
                
                if not articles:
                    self.stdout.write("✅ No articles found needing content fetch")
                    if not continuous:
                        break
                    else:
                        self.stdout.write(f"⏳ Waiting {delay}s before next batch...")
                        time.sleep(delay)
                        continue
                
                # Show batch info
                self.stdout.write(f"📰 Found {len(articles)} articles needing content fetch")
                
                if verbose:
                    date_range = f"{articles[-1].published_at.date()} to {articles[0].published_at.date()}"
                    self.stdout.write(f"📅 Date range: {date_range}")
                    
                    # Sample articles
                    self.stdout.write(f"\n📋 Sample articles:")
                    for i, article in enumerate(articles[:5], 1):
                        regions = ', '.join([r.code for r in article.regions.all()])
                        self.stdout.write(f"   {i}. ID:{article.id} - {article.title[:50]}... (Regions: {regions})")
                    if len(articles) > 5:
                        self.stdout.write(f"   ... and {len(articles) - 5} more articles")
                
                if dry_run:
                    self.stdout.write(f"🧪 DRY RUN: Would fetch content for {len(articles)} articles")
                    if not continuous:
                        break
                    else:
                        self.stdout.write(f"⏳ Waiting {delay}s before next batch...")
                        time.sleep(delay)
                        continue
                
                # Fetch content for articles
                batch_success = 0
                batch_failed = 0
                
                for i, article in enumerate(articles, 1):
                    if verbose:
                        self.stdout.write(f"[{i:3d}/{len(articles)}] Fetching: {article.title[:50]}...")
                    elif i % 10 == 0:
                        self.stdout.write(f"Progress: {i}/{len(articles)} articles...")
                    
                    try:
                        result = fetcher.fetch_article_content(article)
                        if result.success:
                            batch_success += 1
                            if verbose:
                                content_length = len(result.extraction_result.raw_html) if result.extraction_result else 0
                                self.stdout.write(f"   ✅ Success: {content_length:,} chars")
                        else:
                            batch_failed += 1
                            if verbose:
                                error_msg = result.error_message[:50] if result.error_message else "Unknown error"
                                self.stdout.write(f"   ❌ Failed: {error_msg}")
                    except Exception as e:
                        batch_failed += 1
                        if verbose:
                            self.stdout.write(f"   💥 Exception: {str(e)[:50]}")
                
                # Batch results
                batch_time = time.time() - batch_start_time
                total_fetched += batch_success
                
                self.stdout.write(f"\n📊 Batch {batch_count} Results:")
                self.stdout.write(f"   ✅ Successful: {batch_success}")
                self.stdout.write(f"   ❌ Failed: {batch_failed}")
                self.stdout.write(f"   ⏱️  Time: {batch_time:.1f}s")
                self.stdout.write(f"   📈 Total fetched: {total_fetched}")
                
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
        self.stdout.write(f"✅ Total articles fetched: {total_fetched}")
        self.stdout.write(f"⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.stdout.write("=" * 80) 