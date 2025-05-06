from django.core.management.base import BaseCommand
from apps.feeds.models import Publication, Topic, Region, Language
from django.db.models import Q


class Command(BaseCommand):
    help = 'Assign publications to topics, regions, and languages in batches'

    def add_arguments(self, parser):
        parser.add_argument('--topic', type=str, help='Topic slug to assign')
        parser.add_argument('--region', type=str, help='Region code to assign')
        parser.add_argument('--language', type=str, help='Language code to assign')
        parser.add_argument('--filter', type=str, help='Filter publications by name (contains)')
        parser.add_argument('--ids', type=str, help='Comma-separated list of publication IDs')
        parser.add_argument('--missing-topics', action='store_true', help='Only select publications with no topics')
        parser.add_argument('--missing-regions', action='store_true', help='Only select publications with no regions')
        parser.add_argument('--missing-languages', action='store_true', help='Only select publications with no languages')
        parser.add_argument('--dry-run', action='store_true', help='Show what would be updated without making changes')

    def handle(self, *args, **options):
        # Check if at least one assignment option is specified
        if not any([options['topic'], options['region'], options['language']]):
            self.stdout.write(self.style.ERROR("Error: You must specify at least one assignment (--topic, --region, or --language)"))
            return

        # Build query for publications
        query = Q()
        
        # Filter by IDs if provided
        if options['ids']:
            ids = [int(id.strip()) for id in options['ids'].split(',') if id.strip().isdigit()]
            query &= Q(id__in=ids)
        
        # Filter by name
        if options['filter']:
            query &= Q(name__icontains=options['filter'])
        
        # Filter by missing relationships
        if options['missing_topics']:
            query &= Q(topics__isnull=True)
        if options['missing_regions']:
            query &= Q(regions__isnull=True)
        if options['missing_languages']:
            query &= Q(languages__isnull=True)
        
        # Get publications matching the filter
        publications = Publication.objects.filter(query).distinct()
        
        if not publications.exists():
            self.stdout.write(self.style.WARNING("No publications match the specified filters."))
            return
        
        # Get entities to assign
        topic = None
        region = None
        language = None
        
        if options['topic']:
            try:
                topic = Topic.objects.get(slug=options['topic'])
            except Topic.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Topic with slug '{options['topic']}' not found."))
                return
        
        if options['region']:
            try:
                region = Region.objects.get(code=options['region'])
            except Region.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Region with code '{options['region']}' not found."))
                return
        
        if options['language']:
            try:
                language = Language.objects.get(iso_code=options['language'])
            except Language.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Language with code '{options['language']}' not found."))
                return
        
        # Show what will be updated
        self.stdout.write(self.style.SUCCESS(f"Found {publications.count()} publications matching the filters:"))
        for pub in publications:
            self.stdout.write(f"ID: {pub.id}, Name: {pub.name}")
        
        if options['dry_run']:
            self.stdout.write(self.style.SUCCESS("\nDRY RUN - No changes will be made"))
            return
        
        # Confirm with the user
        self.stdout.write("\nAssignments to make:")
        if topic:
            self.stdout.write(f"- Topic: {topic.name} ({topic.slug})")
        if region:
            self.stdout.write(f"- Region: {region.name} ({region.code})")
        if language:
            self.stdout.write(f"- Language: {language.name} ({language.iso_code})")
        
        confirm = input("\nDo you want to continue? [y/N]: ")
        if confirm.lower() != 'y':
            self.stdout.write(self.style.WARNING("Operation cancelled."))
            return
        
        # Make the assignments
        count = 0
        for pub in publications:
            if topic:
                pub.topics.add(topic)
                count += 1
            if region:
                pub.regions.add(region)
                count += 1
            if language:
                pub.languages.add(language)
                count += 1
        
        self.stdout.write(self.style.SUCCESS(f"\nSuccessfully made {count} assignments to {publications.count()} publications."))
        if topic:
            self.stdout.write(f"- Added topic '{topic.name}' to {publications.count()} publications")
        if region:
            self.stdout.write(f"- Added region '{region.name}' to {publications.count()} publications")
        if language:
            self.stdout.write(f"- Added language '{language.name}' to {publications.count()} publications") 