"""
Management command to generate daily digests for users.

This command can be used for:
- Testing digest generation functionality
- Manual digest generation for specific users
- Batch digest generation for all users
- Regenerating failed digests
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Q

from apps.content.digest.services import DigestService
from apps.content.digest.models import Digest

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = """
    Generate daily digests for users.
    
    Examples:
    - Generate digest for specific user: --user-id 123
    - Generate for all users: --all-users
    - Generate for specific date: --date 2024-01-15
    - Regenerate existing digest: --regenerate
    - Test mode (dry run): --test
    """
    
    def add_arguments(self, parser):
        # User selection
        parser.add_argument(
            '--user-id',
            type=int,
            help='Generate digest for specific user ID'
        )
        
        parser.add_argument(
            '--username',
            type=str,
            help='Generate digest for specific username'
        )
        
        parser.add_argument(
            '--all-users',
            action='store_true',
            help='Generate digests for all active users with topics'
        )
        
        # Date selection
        parser.add_argument(
            '--date',
            type=str,
            help='Target date for digest (YYYY-MM-DD format, defaults to today)'
        )
        
        # Generation options
        parser.add_argument(
            '--regenerate',
            action='store_true',
            help='Regenerate digest even if it already exists'
        )
        
        parser.add_argument(
            '--test',
            action='store_true',
            help='Test mode - validate setup but do not generate'
        )
        
        # Filtering options
        parser.add_argument(
            '--max-users',
            type=int,
            default=50,
            help='Maximum number of users to process (default: 50)'
        )
        
        parser.add_argument(
            '--skip-users-with-digests',
            action='store_true',
            help='Skip users who already have digests for the target date'
        )
    
    def handle(self, *args, **options):
        """Main command handler."""
        self.stdout.write(self.style.SUCCESS('🚀 Starting digest generation...'))
        
        # Parse and validate arguments
        target_date = self._parse_target_date(options['date'])
        users = self._get_target_users(options)
        
        if not users:
            raise CommandError("No users found matching the criteria")
        
        self.stdout.write(
            f"📅 Target date: {target_date.strftime('%Y-%m-%d')}\n"
            f"👥 Users to process: {len(users)}\n"
            f"🔄 Regenerate: {options['regenerate']}\n"
            f"🧪 Test mode: {options['test']}"
        )
        
        if options['test']:
            self._run_test_mode(users, target_date, options)
            return
        
        # Initialize digest service
        digest_service = DigestService()
        
        # Process each user
        success_count = 0
        error_count = 0
        skipped_count = 0
        
        for user in users:
            try:
                result = self._generate_user_digest(
                    digest_service, user, target_date, options
                )
                
                if result.get('skipped', False):
                    skipped_count += 1
                    self.stdout.write(
                        f"⏭️  Skipped {user.username} - {result.get('reason', 'Unknown reason')}"
                    )
                elif result.get('success', False):
                    success_count += 1
                    metrics = result.get('metrics', {})
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"✅ Generated digest for {user.username}: "
                            f"{metrics.get('topics_included', 0)} topics, "
                            f"{metrics.get('total_events', 0)} events "
                            f"(${metrics.get('total_cost_usd', 0):.4f})"
                        )
                    )
                else:
                    error_count += 1
                    self.stdout.write(
                        self.style.ERROR(
                            f"❌ Failed for {user.username}: {result.get('error', 'Unknown error')}"
                        )
                    )
                    
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f"❌ Exception for {user.username}: {str(e)}")
                )
                logger.exception(f"Error generating digest for user {user.id}")
        
        # Summary
        self.stdout.write("\n" + "="*50)
        self.stdout.write(
            self.style.SUCCESS(f"📊 Generation Summary:") + "\n"
            f"✅ Successful: {success_count}\n"
            f"❌ Errors: {error_count}\n"
            f"⏭️  Skipped: {skipped_count}\n"
            f"📈 Total: {len(users)}"
        )
        
        if error_count > 0:
            self.stdout.write(
                self.style.WARNING(f"\n⚠️  {error_count} errors occurred. Check logs for details.")
            )
    
    def _parse_target_date(self, date_str: Optional[str]) -> datetime:
        """Parse target date from string or use today."""
        if date_str:
            try:
                parsed_date = datetime.strptime(date_str, '%Y-%m-%d')
                return timezone.make_aware(parsed_date)
            except ValueError:
                raise CommandError(f"Invalid date format: {date_str}. Use YYYY-MM-DD")
        
        return timezone.now()
    
    def _get_target_users(self, options) -> List[User]:
        """Get list of users to process based on options."""
        if options['user_id']:
            try:
                user = User.objects.get(id=options['user_id'])
                return [user]
            except User.DoesNotExist:
                raise CommandError(f"User with ID {options['user_id']} not found")
        
        elif options['username']:
            try:
                user = User.objects.get(username=options['username'])
                return [user]
            except User.DoesNotExist:
                raise CommandError(f"User '{options['username']}' not found")
        
        elif options['all_users']:
            # Get all active users who have followed topics
            queryset = User.objects.filter(
                is_active=True,
                preferred_topics__isnull=False  # Has followed topics
            ).distinct()
            
            if options['skip_users_with_digests']:
                # Exclude users who already have digests for target date
                target_date = self._parse_target_date(options['date'])
                queryset = queryset.exclude(
                    digests__date=target_date.date()
                )
            
            users = list(queryset[:options['max_users']])
            
            if not users:
                raise CommandError("No active users with followed topics found")
                
            return users
        
        else:
            raise CommandError(
                "Must specify either --user-id, --username, or --all-users"
            )
    
    def _generate_user_digest(
        self, 
        digest_service: DigestService, 
        user: User, 
        target_date: datetime, 
        options
    ) -> dict:
        """Generate digest for a single user."""
        
        # Check if user has digest preferences
        if not hasattr(user, 'profile'):
            return {
                'success': False,
                'skipped': True,
                'reason': 'No user profile found'
            }
        
        # Check if user has followed topics
        if not user.preferred_topics.exists():
            return {
                'success': False,
                'skipped': True,
                'reason': 'No followed topics'
            }
        
        # Check for existing digest
        if not options['regenerate']:
            existing_digest = Digest.objects.filter(
                user=user,
                date=target_date.date()
            ).first()
            
            if existing_digest:
                return {
                    'success': True,
                    'skipped': True,
                    'reason': f'Digest already exists ({existing_digest.public_id})'
                }
        
        # Generate digest
        try:
            digest = digest_service.generate_user_digest(
                user=user,
                date=target_date.date(),
                force_regenerate=options['regenerate']
            )
            
            # Convert digest object to result dict for consistent handling
            result = {
                'success': True,
                'digest': digest,
                'metrics': {
                    'topics_included': digest.digest_topics.count(),
                    'total_events': sum(topic.stories.count() for topic in digest.digest_topics.all()),
                    'total_cost_usd': float(digest.generation_cost_usd),
                }
            }
        except Exception as e:
            result = {
                'success': False,
                'error': str(e)
            }
        
        return result
    
    def _run_test_mode(self, users: List[User], target_date: datetime, options):
        """Run in test mode to validate setup."""
        self.stdout.write(self.style.WARNING("🧪 Running in TEST MODE - no digests will be generated"))
        
        # Test digest service initialization
        try:
            digest_service = DigestService()
            self.stdout.write("✅ DigestService initialized successfully")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Failed to initialize DigestService: {e}"))
            return
        
        # Test user validation
        valid_users = 0
        for user in users[:5]:  # Test first 5 users only
            try:
                # Check user profile
                if not hasattr(user, 'profile'):
                    self.stdout.write(f"⚠️  {user.username}: No user profile")
                    continue
                
                # Check followed topics
                if not user.preferred_topics.exists():
                    self.stdout.write(f"⚠️  {user.username}: No followed topics")
                    continue
                
                # Check for articles in date range
                selector = digest_service.content_selector
                date_range = selector.get_date_range_for_digest(
                    target_date, user.profile.timezone
                )
                articles = selector.get_user_articles(user, date_range[0], date_range[1])
                
                article_count = len(articles)
                self.stdout.write(
                    f"✅ {user.username}: "
                    f"{user.preferred_topics.count()} topics, "
                    f"{article_count} articles available"
                )
                
                valid_users += 1
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"❌ {user.username}: Error - {e}")
                )
        
        self.stdout.write(f"\n📊 Test Results: {valid_users} users ready for digest generation")
        
        if valid_users == 0:
            self.stdout.write(
                self.style.WARNING("⚠️  No users are ready for digest generation")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f"🎉 System is ready! Run without --test to generate digests")
            ) 