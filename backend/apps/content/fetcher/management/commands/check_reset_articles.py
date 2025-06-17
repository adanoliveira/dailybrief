from django.core.management.base import BaseCommand
from apps.articles.models import Article, FetchStatus, ProcessingStatus


class Command(BaseCommand):
    """Management command to check and reset specific articles."""
    
    help = 'Check and reset specific article fetch/processing statuses'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--ids',
            type=str,
            help='Comma-separated list of article IDs to check'
        )
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Reset the articles to pending status'
        )
    
    def handle(self, *args, **options):
        """Handle the command execution."""
        
        if not options['ids']:
            self.stdout.write(self.style.ERROR('Please provide article IDs with --ids'))
            return
        
        # Parse article IDs
        try:
            article_ids = [int(id.strip()) for id in options['ids'].split(',')]
        except ValueError:
            self.stdout.write(self.style.ERROR('Invalid article IDs. Please provide comma-separated integers.'))
            return
        
        self.stdout.write(self.style.SUCCESS('🔍 CHECKING ARTICLE STATUSES'))
        self.stdout.write('=' * 80)
        
        for article_id in article_ids:
            try:
                article = Article.objects.get(id=article_id)
                
                self.stdout.write(f"\n📰 Article {article_id}:")
                self.stdout.write(f"   Title: {article.title[:70]}...")
                self.stdout.write(f"   URL: {article.url}")
                self.stdout.write(f"   📥 Fetch Status: {article.fetch_status}")
                self.stdout.write(f"   ⚙️  Process Status: {article.process_status}")
                self.stdout.write(f"   📅 Published: {article.published_at}")
                self.stdout.write(f"   🔄 Last Updated: {article.updated_at}")
                
                # Show content status
                has_content = bool(article.content and len(article.content) > 100)
                self.stdout.write(f"   📄 Has Content: {has_content}")
                if has_content:
                    self.stdout.write(f"   📝 Content Length: {len(article.content)} chars")
                
                # Show processing results
                has_structured_summary = hasattr(article, 'structured_summary') and article.structured_summary is not None
                self.stdout.write(f"   📋 Has Structured Summary: {has_structured_summary}")
                if has_structured_summary:
                    self.stdout.write(f"   📝 Summary Headline: {article.structured_summary.headline[:50]}...")
                
                # Reset if requested
                if options['reset']:
                    old_fetch_status = article.fetch_status
                    old_process_status = article.process_status
                    
                    article.fetch_status = FetchStatus.PENDING
                    article.process_status = ProcessingStatus.PENDING
                    article.save()
                    
                    self.stdout.write(self.style.WARNING(f"   🔄 RESET: Fetch {old_fetch_status} → {FetchStatus.PENDING}"))
                    self.stdout.write(self.style.WARNING(f"   🔄 RESET: Process {old_process_status} → {ProcessingStatus.PENDING}"))
                
            except Article.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"\n❌ Article {article_id} not found"))
        
        if options['reset']:
            self.stdout.write(self.style.SUCCESS(f"\n✅ Reset {len(article_ids)} articles to pending status"))
        else:
            self.stdout.write(f"\n💡 Use --reset to reset these articles to pending status") 