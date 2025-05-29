"""
Django management command to test Twitter embed detection and extraction.
Enhanced to detect both rendered iframes AND original blockquote patterns before JavaScript transformation.
"""

from django.core.management.base import BaseCommand
from apps.articles.models import Article
from apps.content.processor.algorithmic_processor import AlgorithmicProcessor
import json


class Command(BaseCommand):
    help = 'Test Twitter embed detection and extraction'

    def add_arguments(self, parser):
        parser.add_argument(
            '--article-id',
            type=int,
            help='Specific article ID to test',
        )
        parser.add_argument(
            '--url',
            type=str,
            help='Specific article URL to test',
        )

    def handle(self, *args, **options):
        """Test Twitter embed detection on articles."""
        
        if options['article_id']:
            try:
                article = Article.objects.get(id=options['article_id'])
            except Article.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Article with ID {options['article_id']} not found"))
                return
                
        elif options['url']:
            try:
                article = Article.objects.get(url=options['url'])
            except Article.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Article with URL '{options['url']}' not found"))
                return
        else:
            # Get the NHL article which should have Twitter embeds
            article = Article.objects.filter(
                url="https://www.nhl.com/news/united-states-wins-gold-at-2025-iihf-world-championship"
            ).first()
            
            if not article:
                self.stdout.write(self.style.ERROR("NHL article not found"))
                return
            self.stdout.write("Testing NHL article with Twitter embeds")

        self.stdout.write(f"\nArticle: {article.title[:80]}...")
        self.stdout.write(f"URL: {article.url}")

        # Process with enhanced Twitter embed detection
        processor = AlgorithmicProcessor()
        result = processor.process_content(article.raw_html, {
            'title': article.title,
            'url': article.url
        })

        if not result.success:
            self.stdout.write(self.style.ERROR(f"Processing failed: {result.error_message}"))
            return

        self.stdout.write(f"\n✅ Processing successful!")
        self.stdout.write(f"Total content blocks: {len(result.content_blocks)}")

        # Analyze Twitter embeds
        twitter_embeds = [block for block in result.content_blocks if block.type == 'twitter_embed']
        
        if twitter_embeds:
            self.stdout.write(self.style.SUCCESS(f"\n🐦 Found {len(twitter_embeds)} Twitter embed(s)!"))
            
            for i, embed in enumerate(twitter_embeds, 1):
                self.stdout.write(f"\nTwitter Embed #{i}:")
                self.stdout.write(f"  Content: {embed.content}")
                self.stdout.write(f"  Position: {embed.position}")
                
                if embed.metadata:
                    self.stdout.write("  Metadata:")
                    for key, value in embed.metadata.items():
                        if key == 'embed_url' and len(str(value)) > 100:
                            # Truncate long URLs
                            truncated = str(value)[:100] + "..."
                            self.stdout.write(f"    {key}: {truncated}")
                        else:
                            self.stdout.write(f"    {key}: {value}")
        else:
            self.stdout.write(self.style.WARNING("\n⚠️ No Twitter embeds found"))
            
            # Let's debug why Twitter embeds aren't being found
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(article.raw_html, 'html.parser')
            
            # Find all divs with twitter-related classes
            twitter_divs = soup.find_all('div', class_=lambda x: x and 'twitter' in ' '.join(x).lower())
            self.stdout.write(f"\n🔍 Found {len(twitter_divs)} div(s) with 'twitter' in class names:")
            
            for i, div in enumerate(twitter_divs[:5], 1):  # Show first 5
                classes = ' '.join(div.get('class', []))
                self.stdout.write(f"\n  Div #{i}: {classes}")
                
                # Test our detection method
                processor = AlgorithmicProcessor()
                is_twitter_embed = processor._is_twitter_embed(div)
                self.stdout.write(f"    _is_twitter_embed: {is_twitter_embed}")
                
                if is_twitter_embed:
                    twitter_data = processor._extract_twitter_embed_data(div)
                    self.stdout.write(f"    Twitter data: {twitter_data}")
                
                # Check for iframe
                iframe = div.find('iframe')
                if iframe:
                    src = iframe.get('src', '')
                    data_tweet_id = iframe.get('data-tweet-id', '')
                    if 'platform.twitter.com' in src:
                        self.stdout.write(f"    ✅ Contains Twitter iframe")
                        self.stdout.write(f"    Iframe src: {src[:120]}...")
                        self.stdout.write(f"    data-tweet-id: {data_tweet_id}")
                    else:
                        self.stdout.write(f"    ❌ Contains non-Twitter iframe")
                else:
                    self.stdout.write("    ❌ No iframe found")
                
                # Check if this div would be skipped
                would_skip = processor._should_skip_element_for_content_blocks(div)
                self.stdout.write(f"    Would skip element: {would_skip}")
                
                # Check parent context
                parent_classes = ' '.join(div.parent.get('class', [])) if div.parent else "No parent"
                self.stdout.write(f"    Parent classes: {parent_classes}")
            
            # Also check for oembed divs
            oembed_divs = soup.find_all('div', class_=lambda x: x and 'oembed' in ' '.join(x).lower())
            if oembed_divs:
                self.stdout.write(f"\n🔍 Found {len(oembed_divs)} div(s) with 'oembed' in class names:")
                for i, div in enumerate(oembed_divs[:3], 1):
                    classes = ' '.join(div.get('class', []))
                    self.stdout.write(f"  Oembed Div #{i}: {classes}")
                    
                    # Test detection
                    is_twitter_embed = processor._is_twitter_embed(div)
                    self.stdout.write(f"    _is_twitter_embed: {is_twitter_embed}")
            
            # Check what content blocks were actually created for comparison
            self.stdout.write(f"\n📝 Sample content blocks (first 5):")
            for i, block in enumerate(result.content_blocks[:5], 1):
                self.stdout.write(f"  Block #{i} ({block.type}): {block.content[:60]}...")
        
        # Show distribution of all block types
        self.stdout.write(f"\n📊 Content block distribution:")
        block_types = {}
        for block in result.content_blocks:
            block_types[block.type] = block_types.get(block.type, 0) + 1
        
        for block_type, count in sorted(block_types.items()):
            self.stdout.write(f"  {block_type}: {count}")

        self.stdout.write(f"\nProcessing time: {result.processing_time_ms}ms") 