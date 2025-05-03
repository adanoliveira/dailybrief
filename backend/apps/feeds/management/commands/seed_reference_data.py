import os
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import transaction
from apps.feeds.models import Topic, Region, Language, Publication

class Command(BaseCommand):
    help = 'Seeds the database with reference data for topics, regions, languages, and publications'

    def handle(self, *args, **options):
        fixture_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
            'fixtures', 
            'initial_data.json'
        )
        
        self.stdout.write(self.style.SUCCESS(f'Loading fixture from {fixture_path}...'))
        
        with transaction.atomic():
            # Check if data exists
            if Topic.objects.exists() or Region.objects.exists() or Language.objects.exists() or Publication.objects.exists():
                self.stdout.write(self.style.WARNING('Reference data already exists in the database.'))
                
                if options.get('force', False):
                    self.stdout.write(self.style.WARNING('Forcing reload of data...'))
                    # Clear existing data
                    Publication.objects.all().delete()
                    Topic.objects.all().delete()
                    Region.objects.all().delete()
                    Language.objects.all().delete()
                else:
                    self.stdout.write(self.style.WARNING('Skipping seed operation. Use --force to override.'))
                    return
            
            # Load fixture data
            call_command('loaddata', fixture_path, verbosity=1)
            
            # Set up M2M relationships
            self.setup_publication_relations()
            
            self.stdout.write(self.style.SUCCESS('Successfully seeded reference data!'))
    
    def setup_publication_relations(self):
        """
        Sets up many-to-many relationships for publications.
        These cannot be represented in the fixture and need to be established programmatically.
        """
        # Read the fixture directly for category/topic data for each publication
        relations_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            'fixtures',
            'publication_relations.json'
        )
        
        if os.path.exists(relations_path):
            self.stdout.write(self.style.SUCCESS(f'Loading publication relations from {relations_path}...'))
            import json
            with open(relations_path, 'r') as f:
                relations = json.load(f)
                
            # Process the relations
            for news_api_id, rel_data in relations.items():
                try:
                    pub = Publication.objects.get(news_api_id=news_api_id)
                    
                    # Add topics
                    for topic_slug in rel_data.get('topics', []):
                        try:
                            topic = Topic.objects.get(slug=topic_slug)
                            pub.topics.add(topic)
                        except Topic.DoesNotExist:
                            self.stdout.write(self.style.WARNING(f'Topic {topic_slug} not found'))
                    
                    # Add regions
                    for region_code in rel_data.get('regions', []):
                        try:
                            region = Region.objects.get(code=region_code)
                            pub.regions.add(region)
                        except Region.DoesNotExist:
                            self.stdout.write(self.style.WARNING(f'Region {region_code} not found'))
                    
                    # Add languages
                    for lang_code in rel_data.get('languages', []):
                        try:
                            language = Language.objects.get(iso_code=lang_code)
                            pub.languages.add(language)
                        except Language.DoesNotExist:
                            self.stdout.write(self.style.WARNING(f'Language {lang_code} not found'))
                            
                except Publication.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f'Publication with news_api_id {news_api_id} not found'))
        
        # Manually create relationships for initial publications
        self.setup_initial_publications()
    
    def setup_initial_publications(self):
        """Set up relationships for the initial publications defined in the fixture"""
        # BBC News
        try:
            bbc = Publication.objects.get(name="BBC News")
            bbc.topics.add(
                Topic.objects.get(slug="general"),
                Topic.objects.get(slug="business"),
                Topic.objects.get(slug="technology")
            )
            bbc.regions.add(Region.objects.get(code="gb"))
            bbc.languages.add(Language.objects.get(iso_code="en"))
        except Publication.DoesNotExist:
            self.stdout.write(self.style.ERROR('BBC News publication not found'))
            
        # CNN
        try:
            cnn = Publication.objects.get(name="CNN")
            cnn.topics.add(
                Topic.objects.get(slug="general"),
                Topic.objects.get(slug="business"),
                Topic.objects.get(slug="entertainment")
            )
            cnn.regions.add(Region.objects.get(code="us"))
            cnn.languages.add(Language.objects.get(iso_code="en"))
        except Publication.DoesNotExist:
            self.stdout.write(self.style.ERROR('CNN publication not found'))
            
        # NYT
        try:
            nyt = Publication.objects.get(name="The New York Times")
            nyt.topics.add(
                Topic.objects.get(slug="general"),
                Topic.objects.get(slug="business"),
                Topic.objects.get(slug="science"),
                Topic.objects.get(slug="health")
            )
            nyt.regions.add(Region.objects.get(code="us"))
            nyt.languages.add(Language.objects.get(iso_code="en"))
        except Publication.DoesNotExist:
            self.stdout.write(self.style.ERROR('NYT publication not found'))
            
        # Reuters
        try:
            reuters = Publication.objects.get(name="Reuters")
            reuters.topics.add(
                Topic.objects.get(slug="general"),
                Topic.objects.get(slug="business")
            )
            reuters.regions.add(
                Region.objects.get(code="us"),
                Region.objects.get(code="gb")
            )
            reuters.languages.add(Language.objects.get(iso_code="en"))
        except Publication.DoesNotExist:
            self.stdout.write(self.style.ERROR('Reuters publication not found'))
            
        # AP
        try:
            ap = Publication.objects.get(name="Associated Press")
            ap.topics.add(
                Topic.objects.get(slug="general")
            )
            ap.regions.add(Region.objects.get(code="us"))
            ap.languages.add(Language.objects.get(iso_code="en"))
        except Publication.DoesNotExist:
            self.stdout.write(self.style.ERROR('AP publication not found'))
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force reload of reference data even if it exists',
        ) 