from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from apps.accounts.models import UserProfile
from apps.feeds.models import UserTopic, UserRegion, UserLanguage, UserPublication


class Command(BaseCommand):
    """
    Reset a user's onboarding status and optionally clear their preferences.
    
    This command allows administrators to reset a user's onboarding status,
    forcing them to go through the onboarding process again the next time they log in.
    By default, it also clears all user preferences (topics, regions, languages, 
    and publications) to provide a clean slate for re-onboarding.
    
    Examples:
        # Reset onboarding for a user by email (also removes all preferences)
        python manage.py reset_onboarding user@example.com
        
        # Reset onboarding for a user by ID without removing their preferences
        python manage.py reset_onboarding 123 --keep-preferences
        
        # Reset onboarding for multiple users
        python manage.py reset_onboarding user1@example.com
        python manage.py reset_onboarding user2@example.com
    """
    help = 'Reset onboarding status for a user'

    def add_arguments(self, parser):
        """
        Define the command line arguments.
        
        Args:
            parser: The argument parser
        """
        parser.add_argument('identifier', type=str, 
                           help='User email or ID to reset onboarding for')
        parser.add_argument('--keep-preferences', action='store_true', 
                           help='Keep user preferences (topics, regions, etc) instead of clearing them')

    def handle(self, *args, **options):
        """
        Execute the command to reset onboarding status.
        
        Args:
            *args: Additional arguments
            **options: Command options including 'identifier' and 'keep-preferences'
        
        Raises:
            CommandError: If the user or their profile doesn't exist
        
        Returns:
            None
        """
        identifier = options['identifier']
        keep_preferences = options.get('keep_preferences', False)
        
        # Find the user
        try:
            # Try to find by ID first
            if identifier.isdigit():
                user = User.objects.get(id=int(identifier))
            else:
                # Otherwise, search by email
                user = User.objects.get(email=identifier)
        except User.DoesNotExist:
            raise CommandError(f'User with identifier "{identifier}" does not exist')

        # Reset onboarding status
        try:
            profile = UserProfile.objects.get(user=user)
            profile.onboarding_completed = False
            profile.save()
            
            self.stdout.write(self.style.SUCCESS(
                f'Successfully reset onboarding status for user {user.email} (ID: {user.id})'
            ))
            
            # Optionally delete user preferences
            if not keep_preferences:
                # Delete all user topics, regions, languages, and publications
                user_topics = UserTopic.objects.filter(user=user)
                user_regions = UserRegion.objects.filter(user=user)
                user_languages = UserLanguage.objects.filter(user=user)
                user_pubs = UserPublication.objects.filter(user=user)
                
                topics_count = user_topics.count()
                regions_count = user_regions.count()
                languages_count = user_languages.count()
                pubs_count = user_pubs.count()
                
                # Delete all preferences
                user_topics.delete()
                user_regions.delete()
                user_languages.delete()
                user_pubs.delete()
                
                self.stdout.write(self.style.SUCCESS(
                    f'Deleted {topics_count} topics, {regions_count} regions, '
                    f'{languages_count} languages, and {pubs_count} publications'
                ))
            else:
                self.stdout.write(self.style.SUCCESS(
                    'User preferences have been preserved'
                ))
                
        except UserProfile.DoesNotExist:
            raise CommandError(f'User profile for "{user.email}" does not exist') 