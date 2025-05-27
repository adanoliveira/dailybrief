#!/usr/bin/env python3
"""
Test Paywall Bypass Strategy

Test our enhanced paywall bypass strategy on articles known to have paywalls.
"""

import os
import django
from collections import Counter

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dailybrief.settings')
django.setup()

from django.db.models import Q
from apps.articles.models import Article, ContentStatus
from apps.content.fetcher.strategies import PaywallBypassStrategy


def test_paywall_bypass():
    """Test paywall bypass strategy on known paywall articles."""
    
    print("🔓 PAYWALL BYPASS STRATEGY TEST")
    print("=" * 50)
    
    # Get articles that are likely paywalled
    paywall_articles = list(Article.objects.filter(
        Q(content_status=ContentStatus.PAYWALL_BLOCKED) |
        Q(url__icontains='nytimes.com') |
        Q(url__icontains='wsj.com') |
        Q(url__icontains='washingtonpost.com') |
        Q(url__icontains='ft.com') |
        Q(url__icontains='economist.com') |
        Q(url__icontains='bloomberg.com')
    ).select_related('publication')[:10])
    
    print(f"Testing {len(paywall_articles)} potentially paywalled articles")
    
    # Initialize strategy
    strategy = PaywallBypassStrategy()
    
    if not strategy.available:
        print("❌ PaywallBypassStrategy not available (missing dependencies)")
        return
    
    results = {
        'total': 0,
        'successful': 0,
        'failed': 0,
        'strategies_used': Counter(),
        'paywall_detected': 0,
        'content_extracted': 0
    }
    
    print("\n📊 TESTING RESULTS:")
    print("-" * 50)
    
    for i, article in enumerate(paywall_articles, 1):
        print(f"\n[{i}/{len(paywall_articles)}] Testing: {article.title[:60]}...")
        print(f"  Source: {article.source_name}")
        print(f"  URL: {article.url[:80]}...")
        print(f"  Current status: {article.content_status}")
        
        try:
            # Test paywall bypass strategy
            result = strategy.extract(article.url)
            
            results['total'] += 1
            
            if result.success:
                results['successful'] += 1
                results['content_extracted'] += 1
                
                print(f"  ✅ SUCCESS!")
                print(f"  Strategy: {result.strategy_used}")
                print(f"  Content length: {len(result.content)} chars")
                print(f"  Title: {result.title[:50]}...")
                print(f"  Author: {result.author}")
                
                if result.paywall_detected:
                    results['paywall_detected'] += 1
                    print(f"  🚧 Paywall detected: {', '.join(result.paywall_indicators)}")
                
                if result.quality_metrics:
                    quality = result.quality_metrics.get('quality', 0)
                    completeness = result.quality_metrics.get('completeness', 0)
                    print(f"  Quality: {quality:.2f}, Completeness: {completeness:.2f}")
                
            else:
                results['failed'] += 1
                print(f"  ❌ FAILED: {result.error_message}")
            
            results['strategies_used'][result.strategy_used] += 1
            
        except Exception as e:
            results['total'] += 1
            results['failed'] += 1
            print(f"  💥 ERROR: {str(e)}")
    
    # Generate summary report
    print("\n" + "=" * 60)
    print("🔓 PAYWALL BYPASS TEST SUMMARY")
    print("=" * 60)
    
    total = results['total']
    if total > 0:
        success_rate = (results['successful'] / total) * 100
        
        print(f"\n📊 Overall Results:")
        print(f"  Total tested: {total}")
        print(f"  Successful: {results['successful']} ({success_rate:.1f}%)")
        print(f"  Failed: {results['failed']} ({(results['failed']/total)*100:.1f}%)")
        print(f"  Content extracted: {results['content_extracted']}")
        print(f"  Paywalls detected: {results['paywall_detected']}")
        
        print(f"\n🔧 Strategy Breakdown:")
        for strategy, count in results['strategies_used'].most_common():
            percentage = (count / total) * 100
            print(f"  {strategy}: {count} ({percentage:.1f}%)")
        
        print(f"\n💡 Assessment:")
        if success_rate > 50:
            print("  ✅ Excellent! Paywall bypass strategy is highly effective")
        elif success_rate > 25:
            print("  ✅ Good performance, strategy is working well")
        elif success_rate > 10:
            print("  ⚠️  Modest success, consider strategy improvements")
        else:
            print("  ❌ Limited success, review strategy effectiveness")
        
        if results['paywall_detected'] > 0:
            detection_rate = (results['paywall_detected'] / results['successful']) * 100 if results['successful'] > 0 else 0
            print(f"  🚧 Paywall detection rate: {detection_rate:.1f}% of successful extractions")
    
    print(f"\n🎉 Paywall bypass test complete!")
    return results


if __name__ == "__main__":
    test_paywall_bypass() 