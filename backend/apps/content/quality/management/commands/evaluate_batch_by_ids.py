"""
Evaluate Quality for Specific Article IDs

Management command to evaluate content quality for a specific batch of articles
identified by their database IDs. Useful for testing on specific article sets.

Usage:
    python manage.py evaluate_batch_by_ids --ids 15999,15997,15996 --model gpt-4o-mini
"""
import time
from typing import List

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

from apps.articles.models import Article
from apps.content.quality.evaluator import ContentQualityEvaluator


class Command(BaseCommand):
    help = "Evaluate content quality for specific articles by database ID"

    def add_arguments(self, parser):
        parser.add_argument(
            '--ids',
            type=str,
            required=True,
            help='Comma-separated list of article database IDs (e.g., "15999,15997,15996")'
        )
        parser.add_argument(
            '--model',
            type=str,
            default='gpt-4o-mini',
            help='AI model to use (default: gpt-4o-mini)'
        )
        parser.add_argument(
            '--template',
            type=str,
            help='Specific template to use (default: active template)'
        )
        parser.add_argument(
            '--delay',
            type=int,
            default=3,
            help='Delay between evaluations in seconds (default: 3)'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed evaluation results'
        )
        parser.add_argument(
            '--include-html',
            action='store_true',
            default=True,
            help='Include HTML in evaluation (default: True)'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🔬 Evaluating Specific Article Batch')
        )
        
        # Parse article IDs
        try:
            article_ids = [int(id_str.strip()) for id_str in options['ids'].split(',')]
        except ValueError:
            raise CommandError("Invalid article IDs format. Use comma-separated integers.")
        
        self.stdout.write(f"📋 Target Article IDs: {article_ids}")
        self.stdout.write(f"🤖 Model: {options['model']}")
        self.stdout.write(f"⏱️  Delay: {options['delay']}s between evaluations")
        
        # Get articles
        articles = self._get_articles(article_ids)
        
        if not articles:
            raise CommandError("No articles found with the provided IDs")
        
        found_ids = [article.id for article in articles]
        missing_ids = set(article_ids) - set(found_ids)
        
        if missing_ids:
            self.stdout.write(
                self.style.WARNING(f"⚠️  Missing articles: {sorted(missing_ids)}")
            )
        
        self.stdout.write(f"✅ Found {len(articles)} articles to evaluate")
        
        # Initialize evaluator
        evaluator = ContentQualityEvaluator(template_id=options.get('template'))
        
        # Evaluate articles
        results = []
        for i, article in enumerate(articles, 1):
            self.stdout.write(f"\n{'='*60}")
            self.stdout.write(f"📰 Article {i}/{len(articles)} (ID: {article.id})")
            self.stdout.write(f"📄 Title: {article.title}")
            self.stdout.write(f"🔗 URL: {article.url}")
            self.stdout.write(f"📊 Status: {article.process_status}")
            
            try:
                # Evaluate with specified model
                start_time = time.time()
                result = evaluator.evaluate_article_quality(
                    article,
                    include_html=options['include_html'],
                    model_override=options['model']
                )
                evaluation_time = time.time() - start_time
                
                # Store result
                results.append({
                    'article_id': article.id,
                    'article': article,
                    'result': result,
                    'evaluation_time': evaluation_time
                })
                
                # Display results
                self.stdout.write(f"⭐ Overall Score: {result.overall_score:.3f}")
                self.stdout.write(f"📊 Scores: C:{result.completeness:.3f} P:{result.purity:.3f} S:{result.structure:.3f} R:{result.readability:.3f}")
                self.stdout.write(f"🎯 Confidence: {result.confidence:.3f}")
                self.stdout.write(f"💰 Cost: ${result.cost_usd:.6f}")
                self.stdout.write(f"🔢 Tokens: {result.tokens_used:,}")
                self.stdout.write(f"⏱️  Time: {evaluation_time:.2f}s")
                
                if options['verbose']:
                    self.stdout.write(f"💭 Explanation: {result.explanation[:200]}...")
                    if result.missing_elements:
                        self.stdout.write(f"❌ Missing: {', '.join(result.missing_elements[:3])}")
                    if result.noise_detected:
                        self.stdout.write(f"🔊 Noise: {', '.join(result.noise_detected[:3])}")
                
                # Delay to avoid rate limits
                if i < len(articles):  # Don't delay after the last article
                    self.stdout.write(f"⏳ Waiting {options['delay']}s to avoid rate limits...")
                    time.sleep(options['delay'])
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"❌ Evaluation failed: {e}")
                )
                results.append({
                    'article_id': article.id,
                    'article': article,
                    'result': None,
                    'error': str(e),
                    'evaluation_time': 0
                })
                continue
        
        # Summary
        self._display_summary(results, options)

    def _get_articles(self, article_ids: List[int]) -> List[Article]:
        """Get articles by database IDs."""
        articles = Article.objects.filter(
            id__in=article_ids
        ).order_by('id')
        
        return list(articles)

    def _display_summary(self, results: List, options):
        """Display evaluation summary."""
        self.stdout.write(f"\n{'='*60}")
        self.stdout.write(self.style.SUCCESS('📊 BATCH EVALUATION SUMMARY'))
        self.stdout.write(f"{'='*60}")
        
        successful_results = [r for r in results if r.get('result')]
        failed_results = [r for r in results if not r.get('result')]
        
        if successful_results:
            # Calculate statistics
            scores = [r['result'].overall_score for r in successful_results]
            completeness_scores = [r['result'].completeness for r in successful_results]
            purity_scores = [r['result'].purity for r in successful_results]
            structure_scores = [r['result'].structure for r in successful_results]
            readability_scores = [r['result'].readability for r in successful_results]
            confidence_scores = [r['result'].confidence for r in successful_results]
            
            total_cost = sum(r['result'].cost_usd for r in successful_results)
            total_tokens = sum(r['result'].tokens_used for r in successful_results)
            total_time = sum(r['evaluation_time'] for r in successful_results)
            
            # Display statistics
            self.stdout.write(f"✅ Successful Evaluations: {len(successful_results)}")
            self.stdout.write(f"❌ Failed Evaluations: {len(failed_results)}")
            self.stdout.write(f"")
            self.stdout.write(f"📊 SCORE STATISTICS:")
            self.stdout.write(f"   Overall:     Avg={sum(scores)/len(scores):.3f}, Min={min(scores):.3f}, Max={max(scores):.3f}")
            self.stdout.write(f"   Completeness: Avg={sum(completeness_scores)/len(completeness_scores):.3f}, Min={min(completeness_scores):.3f}, Max={max(completeness_scores):.3f}")
            self.stdout.write(f"   Purity:      Avg={sum(purity_scores)/len(purity_scores):.3f}, Min={min(purity_scores):.3f}, Max={max(purity_scores):.3f}")
            self.stdout.write(f"   Structure:   Avg={sum(structure_scores)/len(structure_scores):.3f}, Min={min(structure_scores):.3f}, Max={max(structure_scores):.3f}")
            self.stdout.write(f"   Readability: Avg={sum(readability_scores)/len(readability_scores):.3f}, Min={min(readability_scores):.3f}, Max={max(readability_scores):.3f}")
            self.stdout.write(f"   Confidence:  Avg={sum(confidence_scores)/len(confidence_scores):.3f}, Min={min(confidence_scores):.3f}, Max={max(confidence_scores):.3f}")
            self.stdout.write(f"")
            self.stdout.write(f"💰 COST & PERFORMANCE:")
            self.stdout.write(f"   Total Cost: ${total_cost:.6f}")
            self.stdout.write(f"   Avg Cost/Article: ${total_cost/len(successful_results):.6f}")
            self.stdout.write(f"   Total Tokens: {total_tokens:,}")
            self.stdout.write(f"   Avg Tokens/Article: {total_tokens//len(successful_results):,}")
            self.stdout.write(f"   Total Time: {total_time:.2f}s")
            self.stdout.write(f"   Avg Time/Article: {total_time/len(successful_results):.2f}s")
            
            # Quality distribution
            excellent = len([s for s in scores if s >= 0.8])
            good = len([s for s in scores if 0.5 <= s < 0.8])
            fair = len([s for s in scores if 0.2 <= s < 0.5])
            poor = len([s for s in scores if -0.2 <= s < 0.2])
            failed = len([s for s in scores if s < -0.2])
            
            self.stdout.write(f"")
            self.stdout.write(f"🎯 QUALITY DISTRIBUTION:")
            self.stdout.write(f"   Excellent (≥0.8): {excellent} articles")
            self.stdout.write(f"   Good (0.5-0.8):   {good} articles")
            self.stdout.write(f"   Fair (0.2-0.5):   {fair} articles")
            self.stdout.write(f"   Poor (-0.2-0.2):  {poor} articles")
            self.stdout.write(f"   Failed (<-0.2):   {failed} articles")
        
        if failed_results:
            self.stdout.write(f"")
            self.stdout.write(f"❌ FAILED EVALUATIONS:")
            for result in failed_results:
                self.stdout.write(f"   Article {result['article_id']}: {result.get('error', 'Unknown error')}")
        
        self.stdout.write(f"\n🎉 Batch evaluation completed!") 