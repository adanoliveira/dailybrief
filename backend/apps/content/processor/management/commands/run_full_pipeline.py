"""
Django management command to run the complete content processing pipeline.
Step 1: Fetch content for articles
Step 2: Process with selected processor (algorithmic or AI)
"""
import time
from datetime import datetime
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import transaction
from io import StringIO
import sys

from apps.articles.models import Article


class Command(BaseCommand):
    help = 'Run the complete content processing pipeline: fetch → process (algorithmic or AI)'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--processor',
            choices=['algorithmic', 'ai'],
            default='algorithmic',
            help='Processor type to use: algorithmic (fast, rule-based) or ai (slower, LLM-based) (default: algorithmic)'
        )
        parser.add_argument(
            '--ids',
            type=str,
            help='Comma-separated list of article IDs to process (e.g., "123,456,789"). If provided, only these articles will be processed.'
        )
        parser.add_argument(
            '--fetch-limit',
            type=int,
            default=50,
            help='Number of articles to fetch content for (default: 50). Ignored if --ids is specified.'
        )
        parser.add_argument(
            '--process-limit',
            type=int,
            default=30,
            help='Number of articles to process (default: 30). Ignored if --ids is specified.'
        )
        parser.add_argument(
            '--fetch-status',
            choices=['pending', 'failed', 'all'],
            default='pending',
            help='Article fetch status to process (default: pending)'
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
            '--skip-fetch',
            action='store_true',
            help='Skip Step 1 (fetch) and only run Step 2 (process)'
        )
        parser.add_argument(
            '--skip-process',
            action='store_true',
            help='Skip Step 2 (process) and only run Step 1 (fetch)'
        )
    
    def handle(self, *args, **options):
        processor_type = options['processor']
        article_ids_str = options.get('ids')
        fetch_limit = options['fetch_limit']
        process_limit = options['process_limit']
        fetch_status = options['fetch_status']
        min_html_length = options['min_html_length']
        force_process = options['force_process']
        verbose = options['verbose']
        dry_run = options['dry_run']
        skip_fetch = options['skip_fetch']
        skip_process = options['skip_process']
        
        # Parse article IDs if provided
        article_ids = None
        if article_ids_str:
            try:
                article_ids = [int(id_str.strip()) for id_str in article_ids_str.split(',')]
                self.stdout.write(f"🎯 Processing specific article IDs: {article_ids}")
            except ValueError:
                self.stdout.write(
                    self.style.ERROR("❌ Invalid article IDs format. Use comma-separated integers (e.g., '123,456,789')")
                )
                return
        
        pipeline_start_time = time.time()
        
        # Pipeline header
        self.stdout.write("=" * 100)
        self.stdout.write(
            self.style.SUCCESS("🚀 DAILYBRIEF COMPLETE CONTENT PIPELINE")
        )
        self.stdout.write("=" * 100)
        self.stdout.write(f"⏰ Pipeline started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if dry_run:
            self.stdout.write(self.style.WARNING("🧪 DRY RUN MODE - No changes will be made"))
        
        self.stdout.write(f"📋 Configuration:")
        self.stdout.write(f"   • Processor: {processor_type.upper()}")
        if article_ids:
            self.stdout.write(f"   • Target articles: {len(article_ids)} specific IDs")
        else:
            self.stdout.write(f"   • Fetch limit: {fetch_limit} articles ({fetch_status} status)")
            self.stdout.write(f"   • Process limit: {process_limit} articles")
        self.stdout.write(f"   • Min HTML length: {min_html_length:,} chars")
        self.stdout.write(f"   • Force reprocess: {force_process}")
        
        if skip_fetch and skip_process:
            self.stdout.write(self.style.ERROR("❌ Cannot skip both fetch and process steps!"))
            return
        
        self.stdout.write("\n" + "=" * 100)
        
        # Step 1: Fetch Content
        if not skip_fetch:
            self.stdout.write(
                self.style.SUCCESS("📥 STEP 1: FETCHING CONTENT")
            )
            self.stdout.write("=" * 50)
            
            step1_start_time = time.time()
            
            try:
                # Get initial statistics
                initial_stats = self._get_content_stats(article_ids)
                self.stdout.write(f"📊 Before fetch: {initial_stats['with_content']} articles have content")
                
                if article_ids:
                    # Process specific articles
                    if dry_run:
                        self.stdout.write("🧪 DRY RUN: Would fetch content for specific articles")
                        self._show_specific_articles_info(article_ids, "fetch")
                    else:
                        self.stdout.write(f"🔄 Fetching content for {len(article_ids)} specific articles...")
                        self._fetch_specific_articles(article_ids, verbose)
                else:
                    # Use standard fetch command
                    if dry_run:
                        self.stdout.write("🧪 DRY RUN: Would run fetch_content command")
                        fetch_args = [
                            'fetch_content',
                            '--limit', str(fetch_limit),
                            '--status', fetch_status,
                            '--dry-run'
                        ]
                        call_command(*fetch_args)
                    else:
                        # Run fetch_content command
                        fetch_args = [
                            'fetch_content',
                            '--limit', str(fetch_limit),
                            '--status', fetch_status
                        ]
                        
                        if verbose:
                            fetch_args.append('-v')
                            fetch_args.append('2')
                        
                        self.stdout.write(f"🔄 Fetching content for {fetch_limit} {fetch_status} articles...")
                        call_command(*fetch_args)
                
                step1_time = time.time() - step1_start_time
                
                # Get post-fetch statistics
                post_fetch_stats = self._get_content_stats(article_ids)
                new_content = post_fetch_stats['with_content'] - initial_stats['with_content']
                
                self.stdout.write(
                    self.style.SUCCESS(f"✅ Step 1 completed in {step1_time:.1f}s")
                )
                self.stdout.write(f"📈 New articles with content: +{new_content}")
                self.stdout.write(f"📊 Total articles with content: {post_fetch_stats['with_content']}")
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"❌ Step 1 failed: {str(e)}")
                )
                if not skip_process:
                    self.stdout.write("⚠️  Continuing to Step 2 with existing content...")
        else:
            self.stdout.write(
                self.style.WARNING("⏭️  STEP 1: SKIPPED")
            )
        
        # Step 2: Content Processing
        if not skip_process:
            self.stdout.write("\n" + "=" * 50)
            processor_name = "AI PROCESSING" if processor_type == 'ai' else "ALGORITHMIC PROCESSING"
            processor_emoji = "🤖" if processor_type == 'ai' else "🧠"
            self.stdout.write(
                self.style.SUCCESS(f"{processor_emoji} STEP 2: {processor_name}")
            )
            self.stdout.write("=" * 50)
            
            step2_start_time = time.time()
            
            try:
                # Get processing statistics
                processing_stats = self._get_processing_stats(processor_type, article_ids)
                self.stdout.write(f"📊 Before processing: {processing_stats['unprocessed']} articles need processing")
                
                if article_ids:
                    # Process specific articles
                    processor_description = "AI extraction" if processor_type == 'ai' else "enhanced algorithmic processing"
                    if dry_run:
                        self.stdout.write(f"🧪 DRY RUN: Would process {len(article_ids)} specific articles with {processor_description}")
                        self._show_specific_articles_info(article_ids, "process")
                    else:
                        self.stdout.write(f"🔄 Processing {len(article_ids)} specific articles with {processor_description}...")
                        self._process_specific_articles(article_ids, processor_type, min_html_length, force_process, verbose)
                else:
                    # Use standard processing commands
                    # Run appropriate processing command based on processor type
                    if processor_type == 'ai':
                        process_args = [
                            'bulk_ai_process',
                            '--limit', str(process_limit),
                            '--min-html-length', str(min_html_length),
                            '--template', 'algorithmic_extraction_v3'
                        ]
                    else:  # algorithmic
                        process_args = [
                            'bulk_process_with_content',
                            '--limit', str(process_limit),
                            '--min-html-length', str(min_html_length)
                        ]
                    
                    if force_process:
                        process_args.append('--force')
                    if verbose:
                        process_args.append('--verbose')
                    if dry_run:
                        process_args.append('--dry-run')
                    
                    processor_description = "AI extraction" if processor_type == 'ai' else "enhanced algorithmic processing"
                    self.stdout.write(f"🔄 Processing {process_limit} articles with {processor_description}...")
                    call_command(*process_args)
                
                step2_time = time.time() - step2_start_time
                
                # Get post-processing statistics
                post_process_stats = self._get_processing_stats(processor_type, article_ids)
                newly_processed = processing_stats['unprocessed'] - post_process_stats['unprocessed']
                
                self.stdout.write(
                    self.style.SUCCESS(f"✅ Step 2 completed in {step2_time:.1f}s")
                )
                self.stdout.write(f"📈 Newly processed articles: +{newly_processed}")
                self.stdout.write(f"📊 Total processed articles: {post_process_stats['processed']}")
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"❌ Step 2 failed: {str(e)}")
                )
        else:
            self.stdout.write("\n" + "=" * 50)
            self.stdout.write(
                self.style.WARNING("⏭️  STEP 2: SKIPPED")
            )
        
        # Pipeline summary
        total_pipeline_time = time.time() - pipeline_start_time
        
        self.stdout.write("\n" + "=" * 100)
        self.stdout.write(
            self.style.SUCCESS("🎯 PIPELINE SUMMARY")
        )
        self.stdout.write("=" * 100)
        
        # Final statistics
        final_stats = self._get_pipeline_summary()
        
        self.stdout.write(f"📊 FINAL CONTENT STATISTICS:")
        self.stdout.write(f"   📰 Total articles: {final_stats['total']:,}")
        self.stdout.write(f"   📥 With raw content: {final_stats['with_content']:,}")
        self.stdout.write(f"   🧠 Processed articles: {final_stats['processed']:,}")
        self.stdout.write(f"   ⏳ Pending processing: {final_stats['unprocessed']:,}")
        
        if final_stats['processed'] > 0:
            coverage = (final_stats['processed'] / final_stats['total']) * 100
            processing_rate = (final_stats['processed'] / final_stats['with_content']) * 100 if final_stats['with_content'] > 0 else 0
            
            self.stdout.write(f"\n📈 PIPELINE PERFORMANCE:")
            self.stdout.write(f"   🎯 Overall coverage: {coverage:.1f}% of all articles")
            self.stdout.write(f"   ⚡ Processing rate: {processing_rate:.1f}% of articles with content")
        
        self.stdout.write(f"\n⏱️  Total pipeline time: {total_pipeline_time:.1f}s")
        
        # Quality insights
        if final_stats['recent_quality_samples']:
            self.stdout.write(f"\n🏆 RECENT QUALITY SAMPLES:")
            for i, sample in enumerate(final_stats['recent_quality_samples'][:3], 1):
                self.stdout.write(f"   {i}. {sample['title'][:50]}... (Q:{sample['quality']:.3f}, {sample['blocks']} blocks)")
        
        self.stdout.write(f"\n⏰ Pipeline completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.stdout.write("=" * 100)
    
    def _get_content_stats(self, article_ids=None):
        """Get statistics about articles with content."""
        if article_ids:
            # Filter by specific article IDs
            queryset = Article.objects.filter(id__in=article_ids)
            total_articles = queryset.count()
            with_content = queryset.filter(
                raw_html__isnull=False
            ).exclude(raw_html='').exclude(raw_html__exact='').count()
        else:
            # All articles
            total_articles = Article.objects.count()
            with_content = Article.objects.filter(
                raw_html__isnull=False
            ).exclude(raw_html='').exclude(raw_html__exact='').count()
        
        return {
            'total': total_articles,
            'with_content': with_content,
            'without_content': total_articles - with_content
        }
    
    def _get_processing_stats(self, processor_type='algorithmic', article_ids=None):
        """Get statistics about processed articles."""
        if article_ids:
            # Filter by specific article IDs
            with_content = Article.objects.filter(
                id__in=article_ids,
                raw_html__isnull=False
            ).exclude(raw_html='').exclude(raw_html__exact='').count()
            
            if processor_type == 'ai':
                # Count articles processed with AI (have extracted_metadata with ai_extraction=True)
                processed = Article.objects.filter(
                    id__in=article_ids,
                    extracted_metadata__ai_extraction=True,
                    process_status__in=['completed', 'processed']
                ).count()
            else:
                # Count articles processed algorithmically (have content_blocks but no AI extraction)
                processed = Article.objects.filter(
                    id__in=article_ids,
                    content_blocks__isnull=False,
                    process_status__in=['completed', 'processed']
                ).exclude(
                    extracted_metadata__ai_extraction=True
                ).count()
        else:
            # All articles
            with_content = Article.objects.filter(
                raw_html__isnull=False
            ).exclude(raw_html='').exclude(raw_html__exact='').count()
            
            if processor_type == 'ai':
                # Count articles processed with AI (have extracted_metadata with ai_extraction=True)
                processed = Article.objects.filter(
                    extracted_metadata__ai_extraction=True,
                    process_status__in=['completed', 'processed']
                ).count()
            else:
                # Count articles processed algorithmically (have content_blocks but no AI extraction)
                processed = Article.objects.filter(
                    content_blocks__isnull=False,
                    process_status__in=['completed', 'processed']
                ).exclude(
                    extracted_metadata__ai_extraction=True
                ).count()
        
        return {
            'with_content': with_content,
            'processed': processed,
            'unprocessed': with_content - processed
        }
    
    def _get_pipeline_summary(self):
        """Get comprehensive pipeline statistics."""
        total_articles = Article.objects.count()
        
        with_content = Article.objects.filter(
            raw_html__isnull=False
        ).exclude(raw_html='').exclude(raw_html__exact='').count()
        
        processed = Article.objects.filter(
            content_blocks__isnull=False,
            process_status='processed'
        ).count()
        
        # Get recent quality samples
        recent_processed = Article.objects.filter(
            content_blocks__isnull=False,
            process_status='processed',
            content_quality_metrics__isnull=False
        ).order_by('-updated_at')[:5]
        
        quality_samples = []
        for article in recent_processed:
            if article.content_quality_metrics and 'quality_score' in article.content_quality_metrics:
                quality_samples.append({
                    'title': article.title,
                    'quality': article.content_quality_metrics['quality_score'],
                    'blocks': len(article.content_blocks) if article.content_blocks else 0
                })
        
        return {
            'total': total_articles,
            'with_content': with_content,
            'processed': processed,
            'unprocessed': with_content - processed,
            'recent_quality_samples': quality_samples
        }
    
    def _show_specific_articles_info(self, article_ids, operation_type):
        """Show information about specific articles for dry run mode."""
        articles = Article.objects.filter(id__in=article_ids)
        
        self.stdout.write(f"📋 Articles that would be {operation_type}ed:")
        for article in articles:
            has_content = bool(article.raw_html and len(article.raw_html) > 1000)
            content_info = f"({len(article.raw_html):,} chars)" if article.raw_html else "(no content)"
            self.stdout.write(f"   • {article.id}: {article.title[:60]}... {content_info}")
    
    def _fetch_specific_articles(self, article_ids, verbose):
        """Fetch content for specific articles."""
        from apps.content.fetcher.fetcher import ContentFetcher
        
        articles = Article.objects.filter(id__in=article_ids)
        fetcher = ContentFetcher()
        
        success_count = 0
        for article in articles:
            if not article.needs_fetch:
                if verbose:
                    self.stdout.write(f"⏭️  {article.id}: Already has content, skipping fetch")
                continue
                
            if verbose:
                self.stdout.write(f"🔄 {article.id}: Fetching '{article.title[:50]}...'")
            
            try:
                result = fetcher.fetch_article_content(article)
                if result.success:
                    success_count += 1
                    if verbose:
                        self.stdout.write(f"   ✅ Success: {len(result.extraction_result.raw_html if result.extraction_result else ''):,} chars")
                else:
                    if verbose:
                        self.stdout.write(f"   ❌ Failed: {result.error_message}")
            except Exception as e:
                if verbose:
                    self.stdout.write(f"   ❌ Exception: {str(e)}")
        
        self.stdout.write(f"📊 Fetch complete: {success_count} articles fetched successfully")
    
    def _process_specific_articles(self, article_ids, processor_type, min_html_length, force_process, verbose):
        """Process specific articles with the chosen processor."""
        articles = Article.objects.filter(
            id__in=article_ids,
            raw_html__isnull=False
        ).exclude(raw_html='').exclude(raw_html__exact='')
        
        if processor_type == 'ai':
            self._ai_process_specific_articles(articles, min_html_length, force_process, verbose)
        else:
            self._algorithmic_process_specific_articles(articles, min_html_length, force_process, verbose)
    
    def _ai_process_specific_articles(self, articles, min_html_length, force_process, verbose):
        """Process specific articles with AI."""
        from apps.content.processor.ai_processor import AIContentProcessor
        
        ai_processor = AIContentProcessor()
        success_count = 0
        total_cost = 0.0
        
        for article in articles:
            # Check if content is long enough
            if len(article.raw_html) < min_html_length:
                if verbose:
                    self.stdout.write(f"⏭️  {article.id}: Content too short ({len(article.raw_html)} < {min_html_length})")
                continue
            
            # Check if already processed (unless force)
            has_ai = article.extracted_metadata and article.extracted_metadata.get('ai_extraction', False)
            if has_ai and not force_process:
                if verbose:
                    self.stdout.write(f"⏭️  {article.id}: Already AI processed")
                continue
            
            if verbose:
                self.stdout.write(f"🤖 {article.id}: AI processing '{article.title[:50]}...'")
            
            try:
                # Process the article with AI with enhanced logging
                if verbose:
                    self.stdout.write(f"      📝 HTML Length: {len(article.raw_html):,} chars")
                    self.stdout.write(f"      🔗 URL: {article.url}")
                
                result = ai_processor.process_content(
                    article.raw_html,
                    {
                        'title': article.title,
                        'url': article.url,
                        'source': article.source_name
                    },
                    base_url=article.url,
                    capture_raw_response=True  # Capture raw AI response for debugging
                )
                
                # Enhanced logging for debugging
                if verbose and hasattr(result, 'raw_response'):
                    # Save raw response to debug file for analysis
                    debug_filename = f"debug_ai_response_{article.id}_{int(time.time())}.json"
                    try:
                        import json
                        with open(f"/tmp/{debug_filename}", 'w') as f:
                            debug_data = {
                                'article_id': article.id,
                                'article_title': article.title,
                                'success': result.success,
                                'raw_response': result.raw_response,
                                'error_message': getattr(result, 'error_message', None),
                                'processing_time_ms': getattr(result, 'processing_time_ms', 0),
                                'content_blocks_count': len(result.content_blocks) if hasattr(result, 'content_blocks') and result.content_blocks else 0
                            }
                            json.dump(debug_data, f, indent=2)
                        self.stdout.write(f"      📄 Debug response saved: /tmp/{debug_filename}")
                    except Exception as debug_e:
                        self.stdout.write(f"      ⚠️  Could not save debug file: {debug_e}")
                
                if result.success:
                    success_count += 1
                    
                    # Save the results to the article
                    from apps.content.processor.models import serialize_content_blocks
                    
                    article.clean_content = result.clean_content
                    article.content_blocks = serialize_content_blocks(result.content_blocks)
                    
                    # Update with AI extraction metadata
                    if not article.extracted_metadata:
                        article.extracted_metadata = {}
                    
                    ai_metadata = result.extracted_metadata or {}
                    article.extracted_metadata.update({
                        'ai_extraction': True,
                        'template_used': 'algorithmic_extraction_v3',
                        'processing_time_ms': result.processing_time_ms,
                        'token_usage': ai_metadata.get('token_usage', 0),
                        'visual_title': ai_metadata.get('visual_title'),
                        'extraction_timestamp': time.time()
                    })
                    
                    article.process_status = 'completed'
                    article.process_route = 'llm_enhanced'
                    article.process_duration_ms = result.processing_time_ms
                    article.save()
                    
                    # Calculate cost estimate
                    tokens = ai_metadata.get('token_usage', 0)
                    cost = tokens * 0.00001  # Rough estimate
                    total_cost += cost
                    
                    if verbose:
                        visual_title = ai_metadata.get('visual_title', 'N/A')[:50]
                        self.stdout.write(f"   ✅ Success: ${cost:.4f}, {len(result.content_blocks)} blocks")
                        self.stdout.write(f"      📰 Visual Title: {visual_title}...")
                        self.stdout.write(f"      🏆 Quality Score: {result.quality_score:.3f}")
                else:
                    if verbose:
                        error_msg = result.error_message if hasattr(result, 'error_message') else 'Unknown error'
                        self.stdout.write(f"   ❌ Failed: {error_msg}")
                        
                        # Enhanced error debugging
                        if hasattr(result, 'extracted_metadata'):
                            token_usage = result.extracted_metadata.get('token_usage', 0) if result.extracted_metadata else 0
                            self.stdout.write(f"      🔍 Token Usage: {token_usage}")
                        
                        if hasattr(result, 'raw_response') and result.raw_response:
                            response_preview = str(result.raw_response)[:200].replace('\n', ' ')
                            self.stdout.write(f"      📝 Response Preview: {response_preview}...")
                            
            except Exception as e:
                if verbose:
                    self.stdout.write(f"   ❌ Exception: {str(e)}")
                    # Add stack trace for debugging
                    import traceback
                    stack_trace = traceback.format_exc()
                    self.stdout.write(f"      📋 Stack Trace: {stack_trace[-500:]}")  # Last 500 chars
        
        self.stdout.write(f"📊 AI processing complete: {success_count} articles processed, ${total_cost:.4f} total cost")
    
    def _algorithmic_process_specific_articles(self, articles, min_html_length, force_process, verbose):
        """Process specific articles with algorithmic processor."""
        from apps.content.processor.algorithmic_processor import AlgorithmicProcessor
        
        processor = AlgorithmicProcessor()
        success_count = 0
        
        for article in articles:
            # Check if content is long enough
            if len(article.raw_html) < min_html_length:
                if verbose:
                    self.stdout.write(f"⏭️  {article.id}: Content too short ({len(article.raw_html)} < {min_html_length})")
                continue
            
            # Check if already processed (unless force)
            has_processed = bool(article.content_blocks and article.process_status == 'processed')
            if has_processed and not force_process:
                if verbose:
                    self.stdout.write(f"⏭️  {article.id}: Already processed")
                continue
            
            if verbose:
                self.stdout.write(f"🧠 {article.id}: Algorithmic processing '{article.title[:50]}...'")
            
            try:
                if verbose:
                    self.stdout.write(f"      📝 HTML Length: {len(article.raw_html):,} chars")
                    self.stdout.write(f"      🔗 URL: {article.url}")
                
                result = processor.process_article(article)
                if result and result.get('success'):
                    success_count += 1
                    if verbose:
                        blocks = len(result.get('content_blocks', []))
                        quality = result.get('quality_score', 0.0)
                        self.stdout.write(f"   ✅ Success: {blocks} content blocks")
                        self.stdout.write(f"      🏆 Quality Score: {quality:.3f}")
                else:
                    if verbose:
                        error_msg = result.get('error', 'Unknown error') if result else 'No result'
                        self.stdout.write(f"   ❌ Failed: {error_msg}")
            except Exception as e:
                if verbose:
                    self.stdout.write(f"   ❌ Exception: {str(e)}")
                    # Add stack trace for debugging
                    import traceback
                    stack_trace = traceback.format_exc()
                    self.stdout.write(f"      📋 Stack Trace: {stack_trace[-500:]}")
        
        self.stdout.write(f"📊 Algorithmic processing complete: {success_count} articles processed")