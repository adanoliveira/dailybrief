"""
Compare Prompt Templates Against Reference Examples

This command evaluates both available prompt templates against reference examples
to determine which template produces outputs closer to the expected reference scores.
"""
import json
import time
from typing import Dict, List, Tuple, Any
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

from apps.articles.models import Article
from apps.content.quality.models import ReferenceQualityExample
from apps.content.quality.evaluator import ContentQualityEvaluator
from apps.content.quality.prompt_templates import list_templates


class Command(BaseCommand):
    help = 'Compare prompt templates against reference examples to measure accuracy'

    def add_arguments(self, parser):
        parser.add_argument(
            '--max-examples',
            type=int,
            default=5,
            help='Maximum number of reference examples to test (default: 5)'
        )
        parser.add_argument(
            '--model',
            type=str,
            default='gpt-4.1-mini',
            help='Override AI model for testing (default: gpt-4.1-mini for large context)'
        )
        parser.add_argument(
            '--quality-class',
            type=str,
            choices=['perfect', 'good', 'imperfect', 'awful'],
            help='Test only examples from specific quality class'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed comparison results'
        )
        parser.add_argument(
            '--by-class',
            action='store_true',
            help='Run comprehensive analysis by quality class (tests all examples per class)'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🔬 Comparing Prompt Templates Against Reference Examples')
        )
        
        # Get available templates (excluding few-shot template)
        templates = list_templates()
        main_templates = {
            tid: meta for tid, meta in templates.items() 
            if not tid.startswith('few_shot_')
        }
        
        if len(main_templates) < 2:
            raise CommandError(f"Need at least 2 templates to compare. Found: {list(main_templates.keys())}")
        
        self.stdout.write(f"📋 Found {len(main_templates)} templates to compare:")
        for tid, meta in main_templates.items():
            baseline_indicator = " 🎯 BASELINE" if meta.is_baseline else ""
            self.stdout.write(f"   📝 {tid}: {meta.description}{baseline_indicator}")
        
        # Get reference examples
        reference_examples = self._get_reference_examples(options)
        if not reference_examples:
            raise CommandError("No reference examples found")
        
        if options['by_class']:
            # Run comprehensive by-class analysis
            self._run_by_class_analysis(main_templates, options)
        else:
            # Standard comparison
            self.stdout.write(f"🎯 Testing against {len(reference_examples)} reference examples")
            
            # Run comparison
            results = self._run_comparison(main_templates, reference_examples, options)
            
            # Display results
            self._display_results(results, options)

    def _get_reference_examples(self, options) -> List['ReferenceQualityExample']:
        """Get reference examples for testing."""
        queryset = ReferenceQualityExample.objects.filter(
            use_in_prompts=True,
            article__raw_html__isnull=False,
            article__raw_html__gt=''
        )
        
        if options['quality_class']:
            queryset = queryset.filter(quality_class=options['quality_class'])
        
        # Get diverse examples across quality classes
        examples = list(queryset.order_by('quality_class', 'id')[:options['max_examples']])
        
        return examples

    def _run_comparison(
        self, 
        templates: Dict[str, Any], 
        reference_examples: List['ReferenceQualityExample'],
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run template comparison against reference examples."""
        
        results = {
            'template_results': {},
            'example_details': [],
            'summary': {}
        }
        
        # Initialize results for each template
        for template_id in templates.keys():
            results['template_results'][template_id] = {
                'scores': [],
                'accuracy_metrics': {
                    'completeness_mae': 0.0,  # Mean Absolute Error
                    'purity_mae': 0.0,
                    'structure_mae': 0.0,
                    'readability_mae': 0.0,
                    'overall_mae': 0.0,
                    'total_mae': 0.0
                },
                'evaluation_times': [],
                'errors': []
            }
        
        # Test each reference example
        for i, ref_example in enumerate(reference_examples, 1):
            self.stdout.write(f"\n📊 Testing Example {i}/{len(reference_examples)}: {ref_example.quality_class.upper()}")
            self.stdout.write(f"   📰 {ref_example.article.title[:80]}...")
            
            example_result = {
                'reference_example': ref_example,
                'template_outputs': {}
            }
            
            # Test each template against this example
            for template_id in templates.keys():
                self.stdout.write(f"   🔄 Testing template: {template_id}")
                
                try:
                    # Run evaluation with this template
                    start_time = time.time()
                    evaluator = ContentQualityEvaluator(template_id=template_id)
                    result = evaluator.evaluate_article_quality(
                        ref_example.article,
                        include_html=True,
                        model_override=options['model']
                    )
                    evaluation_time = time.time() - start_time
                    
                    # Calculate accuracy metrics
                    accuracy = self._calculate_accuracy(ref_example, result)
                    
                    # Store results
                    template_results = results['template_results'][template_id]
                    template_results['scores'].append(accuracy)
                    template_results['evaluation_times'].append(evaluation_time)
                    
                    example_result['template_outputs'][template_id] = {
                        'result': result,
                        'accuracy': accuracy,
                        'evaluation_time': evaluation_time
                    }
                    
                    # Show brief accuracy summary
                    self.stdout.write(f"      ✅ Overall MAE: {accuracy['overall_mae']:.3f}, Total MAE: {accuracy['total_mae']:.3f}")
                    
                    # Delay to avoid rate limits (longer for gpt-4.1 models)
                    if 'gpt-4.1' in options['model']:
                        time.sleep(5)  # Longer delay for gpt-4.1 models
                    else:
                        time.sleep(2)  # Shorter delay for other models
                    
                except Exception as e:
                    error_msg = f"Template {template_id} failed: {e}"
                    self.stdout.write(f"      ❌ {error_msg}")
                    results['template_results'][template_id]['errors'].append(error_msg)
            
            results['example_details'].append(example_result)
        
        # Calculate summary metrics
        self._calculate_summary_metrics(results)
        
        return results

    def _calculate_accuracy(
        self, 
        ref_example: 'ReferenceQualityExample', 
        result: Any
    ) -> Dict[str, float]:
        """Calculate accuracy metrics comparing actual vs expected scores."""
        
        # Mean Absolute Error for each dimension
        completeness_mae = abs(result.completeness - ref_example.reference_completeness)
        purity_mae = abs(result.purity - ref_example.reference_purity)
        structure_mae = abs(result.structure - ref_example.reference_structure)
        readability_mae = abs(result.readability - ref_example.reference_readability)
        overall_mae = abs(result.overall_score - ref_example.reference_overall_score)
        
        # Total MAE (average across all dimensions)
        total_mae = (completeness_mae + purity_mae + structure_mae + readability_mae + overall_mae) / 5
        
        return {
            'completeness_mae': completeness_mae,
            'purity_mae': purity_mae,
            'structure_mae': structure_mae,
            'readability_mae': readability_mae,
            'overall_mae': overall_mae,
            'total_mae': total_mae,
            'expected_scores': {
                'completeness': ref_example.reference_completeness,
                'purity': ref_example.reference_purity,
                'structure': ref_example.reference_structure,
                'readability': ref_example.reference_readability,
                'overall': ref_example.reference_overall_score
            },
            'actual_scores': {
                'completeness': result.completeness,
                'purity': result.purity,
                'structure': result.structure,
                'readability': result.readability,
                'overall': result.overall_score
            }
        }

    def _calculate_summary_metrics(self, results: Dict[str, Any]):
        """Calculate summary metrics across all examples."""
        
        for template_id, template_data in results['template_results'].items():
            scores = template_data['scores']
            
            if not scores:
                continue
            
            # Calculate average MAE across all examples
            metrics = template_data['accuracy_metrics']
            metrics['completeness_mae'] = sum(s['completeness_mae'] for s in scores) / len(scores)
            metrics['purity_mae'] = sum(s['purity_mae'] for s in scores) / len(scores)
            metrics['structure_mae'] = sum(s['structure_mae'] for s in scores) / len(scores)
            metrics['readability_mae'] = sum(s['readability_mae'] for s in scores) / len(scores)
            metrics['overall_mae'] = sum(s['overall_mae'] for s in scores) / len(scores)
            metrics['total_mae'] = sum(s['total_mae'] for s in scores) / len(scores)
            
            # Calculate average evaluation time
            times = template_data['evaluation_times']
            avg_time = sum(times) / len(times) if times else 0.0
            template_data['avg_evaluation_time'] = avg_time

    def _display_results(self, results: Dict[str, Any], options: Dict[str, Any]):
        """Display comparison results."""
        
        self.stdout.write(f"\n{'='*80}")
        self.stdout.write(self.style.SUCCESS('📊 TEMPLATE COMPARISON RESULTS'))
        self.stdout.write(f"{'='*80}")
        
        # Sort templates by total MAE (lower is better)
        template_results = results['template_results']
        sorted_templates = sorted(
            template_results.items(),
            key=lambda x: x[1]['accuracy_metrics']['total_mae']
        )
        
        self.stdout.write(f"\n🏆 ACCURACY RANKING (Lower MAE = Better):")
        self.stdout.write(f"{'Rank':<4} {'Template':<40} {'Total MAE':<10} {'Overall MAE':<12} {'Time (s)':<10}")
        self.stdout.write("-" * 80)
        
        for rank, (template_id, data) in enumerate(sorted_templates, 1):
            metrics = data['accuracy_metrics']
            avg_time = data.get('avg_evaluation_time', 0.0)
            error_count = len(data['errors'])
            
            rank_emoji = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else "  "
            error_indicator = f" ❌{error_count}" if error_count > 0 else ""
            
            self.stdout.write(
                f"{rank_emoji}{rank:<3} {template_id:<40} {metrics['total_mae']:<10.3f} "
                f"{metrics['overall_mae']:<12.3f} {avg_time:<10.2f}{error_indicator}"
            )
        
        # Detailed breakdown for best template
        if sorted_templates:
            best_template_id, best_data = sorted_templates[0]
            self.stdout.write(f"\n🎯 BEST TEMPLATE: {best_template_id}")
            self.stdout.write(f"📊 Detailed Metrics:")
            
            metrics = best_data['accuracy_metrics']
            self.stdout.write(f"   • Completeness MAE: {metrics['completeness_mae']:.3f}")
            self.stdout.write(f"   • Purity MAE:       {metrics['purity_mae']:.3f}")
            self.stdout.write(f"   • Structure MAE:    {metrics['structure_mae']:.3f}")
            self.stdout.write(f"   • Readability MAE:  {metrics['readability_mae']:.3f}")
            self.stdout.write(f"   • Overall MAE:      {metrics['overall_mae']:.3f}")
            self.stdout.write(f"   • Total MAE:        {metrics['total_mae']:.3f}")
        
        # Show detailed examples if verbose
        if options['verbose']:
            self._display_detailed_results(results)

    def _display_detailed_results(self, results: Dict[str, Any]):
        """Display detailed per-example results."""
        
        self.stdout.write(f"\n{'='*80}")
        self.stdout.write("📋 DETAILED EXAMPLE RESULTS")
        self.stdout.write(f"{'='*80}")
        
        for i, example_detail in enumerate(results['example_details'], 1):
            ref_example = example_detail['reference_example']
            
            self.stdout.write(f"\n📰 Example {i}: {ref_example.quality_class.upper()}")
            self.stdout.write(f"   Title: {ref_example.article.title}")
            
            # Show expected scores
            self.stdout.write(f"   🎯 Expected Scores:")
            self.stdout.write(f"      Completeness: {ref_example.reference_completeness:.2f}")
            self.stdout.write(f"      Purity:       {ref_example.reference_purity:.2f}")
            self.stdout.write(f"      Structure:    {ref_example.reference_structure:.2f}")
            self.stdout.write(f"      Readability:  {ref_example.reference_readability:.2f}")
            self.stdout.write(f"      Overall:      {ref_example.reference_overall_score:.2f}")
            
            # Show template results
            for template_id, output in example_detail['template_outputs'].items():
                result = output['result']
                accuracy = output['accuracy']
                
                self.stdout.write(f"   📝 {template_id}:")
                self.stdout.write(f"      Actual Scores:  C:{result.completeness:.2f} P:{result.purity:.2f} S:{result.structure:.2f} R:{result.readability:.2f} O:{result.overall_score:.2f}")
                self.stdout.write(f"      MAE:           C:{accuracy['completeness_mae']:.3f} P:{accuracy['purity_mae']:.3f} S:{accuracy['structure_mae']:.3f} R:{accuracy['readability_mae']:.3f} O:{accuracy['overall_mae']:.3f}")
                self.stdout.write(f"      Total MAE:     {accuracy['total_mae']:.3f}")

    def _run_by_class_analysis(self, templates: Dict[str, Any], options: Dict[str, Any]):
        """Run comprehensive analysis by quality class."""
        
        # Define quality classes to analyze
        if options['quality_class']:
            quality_classes = [options['quality_class']]
        else:
            quality_classes = ['good', 'imperfect', 'awful']  # Default classes as requested
        
        overall_results = {}
        
        for quality_class in quality_classes:
            self.stdout.write(f"\n{'='*80}")
            self.stdout.write(self.style.SUCCESS(f'📊 ANALYZING QUALITY CLASS: {quality_class.upper()}'))
            self.stdout.write(f"{'='*80}")
            
            # Get all examples for this quality class
            examples = ReferenceQualityExample.objects.filter(
                quality_class=quality_class,
                use_in_prompts=True,
                article__raw_html__isnull=False,
                article__raw_html__gt=''
            ).order_by('id')
            
            if not examples:
                self.stdout.write(f"⚠️  No examples found for quality class: {quality_class}")
                continue
            
            self.stdout.write(f"🎯 Testing {len(examples)} {quality_class} examples")
            
            # Run comparison for this class
            class_results = self._run_comparison(templates, examples, options)
            overall_results[quality_class] = class_results
            
            # Display class-specific results
            self._display_class_results(quality_class, class_results, options)
        
        # Display overall summary
        self._display_overall_summary(overall_results, quality_classes)

    def _display_class_results(self, quality_class: str, results: Dict[str, Any], options: Dict[str, Any]):
        """Display results for a specific quality class."""
        
        self.stdout.write(f"\n🏆 {quality_class.upper()} CLASS RESULTS:")
        
        # Sort templates by total MAE for this class
        template_results = results['template_results']
        sorted_templates = sorted(
            template_results.items(),
            key=lambda x: x[1]['accuracy_metrics']['total_mae']
        )
        
        self.stdout.write(f"{'Rank':<4} {'Template':<40} {'Total MAE':<10} {'Examples':<10}")
        self.stdout.write("-" * 70)
        
        for rank, (template_id, data) in enumerate(sorted_templates, 1):
            metrics = data['accuracy_metrics']
            example_count = len(data['scores'])
            error_count = len(data['errors'])
            
            rank_emoji = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else "  "
            error_indicator = f" ❌{error_count}" if error_count > 0 else ""
            
            self.stdout.write(
                f"{rank_emoji}{rank:<3} {template_id:<40} {metrics['total_mae']:<10.3f} {example_count:<10}{error_indicator}"
            )
        
        # Show per-article details if verbose or if there are few examples
        if options['verbose'] or len(results['example_details']) <= 5:
            self.stdout.write(f"\n📋 DETAILED ARTICLE RESULTS:")
            
            for i, example_detail in enumerate(results['example_details'], 1):
                ref_example = example_detail['reference_example']
                
                self.stdout.write(f"\n   📰 Article {i}: {ref_example.article.title[:60]}...")
                self.stdout.write(f"      🎯 Expected: C:{ref_example.reference_completeness:.2f} P:{ref_example.reference_purity:.2f} S:{ref_example.reference_structure:.2f} R:{ref_example.reference_readability:.2f} O:{ref_example.reference_overall_score:.2f}")
                
                # Show each template's results
                for template_id, output in example_detail['template_outputs'].items():
                    result = output['result']
                    accuracy = output['accuracy']
                    
                    template_short = template_id.split('_')[-1] if '_' in template_id else template_id[:10]
                    self.stdout.write(f"      📝 {template_short}: C:{result.completeness:.2f} P:{result.purity:.2f} S:{result.structure:.2f} R:{result.readability:.2f} O:{result.overall_score:.2f} (MAE: {accuracy['total_mae']:.3f})")

    def _display_overall_summary(self, overall_results: Dict[str, Any], quality_classes: List[str]):
        """Display overall summary across all quality classes."""
        
        self.stdout.write(f"\n{'='*80}")
        self.stdout.write(self.style.SUCCESS('🎯 OVERALL SUMMARY ACROSS ALL CLASSES'))
        self.stdout.write(f"{'='*80}")
        
        # Calculate average performance across all classes
        template_averages = {}
        
        for quality_class in quality_classes:
            if quality_class not in overall_results:
                continue
                
            class_results = overall_results[quality_class]
            
            for template_id, data in class_results['template_results'].items():
                if template_id not in template_averages:
                    template_averages[template_id] = {
                        'total_maes': [],
                        'class_wins': 0,
                        'example_counts': []
                    }
                
                metrics = data['accuracy_metrics']
                template_averages[template_id]['total_maes'].append(metrics['total_mae'])
                template_averages[template_id]['example_counts'].append(len(data['scores']))
        
        # Determine winners for each class
        for quality_class in quality_classes:
            if quality_class not in overall_results:
                continue
                
            class_results = overall_results[quality_class]
            best_template = min(
                class_results['template_results'].items(),
                key=lambda x: x[1]['accuracy_metrics']['total_mae']
            )[0]
            
            template_averages[best_template]['class_wins'] += 1
        
        # Calculate overall averages
        for template_id, data in template_averages.items():
            if data['total_maes']:
                data['avg_total_mae'] = sum(data['total_maes']) / len(data['total_maes'])
                data['total_examples'] = sum(data['example_counts'])
        
        # Display summary table
        self.stdout.write(f"\n🏆 TEMPLATE PERFORMANCE SUMMARY:")
        self.stdout.write(f"{'Template':<40} {'Avg MAE':<10} {'Class Wins':<12} {'Total Examples':<15}")
        self.stdout.write("-" * 85)
        
        sorted_overall = sorted(
            template_averages.items(),
            key=lambda x: x[1].get('avg_total_mae', float('inf'))
        )
        
        for rank, (template_id, data) in enumerate(sorted_overall, 1):
            avg_mae = data.get('avg_total_mae', 0.0)
            class_wins = data['class_wins']
            total_examples = data.get('total_examples', 0)
            
            rank_emoji = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else "  "
            
            self.stdout.write(
                f"{rank_emoji}{template_id:<39} {avg_mae:<10.3f} {class_wins:<12} {total_examples:<15}"
            )
        
        # Show class-by-class breakdown
        self.stdout.write(f"\n📊 CLASS-BY-CLASS BREAKDOWN:")
        for quality_class in quality_classes:
            if quality_class not in overall_results:
                continue
                
            class_results = overall_results[quality_class]
            best_template = min(
                class_results['template_results'].items(),
                key=lambda x: x[1]['accuracy_metrics']['total_mae']
            )
            
            best_mae = best_template[1]['accuracy_metrics']['total_mae']
            example_count = len(class_results['example_details'])
            
            self.stdout.write(f"   🎯 {quality_class.upper()}: {best_template[0]} (MAE: {best_mae:.3f}, {example_count} examples)") 