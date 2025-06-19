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

from apps.content.digest.models import Digest, DigestTopic, DigestStory

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
    
    def handle(self, *args, **options):
        """Main command handler."""
        self.stdout.write(self.style.SUCCESS('📰 Displaying Daily Digest...'))
        
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
            
            # Abstract
            if topic.topic_abstract:
                self.stdout.write(f"📄 Abstract: {topic.topic_abstract}")
                self.stdout.write("")
            
            # Facts
            if topic.main_facts and not options['compact']:
                self.stdout.write("🔍 KEY FACTS:")
                for j, fact in enumerate(topic.main_facts, 1):
                    self.stdout.write(f"  {j}. {fact}")
                self.stdout.write("")
            
            # Perspectives
            if topic.perspectives and not options['compact']:
                self.stdout.write("💭 PERSPECTIVES:")
                for j, perspective in enumerate(topic.perspectives, 1):
                    self.stdout.write(f"  {j}. {perspective}")
                self.stdout.write("")
            
            # Stories
            stories = DigestStory.objects.filter(digest_topic=topic).order_by('order')
            if stories and not options['compact']:
                self.stdout.write("📰 STORIES:")
                for story in stories:
                    self.stdout.write(f"  • {story.title}")
                    if story.enhanced_abstract:
                        self.stdout.write(f"    {story.enhanced_abstract}")
                    
                    # Key facts
                    if story.key_facts:
                        self.stdout.write("    📋 Facts:")
                        for fact in story.key_facts[:3]:  # Show first 3
                            self.stdout.write(f"      - {fact}")
                    
                    # Show recommended articles if requested
                    if options['show_articles']:
                        articles = story.recommended_articles.all()[:3]
                        if articles:
                            self.stdout.write("    📖 Read more:")
                            for article in articles:
                                pub_name = article.publication.name if article.publication else article.source_name
                                self.stdout.write(f"      - {article.title} ({pub_name})")
                    
                    self.stdout.write("")
            
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
        
        # Success message
        self.stdout.write(
            self.style.SUCCESS(f"✅ Successfully displayed digest for {digest.user.username}")
        ) 