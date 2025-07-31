import os
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import transaction
from apps.feeds.models import Topic, Region, Language, Publication
from apps.articles.models import Article

class Command(BaseCommand):
    help = 'Seeds production/staging database with reference data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--feeds-only',
            action='store_true',
            help='Only load feeds data (publications, topics, regions, languages)',
        )
        parser.add_argument(
            '--sample-articles',
            action='store_true', 
            help='Load sample articles (if file exists)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force reload even if data exists',
        )

    def handle(self, *args, **options):
        # Use fixtures directory
        fixtures_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            'fixtures'
        )
        feeds_file = os.path.join(fixtures_dir, 'clean_feeds_only.json')
        articles_file = 'sample_articles_seed.json'  # In manage.py directory
        
        feeds_only = options.get('feeds_only', False)
        sample_articles = options.get('sample_articles', False)
        force = options.get('force', False)
        
        if not feeds_only and not sample_articles:
            # Load feeds by default
            feeds_only = True

        with transaction.atomic():
            if feeds_only:
                self.load_feeds_data(feeds_file, force)
                
            if sample_articles:
                self.load_articles_data(articles_file, force)

        self.stdout.write(
            self.style.SUCCESS('Successfully seeded database!')
        )

    def load_feeds_data(self, feeds_file, force):
        # Check if feeds data exists
        feeds_exist = (Topic.objects.exists() or Region.objects.exists() or 
                      Language.objects.exists() or Publication.objects.exists())
        
        if feeds_exist and not force:
            self.stdout.write(
                self.style.WARNING('Feeds data already exists. Use --force to overwrite.')
            )
            return
        elif feeds_exist and force:
            self.stdout.write(self.style.WARNING('Clearing existing feeds data...'))
            Publication.objects.all().delete()
            Topic.objects.all().delete()
            Region.objects.all().delete()
            Language.objects.all().delete()

        if not os.path.exists(feeds_file):
            self.stdout.write(
                self.style.ERROR(f'Feeds file {feeds_file} not found')
            )
            return

        self.stdout.write(f'Loading feeds data from {feeds_file}...')
        call_command('loaddata', feeds_file)
        
        # Display summary
        self.stdout.write(self.style.SUCCESS('✅ Feeds data loaded successfully:'))
        self.stdout.write(f'  📂 Topics: {Topic.objects.count()}')
        self.stdout.write(f'  🌍 Regions: {Region.objects.count()}')
        self.stdout.write(f'  🗣️ Languages: {Language.objects.count()}')
        self.stdout.write(f'  📰 Publications: {Publication.objects.count()}')

    def load_articles_data(self, articles_file, force):
        if not os.path.exists(articles_file):
            self.stdout.write(
                self.style.WARNING(f'Sample articles file {articles_file} not found. Skipping.')
            )
            return

        # Check if articles exist
        if Article.objects.exists():
            if not force:
                self.stdout.write(
                    self.style.WARNING('Articles already exist. Use --force to overwrite.')
                )
                return
            else:
                self.stdout.write(self.style.WARNING('Clearing existing articles...'))
                Article.objects.all().delete()

        self.stdout.write(f'Loading sample articles from {articles_file}...')
        call_command('loaddata', articles_file)
        
        # Display summary
        self.stdout.write(self.style.SUCCESS('✅ Sample articles loaded:'))
        self.stdout.write(f'  📄 Articles: {Article.objects.count()}') 