"""
Django management command to bulk process articles with AI extraction.
Only processes articles with raw_html to avoid "Invalid HTML input" errors.
"""
import time
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.articles.models import Article
from apps.content.processor.ai_processor import AIContentProcessor
from ...models import serialize_content_blocks


class Command(BaseCommand):
    help = 'Bulk process articles that have HTML content with AI extraction'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=50,
            help='Number of articles with content to process (default: 50)'
        )
        parser.add_argument(
            '--template',
            type=str,
            default='algorithmic_extraction_v3',
            help='AI template to use for extraction (default: algorithmic_extraction_v3)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Reprocess articles that already have AI extraction'
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
            default=1000,
            help='Minimum HTML length to consider (default: 1000)'
        )
    
    def handle(self, *args, **options):
        limit = options['limit']
        template = options['template']
        force = options['force']
        verbose = options['verbose']
        dry_run = options['dry_run']
        min_html_length = options['min_html_length']
        
        self.stdout.write(
            self.style.SUCCESS(f"🤖 AI Processing articles with HTML content (min length: {min_html_length})...")
        )
        self.stdout.write(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.stdout.write(f"🎯 Template: {template}")
        self.stdout.write("=" * 80)
        
        # Get articles with HTML content, excluding those already processed with AI (unless force)
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
        
        # Exclude already AI-processed articles unless force
        if not force:
            articles_query = articles_query.exclude(
                extracted_metadata__ai_extraction=True
            )
        
        articles_with_content = list(
            articles_query.order_by('-published_at')[:limit]
        )
        
        self.stdout.write(f"📰 Found {len(articles_with_content)} articles for AI processing")
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
            'total_tokens': 0,
            'total_cost': 0.0,
            'successful_results': []
        }
        
        processor = AIContentProcessor(template)
        
        for i, article in enumerate(articles_with_content, 1):
            article_start_time = time.time()
            
            if verbose:
                self.stdout.write(f"\n[{i:3d}/{len(articles_with_content)}] AI Processing: {article.title[:60]}...")
                self.stdout.write(f"                    Source: {article.source_name}")
                self.stdout.write(f"                    HTML: {len(article.raw_html):,} chars")
            else:
                # Simple progress indicator
                if i % 2 == 0:  # Show progress more frequently for AI (slower)
                    self.stdout.write(f"Progress: {i}/{len(articles_with_content)} articles...")
            
            try:
                # Check if already processed with AI
                has_ai_extraction = (
                    article.extracted_metadata and 
                    article.extracted_metadata.get('ai_extraction', False)
                )
                
                if has_ai_extraction and not force:
                    if verbose:
                        self.stdout.write(
                            f"                    ⏭️  Already has AI extraction"
                        )
                    stats['already_processed'] += 1
                    continue
                
                # Process the article with AI
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
                
                # Track token usage and cost
                if result.extracted_metadata:
                    token_usage = result.extracted_metadata.get('token_usage', 0)
                    stats['total_tokens'] += token_usage
                    
                    # Estimate cost (rough estimate for GPT-4)
                    estimated_cost = token_usage * 0.00001  # ~$0.01 per 1K tokens
                    stats['total_cost'] += estimated_cost
                
                if result.success:
                    # Store the successful result
                    if verbose:
                        self.stdout.write(f"                    ✅ AI processing successful!")
                    
                    # Update article with the results including AI metadata
                    article.clean_content = result.clean_content
                    article.content_blocks = serialize_content_blocks(result.content_blocks)
                    
                    # Merge AI metadata with existing metadata
                    if not article.extracted_metadata:
                        article.extracted_metadata = {}
                    
                    # Update with AI extraction metadata
                    ai_metadata = result.extracted_metadata or {}
                    article.extracted_metadata.update({
                        'ai_extraction': True,
                        'template_used': template,
                        'processing_time_ms': result.processing_time_ms,
                        'token_usage': ai_metadata.get('token_usage', 0),
                        'provider': ai_metadata.get('provider', 'unknown'),
                        'model': ai_metadata.get('model', 'unknown'),
                        'extraction_timestamp': datetime.now().isoformat(),
                        'visual_title': ai_metadata.get('visual_title'),
                        'content_types': ai_metadata.get('content_types', {}),
                        'author_information': ai_metadata.get('author_information', {}),
                        'extraction_feedback': ai_metadata.get('extraction_feedback', {}),
                    })
                    
                    article.process_status = 'completed'
                    article.process_route = 'llm_enhanced'
                    article.process_duration_ms = result.processing_time_ms
                    
                    # Update rich content flags
                    article.update_rich_content_metadata()
                    
                    article.save()
                    
                    stats['successful'] += 1
                    stats['successful_results'].append({
                        'id': article.id,
                        'title': article.title[:50],
                        'blocks': len(result.content_blocks),
                        'quality': result.quality_score,
                        'time_ms': int(processing_time * 1000),
                        'tokens': ai_metadata.get('token_usage', 0),
                        'source': article.source_name
                    })
                    
                    if verbose:
                        tokens = ai_metadata.get('token_usage', 0)
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"                    ✅ Success: {result.quality_score:.3f} quality, "
                                f"{len(result.content_blocks)} blocks, {int(processing_time * 1000)}ms, {tokens} tokens"
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
            has_ai_extraction = (
                article.extracted_metadata and 
                article.extracted_metadata.get('ai_extraction', False)
            )
            
            if has_ai_extraction and not force:
                already_processed.append(article)
            else:
                to_process.append(article)
        
        self.stdout.write(f"\n📋 Dry Run Analysis:")
        self.stdout.write(f"   🆕 To process: {len(to_process)} articles")
        self.stdout.write(f"   ✅ Already processed: {len(already_processed)} articles")
        
        if to_process:
            self.stdout.write(f"\n🔍 Sample articles to process:")
            for article in to_process[:5]:
                html_len = len(article.raw_html) if article.raw_html else 0
                self.stdout.write(f"   • {article.title[:60]}... ({html_len:,} chars)")
        
        if already_processed and not force:
            self.stdout.write(f"\n⏭️  Use --force to reprocess {len(already_processed)} already processed articles")
    
    def _show_final_results(self, stats):
        """Show comprehensive processing results."""
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write(self.style.SUCCESS("🎯 AI PROCESSING RESULTS"))
        self.stdout.write("=" * 80)
        
        # Basic statistics
        self.stdout.write(f"📊 Processing Summary:")
        self.stdout.write(f"   📰 Total articles: {stats['total']}")
        self.stdout.write(f"   🔄 Attempted: {stats['processed']}")
        self.stdout.write(f"   ✅ Successful: {stats['successful']}")
        self.stdout.write(f"   ❌ Failed: {stats['failed']}")
        self.stdout.write(f"   ⏭️  Already processed: {stats['already_processed']}")
        
        # Performance metrics
        if stats['total_time'] > 0:
            avg_time = stats['total_time'] / max(stats['processed'], 1)
            self.stdout.write(f"\n⏱️  Performance:")
            self.stdout.write(f"   Total time: {stats['total_time']:.1f}s")
            self.stdout.write(f"   Avg per article: {avg_time:.1f}s")
        
        # AI-specific metrics
        if stats['total_tokens'] > 0:
            self.stdout.write(f"\n🤖 AI Metrics:")
            self.stdout.write(f"   Total tokens: {stats['total_tokens']:,}")
            self.stdout.write(f"   Estimated cost: ${stats['total_cost']:.3f}")
            if stats['successful'] > 0:
                avg_tokens = stats['total_tokens'] / stats['successful']
                avg_cost = stats['total_cost'] / stats['successful']
                self.stdout.write(f"   Avg tokens per article: {avg_tokens:.0f}")
                self.stdout.write(f"   Avg cost per article: ${avg_cost:.3f}")
        
        # Success rate
        if stats['processed'] > 0:
            success_rate = (stats['successful'] / stats['processed']) * 100
            self.stdout.write(f"\n📈 Success Rate: {success_rate:.1f}%")
        
        # Sample successful results
        if stats['successful_results']:
            self.stdout.write(f"\n🏆 Sample Successful Results:")
            for i, result in enumerate(stats['successful_results'][:3], 1):
                self.stdout.write(
                    f"   {i}. {result['title']}... "
                    f"(Q:{result['quality']:.3f}, {result['blocks']}b, {result['time_ms']}ms, {result['tokens']}t)"
                )
        
        self.stdout.write(f"\n⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.stdout.write("=" * 80) 