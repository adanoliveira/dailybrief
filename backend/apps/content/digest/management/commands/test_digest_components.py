"""
Management command to test individual digest components.

This command helps debug and validate specific parts of the digest system:
- Content selection and filtering
- Event grouping and ranking
- AI generation services
- Data model operations
"""

import logging
from datetime import datetime
from typing import List, Dict, Any

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.utils import timezone

from apps.content.digest.services import DigestService, DigestContentSelector, DigestAIGenerator
from apps.content.digest.models import Digest

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = """
    Test individual digest components for debugging.
    
    Examples:
    - Test content selection: --test content-selection --user-id 123
    - Test AI generation: --test ai-generation --user-id 123
    - Test full pipeline: --test full-pipeline --user-id 123
    - List available users: --list-users
    """
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--test',
            type=str,
            choices=['content-selection', 'ai-generation', 'full-pipeline'],
            help='Component to test'
        )
        
        parser.add_argument(
            '--user-id',
            type=int,
            help='User ID to test with'
        )
        
        parser.add_argument(
            '--username',
            type=str,
            help='Username to test with'
        )
        
        parser.add_argument(
            '--list-users',
            action='store_true',
            help='List users with followed topics'
        )
        
        parser.add_argument(
            '--date',
            type=str,
            help='Target date for testing (YYYY-MM-DD format, defaults to today)'
        )
        
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output'
        )
    
    def handle(self, *args, **options):
        """Main command handler."""
        
        if options['list_users']:
            self._list_available_users()
            return
        
        if not options['test']:
            raise CommandError("Must specify --test or --list-users")
        
        # Get user
        user = self._get_user(options)
        target_date = self._parse_target_date(options['date'])
        
        self.stdout.write(
            f"🧪 Testing {options['test']} for user {user.username} on {target_date.date()}"
        )
        
        # Run the appropriate test
        if options['test'] == 'content-selection':
            self._test_content_selection(user, target_date, options['verbose'])
        elif options['test'] == 'ai-generation':
            self._test_ai_generation(user, target_date, options['verbose'])
        elif options['test'] == 'full-pipeline':
            self._test_full_pipeline(user, target_date, options['verbose'])
    
    def _get_user(self, options) -> User:
        """Get user from options."""
        if options['user_id']:
            try:
                return User.objects.get(id=options['user_id'])
            except User.DoesNotExist:
                raise CommandError(f"User with ID {options['user_id']} not found")
        
        elif options['username']:
            try:
                return User.objects.get(username=options['username'])
            except User.DoesNotExist:
                raise CommandError(f"User '{options['username']}' not found")
        
        else:
            raise CommandError("Must specify either --user-id or --username")
    
    def _parse_target_date(self, date_str) -> datetime:
        """Parse target date from string or use today."""
        if date_str:
            try:
                parsed_date = datetime.strptime(date_str, '%Y-%m-%d')
                return timezone.make_aware(parsed_date)
            except ValueError:
                raise CommandError(f"Invalid date format: {date_str}. Use YYYY-MM-DD")
        
        return timezone.now()
    
    def _list_available_users(self):
        """List users with followed topics."""
        users = User.objects.filter(
            is_active=True,
            user_topics__isnull=False
        ).distinct().prefetch_related('user_topics__topic')
        
        if not users:
            self.stdout.write("No active users with followed topics found")
            return
        
        self.stdout.write("👥 Available users with followed topics:")
        self.stdout.write("-" * 50)
        
        for user in users[:20]:  # Show first 20
            topics = list(user.user_topics.values_list('topic__name', flat=True))
            self.stdout.write(
                f"ID: {user.id:3d} | {user.username:20s} | Topics: {', '.join(topics[:3])}"
                + ("..." if len(topics) > 3 else "")
            )
        
        if users.count() > 20:
            self.stdout.write(f"... and {users.count() - 20} more users")
    
    def _test_content_selection(self, user: User, target_date: datetime, verbose: bool):
        """Test content selection functionality."""
        self.stdout.write("🔍 Testing content selection...")
        
        try:
            selector = DigestContentSelector()
            
            # Step 1: Get date range
            date_range = selector.get_date_range_for_digest(target_date, user.profile.timezone)
            self.stdout.write(f"📅 Date range: {date_range[0]} to {date_range[1]}")
            
            # Step 2: Get user articles
            articles = selector.get_user_articles(user, date_range)
            article_count = articles.count()
            self.stdout.write(f"📰 Found {article_count} articles")
            
            if article_count == 0:
                self.stdout.write("⚠️  No articles found - digest will be empty")
                return
            
            if verbose and article_count > 0:
                self.stdout.write("\n📰 Sample articles:")
                for article in articles[:5]:
                    self.stdout.write(f"  - {article.headline[:60]}...")
            
            # Step 3: Group by topic and event
            grouped_data = selector.group_articles_by_topic_and_event(articles)
            self.stdout.write(f"🗂️  Grouped into {len(grouped_data)} topics")
            
            if verbose:
                for topic_id, topic_data in grouped_data.items():
                    topic = topic_data['topic']
                    events = topic_data['events']
                    self.stdout.write(f"\n📝 Topic: {topic.name}")
                    self.stdout.write(f"   Events: {len(events)}")
                    
                    for event_id, event_data in list(events.items())[:3]:  # Show top 3
                        event = event_data['event']
                        score = event_data['score']
                        self.stdout.write(f"   - {event.title[:50]}... (score: {score})")
            
            # Step 4: Select final content
            user_preferences = user.profile.get_digest_preferences()
            digest_content = selector.select_digest_content(grouped_data, user_preferences)
            
            selected_topics = len(digest_content)
            total_events = sum(len(topic_data['events']) for topic_data in digest_content.values())
            
            self.stdout.write(f"✅ Selected {selected_topics} topics with {total_events} events")
            
            if verbose and digest_content:
                self.stdout.write("\n🎯 Final selection:")
                for topic_id, topic_data in digest_content.items():
                    topic = topic_data['topic']
                    events = topic_data['events']
                    self.stdout.write(f"  📝 {topic.name}: {len(events)} events")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Content selection failed: {e}"))
            logger.exception("Content selection test failed")
    
    def _test_ai_generation(self, user: User, target_date: datetime, verbose: bool):
        """Test AI generation functionality."""
        self.stdout.write("🤖 Testing AI generation...")
        
        try:
            # First get some content to enhance
            selector = DigestContentSelector()
            date_range = selector.get_date_range_for_digest(target_date, user.profile.timezone)
            articles = selector.get_user_articles(user, date_range)
            
            if not articles.exists():
                self.stdout.write("⚠️  No articles available for AI testing")
                return
            
            grouped_data = selector.group_articles_by_topic_and_event(articles)
            user_preferences = user.profile.get_digest_preferences()
            digest_content = selector.select_digest_content(grouped_data, user_preferences)
            
            if not digest_content:
                self.stdout.write("⚠️  No content selected for AI testing")
                return
            
            # Test AI generation
            ai_generator = DigestAIGenerator()
            
            # Test digest introduction
            self.stdout.write("📝 Generating digest introduction...")
            intro_result = ai_generator.generate_digest_introduction(digest_content)
            
            if 'error' in intro_result:
                self.stdout.write(f"❌ Introduction generation failed: {intro_result['error']}")
            else:
                self.stdout.write(f"✅ Introduction generated ({len(intro_result['introduction'])} chars)")
                if verbose:
                    self.stdout.write(f"💬 Introduction: {intro_result['introduction'][:200]}...")
            
            # Test topic summary generation
            self.stdout.write("📋 Testing topic summary generation...")
            topic_id, topic_data = next(iter(digest_content.items()))
            topic_result = ai_generator.generate_topic_summary(topic_data)
            
            if 'error' in topic_result:
                self.stdout.write(f"❌ Topic summary failed: {topic_result['error']}")
            else:
                facts_count = len(topic_result.get('main_facts', []))
                perspectives_count = len(topic_result.get('perspectives', []))
                self.stdout.write(f"✅ Topic summary generated ({facts_count} facts, {perspectives_count} perspectives)")
                
                if verbose:
                    self.stdout.write(f"📊 Abstract: {topic_result.get('topic_abstract', '')[:200]}...")
            
            # Test event enhancement
            if topic_data['events']:
                self.stdout.write("🎯 Testing event enhancement...")
                event_data = topic_data['events'][0]
                event_result = ai_generator.enhance_event_summary(event_data)
                
                if 'error' in event_result:
                    self.stdout.write(f"❌ Event enhancement failed: {event_result['error']}")
                else:
                    facts_count = len(event_result.get('key_facts', []))
                    perspectives_count = len(event_result.get('perspectives', []))
                    self.stdout.write(f"✅ Event enhanced ({facts_count} facts, {perspectives_count} perspectives)")
            
            # Show metrics
            metrics = ai_generator.get_generation_metrics()
            self.stdout.write(
                f"💰 AI Metrics: ${metrics['total_cost_usd']:.4f} cost, "
                f"{metrics['total_tokens']} tokens"
            )
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ AI generation failed: {e}"))
            logger.exception("AI generation test failed")
    
    def _test_full_pipeline(self, user: User, target_date: datetime, verbose: bool):
        """Test the complete digest generation pipeline."""
        self.stdout.write("🚀 Testing full digest generation pipeline...")
        
        try:
            digest_service = DigestService()
            
            # Generate digest
            result = digest_service.generate_digest(
                user=user,
                target_date=target_date,
                regenerate=True  # Force regeneration for testing
            )
            
            if result['success']:
                digest = result['digest']
                metrics = result.get('metrics', {})
                
                self.stdout.write(self.style.SUCCESS("✅ Full pipeline test successful!"))
                self.stdout.write(
                    f"📊 Digest created: {digest.public_id}\n"
                    f"   Topics: {metrics.get('topics_included', 0)}\n"
                    f"   Events: {metrics.get('total_events', 0)}\n"
                    f"   Articles: {metrics.get('articles_processed', 0)}\n"
                    f"   Cost: ${metrics.get('total_cost_usd', 0):.4f}\n"
                    f"   Time: {metrics.get('generation_time_seconds', 0):.2f}s"
                )
                
                if verbose:
                    self.stdout.write(f"\n📖 Digest preview:")
                    self.stdout.write(f"Title: {digest.title}")
                    self.stdout.write(f"Introduction: {digest.introduction[:200]}...")
                    
                    # Show topic breakdown
                    for digest_topic in digest.digest_topics.all():
                        story_count = digest_topic.stories.count()
                        self.stdout.write(f"  📝 {digest_topic.topic.name}: {story_count} stories")
                
            else:
                error = result.get('error', 'Unknown error')
                self.stdout.write(self.style.ERROR(f"❌ Pipeline test failed: {error}"))
                
                # Show any partial results
                if 'digest' in result:
                    digest = result['digest']
                    self.stdout.write(f"⚠️  Partial digest created: {digest.public_id}")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Full pipeline test failed: {e}"))
            logger.exception("Full pipeline test failed") 