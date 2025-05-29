"""
Debug command to analyze image caption extraction.
"""
from django.core.management.base import BaseCommand
from apps.articles.models import Article
from bs4 import BeautifulSoup
import re


class Command(BaseCommand):
    help = 'Debug image caption extraction to match Safari Reader Mode'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--article-id',
            type=int,
            required=True,
            help='Article ID to debug'
        )
    
    def handle(self, *args, **options):
        article_id = options['article_id']
        
        try:
            article = Article.objects.get(id=article_id)
        except Article.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Article {article_id} not found')
            )
            return
        
        if not article.raw_html:
            self.stdout.write(
                self.style.ERROR(f'Article {article_id} has no raw HTML')
            )
            return
        
        self.stdout.write(f"🖼️ Debugging image captions for Article {article_id}")
        self.stdout.write(f"Title: {article.title}")
        self.stdout.write("=" * 70)
        
        # Parse HTML
        soup = BeautifulSoup(article.raw_html, 'html.parser')
        
        # Find figures
        figures = soup.find_all('figure')
        self.stdout.write(f"\n📍 Found {len(figures)} figure elements")
        
        for i, figure in enumerate(figures[:3]):  # Analyze first 3 figures
            self.stdout.write(f"\n🖼️ Figure {i+1}:")
            self.stdout.write("-" * 40)
            
            # Show HTML structure
            self.stdout.write(f"HTML structure:")
            html_snippet = str(figure)[:300] + "..." if len(str(figure)) > 300 else str(figure)
            self.stdout.write(html_snippet)
            
            # Get image
            img = figure.find('img')
            if img:
                img_alt = img.get('alt', '')
                self.stdout.write(f"\nIMG alt attribute: \"{img_alt[:100]}...\"")
            
            # Get figcaption and analyze its structure
            figcaption = figure.find('figcaption')
            if figcaption:
                caption_html = str(figcaption)
                caption_text = figcaption.get_text(strip=True)
                self.stdout.write(f"\nFIGCAPTION HTML: {caption_html[:200]}...")
                self.stdout.write(f"FIGCAPTION text: \"{caption_text[:150]}...\"")
                
                # Analyze child elements for visibility
                self.stdout.write(f"\nFIGCAPTION child elements:")
                for j, child in enumerate(figcaption.descendants):
                    if child.name:  # Is a tag
                        child_text = child.get_text(strip=True)
                        if child_text:
                            self.stdout.write(f"  {j+1}. <{child.name}>: \"{child_text[:100]}...\"")
                            # Check for visibility indicators
                            style = child.get('style', '')
                            classes = ' '.join(child.get('class', []))
                            if 'display:none' in style or 'visibility:hidden' in style:
                                self.stdout.write(f"     ❌ HIDDEN by style: {style}")
                            if any(hidden_class in classes.lower() for hidden_class in ['hidden', 'sr-only', 'screen-reader']):
                                self.stdout.write(f"     ❌ HIDDEN by class: {classes}")
                
                # Try Safari-like visible caption extraction
                visible_caption = self._extract_visible_caption(figcaption)
                if visible_caption:
                    self.stdout.write(f"\n🎯 Safari-style visible caption: \"{visible_caption}\"")
            
            # Check for other caption sources
            next_sibling = figure.find_next_sibling()
            if next_sibling and next_sibling.name == 'p':
                sibling_text = next_sibling.get_text(strip=True)
                if len(sibling_text) < 200 and any(pattern in sibling_text.lower() for pattern in ['photo', '©', 'credit', 'image']):
                    self.stdout.write(f"\nNext paragraph caption: \"{sibling_text[:100]}...\"")
        
        # Analyze current processed blocks
        self.stdout.write(f"\n📋 Current processed figure blocks:")
        figure_blocks = [block for block in article.content_blocks if block.get('type') == 'figure']
        for i, block in enumerate(figure_blocks[:2]):
            self.stdout.write(f"\nProcessed Figure {i+1}:")
            self.stdout.write(f"Content: \"{block['content'][:100]}...\"")
            metadata = block.get('metadata', {})
            self.stdout.write(f"Caption: \"{metadata.get('caption', '')[:100]}...\"")
        
        self.stdout.write(f"\n✅ Debug complete")
    
    def _extract_visible_caption(self, figcaption) -> str:
        """
        Extract visible caption like Safari Reader Mode.
        Focus on what's actually visible to users, not hidden metadata.
        """
        if not figcaption:
            return ""
        
        # Method 1: Look for visible child elements with meaningful content
        visible_parts = []
        
        # Check direct text content
        for content in figcaption.contents:
            if hasattr(content, 'strip'):  # Text node
                text = content.strip()
                if text and len(text) > 3:
                    visible_parts.append(text)
            elif hasattr(content, 'name'):  # Element node
                # Check if element is likely visible
                if self._is_likely_visible(content):
                    text = content.get_text(strip=True)
                    if text and len(text) > 3:
                        visible_parts.append(text)
        
        if visible_parts:
            combined = ' '.join(visible_parts).strip()
            # Clean up excessive whitespace
            combined = re.sub(r'\s+', ' ', combined)
            return combined
        
        # Method 2: Fallback to full figcaption text but try to clean it
        full_text = figcaption.get_text(strip=True)
        
        # If text is very long, try to extract the essential parts
        if len(full_text) > 200:
            # Look for photo credit patterns at the end
            photo_credit_match = re.search(r'\(Photo by [^)]+\)\([^)]+\)$', full_text)
            if photo_credit_match:
                return photo_credit_match.group(0)
            
            # Look for copyright at the end
            copyright_match = re.search(r'©[^.]*(?:AP Images?|Reuters|Getty|Sipa|AFP)[^.]*$', full_text)
            if copyright_match:
                return copyright_match.group(0)
        
        return full_text
    
    def _is_likely_visible(self, element) -> bool:
        """
        Determine if an element is likely visible to users.
        Based on Safari Reader Mode visibility logic.
        """
        if not element or not hasattr(element, 'name'):
            return True
        
        # Check style attribute for hiding
        style = element.get('style', '').lower()
        if any(hidden_style in style for hidden_style in [
            'display:none', 'display: none',
            'visibility:hidden', 'visibility: hidden',
            'opacity:0', 'opacity: 0'
        ]):
            return False
        
        # Check classes for hiding
        classes = ' '.join(element.get('class', [])).lower()
        if any(hidden_class in classes for hidden_class in [
            'hidden', 'sr-only', 'screen-reader-only', 'visually-hidden',
            'invisible', 'hide', 'off-screen'
        ]):
            return False
        
        # Check for certain semantic elements that are usually visible
        if element.name in ['span', 'div', 'p', 'em', 'strong', 'b', 'i']:
            return True
        
        # Default to visible if no hiding indicators found
        return True 