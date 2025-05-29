#!/usr/bin/env python3

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dailybrief.settings')
django.setup()

from apps.articles.models import Article, ProcessingStatus
from bs4 import BeautifulSoup
import re

# Get the article
article = Article.objects.filter(process_status=ProcessingStatus.COMPLETED, content_blocks__isnull=False).order_by('-updated_at').first()
if not article:
    print('No articles found')
    sys.exit(1)

print(f'Analyzing image structure for: {article.title}')

# Parse the raw HTML
soup = BeautifulSoup(article.raw_html, 'html.parser')

# Find the first image (the one missing the caption)
first_img = soup.find('img')
if not first_img:
    print('No images found in HTML')
    sys.exit(1)

print(f'First image src: {first_img.get("src", "")[:100]}...')
print(f'First image alt: {first_img.get("alt", "")}')

# Analyze the surrounding structure
print('\n--- Parent Structure ---')
parent = first_img.parent
level = 0
current = first_img
while current and level < 5:
    print(f'Level {level}: <{current.name}> classes={current.get("class", [])}')
    if level > 0:
        # Show siblings at this level
        siblings = current.find_next_siblings()[:3]
        for i, sibling in enumerate(siblings):
            if hasattr(sibling, 'name'):
                sibling_text = sibling.get_text(strip=True)[:100]
                print(f'  Next sibling {i+1}: <{sibling.name}> "{sibling_text}..."')
                
                # Check if this sibling contains our target caption
                if 'cath virginia' in sibling_text.lower() or 'the verge' in sibling_text.lower():
                    print(f'  *** FOUND CAPTION CANDIDATE: "{sibling_text}"')
    
    current = current.parent
    level += 1

print('\n--- Looking for "Cath Virginia" or "The Verge" in nearby text ---')

# Search for elements containing the caption text
caption_elements = soup.find_all(string=re.compile(r'(cath virginia|the verge)', re.IGNORECASE))
for i, caption_string in enumerate(caption_elements[:5]):
    parent_elem = caption_string.parent
    full_text = parent_elem.get_text(strip=True)
    print(f'\nCaption candidate {i+1}:')
    print(f'  Element: <{parent_elem.name}>')
    print(f'  Classes: {parent_elem.get("class", [])}')
    print(f'  Full text: "{full_text}"')
    
    # Check relationship to first image
    # Is it a sibling?
    img_parent = first_img.parent
    if parent_elem in img_parent.find_all():
        print(f'  *** This element is within the first image\'s parent!')
    
    # Is it near the image?
    try:
        # Find position relative to image
        all_elements = soup.find_all()
        img_index = all_elements.index(first_img)
        caption_index = all_elements.index(parent_elem)
        distance = abs(img_index - caption_index)
        print(f'  Distance from first image: {distance} elements')
        if distance < 20:
            print(f'  *** This is close to the first image!')
    except ValueError:
        print(f'  Could not determine distance')

print('\n--- Manual Search around First Image ---')
# Manually check siblings of the image's parent container
img_container = first_img.parent
if img_container:
    print(f'Image container: <{img_container.name}> classes={img_container.get("class", [])}')
    
    # Check all children for caption-like content
    for i, child in enumerate(img_container.children):
        if hasattr(child, 'name') and hasattr(child, 'get_text'):
            child_text = child.get_text(strip=True)
            if child_text and ('image:' in child_text.lower() or 'photo:' in child_text.lower() or 'cath' in child_text.lower()):
                print(f'  Child {i}: <{child.name}> "{child_text}"')
    
    # Check parent's siblings
    container_parent = img_container.parent
    if container_parent:
        print(f'\nContainer parent: <{container_parent.name}>')
        for i, sibling in enumerate(container_parent.children):
            if hasattr(sibling, 'name') and hasattr(sibling, 'get_text'):
                sibling_text = sibling.get_text(strip=True)
                if sibling_text and ('image:' in sibling_text.lower() or 'cath' in sibling_text.lower() or 'getty' in sibling_text.lower()):
                    print(f'  Parent sibling {i}: <{sibling.name}> "{sibling_text}"') 