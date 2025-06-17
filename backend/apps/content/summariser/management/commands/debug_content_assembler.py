#!/usr/bin/env python3
"""
Content Assembler Debug Management Command for DailyBrief

Examines the content assembly process for specific articles to evaluate
the quality of assembled content that gets fed to summarization prompts.

Usage:
    python manage.py debug_content_assembler [article_ids...]
    
    If no article IDs provided, uses default test batch:
    15158 20894 20863 20149 20103 20666 20917 20869 15157
"""

from django.core.management.base import BaseCommand
from typing import List, Optional

from apps.articles.models import Article
from apps.content.summariser.content_assembler import MarkdownContentAssembler, get_markdown_assembler


class Command(BaseCommand):
    help = 'Debug content assembly process for articles'

    def add_arguments(self, parser):
        parser.add_argument(
            'article_ids',
            nargs='*',
            type=int,
            help='Article IDs to debug (if none provided, uses default test batch)'
        )
        parser.add_argument(
            '--max-chars',
            type=int,
            default=25000,
            help='Maximum characters for content assembly (default: 25000)'
        )
        parser.add_argument(
            '--detailed',
            action='store_true',
            help='Show detailed analysis of content assembly'
        )
        parser.add_argument(
            '--show-scoring',
            action='store_true',
            help='Show detailed scoring breakdown for all content blocks'
        )
        parser.add_argument(
            '--mode',
            type=str,
            choices=['hybrid', 'intelligent', 'custom'],
            help='Force a specific summarization mode (hybrid, intelligent, or custom)'
        )

    def handle(self, *args, **options):
        # Default test batch
        default_article_ids = [15158, 20894, 20863, 20149, 20103, 20666, 20917, 20869, 15157]
        
        article_ids = options['article_ids']
        if not article_ids:
            article_ids = default_article_ids
            self.stdout.write(f"🔍 Using default test batch: {article_ids}")
        
        # Remove duplicates while preserving order
        unique_article_ids = []
        for aid in article_ids:
            if aid not in unique_article_ids:
                unique_article_ids.append(aid)
        article_ids = unique_article_ids
        
        self.stdout.write(self.style.SUCCESS(f"\n🚀 Debugging content assembly for {len(article_ids)} articles"))

        # Test all three summarization approaches or just the specified mode
        if options['mode']:
            approaches = [
                (f"Selected Mode: {options['mode'].capitalize()}", True, options['mode'])
            ]
            self.stdout.write(f"\n🔧 Using specified summarization mode: {options['mode']}")
        else:
            approaches = [
                ("Hybrid Summarization (Gensim + Structure)", True, "hybrid"),
                ("Pure Intelligent Summarization (Gensim)", True, "intelligent"), 
                ("Custom Truncation", False, "custom")
            ]
        
        for approach_name, use_intelligent, mode in approaches:
            self.stdout.write(f"\n{'='*100}")
            self.stdout.write(f"TESTING: {approach_name}")
            self.stdout.write(f"{'='*100}")
            
            self._test_summarization_approach(article_ids, options['max_chars'], options['detailed'], options['show_scoring'], use_intelligent, mode)

    def _test_summarization_approach(self, article_ids: List[int], max_chars: int, detailed: bool, show_scoring: bool, use_intelligent: bool, mode: str):
        """Test a specific summarization approach."""
        from ...content_assembler import get_markdown_assembler

        # Create assembler with specified approach
        assembler = get_markdown_assembler(
            max_chars=max_chars, 
            use_intelligent_summarization=use_intelligent,
            summarization_mode=mode
        )
        
        # Print assembler configuration
        self.stdout.write(f"\n📋 Assembler Configuration:")
        self.stdout.write(f"  Max Characters: {max_chars}")
        self.stdout.write(f"  Using Intelligent Summarization: {use_intelligent}")
        self.stdout.write(f"  Summarization Mode: {mode}")
        self.stdout.write(f"  Gensim Available: {getattr(assembler, 'GENSIM_AVAILABLE', False)}")
        self.stdout.write(f"  Actual Mode Used: {assembler.summarization_mode}")
        
        comparison_data = []
        
        for article_id in article_ids:
            try:
                article = Article.objects.get(id=article_id)
                original_chars = len(str(article.content_blocks or []))
                
                self.stdout.write(f"\n\n{'='*50}")
                self.stdout.write(f"ARTICLE {article_id}: {article.title[:60]}")
                self.stdout.write(f"{'='*50}")
                
                # Print original content blocks summary
                self.print_content_blocks_summary(article.content_blocks or [])
                
                # Assemble content
                assembled = assembler.assemble_content(article.content_blocks or [], title=article.title)
                assembled_chars = len(assembled)
                
                # Print the full assembled content for inspection
                self.stdout.write("\n==== FULL ASSEMBLED CONTENT ====")
                self.stdout.write(assembled)
                self.stdout.write("==== END OF ASSEMBLED CONTENT ====")
                
                # Count words and analyze
                word_count = len(assembled.split())
                truncated = assembled_chars < original_chars
                
                comparison_data.append({
                    'id': article_id,
                    'blocks': len(article.content_blocks or []),
                    'original': f"{original_chars:,}",
                    'assembled': f"{assembled_chars:,}",
                    'words': word_count,
                    'truncated': 'YES' if truncated else 'NO',
                    'title': article.title[:60] + "..." if len(article.title) > 60 else article.title
                })
                
                if detailed:
                    self._show_detailed_analysis(article, assembled, assembled_chars)
                    
                if show_scoring and mode == "hybrid":
                    self._show_scoring_analysis(article, assembler, max_chars)
                    
            except Article.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Article {article_id} not found"))
                continue
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error processing article {article_id}: {e}"))
                continue
        
        # Show summary table
        if comparison_data:
            self._show_comparison_table(comparison_data)

    def _show_comparison_table(self, comparison_data):
        """Display a comparison table of the results."""
        self.stdout.write("\n📊 CONTENT ASSEMBLY COMPARISON")
        self.stdout.write("    ID Blocks   Original  Assembled   Words Trunc Title")
        self.stdout.write("─" * 100)
        
        for result in comparison_data:
            truncated_indicator = "🔄" if result['truncated'] == 'YES' else " "
            self.stdout.write(
                f" {result['id']:>5} {result['blocks']:>6}   {result['original']:>8}   {result['assembled']:>8} "
                f"{result['words']:>7} {result['truncated']:>5} {result['title']}")

    def print_separator(self, title: str, char: str = "=", width: int = 80):
        """Print a formatted separator with title."""
        padding = (width - len(title) - 2) // 2
        self.stdout.write(f"\n{char * padding} {title} {char * padding}")

    def print_content_blocks_summary(self, content_blocks: List[dict]):
        """Print a summary of content blocks structure."""
        if not content_blocks:
            self.stdout.write("❌ No content blocks found")
            return
        
        self.stdout.write(f"📦 Content Blocks Summary ({len(content_blocks)} blocks):")
        
        block_types = {}
        total_chars = 0
        
        for i, block in enumerate(content_blocks, 1):
            block_type = block.get('type', 'unknown')
            content = block.get('content', '')
            char_count = len(content)
            
            # Count by type
            if block_type not in block_types:
                block_types[block_type] = {'count': 0, 'chars': 0}
            block_types[block_type]['count'] += 1
            block_types[block_type]['chars'] += char_count
            total_chars += char_count
            
            # Show first few blocks in detail
            if i <= 5:
                preview = content[:100].replace('\n', ' ').strip()
                if len(content) > 100:
                    preview += "..."
                self.stdout.write(f"  {i:2d}. {block_type:12s} ({char_count:4d} chars): {preview}")
        
        if len(content_blocks) > 5:
            self.stdout.write(f"     ... and {len(content_blocks) - 5} more blocks")
        
        self.stdout.write(f"\n📊 Block Type Distribution:")
        for block_type, stats in sorted(block_types.items()):
            self.stdout.write(f"  {block_type:15s}: {stats['count']:2d} blocks, {stats['chars']:6d} chars")
        
        self.stdout.write(f"\n📏 Total original content: {total_chars:,} characters")

    def analyze_assembled_content(self, assembled_content: str):
        """Analyze the quality and structure of assembled content."""
        if not assembled_content:
            self.stdout.write("❌ No assembled content")
            return
        
        lines = assembled_content.split('\n')
        char_count = len(assembled_content)
        word_count = len(assembled_content.split())
        
        # Count markdown elements
        headers = len([line for line in lines if line.startswith('#')])
        quotes = len([line for line in lines if line.startswith('>')])
        lists = len([line for line in lines if line.strip().startswith(('- ', '* ', '1. ', '2. '))])
        images = len([line for line in lines if '*[Image:' in line])
        
        self.stdout.write(f"📊 Assembled Content Analysis:")
        self.stdout.write(f"  Length: {char_count:,} characters, {word_count:,} words")
        self.stdout.write(f"  Lines: {len(lines)}")
        self.stdout.write(f"  Headers: {headers}")
        self.stdout.write(f"  Quotes: {quotes}")
        self.stdout.write(f"  List items: {lists}")
        self.stdout.write(f"  Images: {images}")
        
        # Check for truncation
        if '...' in assembled_content or '[...]' in assembled_content:
            self.stdout.write(f"  ⚠️  Content appears to be truncated")
        
        # Estimate reading time
        reading_time = word_count / 200  # Average 200 WPM
        self.stdout.write(f"  📖 Estimated reading time: {reading_time:.1f} minutes")

    def debug_article_content_assembly(self, article_id: int):
        """Debug content assembly for a specific article."""
        self.print_separator(f"ARTICLE {article_id}", "=", 100)
        
        try:
            article = Article.objects.get(id=article_id)
        except Article.DoesNotExist:
            self.stdout.write(f"❌ Article {article_id} not found")
            return
        
        # Article metadata
        self.stdout.write(f"📰 Title: {article.title}")
        self.stdout.write(f"🗓️  Published: {article.published_at}")
        self.stdout.write(f"🌐 Source: {article.source_name or 'Unknown'}")
        self.stdout.write(f"🔗 URL: {article.url}")
        
        # Get content blocks
        content_blocks = article.content_blocks or []
        
        if not content_blocks:
            self.stdout.write("\n❌ No content blocks available")
            
            # Try fallback content
            self.stdout.write("\n🔄 Checking fallback content sources:")
            if article.cleaned_text:
                self.stdout.write(f"  ✅ Cleaned text available: {len(article.cleaned_text):,} chars")
            else:
                self.stdout.write(f"  ❌ No cleaned text")
                
            if article.incomplete_text:
                self.stdout.write(f"  ✅ Incomplete text available: {len(article.incomplete_text):,} chars")
            else:
                self.stdout.write(f"  ❌ No incomplete text")
            
            return
        
        self.print_content_blocks_summary(content_blocks)
        
        # Test with different limits to show scaling
        limits = [10000, 25000, 50000]
        self.stdout.write(f"\n📊 Testing different character limits:")
        original_chars = sum(len(block.get('content', '')) for block in content_blocks)
        
        for limit in limits:
            assembler = get_markdown_assembler(max_chars=limit)
            assembled_content = assembler.assemble_content(content_blocks, title=article.title)
            truncated = len(assembled_content) < original_chars
            
            self.stdout.write(f"  • {limit:,} chars: {len(assembled_content):,} chars, {len(assembled_content.split()):,} words {'✂️ truncated' if truncated else '✓ full'}")
        
        # Show content samples at target limit
        assembler = get_markdown_assembler(max_chars=25000)
        assembled_content = assembler.assemble_content(content_blocks, title=article.title)
        
        self.analyze_assembled_content(assembled_content)
        
        self.stdout.write(f"\n📝 First 2,000 characters of assembled content:")
        self.stdout.write("─" * 80)
        self.stdout.write(assembled_content[:2000])
        if len(assembled_content) > 2000:
            self.stdout.write("...")
        self.stdout.write("─" * 80)
        
        self.stdout.write(f"\n📝 Last 2,000 characters of assembled content:")
        self.stdout.write("─" * 80)
        if len(assembled_content) > 2000:
            self.stdout.write("..." + assembled_content[-2000:])
        else:
            self.stdout.write(assembled_content)
        self.stdout.write("─" * 80)

    def debug_content_assembly_comparison(self, article_ids: List[int], max_chars: int = 25000):
        """Compare content assembly across multiple articles."""
        self.print_separator("CONTENT ASSEMBLY COMPARISON", "=", 100)
        
        results = []
        
        for article_id in article_ids:
            try:
                article = Article.objects.get(id=article_id)
                content_blocks = article.content_blocks or []
                
                if content_blocks:
                    assembler = get_markdown_assembler(max_chars=max_chars)
                    assembled_content = assembler.assemble_content(content_blocks, title=article.title)
                    
                    results.append({
                        'id': article_id,
                        'title': article.title[:50] + "..." if len(article.title) > 50 else article.title,
                        'blocks': len(content_blocks),
                        'original_chars': sum(len(block.get('content', '')) for block in content_blocks),
                        'assembled_chars': len(assembled_content),
                        'assembled_words': len(assembled_content.split()),
                        'truncated': '...' in assembled_content or '[...]' in assembled_content
                    })
                else:
                    results.append({
                        'id': article_id,
                        'title': article.title[:50] + "..." if len(article.title) > 50 else article.title,
                        'blocks': 0,
                        'original_chars': 0,
                        'assembled_chars': 0,
                        'assembled_words': 0,
                        'truncated': False
                    })
            except Article.DoesNotExist:
                results.append({
                    'id': article_id,
                    'title': 'NOT FOUND',
                    'blocks': 0,
                    'original_chars': 0,
                    'assembled_chars': 0,
                    'assembled_words': 0,
                    'truncated': False
                })
        
        self.stdout.write(f"{'ID':>6} {'Blocks':>6} {'Original':>10} {'Assembled':>10} {'Words':>7} {'Trunc':>5} Title")
        self.stdout.write("─" * 100)
        
        for result in results:
            truncated_indicator = "YES" if result['truncated'] else "NO"
            self.stdout.write(f"{result['id']:>6} {result['blocks']:>6} {result['original_chars']:>10,} "
                            f"{result['assembled_chars']:>10,} {result['assembled_words']:>7,} {truncated_indicator:>5} "
                            f"{result['title']}")

    def _show_detailed_analysis(self, article, assembled, assembled_chars):
        """Show detailed analysis for a specific article."""
        self.print_separator(f"ARTICLE {article.id}", "=", 100)
        self.print_content_blocks_summary(article.content_blocks or [])
        self.analyze_assembled_content(assembled)
        self.print_separator(f"ASSEMBLED CONTENT ({assembled_chars} chars)", "-", 100)
        self.stdout.write(assembled)
        self.print_separator("ANALYSIS COMPLETE", "=", 100)

        self.stdout.write("💡 Tips for evaluation:")
        self.stdout.write("  • Check if important content (headlines, quotes, facts) is preserved")
        self.stdout.write("  • Verify markdown formatting is clean and readable")
        self.stdout.write("  • Ensure truncation (if any) preserves the most informative parts")
        self.stdout.write("  • Look for proper semantic structure (headers, lists, quotes)")

    def _show_scoring_analysis(self, article, assembler, max_chars):
        """Show detailed scoring analysis for a specific article."""
        self.stdout.write(f"\n{'='*100}")
        self.stdout.write(f"📊 SCORING ANALYSIS FOR ARTICLE {article.id}")
        self.stdout.write(f"{'='*100}")
        
        # Get scoring analysis data
        analysis = assembler.get_scoring_analysis(article.content_blocks or [], max_chars)
        
        if "error" in analysis:
            self.stdout.write(self.style.ERROR(f"Analysis error: {analysis['error']}"))
            return
        
        # Overall statistics
        quality = analysis['selection_quality']
        self.stdout.write(f"📊 SELECTION QUALITY METRICS:")
        self.stdout.write(f"  Total blocks: {analysis['total_blocks']}")
        self.stdout.write(f"  Selected: {analysis['selected_count']} blocks")
        self.stdout.write(f"  Excluded: {analysis['excluded_count']} blocks")
        self.stdout.write(f"  Average selected score: {quality['avg_selected_score']:.2f}")
        self.stdout.write(f"  Average excluded score: {quality['avg_excluded_score']:.2f}")
        self.stdout.write(f"  Lowest selected score: {quality['lowest_selected_score']:.2f}")
        self.stdout.write(f"  Highest excluded score: {quality['highest_excluded_score']:.2f}")
        
        # Quality check
        if quality['lowest_selected_score'] >= quality['highest_excluded_score']:
            self.stdout.write(self.style.SUCCESS("  ✅ PERFECT SELECTION: All selected blocks scored higher than all excluded blocks"))
        elif quality['avg_selected_score'] > quality['avg_excluded_score']:
            self.stdout.write(self.style.WARNING("  ⚠️  GOOD SELECTION: Selected blocks scored higher on average"))
        else:
            self.stdout.write(self.style.ERROR("  ❌ POOR SELECTION: Some high-scoring blocks were excluded"))
        
        # Show top excluded blocks (should be least relevant)
        self.stdout.write(f"\n🗑️  TOP 10 EXCLUDED BLOCKS (should be least relevant):")
        for i, block in enumerate(analysis['excluded_blocks'][:10]):
            content_preview = block['content_preview'].replace('\n', ' ')[:80]
            self.stdout.write(f"  {i+1:2d}. Score: {block['final_score']:5.2f} | Type: {block['type']:10s} | {content_preview}")
        
        # Show bottom selected blocks (should still be more relevant than excluded)
        self.stdout.write(f"\n✅ BOTTOM 10 SELECTED BLOCKS (should still be more relevant):")
        selected_bottom = sorted(analysis['selected_blocks'], key=lambda x: x['final_score'])[:10]
        for i, block in enumerate(selected_bottom):
            content_preview = block['content_preview'].replace('\n', ' ')[:80]
            self.stdout.write(f"  {i+1:2d}. Score: {block['final_score']:5.2f} | Type: {block['type']:10s} | {content_preview}")
        
        # Show score distribution
        self.stdout.write(f"\n📈 SCORE DISTRIBUTION:")
        all_scores = [b['final_score'] for b in analysis['selected_blocks'] + analysis['excluded_blocks']]
        if all_scores:
            min_score = min(all_scores)
            max_score = max(all_scores)
            self.stdout.write(f"  Score range: {min_score:.2f} - {max_score:.2f}")
            
            # Simple histogram
            score_ranges = [
                (10.0, "Critical (10.0+)"),
                (7.0, "High (7.0-9.9)"),
                (5.0, "Medium (5.0-6.9)"),
                (3.0, "Low (3.0-4.9)"),
                (0.0, "Very Low (0.0-2.9)")
            ]
            
            for min_range, label in score_ranges:
                selected_count = sum(1 for b in analysis['selected_blocks'] if b['final_score'] >= min_range and (min_range == 0.0 or b['final_score'] < min_range + 3.0))
                excluded_count = sum(1 for b in analysis['excluded_blocks'] if b['final_score'] >= min_range and (min_range == 0.0 or b['final_score'] < min_range + 3.0))
                self.stdout.write(f"  {label:20s}: {selected_count:2d} selected, {excluded_count:2d} excluded") 