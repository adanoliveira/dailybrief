from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.accounts.models import UserProfile


class Command(BaseCommand):
    help = 'Update time window preferences for existing users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--time-window',
            type=str,
            default='72h',
            help='New time window to set (default: 72h)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes'
        )

    def handle(self, *args, **options):
        time_window = options['time_window']
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        # Get all users with profiles
        users_with_profiles = User.objects.filter(profile__isnull=False)
        self.stdout.write(f'Found {users_with_profiles.count()} users with profiles')

        updated_count = 0
        for user in users_with_profiles:
            profile = user.profile
            current_prefs = profile.digest_preferences or {}
            
            # Check if they have a time_window setting
            if 'time_window' in current_prefs:
                old_window = current_prefs['time_window']
                
                if old_window != time_window:
                    if not dry_run:
                        # Update to new time window
                        current_prefs['time_window'] = time_window
                        profile.digest_preferences = current_prefs
                        profile.save()
                    
                    self.stdout.write(f'{"[DRY RUN] " if dry_run else ""}Updated {user.username}: {old_window} -> {time_window}')
                    updated_count += 1
                else:
                    self.stdout.write(f'{user.username}: Already using {time_window}')
            else:
                self.stdout.write(f'{user.username}: No time_window set (will use default)')

        self.stdout.write(
            self.style.SUCCESS(f'{"Would update" if dry_run else "Updated"} {updated_count} users to {time_window} time window')
        ) 