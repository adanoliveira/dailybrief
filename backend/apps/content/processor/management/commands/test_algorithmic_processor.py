"""
Test Algorithmic Processor Command
Tests the new Safari Reader Mode-inspired algorithmic processor on real articles.
"""

import time
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from apps.articles.models import Article
from apps.content.processor.algorithmic_processor import AlgorithmicProcessor


class Command(BaseCommand):
    help = 'Test the new AlgorithmicProcessor on real articles'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=5,
            help='Number of articles to test (default: 5)'
        )
        parser.add_argument(
            '--source',
            type=str,
            help='Filter by source name (e.g., "The Verge", "CNN")'
        )
        parser.add_argument(
            '--article-id',
            type=int,
            help='Test specific article by ID'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed processing information'
        )
        parser.add_argument(
            '--compare-old',
            action='store_true',
            help='Compare with existing processed content if available'
        )

    def handle(self, *args, **options):
        self.verbosity = options['verbosity']
        self.verbose = options['verbose']
        
        # Initialize processor
        processor = AlgorithmicProcessor()
        
        # Get articles to test
        articles = self._get_test_articles(options)
        
        if not articles:
            raise CommandError("No articles found matching criteria")
        
        self.stdout.write(
            self.style.SUCCESS(f"\n🧪 Testing AlgorithmicProcessor on {len(articles)} articles\n")
        )
        
        # Test each article
        results = []
        total_time = 0
        
        for i, article in enumerate(articles, 1):
            self.stdout.write(f"📰 [{i}/{len(articles)}] Testing: {article.title[:60]}...")
            
            result = self._test_article(processor, article, options)
            results.append(result)
            total_time += result['processing_time_ms']
            
            if self.verbose:
                self._print_detailed_result(result)
            else:
                self._print_summary_result(result)
        
        # Print overall statistics
        self._print_overall_statistics(results, total_time)

    def _get_test_articles(self, options):
        """Get articles for testing based on options."""
        
        if options['article_id']:
            # Test specific article
            try:
                return [Article.objects.get(id=options['article_id'])]
            except Article.DoesNotExist:
                raise CommandError(f"Article with ID {options['article_id']} not found")
        
        # Build query for articles with raw_html
        query = Q(raw_html__isnull=False) & ~Q(raw_html='')
        
        if options['source']:
            query &= Q(source_name__icontains=options['source'])
        
        # Get diverse articles from different sources
        articles = Article.objects.filter(query).order_by('-published_at')[:options['count']]
        
        return list(articles)

    def _test_article(self, processor, article, options):
        """Test processing on a single article."""
        
        # Prepare article metadata
        article_metadata = {
            'title': article.title,
            'author': article.author,
            'published_date': article.published_at,
            'source_name': article.source_name,
            'url': article.url
        }
        
        # Process with algorithmic processor
        start_time = time.time()
        result = processor.process_content(article.raw_html, article_metadata)
        end_time = time.time()
        
        # Prepare test result
        test_result = {
            'article_id': article.id,
            'article_title': article.title,
            'source_name': article.source_name,
            'url': article.url,
            'success': result.success,
            'processing_time_ms': result.processing_time_ms,
            'actual_time_ms': int((end_time - start_time) * 1000),
            'quality_score': result.quality_score,
            'content_blocks_count': len(result.content_blocks),
            'clean_content_length': len(result.clean_content),
            'word_count': result.extracted_metadata.get('word_count', 0),
            'error_message': result.error_message,
            'raw_html_length': len(article.raw_html),
            'extracted_metadata': result.extracted_metadata
        }
        
        # Compare with existing content if requested
        if options['compare_old'] and article.clean_content:
            test_result['comparison'] = self._compare_with_existing(article, result)
        
        return test_result

    def _compare_with_existing(self, article, new_result):
        """Compare new result with existing processed content."""
        
        old_content = article.clean_content or ""
        new_content = new_result.clean_content
        
        old_word_count = len(old_content.split())
        new_word_count = len(new_content.split())
        
        # Calculate similarity (simple word overlap)
        old_words = set(old_content.lower().split())
        new_words = set(new_content.lower().split())
        
        if old_words and new_words:
            overlap = len(old_words & new_words)
            union = len(old_words | new_words)
            similarity = overlap / union if union > 0 else 0
        else:
            similarity = 0
        
        return {
            'old_word_count': old_word_count,
            'new_word_count': new_word_count,
            'word_count_change': new_word_count - old_word_count,
            'similarity_score': similarity,
            'content_length_change': len(new_content) - len(old_content)
        }

    def _print_detailed_result(self, result):
        """Print detailed result information."""
        
        if result['success']:
            self.stdout.write(
                self.style.SUCCESS(f"  ✅ Success! Quality: {result['quality_score']:.3f}")
            )
            self.stdout.write(f"     ⏱️  Processing: {result['processing_time_ms']}ms")
            self.stdout.write(f"     📝 Content: {result['clean_content_length']:,} chars, {result['word_count']} words")
            self.stdout.write(f"     🧱 Blocks: {result['content_blocks_count']}")
            self.stdout.write(f"     📊 Metadata: {len(result['extracted_metadata'])} fields")
            
            if 'comparison' in result:
                comp = result['comparison']
                self.stdout.write(f"     🔄 vs Old: {comp['word_count_change']:+d} words, "
                                f"{comp['similarity_score']:.2f} similarity")
        else:
            self.stdout.write(
                self.style.ERROR(f"  ❌ Failed: {result['error_message']}")
            )
        
        self.stdout.write("")  # Empty line

    def _print_summary_result(self, result):
        """Print summary result information."""
        
        if result['success']:
            status = self.style.SUCCESS("✅")
            info = f"Q:{result['quality_score']:.2f} T:{result['processing_time_ms']}ms W:{result['word_count']}"
        else:
            status = self.style.ERROR("❌")
            info = f"Error: {result['error_message'][:30]}..."
        
        self.stdout.write(f"  {status} {info}")

    def _print_overall_statistics(self, results, total_time):
        """Print overall test statistics."""
        
        successful = [r for r in results if r['success']]
        failed = [r for r in results if not r['success']]
        
        self.stdout.write("\n" + "="*60)
        self.stdout.write(self.style.SUCCESS("📊 ALGORITHMIC PROCESSOR TEST RESULTS"))
        self.stdout.write("="*60)
        
        # Success metrics
        success_rate = len(successful) / len(results) * 100 if results else 0
        self.stdout.write(f"✅ Success Rate: {success_rate:.1f}% ({len(successful)}/{len(results)})")
        
        if successful:
            # Quality metrics
            avg_quality = sum(r['quality_score'] for r in successful) / len(successful)
            min_quality = min(r['quality_score'] for r in successful)
            max_quality = max(r['quality_score'] for r in successful)
            
            self.stdout.write(f"🎯 Quality Score: {avg_quality:.3f} avg (range: {min_quality:.3f}-{max_quality:.3f})")
            
            # Performance metrics
            avg_time = sum(r['processing_time_ms'] for r in successful) / len(successful)
            min_time = min(r['processing_time_ms'] for r in successful)
            max_time = max(r['processing_time_ms'] for r in successful)
            
            self.stdout.write(f"⏱️  Processing Time: {avg_time:.0f}ms avg (range: {min_time}-{max_time}ms)")
            
            # Content metrics
            avg_words = sum(r['word_count'] for r in successful) / len(successful)
            avg_blocks = sum(r['content_blocks_count'] for r in successful) / len(successful)
            
            self.stdout.write(f"📝 Content: {avg_words:.0f} words avg, {avg_blocks:.1f} blocks avg")
            
            # Source breakdown
            sources = {}
            for r in successful:
                source = r['source_name'] or 'Unknown'
                if source not in sources:
                    sources[source] = {'count': 0, 'quality': 0}
                sources[source]['count'] += 1
                sources[source]['quality'] += r['quality_score']
            
            self.stdout.write(f"\n📰 Source Performance:")
            for source, data in sorted(sources.items(), key=lambda x: x[1]['count'], reverse=True):
                avg_q = data['quality'] / data['count']
                self.stdout.write(f"   {source}: {data['count']} articles, {avg_q:.3f} avg quality")
        
        if failed:
            self.stdout.write(f"\n❌ Failed Articles: {len(failed)}")
            error_types = {}
            for r in failed:
                error = r['error_message'][:50]
                error_types[error] = error_types.get(error, 0) + 1
            
            for error, count in error_types.items():
                self.stdout.write(f"   {error}: {count} articles")
        
        # Performance summary
        total_articles = len(results)
        total_time_sec = total_time / 1000
        articles_per_sec = total_articles / total_time_sec if total_time_sec > 0 else 0
        
        self.stdout.write(f"\n⚡ Performance: {articles_per_sec:.2f} articles/second")
        self.stdout.write(f"💰 Estimated Cost: $0.001 per article (algorithmic mode)")
        
        # Quality assessment
        if successful:
            high_quality = len([r for r in successful if r['quality_score'] >= 0.8])
            medium_quality = len([r for r in successful if 0.6 <= r['quality_score'] < 0.8])
            low_quality = len([r for r in successful if r['quality_score'] < 0.6])
            
            self.stdout.write(f"\n🏆 Quality Distribution:")
            self.stdout.write(f"   High (≥0.8): {high_quality} articles ({high_quality/len(successful)*100:.1f}%)")
            self.stdout.write(f"   Medium (0.6-0.8): {medium_quality} articles ({medium_quality/len(successful)*100:.1f}%)")
            self.stdout.write(f"   Low (<0.6): {low_quality} articles ({low_quality/len(successful)*100:.1f}%)")
        
        self.stdout.write("\n" + "="*60)
        
        # Recommendations
        if successful:
            if avg_quality >= 0.8:
                self.stdout.write(self.style.SUCCESS("🎉 Excellent! AlgorithmicProcessor is performing very well."))
            elif avg_quality >= 0.6:
                self.stdout.write(self.style.WARNING("⚠️  Good performance, but some articles may benefit from LLM enhancement."))
            else:
                self.stdout.write(self.style.ERROR("🔧 Performance needs improvement. Consider tuning algorithm parameters."))
        
        if success_rate < 90:
            self.stdout.write(self.style.WARNING("⚠️  Success rate below 90%. Check error patterns above."))
        
        self.stdout.write("") 