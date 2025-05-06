from django.core.management.base import BaseCommand
from apps.feeds.models import Publication, Topic, Region, Language
from django.db.models import Count


class Command(BaseCommand):
    help = 'Review publications and their relationships to topics, regions, and languages'

    def add_arguments(self, parser):
        parser.add_argument('--detail', action='store_true', help='Show detailed information about each publication')
        parser.add_argument('--missing', action='store_true', help='Show only publications with missing relationships')
        parser.add_argument('--topic', type=str, help='Filter by topic slug')
        parser.add_argument('--region', type=str, help='Filter by region code')
        parser.add_argument('--language', type=str, help='Filter by language code')

    def handle(self, *args, **options):
        # Get all publications with annotated counts
        publications = Publication.objects.annotate(
            topic_count=Count('topics', distinct=True),
            region_count=Count('regions', distinct=True),
            language_count=Count('languages', distinct=True)
        )

        # Apply filters
        if options['topic']:
            publications = publications.filter(topics__slug=options['topic'])
        if options['region']:
            publications = publications.filter(regions__code=options['region'])
        if options['language']:
            publications = publications.filter(languages__iso_code=options['language'])
        if options['missing']:
            publications = publications.filter(
                topic_count=0
            ) | publications.filter(
                region_count=0
            ) | publications.filter(
                language_count=0
            )

        # Overall statistics
        total_pubs = publications.count()
        missing_topics = publications.filter(topic_count=0).count()
        missing_regions = publications.filter(region_count=0).count()
        missing_languages = publications.filter(language_count=0).count()
        complete_pubs = publications.filter(topic_count__gt=0, region_count__gt=0, language_count__gt=0).count()

        # Print summary
        self.stdout.write(self.style.SUCCESS(f"Publication Relationship Summary"))
        self.stdout.write(f"Total Publications: {total_pubs}")
        self.stdout.write(f"Complete Publications: {complete_pubs} ({(complete_pubs/total_pubs*100 if total_pubs else 0):.1f}%)")
        self.stdout.write(f"Missing Topics: {missing_topics} ({(missing_topics/total_pubs*100 if total_pubs else 0):.1f}%)")
        self.stdout.write(f"Missing Regions: {missing_regions} ({(missing_regions/total_pubs*100 if total_pubs else 0):.1f}%)")
        self.stdout.write(f"Missing Languages: {missing_languages} ({(missing_languages/total_pubs*100 if total_pubs else 0):.1f}%)")

        # Print available topics, regions, and languages
        self.stdout.write("\n" + self.style.SUCCESS("Available Classifications:"))
        self.stdout.write(f"Topics: {Topic.objects.count()}")
        self.stdout.write(", ".join([f"{t.name} ({t.slug})" for t in Topic.objects.all()]))
        
        self.stdout.write(f"\nRegions: {Region.objects.count()}")
        self.stdout.write(", ".join([f"{r.name} ({r.code})" for r in Region.objects.all()]))
        
        self.stdout.write(f"\nLanguages: {Language.objects.count()}")
        self.stdout.write(", ".join([f"{l.name} ({l.iso_code})" for l in Language.objects.all()]))

        # Print detailed publication information if requested
        if options['detail']:
            self.stdout.write("\n" + self.style.SUCCESS("Publication Details:"))
            for pub in publications.order_by('name'):
                self.stdout.write(f"\n{pub.name} (ID: {pub.id})")
                self.stdout.write(f"  Authority: {pub.authority}")
                self.stdout.write(f"  URL: {pub.website_url}")
                
                # Topics
                topics = pub.topics.all()
                if topics:
                    self.stdout.write(f"  Topics ({len(topics)}): {', '.join([t.name for t in topics])}")
                else:
                    self.stdout.write(self.style.WARNING("  Topics: None"))
                
                # Regions
                regions = pub.regions.all()
                if regions:
                    self.stdout.write(f"  Regions ({len(regions)}): {', '.join([r.name for r in regions])}")
                else:
                    self.stdout.write(self.style.WARNING("  Regions: None"))
                
                # Languages
                languages = pub.languages.all()
                if languages:
                    self.stdout.write(f"  Languages ({len(languages)}): {', '.join([l.name for l in languages])}")
                else:
                    self.stdout.write(self.style.WARNING("  Languages: None")) 