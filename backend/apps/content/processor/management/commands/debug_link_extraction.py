"""
Django management command to debug link extraction in the algorithmic processor.
"""

from django.core.management.base import BaseCommand
from apps.articles.models import Article  # Changed to match other commands
from apps.content.processor.algorithmic_processor import AlgorithmicProcessor
import json


class Command(BaseCommand):
    help = 'Debug link extraction in processed articles'

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
        """Debug link extraction on articles."""
        
        if options['article_id']:
            try:
                article = Article.objects.get(id=options['article_id'])
                self.stdout.write(f"Testing specific article ID: {options['article_id']}")
            except Article.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Article with ID {options['article_id']} not found"))
                return
        elif options['url']:
            try:
                article = Article.objects.get(url=options['url'])
                self.stdout.write(f"Testing specific article URL: {options['url']}")
            except Article.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Article with URL {options['url']} not found"))
                return
        else:
            # Get a recent processed article
            article = Article.objects.filter(process_status='completed').order_by('-updated_at').first()
            if not article:
                self.stdout.write(self.style.ERROR("No processed articles found"))
                return
            self.stdout.write("Testing most recent processed article")

        self.stdout.write(f"Article: {article.title[:100]}...")
        self.stdout.write(f"URL: {article.url}")
        self.stdout.write(f"Raw HTML length: {len(article.raw_html) if article.raw_html else 0}")
        
        # Check existing structured content for links
        if article.content_blocks:
            content_blocks = article.content_blocks  # Already a list, no need to parse JSON
            self.stdout.write(f"\nExisting structured content: {len(content_blocks)} blocks")
            
            blocks_with_links = 0
            total_links = 0
            for i, block in enumerate(content_blocks):
                if block.get('metadata', {}).get('links'):
                    blocks_with_links += 1
                    links = block['metadata']['links']
                    total_links += len(links)
                    self.stdout.write(f"\nBlock {i} ({block['type']}): {len(links)} links")
                    self.stdout.write(f"Content preview: {block['content'][:100]}...")
                    for link in links[:3]:  # Show first 3 links
                        self.stdout.write(f"  - '{link['text']}' -> {link['href']}")
            
            self.stdout.write(f"\nSummary: {blocks_with_links} blocks with links, {total_links} total links")
            
            if total_links == 0:
                self.stdout.write(self.style.WARNING("\n🔍 No links found in structured content. Let's check raw HTML..."))
                
                # Re-process the article to see what happens
                processor = AlgorithmicProcessor()
                result = processor.process_content(article.raw_html, {
                    'title': article.title,
                    'url': article.url
                })
                
                if result.success:
                    self.stdout.write(f"\nRe-processed: {len(result.content_blocks)} blocks")
                    
                    new_blocks_with_links = 0
                    new_total_links = 0
                    for i, block in enumerate(result.content_blocks):
                        if block.metadata and block.metadata.get('links'):
                            new_blocks_with_links += 1
                            links = block.metadata['links']
                            new_total_links += len(links)
                            self.stdout.write(f"\nNew Block {i} ({block.type}): {len(links)} links")
                            self.stdout.write(f"Content: {block.content[:100]}...")
                            for link in links[:2]:  # Show first 2 links
                                self.stdout.write(f"  - '{link['text']}' -> {link['href']}")
                    
                    self.stdout.write(f"\nNew processing: {new_blocks_with_links} blocks with links, {new_total_links} total links")
                    
                    if new_total_links == 0:
                        self.stdout.write(self.style.WARNING("\n🔍 Still no links. Let's check raw HTML for <a> tags..."))
                        from bs4 import BeautifulSoup
                        soup = BeautifulSoup(article.raw_html, 'html.parser')
                        all_links = soup.find_all('a', href=True)
                        
                        self.stdout.write(f"Total <a> tags with href in HTML: {len(all_links)}")
                        
                        if len(all_links) > 0:
                            self.stdout.write("\nFirst 5 links in HTML:")
                            for i, link in enumerate(all_links[:5]):
                                href = link.get('href', '')
                                text = link.get_text(strip=True)
                                self.stdout.write(f"  {i+1}. '{text}' -> {href}")
                                
                            # Check if these links are in paragraphs
                            p_links = []
                            for p in soup.find_all('p'):
                                links_in_p = p.find_all('a', href=True)
                                if links_in_p:
                                    p_links.extend(links_in_p)
                            
                            self.stdout.write(f"\nLinks inside <p> tags: {len(p_links)}")
                            if len(p_links) > 0:
                                self.stdout.write("First 3 paragraph links:")
                                for i, link in enumerate(p_links[:3]):
                                    href = link.get('href', '')
                                    text = link.get_text(strip=True)
                                    parent_text = link.parent.get_text(strip=True)[:100]
                                    self.stdout.write(f"  {i+1}. '{text}' -> {href}")
                                    self.stdout.write(f"     In paragraph: {parent_text}...")
                                    
                                # Debug: Let's see what happens when we process a specific paragraph
                                self.stdout.write(self.style.WARNING("\n🔍 Testing paragraph link extraction..."))
                                processor = AlgorithmicProcessor()
                                test_paragraph = p_links[0].parent  # First paragraph with links
                                
                                content, links_metadata = processor._extract_paragraph_with_links(test_paragraph)
                                self.stdout.write(f"Test paragraph content: {content[:150]}...")
                                self.stdout.write(f"Extracted links metadata: {links_metadata}")
                                
                            else:
                                self.stdout.write("No links found inside paragraph tags")
                        else:
                            self.stdout.write("No links found in HTML at all")
                else:
                    self.stdout.write(self.style.ERROR(f"Re-processing failed: {result.error_message}"))
            else:
                self.stdout.write(self.style.SUCCESS(f"✅ Found {total_links} links in {blocks_with_links} blocks"))
                
                # Even if we found some links, let's check if we're missing others
                self.stdout.write(self.style.WARNING("\n🔍 Let's check if there are more links we might be missing..."))
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(article.raw_html, 'html.parser')
                all_links = soup.find_all('a', href=True)
                
                self.stdout.write(f"Total <a> tags with href in HTML: {len(all_links)}")
                
                # Re-process to get the main content element that was selected
                processor = AlgorithmicProcessor()
                result = processor.process_content(article.raw_html, {
                    'title': article.title,
                    'url': article.url
                })
                
                if result.success:
                    # Find links specifically within the main content area
                    self.stdout.write(f"\n🎯 Focusing on links within the main content area...")
                    
                    # Get the main content element (we need to modify the processor to expose this)
                    # For now, let's analyze the content blocks to see which paragraphs have links
                    
                    content_area_links = []
                    for i, block in enumerate(result.content_blocks):
                        if block.type == 'paragraph':
                            # Re-process this specific paragraph to find links
                            # This is a simplified approach - we'd need the actual HTML element for a perfect match
                            paragraph_text = block.content
                            
                            # Look for links in the original HTML that match this paragraph text
                            for link in all_links:
                                link_text = link.get_text(strip=True)
                                if link_text in paragraph_text:
                                    # Check if the link's parent paragraph contains this text
                                    parent_p = link.find_parent('p')
                                    if parent_p:
                                        parent_text = parent_p.get_text(strip=True)
                                        # If substantial overlap, likely the same paragraph
                                        if len(parent_text) > 50 and paragraph_text[:100] in parent_text:
                                            content_area_links.append((link_text, link.get('href', ''), i, block.type))
                    
                    # Remove duplicates
                    seen_links = set()
                    unique_content_links = []
                    for link_text, href, block_idx, block_type in content_area_links:
                        link_key = (link_text, href)
                        if link_key not in seen_links:
                            seen_links.add(link_key)
                            unique_content_links.append((link_text, href, block_idx, block_type))
                    
                    self.stdout.write(f"Links found within main content area: {len(unique_content_links)}")
                    
                    if unique_content_links:
                        self.stdout.write(f"\nContent area links:")
                        for i, (text, href, block_idx, block_type) in enumerate(unique_content_links[:10]):  # Show first 10
                            link_type = "Twitter" if 'twitter.com' in href else "Relative" if href.startswith('/') else "External"
                            self.stdout.write(f"  {i+1}. '{text}' -> {href} ({link_type}, Block {block_idx})")
                    
                    # Compare with what was actually extracted
                    actually_extracted = 0
                    for block in result.content_blocks:
                        if block.metadata and block.metadata.get('links'):
                            actually_extracted += len(block.metadata['links'])
                    
                    self.stdout.write(f"\nComparison:")
                    self.stdout.write(f"  Links in main content area: {len(unique_content_links)}")
                    self.stdout.write(f"  Links actually extracted: {actually_extracted}")
                    
                    if len(unique_content_links) > actually_extracted:
                        missing_count = len(unique_content_links) - actually_extracted
                        self.stdout.write(self.style.WARNING(f"  Missing {missing_count} content links"))
                        
                        # Show which ones are missing
                        extracted_links = set()
                        for block in result.content_blocks:
                            if block.metadata and block.metadata.get('links'):
                                for link in block.metadata['links']:
                                    extracted_links.add((link['text'], link['href']))
                        
                        missing_links = []
                        for text, href, block_idx, block_type in unique_content_links:
                            if (text, href) not in extracted_links:
                                missing_links.append((text, href, block_idx))
                        
                        if missing_links:
                            self.stdout.write(f"\nMissing links:")
                            for text, href, block_idx in missing_links[:5]:  # Show first 5 missing
                                self.stdout.write(f"  - '{text}' -> {href} (from Block {block_idx})")
                    else:
                        self.stdout.write(self.style.SUCCESS(f"  ✅ All content links appear to be extracted!"))
                
                else:
                    self.stdout.write(self.style.ERROR(f"Failed to re-process article: {result.error_message}"))
        else:
            self.stdout.write(self.style.ERROR("No structured content available")) 