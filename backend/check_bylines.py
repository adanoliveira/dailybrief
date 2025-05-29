#!/usr/bin/env python3

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dailybrief.settings')
django.setup()

from apps.articles.models import Article, ProcessingStatus
import json

# Get the same article we were working with
article = Article.objects.filter(process_status=ProcessingStatus.COMPLETED, content_blocks__isnull=False).order_by('-updated_at').first()
if not article:
    print('No articles found')
    sys.exit(1)

print(f'Article: {article.title}')

# Look for byline content in content blocks
byline_blocks = []
for i, block in enumerate(article.content_blocks):
    content = str(block.get('content', '')).lower()
    if 'by ' in content and len(content) < 100:
        byline_blocks.append((i, block))

print(f'Found {len(byline_blocks)} potential byline blocks:')
for i, (block_index, block) in enumerate(byline_blocks):
    print(f'Block {block_index}: {block.get("type")} - "{block.get("content")}"')

# Check if "by tina nguyen" specifically exists
tina_blocks = []
for i, block in enumerate(article.content_blocks):
    content = str(block.get('content', '')).lower()
    if 'tina nguyen' in content:
        tina_blocks.append((i, block))

print(f'\nBlocks containing "tina nguyen": {len(tina_blocks)}')
for i, (block_index, block) in enumerate(tina_blocks):
    print(f'Block {block_index}: {block.get("type")} - "{block.get("content")}"') 