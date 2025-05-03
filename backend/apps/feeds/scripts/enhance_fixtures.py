#!/usr/bin/env python
"""
Script to enhance the initial_data.json fixture with content from top-headlines-sources.json
Run from the project root:
python backend/apps/feeds/scripts/enhance_fixtures.py
"""
import os
import json
from collections import defaultdict

# Path to files
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
FIXTURE_PATH = os.path.join(BASE_DIR, 'apps/feeds/fixtures/initial_data.json')
NEWS_API_PATH = os.path.join(BASE_DIR, '../docs/top-headlines-sources.json')

print(f"Looking for fixture at: {FIXTURE_PATH}")
print(f"Looking for News API data at: {NEWS_API_PATH}")

# Maps for country and language codes to names
COUNTRY_NAMES = {
    'us': 'United States',
    'gb': 'United Kingdom',
    'ca': 'Canada',
    'au': 'Australia',
    'de': 'Germany',
    'fr': 'France',
    'in': 'India',
    'it': 'Italy',
    'jp': 'Japan',
    'ru': 'Russia',
    'sa': 'Saudi Arabia',
    'zh': 'China',
    'ar': 'Argentina',
    'br': 'Brazil',
    'es': 'Spain',
    'ie': 'Ireland',
    'is': 'Israel',
    'nl': 'Netherlands',
    'no': 'Norway',
    'se': 'Sweden',
    'za': 'South Africa',
    'pk': 'Pakistan'
}

LANGUAGE_NAMES = {
    'en': 'English',
    'es': 'Spanish',
    'fr': 'French',
    'de': 'German',
    'it': 'Italian',
    'pt': 'Portuguese',
    'ru': 'Russian',
    'ar': 'Arabic',
    'zh': 'Chinese',
    'ja': 'Japanese',
    'he': 'Hebrew',
    'no': 'Norwegian',
    'se': 'Swedish',
    'nl': 'Dutch',
    'ud': 'Urdu',
    'sv': 'Swedish'
}

def main():
    # Check if files exist
    if not os.path.exists(FIXTURE_PATH):
        print(f"Error: Fixture file not found at {FIXTURE_PATH}")
        return
        
    if not os.path.exists(NEWS_API_PATH):
        print(f"Error: News API sources file not found at {NEWS_API_PATH}")
        return
    
    # Load existing fixture
    with open(FIXTURE_PATH, 'r') as f:
        fixture_data = json.load(f)

    # Load News API sources
    with open(NEWS_API_PATH, 'r') as f:
        news_api_data = json.load(f)

    if 'sources' not in news_api_data:
        print("Error: Invalid News API data format")
        return

    # Build lookup maps from current fixture data
    next_pks = {
        'feeds.topic': 0,
        'feeds.region': 0,
        'feeds.language': 0,
        'feeds.publication': 0
    }
    
    existing = {
        'topics': set(),      # slug
        'regions': set(),     # code
        'languages': set(),   # iso_code
        'publications': set() # news_api_id
    }
    
    # Process existing data
    for item in fixture_data:
        model = item['model']
        next_pks[model] = max(next_pks[model], item['pk'] + 1)
        
        if model == 'feeds.topic':
            existing['topics'].add(item['fields']['slug'])
        elif model == 'feeds.region':
            existing['regions'].add(item['fields']['code'])
        elif model == 'feeds.language':
            existing['languages'].add(item['fields']['iso_code'])
        elif model == 'feeds.publication':
            existing['publications'].add(item['fields']['news_api_id'])
    
    # Track what we'll add
    new_items = []
    new_regions = []
    new_languages = []
    new_publications = []
    
    # First, collect all unique regions and languages
    needed_regions = set()
    needed_languages = set()
    
    for source in news_api_data['sources']:
        if source['id'] not in existing['publications']:
            needed_regions.add(source['country'])
            needed_languages.add(source['language'])
    
    # Add missing regions
    for code in needed_regions:
        if code not in existing['regions']:
            name = COUNTRY_NAMES.get(code, f"Country ({code})")
            region = {
                "model": "feeds.region",
                "pk": next_pks['feeds.region'],
                "fields": {
                    "code": code,
                    "name": name,
                    "created_at": "2025-05-02T00:00:00Z"
                }
            }
            next_pks['feeds.region'] += 1
            existing['regions'].add(code)
            new_regions.append(region)
            new_items.append(region)
    
    # Add missing languages
    for code in needed_languages:
        if code not in existing['languages']:
            name = LANGUAGE_NAMES.get(code, f"Language ({code})")
            language = {
                "model": "feeds.language",
                "pk": next_pks['feeds.language'],
                "fields": {
                    "iso_code": code,
                    "name": name,
                    "created_at": "2025-05-02T00:00:00Z"
                }
            }
            next_pks['feeds.language'] += 1
            existing['languages'].add(code)
            new_languages.append(language)
            new_items.append(language)
    
    # Add publications
    for source in news_api_data['sources']:
        if source['id'] not in existing['publications']:
            publication = {
                "model": "feeds.publication",
                "pk": next_pks['feeds.publication'],
                "fields": {
                    "name": source['name'],
                    "news_api_id": source['id'],
                    "rss_url": "",  # Empty for now
                    "website_url": source['url'],
                    "logo_url": "",  # Empty for now
                    "description": source['description'],
                    "authority": 7.5,  # Default authority
                    "created_at": "2025-05-02T00:00:00Z",
                    "updated_at": "2025-05-02T00:00:00Z"
                }
            }
            next_pks['feeds.publication'] += 1
            existing['publications'].add(source['id'])
            new_publications.append(publication)
            new_items.append(publication)
    
    # Add new items to fixture data
    fixture_data.extend(new_items)
    
    # Create a publication relations json to help with M2M relationships
    pub_relations = defaultdict(lambda: {'topics': [], 'regions': [], 'languages': []})
    
    for source in news_api_data['sources']:
        if source['id'] in existing['publications']:
            if source['category'] in existing['topics']:
                pub_relations[source['id']]['topics'].append(source['category'])
            if source['country'] in existing['regions']:
                pub_relations[source['id']]['regions'].append(source['country'])
            if source['language'] in existing['languages']:
                pub_relations[source['id']]['languages'].append(source['language'])
    
    # Save updated fixture
    with open(FIXTURE_PATH, 'w') as f:
        json.dump(fixture_data, f, indent=2)
    
    # Save publication relations for reference
    relations_path = os.path.join(os.path.dirname(FIXTURE_PATH), 'publication_relations.json')
    with open(relations_path, 'w') as f:
        json.dump(pub_relations, f, indent=2)
    
    print(f"Added {len(new_regions)} new regions")
    print(f"Added {len(new_languages)} new languages")
    print(f"Added {len(new_publications)} new publications")
    print(f"Total items in fixture: {len(fixture_data)}")
    print(f"Updated fixture saved to: {FIXTURE_PATH}")
    print(f"Publication relations saved to: {relations_path}")
    print("You'll need to update seed_reference_data.py to set up M2M relationships")

if __name__ == "__main__":
    main() 