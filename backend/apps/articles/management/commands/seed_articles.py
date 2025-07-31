import os
import json
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.core import serializers
from django.db import transaction
from django.utils import timezone
from apps.articles.models import Article, StoryGroup

class Command(BaseCommand):
    help = 'Seeds production with fully processed articles and related metadata'

    def add_arguments(self, parser):
        parser.add_argument(
            '--export',
            action='store_true',
            help='Export articles from local dev to fixtures',
        )
        parser.add_argument(
            '--load',
            action='store_true',
            help='Load articles from fixtures to production',
        )
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Number of days to look back for export (default: 7)',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=50,
            help='Maximum number of articles to export/load (default: 50)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force reload even if articles exist',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be loaded without making changes',
        )

    def handle(self, *args, **options):
        fixtures_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            'fixtures'
        )
        
        if options['export']:
            self.export_articles(fixtures_dir, options['days'], options['limit'])
        elif options['load']:
            self.load_articles(fixtures_dir, options)
        else:
            self.stdout.write("🔍 Use --export to export articles or --load to load them")
            self.stdout.write("   Examples:")
            self.stdout.write("   📦 Export: python manage.py seed_articles --export --days 7 --limit 50")
            self.stdout.write("   📥 Load: python manage.py seed_articles --load --dry-run")

    def export_articles(self, fixtures_dir, days, limit):
        """Export fully processed articles from local dev to fixtures."""
        
        self.stdout.write("📦 Exporting Articles from Local Dev")
        self.stdout.write(f"   Days back: {days}")
        self.stdout.write(f"   Limit: {limit}")
        
        # Get fully processed articles from recent days
        cutoff_date = timezone.now() - timedelta(days=days)
        
        articles = Article.objects.filter(
            published_at__gte=cutoff_date,
            is_top_headline=True,
            summary_ready=True,
            fetch_status='completed',
            process_status='completed',
            summarization_status='completed'
        ).select_related(
            'publication', 'language', 'primary_topic', 'primary_region', 'story_group'
        ).prefetch_related(
            'topics', 'regions'
        ).order_by('-published_at')[:limit]
        
        if not articles.exists():
            self.stdout.write(
                self.style.WARNING("No fully processed articles found for export")
            )
            return
        
        self.stdout.write(f"   Found: {articles.count()} articles to export")
        
        # Create fixtures
        articles_file = os.path.join(fixtures_dir, 'production_articles.json')
        
        try:
            # Export articles
            with open(articles_file, 'w') as f:
                serializers.serialize(
                    'json', articles, 
                    indent=2, stream=f,
                    use_natural_foreign_keys=False
                )
            
            self.stdout.write(f"✅ Articles exported to: {articles_file}")
            
            # Show summary
            self.stdout.write(f"\n📊 Export Summary:")
            self.stdout.write(f"   Articles: {articles.count()}")
            if articles.exists():
                first_article = articles.first()
                last_article = articles.last()
                self.stdout.write(f"   Date range: {last_article.published_at.date()} to {first_article.published_at.date()}")
                self.stdout.write(f"   Publications: {articles.values('publication__name').distinct().count()}")
            self.stdout.write(f"   File size: {os.path.getsize(articles_file) / 1024:.1f} KB")
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Export failed: {e}")
            )

    def load_articles(self, fixtures_dir, options):
        """Load articles from fixtures to production."""
        
        articles_file = os.path.join(fixtures_dir, 'production_articles.json')
        force = options.get('force', False)
        dry_run = options.get('dry_run', False)
        
        self.stdout.write("📥 Loading Articles to Production")
        self.stdout.write(f"   Articles file: {articles_file}")
        self.stdout.write(f"   Force reload: {force}")
        self.stdout.write(f"   Dry run: {dry_run}")
        
        if not os.path.exists(articles_file):
            self.stdout.write(
                self.style.ERROR(f"Articles file not found: {articles_file}")
            )
            return
        
        # Check existing data
        existing_count = Article.objects.count()
        self.stdout.write(f"   Existing articles: {existing_count}")
        
        if existing_count > 0 and not force:
            self.stdout.write(
                self.style.WARNING(
                    "Articles already exist. Use --force to reload."
                )
            )
            return
        
        # Load and parse the fixture file
        try:
            with open(articles_file, 'r') as f:
                data = json.load(f)
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Failed to load articles file: {e}")
            )
            return
        
        if not isinstance(data, list):
            self.stdout.write(
                self.style.ERROR("Articles file should contain a list of articles")
            )
            return
        
        self.stdout.write(f"   Found {len(data)} articles in file")
        
        if dry_run:
            self.stdout.write(self.style.WARNING("\n🧪 DRY RUN - No changes will be made"))
            for item in data[:5]:  # Show first 5
                fields = item.get('fields', {})
                self.stdout.write(
                    f"   Would create: {fields.get('title', 'No title')[:50]}... "
                    f"({fields.get('published_at', 'No date')[:10]})"
                )
            if len(data) > 5:
                self.stdout.write(f"   ... and {len(data) - 5} more articles")
            return
        
        # Load articles
        with transaction.atomic():
            if force and existing_count > 0:
                # Clear existing articles (be careful!)
                deleted_count = Article.objects.count()
                self.stdout.write(
                    self.style.WARNING(f"   🗑️  Would clear {deleted_count} existing articles")
                )
                # Uncomment only if you really want to clear all articles:
                # Article.objects.all().delete()
                # self.stdout.write(f"   🗑️  Cleared {deleted_count} existing articles")
            
            # Use Django's loaddata functionality
            self.stdout.write("   📥 Loading articles...")
            
            try:
                call_command('loaddata', articles_file, verbosity=0)
                
                loaded_count = Article.objects.count() - existing_count
                self.stdout.write(
                    self.style.SUCCESS(f"✅ Successfully loaded {loaded_count} articles")
                )
                
                # Show summary
                self.stdout.write(f"\n📊 Load Summary:")
                recent_articles = Article.objects.order_by('-published_at')[:10]
                for article in recent_articles:
                    self.stdout.write(f"   📰 {article.title[:60]}... ({article.published_at.date()})")
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Failed to load articles: {e}")
                )

    def export_related_data(self, fixtures_dir, article_ids):
        """Export related data for articles (summaries, analysis, etc.)."""
        
        self.stdout.write("📦 Exporting Related Article Data...")
        
        try:
            # Export related models
            related_models = [
                'content.articlerbc',
                'content.articlesummary', 
                'content.articleembedding',
                'content.articleanalysis',
                'content.articleentity',
                'content.articleevent',
                'newsapi.newsapiarticle',
            ]
            
            for model in related_models:
                model_file = os.path.join(fixtures_dir, f'{model.replace(".", "_")}.json')
                
                # Use dumpdata with article filter
                with open(model_file, 'w') as f:
                    call_command(
                        'dumpdata', model,
                        format='json', indent=2,
                        stdout=f
                    )
                
                if os.path.getsize(model_file) > 0:
                    self.stdout.write(f"   ✅ {model}: {os.path.getsize(model_file) / 1024:.1f} KB")
                else:
                    os.remove(model_file)  # Remove empty files
                    
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Related data export failed: {e}")
            ) 