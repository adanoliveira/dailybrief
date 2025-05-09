import logging
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.feeds.models import Publication
from apps.feeds.utils import generate_logo_url

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Add logos to publications based on their domains'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Replace existing logos'
        )
        
        parser.add_argument(
            '--batch-size',
            type=int,
            default=50,
            help='Number of publications to process in each batch'
        )

    def handle(self, *args, **options):
        force = options['force']
        batch_size = options['batch_size']
        
        self.stdout.write(self.style.SUCCESS(f'Adding logos to publications...'))
        
        # Get publications without logos or all if force is specified
        query = Publication.objects.all()
        if not force:
            query = query.filter(logo_url__isnull=True) | query.filter(logo_url='')
            
        total_pubs = query.count()
        self.stdout.write(f'Found {total_pubs} publications to process')
        
        if total_pubs == 0:
            self.stdout.write(self.style.SUCCESS('No publications need logos'))
            return
        
        # Process in batches
        updated_count = 0
        offset = 0
        
        while True:
            # Get a batch of publications
            publications = query.order_by('id')[offset:offset+batch_size]
            
            if not publications:
                break
                
            # Process each publication
            with transaction.atomic():
                for pub in publications:
                    if not pub.domain:
                        self.stdout.write(f"  Skipping {pub.name}: No domain")
                        continue
                        
                    # Generate logo URL
                    logo_url = generate_logo_url(pub.domain)
                    
                    if not logo_url:
                        self.stdout.write(f"  Skipping {pub.name}: Could not generate logo URL")
                        continue
                        
                    # Update logo
                    if force or not pub.logo_url:
                        pub.logo_url = logo_url
                        pub.save(update_fields=['logo_url'])
                        updated_count += 1
                        
                        if updated_count % 10 == 0:
                            self.stdout.write(f'  Updated {updated_count}/{total_pubs} publication logos')
            
            # Move to next batch
            offset += batch_size
            
        self.stdout.write(self.style.SUCCESS(f'Added logos to {updated_count} publications')) 