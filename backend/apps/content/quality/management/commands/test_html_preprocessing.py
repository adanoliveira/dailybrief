"""
Management command to test HTML preprocessing optimization.

This command compares the original HTML approach vs intelligent preprocessing
to measure token reduction and evaluate impact on quality assessment accuracy.

Usage:
    python manage.py test_html_preprocessing --limit 5
    python manage.py test_html_preprocessing --article-id abc123 --verbose
"""
from typing import List, Dict

from django.core.management.base import BaseCommand, CommandError

from apps.articles.models import Article
from apps.content.quality.html_preprocessor import HTMLPreprocessor
from apps.content.quality.evaluator import ContentQualityEvaluator


class Command(BaseCommand):
    help = "Test HTML preprocessing optimization for quality evaluation"

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=5,
            help="Number of articles to test (default: 5)"
        )
        parser.add_argument(
            "--article-id",
            type=str,
            help="Test specific article by public_id"
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Show detailed preprocessing results and comparisons"
        )
        parser.add_argument(
            "--provider",
            type=str,
            default="openai",
            choices=["openai", "anthropic"],
            help="AI provider for LLM evaluation"
        )
        parser.add_argument(
            "--compare-quality",
            action="store_true",
            help="Compare quality scores between original and preprocessed HTML"
        )

    def handle(self, *args, **options):
        """Execute HTML preprocessing test."""
        self.stdout.write("🔬 Testing HTML Preprocessing Optimization")
        
        # Get articles to test
        articles = self._get_articles(options)
        
        if not articles:
            raise CommandError("No articles found to test")
        
        self.stdout.write(f"📊 Testing {len(articles)} articles")
        
        # Run preprocessing tests
        results = self._test_preprocessing(articles, options)
        
        # Display results
        self._display_results(results, options)
        
        self.stdout.write(
            self.style.SUCCESS("✅ HTML preprocessing test completed")
        )

    def _get_articles(self, options) -> List[Article]:
        """Get articles to test based on options."""
        if options["article_id"]:
            # Single article by ID
            try:
                article = Article.objects.get(public_id=options["article_id"])
                return [article]
            except Article.DoesNotExist:
                raise CommandError(f"Article not found: {options['article_id']}")
        
        # Multiple articles with HTML content
        queryset = Article.objects.exclude(
            raw_html__isnull=True
        ).exclude(
            raw_html=""
        ).exclude(
            clean_content__isnull=True
        ).exclude(
            clean_content=""
        ).order_by("-published_at")
        
        # Apply limit
        queryset = queryset[:options["limit"]]
        
        return list(queryset)

    def _test_preprocessing(self, articles: List[Article], options) -> List[Dict]:
        """Test preprocessing on articles and collect results."""
        preprocessor = HTMLPreprocessor()
        results = []
        
        for i, article in enumerate(articles):
            self.stdout.write(f"Processing article {i+1}/{len(articles)}: {article.public_id}")
            
            try:
                # Test preprocessing
                original_html = article.raw_html or ""
                original_size = len(original_html)
                
                # Apply preprocessing
                preprocessed = preprocessor.preprocess_for_evaluation(
                    original_html, 
                    url=article.url,  # For caching
                    max_tokens=12000,  # Updated parameter name and increased limit
                    use_cache=True
                )
                
                # Calculate metrics
                compression_ratio = preprocessed.compression_ratio
                token_estimate_original = self._estimate_tokens(original_html[:8000])  # Original limit
                token_estimate_preprocessed = self._estimate_tokens(preprocessed.cleaned_html)
                token_reduction = ((token_estimate_original - token_estimate_preprocessed) / 
                                 max(token_estimate_original, 1)) * 100
                
                result = {
                    "article": article,
                    "original_size": original_size,
                    "preprocessed_size": preprocessed.cleaned_size,
                    "compression_ratio": compression_ratio,
                    "token_estimate_original": token_estimate_original,
                    "token_estimate_preprocessed": token_estimate_preprocessed,
                    "token_reduction": token_reduction,
                    "removed_elements": preprocessed.removed_elements,
                    "preserved_structure": preprocessed.preserved_structure,
                    "content_density_info": preprocessed.content_density_info,
                    "preprocessing_method": preprocessed.processing_method,
                    "cache_used": preprocessed.cache_used,
                    "preprocessing_summary": preprocessor.get_preprocessing_summary(preprocessed)
                }
                
                # Optional: Compare quality scores
                if options.get("compare_quality"):
                    quality_comparison = self._compare_quality_scores(article, options["provider"])
                    result.update(quality_comparison)
                
                results.append(result)
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Failed to process article {article.public_id}: {e}")
                )
                continue
        
        return results

    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimation (4 chars ≈ 1 token for English)."""
        return max(1, len(text) // 4)

    def _compare_quality_scores(self, article: Article, provider: str) -> Dict:
        """Compare quality scores between original and preprocessed HTML."""
        evaluator = ContentQualityEvaluator()
        
        try:
            # Evaluate with original HTML approach
            result_original = evaluator.evaluate_article_quality(
                article, 
                use_html_preprocessing=False
            )
            
            # Evaluate with preprocessed HTML
            result_preprocessed = evaluator.evaluate_article_quality(
                article,
                use_html_preprocessing=True
            )
            
            return {
                "quality_original": result_original.overall_score,
                "quality_preprocessed": result_preprocessed.overall_score,
                "quality_difference": result_preprocessed.overall_score - result_original.overall_score,
                "tokens_original": result_original.tokens_used,
                "tokens_preprocessed": result_preprocessed.tokens_used,
                "cost_original": float(result_original.cost_usd),
                "cost_preprocessed": float(result_preprocessed.cost_usd),
                "quality_comparison_available": True
            }
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f"Quality comparison failed: {e}")
            )
            return {
                "quality_comparison_available": False,
                "quality_comparison_error": str(e)
            }

    def _display_results(self, results: List[Dict], options):
        """Display preprocessing test results."""
        if not results:
            self.stdout.write("No results to display")
            return
        
        # Calculate aggregate statistics
        total_articles = len(results)
        avg_compression = sum(r["compression_ratio"] for r in results) / total_articles
        avg_token_reduction = sum(r["token_reduction"] for r in results) / total_articles
        
        # Display summary
        self.stdout.write("\n" + "="*60)
        self.stdout.write("📈 HTML PREPROCESSING SUMMARY")
        self.stdout.write("="*60)
        
        self.stdout.write(f"Articles tested: {total_articles}")
        self.stdout.write(f"Average HTML compression: {avg_compression:.1f}%")
        self.stdout.write(f"Average token reduction: {avg_token_reduction:.1f}%")
        
        # Size reduction statistics
        total_original_size = sum(r["original_size"] for r in results)
        total_preprocessed_size = sum(r["preprocessed_size"] for r in results)
        overall_reduction = ((total_original_size - total_preprocessed_size) / 
                           max(total_original_size, 1)) * 100
        
        self.stdout.write(f"Overall size reduction: {overall_reduction:.1f}%")
        self.stdout.write(f"Total size: {total_original_size:,} → {total_preprocessed_size:,} chars")
        
        # Token statistics
        total_tokens_original = sum(r["token_estimate_original"] for r in results)
        total_tokens_preprocessed = sum(r["token_estimate_preprocessed"] for r in results)
        token_savings = total_tokens_original - total_tokens_preprocessed
        
        self.stdout.write(f"Estimated token savings: {token_savings:,} tokens")
        self.stdout.write(f"Token usage: {total_tokens_original:,} → {total_tokens_preprocessed:,}")
        
        # Quality comparison if available
        quality_results = [r for r in results if r.get("quality_comparison_available")]
        if quality_results:
            avg_quality_diff = sum(r["quality_difference"] for r in quality_results) / len(quality_results)
            avg_cost_savings = sum(
                r["cost_original"] - r["cost_preprocessed"] for r in quality_results
            ) / len(quality_results)
            
            self.stdout.write(f"\n🎯 QUALITY IMPACT:")
            self.stdout.write(f"Average quality difference: {avg_quality_diff:+.3f}")
            self.stdout.write(f"Average cost savings: ${avg_cost_savings:.6f} per evaluation")
        
        # Show detailed results if verbose
        if options.get("verbose"):
            self._display_detailed_results(results)

    def _display_detailed_results(self, results: List[Dict]):
        """Display detailed results for each article."""
        self.stdout.write(f"\n" + "="*80)
        self.stdout.write("📋 DETAILED PREPROCESSING RESULTS")
        self.stdout.write("="*80)
        
        for i, result in enumerate(results, 1):
            article = result["article"]
            
            self.stdout.write(f"\n{'─' * 80}")
            self.stdout.write(f"📄 ARTICLE {i}: {article.title[:50]}...")
            self.stdout.write(f"{'─' * 80}")
            
            self.stdout.write(f"🔗 ID: {article.public_id}")
            self.stdout.write(f"📏 HTML Size: {result['original_size']:,} → {result['preprocessed_size']:,} chars")
            self.stdout.write(f"📉 Compression: {result['compression_ratio']:.1f}%")
            self.stdout.write(f"🎯 Token Reduction: {result['token_reduction']:.1f}%")
            
            self.stdout.write(f"\n🗑️  REMOVED ELEMENTS:")
            for element in result["removed_elements"][:5]:  # Show first 5
                self.stdout.write(f"  • {element}")
            if len(result["removed_elements"]) > 5:
                self.stdout.write(f"  ... and {len(result['removed_elements']) - 5} more")
            
            self.stdout.write(f"\n🏗️  PRESERVED STRUCTURE:")
            for structure in result["preserved_structure"][:5]:  # Show first 5
                self.stdout.write(f"  • {structure}")
            if len(result["preserved_structure"]) > 5:
                self.stdout.write(f"  ... and {len(result['preserved_structure']) - 5} more")
            
            self.stdout.write(f"\n📋 CONTENT SECTIONS:")
            for section in result["content_density_info"]:
                self.stdout.write(f"  • {section}")
            
            # Quality comparison if available
            if result.get("quality_comparison_available"):
                self.stdout.write(f"\n🎯 QUALITY COMPARISON:")
                self.stdout.write(f"  Original: {result['quality_original']:.3f}")
                self.stdout.write(f"  Preprocessed: {result['quality_preprocessed']:.3f}")
                self.stdout.write(f"  Difference: {result['quality_difference']:+.3f}")
                self.stdout.write(f"  Token savings: {result['tokens_original'] - result['tokens_preprocessed']:,}")
                self.stdout.write(f"  Cost savings: ${result['cost_original'] - result['cost_preprocessed']:.6f}")
            
            self.stdout.write(f"\n💬 Summary: {result['preprocessing_summary']}") 