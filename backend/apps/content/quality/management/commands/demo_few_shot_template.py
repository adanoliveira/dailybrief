"""
Demo Few-Shot Template

Management command to demonstrate the new template-based few-shot 
example architecture and show how the FewShotExampleTemplate works.
"""
from django.core.management.base import BaseCommand
from apps.content.quality.models import ReferenceQualityExample
from apps.content.quality.prompt_templates import get_few_shot_template
from apps.content.quality.evaluator import ContentQualityEvaluator
import json


class Command(BaseCommand):
    help = 'Demonstrate the new template-based few-shot example architecture'

    def add_arguments(self, parser):
        parser.add_argument(
            '--example-id',
            type=str,
            help='Specific reference example public_id to demonstrate'
        )
        parser.add_argument(
            '--max-examples',
            type=int,
            default=2,
            help='Maximum number of examples to show per quality class'
        )
        parser.add_argument(
            '--show-template',
            action='store_true',
            help='Show the raw FewShotExampleTemplate structure'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🎯 Few-Shot Template Architecture Demo')
        )
        
        if options['show_template']:
            self._show_template_structure()
        
        if options['example_id']:
            self._demo_specific_example(options['example_id'])
        else:
            self._demo_template_hydration(options['max_examples'])

    def _show_template_structure(self):
        """Show the raw FewShotExampleTemplate structure."""
        self.stdout.write(f"\n{'='*60}")
        self.stdout.write(self.style.WARNING('📄 FewShotExampleTemplate Structure'))
        
        few_shot_template = get_few_shot_template()
        
        self.stdout.write(f"\n📝 Template ID: {few_shot_template.identifier}")
        self.stdout.write(f"📋 Name: {few_shot_template.metadata.name}")
        self.stdout.write(f"🔖 Version: {few_shot_template.metadata.version}")
        self.stdout.write(f"📄 Description: {few_shot_template.metadata.description}")
        
        self.stdout.write(f"\n🏗️  Raw Template Structure:")
        self.stdout.write("-" * 40)
        self.stdout.write(few_shot_template.template_text)
        self.stdout.write("-" * 40)
        
        self.stdout.write(f"\n📊 Template Variables Required:")
        template_vars = [
            'example_id', 'title', 'author', 'description', 
            'content_blocks', 'blocks_count', 'metadata',
            'html_sample', 'html_length', 'expected_json_output'
        ]
        for var in template_vars:
            self.stdout.write(f"   • {{{var}}}")

    def _demo_specific_example(self, example_public_id: str):
        """Demonstrate template hydration with a specific example."""
        self.stdout.write(f"\n{'='*60}")
        self.stdout.write(
            self.style.WARNING(f'🔍 Template Hydration Demo: {example_public_id}')
        )
        
        try:
            example = ReferenceQualityExample.objects.get(public_id=example_public_id)
        except ReferenceQualityExample.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"❌ Reference example not found: {example_public_id}")
            )
            return
        
        # Use the evaluator's method to prepare template data
        evaluator = ContentQualityEvaluator()
        template_data = evaluator._prepare_few_shot_template_data(
            example, f"{example.quality_class.upper()}-DEMO", example.quality_class
        )
        
        self.stdout.write(f"\n📊 Template Data Prepared:")
        self.stdout.write(f"   📝 Example ID: {template_data['example_id']}")
        self.stdout.write(f"   📰 Title: {template_data['title'][:60]}...")
        self.stdout.write(f"   👤 Author: {template_data['author']}")
        self.stdout.write(f"   🧱 Blocks Count: {template_data['blocks_count']}")
        self.stdout.write(f"   🌐 HTML Length: {template_data['html_length']} chars")
        
        # Show the formatted result
        few_shot_template = get_few_shot_template()
        formatted_example = few_shot_template.format(**template_data)
        
        self.stdout.write(f"\n✨ Formatted Example (first 500 chars):")
        self.stdout.write("-" * 40)
        self.stdout.write(formatted_example[:500] + "...")
        self.stdout.write("-" * 40)
        
        self.stdout.write(f"\n📏 Total formatted length: {len(formatted_example):,} characters")

    def _demo_template_hydration(self, max_examples: int):
        """Demonstrate the complete template hydration process."""
        self.stdout.write(f"\n{'='*60}")
        self.stdout.write(
            self.style.WARNING('🏗️  Complete Template Hydration Process')
        )
        
        # Use the evaluator to generate examples (same as in production)
        evaluator = ContentQualityEvaluator()
        reference_examples = evaluator._prepare_reference_examples(max_per_class=max_examples)
        
        if "No reference examples available" in reference_examples:
            self.stdout.write(
                self.style.ERROR("❌ No reference examples available for demonstration")
            )
            return
        
        # Show summary statistics
        lines = reference_examples.split('\n')
        example_count = reference_examples.count('<example id=')
        total_chars = len(reference_examples)
        
        self.stdout.write(f"\n📊 Generation Summary:")
        self.stdout.write(f"   🎯 Examples generated: {example_count}")
        self.stdout.write(f"   📏 Total characters: {total_chars:,}")
        self.stdout.write(f"   📄 Total lines: {len(lines):,}")
        
        # Show the structure
        self.stdout.write(f"\n🏗️  Generated Structure:")
        structure_lines = [line for line in lines[:20] if line.strip()]
        for line in structure_lines:
            if line.startswith('<<<'):
                self.stdout.write(f"   🔖 {line}")
            elif line.startswith('<example'):
                self.stdout.write(f"   📝 {line}")
            elif line.startswith('<input>') or line.startswith('<expected_output>'):
                self.stdout.write(f"   📄 {line}")
        
        if len(lines) > 20:
            self.stdout.write(f"   ... ({len(lines) - 20} more lines)")
        
        # Show quality distribution from the comment
        comment_line = [line for line in lines if line.startswith('<!-- Reference examples:')]
        if comment_line:
            self.stdout.write(f"\n📈 {comment_line[0].replace('<!-- ', '').replace(' -->', '')}")
        
        self.stdout.write(f"\n✅ Template-based architecture working correctly!")
        self.stdout.write(f"   🎯 Clean separation: Template structure vs. data hydration")
        self.stdout.write(f"   🔄 Reusable: Same template across different main prompts")
        self.stdout.write(f"   🧪 Testable: Individual template components")
        self.stdout.write(f"   🔧 Maintainable: Easy to modify template format") 