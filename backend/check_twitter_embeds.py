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
print(f'Total content blocks: {len(article.content_blocks)}')

# Look for Twitter/X related content in content blocks
twitter_blocks = []
twitter_keywords = ['twitter', 'x.com', 't.co', 'tweet', '@', '#']

for i, block in enumerate(article.content_blocks):
    content = str(block.get('content', '')).lower()
    block_type = block.get('type', '')
    
    # Check for Twitter-related content
    has_twitter_content = any(keyword in content for keyword in twitter_keywords)
    is_twitter_embed = block_type == 'twitter_embed'
    
    if has_twitter_content or is_twitter_embed:
        twitter_blocks.append({
            'index': i,
            'type': block_type,
            'content': block.get('content', '')[:200] + ('...' if len(str(block.get('content', ''))) > 200 else ''),
            'metadata': block.get('metadata', {}),
            'is_twitter_embed': is_twitter_embed
        })

print(f'\nFound {len(twitter_blocks)} blocks with Twitter/X content:')
for block in twitter_blocks:
    print(f'\n--- Block {block["index"]} ---')
    print(f'Type: {block["type"]}')
    print(f'Is Twitter Embed: {block["is_twitter_embed"]}')
    print(f'Content: {block["content"]}')
    if block["metadata"]:
        print(f'Metadata: {json.dumps(block["metadata"], indent=2)}')

# Check raw HTML for Twitter embeds that might not be detected
print(f'\n--- Checking Raw HTML for Twitter Content ---')
if article.raw_html:
    raw_html = article.raw_html.lower()
    twitter_indicators = [
        'twitter.com',
        'x.com',
        't.co',
        'platform.twitter.com',
        'twitter-tweet',
        'blockquote class="twitter-tweet"',
        'iframe[src*="twitter"]'
    ]
    
    found_in_html = []
    for indicator in twitter_indicators:
        if indicator in raw_html:
            found_in_html.append(indicator)
    
    print(f'Twitter indicators found in raw HTML: {found_in_html}')
    
    # Count occurrences
    twitter_com_count = raw_html.count('twitter.com')
    x_com_count = raw_html.count('x.com')
    tweet_count = raw_html.count('tweet')
    
    print(f'twitter.com mentions: {twitter_com_count}')
    print(f'x.com mentions: {x_com_count}')
    print(f'tweet mentions: {tweet_count}')
else:
    print('No raw HTML available') 