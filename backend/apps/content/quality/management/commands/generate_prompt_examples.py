"""
Generate Prompt Examples

Management command to generate and save examples of all available
prompt templates for quality evaluation.
"""
import os
from django.core.management.base import BaseCommand
from django.db.models import Q
from apps.articles.models import Article
from apps.content.quality.evaluator import ContentQualityEvaluator
from apps.content.quality.prompt_templates import list_templates


class Command(BaseCommand):
    help = 'Generate and save examples of all available prompt templates'

    def add_arguments(self, parser):
        parser.add_argument(
            '--article-id',
            type=str,
            help='Specific article public_id to use for examples'
        )
        parser.add_argument(
            '--output-dir',
            type=str,
            default=None,  # Will be set to management dir in handle()
            help='Directory to save prompt examples (default: management directory)'
        )
        parser.add_argument(
            '--prefix',
            type=str,
            default='prompt_example',
            help='Prefix for output files (default: prompt_example)'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🎨 Generating Prompt Template Examples')
        )
        
        # Set default output directory to the management folder
        if options['output_dir'] is None:
            # Get the management directory path relative to this command
            command_dir = os.path.dirname(os.path.abspath(__file__))
            management_dir = os.path.dirname(command_dir)  # Go up from commands/ to management/
            options['output_dir'] = management_dir
        
        # Get an article for demonstration
        if options['article_id']:
            try:
                article = Article.objects.get(public_id=options['article_id'])
            except Article.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"Article not found: {options['article_id']}")
                )
                return
        else:
            # Get a sample article with good content
            article = Article.objects.filter(
                Q(clean_content__isnull=False) & 
                Q(clean_content__gt='') &
                Q(raw_html__isnull=False) &
                Q(raw_html__gt='')
            ).order_by('-updated_at').first()
            
            if not article:
                self.stdout.write(
                    self.style.ERROR('No suitable articles found for demonstration')
                )
                return
        
        self.stdout.write(f"📰 Using Article: {article.title[:60]}...")
        self.stdout.write(f"🔗 URL: {article.url}")
        
        # Get all available templates
        templates = list_templates()
        
        # Filter out component templates that aren't meant to be standalone prompts
        main_templates = {
            template_id: metadata 
            for template_id, metadata in templates.items() 
            if template_id not in ['few_shot_example_v1.0']  # Skip component templates
        }
        
        self.stdout.write(f"📋 Found {len(main_templates)} main templates:")
        
        for template_id, metadata in main_templates.items():
            self.stdout.write(f"   📝 {template_id}: {metadata.description}")
        
        output_dir = options['output_dir']
        prefix = options['prefix']
        generated_files = []
        
        self.stdout.write(f"📁 Saving files to: {os.path.abspath(output_dir)}")
        
        # Generate example for each main template
        for template_id, metadata in main_templates.items():
            self.stdout.write(f"\n{'='*60}")
            self.stdout.write(f"🎯 Generating example for: {template_id}")
            
            try:
                # Initialize evaluator with specific template
                evaluator = ContentQualityEvaluator(template_id=template_id)
                
                # Prepare all the content data (same as in evaluation)
                extracted_content = evaluator._prepare_extracted_content(article)
                html_data = evaluator._prepare_html_sample(
                    article, 
                    include_html=True,
                    use_preprocessing=True
                )
                reference_examples = evaluator._prepare_reference_examples()
                
                # Generate the complete prompt
                prompt = evaluator.template.format(
                    title=extracted_content["title"],
                    author=extracted_content["author"],
                    description=extracted_content["description"],
                    blocks_count=extracted_content["blocks_count"],
                    blocks_sample=extracted_content["blocks_sample"],
                    metadata=extracted_content["metadata"],
                    html_length=html_data["html_length"],
                    html_sample=html_data["html_sample"],
                    reference_examples=reference_examples
                )
                
                # Calculate statistics
                prompt_lines = prompt.count('\n')
                prompt_chars = len(prompt)
                prompt_tokens_est = prompt_chars // 4  # Rough token estimation
                blocks_count = extracted_content["blocks_count"]
                
                # Create filename
                safe_template_id = template_id.replace('_', '-').replace('.', '-')
                filename = f"{prefix}_{safe_template_id}.txt"
                filepath = os.path.join(output_dir, filename)
                
                # Check if file exists and will be overwritten
                file_exists = os.path.exists(filepath)
                if file_exists:
                    self.stdout.write(f"   🔄 Overwriting existing: {filename}")
                else:
                    self.stdout.write(f"   📝 Creating new: {filename}")
                
                # Save to file
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(f"# Quality Evaluation Prompt Example\n")
                    f.write(f"# Template: {template_id}\n")
                    f.write(f"# Name: {metadata.name}\n")
                    f.write(f"# Version: {metadata.version}\n")
                    f.write(f"# Description: {metadata.description}\n")
                    f.write(f"# Created by: {metadata.created_by}\n")
                    f.write(f"# Is baseline: {metadata.is_baseline}\n")
                    f.write(f"# \n")
                    f.write(f"# Article: {article.title}\n")
                    f.write(f"# URL: {article.url}\n")
                    f.write(f"# Generated: {article.updated_at}\n")
                    f.write(f"# \n")
                    f.write(f"# Prompt Statistics:\n")
                    f.write(f"# - Length: {prompt_chars:,} characters\n")
                    f.write(f"# - Lines: {prompt_lines:,}\n")
                    f.write(f"# - Estimated tokens: {prompt_tokens_est:,}\n")
                    f.write(f"# - Content blocks: {blocks_count}\n")
                    if html_data.get("preprocessing_summary"):
                        f.write(f"# - HTML preprocessing: {html_data['preprocessing_summary']}\n")
                    f.write(f"\n{'='*80}\n\n")
                    f.write(prompt)
                
                generated_files.append({
                    'template_id': template_id,
                    'filename': filename,
                    'filepath': filepath,
                    'chars': prompt_chars,
                    'tokens': prompt_tokens_est,
                    'metadata': metadata
                })
                
                self.stdout.write(f"✅ Generated: {filename}")
                self.stdout.write(f"   📏 {prompt_chars:,} chars, ~{prompt_tokens_est:,} tokens")
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"❌ Failed to generate {template_id}: {e}")
                )
                continue
        
        # Summary
        self.stdout.write(f"\n{'='*60}")
        self.stdout.write(self.style.SUCCESS('📊 GENERATION SUMMARY'))
        
        if generated_files:
            self.stdout.write(f"\n✅ Successfully generated {len(generated_files)} prompt examples:")
            
            # Sort by size for comparison
            generated_files.sort(key=lambda x: x['chars'], reverse=True)
            
            total_chars = sum(f['chars'] for f in generated_files)
            total_tokens = sum(f['tokens'] for f in generated_files)
            
            self.stdout.write(f"\n{'Template':<35} {'Size':<15} {'Tokens':<10} {'File'}")
            self.stdout.write("-" * 80)
            
            for file_info in generated_files:
                template_display = file_info['template_id'][:34]
                size_display = f"{file_info['chars']:,} chars"
                tokens_display = f"{file_info['tokens']:,}"
                
                self.stdout.write(
                    f"{template_display:<35} {size_display:<15} {tokens_display:<10} {file_info['filename']}"
                )
            
            self.stdout.write("-" * 80)
            self.stdout.write(f"{'TOTAL':<35} {total_chars:,} chars    {total_tokens:,}      {len(generated_files)} files")
            
            # Template comparison
            self.stdout.write(f"\n📋 Template Comparison:")
            for file_info in generated_files:
                metadata = file_info['metadata']
                baseline_indicator = "🎯 BASELINE" if metadata.is_baseline else ""
                self.stdout.write(f"   📝 {file_info['template_id']}")
                self.stdout.write(f"      📄 {metadata.description}")
                self.stdout.write(f"      👤 Created by: {metadata.created_by} {baseline_indicator}")
                self.stdout.write(f"      📏 Size: {file_info['chars']:,} chars (~{file_info['tokens']:,} tokens)")
            
            # Cost estimates for different models
            self.stdout.write(f"\n💰 Cost Estimates (per evaluation):")
            avg_tokens = total_tokens // len(generated_files) if generated_files else 0
            
            # Typical split: 90% input, 10% output for quality evaluation
            input_tokens = int(avg_tokens * 0.9)
            output_tokens = int(avg_tokens * 0.1)
            
            models = [
                ("GPT-4.1 Nano", 0.0000001, 0.0000004),
                ("GPT-4.1 Mini", 0.0000004, 0.0000016),
                ("GPT-4.1 Full", 0.000002, 0.000008),
                ("GPT-4o-mini", 0.00000015, 0.000000075)
            ]
            
            for model_name, input_cost, output_cost in models:
                cost_per_eval = (input_tokens * input_cost) + (output_tokens * output_cost)
                cost_1k = cost_per_eval * 1000
                self.stdout.write(f"   💳 {model_name}: ${cost_per_eval:.6f} per eval, ${cost_1k:.2f} per 1K evals")
            
            self.stdout.write(f"\n📁 Files saved to: {os.path.abspath(output_dir)}")
            
        else:
            self.stdout.write(
                self.style.ERROR('❌ No prompt examples were generated successfully')
            )
        
        self.stdout.write(f"\n✅ Prompt example generation completed!") 