"""
Django management command to search for specific patterns in raw HTML content.
"""

from django.core.management.base import BaseCommand
from apps.articles.models import Article


class Command(BaseCommand):
    help = 'Search for specific patterns in raw HTML content'

    def add_arguments(self, parser):
        parser.add_argument(
            '--article-id',
            type=int,
            help='Specific article ID to search',
        )
        parser.add_argument(
            '--search',
            type=str,
            help='Search term to look for',
            default='twitter'
        )

    def handle(self, *args, **options):
        """Search for patterns in article HTML."""
        
        if options['article_id']:
            try:
                article = Article.objects.get(id=options['article_id'])
            except Article.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Article with ID {options['article_id']} not found"))
                return
        else:
            # Get the NHL article
            article = Article.objects.filter(
                url="https://www.nhl.com/news/united-states-wins-gold-at-2025-iihf-world-championship"
            ).first()
            
            if not article:
                self.stdout.write(self.style.ERROR("NHL article not found"))
                return

        search_term = options['search'].lower()
        self.stdout.write(f"\nSearching for '{search_term}' in article HTML...")
        self.stdout.write(f"Article: {article.title[:80]}...")

        html = article.raw_html
        if not html:
            self.stdout.write(self.style.ERROR("No raw HTML found"))
            return

        # Search for the term (case-insensitive)
        lines = html.split('\n')
        matches = []
        
        for i, line in enumerate(lines, 1):
            if search_term in line.lower():
                matches.append((i, line.strip()))

        if matches:
            self.stdout.write(self.style.SUCCESS(f"\n✅ Found {len(matches)} matches:"))
            
            for line_num, line in matches[:10]:  # Show first 10 matches
                # Truncate very long lines
                if len(line) > 200:
                    line = line[:200] + "..."
                self.stdout.write(f"  Line {line_num}: {line}")
                
            if len(matches) > 10:
                self.stdout.write(f"  ... and {len(matches) - 10} more matches")
        else:
            self.stdout.write(self.style.WARNING(f"\n⚠️ No matches found for '{search_term}'"))
            
            # Try related terms
            related_terms = ['tweet', 'embed', 'oembed', 'iframe', 'platform.twitter']
            for term in related_terms:
                count = html.lower().count(term)
                if count > 0:
                    self.stdout.write(f"  Found {count} occurrence(s) of '{term}'")

        # Show HTML size and structure info
        self.stdout.write(f"\n📊 HTML stats:")
        self.stdout.write(f"  Total size: {len(html):,} characters")
        self.stdout.write(f"  Total lines: {len(lines):,}")
        
        # Count common tags
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        
        div_count = len(soup.find_all('div'))
        iframe_count = len(soup.find_all('iframe'))
        script_count = len(soup.find_all('script'))
        
        self.stdout.write(f"  Div tags: {div_count}")
        self.stdout.write(f"  Iframe tags: {iframe_count}")
        self.stdout.write(f"  Script tags: {script_count}")
        
        # Look for any iframes specifically
        if iframe_count > 0:
            self.stdout.write(f"\n🔍 Found {iframe_count} iframe(s):")
            iframes = soup.find_all('iframe')
            for i, iframe in enumerate(iframes[:5], 1):
                src = iframe.get('src', 'No src')
                self.stdout.write(f"  Iframe #{i}: {src[:100]}...")
        
        self.stdout.write(f"\nSearch completed.")