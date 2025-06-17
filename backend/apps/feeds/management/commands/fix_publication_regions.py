from django.core.management.base import BaseCommand
from apps.feeds.models import Publication, Region
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Fix publications that are missing region assignments'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING("DRY RUN MODE - No changes will be made")
            )
        
        # Get US region as default for US-based publications
        try:
            us_region = Region.objects.get(code='us')
            gb_region = Region.objects.get(code='gb')
        except Region.DoesNotExist:
            self.stdout.write(
                self.style.ERROR("US or GB region not found in database")
            )
            return

        # Find publications without regions
        publications_without_regions = Publication.objects.filter(regions__isnull=True)
        
        self.stdout.write(f"Found {publications_without_regions.count()} publications without regions")
        
        # Mapping of publication names/domains to regions
        us_publications = [
            'espn', 'cnn', 'marketwatch', 'ars technica', 'the verge', 'buzzfeed',
            'huffpost', 'the denver post', 'mlive.com', "men's journal",
            'eatingwell.com', 'who what wear', 'boxoffice pro'
        ]
        
        gb_publications = [
            'thetimes.com', 'the times'
        ]
        
        india_publications = [
            'quartz india'
        ]
        
        # Get India region
        try:
            in_region = Region.objects.get(code='in')
        except Region.DoesNotExist:
            in_region = None
        
        updated_count = 0
        
        for publication in publications_without_regions:
            pub_name_lower = publication.name.lower()
            regions_to_add = []
            
            # Check for US publications
            if any(us_pub in pub_name_lower for us_pub in us_publications):
                regions_to_add.append(us_region)
            # Check for GB publications
            elif any(gb_pub in pub_name_lower for gb_pub in gb_publications):
                regions_to_add.append(gb_region)
            # Check for India publications
            elif any(in_pub in pub_name_lower for in_pub in india_publications) and in_region:
                regions_to_add.append(in_region)
            # Default to US for unknown publications (most content is US-based)
            else:
                regions_to_add.append(us_region)
            
            if regions_to_add:
                if not dry_run:
                    publication.regions.set(regions_to_add)
                    publication.save()
                
                region_names = [r.name for r in regions_to_add]
                self.stdout.write(f"{'Would assign' if dry_run else 'Assigned'} {publication.name} → {region_names}")
                updated_count += 1
        
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(f"Would update {updated_count} publications")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f"Successfully updated {updated_count} publications with regions")
            ) 