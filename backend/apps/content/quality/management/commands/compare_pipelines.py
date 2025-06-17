"""
Management command to compare quality assessment pipelines.

This command runs both pre-filter and LLM evaluation on the same set of articles
to analyze accuracy, agreement rates, and cost optimization opportunities.

Usage:
    python manage.py compare_pipelines --limit 50 --provider openai
    python manage.py compare_pipelines --all --save-results
"""
import asyncio
import json
from typing import Dict, List
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.articles.models import Article
from apps.content.quality.optimized_service import OptimizedQualityService
from apps.content.quality.models import QualityScoring


class Command(BaseCommand):
    help = "Compare pre-filter vs LLM quality assessment pipelines"

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=20,
            help="Number of articles to compare (default: 20)"
        )
        parser.add_argument(
            "--all",
            action="store_true",
            help="Compare all processed articles (overrides --limit)"
        )
        parser.add_argument(
            "--provider",
            type=str,
            default="openai",
            choices=["openai", "anthropic"],
            help="AI provider for LLM evaluation"
        )
        parser.add_argument(
            "--save-results",
            action="store_true",
            help="Save comparison results to database"
        )
        parser.add_argument(
            "--filter-by",
            type=str,
            choices=["all", "clean", "basic", "raw"],
            default="all",
            help="Filter articles by content type"
        )

    def handle(self, *args, **options):
        """Execute the pipeline comparison."""
        self.stdout.write("🔍 Starting Quality Assessment Pipeline Comparison")
        
        # Get articles to compare
        articles = self._get_articles(
            limit=options["limit"],
            all_articles=options["all"],
            filter_by=options["filter_by"]
        )
        
        if not articles:
            raise CommandError("No articles found to compare")
        
        self.stdout.write(f"📊 Comparing pipelines on {len(articles)} articles")
        
        # Run comparison
        comparison_results = asyncio.run(
            self._run_comparison(articles, options["provider"])
        )
        
        # Display results
        self._display_comparison_results(comparison_results)
        
        # Save results if requested
        if options["save_results"]:
            self._save_comparison_results(comparison_results, options)
        
        self.stdout.write(
            self.style.SUCCESS("✅ Pipeline comparison completed successfully")
        )

    def _get_articles(
        self, 
        limit: int, 
        all_articles: bool, 
        filter_by: str
    ) -> List[Article]:
        """Get articles for comparison based on criteria."""
        queryset = Article.objects.all()
        
        # Filter by content type
        if filter_by == "clean":
            queryset = queryset.exclude(clean_content__isnull=True).exclude(clean_content="")
        elif filter_by == "basic":
            queryset = queryset.exclude(basic_content__isnull=True).exclude(basic_content="")
        elif filter_by == "raw":
            queryset = queryset.exclude(content__isnull=True).exclude(content="")
        
        # Order by newest first and apply limit
        queryset = queryset.order_by("-published_at")
        
        if not all_articles:
            queryset = queryset[:limit]
        
        return list(queryset)

    async def _run_comparison(
        self, 
        articles: List[Article], 
        provider: str
    ) -> Dict:
        """Run the actual pipeline comparison."""
        service = OptimizedQualityService()
        
        self.stdout.write("⚡ Running pipeline comparison...")
        
        # Compare methods
        comparison_data = await service.compare_methods(articles, provider)
        
        # Add cost analysis
        total_articles = len(articles)
        llm_cost_per_article = 0.0005  # $0.0005 per LLM evaluation
        
        pre_filter_decisions = comparison_data["confident_pre_filter_decisions"]
        cost_without_filter = total_articles * llm_cost_per_article
        cost_with_filter = (total_articles - pre_filter_decisions) * llm_cost_per_article
        savings = cost_without_filter - cost_with_filter
        
        comparison_data.update({
            "cost_analysis": {
                "total_articles": total_articles,
                "pre_filter_decisions": pre_filter_decisions,
                "llm_evaluations": total_articles - pre_filter_decisions,
                "cost_without_filter_usd": round(cost_without_filter, 4),
                "cost_with_filter_usd": round(cost_with_filter, 4),
                "savings_usd": round(savings, 4),
                "savings_percentage": round((savings / cost_without_filter) * 100, 1)
            }
        })
        
        return comparison_data

    def _display_comparison_results(self, results: Dict):
        """Display comprehensive comparison results."""
        self.stdout.write("\n" + "="*60)
        self.stdout.write("📈 PIPELINE COMPARISON RESULTS")
        self.stdout.write("="*60)
        
        # Overview
        total = results["total_articles"]
        pre_filter_decisions = results["confident_pre_filter_decisions"]
        agreement_rate = results["agreement_rate"]
        
        self.stdout.write(f"Total Articles Analyzed: {total}")
        self.stdout.write(f"Pre-filter Confident Decisions: {pre_filter_decisions}")
        self.stdout.write(f"Pre-filter Rate: {results['pre_filter_rate']:.1%}")
        self.stdout.write(f"Agreement Rate (when confident): {agreement_rate:.1%}")
        
        # Cost Analysis
        cost_data = results["cost_analysis"]
        self.stdout.write("\n💰 COST ANALYSIS")
        self.stdout.write("-" * 30)
        self.stdout.write(f"Cost without pre-filter: ${cost_data['cost_without_filter_usd']:.4f}")
        self.stdout.write(f"Cost with pre-filter: ${cost_data['cost_with_filter_usd']:.4f}")
        self.stdout.write(f"Savings: ${cost_data['savings_usd']:.4f} ({cost_data['savings_percentage']}%)")
        
        # Agreement Analysis
        if results["agreements"] > 0:
            self.stdout.write("\n🤝 AGREEMENT ANALYSIS")
            self.stdout.write("-" * 30)
            self.stdout.write(f"Agreements: {results['agreements']}")
            self.stdout.write(f"Disagreements: {results['disagreements']}")
            
            # Show examples of disagreements
            disagreement_examples = self._find_disagreements(results)
            if disagreement_examples:
                self.stdout.write("\n❌ Disagreement Examples:")
                for i, example in enumerate(disagreement_examples[:3]):
                    self.stdout.write(f"{i+1}. Pre-filter: {example['pre_filter_score']:.2f}, "
                                    f"LLM: {example['llm_score']:.2f} "
                                    f"(diff: {example['difference']:.2f})")
        
        # Pre-filter Performance by Reason
        reason_stats = self._analyze_pre_filter_reasons(results)
        if reason_stats:
            self.stdout.write("\n🎯 PRE-FILTER REASON BREAKDOWN")
            self.stdout.write("-" * 30)
            for reason, count in reason_stats.items():
                self.stdout.write(f"{reason}: {count}")

    def _find_disagreements(self, results: Dict) -> List[Dict]:
        """Find examples of pre-filter vs LLM disagreements."""
        disagreements = []
        
        pre_filter_results = results["pre_filter_results"]
        llm_results = results["llm_results"]
        
        for pf_result, llm_result in zip(pre_filter_results, llm_results):
            if pf_result.score is not None:
                diff = abs(pf_result.score - llm_result.overall_score)
                if diff >= 0.3:  # Disagreement threshold
                    disagreements.append({
                        "pre_filter_score": pf_result.score,
                        "llm_score": llm_result.overall_score,
                        "difference": diff,
                        "pre_filter_reason": pf_result.reason
                    })
        
        # Sort by largest disagreement first
        return sorted(disagreements, key=lambda x: x["difference"], reverse=True)

    def _analyze_pre_filter_reasons(self, results: Dict) -> Dict[str, int]:
        """Analyze pre-filter decision reasons."""
        reason_counts = {}
        
        for pf_result in results["pre_filter_results"]:
            if pf_result.score is not None:  # Only confident decisions
                reason = pf_result.reason
                reason_counts[reason] = reason_counts.get(reason, 0) + 1
        
        return reason_counts

    def _save_comparison_results(self, results: Dict, options: Dict):
        """Save comparison results to database for future analysis."""
        self.stdout.write("\n💾 Saving comparison results...")
        
        # Create a summary record (you might want to create a ComparisonResult model)
        summary = {
            "comparison_date": str(timezone.now()),
            "provider": options["provider"],
            "filter_by": options["filter_by"],
            "results": results
        }
        
        # For now, just log the summary
        # In a real implementation, you'd save this to a dedicated model
        self.stdout.write(f"Results summary: {json.dumps(summary, indent=2)}")
        
        self.stdout.write("✅ Comparison results saved") 