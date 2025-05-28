#!/usr/bin/env python3

import os
import sys
import django

# Add the project root to Python path
sys.path.insert(0, '/app')

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from apps.content.processor.algorithmic_processor import AlgorithmicProcessor
from apps.articles.models import Article
from bs4 import BeautifulSoup

def debug_candidates():
    """Debug candidate selection for King Charles article."""
    
    article = Article.objects.get(id=15193)
    processor = AlgorithmicProcessor()
    
    soup = BeautifulSoup(article.raw_html, 'html.parser')
    
    # Find candidates
    candidates = processor._find_candidate_elements(soup)
    print(f"Found {len(candidates)} candidates")
    
    # Score candidates
    scored_candidates = processor._score_candidates(candidates, soup)
    print(f"Scored {len(scored_candidates)} viable candidates")
    
    # Show top candidates
    for i, candidate in enumerate(scored_candidates[:10]):
        element = candidate.element
        text_preview = element.get_text()[:200].replace('\n', ' ')
        
        print(f"\n--- Candidate {i+1} ---")
        print(f"Score: {candidate.final_score:.2f}")
        print(f"Density: {candidate.score_density:.2f}")
        print(f"Tag: {element.name}")
        print(f"Classes: {element.get('class', [])}")
        print(f"ID: {element.get('id', 'None')}")
        print(f"Text preview: {text_preview}...")
        
        # Check if it contains King Charles content
        full_text = element.get_text()
        has_charles = 'King Charles' in full_text
        has_ottawa = 'Ottawa' in full_text
        has_arrived = 'arrived Monday' in full_text
        
        print(f"Contains 'King Charles': {has_charles}")
        print(f"Contains 'Ottawa': {has_ottawa}")
        print(f"Contains 'arrived Monday': {has_arrived}")
        print(f"Text length: {len(full_text)}")

if __name__ == "__main__":
    debug_candidates() 