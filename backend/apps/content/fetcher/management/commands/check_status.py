#!/usr/bin/env python3
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dailybrief.settings')
django.setup()

from apps.articles.models import Article, FetchStatus, ProcessingStatus
from django.db.models import Q

# Check current status
total_articles = Article.objects.filter(published_at__isnull=False).count()

# Step 1 (Fetch) status breakdown
fetch_completed = Article.objects.filter(fetch_status=FetchStatus.COMPLETED).count()
fetch_pending = Article.objects.filter(fetch_status=FetchStatus.PENDING).count()
fetch_failed = Article.objects.filter(fetch_status=FetchStatus.FAILED).count()

# Step 2 (Processing) status breakdown
process_completed = Article.objects.filter(process_status=ProcessingStatus.COMPLETED).count()
process_pending = Article.objects.filter(process_status=ProcessingStatus.PENDING).count()
process_failed = Article.objects.filter(process_status=ProcessingStatus.FAILED).count()

# Count articles with content blocks (processed content)
content_blocks_articles = Article.objects.filter(
    published_at__isnull=False,
    content_blocks__isnull=False
).exclude(content_blocks__exact='[]').count()

print(f'📊 STEP 1 (FETCH) STATUS:')
print(f'Total articles: {total_articles}')
print(f'✅ Fetch completed: {fetch_completed}')
print(f'⏳ Fetch pending: {fetch_pending}')
print(f'❌ Fetch failed: {fetch_failed}')
print(f'Fetch success rate: {fetch_completed/(fetch_completed+fetch_failed)*100:.1f}%' if (fetch_completed+fetch_failed) > 0 else 'N/A')

print(f'\n🔄 STEP 2 (PROCESSING) STATUS:')
print(f'✅ Processing completed: {process_completed}')
print(f'⏳ Processing pending: {process_pending}')
print(f'❌ Processing failed: {process_failed}')
print(f'Processing success rate: {process_completed/(process_completed+process_failed)*100:.1f}%' if (process_completed+process_failed) > 0 else 'N/A')

print(f'\n📝 CONTENT QUALITY:')
print(f'Articles with structured content: {content_blocks_articles}')
print(f'Content processing rate: {content_blocks_articles/total_articles*100:.1f}%')

# Show latest processed articles with content blocks
latest_processed = Article.objects.filter(
    published_at__isnull=False,
    content_blocks__isnull=False
).exclude(content_blocks__exact='[]').order_by('-published_at')[:5]

print(f'\n🌟 LATEST PROCESSED ARTICLES:')
for article in latest_processed:
    content_blocks = article.content_blocks or []
    blocks_count = len(content_blocks)
    route = article.process_route or 'unknown'
    duration = article.process_duration_ms or 0
    print(f'  📰 {article.title[:50]}...')
    print(f'     🎨 {blocks_count} content blocks, 🔄 {route} route, ⏱️ {duration}ms')
    print(f'     🔗 {article.public_id}')
    print() 