"""
Management command to evaluate content quality using optimized assessment.

This command uses the OptimizedQualityService which combines smart pre-filtering
with LLM evaluation for cost-effective quality assessment.

Usage:
    python manage.py evaluate_quality --limit 10 --provider openai
    python manage.py evaluate_quality --all --force-llm  # Skip pre-filter
    python manage.py evaluate_quality --article-id abc123  # Single article
"""
from typing import List

from django.core.management.base import BaseCommand, CommandError

from apps.articles.models import Article
from apps.content.quality.optimized_service import OptimizedQualityService


class Command(BaseCommand):
    help = "Evaluate content quality using optimized assessment pipeline"

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=10,
            help="Number of articles to evaluate (default: 10)"
        )
        parser.add_argument(
            "--all",
            action="store_true",
            help="Evaluate all processed articles (overrides --limit)"
        )
        parser.add_argument(
            "--article-id",
            type=str,
            help="Evaluate specific article by public_id"
        )
        parser.add_argument(
            "--provider",
            type=str,
            default="openai",
            choices=["openai", "anthropic"],
            help="AI provider for LLM evaluation"
        )
        parser.add_argument(
            "--force-llm",
            action="store_true",
            help="Skip pre-filter and force LLM evaluation for all articles"
        )
        parser.add_argument(
            "--no-save",
            action="store_true",
            help="Don't save results to database (testing only)"
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
            help="Show detailed evaluation results including LLM responses"
        )

    def handle(self, *args, **options):
        """Execute quality evaluation."""
        self.stdout.write("🔍 Starting Optimized Content Quality Evaluation")
        
        # Get articles to evaluate
        articles = self._get_articles(options)
        
        if not articles:
            raise CommandError("No articles found to evaluate")
        
        self.stdout.write(f"📊 Evaluating {len(articles)} articles")
        if options["force_llm"]:
            self.stdout.write("⚡ LLM-only mode: Pre-filter disabled")
        else:
            self.stdout.write("🎯 Optimized mode: Pre-filter + LLM evaluation")
        
        # Run evaluation
        results = self._evaluate_articles(articles, options)
        
        # Display summary
        self._display_summary(results, options)
        
        self.stdout.write(
            self.style.SUCCESS("✅ Quality evaluation completed successfully")
        )

    def _get_articles(self, options) -> List[Article]:
        """Get articles to evaluate based on options."""
        if options["article_id"]:
            # Single article by ID
            try:
                article = Article.objects.get(public_id=options["article_id"])
                return [article]
            except Article.DoesNotExist:
                raise CommandError(f"Article not found: {options['article_id']}")
        
        # Multiple articles with filtering
        queryset = Article.objects.all()
        
        # Filter by content type
        filter_by = options["filter_by"]
        if filter_by == "clean":
            queryset = queryset.exclude(clean_content__isnull=True).exclude(clean_content="")
        elif filter_by == "basic":
            queryset = queryset.exclude(basic_content__isnull=True).exclude(basic_content="")
        elif filter_by == "raw":
            queryset = queryset.exclude(content__isnull=True).exclude(content="")
        
        # Order by newest first
        queryset = queryset.order_by("-published_at")
        
        # Apply limit
        if not options["all"]:
            queryset = queryset[:options["limit"]]
        
        return list(queryset)

    def _evaluate_articles(self, articles: List[Article], options) -> List:
        """Evaluate articles using the optimized service."""
        service = OptimizedQualityService()
        
        # Use batch assessment for efficiency
        results = service.batch_assess_articles(
            articles=articles,
            provider=options["provider"],
            force_llm=options["force_llm"],
            save_to_db=not options["no_save"]
        )
        
        return results

    def _display_summary(self, results: List, options):
        """Display evaluation summary."""
        if not results:
            self.stdout.write("No results to display")
            return
        
        total_articles = len(results)
        
        # Count by assessment method
        pre_filter_count = sum(1 for r in results if r.assessment_method == "pre_filter")
        llm_count = sum(1 for r in results if r.assessment_method == "llm_evaluation")
        error_count = sum(1 for r in results if "error" in r.assessment_method)
        
        # Calculate score statistics
        valid_scores = [r.quality_score for r in results if r.quality_score is not None]
        
        if valid_scores:
            avg_score = sum(valid_scores) / len(valid_scores)
            min_score = min(valid_scores)
            max_score = max(valid_scores)
        else:
            avg_score = min_score = max_score = 0
        
        # Cost savings calculation
        cost_savings_count = sum(1 for r in results if r.cost_savings)
        cost_savings_rate = (cost_savings_count / total_articles) * 100 if total_articles > 0 else 0
        
        # Display summary
        self.stdout.write("\n" + "="*50)
        self.stdout.write("📈 EVALUATION SUMMARY")
        self.stdout.write("="*50)
        
        self.stdout.write(f"Total Articles: {total_articles}")
        self.stdout.write(f"Provider: {options['provider'].upper()}")
        
        self.stdout.write(f"\n📊 ASSESSMENT METHODS:")
        self.stdout.write(f"  Pre-filter decisions: {pre_filter_count}")
        self.stdout.write(f"  LLM evaluations: {llm_count}")
        self.stdout.write(f"  Errors: {error_count}")
        
        self.stdout.write(f"\n🎯 QUALITY SCORES:")
        self.stdout.write(f"  Average: {avg_score:.3f}")
        self.stdout.write(f"  Range: {min_score:.3f} to {max_score:.3f}")
        
        self.stdout.write(f"\n💰 COST OPTIMIZATION:")
        self.stdout.write(f"  Cost savings rate: {cost_savings_rate:.1f}%")
        self.stdout.write(f"  Articles pre-filtered: {cost_savings_count}")
        
        # Show detailed results if verbose
        if options.get("verbose", False):
            self._display_detailed_results(results)
        else:
            # Show a few example results
            self.stdout.write(f"\n📋 EXAMPLE RESULTS:")
            for i, result in enumerate(results[:3]):
                method_icon = "⚡" if result.assessment_method == "pre_filter" else "🤖"
                self.stdout.write(f"  {i+1}. {method_icon} Score: {result.quality_score:.3f} "
                                f"({result.assessment_method}) - {result.confidence:.2f} confidence")
            
            if len(results) > 3:
                self.stdout.write(f"  ... and {len(results) - 3} more")
        
        # Quality distribution
        excellent = sum(1 for r in results if r.quality_score >= 0.7)
        good = sum(1 for r in results if 0.3 <= r.quality_score < 0.7)
        poor = sum(1 for r in results if 0 <= r.quality_score < 0.3)
        very_poor = sum(1 for r in results if r.quality_score < 0)
        
        self.stdout.write(f"\n🏆 QUALITY DISTRIBUTION:")
        self.stdout.write(f"  Excellent (≥0.7): {excellent}")
        self.stdout.write(f"  Good (0.3-0.7): {good}")
        self.stdout.write(f"  Poor (0.0-0.3): {poor}")
        self.stdout.write(f"  Very Poor (<0.0): {very_poor}")
        
        if not options.get("no_save", False):
            self.stdout.write(f"\n💾 Results saved to QualityScoring table")

    def _display_detailed_results(self, results: List):
        """Display detailed evaluation results for review."""
        self.stdout.write(f"\n" + "="*80)
        self.stdout.write("📋 DETAILED EVALUATION RESULTS")
        self.stdout.write("="*80)
        
        for i, result in enumerate(results, 1):
            self.stdout.write(f"\n{'─' * 80}")
            self.stdout.write(f"📄 ARTICLE {i} - {result.assessment_method.upper()}")
            self.stdout.write(f"{'─' * 80}")
            
            # Basic info
            self.stdout.write(f"🎯 Overall Score: {result.quality_score:.3f}")
            self.stdout.write(f"🔍 Assessment Method: {result.assessment_method}")
            self.stdout.write(f"📊 Confidence: {result.confidence:.2f}")
            self.stdout.write(f"⏱️  Processing Time: {result.processing_time_ms}ms")
            self.stdout.write(f"💰 Cost Savings: {'Yes' if result.cost_savings else 'No'}")
            
            # Pre-filter details
            if result.pre_filter_result:
                self.stdout.write(f"\n⚡ PRE-FILTER ASSESSMENT:")
                self.stdout.write(f"  Decision: {'Use LLM' if result.pre_filter_result.should_use_llm else 'Skip LLM'}")
                self.stdout.write(f"  Reason: {result.pre_filter_result.reason}")
                if result.pre_filter_result.detected_issues:
                    self.stdout.write(f"  Issues: {', '.join(result.pre_filter_result.detected_issues)}")
            
            # LLM evaluation details
            if result.llm_result:
                self.stdout.write(f"\n🤖 LLM EVALUATION:")
                self.stdout.write(f"  Model: {result.llm_result.model_used}")
                self.stdout.write(f"  Tokens: {result.llm_result.tokens_used}")
                self.stdout.write(f"  Cost: ${result.llm_result.cost_usd:.6f}")
                
                self.stdout.write(f"\n📊 DIMENSIONAL SCORES:")
                self.stdout.write(f"  Completeness: {result.llm_result.completeness:.3f}")
                self.stdout.write(f"  Purity: {result.llm_result.purity:.3f}")
                self.stdout.write(f"  Structure: {result.llm_result.structure:.3f}")
                self.stdout.write(f"  Readability: {result.llm_result.readability:.3f}")
                
                self.stdout.write(f"\n💬 EXPLANATION:")
                self.stdout.write(f"  {result.llm_result.explanation}")
                
                if result.llm_result.missing_elements:
                    self.stdout.write(f"\n❌ MISSING ELEMENTS:")
                    for element in result.llm_result.missing_elements:
                        self.stdout.write(f"  • {element}")
                
                if result.llm_result.noise_detected:
                    self.stdout.write(f"\n🔊 NOISE DETECTED:")
                    for noise in result.llm_result.noise_detected:
                        self.stdout.write(f"  • {noise}") 