"""
Management command to debug and save pre-processed HTML input for AI models.

This command extracts and saves the pre-processed HTML that is used as input
to AI models for content extraction, helping debug why model outputs may not
be changing as expected.
"""

import os
import time
from pathlib import Path
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from apps.articles.models import Article
from apps.content.processor.ai_processor import get_ai_processor


class Command(BaseCommand):
    """
    Debug AI preprocessing by saving the actual HTML input sent to models.
    
    This helps identify issues where template changes don't affect model output
    because the preprocessing isn't working as expected.
    """
    
    help = 'Debug and save pre-processed HTML input for AI models'
    
    def add_arguments(self, parser):
        """Add command arguments."""
        parser.add_argument(
            'article_ids',
            nargs='+',
            type=int,
            help='Article IDs to debug preprocessing for'
        )
        
        parser.add_argument(
            '--template',
            type=str,
            default='content_extraction_v2',
            help='Template ID to use for extraction (default: content_extraction_v2)'
        )
        
        parser.add_argument(
            '--output-dir',
            type=str,
            default='debug_preprocessing',
            help='Directory to save debug files (default: debug_preprocessing)'
        )
        
        parser.add_argument(
            '--model',
            type=str,
            help='Override AI model to use'
        )
        
        parser.add_argument(
            '--no-preprocessing',
            action='store_true',
            help='Disable HTML preprocessing to compare'
        )
    
    def handle(self, *args, **options):
        """Execute the command."""
        try:
            # Validate article IDs
            article_ids = options['article_ids']
            articles = []
            
            for article_id in article_ids:
                try:
                    article = Article.objects.get(id=article_id)
                    if not article.raw_html:
                        self.stdout.write(
                            self.style.WARNING(f"⚠️  Article {article_id} has no raw HTML content - skipping")
                        )
                        continue
                    articles.append(article)
                except Article.DoesNotExist:
                    self.stdout.write(
                        self.style.ERROR(f"❌ Article {article_id} not found - skipping")
                    )
                    continue
            
            if not articles:
                raise CommandError("No valid articles found with HTML content")
            
            # Setup output directory
            output_dir = Path(options['output_dir'])
            output_dir.mkdir(exist_ok=True)
            
            self.stdout.write(
                self.style.SUCCESS(f"\n🔍 Debugging preprocessing for {len(articles)} articles")
            )
            self.stdout.write(f"📁 Output directory: {output_dir.absolute()}")
            self.stdout.write(f"🎯 Template: {options['template']}")
            if options['model']:
                self.stdout.write(f"🤖 Model: {options['model']}")
            self.stdout.write("=" * 80)
            
            # Initialize AI processor
            ai_processor = get_ai_processor(template_id=options['template'])
            
            # Process each article
            for article in articles:
                self._debug_article_preprocessing(
                    article,
                    ai_processor,
                    output_dir,
                    options
                )
            
            self.stdout.write(
                self.style.SUCCESS(f"\n✅ Preprocessing debug completed for {len(articles)} articles")
            )
            self.stdout.write(f"📂 Check files in: {output_dir.absolute()}")
            
        except Exception as e:
            raise CommandError(f"Preprocessing debug failed: {e}")
    
    def _debug_article_preprocessing(
        self,
        article: Article,
        ai_processor,
        output_dir: Path,
        options: dict
    ):
        """
        Debug preprocessing for a single article.
        
        Args:
            article: Article instance to debug
            ai_processor: AI processor instance
            output_dir: Directory to save debug files
            options: Command options
        """
        
        self.stdout.write(f"\n📰 Processing article {article.id}: {article.title[:60]}...")
        
        # Prepare article metadata
        article_metadata = {
            'title': article.title,
            'url': article.url,
            'source': article.publication.name if article.publication else 'Unknown',
            'published_date': article.published_at.isoformat() if article.published_at else None,
            'author': article.author,
            'source_name': article.source_name
        }
        
        # Create debug files for this article
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        article_dir = output_dir / f"article_{article.id}_{timestamp}"
        article_dir.mkdir(exist_ok=True)
        
        # Save original raw HTML
        self._save_file(
            article_dir / "01_original_raw_html.html",
            article.raw_html,
            f"Original raw HTML ({len(article.raw_html):,} chars)"
        )
        
        # Save article metadata
        self._save_file(
            article_dir / "02_article_metadata.json",
            self._format_json(article_metadata),
            "Article metadata"
        )
        
        # Get preprocessed HTML that would be sent to AI
        try:
            # Use the same method as the AI processor for preprocessing
            preprocessed_data = ai_processor._prepare_html_for_extraction(
                article.raw_html,
                use_preprocessing=True,
                max_tokens=75000
            )
            
            preprocessed_html = preprocessed_data["html_sample"]
            
            self._save_file(
                article_dir / "03_preprocessed_html.html",
                preprocessed_html,
                f"Preprocessed HTML ({len(preprocessed_html):,} chars)"
            )
            
            # Save preprocessing metadata
            self._save_file(
                article_dir / "03b_preprocessing_metadata.json",
                self._format_json(preprocessed_data),
                "Preprocessing metadata"
            )
            
            # Calculate size reduction
            original_size = len(article.raw_html)
            processed_size = len(preprocessed_html)
            reduction_pct = ((original_size - processed_size) / original_size) * 100
            
            self.stdout.write(f"   📏 Size: {original_size:,} → {processed_size:,} chars (-{reduction_pct:.1f}%)")
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"   ❌ Failed to get preprocessed HTML: {e}")
            )
            preprocessed_html = article.raw_html
            preprocessed_data = {
                "html_sample": article.raw_html,
                "html_length": len(article.raw_html),
                "preprocessing_summary": "Failed to preprocess"
            }
        
        # Get the complete prompt that would be sent to the model
        try:
            # Use the template to format the prompt
            full_prompt = ai_processor.template.format(
                preprocessed_html=preprocessed_html,
                article_metadata=article_metadata
            )
            
            self._save_file(
                article_dir / "04_complete_prompt.txt",
                full_prompt,
                f"Complete prompt sent to model ({len(full_prompt):,} chars)"
            )
            
            self.stdout.write(f"   📝 Prompt: {len(full_prompt):,} chars")
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"   ❌ Failed to build prompt: {e}")
            )
            full_prompt = "Failed to generate prompt"
        
        # If no preprocessing option is set, also save raw version for comparison
        if not options['no_preprocessing']:
            try:
                no_preprocess_data = ai_processor._prepare_html_for_extraction(
                    article.raw_html,
                    use_preprocessing=False,
                    max_tokens=75000
                )
                
                no_preprocess_prompt = ai_processor.template.format(
                    preprocessed_html=no_preprocess_data["html_sample"],
                    article_metadata=article_metadata
                )
                
                self._save_file(
                    article_dir / "05_no_preprocessing_prompt.txt",
                    no_preprocess_prompt,
                    f"Prompt without preprocessing ({len(no_preprocess_prompt):,} chars)"
                )
                
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f"   ⚠️  Could not generate no-preprocessing version: {e}")
                )
        
        # Save extraction template being used
        try:
            # Get the template system prompt and output format
            system_prompt = ai_processor.template._get_system_prompt()
            output_format = ai_processor.template._get_output_format_specification()
            
            template_content = f"""Template: {ai_processor.template.identifier}
Version: {ai_processor.template.version}

SYSTEM PROMPT:
{system_prompt}

OUTPUT FORMAT SPECIFICATION:
{output_format}
"""
            
            self._save_file(
                article_dir / "06_extraction_template.txt",
                template_content,
                "Extraction template used"
            )
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f"   ⚠️  Could not save template content: {e}")
            )
        
        # Create summary file
        # Calculate variables used in summary
        original_size = len(article.raw_html)
        processed_size = len(preprocessed_html) if 'preprocessed_html' in locals() else original_size
        reduction_pct = ((original_size - processed_size) / original_size) * 100 if original_size > 0 else 0
        prompt_size = len(full_prompt) if 'full_prompt' in locals() and isinstance(full_prompt, str) else 0
        
        summary = f"""
Preprocessing Debug Summary for Article {article.id}
{'=' * 60}

Article Info:
- Title: {article.title}
- URL: {article.url}
- Source: {article.publication.name if article.publication else 'Unknown'}
- Published: {article.published_at}
- Author: {article.author or 'Unknown'}

File Sizes:
- Original HTML: {original_size:,} characters
- Preprocessed HTML: {processed_size:,} characters (reduction: {reduction_pct:.1f}%)
- Complete Prompt: {prompt_size:,} characters

Template: {options['template']}
Model: {options.get('model', 'Default')}
Timestamp: {timestamp}

Files Generated:
- 01_original_raw_html.html: Raw HTML from article.raw_html
- 02_article_metadata.json: Metadata passed to processor
- 03_preprocessed_html.html: HTML after preprocessing
- 03b_preprocessing_metadata.json: Preprocessing metadata and stats
- 04_complete_prompt.txt: Full prompt sent to AI model
- 05_no_preprocessing_prompt.txt: Prompt without preprocessing (if available)
- 06_extraction_template.txt: Template used for extraction
- README.txt: This summary file

Use these files to understand exactly what input the AI model receives
and debug why template changes may not be affecting model output.
        """.strip()
        
        self._save_file(
            article_dir / "README.txt",
            summary,
            "Debug summary"
        )
        
        self.stdout.write(f"   📂 Saved to: {article_dir.name}")
    
    def _save_file(self, filepath: Path, content: str, description: str):
        """
        Save content to file with error handling.
        
        Args:
            filepath: Path to save file
            content: Content to save
            description: Description for logging
        """
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            self.stdout.write(f"   ✅ {description}")
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"   ❌ Failed to save {description}: {e}")
            )
    
    def _format_json(self, data: dict) -> str:
        """Format dictionary as pretty JSON."""
        import json
        return json.dumps(data, indent=2, default=str, ensure_ascii=False) 