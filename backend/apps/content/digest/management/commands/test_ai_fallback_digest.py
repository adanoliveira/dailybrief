"""
Test command for AI-powered fallback digest generation.

Tests the new generate_fallback_topic_summary method to ensure it creates
proper topic summaries with title, abstract, facts, opinions, and impacts.
"""

import logging
from datetime import datetime, date
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.feeds.models import Topic
from apps.articles.models import Article
from apps.content.digest.services.ai_generator import DigestAIGenerator

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Test AI-powered fallback topic summary generation'

    def add_arguments(self, parser):
        parser.add_argument(
            '--topic-id',
            type=int,
            help='Specific topic ID to test'
        )
        parser.add_argument(
            '--user-id',
            type=int,
            help='User ID for regional filtering'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=3,
            help='Number of articles to include (default: 3)'
        )

    def handle(self, *args, **options):
        """Test AI-powered fallback topic summary generation."""
        
        topic_id = options.get('topic_id')
        user_id = options.get('user_id')
        limit = options.get('limit', 3)
        
        self.stdout.write("Testing AI-powered fallback topic summary generation...")
        
        # Get topic
        if topic_id:
            try:
                topic = Topic.objects.get(id=topic_id)
            except Topic.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Topic with ID {topic_id} not found"))
                return
        else:
            # Get the first available topic with processed articles
            topic = Topic.objects.filter(
                articles__summarization_status='completed'
            ).first()
            
            if not topic:
                self.stdout.write(self.style.ERROR("No topics found with processed articles"))
                return
        
        self.stdout.write(f"Testing with topic: {topic.name}")
        
        # Get user for regional filtering (optional)
        user = None
        if user_id:
            try:
                user = User.objects.get(id=user_id)
                self.stdout.write(f"Using user: {user.username}")
            except User.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"User with ID {user_id} not found, proceeding without user"))
        
        # Get articles for this topic with summaries
        target_date = date.today()
        articles_query = Article.objects.filter(
            summarization_status='completed',
            analyzer_status='completed'
        ).select_related('primary_topic', 'structured_summary', 'publication')
        
        # Filter by topic - try primary_topic first, then many-to-many
        primary_topic_articles = articles_query.filter(primary_topic=topic)[:limit]
        
        if not primary_topic_articles.exists():
            # Fallback to many-to-many relationship
            many_to_many_articles = articles_query.filter(topics=topic)[:limit]
            articles = list(many_to_many_articles)
        else:
            articles = list(primary_topic_articles)
        
        if not articles:
            self.stdout.write(self.style.ERROR(f"No articles with summaries found for topic {topic.name}"))
            return
        
        self.stdout.write(f"Found {len(articles)} articles with summaries:")
        for i, article in enumerate(articles, 1):
            summary = article.structured_summary
            self.stdout.write(f"  {i}. {article.title[:80]}...")
            self.stdout.write(f"     Facts: {len(summary.facts) if summary and summary.facts else 0}")
            self.stdout.write(f"     Opinions: {len(summary.opinions) if summary and summary.opinions else 0}")
            self.stdout.write(f"     Impact: {len(summary.impact) if summary and summary.impact else 0}")
        
        # Test AI generation
        self.stdout.write("\n" + "="*60)
        self.stdout.write("Testing AI-powered fallback topic summary generation...")
        self.stdout.write("="*60)
        
        ai_generator = DigestAIGenerator()
        
        try:
            # Generate AI-powered topic summary
            start_time = datetime.now()
            
            topic_summary = ai_generator.generate_fallback_topic_summary(
                topic_data={
                    'topic': topic,
                    'articles': articles
                }
            )
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Display results
            self.stdout.write(self.style.SUCCESS(f"✅ AI generation completed in {duration:.2f} seconds"))
            self.stdout.write(f"💰 Cost: ${topic_summary.get('cost', 0):.6f}")
            self.stdout.write(f"🔢 Tokens: {topic_summary.get('tokens_input', 0)} in / {topic_summary.get('tokens_output', 0)} out")
            self.stdout.write(f"🤖 Model: {topic_summary.get('model_used', 'unknown')}")
            
            self.stdout.write("\n📋 Generated Topic Summary:")
            self.stdout.write("-" * 40)
            
            # Display title
            title = topic_summary.get('title', 'No title')
            self.stdout.write(f"📰 Title: {title}")
            self.stdout.write(f"   Length: {len(title.split())} words")
            
            # Display abstract
            abstract = topic_summary.get('abstract', 'No abstract')
            self.stdout.write(f"\n📝 Abstract: {abstract}")
            self.stdout.write(f"   Length: {len(abstract.split())} words (target: ≤60)")
            
            # Display facts
            facts = topic_summary.get('facts', [])
            self.stdout.write(f"\n📊 Facts ({len(facts)}):")
            for i, fact in enumerate(facts, 1):
                self.stdout.write(f"   {i}. {fact}")
            
            # Display opinions
            opinions = topic_summary.get('opinions', [])
            self.stdout.write(f"\n💭 Opinions ({len(opinions)}):")
            for i, opinion in enumerate(opinions, 1):
                self.stdout.write(f"   {i}. {opinion}")
            
            # Display impacts
            impacts = topic_summary.get('impacts', [])
            self.stdout.write(f"\n🎯 Impacts ({len(impacts)}):")
            for i, impact in enumerate(impacts, 1):
                self.stdout.write(f"   {i}. {impact}")
            
            # Validation checks
            self.stdout.write("\n🔍 Validation Results:")
            self.stdout.write("-" * 30)
            
            # Check abstract length
            abstract_words = len(abstract.split())
            if abstract_words <= 60:
                self.stdout.write(self.style.SUCCESS(f"✅ Abstract length: {abstract_words}/60 words"))
            else:
                self.stdout.write(self.style.WARNING(f"⚠️  Abstract too long: {abstract_words}/60 words"))
            
            # Check title length
            title_words = len(title.split())
            if title_words <= 15:
                self.stdout.write(self.style.SUCCESS(f"✅ Title length: {title_words}/15 words"))
            else:
                self.stdout.write(self.style.WARNING(f"⚠️  Title too long: {title_words}/15 words"))
            
            # Check content counts
            if 3 <= len(facts) <= 6:
                self.stdout.write(self.style.SUCCESS(f"✅ Facts count: {len(facts)} (target: 3-6)"))
            else:
                self.stdout.write(self.style.WARNING(f"⚠️  Facts count: {len(facts)} (target: 3-6)"))
            
            if 2 <= len(opinions) <= 5:
                self.stdout.write(self.style.SUCCESS(f"✅ Opinions count: {len(opinions)} (target: 2-5)"))
            else:
                self.stdout.write(self.style.WARNING(f"⚠️  Opinions count: {len(opinions)} (target: 2-5)"))
            
            if 2 <= len(impacts) <= 3:
                self.stdout.write(self.style.SUCCESS(f"✅ Impacts count: {len(impacts)} (target: 2-3)"))
            else:
                self.stdout.write(self.style.WARNING(f"⚠️  Impacts count: {len(impacts)} (target: 2-3)"))
            
            # Check for error
            if topic_summary.get('error'):
                self.stdout.write(self.style.ERROR(f"❌ Error occurred: {topic_summary['error']}"))
            else:
                self.stdout.write(self.style.SUCCESS("✅ No errors detected"))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ AI generation failed: {str(e)}"))
            logger.exception("Failed to generate AI fallback topic summary")
        
        self.stdout.write("\nTest completed!") 