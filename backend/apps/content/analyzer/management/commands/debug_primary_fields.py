"""
Debug command to test and verify primary_topic and primary_region field recording.

This command will:
1. Find articles that have been analyzed but may be missing primary fields
2. Run a single article through the analyzer with detailed debugging
3. Verify that primary fields are being set correctly
4. Identify any issues in the classification pipeline
"""
import logging
from decimal import Decimal
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.articles.models import Article, AnalyzerStatus
from apps.feeds.models import Topic, Region
from apps.content.analyzer.services import AnalyzerService
from apps.content.analyzer.models import ArticleAnalysis

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Debug primary_topic and primary_region field recording in analyzer'

    def add_arguments(self, parser):
        parser.add_argument(
            '--article-id',
            type=int,
            help='Specific article ID to test (optional)'
        )
        parser.add_argument(
            '--check-existing',
            action='store_true',
            help='Check existing analyzed articles for missing primary fields'
        )
        parser.add_argument(
            '--force-reanalyze',
            action='store_true',
            help='Force re-analysis of the test article'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("=== Primary Fields Debug Tool ===\n"))
        
        # Check existing analyzed articles first
        if options['check_existing']:
            self.check_existing_articles()
            self.stdout.write("")

        # Test specific article or find one automatically
        if options['article_id']:
            try:
                article = Article.objects.get(id=options['article_id'])
                self.test_article_analysis(article, force=options['force_reanalyze'])
            except Article.DoesNotExist:
                raise CommandError(f"Article with ID {options['article_id']} not found")
        else:
            # Find a suitable test article
            test_article = self.find_test_article()
            if test_article:
                self.test_article_analysis(test_article, force=options['force_reanalyze'])
            else:
                self.stdout.write(self.style.WARNING("No suitable test article found"))

    def check_existing_articles(self):
        """Check existing analyzed articles for missing primary fields."""
        self.stdout.write(self.style.SUCCESS("=== Checking Existing Analyzed Articles ==="))
        
        # Get analyzed articles
        analyzed_articles = Article.objects.filter(
            analyzer_status=AnalyzerStatus.COMPLETED
        )
        
        total_analyzed = analyzed_articles.count()
        
        if total_analyzed == 0:
            self.stdout.write("No analyzed articles found")
            return
            
        missing_topic = analyzed_articles.filter(primary_topic__isnull=True).count()
        missing_region = analyzed_articles.filter(primary_region__isnull=True).count()
        
        self.stdout.write(f"Total analyzed articles: {total_analyzed}")
        self.stdout.write(f"Missing primary_topic: {missing_topic} ({missing_topic/total_analyzed*100:.1f}%)")
        self.stdout.write(f"Missing primary_region: {missing_region} ({missing_region/total_analyzed*100:.1f}%)")
        
        # Show some examples
        if missing_topic > 0:
            self.stdout.write("\nArticles missing primary_topic:")
            for article in analyzed_articles.filter(primary_topic__isnull=True)[:5]:
                analysis = getattr(article, 'analyzer_result', None)
                topic_confidence = analysis.primary_topic_confidence if analysis else 0
                self.stdout.write(f"  - Article {article.id}: '{article.title[:60]}...' (confidence: {topic_confidence:.2f})")
        
        if missing_region > 0:
            self.stdout.write("\nArticles missing primary_region:")
            for article in analyzed_articles.filter(primary_region__isnull=True)[:5]:
                analysis = getattr(article, 'analyzer_result', None)
                region_confidence = analysis.primary_region_confidence if analysis else 0
                self.stdout.write(f"  - Article {article.id}: '{article.title[:60]}...' (confidence: {region_confidence:.2f})")

    def find_test_article(self):
        """Find a suitable article for testing."""
        # Prefer an article that has been analyzed but is missing primary fields
        test_article = Article.objects.filter(
            analyzer_status=AnalyzerStatus.COMPLETED,
            primary_topic__isnull=True
        ).first()
        
        if not test_article:
            # Fallback to any analyzed article
            test_article = Article.objects.filter(
                analyzer_status=AnalyzerStatus.COMPLETED
            ).first()
        
        if not test_article:
            # Fallback to any article with content
            test_article = Article.objects.filter(
                content__isnull=False
            ).exclude(content='').first()
        
        return test_article

    def test_article_analysis(self, article, force=False):
        """Test analysis of a specific article with detailed debugging."""
        self.stdout.write(self.style.SUCCESS(f"=== Testing Article {article.id} ==="))
        self.stdout.write(f"Title: {article.title}")
        self.stdout.write(f"Current status: {article.analyzer_status}")
        self.stdout.write(f"Current primary_topic: {article.primary_topic}")
        self.stdout.write(f"Current primary_region: {article.primary_region}")
        
        # Check if article has analysis record
        try:
            analysis = article.analyzer_result
            self.stdout.write(f"Analysis record exists: Yes")
            self.stdout.write(f"Topic confidence: {analysis.primary_topic_confidence:.2f}")
            self.stdout.write(f"Region confidence: {analysis.primary_region_confidence:.2f}")
        except ArticleAnalysis.DoesNotExist:
            self.stdout.write(f"Analysis record exists: No")
            analysis = None
        
        # Check available topics and regions
        topics_count = Topic.objects.count()
        regions_count = Region.objects.count()
        self.stdout.write(f"Available topics: {topics_count}")
        self.stdout.write(f"Available regions: {regions_count}")
        
        if topics_count == 0:
            self.stdout.write(self.style.ERROR("❌ No topics found in database - this will cause topic classification to fail"))
            return
            
        if regions_count == 0:
            self.stdout.write(self.style.ERROR("❌ No regions found in database - this will cause region classification to fail"))
            return
        
        # Show sample topics and regions
        self.stdout.write("\nSample topics:")
        for topic in Topic.objects.all()[:3]:
            self.stdout.write(f"  - {topic.slug}: {topic.name}")
            
        self.stdout.write("\nSample regions:")
        for region in Region.objects.all()[:3]:
            self.stdout.write(f"  - {region.code}: {region.name}")
        
        # Run analysis with debugging
        self.stdout.write(self.style.SUCCESS("\n=== Running Analysis ==="))
        
        # Create patched analyzer with debugging
        analyzer_service = AnalyzerService()
        
        # Store original methods
        original_region_method = analyzer_service._stage_6_region_classification
        original_topic_method = analyzer_service._stage_7_topic_classification
        
        # Create debug wrapper
        def debug_region_classification(article, content, analysis_record):
            self.stdout.write("🔍 Running region classification...")
            self.stdout.write(f"   Content length: {len(content)} chars")
            
            result = original_region_method(article, content, analysis_record)
            
            self.stdout.write(f"   Region result: {result}")
            
            if 'error' in result:
                self.stdout.write(self.style.ERROR(f"   ❌ Region classification error: {result['error']}"))
            else:
                primary_region = result.get('primary_region')
                confidence = result.get('primary_confidence', 0)
                self.stdout.write(f"   Primary region: {primary_region} (confidence: {confidence:.2f})")
                
                if primary_region and confidence >= 0.5:
                    # Check if region exists
                    try:
                        region_obj = Region.objects.get(code=primary_region)
                        self.stdout.write(f"   ✓ Region exists in database: {region_obj.name}")
                        
                        # Check if article was updated
                        article.refresh_from_db()
                        if article.primary_region and article.primary_region.code == primary_region:
                            self.stdout.write(f"   ✓ Article primary_region set successfully")
                        else:
                            self.stdout.write(f"   ❌ Article primary_region NOT set (current: {article.primary_region})")
                    except Region.DoesNotExist:
                        self.stdout.write(f"   ❌ Region {primary_region} does not exist in database")
                else:
                    self.stdout.write(f"   ⚠️  Primary region not set (confidence {confidence:.2f} < 0.5 threshold)")
            
            return result
        
        def debug_topic_classification(article, content, analysis_record):
            self.stdout.write("🔍 Running topic classification...")
            self.stdout.write(f"   Content length: {len(content)} chars")
            
            result = original_topic_method(article, content, analysis_record)
            
            self.stdout.write(f"   Topic result: {result}")
            
            if 'error' in result:
                self.stdout.write(self.style.ERROR(f"   ❌ Topic classification error: {result['error']}"))
            else:
                primary_topic = result.get('primary_topic')
                confidence = result.get('primary_confidence', 0)
                self.stdout.write(f"   Primary topic: {primary_topic} (confidence: {confidence:.2f})")
                
                if primary_topic and confidence >= 0.5:
                    # Check if topic exists
                    try:
                        topic_obj = Topic.objects.get(slug=primary_topic)
                        self.stdout.write(f"   ✓ Topic exists in database: {topic_obj.name}")
                        
                        # Check if article was updated
                        article.refresh_from_db()
                        if article.primary_topic and article.primary_topic.slug == primary_topic:
                            self.stdout.write(f"   ✓ Article primary_topic set successfully")
                        else:
                            self.stdout.write(f"   ❌ Article primary_topic NOT set (current: {article.primary_topic})")
                    except Topic.DoesNotExist:
                        self.stdout.write(f"   ❌ Topic {primary_topic} does not exist in database")
                else:
                    self.stdout.write(f"   ⚠️  Primary topic not set (confidence {confidence:.2f} < 0.5 threshold)")
            
            return result
        
        # Patch the methods
        analyzer_service._stage_6_region_classification = debug_region_classification
        analyzer_service._stage_7_topic_classification = debug_topic_classification
        
        try:
            # Run analysis
            result = analyzer_service.analyze_article(article, force=force)
            
            self.stdout.write(self.style.SUCCESS("\n=== Analysis Results ==="))
            self.stdout.write(f"Success: {result.get('success', False)}")
            
            if result.get('success'):
                self.stdout.write(f"Duration: {result.get('duration_ms', 0)}ms")
                self.stdout.write(f"Cost: ${result.get('cost_usd', 0):.6f}")
                
                # Refresh article and check final state
                article.refresh_from_db()
                self.stdout.write(f"\nFinal article state:")
                self.stdout.write(f"  Primary topic: {article.primary_topic}")
                self.stdout.write(f"  Primary region: {article.primary_region}")
                self.stdout.write(f"  Secondary topics: {article.topics.count()}")
                self.stdout.write(f"  Secondary regions: {article.regions.count()}")
                
                # Check analysis record
                try:
                    analysis = article.analyzer_result
                    self.stdout.write(f"  Topic confidence: {analysis.primary_topic_confidence:.2f}")
                    self.stdout.write(f"  Region confidence: {analysis.primary_region_confidence:.2f}")
                except ArticleAnalysis.DoesNotExist:
                    self.stdout.write(f"  No analysis record found")
            else:
                self.stdout.write(self.style.ERROR(f"Analysis failed: {result.get('error', 'Unknown error')}"))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Analysis exception: {str(e)}"))
            import traceback
            self.stdout.write(traceback.format_exc())
        
        self.stdout.write(self.style.SUCCESS("\n=== Debug Complete ===")) 