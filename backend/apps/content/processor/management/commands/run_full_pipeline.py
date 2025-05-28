"""
Django management command to run the complete content processing pipeline.
Step 1: Fetch content for articles
Step 2: Process with enhanced algorithmic processor
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
    help = 'Run the complete content processing pipeline: fetch → process'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--fetch-limit',
            type=int,
            default=50,
            help='Number of articles to fetch content for (default: 50)'
        )
        parser.add_argument(
            '--process-limit',
            type=int,
            default=30,
            help='Number of articles to process (default: 30)'
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
        fetch_limit = options['fetch_limit']
        process_limit = options['process_limit']
        fetch_status = options['fetch_status']
        min_html_length = options['min_html_length']
        force_process = options['force_process']
        verbose = options['verbose']
        dry_run = options['dry_run']
        skip_fetch = options['skip_fetch']
        skip_process = options['skip_process']
        
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
                initial_stats = self._get_content_stats()
                self.stdout.write(f"📊 Before fetch: {initial_stats['with_content']} articles have content")
                
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
                post_fetch_stats = self._get_content_stats()
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
        
        # Step 2: Enhanced Processing
        if not skip_process:
            self.stdout.write("\n" + "=" * 50)
            self.stdout.write(
                self.style.SUCCESS("🧠 STEP 2: ENHANCED ALGORITHMIC PROCESSING")
            )
            self.stdout.write("=" * 50)
            
            step2_start_time = time.time()
            
            try:
                # Get processing statistics
                processing_stats = self._get_processing_stats()
                self.stdout.write(f"📊 Before processing: {processing_stats['unprocessed']} articles need processing")
                
                # Run bulk_process_with_content command
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
                
                self.stdout.write(f"🔄 Processing {process_limit} articles with enhanced algorithm...")
                call_command(*process_args)
                
                step2_time = time.time() - step2_start_time
                
                # Get post-processing statistics
                post_process_stats = self._get_processing_stats()
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
    
    def _get_content_stats(self):
        """Get statistics about articles with content."""
        total_articles = Article.objects.count()
        with_content = Article.objects.filter(
            raw_html__isnull=False
        ).exclude(raw_html='').exclude(raw_html__exact='').count()
        
        return {
            'total': total_articles,
            'with_content': with_content,
            'without_content': total_articles - with_content
        }
    
    def _get_processing_stats(self):
        """Get statistics about processed articles."""
        with_content = Article.objects.filter(
            raw_html__isnull=False
        ).exclude(raw_html='').exclude(raw_html__exact='').count()
        
        processed = Article.objects.filter(
            content_blocks__isnull=False,
            process_status='processed'
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