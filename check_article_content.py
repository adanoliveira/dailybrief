#!/usr/bin/env python3
"""
Check Article Rich Content

Check the current rich content data for article 8bef8c09-2645-4637-8683-9d3fe95c4eec
"""

import os
import django
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dailybrief.settings')
django.setup()

from apps.articles.models import Article

def check_article_content():
    """Check the current rich content data for the specific article."""
    
    try:
        article = Article.objects.get(public_id='8bef8c09-2645-4637-8683-9d3fe95c4eec')
        
        print("=== ARTICLE INFO ===")
        print(f"Title: {article.title}")
        print(f"URL: {article.url}")
        print(f"Content length: {len(article.content)} chars")
        print(f"Rich content blocks: {len(article.rich_content.get('blocks', [])) if article.rich_content else 0}")
        print(f"Media assets: {len(article.media_assets) if article.media_assets else 0}")
        print(f"Has rich content: {article.has_rich_content}")
        print()
        
        print("=== MEDIA ASSETS ===")
        if article.media_assets:
            for i, asset in enumerate(article.media_assets):
                print(f"{i+1}. {asset.get('type', 'unknown')} - {asset.get('src', 'no src')}")
                if asset.get('alt'):
                    print(f"   Alt: {asset['alt']}")
                if asset.get('caption'):
                    print(f"   Caption: {asset['caption']}")
        else:
            print("No media assets found")
        print()
        
        print("=== CONTENT BLOCKS (first 10) ===")
        if article.rich_content and article.rich_content.get('blocks'):
            for i, block in enumerate(article.rich_content['blocks'][:10]):
                content_preview = block.get('content', '')[:100]
                print(f"{i+1}. {block.get('type', 'unknown')} - {content_preview}...")
        else:
            print("No content blocks found")
        print()
        
        print("=== CONTENT PREVIEW (first 500 chars) ===")
        print(article.content[:500])
        print("...")
        
    except Article.DoesNotExist:
        print("Article not found!")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    check_article_content() 