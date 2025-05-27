#!/usr/bin/env python3
"""
Debug Rich Content Extraction

Test the rich content extraction directly to identify the error source.
"""

import os
import django
import traceback

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dailybrief.settings')
django.setup()

from apps.content.fetcher.strategies import PaywallBypassStrategy

def test_rich_content_extraction():
    """Test rich content extraction directly."""
    
    url = "https://www.washingtonpost.com/health/2025/05/26/covid-vaccine-fda-restrictions-approval/"
    
    print("🔍 TESTING RICH CONTENT EXTRACTION")
    print("=" * 50)
    print(f"URL: {url}")
    print()
    
    try:
        strategy = PaywallBypassStrategy()
        
        if not strategy.available:
            print("❌ PaywallBypassStrategy not available")
            return
        
        print("📥 Extracting content...")
        result = strategy.extract(url)
        
        print(f"✅ Extraction result: {result.success}")
        print(f"📄 Content length: {len(result.content) if result.content else 0}")
        print(f"🎨 Rich content blocks: {len(result.rich_content.get('blocks', [])) if result.rich_content else 0}")
        print(f"🖼️  Media assets: {len(result.media_assets) if result.media_assets else 0}")
        
        if result.media_assets:
            print("\n=== MEDIA ASSETS ===")
            for i, asset in enumerate(result.media_assets):
                print(f"{i+1}. {asset.get('type', 'unknown')}: {asset.get('src', 'no src')}")
                metadata = asset.get('metadata', {})
                width = metadata.get('width')
                height = metadata.get('height')
                print(f"   Size: {width}x{height}")
        
        if result.rich_content and result.rich_content.get('blocks'):
            print(f"\n=== CONTENT BLOCKS (first 5) ===")
            for i, block in enumerate(result.rich_content['blocks'][:5]):
                print(f"{i+1}. {block.get('type', 'unknown')}: {block.get('content', '')[:100]}...")
        
    except Exception as e:
        print(f"❌ Error during extraction: {str(e)}")
        print("\n=== TRACEBACK ===")
        traceback.print_exc()

if __name__ == "__main__":
    test_rich_content_extraction() 