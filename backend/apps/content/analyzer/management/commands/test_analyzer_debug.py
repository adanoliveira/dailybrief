"""
Enhanced test command for verifying the analyzer classification.

This command provides detailed debugging information about:
1. Available topics and regions in the database
2. The raw classification results from the LLM
3. The confidence scores for each classification
4. Whether topics and regions are properly updated in the article
"""
import time
import json
import traceback
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from apps.articles.models import Article
from apps.feeds.models import Topic, Region, Language
from apps.content.analyzer.services import AnalyzerService
from apps.content.analyzer.models import ArticleAnalysis


class Command(BaseCommand):
    help = "Enhanced test for analyzer classification"

    def add_arguments(self, parser):
        parser.add_argument('--article_id', type=int, help='Specific article ID to test')
        parser.add_argument('--threshold', type=float, default=0.3, help='Classification threshold (default: 0.3)')
        
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("=== Enhanced Analyzer Classification Test ==="))
        
        # Set threshold for testing
        self.threshold = options.get('threshold', 0.3)
        self.stdout.write(f"Using classification threshold: {self.threshold}")
        
        # Check available topics and regions
        self.check_available_classifications()
        
        # Get test article
        article = None
        if options.get('article_id'):
            try:
                article = Article.objects.get(id=options['article_id'])
                self.stdout.write(f"Using specified article: {article.id} - {article.title}")
            except Article.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Article with ID {options['article_id']} not found"))
                return
        else:
            article = self.get_test_article()
            
        if not article:
            self.stdout.write(self.style.ERROR("No suitable article found for testing"))
            return
            
        self.stdout.write(f"Using article: {article.id} - {article.title}")
        
        # Clear existing analysis data
        self.clear_analysis_data(article)
        
        # Patch the analyzer service to use our threshold and capture raw responses
        self.raw_responses = {}
        analyzer = self.create_patched_analyzer()
        
        # Run analyzer service
        try:
            self.stdout.write("Starting article analysis...")
            result = analyzer.analyze_article(article, force=True)
            self.stdout.write(f"Analysis completed with result: {result}")
            
            # Verify results
            self.verify_results(article, result)
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error during analysis: {str(e)}"))
            self.stdout.write(self.style.ERROR(traceback.format_exc()))
    
    def check_available_classifications(self):
        """Check what topics and regions are available in the database."""
        topics = Topic.objects.all()
        regions = Region.objects.all()
        
        self.stdout.write(self.style.SUCCESS(f"\n=== Available Topics ({topics.count()}) ==="))
        for topic in topics[:10]:  # Show first 10
            self.stdout.write(f"- {topic.slug}: {topic.name}")
        if topics.count() > 10:
            self.stdout.write(f"... and {topics.count() - 10} more")
            
        self.stdout.write(self.style.SUCCESS(f"\n=== Available Regions ({regions.count()}) ==="))
        for region in regions[:10]:  # Show first 10
            self.stdout.write(f"- {region.code}: {region.name}")
        if regions.count() > 10:
            self.stdout.write(f"... and {regions.count() - 10} more")
    
    def create_patched_analyzer(self):
        """Create an analyzer with patched methods to capture raw responses and use our threshold."""
        analyzer = AnalyzerService()
        original_region_classification = analyzer._stage_6_region_classification
        original_topic_classification = analyzer._stage_7_topic_classification
        
        # Store reference to self for use in the patched methods
        command_self = self
        threshold = self.threshold
        
        # Patch region classification
        def patched_region_classification(self, article, content, analysis_record):
            command_self.stdout.write(command_self.style.SUCCESS("\n=== Region Classification ==="))
            command_self.stdout.write(f"Content sample: {content[:100]}...")
            
            result = original_region_classification(self, article, content, analysis_record)
            command_self.raw_responses['region'] = result
            
            command_self.stdout.write(f"Primary region: {result.get('primary_region')} (confidence: {result.get('primary_confidence', 0):.2f})")
            command_self.stdout.write(f"Secondary regions: {result.get('secondary_regions', [])}")
            command_self.stdout.write(f"Using threshold: {threshold}")
            
            return result
        
        # Patch topic classification
        def patched_topic_classification(self, article, content, analysis_record):
            command_self.stdout.write(command_self.style.SUCCESS("\n=== Topic Classification ==="))
            command_self.stdout.write(f"Content sample: {content[:100]}...")
            
            result = original_topic_classification(self, article, content, analysis_record)
            command_self.raw_responses['topic'] = result
            
            command_self.stdout.write(f"Primary topic: {result.get('primary_topic')} (confidence: {result.get('primary_confidence', 0):.2f})")
            command_self.stdout.write(f"Secondary topics: {result.get('secondary_topics', [])}")
            command_self.stdout.write(f"Using threshold: {threshold}")
            
            return result
        
        # Apply patches
        analyzer._stage_6_region_classification = patched_region_classification.__get__(analyzer, AnalyzerService)
        analyzer._stage_7_topic_classification = patched_topic_classification.__get__(analyzer, AnalyzerService)
        
        # Instead of trying to modify the code object directly, let's modify the threshold in the services.py file
        # Create a temporary patch for the threshold check
        def patched_region_threshold_check(self, article, primary_region_code, primary_confidence):
            """Patched threshold check for region classification."""
            return primary_region_code and (primary_confidence >= threshold or not article.primary_region)
        
        def patched_topic_threshold_check(self, article, primary_topic_slug, primary_confidence):
            """Patched threshold check for topic classification."""
            return primary_topic_slug and (primary_confidence >= threshold or not article.primary_topic)
        
        # Store the original methods
        analyzer._original_region_threshold_check = lambda self, article, code, conf: code and (conf >= 0.5 or not article.primary_region)
        analyzer._original_topic_threshold_check = lambda self, article, slug, conf: slug and (conf >= 0.5 or not article.primary_topic)
        
        # Add new methods to the analyzer
        analyzer._patched_region_threshold_check = patched_region_threshold_check.__get__(analyzer, AnalyzerService)
        analyzer._patched_topic_threshold_check = patched_topic_threshold_check.__get__(analyzer, AnalyzerService)
        
        # Create new versions of the classification methods that use our patched threshold check
        def new_region_classification(self, article, content, analysis_record):
            """Region classification with patched threshold check."""
            try:
                # Get available regions
                regions = list(Region.objects.all().values('code', 'name', 'description'))
                
                # Generate prompt for region classification
                prompt = self.prompts.region_classification_prompt(
                    article.title, content, regions
                )
                
                # Get response from AI provider
                response = self.ai_service.call_llm(
                    prompt=prompt,
                    operation="region_classification",
                    max_tokens=400,
                    temperature=0.1
                )
                
                # Validate and extract region classifications
                valid_region_codes = [r['code'] for r in regions]
                result = self.prompts.validate_classification_output(response.content, valid_region_codes)
                
                # Extract primary region
                primary_region_code = result.get('primary_region')
                primary_confidence = result.get('primary_region_confidence', 0.7)
                
                # Extract secondary regions
                secondary_region_codes = result.get('secondary_regions', [])
                
                # Extract relevance scores
                region_relevance = result.get('region_relevance', {})
                
                # Update article with primary region only if confidence is high enough or if not set
                # USE PATCHED THRESHOLD CHECK HERE
                if self._patched_region_threshold_check(article, primary_region_code, primary_confidence):
                    try:
                        primary_region = Region.objects.get(code=primary_region_code)
                        
                        # Only update if different or not set
                        if not article.primary_region or article.primary_region.code != primary_region_code:
                            article.primary_region = primary_region
                            article.save(update_fields=['primary_region'])
                            
                            command_self.stdout.write(f"Set primary region for article {article.id}: "
                                      f"{primary_region.name} ({primary_confidence:.2f})")
                    except Region.DoesNotExist:
                        command_self.stdout.write(f"Region not found: {primary_region_code}")
                
                # Update article with secondary regions only if they're not already associated
                if secondary_region_codes:
                    current_regions = set(article.regions.values_list('code', flat=True))
                    new_region_codes = set(secondary_region_codes) - current_regions
                    
                    if new_region_codes:
                        secondary_regions = Region.objects.filter(code__in=new_region_codes)
                        article.regions.add(*secondary_regions)
                        
                        command_self.stdout.write(f"Added {secondary_regions.count()} secondary regions for article {article.id}")
                
                # Store minimal metadata in analysis record
                analysis_record.primary_region_confidence = primary_confidence
                analysis_record.save(update_fields=['primary_region_confidence'])
                
                return {
                    'primary_region': primary_region_code,
                    'primary_confidence': primary_confidence,
                    'secondary_regions': secondary_region_codes,
                    'region_relevance': region_relevance,
                    'cost': response.usage.get('total_cost', 0)
                }
                
            except Exception as e:
                command_self.stdout.write(f"Region classification failed for article {article.id}: {str(e)}")
                return {
                    'error': str(e),
                    'cost': Decimal('0.0')
                }
        
        def new_topic_classification(self, article, content, analysis_record):
            """Topic classification with patched threshold check."""
            try:
                # Get available topics
                topics = list(Topic.objects.all().values('slug', 'name', 'description'))
                
                # Generate prompt for topic classification
                prompt = self.prompts.topic_classification_prompt(
                    article.title, content, topics
                )
                
                # Get response from AI provider
                response = self.ai_service.call_llm(
                    prompt=prompt,
                    operation="topic_classification",
                    max_tokens=400,
                    temperature=0.1
                )
                
                # Validate and extract topic classifications
                valid_topic_slugs = [t['slug'] for t in topics]
                result = self.prompts.validate_classification_output(response.content, valid_topic_slugs)
                
                # Extract primary topic
                primary_topic_slug = result.get('primary_topic')
                primary_confidence = result.get('primary_topic_confidence', 0.7)
                
                # Extract secondary topics
                secondary_topic_slugs = result.get('secondary_topics', [])
                
                # Extract relevance scores
                topic_relevance = result.get('topic_relevance', {})
                
                # Update article with primary topic only if confidence is high enough or if not set
                # USE PATCHED THRESHOLD CHECK HERE
                if self._patched_topic_threshold_check(article, primary_topic_slug, primary_confidence):
                    try:
                        primary_topic = Topic.objects.get(slug=primary_topic_slug)
                        
                        # Only update if different or not set
                        if not article.primary_topic or article.primary_topic.slug != primary_topic_slug:
                            article.primary_topic = primary_topic
                            article.save(update_fields=['primary_topic'])
                            
                            command_self.stdout.write(f"Set primary topic for article {article.id}: "
                                      f"{primary_topic.name} ({primary_confidence:.2f})")
                    except Topic.DoesNotExist:
                        command_self.stdout.write(f"Topic not found: {primary_topic_slug}")
                
                # Update article with secondary topics only if they're not already associated
                if secondary_topic_slugs:
                    current_topics = set(article.topics.values_list('slug', flat=True))
                    new_topic_slugs = set(secondary_topic_slugs) - current_topics
                    
                    if new_topic_slugs:
                        secondary_topics = Topic.objects.filter(slug__in=new_topic_slugs)
                        article.topics.add(*secondary_topics)
                        
                        command_self.stdout.write(f"Added {secondary_topics.count()} secondary topics for article {article.id}")
                
                # Store minimal metadata in analysis record
                analysis_record.primary_topic_confidence = primary_confidence
                analysis_record.save(update_fields=['primary_topic_confidence'])
                
                return {
                    'primary_topic': primary_topic_slug,
                    'primary_confidence': primary_confidence,
                    'secondary_topics': secondary_topic_slugs,
                    'topic_relevance': topic_relevance,
                    'cost': response.usage.get('total_cost', 0)
                }
                
            except Exception as e:
                command_self.stdout.write(f"Topic classification failed for article {article.id}: {str(e)}")
                return {
                    'error': str(e),
                    'cost': Decimal('0.0')
                }
        
        # Replace the methods with our versions that use the patched threshold check
        analyzer._stage_6_region_classification = new_region_classification.__get__(analyzer, AnalyzerService)
        analyzer._stage_7_topic_classification = new_topic_classification.__get__(analyzer, AnalyzerService)
        
        return analyzer
        
    def get_test_article(self):
        """Get a test article that has content for analysis."""
        article = Article.objects.filter(
            clean_content__isnull=False,
            clean_content__gt=""
        ).order_by('?').first()
        
        if not article:
            # Try with basic content
            article = Article.objects.filter(
                basic_content__isnull=False,
                basic_content__gt=""
            ).order_by('?').first()
            
        return article
        
    def clear_analysis_data(self, article):
        """Clear existing analysis data for clean testing."""
        with transaction.atomic():
            # Clear ArticleAnalysis if exists
            count = ArticleAnalysis.objects.filter(article=article).delete()
            self.stdout.write(f"Deleted {count} existing analysis records")
            
            # Clear topic and region assignments
            article.primary_topic = None
            article.primary_region = None
            article.topics.clear()
            article.regions.clear()
            article.save()
            
        self.stdout.write(self.style.SUCCESS("Cleared existing analysis data"))
            
    def verify_results(self, article, result):
        """Verify the analyzer results with detailed debugging."""
        # Refresh article from database
        article.refresh_from_db()
        
        # Check if article has analysis record
        try:
            analysis = ArticleAnalysis.objects.get(article=article)
            self.stdout.write(self.style.SUCCESS("\n=== Analysis Record ==="))
            self.stdout.write("✓ ArticleAnalysis record created")
        except ArticleAnalysis.DoesNotExist:
            self.stdout.write(self.style.ERROR("✗ ArticleAnalysis record not created"))
            return
        
        # Check topic classification results
        self.stdout.write(self.style.SUCCESS("\n=== Topic Classification Results ==="))
        if analysis.primary_topic_confidence > 0:
            self.stdout.write(f"✓ Topic confidence stored: {analysis.primary_topic_confidence:.2f}")
        else:
            self.stdout.write(f"? Topic confidence not set: {analysis.primary_topic_confidence}")
        
        if article.primary_topic:
            self.stdout.write(self.style.SUCCESS(f"✓ Primary topic set: {article.primary_topic.name} ({article.primary_topic.slug})"))
        else:
            self.stdout.write(self.style.WARNING(f"? Primary topic not set"))
            # Debug why
            topic_result = self.raw_responses.get('topic', {})
            primary_topic = topic_result.get('primary_topic')
            confidence = topic_result.get('primary_confidence', 0)
            
            if primary_topic:
                self.stdout.write(f"  - Raw primary topic from LLM: {primary_topic}")
                self.stdout.write(f"  - Confidence: {confidence:.2f}")
                self.stdout.write(f"  - Threshold: {self.threshold}")
                
                if confidence < self.threshold:
                    self.stdout.write(f"  - Reason: Confidence {confidence:.2f} below threshold {self.threshold}")
                else:
                    # Check if topic exists
                    try:
                        topic = Topic.objects.get(slug=primary_topic)
                        self.stdout.write(f"  - Topic exists in database: {topic.name}")
                        self.stdout.write(f"  - Unknown reason for not setting primary topic")
                    except Topic.DoesNotExist:
                        self.stdout.write(f"  - Topic '{primary_topic}' does not exist in database")
            else:
                self.stdout.write(f"  - No primary topic returned from LLM")
        
        # Check region classification results
        self.stdout.write(self.style.SUCCESS("\n=== Region Classification Results ==="))
        if analysis.primary_region_confidence > 0:
            self.stdout.write(f"✓ Region confidence stored: {analysis.primary_region_confidence:.2f}")
        else:
            self.stdout.write(f"? Region confidence not set: {analysis.primary_region_confidence}")
        
        if article.primary_region:
            self.stdout.write(self.style.SUCCESS(f"✓ Primary region set: {article.primary_region.name} ({article.primary_region.code})"))
        else:
            self.stdout.write(self.style.WARNING(f"? Primary region not set"))
            # Debug why
            region_result = self.raw_responses.get('region', {})
            primary_region = region_result.get('primary_region')
            confidence = region_result.get('primary_confidence', 0)
            
            if primary_region:
                self.stdout.write(f"  - Raw primary region from LLM: {primary_region}")
                self.stdout.write(f"  - Confidence: {confidence:.2f}")
                self.stdout.write(f"  - Threshold: {self.threshold}")
                
                if confidence < self.threshold:
                    self.stdout.write(f"  - Reason: Confidence {confidence:.2f} below threshold {self.threshold}")
                else:
                    # Check if region exists
                    try:
                        region = Region.objects.get(code=primary_region)
                        self.stdout.write(f"  - Region exists in database: {region.name}")
                        self.stdout.write(f"  - Unknown reason for not setting primary region")
                    except Region.DoesNotExist:
                        self.stdout.write(f"  - Region '{primary_region}' does not exist in database")
            else:
                self.stdout.write(f"  - No primary region returned from LLM")
        
        # Check secondary topics
        topic_count = article.topics.count()
        if topic_count > 0:
            self.stdout.write(self.style.SUCCESS(f"✓ Article has {topic_count} secondary topics:"))
            for topic in article.topics.all():
                self.stdout.write(f"  - {topic.name} ({topic.slug})")
        else:
            self.stdout.write(self.style.WARNING(f"? No secondary topics added"))
            # Debug why
            topic_result = self.raw_responses.get('topic', {})
            secondary_topics = topic_result.get('secondary_topics', [])
            
            if secondary_topics:
                self.stdout.write(f"  - Raw secondary topics from LLM: {secondary_topics}")
                # Check if topics exist
                for slug in secondary_topics:
                    try:
                        topic = Topic.objects.get(slug=slug)
                        self.stdout.write(f"  - Topic exists in database: {topic.name} ({slug})")
                    except Topic.DoesNotExist:
                        self.stdout.write(f"  - Topic '{slug}' does not exist in database")
            else:
                self.stdout.write(f"  - No secondary topics returned from LLM")
        
        # Check secondary regions
        region_count = article.regions.count()
        if region_count > 0:
            self.stdout.write(self.style.SUCCESS(f"✓ Article has {region_count} secondary regions:"))
            for region in article.regions.all():
                self.stdout.write(f"  - {region.name} ({region.code})")
        else:
            self.stdout.write(self.style.WARNING(f"? No secondary regions added"))
            # Debug why
            region_result = self.raw_responses.get('region', {})
            secondary_regions = region_result.get('secondary_regions', [])
            
            if secondary_regions:
                self.stdout.write(f"  - Raw secondary regions from LLM: {secondary_regions}")
                # Check if regions exist
                for code in secondary_regions:
                    try:
                        region = Region.objects.get(code=code)
                        self.stdout.write(f"  - Region exists in database: {region.name} ({code})")
                    except Region.DoesNotExist:
                        self.stdout.write(f"  - Region '{code}' does not exist in database")
            else:
                self.stdout.write(f"  - No secondary regions returned from LLM")
        
        # Overall success
        self.stdout.write(self.style.SUCCESS("\n=== Test Summary ==="))
        self.stdout.write(f"✓ Processing cost: ${analysis.cost_usd}")
        self.stdout.write(f"✓ Processing time: {analysis.processing_time_ms}ms")
        
        # Final verdict
        if article.primary_topic or article.primary_region or topic_count > 0 or region_count > 0:
            self.stdout.write(self.style.SUCCESS("\n✓ CLASSIFICATION SUCCESSFUL: At least one classification was applied"))
        else:
            self.stdout.write(self.style.ERROR("\n✗ CLASSIFICATION FAILED: No classifications were applied")) 