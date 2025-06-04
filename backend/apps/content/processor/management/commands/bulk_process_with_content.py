"""
Django management command to bulk process articles that have HTML content.
Only processes articles with raw_html to avoid "Invalid HTML input" errors.
"""
import time
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.articles.models import Article
from apps.content.processor.algorithmic_processor import AlgorithmicProcessor
from ...models import serialize_content_blocks


class Command(BaseCommand):
    help = 'Bulk process articles that have HTML content with enhanced algorithmic processor'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=50,
            help='Number of articles with content to process (default: 50)'
        )
        parser.add_argument(
            '--force',
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
            help='Show what would be processed without actually processing'
        )
        parser.add_argument(
            '--min-html-length',
            type=int,
            default=100,
            help='Minimum HTML length to consider (default: 100)'
        )
    
    def handle(self, *args, **options):
        limit = options['limit']
        force = options['force']
        verbose = options['verbose']
        dry_run = options['dry_run']
        min_html_length = options['min_html_length']
        
        self.stdout.write(
            self.style.SUCCESS(f"🔄 Processing articles with HTML content (min length: {min_html_length})...")
        )
        self.stdout.write(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.stdout.write("=" * 80)
        
        # Get articles with HTML content only
        articles_with_content = list(
            Article.objects.filter(
                raw_html__isnull=False
            ).exclude(
                raw_html=''
            ).exclude(
                raw_html__exact=''
            ).extra(
                where=["CHAR_LENGTH(raw_html) > %s"],
                params=[min_html_length]
            ).order_by('-published_at')[:limit]
        )
        
        self.stdout.write(f"📰 Found {len(articles_with_content)} articles with HTML content")
        if articles_with_content:
            self.stdout.write(
                f"📅 Date range: {articles_with_content[-1].published_at.date()} to {articles_with_content[0].published_at.date()}"
            )
        
        # Show content statistics
        total_html_length = sum(len(art.raw_html) for art in articles_with_content)
        avg_html_length = total_html_length / len(articles_with_content) if articles_with_content else 0
        self.stdout.write(f"📊 Avg HTML length: {avg_html_length:.0f} chars")
        
        self.stdout.write("=" * 80)
        
        if dry_run:
            self.stdout.write(self.style.WARNING("🧪 DRY RUN MODE - No changes will be made"))
            self._show_dry_run_info(articles_with_content, force)
            return
        
        # Statistics tracking
        stats = {
            'total': len(articles_with_content),
            'processed': 0,
            'successful': 0,
            'failed': 0,
            'already_processed': 0,
            'total_time': 0,
            'successful_results': []
        }
        
        processor = AlgorithmicProcessor()
        
        for i, article in enumerate(articles_with_content, 1):
            article_start_time = time.time()
            
            if verbose:
                self.stdout.write(f"\n[{i:3d}/{len(articles_with_content)}] Processing: {article.title[:60]}...")
                self.stdout.write(f"                    Source: {article.source_name}")
                self.stdout.write(f"                    HTML: {len(article.raw_html):,} chars")
            else:
                # Simple progress indicator
                if i % 5 == 0:
                    self.stdout.write(f"Progress: {i}/{len(articles_with_content)} articles...")
            
            try:
                # Check if already processed with rich content
                if article.has_rich_content and article.content_blocks and not force:
                    if verbose:
                        self.stdout.write(
                            f"                    ⏭️  Already has rich content ({len(article.content_blocks)} blocks)"
                        )
                    stats['already_processed'] += 1
                    continue
                
                # Process the article
                result = processor.process_content(
                    article.raw_html,
                    {
                        'title': article.title,
                        'url': article.url,
                        'source': article.source_name
                    }
                )
                
                processing_time = time.time() - article_start_time
                stats['total_time'] += processing_time
                stats['processed'] += 1
                
                if result.success:
                    # Store the successful result
                    self.stdout.write(f"   ✅ Processing successful!")
                    
                    # Update article with the results
                    article.clean_content = result.clean_content
                    article.content_blocks = serialize_content_blocks(result.content_blocks)  # Use unified serialization
                        article.extracted_metadata = result.extracted_metadata
                    article.process_status = 'completed'
                    article.process_route = 'safari_mode'
                    article.process_duration_ms = result.processing_time_ms
                        article.save()
                    
                    stats['successful'] += 1
                    stats['successful_results'].append({
                        'id': article.id,
                        'title': article.title[:50],
                        'blocks': len(result.content_blocks),
                        'quality': result.quality_score,
                        'time_ms': int(processing_time * 1000),
                        'source': article.source_name
                    })
                    
                    if verbose:
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"                    ✅ Success: {result.quality_score:.3f} quality, "
                                f"{len(result.content_blocks)} blocks, {int(processing_time * 1000)}ms"
                            )
                        )
                else:
                    stats['failed'] += 1
                    error_msg = result.error_message[:50] if result.error_message else "Unknown error"
                    if verbose:
                        self.stdout.write(
                            self.style.ERROR(f"                    ❌ Failed: {error_msg}")
                        )
                    
            except Exception as e:
                stats['failed'] += 1
                processing_time = time.time() - article_start_time
                stats['total_time'] += processing_time
                error_msg = str(e)[:50]
                if verbose:
                    self.stdout.write(
                        self.style.ERROR(f"                    💥 Exception: {error_msg}")
                    )
                # Log full exception for debugging
                self.stderr.write(f"Exception processing article {article.id}: {str(e)}")
        
        # Final results
        self._show_final_results(stats)
    
    def _show_dry_run_info(self, articles, force):
        """Show what would be processed in dry-run mode."""
        to_process = []
        already_processed = []
        
        for article in articles:
            if article.has_rich_content and article.content_blocks and not force:
                already_processed.append(article)
            else:
                to_process.append(article)
        
        self.stdout.write(f"📊 DRY RUN ANALYSIS:")
        self.stdout.write(f"  🔄 Would process: {len(to_process)} articles")
        self.stdout.write(f"  ⏭️  Already processed: {len(already_processed)} articles")
        
        if to_process:
            self.stdout.write(f"\n📋 Sample articles to process:")
            for i, article in enumerate(to_process[:5], 1):
                html_size = f"{len(article.raw_html):,}" if article.raw_html else "0"
                self.stdout.write(f"  {i}. {article.title[:50]}... ({article.source_name}) [{html_size} chars]")
            if len(to_process) > 5:
                self.stdout.write(f"  ... and {len(to_process) - 5} more")
    
    def _show_final_results(self, stats):
        """Display final processing results."""
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write(self.style.SUCCESS("📊 ENHANCED ALGORITHMIC PROCESSING RESULTS"))
        self.stdout.write("=" * 80)
        self.stdout.write(f"📰 Total articles: {stats['total']}")
        self.stdout.write(f"🔄 Processed: {stats['processed']}")
        self.stdout.write(
            self.style.SUCCESS(f"✅ Successful: {stats['successful']}")
        )
        if stats['failed'] > 0:
            self.stdout.write(
                self.style.ERROR(f"❌ Failed: {stats['failed']}")
            )
        else:
            self.stdout.write(f"❌ Failed: {stats['failed']}")
        self.stdout.write(f"⏭️  Already processed: {stats['already_processed']}")
        self.stdout.write(f"⏱️  Total time: {stats['total_time']:.1f}s")
        
        if stats['processed'] > 0:
            success_rate = (stats['successful'] / stats['processed']) * 100
            avg_time = stats['total_time'] / stats['processed']
            
            self.stdout.write(
                self.style.SUCCESS(f"📈 Success rate: {success_rate:.1f}%")
            )
            self.stdout.write(f"⚡ Avg time/article: {avg_time:.2f}s")
        
        if stats['successful_results']:
            self.stdout.write(f"\n🏆 TOP RESULTS BY QUALITY:")
            top_results = sorted(stats['successful_results'], key=lambda x: x['quality'], reverse=True)
            for i, result in enumerate(top_results, 1):
                quality_color = self.style.SUCCESS if result['quality'] >= 0.8 else self.style.WARNING
                quality_text = f"Q:{result['quality']:.3f}"
                self.stdout.write(
                    f"  {i:2d}. {result['title']}... "
                    f"({quality_color(quality_text)}, {result['blocks']} blocks, {result['source']})"
                )
        
        self.stdout.write(f"\n⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.stdout.write("=" * 80) 