#!/usr/bin/env python3

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dailybrief.settings')
django.setup()

from apps.articles.models import Article, ProcessingStatus

# Get article 15158 specifically
try:
    article = Article.objects.get(id=15158)
    print(f'Article: {article.title}')
    print(f'Content blocks: {len(article.content_blocks)}')
    
    # Show all content blocks with their position and type
    for i, block in enumerate(article.content_blocks):
        block_type = block.get('type', 'unknown')
        content = block.get('content', '')
        level = block.get('level')
        
        # Truncate long content for readability
        if len(content) > 100:
            content_display = content[:100] + '...'
        else:
            content_display = content
        
        # Highlight headings and specific problematic content
        if block_type == 'heading':
            level_str = f" (h{level})" if level else ""
            print(f'{i:3d}. 🎯 HEADING{level_str}: "{content_display}"')
        elif 'related' in content.lower() or 'popular' in content.lower() or 'installer' in content.lower():
            print(f'{i:3d}. ⚠️  {block_type.upper()}: "{content_display}"')
        elif 'newsletter' in content.lower() and len(content) > 200:
            print(f'{i:3d}. ⚠️  NEWSLETTER: "{content_display}"')
        else:
            print(f'{i:3d}. {block_type}: "{content_display}"')
    
    # Look for specific problematic patterns
    print('\n=== PROBLEMATIC CONTENT ANALYSIS ===')
    
    problem_headings = []
    problem_content = []
    
    for i, block in enumerate(article.content_blocks):
        content = block.get('content', '').lower()
        block_type = block.get('type', 'unknown')
        
        # Check for problematic headings
        if block_type == 'heading':
            if any(pattern in content for pattern in ['related', 'most popular', 'installer', 'trending', 'more from']):
                problem_headings.append((i, block))
        
        # Check for newsletter content
        if 'newsletter' in content and 'david pierce' in content:
            problem_content.append((i, block))
    
    print(f'Found {len(problem_headings)} problematic headings:')
    for pos, block in problem_headings:
        print(f'  Position {pos}: "{block.get("content")}"')
    
    print(f'Found {len(problem_content)} problematic content blocks:')
    for pos, block in problem_content:
        content = block.get('content', '')
        print(f'  Position {pos}: "{content[:150]}..."')

except Article.DoesNotExist:
    print('Article 15158 not found')
    sys.exit(1) 