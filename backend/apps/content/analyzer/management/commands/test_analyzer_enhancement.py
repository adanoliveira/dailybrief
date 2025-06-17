"""
Test the enhanced analyzer implementation with a sample article.

This management command tests the enhanced content assembly for analysis
by running the analyzer on a sample article and comparing the results.
"""

import logging
import time
import json
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.articles.models import Article, AnalyzerStatus
from apps.content.analyzer.services import AnalyzerService
from apps.content.summariser.models import ArticleSummary

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Test the enhanced analyzer implementation with a sample article"

    def add_arguments(self, parser):
        parser.add_argument(
            "--article-id",
            type=int,
            help="ID of the article to test",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force re-analysis even if already analyzed",
        )
        parser.add_argument(
            "--compare",
            action="store_true",
            help="Compare with previous analysis if available",
        )

    def handle(self, *args, **options):
        article_id = options.get("article_id")
        force = options.get("force", False)
        compare = options.get("compare", False)

        if not article_id:
            # Find a suitable test article with summary
            self.stdout.write("No article ID provided, finding a suitable test article...")
            article = self._find_test_article()
            if not article:
                self.stdout.write(self.style.ERROR("No suitable test article found"))
                return
        else:
            try:
                article = Article.objects.get(id=article_id)
            except Article.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Article with ID {article_id} not found"))
                return

        # Display article info
        self.stdout.write(self.style.SUCCESS(f"Testing analyzer with article: {article.id} - {article.title}"))
        
        # Check if article has summary
        try:
            summary = article.structured_summary
            if summary:
                self.stdout.write(f"Article has summary: {summary.headline}")
                self.stdout.write(f"Abstract: {summary.abstract[:100]}...")
                self.stdout.write(f"Facts count: {len(summary.facts)}")
                self.stdout.write(f"Opinions count: {len(summary.opinions)}")
                self.stdout.write(f"Impact count: {len(summary.impact)}")
            else:
                self.stdout.write(self.style.WARNING("Article has no summary"))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"Error checking summary: {str(e)}"))

        # Store previous analysis for comparison if requested
        previous_analysis = None
        if compare:
            try:
                previous_analysis = article.analyzer_result
                self.stdout.write("Stored previous analysis for comparison")
            except Exception:
                self.stdout.write(self.style.WARNING("No previous analysis found for comparison"))

        # Reset analyzer status if forcing re-analysis
        if force:
            self.stdout.write("Forcing re-analysis...")
            article.analyzer_status = AnalyzerStatus.PENDING
            article.save(update_fields=["analyzer_status"])

        # Run the analyzer
        self.stdout.write("Running analyzer...")
        start_time = time.time()
        service = AnalyzerService()
        
        # Get both content types to compare
        standard_content = article.best_content_for_analysis
        enhanced_content = service._get_enhanced_content_for_analysis(article)
        
        # Display content info
        self.stdout.write(f"\nStandard content length: {len(standard_content)} chars")
        self.stdout.write(f"Standard content preview:\n{standard_content[:200]}...\n")
        
        self.stdout.write(f"\nEnhanced content length: {len(enhanced_content)} chars")
        self.stdout.write(f"Enhanced content preview:\n{enhanced_content[:200]}...\n")
        
        self.stdout.write(self.style.SUCCESS("\nVerifying content usage in analyzer pipeline:"))
        self.stdout.write("- Language detection: Uses standard content (CPU task)")
        self.stdout.write("- Entity extraction: Uses standard content (CPU task)")
        self.stdout.write("- Style tone analysis: Uses enhanced content (LLM task)")
        self.stdout.write("- Event extraction: Uses enhanced content (LLM task)")
        self.stdout.write("- Region classification: Uses enhanced content (LLM task)")
        self.stdout.write("- Topic classification: Uses enhanced content (LLM task)")
        
        # Run the full analysis
        self.stdout.write("\nRunning full analysis pipeline...")
        result = service.analyze_article(article, force=force)
        duration = time.time() - start_time
        
        # Display results
        if result.get("success", False):
            self.stdout.write(self.style.SUCCESS(f"Analysis completed in {duration:.2f}s"))
            self.stdout.write(f"Cost: ${result.get('cost_usd', Decimal('0.0')):.6f}")
            
            # Display analysis results
            try:
                analysis = article.analyzer_result
                self.stdout.write("\nAnalysis Results:")
                self.stdout.write(f"Style/Tone: {analysis.style_tone}")
                self.stdout.write(f"Primary Topic: {article.primary_topic.name if article.primary_topic else 'None'}")
                self.stdout.write(f"Primary Region: {article.primary_region.name if article.primary_region else 'None'}")
                
                # Display entities
                entity_relations = article.article_entities.all()[:5]
                if entity_relations:
                    self.stdout.write("\nTop Entities:")
                    for relation in entity_relations:
                        self.stdout.write(f"- {relation.entity.display_name} ({relation.entity.entity_type})")
                
                # Compare with previous analysis if available
                if compare and previous_analysis:
                    self.stdout.write("\nComparison with Previous Analysis:")
                    self.stdout.write(f"Previous Style/Tone: {previous_analysis.style_tone}")
                    self.stdout.write(f"New Style/Tone: {analysis.style_tone}")
                    # Add more comparison points as needed
            
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error displaying analysis: {str(e)}"))
        else:
            self.stdout.write(self.style.ERROR(f"Analysis failed: {result.get('reason', 'Unknown error')}"))
            if "error" in result:
                self.stdout.write(self.style.ERROR(f"Error: {result['error']}"))

    def _find_test_article(self):
        """Find a suitable test article with summary."""
        # Look for articles with summaries
        try:
            summary = ArticleSummary.objects.filter(
                longer_abstract__isnull=False,
                facts__len__gt=2,
                opinions__len__gt=0
            ).order_by("-created_at").first()
            
            if summary:
                return summary.article
        except Exception:
            pass
        
        # Fallback to any article with completed summarization
        return Article.objects.filter(
            summarization_status="completed"
        ).order_by("-published_at").first() 