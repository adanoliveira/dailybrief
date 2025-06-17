"""
Test Full Content Quality Assessment

Management command to demonstrate the enhanced quality evaluation system
using complete content and modern LLM context windows.
"""
from django.core.management.base import BaseCommand
from django.db.models import Q
from apps.articles.models import Article
from apps.content.quality.evaluator import ContentQualityEvaluator
import json


class Command(BaseCommand):
    help = 'Test full content quality assessment with modern LLM context windows'

    def add_arguments(self, parser):
        parser.add_argument(
            '--article-id',
            type=str,
            help='Specific article public_id to evaluate'
        )
        parser.add_argument(
            '--count',
            type=int,
            default=3,
            help='Number of articles to evaluate (default: 3)'
        )
        parser.add_argument(
            '--model',
            type=str,
            default='gpt-4.1-mini',
            help='LLM model to use (default: gpt-4.1-mini)'
        )
        parser.add_argument(
            '--include-html',
            action='store_true',
            default=True,
            help='Include HTML preprocessing in evaluation'
        )
        parser.add_argument(
            '--show-content-preview',
            action='store_true',
            help='Show preview of content being sent to LLM'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🚀 Testing Full Content Quality Assessment')
        )
        self.stdout.write(
            self.style.WARNING(f"Using model: {options['model']}")
        )
        self.stdout.write(
            self.style.WARNING(f"Modern context windows support complete articles!")
        )
        
        evaluator = ContentQualityEvaluator()
        
        if options['article_id']:
            # Evaluate specific article
            try:
                article = Article.objects.get(public_id=options['article_id'])
                articles = [article]
            except Article.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"Article not found: {options['article_id']}")
                )
                return
        else:
            # Get sample articles with good content
            articles = Article.objects.filter(
                Q(clean_content__isnull=False) & 
                Q(clean_content__gt='') &
                Q(raw_html__isnull=False) &
                Q(raw_html__gt='')
            ).order_by('-updated_at')[:options['count']]
        
        if not articles:
            self.stdout.write(
                self.style.ERROR('No suitable articles found for evaluation')
            )
            return
        
        self.stdout.write(f"\n📊 Evaluating {len(articles)} articles with FULL content:\n")
        
        total_content_chars = 0
        total_html_chars = 0
        total_blocks = 0
        
        for i, article in enumerate(articles, 1):
            self.stdout.write(f"{'='*60}")
            self.stdout.write(f"📰 Article {i}: {article.title[:50]}...")
            self.stdout.write(f"🔗 URL: {article.url}")
            self.stdout.write(f"📅 Published: {article.published_at}")
            
            # Show content statistics
            content_length = len(article.clean_content or article.basic_content or article.content or '')
            html_length = len(article.raw_html or '')
            blocks_count = len(article.content_blocks or [])
            
            total_content_chars += content_length
            total_html_chars += html_length
            total_blocks += blocks_count
            
            self.stdout.write(f"📄 Content: {content_length:,} chars")
            self.stdout.write(f"🏗️  HTML: {html_length:,} chars")
            self.stdout.write(f"🧱 Blocks: {blocks_count}")
            
            if options['show_content_preview']:
                content_preview = (article.clean_content or article.basic_content or article.content or '')[:200]
                self.stdout.write(f"📖 Preview: {content_preview}...")
            
            # Evaluate with full content
            self.stdout.write(f"🔍 Evaluating with COMPLETE content...")
            
            try:
                result = evaluator.evaluate_article_quality(
                    article,
                    include_html=options['include_html'],
                    model_override=options['model']
                )
                
                # Display results
                self.stdout.write(f"⭐ Overall Score: {result.overall_score:.3f}")
                self.stdout.write(f"   📝 Completeness: {result.completeness:.3f}")
                self.stdout.write(f"   🧹 Purity: {result.purity:.3f}")
                self.stdout.write(f"   🏗️  Structure: {result.structure:.3f}")
                self.stdout.write(f"   📖 Readability: {result.readability:.3f}")
                self.stdout.write(f"   🎯 Confidence: {result.confidence:.3f}")
                
                self.stdout.write(f"💰 Cost: ${result.cost_usd:.6f}")
                self.stdout.write(f"🔢 Tokens: {result.tokens_used:,}")
                self.stdout.write(f"⏱️  Time: {result.evaluation_time:.2f}s")
                
                if result.explanation:
                    self.stdout.write(f"💭 Explanation: {result.explanation[:200]}...")
                
                if result.missing_elements:
                    self.stdout.write(f"❌ Missing: {', '.join(result.missing_elements[:3])}")
                
                if result.noise_detected:
                    self.stdout.write(f"🔊 Noise: {', '.join(result.noise_detected[:3])}")
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"❌ Evaluation failed: {e}")
                )
                continue
        
        # Summary statistics
        self.stdout.write(f"\n{'='*60}")
        self.stdout.write(self.style.SUCCESS('📈 FULL CONTENT ASSESSMENT SUMMARY'))
        self.stdout.write(f"📊 Total Articles: {len(articles)}")
        self.stdout.write(f"📄 Total Content: {total_content_chars:,} characters")
        self.stdout.write(f"🏗️  Total HTML: {total_html_chars:,} characters")
        self.stdout.write(f"🧱 Total Blocks: {total_blocks:,}")
        self.stdout.write(f"📊 Avg Content: {total_content_chars//len(articles):,} chars/article")
        self.stdout.write(f"📊 Avg HTML: {total_html_chars//len(articles):,} chars/article")
        self.stdout.write(f"📊 Avg Blocks: {total_blocks//len(articles):.1f} blocks/article")
        
        self.stdout.write(f"\n🎯 Modern LLMs can handle complete articles for better quality assessment!")
        self.stdout.write(f"   • GPT-4.1-mini: 1M+ tokens (~3M+ characters)")
        self.stdout.write(f"   • GPT-4o-mini: 128K tokens (~400K characters)")
        self.stdout.write(f"   • GPT o3: 200K tokens (~650K characters)") 
        self.stdout.write(f"\n✅ Full content evaluation completed!") 