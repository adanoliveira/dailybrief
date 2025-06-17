"""
Calibrate Quality Evaluator

Management command to test and calibrate the quality evaluator against
reference examples with known quality scores.
"""
from django.core.management.base import BaseCommand
from apps.content.quality.models import ReferenceQualityExample
from apps.content.quality.evaluator import ContentQualityEvaluator
import json
import statistics


class Command(BaseCommand):
    help = 'Calibrate quality evaluator against reference examples'

    def add_arguments(self, parser):
        parser.add_argument(
            '--quality-class',
            type=str,
            choices=['perfect', 'good', 'imperfect', 'awful'],
            help='Test only specific quality class'
        )
        parser.add_argument(
            '--model',
            type=str,
            default='gpt-4.1-mini',
            help='LLM model to use (default: gpt-4.1-mini)'
        )
        parser.add_argument(
            '--show-details',
            action='store_true',
            help='Show detailed comparison for each reference example'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🎯 Calibrating Quality Evaluator Against Reference Examples')
        )
        
        # Get reference examples
        if options['quality_class']:
            examples = ReferenceQualityExample.objects.filter(
                quality_class=options['quality_class'],
                use_for_calibration=True
            )
            self.stdout.write(f"📊 Testing {options['quality_class']} quality examples only")
        else:
            examples = ReferenceQualityExample.get_calibration_set()
            self.stdout.write(f"📊 Testing all quality classes")
        
        if not examples:
            self.stdout.write(
                self.style.ERROR('No reference examples found for calibration')
            )
            return
        
        self.stdout.write(f"📚 Found {len(examples)} reference examples")
        
        evaluator = ContentQualityEvaluator()
        results = []
        
        # Test each reference example
        for i, example in enumerate(examples, 1):
            self.stdout.write(f"\n{'='*60}")
            self.stdout.write(f"🧪 Testing {i}/{len(examples)}: {example.quality_class.upper()}")
            self.stdout.write(f"📰 {example.short_title}")
            self.stdout.write(f"🎯 Reference Score: {example.reference_overall_score:.3f}")
            
            try:
                # Evaluate the article
                result = evaluator.evaluate_article_quality(
                    example.article,
                    include_html=True,
                    model_override=options['model']
                )
                
                # Calculate differences
                score_diff = result.overall_score - example.reference_overall_score
                completeness_diff = result.completeness - example.reference_completeness
                purity_diff = result.purity - example.reference_purity
                structure_diff = result.structure - example.reference_structure
                readability_diff = result.readability - example.reference_readability
                
                # Store results
                test_result = {
                    'example': example,
                    'evaluation': result,
                    'score_diff': score_diff,
                    'completeness_diff': completeness_diff,
                    'purity_diff': purity_diff,
                    'structure_diff': structure_diff,
                    'readability_diff': readability_diff,
                    'abs_score_diff': abs(score_diff),
                    'quality_class': example.quality_class
                }
                results.append(test_result)
                
                # Display results
                self.stdout.write(f"📊 Evaluated Score: {result.overall_score:.3f}")
                self.stdout.write(f"📈 Difference: {score_diff:+.3f}")
                
                if abs(score_diff) <= 0.1:
                    self.stdout.write(self.style.SUCCESS(f"✅ Excellent calibration (±0.1)"))
                elif abs(score_diff) <= 0.2:
                    self.stdout.write(self.style.WARNING(f"⚠️ Good calibration (±0.2)"))
                else:
                    self.stdout.write(self.style.ERROR(f"❌ Poor calibration (>{score_diff:.3f})"))
                
                if options['show_details']:
                    self.stdout.write(f"   📝 Completeness: {result.completeness:.3f} (ref: {example.reference_completeness:.3f}, diff: {completeness_diff:+.3f})")
                    self.stdout.write(f"   🧹 Purity: {result.purity:.3f} (ref: {example.reference_purity:.3f}, diff: {purity_diff:+.3f})")
                    self.stdout.write(f"   🏗️ Structure: {result.structure:.3f} (ref: {example.reference_structure:.3f}, diff: {structure_diff:+.3f})")
                    self.stdout.write(f"   📖 Readability: {result.readability:.3f} (ref: {example.reference_readability:.3f}, diff: {readability_diff:+.3f})")
                    self.stdout.write(f"   🎯 Confidence: {result.confidence:.3f}")
                    self.stdout.write(f"   💰 Cost: ${result.cost_usd:.6f}")
                    self.stdout.write(f"   ⏱️ Time: {result.evaluation_time:.2f}s")
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"❌ Evaluation failed: {e}")
                )
                continue
        
        # Calibration Analysis
        if results:
            self.stdout.write(f"\n{'='*60}")
            self.stdout.write(self.style.SUCCESS('📊 CALIBRATION ANALYSIS'))
            
            # Overall statistics
            score_diffs = [r['score_diff'] for r in results]
            abs_score_diffs = [r['abs_score_diff'] for r in results]
            
            mean_diff = statistics.mean(score_diffs)
            mean_abs_diff = statistics.mean(abs_score_diffs)
            median_abs_diff = statistics.median(abs_score_diffs)
            max_diff = max(abs_score_diffs)
            
            self.stdout.write(f"\n📈 Overall Calibration Performance:")
            self.stdout.write(f"   📊 Mean Difference: {mean_diff:+.3f}")
            self.stdout.write(f"   📊 Mean Absolute Difference: {mean_abs_diff:.3f}")
            self.stdout.write(f"   📊 Median Absolute Difference: {median_abs_diff:.3f}")
            self.stdout.write(f"   📊 Maximum Difference: {max_diff:.3f}")
            
            # Accuracy by tolerance
            excellent_count = sum(1 for r in results if r['abs_score_diff'] <= 0.1)
            good_count = sum(1 for r in results if r['abs_score_diff'] <= 0.2)
            acceptable_count = sum(1 for r in results if r['abs_score_diff'] <= 0.3)
            
            self.stdout.write(f"\n🎯 Calibration Accuracy:")
            self.stdout.write(f"   ✅ Excellent (±0.1): {excellent_count}/{len(results)} ({excellent_count/len(results)*100:.1f}%)")
            self.stdout.write(f"   ⚠️ Good (±0.2): {good_count}/{len(results)} ({good_count/len(results)*100:.1f}%)")
            self.stdout.write(f"   📊 Acceptable (±0.3): {acceptable_count}/{len(results)} ({acceptable_count/len(results)*100:.1f}%)")
            
            # Performance by quality class
            quality_classes = ['perfect', 'good', 'imperfect', 'awful']
            self.stdout.write(f"\n📋 Performance by Quality Class:")
            for quality_class in quality_classes:
                class_results = [r for r in results if r['quality_class'] == quality_class]
                if class_results:
                    class_mean_abs_diff = statistics.mean([r['abs_score_diff'] for r in class_results])
                    class_excellent = sum(1 for r in class_results if r['abs_score_diff'] <= 0.1)
                    self.stdout.write(f"   📝 {quality_class.title()}: {len(class_results)} examples, MAD: {class_mean_abs_diff:.3f}, Excellent: {class_excellent}/{len(class_results)}")
            
            # Best and worst performers
            best_result = min(results, key=lambda r: r['abs_score_diff'])
            worst_result = max(results, key=lambda r: r['abs_score_diff'])
            
            self.stdout.write(f"\n🏆 Best Calibration:")
            self.stdout.write(f"   📰 {best_result['example'].short_title}")
            self.stdout.write(f"   📊 Difference: {best_result['score_diff']:+.3f}")
            
            self.stdout.write(f"\n⚠️ Worst Calibration:")
            self.stdout.write(f"   📰 {worst_result['example'].short_title}")
            self.stdout.write(f"   📊 Difference: {worst_result['score_diff']:+.3f}")
            
            # Calibration rating
            if mean_abs_diff <= 0.1:
                calibration_rating = "EXCELLENT"
                rating_style = self.style.SUCCESS
            elif mean_abs_diff <= 0.2:
                calibration_rating = "GOOD"
                rating_style = self.style.WARNING
            elif mean_abs_diff <= 0.3:
                calibration_rating = "ACCEPTABLE"
                rating_style = self.style.WARNING
            else:
                calibration_rating = "POOR"
                rating_style = self.style.ERROR
            
            self.stdout.write(f"\n🎯 Overall Calibration Rating: {rating_style(calibration_rating)}")
            
            # Recommendations
            self.stdout.write(f"\n💡 Recommendations:")
            if mean_abs_diff <= 0.15:
                self.stdout.write(f"   ✅ Quality evaluator is well-calibrated for production use")
            else:
                self.stdout.write(f"   ⚠️ Consider adjusting evaluation criteria or adding more reference examples")
                
            if max_diff > 0.5:
                self.stdout.write(f"   ⚠️ Large outliers detected - review worst performing examples")
        
        self.stdout.write(f"\n✅ Quality evaluator calibration completed!") 