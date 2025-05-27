#!/usr/bin/env python3
"""
Test Rich Content Extraction

Test our enhanced content extraction with rich media and formatting preservation.
"""

import os
import django
import json
from collections import Counter

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dailybrief.settings')
django.setup()

from django.db.models import Q
from apps.articles.models import Article, ContentStatus
from apps.content.fetcher.strategies import PaywallBypassStrategy


def test_rich_content_extraction():
    """Test rich content extraction on various article types."""
    
    print("🎨 RICH CONTENT EXTRACTION TEST")
    print("=" * 50)
    
    # Get articles with different content types
    test_articles = list(Article.objects.filter(
        Q(content_status__in=[ContentStatus.CONTENT_AVAILABLE, ContentStatus.PARTIAL_CONTENT]) |
        Q(url__icontains='cnn.com') |
        Q(url__icontains='bbc.com') |
        Q(url__icontains='washingtonpost.com') |
        Q(url__icontains='nytimes.com')
    ).select_related('publication')[:8])
    
    print(f"Testing {len(test_articles)} articles for rich content extraction")
    
    # Initialize strategy
    strategy = PaywallBypassStrategy()
    
    if not strategy.available:
        print("❌ PaywallBypassStrategy not available (missing dependencies)")
        return
    
    results = {
        'total': 0,
        'successful': 0,
        'with_images': 0,
        'with_videos': 0,
        'with_audio': 0,
        'with_formatting': 0,
        'with_structured_blocks': 0,
        'media_count': Counter(),
        'block_types': Counter(),
        'formatting_types': Counter()
    }
    
    print("\n🎨 RICH CONTENT RESULTS:")
    print("-" * 50)
    
    for i, article in enumerate(test_articles, 1):
        print(f"\n[{i}/{len(test_articles)}] Testing: {article.title[:60]}...")
        print(f"  Source: {article.source_name}")
        print(f"  URL: {article.url[:80]}...")
        
        try:
            # Test rich content extraction
            result = strategy.extract(article.url)
            
            results['total'] += 1
            
            if result.success:
                results['successful'] += 1
                
                print(f"  ✅ SUCCESS!")
                print(f"  Content length: {len(result.content)} chars")
                print(f"  Title: {result.title[:50]}...")
                
                # Analyze rich content
                if result.rich_content and result.rich_content.get('blocks'):
                    results['with_structured_blocks'] += 1
                    blocks = result.rich_content['blocks']
                    print(f"  📄 Structured blocks: {len(blocks)}")
                    
                    # Count block types
                    for block in blocks:
                        block_type = block.get('type', 'unknown')
                        results['block_types'][block_type] += 1
                
                # Analyze media assets
                if result.media_assets:
                    media_types = [asset['type'] for asset in result.media_assets]
                    
                    if any('image' in t for t in media_types):
                        results['with_images'] += 1
                        image_count = len([t for t in media_types if 'image' in t])
                        print(f"  🖼️  Images: {image_count}")
                        results['media_count']['images'] += image_count
                    
                    if any('video' in t for t in media_types):
                        results['with_videos'] += 1
                        video_count = len([t for t in media_types if 'video' in t])
                        print(f"  🎥 Videos: {video_count}")
                        results['media_count']['videos'] += video_count
                    
                    if any('audio' in t for t in media_types):
                        results['with_audio'] += 1
                        audio_count = len([t for t in media_types if 'audio' in t])
                        print(f"  🎵 Audio: {audio_count}")
                        results['media_count']['audio'] += audio_count
                    
                    # Show sample media
                    for asset in result.media_assets[:2]:  # Show first 2 media items
                        print(f"    - {asset['type']}: {asset.get('src', '')[:60]}...")
                        if asset.get('alt'):
                            print(f"      Alt: {asset['alt'][:40]}...")
                        if asset.get('caption'):
                            print(f"      Caption: {asset['caption'][:40]}...")
                
                # Analyze formatting
                if result.formatting_data:
                    results['with_formatting'] += 1
                    formatting = result.formatting_data
                    
                    format_summary = []
                    if formatting.get('headings'):
                        count = len(formatting['headings'])
                        format_summary.append(f"headings({count})")
                        results['formatting_types']['headings'] += count
                    
                    if formatting.get('links'):
                        count = len(formatting['links'])
                        format_summary.append(f"links({count})")
                        results['formatting_types']['links'] += count
                    
                    if formatting.get('lists'):
                        count = len(formatting['lists'])
                        format_summary.append(f"lists({count})")
                        results['formatting_types']['lists'] += count
                    
                    if formatting.get('quotes'):
                        count = len(formatting['quotes'])
                        format_summary.append(f"quotes({count})")
                        results['formatting_types']['quotes'] += count
                    
                    if formatting.get('emphasis'):
                        count = len(formatting['emphasis'])
                        format_summary.append(f"emphasis({count})")
                        results['formatting_types']['emphasis'] += count
                    
                    if format_summary:
                        print(f"  ✨ Formatting: {', '.join(format_summary)}")
                
                # Show quality metrics
                if result.quality_metrics:
                    quality = result.quality_metrics.get('quality', 0)
                    completeness = result.quality_metrics.get('completeness', 0)
                    print(f"  📊 Quality: {quality:.2f}, Completeness: {completeness:.2f}")
                
            else:
                print(f"  ❌ FAILED: {result.error_message}")
            
        except Exception as e:
            results['total'] += 1
            print(f"  💥 ERROR: {str(e)}")
    
    # Generate summary report
    print("\n" + "=" * 60)
    print("🎨 RICH CONTENT EXTRACTION SUMMARY")
    print("=" * 60)
    
    total = results['total']
    if total > 0:
        success_rate = (results['successful'] / total) * 100
        
        print(f"\n📊 Overall Results:")
        print(f"  Total tested: {total}")
        print(f"  Successful: {results['successful']} ({success_rate:.1f}%)")
        print(f"  With structured blocks: {results['with_structured_blocks']} ({(results['with_structured_blocks']/total)*100:.1f}%)")
        
        print(f"\n🎬 Media Extraction:")
        print(f"  Articles with images: {results['with_images']} ({(results['with_images']/total)*100:.1f}%)")
        print(f"  Articles with videos: {results['with_videos']} ({(results['with_videos']/total)*100:.1f}%)")
        print(f"  Articles with audio: {results['with_audio']} ({(results['with_audio']/total)*100:.1f}%)")
        print(f"  Total media assets: {sum(results['media_count'].values())}")
        
        if results['media_count']:
            print(f"\n📈 Media Breakdown:")
            for media_type, count in results['media_count'].most_common():
                print(f"  {media_type}: {count}")
        
        print(f"\n✨ Formatting Extraction:")
        print(f"  Articles with formatting: {results['with_formatting']} ({(results['with_formatting']/total)*100:.1f}%)")
        
        if results['formatting_types']:
            print(f"\n📝 Formatting Breakdown:")
            for format_type, count in results['formatting_types'].most_common():
                print(f"  {format_type}: {count}")
        
        if results['block_types']:
            print(f"\n🧱 Content Block Types:")
            for block_type, count in results['block_types'].most_common():
                print(f"  {block_type}: {count}")
        
        print(f"\n💡 Assessment:")
        if success_rate > 80:
            print("  ✅ Excellent! Rich content extraction is highly effective")
        elif success_rate > 60:
            print("  ✅ Good performance, rich content extraction working well")
        elif success_rate > 40:
            print("  ⚠️  Modest success, consider improvements")
        else:
            print("  ❌ Limited success, review extraction strategies")
        
        if results['with_images'] > 0:
            print(f"  🖼️  Image extraction: {(results['with_images']/total)*100:.1f}% success rate")
        
        if results['with_formatting'] > 0:
            print(f"  ✨ Formatting preservation: {(results['with_formatting']/total)*100:.1f}% success rate")
    
    print(f"\n🎉 Rich content extraction test complete!")
    return results


if __name__ == "__main__":
    test_rich_content_extraction() 