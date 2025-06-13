"""
Management command to fix malformed URLs containing Unicode escapes.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.articles.models import Article
from apps.content.fetcher.utils import normalize_url


class Command(BaseCommand):
    """Management command to fix malformed URLs with Unicode escapes."""
    
    help = 'Fix malformed URLs containing Unicode escapes (e.g., \\u003d instead of =)'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be fixed without making changes'
        )
        parser.add_argument(
            '--limit',
            type=int,
            help='Limit number of articles to process'
        )
    
    def handle(self, *args, **options):
        """Handle the command execution."""
        
        dry_run = options['dry_run']
        limit = options['limit']
        
        self.stdout.write("🔍 Searching for articles with malformed URLs...")
        
        # Find articles with Unicode escapes in URLs
        malformed_articles = []
        articles_to_check = Article.objects.all()
        
        if limit:
            articles_to_check = articles_to_check[:limit]
        
        for article in articles_to_check:
            if '\\u' in article.url:
                malformed_articles.append(article)
        
        if not malformed_articles:
            self.stdout.write(
                self.style.SUCCESS("✅ No malformed URLs found!")
            )
            return
        
        self.stdout.write(f"📋 Found {len(malformed_articles)} articles with malformed URLs")
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING("🧪 DRY RUN - No changes will be made")
            )
        
        fixed_count = 0
        unchanged_count = 0
        
        for article in malformed_articles:
            original_url = article.url
            normalized_url = normalize_url(original_url)
            
            if original_url != normalized_url:
                fixed_count += 1
                
                self.stdout.write(f"\n📰 Article {article.id}: {article.title[:50]}...")
                self.stdout.write(f"   🔗 Original:  {original_url}")
                self.stdout.write(f"   ✨ Fixed:     {normalized_url}")
                
                if not dry_run:
                    with transaction.atomic():
                        article.url = normalized_url
                        article.save(update_fields=['url'])
                    self.stdout.write("   ✅ Saved to database")
                else:
                    self.stdout.write("   🧪 Would be fixed (dry run)")
            else:
                unchanged_count += 1
                if options.get('verbosity', 1) >= 2:
                    self.stdout.write(f"Article {article.id}: URL already normalized")
        
        # Summary
        self.stdout.write("\n" + "="*60)
        self.stdout.write(f"📊 Summary:")
        self.stdout.write(f"   • Total articles checked: {len(malformed_articles)}")
        self.stdout.write(f"   • URLs fixed: {fixed_count}")
        self.stdout.write(f"   • URLs unchanged: {unchanged_count}")
        
        if dry_run and fixed_count > 0:
            self.stdout.write(
                self.style.WARNING(
                    f"\n🧪 This was a dry run. Run without --dry-run to fix {fixed_count} URLs."
                )
            )
        elif fixed_count > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f"\n✅ Successfully fixed {fixed_count} malformed URLs!"
                )
            )
            self.stdout.write(
                "💡 Tip: These articles can now be re-fetched with proper URLs."
            )
        else:
            self.stdout.write(
                self.style.SUCCESS("\n✅ All URLs are already properly formatted!")
            ) 