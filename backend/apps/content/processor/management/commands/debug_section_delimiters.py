"""
Debug command to analyze section delimiter detection.
"""
from django.core.management.base import BaseCommand
from apps.articles.models import Article
from apps.content.processor.algorithmic_processor import AlgorithmicProcessor
from bs4 import BeautifulSoup


class Command(BaseCommand):
    help = 'Debug section delimiter detection in algorithmic processor'
    
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
        
        self.stdout.write(f"🔍 Debugging section delimiters for Article {article_id}")
        self.stdout.write(f"Title: {article.title}")
        self.stdout.write("=" * 60)
        
        # Parse HTML
        soup = BeautifulSoup(article.raw_html, 'html.parser')
        
        # Initialize processor
        processor = AlgorithmicProcessor()
        processor._current_soup = soup
        processor._section_delimiters_cache = None
        
        # Find section delimiters
        delimiters = processor._find_section_delimiters()
        
        self.stdout.write(f"\n📍 Found {len(delimiters)} section delimiters:")
        for i, delimiter in enumerate(delimiters):
            self.stdout.write(f"{i+1}. {delimiter.name}: \"{delimiter.get_text(strip=True)}\"")
            
            # Show parent context
            parent_class = ' '.join(delimiter.parent.get('class', [])) if delimiter.parent else ''
            if parent_class:
                self.stdout.write(f"   Parent classes: {parent_class}")
        
        # Find main content elements
        self.stdout.write(f"\n📰 Main content elements:")
        headings = soup.find_all(['h1', 'h2', 'h3'])[:5]  # First few headings
        for i, heading in enumerate(headings):
            heading_text = heading.get_text(strip=True)
            self.stdout.write(f"{i+1}. {heading.name}: \"{heading_text[:80]}...\"")
            
            # Check if this would be filtered
            if delimiters:
                is_after = any(processor._element_comes_after(heading, delimiter) for delimiter in delimiters)
                self.stdout.write(f"   Would be filtered: {is_after}")
        
        # Test with paragraphs too
        self.stdout.write(f"\n📝 Sample paragraphs:")
        paragraphs = soup.find_all('p')[:5]  # First few paragraphs
        for i, para in enumerate(paragraphs):
            para_text = para.get_text(strip=True)
            if len(para_text) > 20:  # Only substantial paragraphs
                self.stdout.write(f"{i+1}. \"{para_text[:80]}...\"")
                
                # Check if this would be filtered
                if delimiters:
                    is_after = any(processor._element_comes_after(para, delimiter) for delimiter in delimiters)
                    self.stdout.write(f"   Would be filtered: {is_after}")
        
        self.stdout.write(f"\n✅ Debug complete") 