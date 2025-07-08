"""
Management command to calculate and update reading times for existing digests.
"""

import logging
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.content.digest.models import Digest

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Calculate and update reading times for existing digests'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes'
        )
        parser.add_argument(
            '--digest-id',
            type=str,
            help='Update specific digest by public ID'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        digest_id = options.get('digest_id')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        # Filter digests
        queryset = Digest.objects.filter(generation_status='completed')
        
        if digest_id:
            queryset = queryset.filter(public_id=digest_id)
        
        # Only update digests with reading_time_minutes = 0
        queryset = queryset.filter(reading_time_minutes=0)
        
        total_count = queryset.count()
        
        if total_count == 0:
            self.stdout.write(self.style.SUCCESS('No digests need reading time calculation'))
            return
        
        self.stdout.write(f'Found {total_count} digests to update')
        
        updated_count = 0
        error_count = 0
        
        for digest in queryset.iterator():
            try:
                old_reading_time = digest.reading_time_minutes
                new_reading_time = digest.calculate_reading_time()
                
                if dry_run:
                    self.stdout.write(
                        f'Digest {digest.public_id} ({digest.date}): '
                        f'{old_reading_time} -> {new_reading_time} minutes'
                    )
                else:
                    digest.reading_time_minutes = new_reading_time
                    digest.save(update_fields=['reading_time_minutes'])
                    
                    self.stdout.write(
                        f'Updated digest {digest.public_id} ({digest.date}): '
                        f'{old_reading_time} -> {new_reading_time} minutes'
                    )
                
                updated_count += 1
                
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(
                        f'Error updating digest {digest.public_id}: {str(e)}'
                    )
                )
        
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f'DRY RUN: Would update {updated_count} digests '
                    f'({error_count} errors)'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully updated {updated_count} digests '
                    f'({error_count} errors)'
                )
            ) 