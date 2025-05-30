"""
Management command to benchmark content quality assessment performance.

This command provides comprehensive quality benchmarking including:
- Performance metrics (speed, cost, accuracy)
- Quality distribution analysis
- Provider comparison
- Pipeline optimization recommendations

Usage:
    python manage.py quality_benchmark --articles 100 --provider openai
    python manage.py quality_benchmark --all --compare-providers
    python manage.py quality_benchmark --speed-test --iterations 10
"""
import asyncio
import time
import statistics
from typing import Dict, List, Tuple
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Avg, Count, Q
from django.utils import timezone

from apps.articles.models import Article
from apps.content.quality.optimized_service import OptimizedQualityService
from apps.content.quality.evaluator import ContentQualityEvaluator
from apps.content.quality.pre_filter import SmartPreFilter
from apps.content.quality.models import QualityScoring


class Command(BaseCommand):
    help = "Benchmark content quality assessment performance and generate reports"

    def add_arguments(self, parser):
        parser.add_argument(
            "--articles",
            type=int,
            default=50,
            help="Number of articles to benchmark (default: 50)"
        )
        parser.add_argument(
            "--all",
            action="store_true",
            help="Benchmark all available articles"
        )
        parser.add_argument(
            "--provider",
            type=str,
            default="openai",
            choices=["openai", "anthropic"],
            help="AI provider for benchmarking"
        )
        parser.add_argument(
            "--compare-providers",
            action="store_true",
            help="Compare different AI providers"
        )
        parser.add_argument(
            "--speed-test",
            action="store_true",
            help="Run speed benchmarks"
        )
        parser.add_argument(
            "--iterations",
            type=int,
            default=5,
            help="Number of iterations for speed tests"
        )
        parser.add_argument(
            "--analyze-existing",
            action="store_true",
            help="Analyze existing quality scores in database"
        )

    def handle(self, *args, **options):
        """Execute the quality benchmarking."""
        self.stdout.write("🚀 Starting Quality Assessment Benchmarking")
        
        if options["analyze_existing"]:
            self._analyze_existing_scores()
            return
        
        # Get articles for benchmarking
        articles = self._get_benchmark_articles(
            limit=options["articles"],
            all_articles=options["all"]
        )
        
        if not articles:
            raise CommandError("No articles found for benchmarking")
        
        self.stdout.write(f"📊 Benchmarking {len(articles)} articles")
        
        # Run different benchmark types based on options
        if options["speed_test"]:
            asyncio.run(self._run_speed_benchmark(articles, options))
        
        if options["compare_providers"]:
            asyncio.run(self._run_provider_comparison(articles))
        else:
            asyncio.run(self._run_standard_benchmark(articles, options["provider"]))
        
        self.stdout.write(
            self.style.SUCCESS("✅ Benchmarking completed successfully")
        )

    def _get_benchmark_articles(
        self, 
        limit: int, 
        all_articles: bool
    ) -> List[Article]:
        """Get articles for benchmarking."""
        queryset = Article.objects.exclude(
            Q(content__isnull=True) | Q(content="")
        ).order_by("-published_at")
        
        if not all_articles:
            queryset = queryset[:limit]
        
        return list(queryset)

    async def _run_standard_benchmark(
        self, 
        articles: List[Article], 
        provider: str
    ):
        """Run standard benchmarking with single provider."""
        self.stdout.write(f"\n🎯 Standard Benchmark (Provider: {provider})")
        self.stdout.write("=" * 50)
        
        service = OptimizedQualityService()
        results = []
        
        start_time = time.time()
        
        for i, article in enumerate(articles):
            self.stdout.write(f"Processing {i+1}/{len(articles)}: {article.title[:50]}...")
            
            result = await service.assess_article_quality(article, provider=provider)
            results.append(result)
        
        total_time = time.time() - start_time
        
        # Analyze results
        self._analyze_benchmark_results(results, total_time, provider)
        
        # Show optimization stats
        stats = service.get_optimization_stats()
        self._display_optimization_stats(stats)

    async def _run_provider_comparison(self, articles: List[Article]):
        """Compare different AI providers."""
        self.stdout.write("\n🔄 Provider Comparison Benchmark")
        self.stdout.write("=" * 50)
        
        providers = ["openai", "anthropic"]
        provider_results = {}
        
        for provider in providers:
            self.stdout.write(f"\n📡 Testing {provider.upper()}...")
            
            service = OptimizedQualityService()
            results = []
            
            start_time = time.time()
            
            # Test subset for provider comparison (to avoid high costs)
            test_articles = articles[:10]
            
            for article in test_articles:
                try:
                    result = await service.assess_article_quality(
                        article, 
                        provider=provider,
                        force_llm=True  # Force LLM for fair comparison
                    )
                    results.append(result)
                except Exception as e:
                    self.stdout.write(f"Error with {provider}: {e}")
                    continue
            
            total_time = time.time() - start_time
            provider_results[provider] = {
                "results": results,
                "total_time": total_time,
                "avg_time": total_time / len(results) if results else 0
            }
        
        self._compare_providers(provider_results)

    async def _run_speed_benchmark(
        self, 
        articles: List[Article], 
        options: Dict
    ):
        """Run speed benchmarking tests."""
        self.stdout.write("\n⚡ Speed Benchmark")
        self.stdout.write("=" * 50)
        
        test_article = articles[0]  # Use first article for speed tests
        iterations = options["iterations"]
        provider = options["provider"]
        
        # Benchmark different components
        components = {
            "pre_filter": self._benchmark_pre_filter,
            "llm_evaluation": self._benchmark_llm_evaluation,
            "optimized_service": self._benchmark_optimized_service
        }
        
        for component_name, benchmark_func in components.items():
            self.stdout.write(f"\n🔥 Benchmarking {component_name}...")
            
            times = []
            for i in range(iterations):
                execution_time = await benchmark_func(test_article, provider)
                times.append(execution_time)
                self.stdout.write(f"  Iteration {i+1}: {execution_time:.3f}s")
            
            # Calculate statistics
            avg_time = statistics.mean(times)
            median_time = statistics.median(times)
            min_time = min(times)
            max_time = max(times)
            
            self.stdout.write(f"\n📈 {component_name.upper()} STATS:")
            self.stdout.write(f"  Average: {avg_time:.3f}s")
            self.stdout.write(f"  Median:  {median_time:.3f}s")
            self.stdout.write(f"  Min:     {min_time:.3f}s")
            self.stdout.write(f"  Max:     {max_time:.3f}s")

    async def _benchmark_pre_filter(self, article: Article, provider: str) -> float:
        """Benchmark pre-filter performance."""
        pre_filter = SmartPreFilter()
        
        start_time = time.time()
        result = pre_filter.quick_quality_assessment(article)
        end_time = time.time()
        
        return end_time - start_time

    async def _benchmark_llm_evaluation(self, article: Article, provider: str) -> float:
        """Benchmark LLM evaluation performance."""
        evaluator = ContentQualityEvaluator()
        
        start_time = time.time()
        result = await evaluator.evaluate_article(article, provider)
        end_time = time.time()
        
        return end_time - start_time

    async def _benchmark_optimized_service(self, article: Article, provider: str) -> float:
        """Benchmark optimized service performance."""
        service = OptimizedQualityService()
        
        start_time = time.time()
        result = await service.assess_article_quality(article, provider=provider)
        end_time = time.time()
        
        return end_time - start_time

    def _analyze_benchmark_results(
        self, 
        results: List, 
        total_time: float, 
        provider: str
    ):
        """Analyze and display benchmark results."""
        if not results:
            self.stdout.write("No results to analyze")
            return
        
        # Extract scores
        scores = [r.quality_score for r in results]
        processing_times = [r.processing_time_ms for r in results]
        
        # Calculate statistics
        avg_score = statistics.mean(scores)
        median_score = statistics.median(scores)
        score_std = statistics.stdev(scores) if len(scores) > 1 else 0
        
        avg_processing_time = statistics.mean(processing_times)
        
        # Count by assessment method
        pre_filter_count = sum(1 for r in results if r.assessment_method == "pre_filter")
        llm_count = sum(1 for r in results if r.assessment_method == "llm_evaluation")
        
        # Display results
        self.stdout.write(f"\n📊 BENCHMARK RESULTS ({provider.upper()})")
        self.stdout.write("-" * 40)
        self.stdout.write(f"Total Articles: {len(results)}")
        self.stdout.write(f"Total Time: {total_time:.2f}s")
        self.stdout.write(f"Avg Time per Article: {total_time/len(results):.3f}s")
        
        self.stdout.write(f"\n📈 QUALITY SCORES:")
        self.stdout.write(f"  Average: {avg_score:.3f}")
        self.stdout.write(f"  Median:  {median_score:.3f}")
        self.stdout.write(f"  Std Dev: {score_std:.3f}")
        self.stdout.write(f"  Range:   {min(scores):.3f} to {max(scores):.3f}")
        
        self.stdout.write(f"\n⚡ PROCESSING:")
        self.stdout.write(f"  Pre-filter decisions: {pre_filter_count}")
        self.stdout.write(f"  LLM evaluations: {llm_count}")
        self.stdout.write(f"  Avg processing time: {avg_processing_time:.0f}ms")

    def _compare_providers(self, provider_results: Dict):
        """Compare results across different providers."""
        self.stdout.write(f"\n🏆 PROVIDER COMPARISON")
        self.stdout.write("=" * 50)
        
        for provider, data in provider_results.items():
            results = data["results"]
            if not results:
                continue
            
            scores = [r.quality_score for r in results]
            avg_score = statistics.mean(scores)
            avg_time = data["avg_time"]
            
            self.stdout.write(f"\n📡 {provider.upper()}:")
            self.stdout.write(f"  Articles processed: {len(results)}")
            self.stdout.write(f"  Average score: {avg_score:.3f}")
            self.stdout.write(f"  Average time: {avg_time:.3f}s")
            self.stdout.write(f"  Score range: {min(scores):.3f} to {max(scores):.3f}")

    def _display_optimization_stats(self, stats: Dict):
        """Display optimization statistics."""
        self.stdout.write(f"\n💰 OPTIMIZATION STATS")
        self.stdout.write("-" * 30)
        self.stdout.write(f"Total assessments: {stats['total_assessments']}")
        self.stdout.write(f"Pre-filter rate: {stats['pre_filter_rate']:.1%}")
        self.stdout.write(f"Cost savings: {stats['cost_savings_percentage']:.1f}%")
        self.stdout.write(f"Estimated savings: ${stats['savings_usd']:.4f}")

    def _analyze_existing_scores(self):
        """Analyze existing quality scores in the database."""
        self.stdout.write("\n📊 Analyzing Existing Quality Scores")
        self.stdout.write("=" * 50)
        
        # Get basic statistics
        total_scores = QualityScoring.objects.count()
        
        if total_scores == 0:
            self.stdout.write("No quality scores found in database")
            return
        
        # Score distribution
        score_stats = QualityScoring.objects.aggregate(
            avg_score=Avg('overall_score'),
            count=Count('id')
        )
        
        # Method breakdown
        method_breakdown = QualityScoring.objects.values('assessment_method').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Cost optimization stats
        cost_optimized = QualityScoring.objects.filter(cost_optimized=True).count()
        optimization_rate = (cost_optimized / total_scores) * 100 if total_scores > 0 else 0
        
        # Display results
        self.stdout.write(f"Total Quality Assessments: {total_scores}")
        self.stdout.write(f"Average Quality Score: {score_stats['avg_score']:.3f}")
        self.stdout.write(f"Cost Optimization Rate: {optimization_rate:.1f}%")
        
        self.stdout.write(f"\n📈 Assessment Method Breakdown:")
        for method in method_breakdown:
            percentage = (method['count'] / total_scores) * 100
            self.stdout.write(f"  {method['assessment_method']}: {method['count']} ({percentage:.1f}%)")
        
        # Quality distribution
        score_ranges = [
            ("Excellent (0.7 to 1.0)", Q(overall_score__gte=0.7)),
            ("Good (0.3 to 0.7)", Q(overall_score__gte=0.3, overall_score__lt=0.7)),
            ("Poor (0.0 to 0.3)", Q(overall_score__gte=0.0, overall_score__lt=0.3)),
            ("Very Poor (-1.0 to 0.0)", Q(overall_score__lt=0.0))
        ]
        
        self.stdout.write(f"\n🎯 Quality Distribution:")
        for range_name, query in score_ranges:
            count = QualityScoring.objects.filter(query).count()
            percentage = (count / total_scores) * 100 if total_scores > 0 else 0
            self.stdout.write(f"  {range_name}: {count} ({percentage:.1f}%)") 