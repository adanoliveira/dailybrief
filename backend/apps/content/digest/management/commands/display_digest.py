"""
Management command to display daily digest content in a readable format.

This command retrieves and displays the generated digest for a user in a
nicely formatted text output suitable for testing and review.
"""

import logging
from datetime import datetime, date
from typing import Optional

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import models

from apps.content.digest.models import Digest, DigestTopic, DigestStory
from apps.articles.models import Article
from apps.content.analyzer.models import Event, ArticleEvent

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = """
    Display daily digest content in readable format.
    
    Examples:
    - Display digest for specific user: --user-id 123
    - Display digest for username: --username john
    - Display digest for specific date: --date 2024-01-15
    - Display latest digest: --latest
    """
    
    def add_arguments(self, parser):
        # User selection
        parser.add_argument(
            '--user-id',
            type=int,
            help='Display digest for specific user ID'
        )
        
        parser.add_argument(
            '--username',
            type=str,
            help='Display digest for specific username'
        )
        
        parser.add_argument(
            '--email',
            type=str,
            help='Display digest for specific email'
        )
        
        # Date selection
        parser.add_argument(
            '--date',
            type=str,
            help='Target date for digest (YYYY-MM-DD format, defaults to today)'
        )
        
        parser.add_argument(
            '--latest',
            action='store_true',
            help='Display the latest digest for the user'
        )
        
        # Output options
        parser.add_argument(
            '--compact',
            action='store_true',
            help='Display in compact format (no stories details)'
        )
        
        parser.add_argument(
            '--show-articles',
            action='store_true',
            help='Show recommended articles for each story'
        )
        
        parser.add_argument(
            '--debug',
            action='store_true',
            help='Show detailed debugging information including article selection and event prioritization'
        )
    
    def handle(self, *args, **options):
        """Main command handler."""
        self.stdout.write(self.style.SUCCESS('📰 Displaying Daily Digest...'))
        
        try:
            # Get target user
            user = self._get_target_user(options)
            if not user:
                return
            
            # Get target digest
            digest = self._get_target_digest(user, options)
            if not digest:
                return
            
            # Display the digest
            self._display_digest(digest, options)
            
            # Debug information
            debug_summary = {}  # Track debug stats for summary
            if options['debug']:
                digest_topics = DigestTopic.objects.filter(digest=digest).order_by('order')
                for digest_topic in digest_topics:
                    topic_stats = self._display_topic_debug_info(digest_topic, digest)
                    debug_summary[digest_topic.topic.name] = topic_stats
                
                # Print debug summary
                self._print_debug_summary(debug_summary)
            
            # Show standard generation stats
            self._display_generation_stats(digest)
            
            self.stdout.write(self.style.SUCCESS(f"✅ Successfully displayed digest for {digest.user.username}"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error: {str(e)}"))
            if options['verbosity'] >= 2:
                import traceback
                traceback.print_exc()
    
    def _get_target_user(self, options) -> Optional[User]:
        """Get the target user based on options."""
        if options['user_id']:
            try:
                return User.objects.get(id=options['user_id'])
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"❌ User with ID {options['user_id']} not found")
                )
                return None
        
        elif options['username']:
            try:
                return User.objects.get(username=options['username'])
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"❌ User '{options['username']}' not found")
                )
                return None
        
        elif options['email']:
            try:
                return User.objects.get(email=options['email'])
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"❌ User with email '{options['email']}' not found")
                )
                return None
        
        else:
            # Default to the first user with email adan.arnord@gmail.com
            try:
                return User.objects.get(email='adan.arnord@gmail.com')
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR("❌ Please specify --user-id, --username, or --email")
                )
                return None
    
    def _get_target_digest(self, user: User, options) -> Optional[Digest]:
        """Get the target digest based on options."""
        if options['latest']:
            # Get the latest digest
            digest = Digest.objects.filter(
                user=user,
                generation_status='completed'
            ).order_by('-date').first()
            
            if not digest:
                self.stdout.write(
                    self.style.ERROR(f"❌ No completed digests found for {user.username}")
                )
                return None
            
            self.stdout.write(f"📅 Showing latest digest: {digest.date}")
            return digest
        
        # Parse target date
        if options['date']:
            try:
                target_date = datetime.strptime(options['date'], '%Y-%m-%d').date()
            except ValueError:
                self.stdout.write(
                    self.style.ERROR(f"❌ Invalid date format: {options['date']}. Use YYYY-MM-DD")
                )
                return None
        else:
            target_date = date.today()
        
        # Get digest for specific date
        try:
            digest = Digest.objects.get(user=user, date=target_date)
        except Digest.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"❌ No digest found for {user.username} on {target_date}")
            )
            return None
        
        if digest.generation_status != 'completed':
            self.stdout.write(
                self.style.WARNING(f"⚠️  Digest exists but status is: {digest.generation_status}")
            )
            if digest.error_message:
                self.stdout.write(f"Error: {digest.error_message}")
        
        return digest
    
    def _display_digest(self, digest: Digest, options):
        """Display the digest content."""
        # Header
        self.stdout.write("=" * 60)
        self.stdout.write(self.style.SUCCESS(f"🗞️  {digest.title}"))
        self.stdout.write(f"👤 User: {digest.user.username} ({digest.user.email})")
        self.stdout.write(f"📅 Date: {digest.date}")
        self.stdout.write(f"🕐 Generated: {digest.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        self.stdout.write("=" * 60)
        
        # Introduction
        if digest.introduction:
            self.stdout.write(self.style.WARNING("📝 INTRODUCTION"))
            self.stdout.write(digest.introduction)
            self.stdout.write("")
        
        # Topics
        topics = DigestTopic.objects.filter(digest=digest).order_by('order')
        
        for i, topic in enumerate(topics, 1):
            # Topic header
            self.stdout.write(self.style.SUCCESS(f"📂 {i}. {topic.topic.name.upper()}"))
            self.stdout.write("-" * 40)
            
            # Debug information
            if options['debug']:
                self._display_topic_debug_info(topic, digest)
            
            # Abstract (no title, just the text directly)
            if topic.topic_abstract:
                self.stdout.write(f"{topic.topic_abstract}")
                self.stdout.write("")
            
            # Stories (the new main content)
            stories = DigestStory.objects.filter(digest_topic=topic).order_by('order')
            if stories and not options['compact']:
                self.stdout.write("📰 TOP STORIES:")
                for story in stories:
                    self.stdout.write(f"  • {story.title}")
                    if story.enhanced_abstract:
                        self.stdout.write(f"    {story.enhanced_abstract}")
                    
                    # Key facts
                    if story.key_facts:
                        self.stdout.write("    📋 Main Points:")
                        for fact in story.key_facts[:5]:  # Show up to 5 facts
                            self.stdout.write(f"      - {fact}")
                    
                    # Key perspectives
                    if story.perspectives:
                        self.stdout.write("    💭 Key Perspectives:")
                        for perspective in story.perspectives[:3]:  # Show up to 3 perspectives
                            self.stdout.write(f"      - {perspective}")
                    
                    # Show recommended articles if requested
                    if options['show_articles']:
                        articles = story.recommended_articles.all()[:3]
                        if articles:
                            self.stdout.write("    📖 READ MORE:")
                            for j, article in enumerate(articles, 1):
                                pub_name = article.publication.name if article.publication else article.source_name
                                
                                # Get the best abstract available
                                abstract = None
                                try:
                                    if hasattr(article, 'structured_summary') and article.structured_summary:
                                        summary = article.structured_summary
                                        # Prefer longer_abstract (≤200 words) over regular abstract (≤60 words)
                                        abstract = summary.longer_abstract or summary.abstract
                                except Exception:
                                    pass
                                
                                # Display article with enhanced formatting
                                self.stdout.write(f"      {j}. {self.style.HTTP_INFO(article.title)}")
                                self.stdout.write(f"         📰 {pub_name}")
                                
                                if abstract:
                                    # Truncate abstract if too long for terminal display
                                    display_abstract = abstract[:200] + "..." if len(abstract) > 200 else abstract
                                    self.stdout.write(f"         💬 {display_abstract}")
                                
                                self.stdout.write(f"         🔗 {article.url}")
                                self.stdout.write("")  # Add spacing between articles
                    
                    self.stdout.write("")
            
            self.stdout.write("")
        
        # Conclusion
        if digest.conclusion:
            self.stdout.write(self.style.WARNING("🎯 CONCLUSION"))
            self.stdout.write(digest.conclusion)
            self.stdout.write("")
        
        # Footer with stats
        self.stdout.write("=" * 60)
        self.stdout.write(self.style.SUCCESS("📊 GENERATION STATS"))
        self.stdout.write(f"⏱️  Duration: {digest.generation_duration_ms}ms")
        self.stdout.write(f"💰 Cost: ${float(digest.generation_cost_usd):.6f}")
        self.stdout.write(f"📂 Topics: {digest.topics_included}")
        self.stdout.write(f"📰 Events: {digest.events_included}")
        self.stdout.write(f"📄 Articles: {digest.articles_processed}")
        
        if digest.tokens_input or digest.tokens_output:
            total_tokens = digest.tokens_input + digest.tokens_output
            self.stdout.write(f"🤖 Tokens: {total_tokens:,} (in: {digest.tokens_input:,}, out: {digest.tokens_output:,})")
        
        if digest.ai_model_used:
            self.stdout.write(f"🧠 AI Model: {digest.ai_model_used}")
        
        self.stdout.write("=" * 60)
    
    def _display_topic_debug_info(self, digest_topic: DigestTopic, digest: Digest):
        """Display detailed debugging information for a topic."""
        self.stdout.write(self.style.WARNING("🔍 DEBUG INFO"))
        self.stdout.write(self.style.WARNING("🎯 Using EXACT same content selector methods as digest generation"))
        
        # Use the exact same content selector as digest generation
        from apps.content.digest.services.content_selector import DigestContentSelector
        
        content_selector = DigestContentSelector()
        
        # Use the exact same parameters as digest generation
        user_preferences = digest.digest_preferences
        target_date = digest.date
        max_events_per_topic = user_preferences.get('max_events_per_topic', 3)
        
        self.stdout.write(f"📊 EXACT DIGEST METHODS USED:")
        self.stdout.write(f"   🎯 Method: content_selector.get_top_events_for_topic()")
        self.stdout.write(f"   📅 Target date: {target_date}")
        self.stdout.write(f"   👤 User: {digest.user.username}")
        self.stdout.write(f"   ⚙️  User preferences: {user_preferences}")
        self.stdout.write(f"   🎯 Max events per topic: {max_events_per_topic}")
        self.stdout.write("")
        
        # STEP 1: Get ALL articles that match the digest filters
        # Extract the same filtering logic from content selector
        user_timezone = digest.user.profile.timezone if hasattr(digest.user, 'profile') else 'UTC'
        start_date, end_date = content_selector._calculate_date_range_from_preferences(
            target_date, user_preferences, user_timezone
        )
        
        # Get all articles for this topic using the exact same filters
        all_articles_query = Article.objects.filter(
            primary_topic=digest_topic.topic,  # Only primary topic - same as digest generation
            published_at__gte=start_date,
            published_at__lte=end_date,
            analyzer_status='completed'  # Only fully processed articles
        ).select_related('primary_topic', 'primary_region', 'publication').prefetch_related('topics', 'regions')
        
        # Apply user region preferences if available (same as content selector)
        if hasattr(digest.user, 'preferred_regions'):
            user_region_relations = digest.user.preferred_regions.all()
            if user_region_relations.exists():
                user_regions = [ur.region for ur in user_region_relations]
                all_articles_query = all_articles_query.filter(regions__in=user_regions).distinct()
        
        all_articles = list(all_articles_query.order_by('-published_at'))
        
        self.stdout.write(f"🔍 ALL ARTICLES MATCHING DIGEST FILTERS ({len(all_articles)}):")
        
        for j, article in enumerate(all_articles[:15], 1):  # Show first 15
            pub_name = article.publication.name if article.publication else article.source_name
            self.stdout.write(f"  {j}. {article.title[:80]}...")
            self.stdout.write(f"     📰 Source: {pub_name}")
            self.stdout.write(f"     🕐 Published: {article.published_at.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Topic assignments
            primary_topic_name = article.primary_topic.name if article.primary_topic else "None"
            other_topics = [t.name for t in article.topics.all() if t != article.primary_topic]
            self.stdout.write(f"     🎯 Primary Topic: {primary_topic_name}")
            if other_topics:
                self.stdout.write(f"     🏷️  Other Topics: {', '.join(other_topics)}")
            
            # Region assignments
            primary_region_name = article.primary_region.name if article.primary_region else "None"
            other_regions = [r.name for r in article.regions.all() if r != article.primary_region]
            self.stdout.write(f"     🌍 Primary Region: {primary_region_name}")
            if other_regions:
                self.stdout.write(f"     🗺️  Other Regions: {', '.join(other_regions)}")
            
            self.stdout.write("")
        
        if len(all_articles) > 15:
            self.stdout.write(f"     ... and {len(all_articles) - 15} more articles")
            self.stdout.write("")
        
        # STEP 2: Get ALL events for this topic (call with high max_events to see all)
        all_topic_events = content_selector.get_top_events_for_topic(
            topic=digest_topic.topic,
            target_date=target_date,
            max_events=100,  # High limit to get ALL events
            user=digest.user,
            user_preferences=user_preferences
        )
        
        # Get actual digest articles count
        story_article_ids = Article.objects.filter(
            models.Q(digest_recommendations__digest_topic=digest_topic) |
            models.Q(digest_stories__digest_topic=digest_topic)
        ).values_list('id', flat=True)
        actual_articles_used = len(story_article_ids)
        
        if not all_topic_events:
            self.stdout.write(f"⚠️  No events found using get_top_events_for_topic(), trying fallback method...")
            
            fallback_articles = content_selector.get_topic_articles_for_fallback_digest(
                topic=digest_topic.topic,
                target_date=target_date,
                max_articles=100,  # High limit to get ALL articles
                user=digest.user,
                user_preferences=user_preferences
            )
            
            if fallback_articles:
                self.stdout.write(f"📊 Found {len(fallback_articles)} articles using fallback method:")
                
                for j, article in enumerate(fallback_articles[:10], 1):
                    pub_name = article.publication.name if article.publication else article.source_name
                    self.stdout.write(f"  {j}. {article.title[:80]}...")
                    self.stdout.write(f"     📰 Source: {pub_name}")
                    self.stdout.write(f"     🕐 Published: {article.published_at.strftime('%Y-%m-%d %H:%M:%S')}")
                    self.stdout.write("")
                
                self.stdout.write(f"🔄 Topic processed in FALLBACK MODE (no events found)")
                
                # Return stats for fallback mode
                return {
                    'articles_found': len(all_articles),
                    'articles_used': actual_articles_used,
                    'events_found': 0,
                    'events_used': 0,
                    'fallback_mode': True
                }
            else:
                self.stdout.write(f"❌ No articles found using fallback method either")
                return {
                    'articles_found': len(all_articles),
                    'articles_used': actual_articles_used,
                    'events_found': 0,
                    'events_used': 0,
                    'fallback_mode': False
                }
        else:
            # Show ALL events found, ordered by priority
            self.stdout.write(f"🎯 ALL EVENTS FOUND AND ORDERED BY PRIORITY ({len(all_topic_events)}):")
            
            for k, event_data in enumerate(all_topic_events, 1):
                event = event_data['event']
                articles = event_data['articles']
                score = event_data['score']
                primary_mentions = event_data['primary_mentions']
                secondary_mentions = event_data['secondary_mentions']
                
                # Highlight if this is one of the top 3 used in digest
                is_top_event = k <= max_events_per_topic
                prefix = "⭐" if is_top_event else "  "
                
                self.stdout.write(f"{prefix} {k}. {event.title}")
                self.stdout.write(f"     📊 Score: {score} (Primary: {primary_mentions}, Secondary: {secondary_mentions})")
                self.stdout.write(f"     🕐 Detected: {event.first_seen_at.strftime('%Y-%m-%d %H:%M:%S')}")
                self.stdout.write(f"     📄 Articles: {len(articles)}")
                
                if is_top_event:
                    self.stdout.write(f"     ✅ USED IN DIGEST (Top {max_events_per_topic})")
                else:
                    self.stdout.write(f"     ❌ Not used in digest (ranked #{k})")
                
                # Show first few articles for this event
                for article in articles[:2]:
                    pub_name = article.publication.name if article.publication else article.source_name
                    self.stdout.write(f"       - {article.title[:60]}... ({pub_name})")
                
                if len(articles) > 2:
                    self.stdout.write(f"       ... and {len(articles) - 2} more articles")
                
                self.stdout.write("")
        
        # STEP 3: Get the exact same top events as used in digest generation
        digest_topic_events = content_selector.get_top_events_for_topic(
            topic=digest_topic.topic,
            target_date=target_date,
            max_events=max_events_per_topic,  # Exact same limit as digest
            user=digest.user,
            user_preferences=user_preferences
        )
        
        # Collect all articles from the TOP events used in digest
        digest_event_articles = []
        for event_data in digest_topic_events:
            digest_event_articles.extend(event_data['articles'])
        
        # Remove duplicates while preserving order
        seen_ids = set()
        unique_digest_articles = []
        for article in digest_event_articles:
            if article.id not in seen_ids:
                unique_digest_articles.append(article)
                seen_ids.add(article.id)
        
        self.stdout.write(f"🎯 ARTICLES FROM TOP {max_events_per_topic} EVENTS USED IN DIGEST ({len(unique_digest_articles)}):")
        for j, article in enumerate(unique_digest_articles, 1):
            pub_name = article.publication.name if article.publication else article.source_name
            self.stdout.write(f"  {j}. {article.title[:80]}... ({pub_name})")
        self.stdout.write("")
        
        # Show actual digest articles separately for comparison
        if story_article_ids:
            actual_digest_articles = Article.objects.filter(
                id__in=story_article_ids
            ).select_related('primary_topic', 'primary_region').prefetch_related('topics', 'regions', 'publication').order_by('-published_at')
            
            self.stdout.write(f"📰 ACTUAL ARTICLES USED IN DIGEST ({actual_digest_articles.count()}):")
            for j, article in enumerate(actual_digest_articles, 1):
                pub_name = article.publication.name if article.publication else article.source_name
                self.stdout.write(f"  {j}. {article.title[:60]}... ({pub_name})")
            self.stdout.write("")
        
        self.stdout.write("-" * 80)
        
        # Return stats for summary
        return {
            'articles_found': len(all_articles),
            'articles_used': actual_articles_used,
            'events_found': len(all_topic_events),
            'events_used': min(max_events_per_topic, len(all_topic_events)),
            'fallback_mode': False
        }

    def _print_debug_summary(self, debug_summary):
        """Print a summary of debug statistics."""
        self.stdout.write("")
        self.stdout.write("=" * 80)
        self.stdout.write(self.style.SUCCESS("📊 DEBUG SUMMARY"))
        self.stdout.write("=" * 80)
        
        self.stdout.write("")
        self.stdout.write(self.style.WARNING("🔍 Step 1: All Articles Matching Filters"))
        for topic_name, stats in debug_summary.items():
            articles_found = stats['articles_found']
            articles_used = stats['articles_used']
            self.stdout.write(f"{topic_name}: {articles_found} articles found vs {articles_used} used")
        
        self.stdout.write("")
        self.stdout.write(self.style.WARNING("🎯 Step 2: All Events Ranked by Priority"))
        for topic_name, stats in debug_summary.items():
            events_found = stats['events_found']
            events_used = stats['events_used']
            
            if stats['fallback_mode']:
                self.stdout.write(f"{topic_name}: Fallback mode used (no events found)")
            elif events_found == 0:
                self.stdout.write(f"{topic_name}: No events found")
            else:
                emphasis = "!" if events_found > events_used else ""
                self.stdout.write(f"{topic_name}: {events_found} events found{emphasis} Only top {events_used} used in digest")
        
        # Calculate totals
        total_articles_found = sum(stats['articles_found'] for stats in debug_summary.values())
        total_articles_used = sum(stats['articles_used'] for stats in debug_summary.values())
        total_events_found = sum(stats['events_found'] for stats in debug_summary.values())
        total_events_used = sum(stats['events_used'] for stats in debug_summary.values())
        
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("📈 TOTALS:"))
        self.stdout.write(f"Articles: {total_articles_found} found vs {total_articles_used} used ({total_articles_used/total_articles_found*100:.1f}% usage)")
        self.stdout.write(f"Events: {total_events_found} found vs {total_events_used} used ({total_events_used/total_events_found*100:.1f}% usage)" if total_events_found > 0 else "Events: 0 found (fallback mode used)")
        self.stdout.write("")

    def _display_generation_stats(self, digest: Digest):
        """Display additional statistics for the digest."""
        self.stdout.write("=" * 60)
        self.stdout.write(self.style.SUCCESS("📊 ADDITIONAL STATISTICS"))
        self.stdout.write("=" * 60)
        
        self.stdout.write(f"📅 Date: {digest.date}")
        self.stdout.write(f"🕐 Generated: {digest.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        self.stdout.write(f"⏱️  Duration: {digest.generation_duration_ms}ms")
        self.stdout.write(f"💰 Cost: ${float(digest.generation_cost_usd):.6f}")
        self.stdout.write(f"📂 Topics: {digest.topics_included}")
        self.stdout.write(f"📰 Events: {digest.events_included}")
        self.stdout.write(f"📄 Articles: {digest.articles_processed}")
        
        if digest.tokens_input or digest.tokens_output:
            total_tokens = digest.tokens_input + digest.tokens_output
            self.stdout.write(f"🤖 Tokens: {total_tokens:,} (in: {digest.tokens_input:,}, out: {digest.tokens_output:,})")
        
        if digest.ai_model_used:
            self.stdout.write(f"🧠 AI Model: {digest.ai_model_used}")
        
        self.stdout.write("=" * 60) 