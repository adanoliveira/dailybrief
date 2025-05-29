"""
Django management command to test the new enhanced link extraction.
"""

from django.core.management.base import BaseCommand
from apps.articles.models import Article
from apps.content.processor.algorithmic_processor import AlgorithmicProcessor


class Command(BaseCommand):
    help = 'Test the enhanced link extraction on fresh processing'

    def handle(self, *args, **options):
        """Test enhanced link extraction by force-reprocessing an article."""
        
        # Get the NHL article
        try:
            article = Article.objects.get(url="https://www.nhl.com/news/united-states-wins-gold-at-2025-iihf-world-championship")
        except Article.DoesNotExist:
            self.stdout.write(self.style.ERROR("NHL article not found"))
            return

        self.stdout.write(f"Testing enhanced link extraction on: {article.title[:80]}...")
        
        # Force fresh processing with the enhanced algorithm
        processor = AlgorithmicProcessor()
        result = processor.process_content(article.raw_html, {
            'title': article.title,
            'url': article.url
        })
        
        if result.success:
            self.stdout.write(f"\n✅ Processing successful!")
            self.stdout.write(f"Content blocks: {len(result.content_blocks)}")
            
            # Analyze all links found
            total_links = 0
            blocks_with_links = 0
            
            self.stdout.write(f"\n📋 Link extraction results:")
            
            for i, block in enumerate(result.content_blocks):
                if block.metadata and block.metadata.get('links'):
                    blocks_with_links += 1
                    links = block.metadata['links']
                    total_links += len(links)
                    
                    self.stdout.write(f"\nBlock {i} ({block.type}): {len(links)} links")
                    self.stdout.write(f"Content: {block.content[:100]}...")
                    
                    for link in links:
                        link_type = "Twitter" if 'twitter.com' in link['href'] else "Relative" if link['href'].startswith('/') else "External"
                        self.stdout.write(f"  - '{link['text']}' -> {link['href']} ({link_type})")
            
            self.stdout.write(f"\n📊 Summary:")
            self.stdout.write(f"  Total blocks: {len(result.content_blocks)}")
            self.stdout.write(f"  Blocks with links: {blocks_with_links}")
            self.stdout.write(f"  Total links extracted: {total_links}")
            
            # Show some content blocks without links for context
            self.stdout.write(f"\n📖 Sample content blocks (first 5):")
            for i, block in enumerate(result.content_blocks[:5]):
                self.stdout.write(f"  Block {i} ({block.type}): {block.content[:60]}...")
                
        else:
            self.stdout.write(self.style.ERROR(f"Processing failed: {result.error_message}")) 