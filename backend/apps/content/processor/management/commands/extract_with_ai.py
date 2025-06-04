"""
Management command to test AI extraction on individual articles.

This command allows testing the AI processor on specific articles
following quality evaluation patterns for validation and debugging.
"""
import json
import time
from typing import Optional
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from datetime import datetime

from apps.articles.models import Article
from apps.content.processor.ai_processor import get_ai_processor
from apps.content.processor.algorithmic_processor import AlgorithmicProcessor
from apps.content.quality.evaluator import ContentQualityEvaluator
from apps.content.processor.models import serialize_content_blocks


class Command(BaseCommand):
    """
    Test AI extraction on individual articles with detailed output.
    
    Provides comprehensive testing and comparison capabilities following
    the patterns established by the quality evaluation system.
    """
    
    help = 'Test AI content extraction on individual articles'
    
    def add_arguments(self, parser):
        """Add command arguments."""
        parser.add_argument(
            'article_identifier',
            type=str,
            help='Article ID, public_id, or URL to process'
        )
        
        parser.add_argument(
            '--template',
            type=str,
            default='content_extraction_v2',
            help='Template ID to use for extraction (default: content_extraction_v2)'
        )
        
        parser.add_argument(
            '--model',
            type=str,
            help='Override AI model to use'
        )
        
        parser.add_argument(
            '--compare',
            action='store_true',
            help='Compare AI extraction with algorithmic processor'
        )
        
        parser.add_argument(
            '--evaluate',
            action='store_true',
            help='Run quality evaluation on extraction results'
        )
        
        parser.add_argument(
            '--save-result',
            action='store_true',
            help='Save AI extraction result to the article'
        )
        
        parser.add_argument(
            '--output-format',
            choices=['summary', 'detailed', 'json'],
            default='detailed',
            help='Output format (default: detailed)'
        )
        
        parser.add_argument(
            '--no-preprocessing',
            action='store_true',
            help='Disable HTML preprocessing'
        )
        
        parser.add_argument(
            '--show-raw-response',
            action='store_true',
            help='Show raw AI response for debugging'
        )
    
    def handle(self, *args, **options):
        """Execute the command."""
        try:
            # Find article
            article = self._find_article(options['article_identifier'])
            
            # Validate article has content
            if not article.raw_html:
                raise CommandError(f"Article {article.public_id} has no raw HTML content")
            
            self.stdout.write(
                self.style.SUCCESS(f"\n🔍 Testing AI extraction on article: {article.title}")
            )
            self.stdout.write(f"   Article ID: {article.public_id}")
            self.stdout.write(f"   URL: {article.url}")
            self.stdout.write(f"   Source: {article.publication.name if article.publication else 'Unknown'}")
            self.stdout.write(f"   HTML length: {len(article.raw_html):,} characters")
            
            # Initialize processors
            ai_processor = get_ai_processor(template_id=options['template'])
            
            # Prepare article metadata
            article_metadata = {
                'title': article.title,
                'url': article.url,
                'source': article.publication.name if article.publication else 'Unknown',
                'published_date': article.published_at.isoformat() if article.published_at else None
            }
            
            # Run AI extraction
            self.stdout.write(f"\n⚡ Running AI extraction...")
            self.stdout.write(f"   Template: {options['template']}")
            if options['model']:
                self.stdout.write(f"   Model: {options['model']}")
            if options['no_preprocessing']:
                self.stdout.write(f"   Preprocessing: Disabled")
            
            start_time = time.time()
            ai_result = ai_processor.process_content(
                raw_html=article.raw_html,
                article_metadata=article_metadata,
                model_override=options['model'],
                use_html_preprocessing=not options['no_preprocessing'],
                capture_raw_response=options['show_raw_response'] or options['save_result']
            )
            ai_time = time.time() - start_time
            
            # Display AI results
            self._display_ai_results(ai_result, ai_time, options['output_format'])
            
            # Show raw AI response if requested
            if options['show_raw_response'] and ai_result.raw_response:
                self._display_raw_response(ai_result.raw_response)
            
            # Compare with algorithmic processor if requested
            if options['compare']:
                self._run_comparison(article, article_metadata, ai_result, options['output_format'])
            
            # Run quality evaluation if requested
            if options['evaluate']:
                self._run_quality_evaluation(article, ai_result, options['output_format'])
            
            # Save result if requested
            if options['save_result'] and ai_result.success:
                self._save_result_to_article(article, ai_result)
            
            self.stdout.write(self.style.SUCCESS(f"\n✅ AI extraction test completed"))
            
        except Exception as e:
            raise CommandError(f"AI extraction test failed: {e}")
    
    def _find_article(self, identifier: str) -> Article:
        """
        Find article by ID, public_id, or URL.
        
        Args:
            identifier: Article identifier
            
        Returns:
            Article instance
            
        Raises:
            CommandError: If article not found
        """
        # Try by ID first
        try:
            article_id = int(identifier)
            return Article.objects.get(id=article_id)
        except (ValueError, Article.DoesNotExist):
            pass
        
        # Try by public_id
        try:
            return Article.objects.get(public_id=identifier)
        except Article.DoesNotExist:
            pass
        
        # Try by URL
        try:
            return Article.objects.get(url=identifier)
        except Article.DoesNotExist:
            pass
        
        # Search in title or URL
        articles = Article.objects.filter(
            Q(title__icontains=identifier) | Q(url__icontains=identifier)
        )[:5]
        
        if not articles:
            raise CommandError(f"No article found matching '{identifier}'")
        
        if len(articles) == 1:
            return articles[0]
        
        # Multiple matches - show options
        self.stdout.write(f"Multiple articles found matching '{identifier}':")
        for i, article in enumerate(articles):
            self.stdout.write(f"  {i+1}. {article.title} ({article.public_id})")
        
        raise CommandError("Multiple matches found. Please use specific article ID or public_id.")
    
    def _display_ai_results(self, result, processing_time: float, output_format: str):
        """Display AI extraction results."""
        self.stdout.write(f"\n📊 AI Extraction Results:")
        self.stdout.write(f"   Success: {result.success}")
        self.stdout.write(f"   Processing time: {processing_time:.2f}s")
        
        if not result.success:
            self.stdout.write(self.style.ERROR(f"   Error: {result.error_message}"))
            return
        
        # Basic metrics
        self.stdout.write(f"   Content blocks: {len(result.content_blocks)}")
        self.stdout.write(f"   Clean content length: {len(result.clean_content):,} characters")
        self.stdout.write(f"   Estimated quality: {result.quality_score:.2f}")
        
        # Token usage and costs
        if 'token_usage' in result.extracted_metadata:
            tokens = result.extracted_metadata['token_usage']
            self.stdout.write(f"   Token usage: {tokens:,}")
            
            # Rough cost estimate (adjust based on model)
            cost_per_1k = 0.01  # Example rate
            estimated_cost = (tokens / 1000) * cost_per_1k
            self.stdout.write(f"   Estimated cost: ${estimated_cost:.4f}")
        
        # Content type analysis
        if 'content_types' in result.extracted_metadata:
            types = result.extracted_metadata['content_types']
            self.stdout.write(f"   Content types: {dict(types)}")
        
        # Heading hierarchy analysis
        if 'heading_hierarchy' in result.extracted_metadata:
            hierarchy = result.extracted_metadata['heading_hierarchy']
            if hierarchy['has_headings']:
                self.stdout.write(f"   Heading hierarchy: {hierarchy['heading_count']} headings, max level h{hierarchy['max_level']}")
                if not hierarchy['hierarchy_valid']:
                    self.stdout.write(f"   ⚠️  Hierarchy issues: {len(hierarchy['issues'])}")
                    for issue in hierarchy['issues'][:3]:  # Show first 3 issues
                        self.stdout.write(f"     - {issue}")
                else:
                    self.stdout.write(f"   ✅ Heading hierarchy is well-structured")
        
        # Author information analysis
        if 'author_information' in result.extracted_metadata:
            author_info = result.extracted_metadata['author_information']
            if author_info and author_info.get('primary_author'):
                primary = author_info['primary_author']
                author_name = primary.get('name') or primary.get('display_name', 'Unknown')
                self.stdout.write(f"   Primary author: {author_name}")
                
                if primary.get('title'):
                    self.stdout.write(f"   Author title: {primary['title']}")
                
                if author_info.get('byline_text'):
                    byline = author_info['byline_text'][:100] + "..." if len(author_info['byline_text']) > 100 else author_info['byline_text']
                    self.stdout.write(f"   Byline: {byline}")
                
                if author_info.get('additional_authors'):
                    co_authors = len(author_info['additional_authors'])
                    self.stdout.write(f"   Co-authors: {co_authors}")
                
                confidence = author_info.get('source_confidence', 'unknown')
                self.stdout.write(f"   Author extraction confidence: {confidence}")
            else:
                self.stdout.write(f"   ⚠️  No author information extracted")
        
        # Extraction feedback analysis
        if 'extraction_feedback' in result.extracted_metadata:
            feedback = result.extracted_metadata['extraction_feedback']
            if feedback:
                self.stdout.write(f"\n📝 AI Feedback:")
                
                # Unmapped content
                if feedback.get('unmapped_content'):
                    unmapped = feedback['unmapped_content']
                    self.stdout.write(f"   Unmapped content types: {len(unmapped)}")
                    for item in unmapped[:2]:  # Show first 2
                        content_type = item.get('content_type', 'Unknown')
                        suggested = item.get('suggested_block_type', 'N/A')
                        self.stdout.write(f"     - {content_type} → suggests '{suggested}'")
                
                # Improvement suggestions
                if feedback.get('improvement_suggestions'):
                    suggestions = feedback['improvement_suggestions']
                    self.stdout.write(f"   Improvement suggestions: {len(suggestions)}")
                    for suggestion in suggestions[:1]:  # Show first suggestion
                        self.stdout.write(f"     - {suggestion}")
                
                # Extraction challenges
                if feedback.get('extraction_challenges'):
                    challenges = feedback['extraction_challenges']
                    self.stdout.write(f"   Extraction challenges: {len(challenges)}")
                
                # Overall confidence
                if feedback.get('confidence_notes'):
                    notes = feedback['confidence_notes'][:100] + "..." if len(feedback['confidence_notes']) > 100 else feedback['confidence_notes']
                    self.stdout.write(f"   Confidence notes: {notes}")
                
                # Content completeness assessment
                if feedback.get('content_completeness'):
                    completeness = feedback['content_completeness']
                    is_complete = completeness.get('is_complete')
                    percentage = completeness.get('estimated_completeness_percentage', 0)
                    confidence = completeness.get('confidence', 'unknown')
                    
                    self.stdout.write(f"\n📄 Content Completeness Assessment:")
                    status_icon = "✅" if is_complete else "⚠️"
                    status_text = "Complete" if is_complete else "Truncated/Incomplete"
                    self.stdout.write(f"   Status: {status_icon} {status_text} ({percentage}% complete)")
                    self.stdout.write(f"   Assessment confidence: {confidence}")
                    
                    if not is_complete and completeness.get('truncation_indicators'):
                        indicators = completeness['truncation_indicators']
                        self.stdout.write(f"   Truncation indicators: {len(indicators)}")
                        for indicator in indicators[:3]:  # Show first 3
                            self.stdout.write(f"     • {indicator}")
                    
                    if completeness.get('assessment_notes'):
                        notes = completeness['assessment_notes'][:150] + "..." if len(completeness['assessment_notes']) > 150 else completeness['assessment_notes']
                        self.stdout.write(f"   Assessment notes: {notes}")
        
        # Detailed or JSON output
        if output_format == 'detailed':
            self._display_detailed_blocks(result.content_blocks)
        elif output_format == 'json':
            self._display_json_output(result)
    
    def _display_detailed_blocks(self, content_blocks):
        """Display detailed content blocks."""
        self.stdout.write(f"\n📝 Content Blocks ({len(content_blocks)} total):")
        
        for i, block in enumerate(content_blocks[:10]):  # Show first 10
            self.stdout.write(f"\n   Block {block.position} ({block.type}):")
            
            if block.type == 'heading':
                self.stdout.write(f"      Level: h{block.level}")
                self.stdout.write(f"      Content: {block.content[:100]}...")
            
            elif block.type == 'paragraph':
                self.stdout.write(f"      Content: {block.content[:150]}...")
                if block.metadata.get('links'):
                    self.stdout.write(f"      Links: {len(block.metadata['links'])}")
            
            elif block.type == 'image':
                self.stdout.write(f"      Src: {block.metadata.get('src', 'N/A')}")
                self.stdout.write(f"      Alt: {block.metadata.get('alt', 'N/A')}")
                if block.content:
                    self.stdout.write(f"      Caption: {block.content[:100]}...")
            
            elif block.type == 'list':
                items = block.metadata.get('items', [])
                list_type = block.metadata.get('list_type', 'ul')
                self.stdout.write(f"      Type: {list_type}")
                self.stdout.write(f"      Items: {len(items)}")
                for j, item in enumerate(items[:3]):
                    self.stdout.write(f"        {j+1}. {item[:80]}...")
            
            elif block.type == 'quote':
                self.stdout.write(f"      Content: {block.content[:150]}...")
                if block.metadata.get('cite'):
                    self.stdout.write(f"      Attribution: {block.metadata['cite']}")
            
            elif block.type == 'twitter_embed':
                self.stdout.write(f"      Tweet ID: {block.metadata.get('tweet_id', 'N/A')}")
                if block.content:
                    self.stdout.write(f"      Content: {block.content[:100]}...")
        
        if len(content_blocks) > 10:
            self.stdout.write(f"\n   ... and {len(content_blocks) - 10} more blocks")
    
    def _display_json_output(self, result):
        """Display JSON output of extraction result."""
        output = {
            "success": result.success,
            "content_blocks": [],
            "extracted_metadata": result.extracted_metadata,
            "quality_score": result.quality_score,
            "processing_time_ms": result.processing_time_ms
        }
        
        for block in result.content_blocks:
            block_dict = {
                "type": block.type,
                "content": block.content,
                "level": block.level,
                "position": block.position,
                "metadata": block.metadata
            }
            output["content_blocks"].append(block_dict)
        
        self.stdout.write(f"\n📄 JSON Output:")
        self.stdout.write(json.dumps(output, indent=2, ensure_ascii=False))
    
    def _display_raw_response(self, raw_response: str):
        """Display raw AI response for debugging."""
        self.stdout.write(f"\n🔍 Raw AI Response:")
        self.stdout.write("=" * 80)
        self.stdout.write(raw_response)
        self.stdout.write("=" * 80)
        
        # Try to analyze the response structure
        try:
            parsed = json.loads(raw_response.strip())
            self.stdout.write(f"\n📊 Response Analysis:")
            self.stdout.write(f"   JSON valid: ✅ Yes")
            self.stdout.write(f"   Top-level keys: {list(parsed.keys())}")
            
            if 'content_blocks' in parsed:
                blocks = parsed['content_blocks']
                self.stdout.write(f"   Content blocks: {len(blocks)}")
                
                # Analyze block types
                block_types = {}
                for block in blocks:
                    block_type = block.get('type', 'unknown')
                    block_types[block_type] = block_types.get(block_type, 0) + 1
                self.stdout.write(f"   Block types: {dict(block_types)}")
                
                # Check for missing position fields
                missing_positions = [i for i, block in enumerate(blocks) if 'position' not in block]
                if missing_positions:
                    self.stdout.write(f"   ⚠️  Missing positions in blocks: {missing_positions}")
                else:
                    self.stdout.write(f"   ✅ All blocks have position field")
            
            if 'extraction_metadata' in parsed:
                metadata = parsed['extraction_metadata']
                self.stdout.write(f"   Extraction metadata keys: {list(metadata.keys())}")
                
        except json.JSONDecodeError as e:
            self.stdout.write(f"\n❌ JSON parsing failed: {e}")
            # Show first and last parts of response for debugging
            if len(raw_response) > 200:
                self.stdout.write(f"   First 100 chars: {raw_response[:100]}...")
                self.stdout.write(f"   Last 100 chars: ...{raw_response[-100:]}")
    
    def _run_comparison(self, article, article_metadata, ai_result, output_format):
        """Compare AI extraction with algorithmic processor."""
        self.stdout.write(f"\n🔄 Running algorithmic processor for comparison...")
        
        algorithmic_processor = AlgorithmicProcessor()
        start_time = time.time()
        algo_result = algorithmic_processor.process_content(
            raw_html=article.raw_html,
            article_metadata=article_metadata
        )
        algo_time = time.time() - start_time
        
        self.stdout.write(f"\n📊 Comparison Results:")
        self.stdout.write(f"   {'Metric':<25} {'AI':<15} {'Algorithmic':<15} {'Difference'}")
        self.stdout.write(f"   {'-'*70}")
        
        # Processing time
        time_diff = f"{ai_result.processing_time_ms - algo_result.processing_time_ms:+d}ms"
        self.stdout.write(f"   {'Processing time':<25} {ai_result.processing_time_ms}ms{'':<6} {algo_result.processing_time_ms}ms{'':<6} {time_diff}")
        
        # Content blocks
        block_diff = len(ai_result.content_blocks) - len(algo_result.content_blocks)
        self.stdout.write(f"   {'Content blocks':<25} {len(ai_result.content_blocks):<15} {len(algo_result.content_blocks):<15} {block_diff:+d}")
        
        # Content length
        ai_length = len(ai_result.clean_content)
        algo_length = len(algo_result.clean_content)
        length_diff = ai_length - algo_length
        self.stdout.write(f"   {'Content length':<25} {ai_length:,}{'':<6} {algo_length:,}{'':<6} {length_diff:+,}")
        
        # Quality score
        quality_diff = ai_result.quality_score - algo_result.quality_score
        self.stdout.write(f"   {'Quality score':<25} {ai_result.quality_score:.3f}{'':<10} {algo_result.quality_score:.3f}{'':<10} {quality_diff:+.3f}")
        
        # Content type comparison
        ai_types = ai_result.extracted_metadata.get('content_types', {})
        algo_types = algo_result.extracted_metadata.get('content_types', {})
        
        all_types = set(ai_types.keys()) | set(algo_types.keys())
        self.stdout.write(f"\n   Content Type Breakdown:")
        for content_type in sorted(all_types):
            ai_count = ai_types.get(content_type, 0)
            algo_count = algo_types.get(content_type, 0)
            diff = ai_count - algo_count
            self.stdout.write(f"     {'  ' + content_type:<23} {ai_count:<15} {algo_count:<15} {diff:+d}")
    
    def _run_quality_evaluation(self, article, result, output_format):
        """Run quality evaluation on extraction results."""
        if not result.success:
            self.stdout.write(self.style.WARNING("   Skipping quality evaluation due to extraction failure"))
            return
        
        self.stdout.write(f"\n🎯 Running quality evaluation...")
        
        # Create a temporary article with AI extraction results for evaluation
        temp_article = Article(
            title=article.title,
            url=article.url,
            raw_html=article.raw_html,
            clean_content=result.clean_content,
            content_blocks=result.content_blocks,
            word_count=len(result.clean_content.split()) if result.clean_content else 0,
            has_images=any(block.type == 'image' for block in result.content_blocks)
        )
        temp_article.publication = article.publication
        
        evaluator = ContentQualityEvaluator()
        quality_result = evaluator.evaluate_article_quality(temp_article)
        
        self.stdout.write(f"\n🎯 Quality Evaluation Results:")
        self.stdout.write(f"   Overall Score: {quality_result.overall_score:.3f}")
        
        if hasattr(quality_result, 'scoring') and quality_result.scoring:
            scoring = quality_result.scoring
            self.stdout.write(f"   Content Completeness: {scoring.content_completeness:.3f}")
            self.stdout.write(f"   Structure Quality: {scoring.structure_quality:.3f}")
            self.stdout.write(f"   Content Relevance: {scoring.content_relevance:.3f}")
            self.stdout.write(f"   Technical Quality: {scoring.technical_quality:.3f}")
        
        if quality_result.ai_feedback:
            self.stdout.write(f"\n   AI Feedback:")
            feedback_lines = quality_result.ai_feedback.split('\n')[:5]  # First 5 lines
            for line in feedback_lines:
                if line.strip():
                    self.stdout.write(f"     {line.strip()}")
    
    def _save_result_to_article(self, article, result):
        """
        Save AI extraction result to article model with comprehensive metadata.
        Enhanced to save AI feedback, author information, heading hierarchy,
        and all extraction insights for analysis.
        """
        try:
            # Update article fields with processing results
            article.clean_content = result.clean_content
            article.content_blocks = serialize_content_blocks(result.content_blocks)  # Properly serialize
            article.process_status = 'completed'
            article.process_route = 'llm_enhanced'
            article.process_duration_ms = result.processing_time_ms
            
            # Extract comprehensive metadata from AI response
            ai_metadata = result.extracted_metadata or {}
            
            # Store comprehensive extraction metadata including AI feedback
            comprehensive_metadata = {
                # Core processing info
                'ai_extraction': True,
                'template_used': ai_metadata.get('template_used', 'unknown'),
                'template_version': ai_metadata.get('template_version', 'unknown'),
                'processing_time_ms': result.processing_time_ms,
                'token_usage': ai_metadata.get('token_usage', 0),
                'provider': ai_metadata.get('provider', 'unknown'),
                'model': ai_metadata.get('model', 'unknown'),
                'extraction_timestamp': datetime.now().isoformat(),
                
                # Title extraction (for clean page titles)
                'visual_title': ai_metadata.get('visual_title'),
                
                # Content analysis
                'total_blocks': len(result.content_blocks),
                'content_types': ai_metadata.get('content_types', {}),
                'estimated_word_count': ai_metadata.get('estimated_word_count', 0),
                'quality_score': result.quality_score,
                
                # Author information analysis
                'author_information': ai_metadata.get('author_information', {}),
                
                # Heading hierarchy analysis
                'heading_hierarchy': ai_metadata.get('heading_hierarchy', {}),
                
                # AI feedback for system improvement
                'extraction_feedback': ai_metadata.get('extraction_feedback', {}),
                
                # HTML preprocessing info
                'html_preprocessing_summary': ai_metadata.get('html_preprocessing_summary', ''),
                'original_html_length': ai_metadata.get('original_html_length', 0),
                'preprocessed_html_length': ai_metadata.get('preprocessed_html_length', 0),
                
                # Raw AI response for debugging (truncated for storage)
                'raw_ai_response': result.raw_response[:7000] if result.raw_response else '',
                
                # Processing metadata
                'processing_route': 'ai_extraction',
                'processing_version': '2.0'
            }
            
            # Save comprehensive metadata
            article.extracted_metadata = comprehensive_metadata
            
            # Update rich content flags based on content blocks
            article.update_rich_content_metadata()
            
            # Save to database
            article.save()
            
            self.stdout.write(self.style.SUCCESS(f"✅ Saved comprehensive AI extraction data to article"))
            
            # Log key extraction insights
            if comprehensive_metadata.get('author_information'):
                author_info = comprehensive_metadata['author_information']
                if author_info.get('primary_author'):
                    primary = author_info['primary_author']
                    author_name = primary.get('name') or primary.get('display_name', 'Unknown')
                    self.stdout.write(f"📝 Extracted author: {author_name}")
            
            # Log heading hierarchy
            hierarchy = comprehensive_metadata.get('heading_hierarchy', {})
            if hierarchy.get('heading_count', 0) > 0:
                max_level = hierarchy.get('max_level', 'unknown')
                is_structured = hierarchy.get('is_well_structured', False)
                status = "✅ Well-structured" if is_structured else "⚠️ Poor structure"
                self.stdout.write(f"📋 Heading hierarchy: {hierarchy['heading_count']} headings, max level h{max_level}, {status}")
            
            # Log content completeness if available
            feedback = comprehensive_metadata.get('extraction_feedback', {})
            if feedback.get('content_completeness'):
                completeness = feedback['content_completeness']
                is_complete = completeness.get('is_complete')
                percentage = completeness.get('estimated_completeness_percentage', 0)
                if is_complete:
                    self.stdout.write(f"✅ Complete ({percentage}% complete)")
                else:
                    indicators = completeness.get('truncation_indicators', [])
                    indicator_text = f" - {', '.join(indicators[:2])}" if indicators else ""
                    self.stdout.write(f"⚠️ Truncated ({percentage}% complete{indicator_text})")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error saving result to article: {e}"))
            logger.exception("Error saving AI extraction result") 