#!/usr/bin/env python
import os
import sys
import django

# Setup Django
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dailybrief.settings')
django.setup()

from apps.articles.models import Article, FetchStatus, ProcessingStatus

print(f'Total articles: {Article.objects.count()}')

print('\nStep 1 (Fetch) status breakdown:')
for status in FetchStatus.choices:
    count = Article.objects.filter(fetch_status=status[0]).count()
    print(f'  {status[1]}: {count}')

print('\nStep 2 (Processing) status breakdown:')
for status in ProcessingStatus.choices:
    count = Article.objects.filter(process_status=status[0]).count()
    print(f'  {status[1]}: {count}')

print('\nRecent articles (last 10):')
recent_articles = Article.objects.order_by('-published_at')[:10]
for article in recent_articles:
    print(f'  {article.id}: {article.title[:50]}... (Fetch: {article.fetch_status}, Process: {article.process_status})') 