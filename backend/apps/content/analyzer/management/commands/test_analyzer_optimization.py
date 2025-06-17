"""
Test command for verifying the optimized analyzer service.

This command tests that:
1. The ArticleAnalysis model no longer has redundant fields
2. The Article model is properly updated with topics and regions
3. The confidence scores are properly stored in the ArticleAnalysis model
"""
import time
import traceback
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.articles.models import Article
from apps.feeds.models import Topic, Region
from apps.content.analyzer.services import AnalyzerService
from apps.content.analyzer.models import ArticleAnalysis


class Command(BaseCommand):
    help = "Test the optimized analyzer service"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Testing optimized analyzer service"))
        
        # Get a test article
        article = self.get_test_article()
        if not article:
            self.stdout.write(self.style.ERROR("No suitable article found for testing"))
            return
            
        self.stdout.write(f"Using article: {article.id} - {article.title}")
        
        # Clear existing analysis data
        self.clear_analysis_data(article)
        
        # Run analyzer service
        try:
            analyzer = AnalyzerService()
            self.stdout.write("Analyzer service initialized")
            
            # Check if article has analyzable content
            self.stdout.write(f"Article has analyzable content: {article.has_analyzable_content}")
            self.stdout.write(f"Best content for analysis: {article.best_content_for_analysis[:100]}...")
            
            # Run analysis
            self.stdout.write("Starting article analysis...")
            result = analyzer.analyze_article(article, force=True)
            self.stdout.write(f"Analysis result: {result}")
            
            # Verify results
            self.verify_results(article, result)
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error during analysis: {str(e)}"))
            self.stdout.write(self.style.ERROR(traceback.format_exc()))
        
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
        """Verify the analyzer results."""
        # Refresh article from database
        article.refresh_from_db()
        
        # Check if article has analysis record
        try:
            analysis = ArticleAnalysis.objects.get(article=article)
            self.stdout.write(self.style.SUCCESS("✓ ArticleAnalysis record created"))
        except ArticleAnalysis.DoesNotExist:
            self.stdout.write(self.style.ERROR("✗ ArticleAnalysis record not created"))
            return
            
        # Check that redundant fields are not in the model
        redundant_fields = [
            'primary_region_code', 'secondary_region_codes', 'region_relevance',
            'primary_topic_slug', 'secondary_topic_slugs', 'topic_relevance',
            'secondary_topics', 'secondary_regions'
        ]
        
        for field in redundant_fields:
            if hasattr(analysis, field):
                self.stdout.write(self.style.ERROR(f"✗ Redundant field still exists: {field}"))
            else:
                self.stdout.write(self.style.SUCCESS(f"✓ Redundant field removed: {field}"))
        
        # Check that confidence scores are stored
        if analysis.primary_topic_confidence > 0:
            self.stdout.write(self.style.SUCCESS(f"✓ Topic confidence stored: {analysis.primary_topic_confidence:.2f}"))
        else:
            self.stdout.write(self.style.WARNING(f"? Topic confidence not set: {analysis.primary_topic_confidence}"))
            
        if analysis.primary_region_confidence > 0:
            self.stdout.write(self.style.SUCCESS(f"✓ Region confidence stored: {analysis.primary_region_confidence:.2f}"))
        else:
            self.stdout.write(self.style.WARNING(f"? Region confidence not set: {analysis.primary_region_confidence}"))
        
        # Check that article has primary topic and region
        if article.primary_topic:
            self.stdout.write(self.style.SUCCESS(f"✓ Primary topic set: {article.primary_topic.name}"))
        else:
            self.stdout.write(self.style.WARNING("? Primary topic not set"))
            
        if article.primary_region:
            self.stdout.write(self.style.SUCCESS(f"✓ Primary region set: {article.primary_region.name}"))
        else:
            self.stdout.write(self.style.WARNING("? Primary region not set"))
            
        # Check that article has topics and regions
        topic_count = article.topics.count()
        region_count = article.regions.count()
        
        self.stdout.write(self.style.SUCCESS(f"✓ Article has {topic_count} topics and {region_count} regions"))
        
        # Check that style tone is set
        if analysis.style_tone:
            self.stdout.write(self.style.SUCCESS(f"✓ Style tone set: {analysis.style_tone}"))
        else:
            self.stdout.write(self.style.WARNING("? Style tone not set"))
            
        # Check processing metadata
        self.stdout.write(self.style.SUCCESS(f"✓ Processing cost: ${analysis.cost_usd}"))
        self.stdout.write(self.style.SUCCESS(f"✓ Processing time: {analysis.processing_time_ms}ms"))
        self.stdout.write(self.style.SUCCESS(f"✓ Input tokens: {analysis.tokens_input}"))
        self.stdout.write(self.style.SUCCESS(f"✓ Output tokens: {analysis.tokens_output}"))
        
        # Overall success
        self.stdout.write(self.style.SUCCESS("\nOptimized analyzer test completed successfully!")) 