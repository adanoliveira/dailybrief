"""
Show Prompt Example

Management command to display what the complete prompt looks like
after all variables are filled in for quality evaluation.
"""
from django.core.management.base import BaseCommand
from django.db.models import Q
from apps.articles.models import Article
from apps.content.quality.evaluator import ContentQualityEvaluator


class Command(BaseCommand):
    help = 'Show example of complete prompt with all variables filled in'

    def add_arguments(self, parser):
        parser.add_argument(
            '--article-id',
            type=str,
            help='Specific article public_id to use for example'
        )
        parser.add_argument(
            '--template',
            type=str,
            default='comprehensive_quality_evaluation_v3.1',
            help='Template to demonstrate (default: comprehensive_quality_evaluation_v3.1)'
        )
        parser.add_argument(
            '--save-to-file',
            type=str,
            help='Save prompt to file instead of displaying'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('📝 Quality Evaluation Prompt Example')
        )
        
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
        self.stdout.write(f"📊 Template: {options['template']}")
        
        # Initialize evaluator with specific template
        evaluator = ContentQualityEvaluator(template_id=options['template'])
        
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
            content_length=extracted_content["content_length"],
            content_sample=extracted_content["content_sample"],
            blocks_count=extracted_content["blocks_count"],
            blocks_sample=extracted_content["blocks_sample"],
            metadata=extracted_content["metadata"],
            html_length=html_data["html_length"],
            html_sample=html_data["html_sample"],
            reference_examples=reference_examples
        )
        
        # Show prompt statistics
        prompt_lines = prompt.count('\n')
        prompt_chars = len(prompt)
        prompt_tokens_est = prompt_chars // 4  # Rough token estimation
        
        self.stdout.write(f"\n📊 Prompt Statistics:")
        self.stdout.write(f"   📏 Length: {prompt_chars:,} characters")
        self.stdout.write(f"   📄 Lines: {prompt_lines:,}")
        self.stdout.write(f"   🔢 Estimated tokens: {prompt_tokens_est:,}")
        
        if html_data.get("preprocessing_summary"):
            self.stdout.write(f"   🔧 HTML preprocessing: {html_data['preprocessing_summary']}")
        
        # Save to file or display
        if options['save_to_file']:
            try:
                with open(options['save_to_file'], 'w', encoding='utf-8') as f:
                    f.write(f"# Quality Evaluation Prompt Example\n")
                    f.write(f"# Article: {article.title}\n")
                    f.write(f"# URL: {article.url}\n")
                    f.write(f"# Template: {options['template']}\n")
                    f.write(f"# Generated: {article.updated_at}\n")
                    f.write(f"# Prompt Length: {prompt_chars:,} chars, ~{prompt_tokens_est:,} tokens\n")
                    f.write(f"\n{'='*80}\n\n")
                    f.write(prompt)
                
                self.stdout.write(
                    self.style.SUCCESS(f"💾 Prompt saved to: {options['save_to_file']}")
                )
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Failed to save prompt: {e}")
                )
        else:
            # Display in terminal (truncated for readability)
            self.stdout.write(f"\n{'='*80}")
            self.stdout.write(self.style.WARNING('📝 COMPLETE PROMPT (showing first 2000 chars):'))
            self.stdout.write(f"{'='*80}")
            
            # Show first part of prompt
            display_prompt = prompt[:2000]
            if len(prompt) > 2000:
                display_prompt += f"\n\n... [TRUNCATED - showing 2000 of {prompt_chars:,} total characters] ..."
                display_prompt += f"\n\n[Last 500 characters:]"
                display_prompt += prompt[-500:]
            
            self.stdout.write(display_prompt)
            
            self.stdout.write(f"\n{'='*80}")
            self.stdout.write(
                self.style.WARNING(f"💡 Use --save-to-file prompt_example.txt to see the complete prompt")
            )
        
        # Show content breakdown
        self.stdout.write(f"\n📋 Content Breakdown:")
        self.stdout.write(f"   📰 Title: {len(extracted_content['title']):,} chars")
        self.stdout.write(f"   👤 Author: {len(extracted_content['author']):,} chars")
        self.stdout.write(f"   📝 Description: {len(extracted_content['description']):,} chars")
        self.stdout.write(f"   📄 Content: {extracted_content['content_length']:,} chars")
        self.stdout.write(f"   🧱 Blocks: {extracted_content['blocks_count']} blocks")
        self.stdout.write(f"   🏗️  HTML: {html_data['html_length']:,} chars")
        self.stdout.write(f"   📚 References: {len(reference_examples):,} chars")
        
        self.stdout.write(f"\n✅ Prompt example completed!") 