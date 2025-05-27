#!/usr/bin/env python3
"""
Test Enhanced Content Fetching Pipeline

This script re-runs content fetching on previously processed articles
to test the effectiveness of our new strategies and analyze error patterns.
"""

import os
import sys
import django
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import json

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dailybrief.settings')
django.setup()

from django.db.models import Q, Count
from apps.articles.models import Article, ContentStatus
from apps.content.fetcher.services import ContentFetcher
from apps.content.fetcher.models import ContentFetchLog


class PipelineTestRunner:
    """Test runner for enhanced content fetching pipeline."""
    
    def __init__(self):
        self.fetcher = ContentFetcher()
        self.results = {
            'total_tested': 0,
            'improved': 0,
            'same_result': 0,
            'degraded': 0,
            'strategy_usage': Counter(),
            'error_patterns': Counter(),
            'before_after': {},
            'detailed_results': []
        }
    
    def get_test_articles(self, limit=200):
        """Get articles for testing - focus on previously failed/problematic ones."""
        
        # Get articles that were previously processed but had issues
        test_articles = Article.objects.filter(
            Q(content_status__in=[
                ContentStatus.PAYWALL_BLOCKED,
                ContentStatus.METADATA_ONLY,
                ContentStatus.TECHNICAL_ERROR,
                ContentStatus.ACCESS_DENIED,
                ContentStatus.TIMEOUT
            ]) |
            Q(content_fetch_attempts__gte=1)  # Articles that had fetch attempts
        ).select_related('publication').order_by('-published_at')[:limit]
        
        print(f"Selected {len(test_articles)} articles for testing")
        
        # Show breakdown by current status (separate query to avoid slice issue)
        status_breakdown = Article.objects.filter(
            Q(content_status__in=[
                ContentStatus.PAYWALL_BLOCKED,
                ContentStatus.METADATA_ONLY,
                ContentStatus.TECHNICAL_ERROR,
                ContentStatus.ACCESS_DENIED,
                ContentStatus.TIMEOUT
            ]) |
            Q(content_fetch_attempts__gte=1)
        ).values('content_status').annotate(
            count=Count('id')
        ).order_by('-count')[:limit]
        
        print("\nCurrent status breakdown:")
        for item in status_breakdown:
            print(f"  {item['content_status']}: {item['count']} articles")
        
        return list(test_articles)
    
    def backup_article_state(self, article):
        """Backup current article state before testing."""
        return {
            'id': article.id,
            'content_status': article.content_status,
            'content_source': article.content_source,
            'content_length': len(article.content or ''),
            'content_quality_score': article.content_quality_score,
            'content_completeness': article.content_completeness,
            'fetch_attempts': article.content_fetch_attempts,
            'error_message': article.fetch_error_message,
            'word_count': article.word_count,
            'read_time': article.read_time_minutes
        }
    
    def reset_article_for_testing(self, article):
        """Reset article to allow re-fetching."""
        # Backup original state
        original_state = self.backup_article_state(article)
        
        # Reset for testing
        article.content_status = ContentStatus.PENDING
        article.content_fetch_attempts = 0
        article.last_fetch_attempt = None
        article.fetch_error_message = ""
        
        # Don't reset content/metadata - we want to compare
        article.save(update_fields=[
            'content_status', 'content_fetch_attempts', 
            'last_fetch_attempt', 'fetch_error_message'
        ])
        
        return original_state
    
    def test_single_article(self, article):
        """Test content fetching for a single article."""
        print(f"\nTesting Article {article.id}: {article.title[:60]}...")
        print(f"  URL: {article.url}")
        print(f"  Source: {article.source_name}")
        
        # Backup original state
        original_state = self.backup_article_state(article)
        
        # Reset for testing
        self.reset_article_for_testing(article)
        
        try:
            # Run enhanced content fetching
            result = self.fetcher.fetch_article_content(article)
            
            # Refresh article from database
            article.refresh_from_db()
            
            # Analyze results
            new_state = self.backup_article_state(article)
            analysis = self.analyze_result(original_state, new_state, result)
            
            print(f"  Original: {original_state['content_status']} -> New: {new_state['content_status']}")
            print(f"  Strategy used: {result.extraction_result.strategy_used if result.extraction_result else 'None'}")
            print(f"  Result: {analysis['outcome']}")
            
            return analysis
            
        except Exception as e:
            print(f"  ERROR: {str(e)}")
            return {
                'outcome': 'error',
                'error': str(e),
                'original_state': original_state,
                'new_state': original_state
            }
    
    def analyze_result(self, original_state, new_state, result):
        """Analyze the result of content fetching."""
        analysis = {
            'original_state': original_state,
            'new_state': new_state,
            'result': result,
            'outcome': 'unknown'
        }
        
        # Determine outcome
        original_status = original_state['content_status']
        new_status = new_state['content_status']
        
        # Define status hierarchy (higher is better)
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
            analysis['outcome'] = 'improved'
        elif new_score == original_score:
            # Check content quality improvements
            original_quality = original_state.get('content_quality_score', 0) or 0
            new_quality = new_state.get('content_quality_score', 0) or 0
            
            if new_quality > original_quality + 0.1:  # Significant improvement
                analysis['outcome'] = 'improved'
            else:
                analysis['outcome'] = 'same_result'
        else:
            analysis['outcome'] = 'degraded'
        
        # Track strategy usage
        if result.extraction_result:
            analysis['strategy_used'] = result.extraction_result.strategy_used
            analysis['success'] = result.success
            analysis['error_message'] = result.extraction_result.error_message
        
        return analysis
    
    def run_test_batch(self, articles, batch_size=10):
        """Run tests on a batch of articles."""
        total_articles = len(articles)
        
        print(f"\n{'='*60}")
        print(f"TESTING ENHANCED CONTENT FETCHING PIPELINE")
        print(f"{'='*60}")
        print(f"Testing {total_articles} articles in batches of {batch_size}")
        
        for i in range(0, total_articles, batch_size):
            batch = articles[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (total_articles + batch_size - 1) // batch_size
            
            print(f"\n--- Batch {batch_num}/{total_batches} ---")
            
            for article in batch:
                try:
                    analysis = self.test_single_article(article)
                    self.update_results(analysis)
                    
                except Exception as e:
                    print(f"Error testing article {article.id}: {str(e)}")
                    self.results['error_patterns'][f"Test error: {str(e)}"] += 1
            
            # Show progress
            print(f"\nProgress: {min(i + batch_size, total_articles)}/{total_articles} articles tested")
            self.print_interim_results()
    
    def update_results(self, analysis):
        """Update overall results with analysis from single article."""
        self.results['total_tested'] += 1
        
        outcome = analysis['outcome']
        if outcome == 'improved':
            self.results['improved'] += 1
        elif outcome == 'same_result':
            self.results['same_result'] += 1
        elif outcome == 'degraded':
            self.results['degraded'] += 1
        
        # Track strategy usage
        if 'strategy_used' in analysis:
            self.results['strategy_usage'][analysis['strategy_used']] += 1
        
        # Track error patterns
        if 'error_message' in analysis and analysis['error_message']:
            self.results['error_patterns'][analysis['error_message']] += 1
        
        # Store detailed result
        self.results['detailed_results'].append(analysis)
        
        # Track before/after status changes
        original_status = analysis['original_state']['content_status']
        new_status = analysis['new_state']['content_status']
        transition = f"{original_status} -> {new_status}"
        
        if transition not in self.results['before_after']:
            self.results['before_after'][transition] = 0
        self.results['before_after'][transition] += 1
    
    def print_interim_results(self):
        """Print interim results during testing."""
        total = self.results['total_tested']
        if total == 0:
            return
        
        improved = self.results['improved']
        same = self.results['same_result']
        degraded = self.results['degraded']
        
        print(f"  Results so far: {improved} improved, {same} same, {degraded} degraded")
        print(f"  Improvement rate: {(improved/total)*100:.1f}%")
    
    def generate_final_report(self):
        """Generate comprehensive final report."""
        total = self.results['total_tested']
        
        print(f"\n{'='*80}")
        print(f"ENHANCED PIPELINE TEST RESULTS")
        print(f"{'='*80}")
        
        # Overall summary
        print(f"\n📊 OVERALL SUMMARY")
        print(f"Total articles tested: {total}")
        print(f"Improved: {self.results['improved']} ({(self.results['improved']/total)*100:.1f}%)")
        print(f"Same result: {self.results['same_result']} ({(self.results['same_result']/total)*100:.1f}%)")
        print(f"Degraded: {self.results['degraded']} ({(self.results['degraded']/total)*100:.1f}%)")
        
        improvement_rate = (self.results['improved'] / total) * 100
        print(f"\n🎯 IMPROVEMENT RATE: {improvement_rate:.1f}%")
        
        # Strategy usage
        print(f"\n🔧 STRATEGY USAGE")
        for strategy, count in self.results['strategy_usage'].most_common():
            percentage = (count / total) * 100
            print(f"  {strategy}: {count} ({percentage:.1f}%)")
        
        # Status transitions
        print(f"\n🔄 STATUS TRANSITIONS")
        for transition, count in sorted(self.results['before_after'].items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total) * 100
            print(f"  {transition}: {count} ({percentage:.1f}%)")
        
        # Error patterns
        print(f"\n❌ ERROR PATTERNS")
        for error, count in self.results['error_patterns'].most_common(10):
            percentage = (count / total) * 100
            print(f"  {error}: {count} ({percentage:.1f}%)")
        
        # Success stories
        print(f"\n✅ SUCCESS STORIES")
        success_stories = [
            analysis for analysis in self.results['detailed_results']
            if analysis['outcome'] == 'improved'
        ]
        
        for story in success_stories[:5]:  # Show top 5
            original = story['original_state']
            new = story['new_state']
            print(f"  Article {original['id']}: {original['content_status']} -> {new['content_status']}")
            if 'strategy_used' in story:
                print(f"    Strategy: {story['strategy_used']}")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS")
        
        if improvement_rate > 20:
            print("  ✅ Excellent improvement rate! The enhanced pipeline is working well.")
        elif improvement_rate > 10:
            print("  ✅ Good improvement rate. Consider optimizing underperforming strategies.")
        else:
            print("  ⚠️  Low improvement rate. Review strategy effectiveness and error patterns.")
        
        # Strategy-specific recommendations
        top_strategy = self.results['strategy_usage'].most_common(1)
        if top_strategy:
            strategy_name, usage_count = top_strategy[0]
            print(f"  📈 {strategy_name} is the most used strategy ({usage_count} uses)")
            
            if strategy_name == 'rss_enhanced':
                print("     Consider improving RSS description quality scoring")
            elif strategy_name == 'publisher_api':
                print("     Consider expanding publisher-specific implementations")
            elif strategy_name in ['newspaper3k', 'readability', 'beautifulsoup']:
                print("     Traditional strategies still dominant - enhance anti-bot measures")
        
        # Error-based recommendations
        top_errors = self.results['error_patterns'].most_common(3)
        for error, count in top_errors:
            if 'paywall' in error.lower():
                print(f"  💰 High paywall detection ({count} cases) - RSS enhancement working as intended")
            elif '403' in error or 'forbidden' in error.lower():
                print(f"  🚫 403 errors ({count} cases) - consider more aggressive anti-bot measures")
            elif 'timeout' in error.lower():
                print(f"  ⏱️  Timeout issues ({count} cases) - optimize request timeouts")
        
        return self.results
    
    def save_results(self, filename=None):
        """Save detailed results to JSON file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"pipeline_test_results_{timestamp}.json"
        
        # Prepare serializable results
        serializable_results = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_tested': self.results['total_tested'],
                'improved': self.results['improved'],
                'same_result': self.results['same_result'],
                'degraded': self.results['degraded'],
                'improvement_rate': (self.results['improved'] / self.results['total_tested']) * 100 if self.results['total_tested'] > 0 else 0
            },
            'strategy_usage': dict(self.results['strategy_usage']),
            'error_patterns': dict(self.results['error_patterns']),
            'status_transitions': self.results['before_after'],
            'detailed_results': [
                {
                    'article_id': analysis['original_state']['id'],
                    'outcome': analysis['outcome'],
                    'original_status': analysis['original_state']['content_status'],
                    'new_status': analysis['new_state']['content_status'],
                    'strategy_used': analysis.get('strategy_used', 'unknown'),
                    'success': analysis.get('success', False),
                    'error_message': analysis.get('error_message', '')
                }
                for analysis in self.results['detailed_results']
            ]
        }
        
        with open(filename, 'w') as f:
            json.dump(serializable_results, f, indent=2)
        
        print(f"\n💾 Results saved to: {filename}")
        return filename


def main():
    """Main test execution."""
    runner = PipelineTestRunner()
    
    # Get test articles
    test_articles = runner.get_test_articles(limit=200)
    
    if not test_articles:
        print("No articles found for testing!")
        return
    
    # Run tests
    runner.run_test_batch(test_articles, batch_size=10)
    
    # Generate final report
    results = runner.generate_final_report()
    
    # Save results
    runner.save_results()
    
    print(f"\n🎉 Testing complete!")


if __name__ == "__main__":
    main() 