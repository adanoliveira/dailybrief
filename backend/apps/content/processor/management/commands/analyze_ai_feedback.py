"""
Management command to analyze AI extraction feedback across articles.

This command provides insights into AI extraction patterns, common challenges,
and improvement suggestions across a sample of processed articles.
"""
import json
from collections import Counter, defaultdict
from typing import Dict, List, Any
from django.core.management.base import BaseCommand
from django.db.models import Q

from apps.articles.models import Article


class Command(BaseCommand):
    """
    Analyze AI extraction feedback across articles for system improvement insights.
    
    This command helps identify patterns in AI extraction feedback to guide
    system improvements and understand common extraction challenges.
    """
    
    help = 'Analyze AI extraction feedback across processed articles'
    
    def add_arguments(self, parser):
        """Add command arguments."""
        parser.add_argument(
            '--limit',
            type=int,
            default=50,
            help='Number of articles to analyze (default: 50)'
        )
        
        parser.add_argument(
            '--min-quality',
            type=float,
            default=0.0,
            help='Minimum quality score to include (default: 0.0)'
        )
        
        parser.add_argument(
            '--template',
            type=str,
            help='Filter by specific template used'
        )
        
        parser.add_argument(
            '--source',
            type=str,
            help='Filter by source/publication name'
        )
        
        parser.add_argument(
            '--export-json',
            type=str,
            help='Export detailed analysis to JSON file'
        )
        
        parser.add_argument(
            '--show-examples',
            action='store_true',
            help='Show specific examples of feedback categories'
        )
    
    def handle(self, *args, **options):
        """Execute the command."""
        try:
            # Find articles with AI extraction data
            articles = self._find_ai_processed_articles(options)
            
            if not articles:
                self.stdout.write(self.style.WARNING("No articles found with AI extraction data"))
                return
            
            self.stdout.write(
                self.style.SUCCESS(f"\n📊 Analyzing AI extraction feedback from {len(articles)} articles")
            )
            
            # Analyze the articles
            analysis = self._analyze_ai_feedback(articles)
            
            # Display analysis results
            self._display_analysis(analysis, options)
            
            # Export to JSON if requested
            if options['export_json']:
                self._export_analysis(analysis, options['export_json'])
            
            self.stdout.write(self.style.SUCCESS(f"\n✅ AI feedback analysis completed"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Analysis failed: {e}"))
    
    def _find_ai_processed_articles(self, options) -> List[Article]:
        """Find articles with AI extraction data."""
        # Base query for articles with AI extraction data
        queryset = Article.objects.filter(
            extracted_metadata__ai_extraction__success=True
        )
        
        # Apply filters
        if options['min_quality'] > 0:
            queryset = queryset.filter(
                extracted_metadata__ai_extraction__quality_score__gte=options['min_quality']
            )
        
        if options['template']:
            queryset = queryset.filter(
                extracted_metadata__ai_extraction__template_used=options['template']
            )
        
        if options['source']:
            queryset = queryset.filter(
                Q(source_name__icontains=options['source']) |
                Q(publication__name__icontains=options['source'])
            )
        
        # Order by most recent and limit
        return list(queryset.order_by('-updated_at')[:options['limit']])
    
    def _analyze_ai_feedback(self, articles: List[Article]) -> Dict[str, Any]:
        """Analyze AI feedback patterns across articles."""
        analysis = {
            'total_articles': len(articles),
            'processing_stats': {
                'total_processing_time_ms': 0,
                'total_tokens': 0,
                'total_estimated_cost': 0.0,
                'avg_quality_score': 0.0,
                'template_usage': Counter(),
                'provider_usage': Counter(),
                'model_usage': Counter()
            },
            'content_analysis': {
                'content_types': Counter(),
                'total_blocks': 0,
                'avg_blocks_per_article': 0.0
            },
            'author_extraction': {
                'total_with_authors': 0,
                'confidence_distribution': Counter(),
                'extraction_success_rate': 0.0
            },
            'heading_analysis': {
                'articles_with_headings': 0,
                'avg_heading_count': 0.0,
                'hierarchy_issues': 0,
                'max_levels_distribution': Counter()
            },
            'feedback_patterns': {
                'improvement_suggestions': Counter(),
                'extraction_challenges': Counter(),
                'unmapped_content_types': Counter(),
                'structural_observations': Counter(),
                'common_confidence_themes': Counter()
            },
            'content_completeness': {
                'total_assessed': 0,
                'complete_articles': 0,
                'incomplete_articles': 0,
                'completeness_rate': 0.0,
                'avg_completeness_percentage': 0.0,
                'truncation_indicators': Counter(),
                'confidence_distribution': Counter(),
                'incomplete_articles_list': []
            },
            'articles_with_feedback': []
        }
        
        # Process each article
        for article in articles:
            ai_data = article.extracted_metadata.get('ai_extraction', {})
            self._process_article_data(article, ai_data, analysis)
        
        # Calculate averages and percentages
        self._calculate_summary_stats(analysis)
        
        return analysis
    
    def _process_article_data(self, article: Article, ai_data: Dict[str, Any], analysis: Dict[str, Any]):
        """Process individual article AI data."""
        # Processing stats
        stats = analysis['processing_stats']
        stats['total_processing_time_ms'] += ai_data.get('processing_time_ms', 0)
        stats['total_tokens'] += ai_data.get('token_usage', 0)
        stats['avg_quality_score'] += ai_data.get('quality_score', 0.0)
        
        # Template and provider usage
        template = ai_data.get('template_used', 'unknown')
        provider = ai_data.get('provider', 'unknown')
        model = ai_data.get('model', 'unknown')
        stats['template_usage'][template] += 1
        stats['provider_usage'][provider] += 1
        stats['model_usage'][model] += 1
        
        # Content analysis
        content_types = ai_data.get('content_types', {})
        for content_type, count in content_types.items():
            analysis['content_analysis']['content_types'][content_type] += count
            analysis['content_analysis']['total_blocks'] += count
        
        # Author extraction
        author_data = ai_data.get('author_extraction', {})
        if author_data.get('extracted'):
            analysis['author_extraction']['total_with_authors'] += 1
            confidence = author_data.get('confidence', 'unknown')
            analysis['author_extraction']['confidence_distribution'][confidence] += 1
        
        # Heading analysis
        heading_data = ai_data.get('heading_analysis', {})
        if heading_data.get('has_headings'):
            analysis['heading_analysis']['articles_with_headings'] += 1
            analysis['heading_analysis']['avg_heading_count'] += heading_data.get('heading_count', 0)
            
            if not heading_data.get('hierarchy_valid', True):
                analysis['heading_analysis']['hierarchy_issues'] += 1
            
            max_level = heading_data.get('max_level')
            if max_level:
                analysis['heading_analysis']['max_levels_distribution'][f'h{max_level}'] += 1
        
        # Feedback analysis
        feedback = ai_data.get('ai_feedback', {})
        if feedback:
            # Track this article has feedback
            analysis['articles_with_feedback'].append({
                'title': article.title[:80] + "..." if len(article.title) > 80 else article.title,
                'public_id': str(article.public_id),
                'source': article.source_name or (article.publication.name if article.publication else 'Unknown'),
                'feedback_summary': self._summarize_article_feedback(feedback)
            })
            
            # Process improvement suggestions
            for suggestion in feedback.get('improvement_suggestions', []):
                # Extract key themes from suggestions
                suggestion_lower = suggestion.lower()
                if 'nested' in suggestion_lower or 'complex' in suggestion_lower:
                    analysis['feedback_patterns']['improvement_suggestions']['nested_content_handling'] += 1
                elif 'dynamic' in suggestion_lower or 'interactive' in suggestion_lower:
                    analysis['feedback_patterns']['improvement_suggestions']['dynamic_content_support'] += 1
                elif 'metadata' in suggestion_lower:
                    analysis['feedback_patterns']['improvement_suggestions']['metadata_extraction'] += 1
                elif 'layout' in suggestion_lower or 'structure' in suggestion_lower:
                    analysis['feedback_patterns']['improvement_suggestions']['layout_understanding'] += 1
                else:
                    analysis['feedback_patterns']['improvement_suggestions']['other'] += 1
            
            # Process extraction challenges
            for challenge in feedback.get('extraction_challenges', []):
                challenge_lower = challenge.lower()
                if 'table' in challenge_lower:
                    analysis['feedback_patterns']['extraction_challenges']['complex_tables'] += 1
                elif 'javascript' in challenge_lower or 'dynamic' in challenge_lower:
                    analysis['feedback_patterns']['extraction_challenges']['dynamic_content'] += 1
                elif 'embed' in challenge_lower:
                    analysis['feedback_patterns']['extraction_challenges']['embedded_content'] += 1
                elif 'format' in challenge_lower:
                    analysis['feedback_patterns']['extraction_challenges']['unusual_formatting'] += 1
                else:
                    analysis['feedback_patterns']['extraction_challenges']['other'] += 1
            
            # Process unmapped content
            for unmapped in feedback.get('unmapped_content', []):
                content_type = unmapped.get('content_type', 'unknown')
                analysis['feedback_patterns']['unmapped_content_types'][content_type] += 1
            
            # Process confidence themes
            confidence_notes = feedback.get('confidence_notes', '')
            if confidence_notes:
                confidence_lower = confidence_notes.lower()
                if 'high' in confidence_lower and 'confident' in confidence_lower:
                    analysis['feedback_patterns']['common_confidence_themes']['high_confidence'] += 1
                elif 'challenge' in confidence_lower or 'difficult' in confidence_lower:
                    analysis['feedback_patterns']['common_confidence_themes']['extraction_challenges'] += 1
                elif 'partial' in confidence_lower or 'incomplete' in confidence_lower:
                    analysis['feedback_patterns']['common_confidence_themes']['partial_extraction'] += 1
                else:
                    analysis['feedback_patterns']['common_confidence_themes']['other'] += 1
            
            # Process content completeness assessment
            if feedback.get('content_completeness'):
                completeness_data = feedback['content_completeness']
                analysis['content_completeness']['total_assessed'] += 1
                
                is_complete = completeness_data.get('is_complete')
                percentage = completeness_data.get('estimated_completeness_percentage', 0)
                confidence = completeness_data.get('confidence', 'unknown')
                
                # Track completion stats
                if is_complete:
                    analysis['content_completeness']['complete_articles'] += 1
                else:
                    analysis['content_completeness']['incomplete_articles'] += 1
                    # Track incomplete articles for detailed analysis
                    analysis['content_completeness']['incomplete_articles_list'].append({
                        'title': article.title[:80] + "..." if len(article.title) > 80 else article.title,
                        'public_id': str(article.public_id),
                        'source': article.source_name or (article.publication.name if article.publication else 'Unknown'),
                        'percentage': percentage,
                        'indicators': completeness_data.get('truncation_indicators', [])
                    })
                
                # Track completeness percentage
                analysis['content_completeness']['avg_completeness_percentage'] += percentage
                
                # Track confidence distribution
                analysis['content_completeness']['confidence_distribution'][confidence] += 1
                
                # Track truncation indicators
                for indicator in completeness_data.get('truncation_indicators', []):
                    # Categorize indicators
                    indicator_lower = indicator.lower()
                    if 'paywall' in indicator_lower or 'subscribe' in indicator_lower:
                        analysis['content_completeness']['truncation_indicators']['paywall_detected'] += 1
                    elif 'continue reading' in indicator_lower or 'read more' in indicator_lower:
                        analysis['content_completeness']['truncation_indicators']['continue_reading_prompt'] += 1
                    elif 'sign in' in indicator_lower or 'login' in indicator_lower:
                        analysis['content_completeness']['truncation_indicators']['login_required'] += 1
                    elif 'abrupt' in indicator_lower or 'cut off' in indicator_lower:
                        analysis['content_completeness']['truncation_indicators']['abrupt_ending'] += 1
                    else:
                        analysis['content_completeness']['truncation_indicators']['other'] += 1
    
    def _summarize_article_feedback(self, feedback: Dict[str, Any]) -> Dict[str, int]:
        """Summarize feedback for a single article."""
        return {
            'suggestions': len(feedback.get('improvement_suggestions', [])),
            'challenges': len(feedback.get('extraction_challenges', [])),
            'unmapped': len(feedback.get('unmapped_content', [])),
            'observations': len(feedback.get('structural_observations', [])),
            'has_confidence_notes': bool(feedback.get('confidence_notes')),
            'has_completeness_assessment': bool(feedback.get('content_completeness')),
            'is_complete': feedback.get('content_completeness', {}).get('is_complete', True)
        }
    
    def _calculate_summary_stats(self, analysis: Dict[str, Any]):
        """Calculate summary statistics."""
        total = analysis['total_articles']
        
        if total > 0:
            # Processing averages
            stats = analysis['processing_stats']
            stats['avg_processing_time_ms'] = stats['total_processing_time_ms'] / total
            stats['avg_tokens_per_article'] = stats['total_tokens'] / total
            stats['avg_quality_score'] = stats['avg_quality_score'] / total
            
            # Rough cost estimation (adjust based on actual pricing)
            cost_per_1k_tokens = 0.01
            stats['total_estimated_cost'] = (stats['total_tokens'] / 1000) * cost_per_1k_tokens
            stats['avg_cost_per_article'] = stats['total_estimated_cost'] / total
            
            # Content averages
            content = analysis['content_analysis']
            content['avg_blocks_per_article'] = content['total_blocks'] / total
            
            # Author extraction rate
            author = analysis['author_extraction']
            author['extraction_success_rate'] = author['total_with_authors'] / total
            
            # Heading averages
            heading = analysis['heading_analysis']
            if heading['articles_with_headings'] > 0:
                heading['avg_heading_count'] = heading['avg_heading_count'] / heading['articles_with_headings']
            
            heading['heading_success_rate'] = heading['articles_with_headings'] / total
            heading['hierarchy_issue_rate'] = heading['hierarchy_issues'] / total
            
            # Content completeness averages
            completeness = analysis['content_completeness']
            if completeness['total_assessed'] > 0:
                completeness['completeness_rate'] = completeness['complete_articles'] / completeness['total_assessed']
                completeness['avg_completeness_percentage'] = completeness['avg_completeness_percentage'] / completeness['total_assessed']
    
    def _display_analysis(self, analysis: Dict[str, Any], options: Dict[str, Any]):
        """Display analysis results."""
        total = analysis['total_articles']
        
        # Processing Overview
        self.stdout.write(f"\n📈 Processing Overview:")
        stats = analysis['processing_stats']
        self.stdout.write(f"   Average processing time: {stats['avg_processing_time_ms']:.0f}ms")
        self.stdout.write(f"   Average tokens per article: {stats['avg_tokens_per_article']:.0f}")
        self.stdout.write(f"   Average quality score: {stats['avg_quality_score']:.3f}")
        self.stdout.write(f"   Total estimated cost: ${stats['total_estimated_cost']:.3f}")
        self.stdout.write(f"   Average cost per article: ${stats['avg_cost_per_article']:.4f}")
        
        # Template and Provider Usage
        self.stdout.write(f"\n🔧 Technology Usage:")
        self.stdout.write(f"   Templates: {dict(stats['template_usage'].most_common())}")
        self.stdout.write(f"   Providers: {dict(stats['provider_usage'].most_common())}")
        self.stdout.write(f"   Models: {dict(stats['model_usage'].most_common())}")
        
        # Content Analysis
        self.stdout.write(f"\n📝 Content Analysis:")
        content = analysis['content_analysis']
        self.stdout.write(f"   Average blocks per article: {content['avg_blocks_per_article']:.1f}")
        self.stdout.write(f"   Most common content types:")
        for content_type, count in content['content_types'].most_common(5):
            percentage = (count / content['total_blocks']) * 100
            self.stdout.write(f"     {content_type}: {count} ({percentage:.1f}%)")
        
        # Author Extraction
        self.stdout.write(f"\n👤 Author Extraction:")
        author = analysis['author_extraction']
        self.stdout.write(f"   Success rate: {author['extraction_success_rate']:.1%}")
        self.stdout.write(f"   Confidence distribution: {dict(author['confidence_distribution'])}")
        
        # Heading Analysis
        self.stdout.write(f"\n📋 Heading Analysis:")
        heading = analysis['heading_analysis']
        self.stdout.write(f"   Articles with headings: {heading['heading_success_rate']:.1%}")
        self.stdout.write(f"   Average headings per article: {heading['avg_heading_count']:.1f}")
        self.stdout.write(f"   Hierarchy issue rate: {heading['hierarchy_issue_rate']:.1%}")
        self.stdout.write(f"   Max heading levels: {dict(heading['max_levels_distribution'])}")
        
        # Content Completeness Analysis
        self.stdout.write(f"\n📄 Content Completeness Analysis:")
        completeness = analysis['content_completeness']
        if completeness['total_assessed'] > 0:
            self.stdout.write(f"   Articles assessed: {completeness['total_assessed']}")
            self.stdout.write(f"   Completeness rate: {completeness['completeness_rate']:.1%}")
            self.stdout.write(f"   Average completeness: {completeness['avg_completeness_percentage']:.1f}%")
            self.stdout.write(f"   Complete articles: {completeness['complete_articles']}")
            self.stdout.write(f"   Incomplete articles: {completeness['incomplete_articles']}")
            
            if completeness['truncation_indicators']:
                self.stdout.write(f"   Common truncation indicators:")
                for indicator, count in completeness['truncation_indicators'].most_common(3):
                    self.stdout.write(f"     {indicator}: {count} articles")
            
            self.stdout.write(f"   Assessment confidence: {dict(completeness['confidence_distribution'])}")
            
            # Show incomplete articles if examples requested
            if options['show_examples'] and completeness['incomplete_articles_list']:
                self.stdout.write(f"\n   📋 Incomplete Articles:")
                for article in completeness['incomplete_articles_list'][:3]:
                    self.stdout.write(f"     {article['title']}")
                    self.stdout.write(f"       Source: {article['source']}, Completeness: {article['percentage']}%")
                    if article['indicators']:
                        indicators = ", ".join(article['indicators'][:2])
                        self.stdout.write(f"       Indicators: {indicators}")
        else:
            self.stdout.write(f"   No content completeness assessments found")
        
        # Feedback Patterns
        self.stdout.write(f"\n💡 AI Feedback Patterns:")
        patterns = analysis['feedback_patterns']
        
        # Improvement suggestions
        if patterns['improvement_suggestions']:
            self.stdout.write(f"   Top improvement themes:")
            for theme, count in patterns['improvement_suggestions'].most_common(3):
                self.stdout.write(f"     {theme}: {count} articles")
        
        # Extraction challenges
        if patterns['extraction_challenges']:
            self.stdout.write(f"   Common extraction challenges:")
            for challenge, count in patterns['extraction_challenges'].most_common(3):
                self.stdout.write(f"     {challenge}: {count} articles")
        
        # Unmapped content
        if patterns['unmapped_content_types']:
            self.stdout.write(f"   Unmapped content types:")
            for content_type, count in patterns['unmapped_content_types'].most_common(3):
                self.stdout.write(f"     {content_type}: {count} occurrences")
        
        # Confidence themes
        if patterns['common_confidence_themes']:
            self.stdout.write(f"   Confidence themes:")
            for theme, count in patterns['common_confidence_themes'].most_common(3):
                self.stdout.write(f"     {theme}: {count} articles")
        
        # Show examples if requested
        if options['show_examples'] and analysis['articles_with_feedback']:
            self.stdout.write(f"\n📋 Example Articles with Feedback:")
            for article in analysis['articles_with_feedback'][:5]:
                self.stdout.write(f"   {article['title']}")
                self.stdout.write(f"     Source: {article['source']}")
                summary = article['feedback_summary']
                self.stdout.write(f"     Feedback: {summary['suggestions']} suggestions, {summary['challenges']} challenges, {summary['unmapped']} unmapped")
    
    def _export_analysis(self, analysis: Dict[str, Any], filename: str):
        """Export analysis to JSON file."""
        # Convert Counter objects to regular dicts for JSON serialization
        def convert_counters(obj):
            if isinstance(obj, Counter):
                return dict(obj)
            elif isinstance(obj, dict):
                return {k: convert_counters(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_counters(item) for item in obj]
            else:
                return obj
        
        serializable_analysis = convert_counters(analysis)
        
        with open(filename, 'w') as f:
            json.dump(serializable_analysis, f, indent=2, default=str)
        
        self.stdout.write(self.style.SUCCESS(f"   📄 Analysis exported to {filename}")) 