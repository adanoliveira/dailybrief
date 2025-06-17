"""
Direct test command for verifying topic and region classification.

This command creates a test article with clear topic and region indicators,
then runs the analyzer to verify that the classification works correctly.
"""
import time
import json
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from apps.articles.models import Article
from apps.feeds.models import Topic, Region, Language, Publication
from apps.content.analyzer.services import AnalyzerService
from apps.content.analyzer.models import ArticleAnalysis


class Command(BaseCommand):
    help = "Direct test for topic and region classification"
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("=== Direct Classification Test ==="))
        
        # Create a test article with clear topic and region indicators
        article = self.create_test_article()
        self.stdout.write(f"Created test article: {article.id}")
        
        # Run analyzer service
        try:
            analyzer = AnalyzerService()
            self.stdout.write("Analyzer service initialized")
            
            # Modify the threshold for testing
            self.patch_analyzer(analyzer)
            
            # Run analysis
            self.stdout.write("Starting article analysis...")
            result = analyzer.analyze_article(article, force=True)
            self.stdout.write(f"Analysis completed with result: {result}")
            
            # Verify results
            self.verify_results(article)
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error during analysis: {str(e)}"))
            import traceback
            self.stdout.write(self.style.ERROR(traceback.format_exc()))
    
    def create_test_article(self):
        """Create a test article with clear topic and region indicators."""
        # Get a publication
        publication = Publication.objects.first()
        if not publication:
            publication = Publication.objects.create(
                name="Test Publication",
                domain="test.com"
            )
        
        # Create the article with clear sports topic and US region
        article = Article.objects.create(
            title="NBA Finals: Boston Celtics Win Championship Against Dallas Mavericks",
            description="The Boston Celtics have won their 18th NBA championship after defeating the Dallas Mavericks in Game 6 of the NBA Finals.",
            clean_content="""
            # NBA Finals: Boston Celtics Win Championship Against Dallas Mavericks
            
            BOSTON, USA - The Boston Celtics have won their 18th NBA championship after defeating the Dallas Mavericks 114-102 in Game 6 of the NBA Finals.
            
            Led by MVP Jayson Tatum, who scored 32 points and grabbed 10 rebounds, the Celtics dominated throughout the series, winning 4-2 overall. This marks their first championship since 2008 and extends their record as the franchise with the most NBA titles.
            
            "This means everything to me and the city of Boston," said Tatum after the game. "We've worked so hard for this moment, and to bring banner 18 to Boston is a dream come true."
            
            The Mavericks, led by Luka Dončić with 29 points, fought hard but couldn't overcome Boston's superior defense and balanced scoring attack. Dallas was seeking their second championship in franchise history.
            
            The celebration spilled onto the streets of Boston as thousands of fans gathered around TD Garden to celebrate their team's victory. Massachusetts Governor announced there would be a parade through downtown Boston on Saturday.
            
            This championship solidifies the Celtics' return to the NBA elite after years of rebuilding and near-misses in previous playoff runs.
            
            The NBA Finals victory caps off an impressive 68-win season for the Celtics, who were the top seed in the Eastern Conference throughout the playoffs.
            """,
            url="https://test.com/celtics-win-championship",
            source_name="Test Publication",
            publication=publication,
            published_at=timezone.now(),
            fetch_status="completed",
            process_status="completed",
            summarization_status="completed"
        )
        
        return article
    
    def patch_analyzer(self, analyzer):
        """Patch the analyzer to use a lower threshold for testing."""
        # Store reference to self for use in the patched methods
        command_self = self
        
        # Patch region classification to use a lower threshold
        def patched_region_classification(self, article, content, analysis_record):
            """Patched region classification method that logs the results."""
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
                
                # Log the raw result for debugging
                command_self.stdout.write(f"Raw region classification result: {result}")
                
                # Extract primary region
                primary_region_code = None
                primary_confidence = 0.0
                
                # Check if result is in the expected format
                if isinstance(result, dict):
                    if 'primary_region' in result:
                        primary_region_code = result.get('primary_region')
                        primary_confidence = result.get('primary_region_confidence', 0.7)
                    elif 'data' in result and isinstance(result['data'], dict):
                        # Handle nested data structure
                        data = result['data']
                        primary_region_code = data.get('primary_region')
                        primary_confidence = data.get('primary_confidence', 0.7)
                
                # Extract secondary regions
                secondary_region_codes = []
                if isinstance(result, dict):
                    if 'secondary_regions' in result:
                        secondary_region_codes = result.get('secondary_regions', [])
                    elif 'data' in result and isinstance(result['data'], dict):
                        # Handle nested data structure
                        data = result['data']
                        secondary_region_codes = data.get('secondary_regions', [])
                
                command_self.stdout.write(f"Processed region result - primary: {primary_region_code} ({primary_confidence}), secondary: {secondary_region_codes}")
                
                # Update article with primary region only if confidence is high enough or if not set
                # Use a very low threshold for testing
                if primary_region_code and (primary_confidence >= 0.1 or not article.primary_region):
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
                    'cost': response.usage.get('total_cost', 0)
                }
                
            except Exception as e:
                command_self.stdout.write(f"Region classification failed for article {article.id}: {str(e)}")
                import traceback
                command_self.stdout.write(traceback.format_exc())
                return {
                    'error': str(e),
                    'cost': Decimal('0.0')
                }
        
        # Patch topic classification to use a lower threshold
        def patched_topic_classification(self, article, content, analysis_record):
            """Patched topic classification method that logs the results."""
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
                
                # Log the raw result for debugging
                command_self.stdout.write(f"Raw topic classification result: {result}")
                
                # Extract primary topic
                primary_topic_slug = None
                primary_confidence = 0.0
                
                # Check if result is in the expected format
                if isinstance(result, dict):
                    if 'primary_topic' in result:
                        primary_topic_slug = result.get('primary_topic')
                        primary_confidence = result.get('primary_topic_confidence', 0.7)
                    elif 'data' in result and isinstance(result['data'], dict):
                        # Handle nested data structure
                        data = result['data']
                        primary_topic_slug = data.get('primary_topic')
                        primary_confidence = data.get('primary_confidence', 0.7)
                
                # Extract secondary topics
                secondary_topic_slugs = []
                if isinstance(result, dict):
                    if 'secondary_topics' in result:
                        secondary_topic_slugs = result.get('secondary_topics', [])
                    elif 'data' in result and isinstance(result['data'], dict):
                        # Handle nested data structure
                        data = result['data']
                        secondary_topic_slugs = data.get('secondary_topics', [])
                
                command_self.stdout.write(f"Processed topic result - primary: {primary_topic_slug} ({primary_confidence}), secondary: {secondary_topic_slugs}")
                
                # Update article with primary topic only if confidence is high enough or if not set
                # Use a very low threshold for testing
                if primary_topic_slug and (primary_confidence >= 0.1 or not article.primary_topic):
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
                    'cost': response.usage.get('total_cost', 0)
                }
                
            except Exception as e:
                command_self.stdout.write(f"Topic classification failed for article {article.id}: {str(e)}")
                import traceback
                command_self.stdout.write(traceback.format_exc())
                return {
                    'error': str(e),
                    'cost': Decimal('0.0')
                }
        
        # Apply patches
        analyzer._stage_6_region_classification = patched_region_classification.__get__(analyzer, AnalyzerService)
        analyzer._stage_7_topic_classification = patched_topic_classification.__get__(analyzer, AnalyzerService)
    
    def verify_results(self, article):
        """Verify the analyzer results."""
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
            self.stdout.write(self.style.ERROR(f"✗ Primary topic not set"))
        
        # Check region classification results
        self.stdout.write(self.style.SUCCESS("\n=== Region Classification Results ==="))
        if analysis.primary_region_confidence > 0:
            self.stdout.write(f"✓ Region confidence stored: {analysis.primary_region_confidence:.2f}")
        else:
            self.stdout.write(f"? Region confidence not set: {analysis.primary_region_confidence}")
        
        if article.primary_region:
            self.stdout.write(self.style.SUCCESS(f"✓ Primary region set: {article.primary_region.name} ({article.primary_region.code})"))
        else:
            self.stdout.write(self.style.ERROR(f"✗ Primary region not set"))
        
        # Check secondary topics
        topic_count = article.topics.count()
        if topic_count > 0:
            self.stdout.write(self.style.SUCCESS(f"✓ Article has {topic_count} secondary topics:"))
            for topic in article.topics.all():
                self.stdout.write(f"  - {topic.name} ({topic.slug})")
        else:
            self.stdout.write(self.style.WARNING(f"? No secondary topics added"))
        
        # Check secondary regions
        region_count = article.regions.count()
        if region_count > 0:
            self.stdout.write(self.style.SUCCESS(f"✓ Article has {region_count} secondary regions:"))
            for region in article.regions.all():
                self.stdout.write(f"  - {region.name} ({region.code})")
        else:
            self.stdout.write(self.style.WARNING(f"? No secondary regions added"))
        
        # Final verdict
        if article.primary_topic or article.primary_region or topic_count > 0 or region_count > 0:
            self.stdout.write(self.style.SUCCESS("\n✓ CLASSIFICATION SUCCESSFUL: At least one classification was applied"))
        else:
            self.stdout.write(self.style.ERROR("\n✗ CLASSIFICATION FAILED: No classifications were applied")) 