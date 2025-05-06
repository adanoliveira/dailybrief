from django.core.management.base import BaseCommand
from apps.feeds.models import Publication, Topic
from django.db.models import Count, Q


class Command(BaseCommand):
    help = 'Find publications that have any of the specified topics'

    def add_arguments(self, parser):
        parser.add_argument('--topics', type=str, required=True, help='Comma-separated list of topic slugs')
        parser.add_argument('--detail', action='store_true', help='Show detailed information')
        parser.add_argument('--any', action='store_true', help='Match ANY of the topics (OR) instead of ALL (AND)')

    def handle(self, *args, **options):
        # Get the topic slugs
        topic_slugs = [slug.strip() for slug in options['topics'].split(',')]
        
        # Validate the topics
        topics = []
        for slug in topic_slugs:
            try:
                topic = Topic.objects.get(slug=slug)
                topics.append(topic)
                self.stdout.write(f"Including topic: {topic.name}")
            except Topic.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Topic with slug '{slug}' not found"))
                return
        
        # Find publications based on topics
        if options['any'] or len(topics) == 1:
            # OR condition - publications with ANY of the specified topics
            query = Q()
            for topic in topics:
                query |= Q(topics=topic)
            publications = Publication.objects.filter(query).distinct()
            logic_description = "any of"
        else:
            # AND condition - publications with ALL of the specified topics
            publications = Publication.objects.all()
            for topic in topics:
                publications = publications.filter(topics=topic)
            logic_description = "all of"
        
        # Count by region
        self.stdout.write(self.style.SUCCESS(f"\nFound {publications.count()} publications with {logic_description} topics: {', '.join([t.name for t in topics])}"))
        
        # Group by region
        region_counts = {}
        for pub in publications:
            for region in pub.regions.all():
                region_counts[region.name] = region_counts.get(region.name, 0) + 1
        
        self.stdout.write(self.style.SUCCESS("\nPublications by Region:"))
        for region_name, count in sorted(region_counts.items(), key=lambda x: x[1], reverse=True):
            self.stdout.write(f"{region_name}: {count}")
        
        # Print all publications by region
        regions = {}
        for pub in publications:
            for region in pub.regions.all():
                if region.name not in regions:
                    regions[region.name] = []
                regions[region.name].append(pub)
        
        self.stdout.write(self.style.SUCCESS("\nDetailed Breakdown by Region:"))
        for region_name, pubs in sorted(regions.items()):
            self.stdout.write(f"\n{region_name} ({len(pubs)}):")
            for pub in sorted(pubs, key=lambda p: p.name):
                self.stdout.write(f"  • {pub.name}")
                if options['detail']:
                    self.stdout.write(f"    Authority: {pub.authority}")
                    self.stdout.write(f"    URL: {pub.website_url}")
                    self.stdout.write(f"    Topics: {', '.join([t.name for t in pub.topics.all()])}")
                    self.stdout.write(f"    Languages: {', '.join([l.name for l in pub.languages.all()])}") 