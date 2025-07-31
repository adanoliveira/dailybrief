from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.db import transaction
from datetime import datetime, timedelta
from apps.content.digest.models import Digest, DigestTopic, DigestStory
from apps.accounts.models import UserProfile
from apps.feeds.models import UserTopic, UserRegion, UserLanguage, UserPublication


class Command(BaseCommand):
    """
    Clean up test data by deleting user digests and optionally users themselves.
    
    This command is designed for testing and development environments to quickly
    clean up data and test digest generation scenarios from scratch.
    
    Examples:
        # Delete all digests for a user (useful for testing auto-generation)
        python manage.py cleanup_test_data user@example.com --digests-only
        
        # Delete digests from the last 7 days for a user
        python manage.py cleanup_test_data user@example.com --digests-only --days 7
        
        # Delete all data for a user (digests, preferences, profile)
        python manage.py cleanup_test_data user@example.com --delete-user
        
        # Delete specific digest by date
        python manage.py cleanup_test_data user@example.com --digests-only --date 2025-07-30
        
        # Dry run to see what would be deleted
        python manage.py cleanup_test_data user@example.com --digests-only --dry-run
    """
    help = 'Clean up test data for users and digests'

    def add_arguments(self, parser):
        """Define command line arguments."""
        parser.add_argument(
            'identifier', 
            type=str, 
            help='User email or ID to clean up data for'
        )
        
        # Action options
        parser.add_argument(
            '--digests-only',
            action='store_true',
            help='Only delete digests, keep user and preferences intact'
        )
        parser.add_argument(
            '--delete-user',
            action='store_true', 
            help='Delete the entire user account and all associated data'
        )
        
        # Date filtering options
        parser.add_argument(
            '--date',
            type=str,
            help='Delete digest for specific date (YYYY-MM-DD format)'
        )
        parser.add_argument(
            '--days',
            type=int,
            help='Delete digests from the last N days (default: all digests)'
        )
        
        # Safety options
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting anything'
        )

    def handle(self, *args, **options):
        """Execute the cleanup command."""
        identifier = options['identifier']
        digests_only = options.get('digests_only', False)
        delete_user = options.get('delete_user', False)
        target_date = options.get('date')
        days = options.get('days')
        dry_run = options.get('dry_run', False)
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No data will be deleted'))
        
        # Validate arguments
        if digests_only and delete_user:
            raise CommandError('Cannot use both --digests-only and --delete-user. Choose one.')
        
        if not digests_only and not delete_user:
            raise CommandError('Must specify either --digests-only or --delete-user')
        
        # Find the user
        try:
            if identifier.isdigit():
                user = User.objects.get(id=int(identifier))
            else:
                user = User.objects.get(email=identifier)
        except User.DoesNotExist:
            raise CommandError(f'User with identifier "{identifier}" does not exist')

        self.stdout.write(f'Found user: {user.email} (ID: {user.id})')
        
        # Execute the cleanup
        if digests_only:
            self._cleanup_digests(user, target_date, days, dry_run)
        elif delete_user:
            self._delete_user(user, dry_run)

    def _cleanup_digests(self, user, target_date=None, days=None, dry_run=False):
        """Delete digests for a user based on criteria."""
        # Build the query
        digests_query = Digest.objects.filter(user=user)
        
        if target_date:
            # Validate and parse the date
            try:
                parsed_date = datetime.strptime(target_date, '%Y-%m-%d').date()
                digests_query = digests_query.filter(date=parsed_date)
                self.stdout.write(f'Filtering digests for date: {parsed_date}')
            except ValueError:
                raise CommandError(f'Invalid date format: {target_date}. Use YYYY-MM-DD.')
        
        elif days:
            # Filter by days
            cutoff_date = datetime.now().date() - timedelta(days=days)
            digests_query = digests_query.filter(date__gte=cutoff_date)
            self.stdout.write(f'Filtering digests from last {days} days (since {cutoff_date})')
        
        else:
            self.stdout.write('Targeting ALL digests for this user')
        
        # Get the digests
        digests = list(digests_query.order_by('-date'))
        
        if not digests:
            self.stdout.write(self.style.WARNING('No digests found matching criteria'))
            return
        
        # Show what we found
        self.stdout.write(f'Found {len(digests)} digest(s) to delete:')
        for digest in digests:
            topics_count = DigestTopic.objects.filter(digest=digest).count()
            stories_count = DigestStory.objects.filter(digest_topic__digest=digest).count()
            
            self.stdout.write(
                f'  - {digest.date} | {digest.generation_status} | '
                f'{topics_count} topics, {stories_count} stories | ID: {digest.public_id}'
            )
        
        if dry_run:
            self.stdout.write(self.style.SUCCESS(f'DRY RUN: Would delete {len(digests)} digests'))
            return
        
        # Confirm deletion
        confirm = input(f'\nAre you sure you want to delete {len(digests)} digest(s)? (y/N): ')
        if confirm.lower() != 'y':
            self.stdout.write('Cancelled by user')
            return
        
        # Delete digests
        with transaction.atomic():
            deleted_count = 0
            for digest in digests:
                # Delete related objects first
                DigestStory.objects.filter(digest_topic__digest=digest).delete()
                DigestTopic.objects.filter(digest=digest).delete()
                digest.delete()
                deleted_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully deleted {deleted_count} digest(s) for user {user.email}')
        )

    def _delete_user(self, user, dry_run=False):
        """Delete a user and all associated data."""
        # Count what we're about to delete
        digests_count = Digest.objects.filter(user=user).count()
        topics_count = UserTopic.objects.filter(user=user).count()
        regions_count = UserRegion.objects.filter(user=user).count()
        languages_count = UserLanguage.objects.filter(user=user).count()
        publications_count = UserPublication.objects.filter(user=user).count()
        
        # Check if user has a profile
        try:
            profile = UserProfile.objects.get(user=user)
            has_profile = True
        except UserProfile.DoesNotExist:
            has_profile = False
        
        self.stdout.write(f'User data summary for {user.email}:')
        self.stdout.write(f'  - Digests: {digests_count}')
        self.stdout.write(f'  - Topics: {topics_count}')
        self.stdout.write(f'  - Regions: {regions_count}')
        self.stdout.write(f'  - Languages: {languages_count}')
        self.stdout.write(f'  - Publications: {publications_count}')
        self.stdout.write(f'  - Profile: {"Yes" if has_profile else "No"}')
        
        if dry_run:
            self.stdout.write(self.style.SUCCESS('DRY RUN: Would delete user and all associated data'))
            return
        
        # Confirm deletion
        confirm = input(f'\nAre you sure you want to PERMANENTLY DELETE user {user.email} and ALL associated data? (y/N): ')
        if confirm.lower() != 'y':
            self.stdout.write('Cancelled by user')
            return
        
        # Double confirmation for user deletion
        confirm2 = input(f'This will permanently delete the user account. Type "DELETE" to confirm: ')
        if confirm2 != 'DELETE':
            self.stdout.write('Cancelled - confirmation text did not match')
            return
        
        # Delete everything
        with transaction.atomic():
            # Delete digests and related objects (CASCADE will handle DigestStory/DigestTopic automatically)
            Digest.objects.filter(user=user).delete()
            
            # Delete preferences
            UserTopic.objects.filter(user=user).delete()
            UserRegion.objects.filter(user=user).delete()
            UserLanguage.objects.filter(user=user).delete()
            UserPublication.objects.filter(user=user).delete()
            
            # Delete profile
            if has_profile:
                profile.delete()
            
            # Delete user account
            user_email = user.email
            user.delete()
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully deleted user {user_email} and all associated data')
        ) 