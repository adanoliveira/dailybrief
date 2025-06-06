"""
Django management command to process articles by date and region using AI extraction.
"""
import time
from datetime import datetime, date
from django.core.management.base import BaseCommand
from django.core.management import call_command

from apps.articles.models import Article


class Command(BaseCommand):
    help = 'Find and process articles by date and region using AI extraction'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            required=True,
            help='Date to filter articles (YYYY-MM-DD format, e.g., 2025-06-05)'
        )
        parser.add_argument(
            '--regions',
            type=str,
            default='us,ca,uk,br',
            help='Comma-separated region codes (default: us,ca,uk,br)'
        )
        parser.add_argument(
            '--processor',
            choices=['algorithmic', 'ai'],
            default='ai',
            help='Processor type to use (default: ai)'
        )
        parser.add_argument(
            '--min-html-length',
            type=int,
            default=1000,
            help='Minimum HTML length for processing (default: 1000)'
        )
        parser.add_argument(
            '--force-process',
            action='store_true',
            help='Reprocess articles that already have rich content'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed processing information'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be processed without actually doing it'
        )
        parser.add_argument(
            '--limit',
            type=int,
            help='Limit number of articles to process'
        )
    
    def handle(self, *args, **options):
        # Parse date
        try:
            target_date = datetime.strptime(options['date'], '%Y-%m-%d').date()
        except ValueError:
            self.stdout.write(
                self.style.ERROR(f"❌ Invalid date format. Use YYYY-MM-DD (e.g., 2025-06-05)")
            )
            return
        
        # Parse regions
        region_codes = [r.strip() for r in options['regions'].split(',')]
        
        processor_type = options['processor']
        min_html_length = options['min_html_length']
        force_process = options['force_process']
        verbose = options['verbose']
        dry_run = options['dry_run']
        limit = options.get('limit')
        
        self.stdout.write("=" * 80)
        self.stdout.write(
            self.style.SUCCESS(f"🎯 PROCESSING ARTICLES BY DATE AND REGION")
        )
        self.stdout.write("=" * 80)
        self.stdout.write(f"📅 Target date: {target_date}")
        self.stdout.write(f"🌍 Regions: {', '.join(region_codes)}")
        self.stdout.write(f"🤖 Processor: {processor_type.upper()}")
        if dry_run:
            self.stdout.write(self.style.WARNING("🧪 DRY RUN MODE - No changes will be made"))
        
        # Find articles
        self.stdout.write(f"\n📊 Searching for articles...")
        
        articles_query = Article.objects.filter(
            published_at__date=target_date,
            regions__code__in=region_codes
        ).distinct().order_by('-published_at')
        
        if limit:
            articles_query = articles_query[:limit]
        
        articles = list(articles_query)
        article_ids = [article.id for article in articles]
        
        self.stdout.write(f"✅ Found {len(article_ids)} articles published on {target_date}")
        
        if not article_ids:
            self.stdout.write(self.style.WARNING("No articles found matching the criteria"))
            return
        
        # Show preview
        self.stdout.write(f"\n📰 Article Preview:")
        for i, article in enumerate(articles[:5], 1):
            regions = ', '.join([r.code for r in article.regions.all()])
            content_status = "✅ Has content" if article.raw_html and len(article.raw_html) > 1000 else "❌ No content"
            self.stdout.write(f"   {i}. ID:{article.id} - {article.title[:60]}... (Regions: {regions}) {content_status}")
        
        if len(articles) > 5:
            self.stdout.write(f"   ... and {len(articles) - 5} more articles")
        
        # Check content availability
        with_content = [a for a in articles if a.raw_html and len(a.raw_html) > min_html_length]
        self.stdout.write(f"\n📊 Content Analysis:")
        self.stdout.write(f"   📄 Total articles: {len(articles)}")
        self.stdout.write(f"   ✅ With content (>{min_html_length:,} chars): {len(with_content)}")
        self.stdout.write(f"   ❌ Without content: {len(articles) - len(with_content)}")
        
        if not with_content:
            self.stdout.write(self.style.WARNING("⚠️  No articles have sufficient content for processing"))
            return
        
        # Run the pipeline
        if dry_run:
            self.stdout.write(f"\n🧪 DRY RUN: Would process {len(with_content)} articles with {processor_type} processor")
        else:
            self.stdout.write(f"\n🚀 Running {processor_type.upper()} extraction pipeline for {len(with_content)} articles...")
            
            # Build article IDs string
            ids_str = ','.join(map(str, article_ids))
            
            # Call run_full_pipeline with specific IDs
            pipeline_args = [
                'run_full_pipeline',
                '--processor', processor_type,
                '--ids', ids_str,
                '--min-html-length', str(min_html_length)
            ]
            
            if force_process:
                pipeline_args.append('--force-process')
            if verbose:
                pipeline_args.append('--verbose')
            
            start_time = time.time()
            call_command(*pipeline_args)
            processing_time = time.time() - start_time
            
            self.stdout.write(f"\n✅ Pipeline completed in {processing_time:.1f}s")
        
        self.stdout.write("=" * 80) 