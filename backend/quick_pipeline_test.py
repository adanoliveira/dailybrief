#!/usr/bin/env python3
"""
Quick Enhanced Pipeline Test

Test our enhanced content fetching pipeline on a small set of articles
to evaluate improvements and identify error patterns.
"""

import os
import django
from collections import Counter

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dailybrief.settings')
django.setup()

from django.db.models import Q
from apps.articles.models import Article, ContentStatus
from apps.content.fetcher.services import ContentFetcher


def test_enhanced_pipeline():
    """Test enhanced pipeline on problematic articles."""
    
    print("🔍 ENHANCED PIPELINE QUICK TEST")
    print("=" * 50)
    
    # Get articles that had issues (focus on different types)
    test_cases = []
    
    # Get some paywall-blocked articles
    paywall_articles = list(Article.objects.filter(
        content_status=ContentStatus.PAYWALL_BLOCKED
    ).select_related('publication')[:5])
    test_cases.extend(paywall_articles)
    
    # Get some metadata-only articles
    metadata_articles = list(Article.objects.filter(
        content_status=ContentStatus.METADATA_ONLY
    ).select_related('publication')[:5])
    test_cases.extend(metadata_articles)
    
    # Get some articles that had fetch attempts but failed
    failed_articles = list(Article.objects.filter(
        content_fetch_attempts__gte=1,
        content_status__in=[ContentStatus.PENDING, ContentStatus.TECHNICAL_ERROR]
    ).select_related('publication')[:5])
    test_cases.extend(failed_articles)
    
    print(f"Testing {len(test_cases)} articles:")
    print(f"  - {len(paywall_articles)} paywall-blocked")
    print(f"  - {len(metadata_articles)} metadata-only") 
    print(f"  - {len(failed_articles)} previously failed")
    
    # Initialize results tracking
    results = {
        'total': 0,
        'improved': 0,
        'same': 0,
        'degraded': 0,
        'strategies': Counter(),
        'errors': Counter(),
        'transitions': Counter()
    }
    
    fetcher = ContentFetcher()
    
    print("\n📊 TESTING RESULTS:")
    print("-" * 50)
    
    for i, article in enumerate(test_cases, 1):
        print(f"\n[{i}/{len(test_cases)}] Testing: {article.title[:60]}...")
        print(f"  Source: {article.source_name}")
        print(f"  URL: {article.url[:80]}...")
        print(f"  Original status: {article.content_status}")
        
        # Backup original state
        original_status = article.content_status
        original_content_length = len(article.content or '')
        original_quality = article.content_quality_score or 0
        
        # Reset for testing
        article.content_status = ContentStatus.PENDING
        article.content_fetch_attempts = 0
        article.last_fetch_attempt = None
        article.fetch_error_message = ""
        article.save(update_fields=[
            'content_status', 'content_fetch_attempts', 
            'last_fetch_attempt', 'fetch_error_message'
        ])
        
        try:
            # Run enhanced content fetching
            result = fetcher.fetch_article_content(article)
            
            # Refresh from database
            article.refresh_from_db()
            
            # Analyze results
            new_status = article.content_status
            new_content_length = len(article.content or '')
            new_quality = article.content_quality_score or 0
            
            # Determine outcome
            status_hierarchy = {
                ContentStatus.CONTENT_AVAILABLE: 5,
                ContentStatus.PARTIAL_CONTENT: 4,
                ContentStatus.METADATA_ONLY: 3,
                ContentStatus.PAYWALL_BLOCKED: 2,
                ContentStatus.ACCESS_DENIED: 1,
                ContentStatus.TECHNICAL_ERROR: 1,
                ContentStatus.TIMEOUT: 1,
                ContentStatus.INVALID_URL: 0,
                ContentStatus.PENDING: 0,
                ContentStatus.FETCHING: 0
            }
            
            original_score = status_hierarchy.get(original_status, 0)
            new_score = status_hierarchy.get(new_status, 0)
            
            if new_score > original_score:
                outcome = "IMPROVED ✅"
                results['improved'] += 1
            elif new_score == original_score and new_quality > original_quality + 0.1:
                outcome = "IMPROVED ✅ (quality)"
                results['improved'] += 1
            elif new_score == original_score:
                outcome = "SAME ➡️"
                results['same'] += 1
            else:
                outcome = "DEGRADED ❌"
                results['degraded'] += 1
            
            # Track strategy and errors
            if result.extraction_result:
                strategy = result.extraction_result.strategy_used
                results['strategies'][strategy] += 1
                if result.extraction_result.error_message:
                    results['errors'][result.extraction_result.error_message] += 1
            
            # Track transition
            transition = f"{original_status} → {new_status}"
            results['transitions'][transition] += 1
            
            print(f"  New status: {new_status}")
            print(f"  Strategy: {strategy if result.extraction_result else 'None'}")
            print(f"  Content: {original_content_length} → {new_content_length} chars")
            print(f"  Quality: {original_quality:.2f} → {new_quality:.2f}")
            print(f"  Result: {outcome}")
            
            results['total'] += 1
            
        except Exception as e:
            print(f"  ERROR: {str(e)}")
            results['errors'][f"Test error: {str(e)}"] += 1
            results['total'] += 1
    
    # Generate summary report
    print("\n" + "=" * 60)
    print("📈 ENHANCED PIPELINE TEST SUMMARY")
    print("=" * 60)
    
    total = results['total']
    if total > 0:
        print(f"\n📊 Overall Results:")
        print(f"  Total tested: {total}")
        print(f"  Improved: {results['improved']} ({(results['improved']/total)*100:.1f}%)")
        print(f"  Same result: {results['same']} ({(results['same']/total)*100:.1f}%)")
        print(f"  Degraded: {results['degraded']} ({(results['degraded']/total)*100:.1f}%)")
        
        improvement_rate = (results['improved'] / total) * 100
        print(f"\n🎯 Improvement Rate: {improvement_rate:.1f}%")
        
        print(f"\n🔧 Strategy Usage:")
        for strategy, count in results['strategies'].most_common():
            percentage = (count / total) * 100
            print(f"  {strategy}: {count} ({percentage:.1f}%)")
        
        print(f"\n🔄 Status Transitions:")
        for transition, count in results['transitions'].most_common():
            percentage = (count / total) * 100
            print(f"  {transition}: {count} ({percentage:.1f}%)")
        
        if results['errors']:
            print(f"\n❌ Error Patterns:")
            for error, count in results['errors'].most_common(5):
                percentage = (count / total) * 100
                print(f"  {error}: {count} ({percentage:.1f}%)")
        
        # Recommendations
        print(f"\n💡 Quick Assessment:")
        if improvement_rate > 30:
            print("  ✅ Excellent! Enhanced pipeline showing strong improvements")
        elif improvement_rate > 15:
            print("  ✅ Good improvements, pipeline enhancements are working")
        elif improvement_rate > 5:
            print("  ⚠️  Modest improvements, consider strategy optimization")
        else:
            print("  ❌ Limited improvements, review strategy effectiveness")
        
        # Strategy insights
        top_strategy = results['strategies'].most_common(1)
        if top_strategy:
            strategy_name, usage = top_strategy[0]
            print(f"  📈 Most used strategy: {strategy_name} ({usage} uses)")
            
            if strategy_name == 'rss_enhanced':
                print("     RSS enhancement strategy is being utilized effectively")
            elif strategy_name == 'publisher_api':
                print("     Publisher-specific APIs are working well")
            elif strategy_name in ['newspaper3k', 'readability', 'beautifulsoup']:
                print("     Traditional strategies still dominant - good baseline")
    
    print(f"\n🎉 Quick test complete!")
    return results


if __name__ == "__main__":
    test_enhanced_pipeline() 