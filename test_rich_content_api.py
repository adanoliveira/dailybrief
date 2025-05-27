#!/usr/bin/env python3
"""
Test script to verify rich content API functionality
"""

import requests
import json

def test_article_detail_api():
    """Test the article detail API with rich content"""
    
    # Test article public UUID that we know has rich content
    article_id = "d5406bef-c3ca-484f-8070-a2c97513c46b"  # The article we just fetched with rich content
    
    # API endpoint (note: no trailing slash)
    url = f"http://localhost:8000/api/articles/{article_id}"
    
    try:
        print(f"🧪 Testing Article Detail API for article {article_id}")
        print(f"URL: {url}")
        print("-" * 60)
        
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            
            print("✅ API Response successful!")
            print(f"Title: {data.get('title', 'N/A')}")
            print(f"Content Status: {data.get('contentStatus', 'N/A')}")
            
            # Check rich content
            rich_content = data.get('richContent', {})
            if rich_content:
                print("\n🎨 Rich Content Data:")
                print(f"  Has Rich Content: {rich_content.get('hasRichContent', False)}")
                print(f"  Content Blocks: {len(rich_content.get('blocks', []))}")
                print(f"  Media Assets: {len(rich_content.get('mediaAssets', []))}")
                print(f"  Has Images: {rich_content.get('hasImages', False)}")
                print(f"  Has Videos: {rich_content.get('hasVideos', False)}")
                print(f"  Media Count: {rich_content.get('mediaCount', 0)}")
                print(f"  Formatting Score: {rich_content.get('formattingScore', 0)}")
                
                # Show first few content blocks
                blocks = rich_content.get('blocks', [])
                if blocks:
                    print(f"\n📄 First 3 Content Blocks:")
                    for i, block in enumerate(blocks[:3]):
                        print(f"  [{i+1}] Type: {block.get('type', 'unknown')}")
                        if block.get('type') == 'heading':
                            print(f"      Level: {block.get('level', 'N/A')}")
                            print(f"      Content: {block.get('content', 'N/A')[:50]}...")
                        elif block.get('type') == 'paragraph':
                            print(f"      Text: {block.get('text', 'N/A')[:50]}...")
                        elif block.get('type') == 'image':
                            print(f"      Src: {block.get('src', 'N/A')[:50]}...")
                            print(f"      Alt: {block.get('alt', 'N/A')[:30]}...")
                
                # Show media assets
                media_assets = rich_content.get('mediaAssets', [])
                if media_assets:
                    print(f"\n🖼️  Media Assets:")
                    for i, asset in enumerate(media_assets[:3]):
                        print(f"  [{i+1}] Type: {asset.get('type', 'unknown')}")
                        print(f"      Src: {asset.get('src', 'N/A')[:50]}...")
                        if asset.get('alt'):
                            print(f"      Alt: {asset.get('alt', 'N/A')[:30]}...")
            else:
                print("\n❌ No rich content data found")
                
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Make sure the backend server is running on localhost:8000")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    test_article_detail_api() 