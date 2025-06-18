import logging
from django.core.management.base import BaseCommand
from django.db import models, transaction
from apps.articles.models import Article
from apps.newsapi.models import NewsAPIArticle

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Clean up duplicate articles based on content_hash, keeping the most recent one'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting anything',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Number of duplicate groups to process at a time (default: 100)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        batch_size = options['batch_size']
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No articles will be deleted')
            )
        
        # Find all content_hash values that have duplicates
        duplicate_hashes = Article.objects.values('content_hash').annotate(
            count=models.Count('id')
        ).filter(
            count__gt=1,
            content_hash__isnull=False
        ).values_list('content_hash', flat=True)
        
        total_duplicate_groups = duplicate_hashes.count()
        self.stdout.write(
            self.style.SUCCESS(f'Found {total_duplicate_groups} duplicate content_hash groups')
        )
        
        if total_duplicate_groups == 0:
            self.stdout.write(self.style.SUCCESS('No duplicates found!'))
            return
        
        total_deleted = 0
        processed_groups = 0
        
        # Process duplicates in batches
        for i in range(0, total_duplicate_groups, batch_size):
            batch_hashes = duplicate_hashes[i:i + batch_size]
            
            with transaction.atomic():
                for content_hash in batch_hashes:
                    # Get all articles with this content_hash, ordered by creation date (newest first)
                    duplicate_articles = Article.objects.filter(
                        content_hash=content_hash
                    ).order_by('-fetched_at', '-id')
                    
                    if duplicate_articles.count() <= 1:
                        continue
                    
                    # Keep the first (most recent) article, delete the rest
                    articles_to_keep = duplicate_articles.first()
                    articles_to_delete = duplicate_articles[1:]
                    
                    self.stdout.write(
                        f'Content hash {content_hash}: '
                        f'Keeping article {articles_to_keep.id} "{articles_to_keep.title[:50]}..." '
                        f'(fetched: {articles_to_keep.fetched_at})'
                    )
                    
                    for article in articles_to_delete:
                        self.stdout.write(
                            f'  -> Deleting article {article.id} "{article.title[:50]}..." '
                            f'(fetched: {article.fetched_at})'
                        )
                        
                        if not dry_run:
                            # Delete associated NewsAPIArticle first (if exists)
                            try:
                                newsapi_article = NewsAPIArticle.objects.get(article=article)
                                newsapi_article.delete()
                            except NewsAPIArticle.DoesNotExist:
                                pass
                            
                            # Delete the article
                            article.delete()
                            total_deleted += 1
                    
                    processed_groups += 1
                    
                    # Progress update
                    if processed_groups % 10 == 0:
                        self.stdout.write(
                            f'Processed {processed_groups}/{total_duplicate_groups} duplicate groups'
                        )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'DRY RUN: Would have deleted {sum(Article.objects.filter(content_hash=h).count() - 1 for h in duplicate_hashes)} duplicate articles'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully deleted {total_deleted} duplicate articles')
            )
            
            # Verify no duplicates remain
            remaining_duplicates = Article.objects.values('content_hash').annotate(
                count=models.Count('id')
            ).filter(count__gt=1, content_hash__isnull=False).count()
            
            if remaining_duplicates == 0:
                self.stdout.write(
                    self.style.SUCCESS('✅ No duplicate content_hash values remaining!')
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f'❌ Still have {remaining_duplicates} duplicate groups')
                ) 