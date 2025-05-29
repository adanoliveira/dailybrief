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
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

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

print('\n=== TESTING TWITTER DETECTION IN PROCESSED PIPELINE ===')

# Find all blockquotes
blockquotes = soup.find_all('blockquote')
print(f'Total blockquotes found: {len(blockquotes)}')

# Test each blockquote through the content block pipeline
for i, bq in enumerate(blockquotes):
    print(f'\n--- Processing Blockquote {i+1} ---')
    
    # Test our detection method
    is_twitter_embed = processor._is_twitter_embed(bq)
    print(f'🐦 Detected as Twitter embed: {is_twitter_embed}')
    
    if is_twitter_embed:
        # Test metadata extraction
        try:
            metadata = processor._extract_twitter_embed_data(bq)
            print(f'   Tweet ID: {metadata.get("tweet_id")}')
            print(f'   Embed URL: {metadata.get("embed_url")}')
            print(f'   Embed type: {metadata.get("embed_type")}')
        except Exception as e:
            print(f'   ❌ Error extracting metadata: {e}')
        
        # Test content block creation
        try:
            print('   Testing content block creation...')
            content_block = processor._element_to_content_block(bq, position=i)
            if content_block:
                print(f'   ✅ Content block created: type={content_block.type}')
                print(f'      Content: {content_block.content}')
                print(f'      Metadata: {content_block.metadata}')
            else:
                print(f'   ❌ Content block creation returned None')
        except Exception as e:
            print(f'   ❌ Error creating content block: {e}')
            import traceback
            traceback.print_exc()

# Also test if blockquotes are being filtered out by section filtering
print('\n=== TESTING SECTION FILTERING ===')
for i, bq in enumerate(blockquotes):
    if processor._is_twitter_embed(bq):
        should_skip = processor._should_skip_element_for_content_blocks(bq)
        print(f'Blockquote {i+1}: should_skip = {should_skip}')
        
        # Test ancestor filtering
        parent = bq.parent
        depth = 0
        while parent and parent.name not in ['body', 'html'] and depth < 5:
            parent_should_skip = processor._should_skip_element_for_content_blocks(parent)
            if parent_should_skip:
                print(f'   Parent {parent.name} (depth {depth}) would be skipped')
            parent = parent.parent
            depth += 1

print('\n=== TESTING FULL PIPELINE ===')
# Test the full pipeline to see where things break
try:
    # Initialize processor state
    processor._current_article_metadata = {}
    processor._extracted_author_info = []
    processor._section_delimiters_cache = None
    processor._current_soup = soup
    
    # Find candidates (simplified)
    print('Finding candidate elements...')
    candidates = processor._find_candidate_elements(soup)
    print(f'Found {len(candidates)} candidates')
    
    if candidates:
        # Score candidates  
        print('Scoring candidates...')
        scored_candidates = processor._score_candidates(candidates, soup)
        print(f'Found {len(scored_candidates)} scored candidates')
        
        if scored_candidates:
            # Select best
            print('Selecting best candidate...')
            best_candidate = processor._select_best_candidate(scored_candidates)
            
            if best_candidate:
                print(f'Best candidate selected with score: {best_candidate.final_score}')
                
                # Test content block creation on the best candidate
                print('Testing content blocks creation...')
                try:
                    content_blocks = processor._structure_content_blocks(best_candidate.element)
                    print(f'Created {len(content_blocks)} content blocks')
                    
                    # Check for Twitter embeds
                    twitter_blocks = [block for block in content_blocks if block.type == 'twitter_embed']
                    print(f'Twitter embed blocks: {len(twitter_blocks)}')
                    
                    for block in twitter_blocks:
                        print(f'   - {block.content}')
                        
                except Exception as e:
                    print(f'❌ Error in content block creation: {e}')
                    import traceback
                    traceback.print_exc()
        
except Exception as e:
    print(f'❌ Error in pipeline: {e}')
    import traceback
    traceback.print_exc() 