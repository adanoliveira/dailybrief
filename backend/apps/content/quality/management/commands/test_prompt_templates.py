"""
Management command to test and compare different prompt template versions.

This command allows you to:
1. Test individual prompt templates on articles
2. Compare multiple templates side-by-side
3. Analyze performance differences (cost, accuracy, speed)
4. Generate A/B testing reports

Usage:
    python manage.py test_prompt_templates --list
    python manage.py test_prompt_templates --template quality_evaluation_v1.1-concise --limit 5
    python manage.py test_prompt_templates --compare v1.0 v1.1-concise --limit 10
"""
import time
from typing import List, Dict, Any

from django.core.management.base import BaseCommand, CommandError

from apps.articles.models import Article
from apps.content.quality.evaluator import ContentQualityEvaluator
from apps.content.quality.prompt_templates import list_templates, get_template, AVAILABLE_TEMPLATES


class Command(BaseCommand):
    help = "Test and compare different prompt template versions"

    def add_arguments(self, parser):
        parser.add_argument(
            "--list",
            action="store_true",
            help="List all available prompt templates"
        )
        parser.add_argument(
            "--template",
            type=str,
            help="Test a specific template (e.g., 'quality_evaluation_v1.1-concise')"
        )
        parser.add_argument(
            "--compare",
            nargs=2,
            metavar=("TEMPLATE1", "TEMPLATE2"),
            help="Compare two templates (e.g., --compare v1.0 v1.1-concise)"
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=5,
            help="Number of articles to test (default: 5)"
        )
        parser.add_argument(
            "--filter-by",
            type=str,
            choices=["all", "clean", "basic", "raw"],
            default="clean",
            help="Filter articles by content type (default: clean)"
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Show detailed evaluation results"
        )
        parser.add_argument(
            "--save-results",
            action="store_true",
            help="Save results to database"
        )

    def handle(self, *args, **options):
        """Execute the prompt template testing."""
        if options["list"]:
            self._list_templates()
        elif options["template"]:
            self._test_single_template(options)
        elif options["compare"]:
            self._compare_templates(options)
        else:
            raise CommandError("Please specify --list, --template, or --compare")

    def _list_templates(self):
        """List all available prompt templates."""
        self.stdout.write("📋 Available Prompt Templates:")
        self.stdout.write("=" * 50)
        
        templates = list_templates()
        for template_id, metadata in templates.items():
            status = "🟢 BASELINE" if metadata.is_baseline else "⚪ VARIANT"
            self.stdout.write(f"\n{status} {template_id}")
            self.stdout.write(f"  Version: {metadata.version}")
            self.stdout.write(f"  Description: {metadata.description}")
            self.stdout.write(f"  Created by: {metadata.created_by}")
            
            # Show token count estimation
            template = get_template(template_id)
            sample_prompt = template.format(
                title="Sample Article Title",
                author="Sample Author",
                description="Sample description",
                content_length=1000,
                content_sample="Sample content...",
                blocks_count=3,
                blocks_sample="Sample blocks",
                metadata="Sample metadata",
                html_length=5000,
                html_sample="Sample HTML..."
            )
            estimated_tokens = len(sample_prompt.split()) * 1.3  # Rough estimation
            self.stdout.write(f"  Estimated tokens: ~{estimated_tokens:.0f}")

    def _test_single_template(self, options):
        """Test a single prompt template."""
        template_id = self._resolve_template_id(options["template"])
        
        self.stdout.write(f"🧪 Testing Template: {template_id}")
        self.stdout.write("=" * 50)
        
        # Get articles
        articles = self._get_articles(options)
        if not articles:
            raise CommandError("No articles found to test")
        
        # Test template
        results = self._evaluate_with_template(template_id, articles, options)
        
        # Display results
        self._display_template_results(template_id, results, options)
        
        self.stdout.write(
            self.style.SUCCESS(f"✅ Template testing completed: {template_id}")
        )

    def _compare_templates(self, options):
        """Compare two prompt templates."""
        template1_id = self._resolve_template_id(options["compare"][0])
        template2_id = self._resolve_template_id(options["compare"][1])
        
        self.stdout.write(f"⚖️  Comparing Templates:")
        self.stdout.write(f"  Template A: {template1_id}")
        self.stdout.write(f"  Template B: {template2_id}")
        self.stdout.write("=" * 50)
        
        # Get articles
        articles = self._get_articles(options)
        if not articles:
            raise CommandError("No articles found to test")
        
        # Test both templates
        self.stdout.write("Testing Template A...")
        results1 = self._evaluate_with_template(template1_id, articles, options)
        
        self.stdout.write("Testing Template B...")
        results2 = self._evaluate_with_template(template2_id, articles, options)
        
        # Compare results
        self._display_comparison_results(template1_id, template2_id, results1, results2, options)
        
        self.stdout.write(
            self.style.SUCCESS("✅ Template comparison completed")
        )

    def _resolve_template_id(self, template_input: str) -> str:
        """Resolve template input to full template ID."""
        # Check if it's already a full template ID
        if template_input in AVAILABLE_TEMPLATES:
            return template_input
        
        # Try to find by version (e.g., "v1.0" -> "quality_evaluation_v1.0")
        for template_id in AVAILABLE_TEMPLATES:
            if template_input in template_id:
                return template_id
        
        raise CommandError(f"Template not found: {template_input}. Use --list to see available templates.")

    def _get_articles(self, options) -> List[Article]:
        """Get articles for testing."""
        queryset = Article.objects.all()
        
        # Filter by content type
        filter_by = options["filter_by"]
        if filter_by == "clean":
            queryset = queryset.exclude(clean_content__isnull=True).exclude(clean_content="")
        elif filter_by == "basic":
            queryset = queryset.exclude(basic_content__isnull=True).exclude(basic_content="")
        elif filter_by == "raw":
            queryset = queryset.exclude(content__isnull=True).exclude(content="")
        
        # Order by newest first and limit
        queryset = queryset.order_by("-published_at")[:options["limit"]]
        
        return list(queryset)

    def _evaluate_with_template(self, template_id: str, articles: List[Article], options) -> List:
        """Evaluate articles with a specific template."""
        evaluator = ContentQualityEvaluator(template_id=template_id)
        results = []
        
        for i, article in enumerate(articles, 1):
            self.stdout.write(f"  Evaluating article {i}/{len(articles)}...")
            
            start_time = time.time()
            result = evaluator.evaluate_article_quality(article)
            
            results.append({
                'article_id': article.public_id,
                'article_title': article.title[:50] + "..." if len(article.title) > 50 else article.title,
                'result': result,
                'processing_time': time.time() - start_time
            })
        
        return results

    def _display_template_results(self, template_id: str, results: List, options):
        """Display results for a single template."""
        if not results:
            self.stdout.write("No results to display")
            return
        
        # Calculate statistics
        scores = [r['result'].overall_score for r in results]
        confidences = [r['result'].confidence for r in results]
        costs = [float(r['result'].cost_usd) for r in results]
        tokens = [r['result'].tokens_used for r in results]
        times = [r['processing_time'] for r in results]
        
        avg_score = sum(scores) / len(scores)
        avg_confidence = sum(confidences) / len(confidences)
        avg_cost = sum(costs) / len(costs)
        avg_tokens = sum(tokens) / len(tokens)
        avg_time = sum(times) / len(times)
        
        # Display summary
        self.stdout.write(f"\n📊 RESULTS SUMMARY - {template_id}")
        self.stdout.write("─" * 50)
        self.stdout.write(f"Articles tested: {len(results)}")
        self.stdout.write(f"Average score: {avg_score:.3f}")
        self.stdout.write(f"Average confidence: {avg_confidence:.3f}")
        self.stdout.write(f"Average cost: ${avg_cost:.6f}")
        self.stdout.write(f"Average tokens: {avg_tokens:.0f}")
        self.stdout.write(f"Average time: {avg_time:.2f}s")
        
        # Show individual results if verbose
        if options.get("verbose", False):
            self.stdout.write(f"\n📋 DETAILED RESULTS:")
            self.stdout.write("─" * 50)
            for i, result_data in enumerate(results, 1):
                result = result_data['result']
                self.stdout.write(f"\n{i}. {result_data['article_title']}")
                self.stdout.write(f"   Score: {result.overall_score:.3f} | Confidence: {result.confidence:.2f}")
                self.stdout.write(f"   Cost: ${result.cost_usd:.6f} | Tokens: {result.tokens_used}")
                self.stdout.write(f"   Time: {result_data['processing_time']:.2f}s")
                self.stdout.write(f"   Explanation: {result.explanation[:100]}...")

    def _display_comparison_results(self, template1_id: str, template2_id: str, results1: List, results2: List, options):
        """Display comparison results between two templates."""
        if not results1 or not results2:
            self.stdout.write("Insufficient results for comparison")
            return
        
        # Calculate statistics for both templates
        def calc_stats(results):
            scores = [r['result'].overall_score for r in results]
            confidences = [r['result'].confidence for r in results]
            costs = [float(r['result'].cost_usd) for r in results]
            tokens = [r['result'].tokens_used for r in results]
            times = [r['processing_time'] for r in results]
            
            return {
                'avg_score': sum(scores) / len(scores),
                'avg_confidence': sum(confidences) / len(confidences),
                'avg_cost': sum(costs) / len(costs),
                'avg_tokens': sum(tokens) / len(tokens),
                'avg_time': sum(times) / len(times),
                'score_range': (min(scores), max(scores))
            }
        
        stats1 = calc_stats(results1)
        stats2 = calc_stats(results2)
        
        # Display comparison
        self.stdout.write(f"\n⚖️  COMPARISON RESULTS")
        self.stdout.write("=" * 60)
        self.stdout.write(f"{'Metric':<20} {'Template A':<15} {'Template B':<15} {'Difference':<10}")
        self.stdout.write("─" * 60)
        
        # Score comparison
        score_diff = stats2['avg_score'] - stats1['avg_score']
        score_icon = "🟢" if score_diff > 0 else "🔴" if score_diff < 0 else "⚪"
        self.stdout.write(f"{'Average Score':<20} {stats1['avg_score']:<15.3f} {stats2['avg_score']:<15.3f} {score_icon} {score_diff:+.3f}")
        
        # Confidence comparison
        conf_diff = stats2['avg_confidence'] - stats1['avg_confidence']
        conf_icon = "🟢" if conf_diff > 0 else "🔴" if conf_diff < 0 else "⚪"
        self.stdout.write(f"{'Average Confidence':<20} {stats1['avg_confidence']:<15.3f} {stats2['avg_confidence']:<15.3f} {conf_icon} {conf_diff:+.3f}")
        
        # Cost comparison
        cost_diff = stats2['avg_cost'] - stats1['avg_cost']
        cost_icon = "🟢" if cost_diff < 0 else "🔴" if cost_diff > 0 else "⚪"  # Lower cost is better
        self.stdout.write(f"{'Average Cost':<20} ${stats1['avg_cost']:<14.6f} ${stats2['avg_cost']:<14.6f} {cost_icon} ${cost_diff:+.6f}")
        
        # Token comparison
        token_diff = stats2['avg_tokens'] - stats1['avg_tokens']
        token_icon = "🟢" if token_diff < 0 else "🔴" if token_diff > 0 else "⚪"  # Lower tokens is better
        self.stdout.write(f"{'Average Tokens':<20} {stats1['avg_tokens']:<15.0f} {stats2['avg_tokens']:<15.0f} {token_icon} {token_diff:+.0f}")
        
        # Time comparison
        time_diff = stats2['avg_time'] - stats1['avg_time']
        time_icon = "🟢" if time_diff < 0 else "🔴" if time_diff > 0 else "⚪"  # Lower time is better
        self.stdout.write(f"{'Average Time':<20} {stats1['avg_time']:<15.2f}s {stats2['avg_time']:<15.2f}s {time_icon} {time_diff:+.2f}s")
        
        # Overall recommendation
        self.stdout.write(f"\n🎯 RECOMMENDATION:")
        if score_diff > 0.05 and cost_diff <= 0:
            self.stdout.write(f"   Template B ({template2_id}) is better: Higher accuracy at same/lower cost")
        elif score_diff < -0.05 and cost_diff >= 0:
            self.stdout.write(f"   Template A ({template1_id}) is better: Higher accuracy at same/lower cost")
        elif cost_diff < -0.001 and abs(score_diff) < 0.02:
            self.stdout.write(f"   Template B ({template2_id}) is more cost-effective: Similar accuracy at lower cost")
        elif cost_diff > 0.001 and abs(score_diff) < 0.02:
            self.stdout.write(f"   Template A ({template1_id}) is more cost-effective: Similar accuracy at lower cost")
        else:
            self.stdout.write("   Results are inconclusive. Consider testing with more samples.") 