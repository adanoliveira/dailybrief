#!/usr/bin/env python3

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dailybrief.settings')
django.setup()

from apps.articles.models import Article, ProcessingStatus
from bs4 import BeautifulSoup
import re

# Get the article  
article = Article.objects.filter(process_status=ProcessingStatus.COMPLETED, content_blocks__isnull=False).order_by('-updated_at').first()
print('Analyzing:', article.title[:50] + '...')

# Parse HTML and find images
soup = BeautifulSoup(article.raw_html, 'html.parser')
all_images = soup.find_all('img')
print(f'Found {len(all_images)} total images')

# Filter out tracking/analytics images and find content images
content_images = []
for i, img in enumerate(all_images):
    src = img.get('src', '')
    alt = img.get('alt', '')
    
    # Skip tracking pixels and analytics images
    if any(skip in src for skip in ['google-analytics', 'tracking', 'pixel', 'analytics']):
        print(f'  {i+1}. SKIPPING tracking image: {src[:50]}...')
        continue
    
    content_images.append(img)
    print(f'  {i+1}. Content image: {src[:80]}...')
    print(f'      Alt: "{alt}"')
    
    # Check if this is the Cath Virginia image
    if 'CVirginia' in src:
        print('      *** This is the Cath Virginia image we expect to have a caption')

print(f'\nFound {len(content_images)} content images')

if content_images:
    first_content_img = content_images[0]
    print(f'\nAnalyzing first content image:')
    print(f'  Parent: <{first_content_img.parent.name}>')
    
    # Look for caption text in surrounding elements
    caption_elements = soup.find_all(string=re.compile(r'(cath virginia|getty)', re.IGNORECASE))
    print(f'\nFound {len(caption_elements)} caption candidates:')
    for i, caption_string in enumerate(caption_elements[:3]):
        parent = caption_string.parent
        text = parent.get_text(strip=True)
        print(f'  {i+1}. <{parent.name}> "{text[:100]}..."')
        
        # Check distance from first CONTENT image
        try:
            all_elements = soup.find_all()
            img_index = all_elements.index(first_content_img)
            caption_index = all_elements.index(parent)
            distance = abs(img_index - caption_index)
            print(f'      Distance from first content image: {distance} elements')
            
            if distance < 50:  # Close to the image
                print(f'      *** CLOSE TO IMAGE - potential caption!')
        except ValueError:
            print('      Could not determine distance')
        print() 