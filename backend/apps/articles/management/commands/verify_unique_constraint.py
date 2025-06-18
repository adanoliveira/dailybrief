from django.core.management.base import BaseCommand
from django.db.models import Count
from apps.articles.models import Article


class Command(BaseCommand):
    help = 'Verify that unique constraint on content_hash is working and no duplicates exist'

    def handle(self, *args, **options):
        # Check current article count
        total_articles = Article.objects.count()
        self.stdout.write(f'Total articles: {total_articles}')

        # Check for any remaining duplicates by content_hash
        duplicates = Article.objects.values('content_hash').annotate(
            count=Count('id')
        ).filter(count__gt=1, content_hash__isnull=False)
        
        duplicate_count = duplicates.count()
        self.stdout.write(f'Duplicate content_hash groups: {duplicate_count}')

        # Check articles with null content_hash
        null_hash = Article.objects.filter(content_hash__isnull=True).count()
        self.stdout.write(f'Articles with null content_hash: {null_hash}')

        # Show some sample content_hashes
        sample_articles = Article.objects.filter(content_hash__isnull=False)[:5]
        self.stdout.write('\nSample articles with content_hash:')
        for article in sample_articles:
            hash_preview = article.content_hash[:16] + '...' if article.content_hash else 'None'
            title_preview = article.title[:50] + '...' if len(article.title) > 50 else article.title
            self.stdout.write(f'  ID {article.id}: {hash_preview} - {title_preview}')

        if duplicate_count == 0:
            self.stdout.write(
                self.style.SUCCESS('\n✅ Verification complete! No duplicates found.')
            )
        else:
            self.stdout.write(
                self.style.ERROR(f'\n❌ Found {duplicate_count} duplicate groups!')
            ) 