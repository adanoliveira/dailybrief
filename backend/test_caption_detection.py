#!/usr/bin/env python3

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dailybrief.settings')
django.setup()

from apps.articles.models import Article, ProcessingStatus
from apps.content.processor.algorithmic_processor import AlgorithmicProcessor
from bs4 import BeautifulSoup
import re

# Get the article
article = Article.objects.filter(process_status=ProcessingStatus.COMPLETED, content_blocks__isnull=False).order_by('-updated_at').first()
if not article:
    print('No articles found')
    sys.exit(1)

print(f'Testing caption detection for: {article.title}')

# Create processor instance to test caption methods
processor = AlgorithmicProcessor()

# Test the specific caption
test_caption = "Image: Cath Virginia / The Verge, Getty Images"
print(f'\nTesting caption: "{test_caption}"')
print(f'Is meaningful: {processor._is_meaningful_caption(test_caption)}')

# Parse the raw HTML and find figure elements
soup = BeautifulSoup(article.raw_html, 'html.parser')
figures = soup.find_all('figure')
print(f'\nFound {len(figures)} figure elements in HTML')

for i, figure in enumerate(figures[:3]):  # Check first 3 figures
    print(f'\n--- Figure {i+1} ---')
    
    # Check if it has img
    img = figure.find('img')
    if img:
        print(f'Image src: {img.get("src", "")[:100]}...')
        print(f'Image alt: {img.get("alt", "")}')
    
    # Test caption extraction
    extracted_caption = processor._extract_visible_figure_caption(figure)
    print(f'Extracted caption: {extracted_caption}')
    
    # Check figcaption
    figcaption = figure.find('figcaption')
    if figcaption:
        figcaption_text = figcaption.get_text(strip=True)
        print(f'Raw figcaption text: "{figcaption_text}"')
        print(f'Is meaningful: {processor._is_meaningful_caption(figcaption_text)}')
        
        # Test the visible caption extraction
        visible = processor._extract_visible_caption_text(figcaption)
        print(f'Visible caption text: "{visible}"')
    else:
        print('No figcaption found')
    
    # Check classes and structure
    print(f'Figure classes: {figure.get("class", [])}')
    
    # Look for caption-related elements around it
    next_sibling = figure.find_next_sibling()
    if next_sibling:
        sibling_text = next_sibling.get_text(strip=True)[:100]
        print(f'Next sibling: {next_sibling.name} - "{sibling_text}..."')

# Look for images in content blocks
print(f'\n--- Content Blocks Analysis ---')
image_blocks = [block for block in article.content_blocks if block.get('type') in ['img', 'figure', 'image']]
print(f'Found {len(image_blocks)} image blocks in content blocks')

for i, block in enumerate(image_blocks[:3]):
    print(f'\nImage block {i+1}:')
    print(f'  Type: {block.get("type")}')
    print(f'  Caption: {block.get("caption")}')
    print(f'  Alt: {block.get("alt")}')
    print(f'  Metadata: {block.get("metadata", {})}')
    print(f'  Content: {block.get("content", "")[:100]}...') 