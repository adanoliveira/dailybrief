#!/usr/bin/env python3

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dailybrief.settings')
django.setup()

from apps.articles.models import Article, ProcessingStatus
from bs4 import BeautifulSoup
from apps.content.processor.algorithmic_processor import AlgorithmicProcessor
import html

# Get the same article we were working with
article = Article.objects.filter(process_status=ProcessingStatus.COMPLETED, content_blocks__isnull=False).order_by('-updated_at').first()
if not article:
    print('No articles found')
    sys.exit(1)

print(f'Article: {article.title}')

# Recreate the same HTML decoding logic as the processor
decoded_html = html.unescape(article.raw_html)
decoded_html = decoded_html.replace('\\u003c', '<')
decoded_html = decoded_html.replace('\\u003e', '>')
decoded_html = decoded_html.replace('\\u0026', '&')
decoded_html = decoded_html.replace('\\"', '"')
decoded_html = decoded_html.replace('\\/', '/')

soup = BeautifulSoup(decoded_html, 'html.parser')
processor = AlgorithmicProcessor()

# Initialize processor state
processor._current_article_metadata = {}
processor._extracted_author_info = []
processor._section_delimiters_cache = None
processor._current_soup = soup

print('\n=== FINDING BEST CANDIDATE ===')
candidates = processor._find_candidate_elements(soup)
scored_candidates = processor._score_candidates(candidates, soup)
best_candidate = processor._select_best_candidate(scored_candidates)

if best_candidate:
    print(f'Best candidate element: {best_candidate.element.name}')
    print(f'Best candidate classes: {best_candidate.element.get("class", [])}')
    print(f'Best candidate ID: {best_candidate.element.get("id", "")}')
    
    # Get some identifying text from the best candidate
    best_text = best_candidate.element.get_text(strip=True)[:200]
    print(f'Best candidate text: {best_text}...')

print('\n=== LOCATING TWITTER BLOCKQUOTES ===')
blockquotes = soup.find_all('blockquote')
twitter_blockquotes = [bq for bq in blockquotes if processor._is_twitter_embed(bq)]

for i, bq in enumerate(twitter_blockquotes):
    print(f'\n--- Twitter Blockquote {i+1} ---')
    
    # Check if it's inside the best candidate
    is_inside_best = False
    if best_candidate:
        is_inside_best = bq in best_candidate.element.find_all('blockquote')
    
    print(f'Inside best candidate: {is_inside_best}')
    
    # Find parent structure
    print('Parent hierarchy:')
    current = bq
    depth = 0
    while current.parent and depth < 8:
        parent = current.parent
        classes = parent.get('class', [])
        element_id = parent.get('id', '')
        print(f'  {depth}: {parent.name} (classes: {classes[:3]}, id: {element_id})')
        current = parent
        depth += 1
    
    # Check surrounding context
    print(f'Text before: {bq.previous_sibling}')
    print(f'Text after: {bq.next_sibling}')
    
    # Get the tweet content
    tweet_text = bq.get_text(strip=True)[:100]
    print(f'Tweet content: {tweet_text}...')

# Check if Twitter blockquotes are in prepended/appended content
if best_candidate:
    print('\n=== CHECKING PREPENDED/APPENDED CONTENT ===')
    try:
        prepended, appended = processor._find_prepended_appended_content(best_candidate.element)
        print(f'Prepended elements: {len(prepended)}')
        print(f'Appended elements: {len(appended)}')
        
        # Check if Twitter blockquotes are in these sections
        for bq in twitter_blockquotes:
            in_prepended = any(bq in elem.find_all('blockquote') for elem in prepended)
            in_appended = any(bq in elem.find_all('blockquote') for elem in appended)
            print(f'Twitter blockquote in prepended: {in_prepended}')
            print(f'Twitter blockquote in appended: {in_appended}')
            
    except Exception as e:
        print(f'Error checking prepended/appended: {e}')

# Test the structure_content_blocks_with_siblings method
if best_candidate:
    print('\n=== TESTING WITH SIBLINGS METHOD ===')
    try:
        prepended, appended = processor._find_prepended_appended_content(best_candidate.element)
        content_blocks = processor._structure_content_blocks_with_siblings(
            best_candidate.element, prepended, appended
        )
        print(f'Content blocks with siblings: {len(content_blocks)}')
        
        # Check for Twitter embeds
        twitter_blocks = [block for block in content_blocks if block.type == 'twitter_embed']
        print(f'Twitter embed blocks with siblings: {len(twitter_blocks)}')
        
        for block in twitter_blocks:
            print(f'   - {block.content}')
            
    except Exception as e:
        print(f'❌ Error in siblings method: {e}')
        import traceback
        traceback.print_exc() 