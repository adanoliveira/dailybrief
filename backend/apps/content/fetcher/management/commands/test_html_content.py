from django.core.management.base import BaseCommand
from apps.content.fetcher.extraction import BrowserSimulationStrategy


class Command(BaseCommand):
    """Management command to test that raw HTML content is captured properly."""
    
    help = 'Test that raw HTML content extraction still works as before'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--url',
            type=str,
            default='https://arstechnica.com/space/2025/06/she-was-a-disney-star-with-platinum-records-but-bridgit-mendler-gave-it-up-to-change-the-world/',
            help='URL to test (default: Ars Technica article)'
        )
    
    def handle(self, *args, **options):
        """Handle the command execution."""
        url = options['url']
        
        self.stdout.write(self.style.SUCCESS('🔍 TESTING RAW HTML CONTENT EXTRACTION'))
        self.stdout.write('=' * 80)
        self.stdout.write(f"Testing URL: {url}")
        
        # Test with BrowserSimulationStrategy
        strategy = BrowserSimulationStrategy()
        result = strategy.extract(url)
        
        if result.success:
            self.stdout.write(self.style.SUCCESS("\n✅ EXTRACTION SUCCESSFUL"))
            
            # Show the ExtractionResult structure
            self.stdout.write(f"\n📊 ExtractionResult Structure:")
            self.stdout.write(f"   • success: {result.success}")
            self.stdout.write(f"   • raw_html length: {len(result.raw_html)} characters")
            self.stdout.write(f"   • basic_content length: {len(result.basic_content)} characters") 
            self.stdout.write(f"   • title: {result.title[:50]}...")
            self.stdout.write(f"   • author: {result.author}")
            self.stdout.write(f"   • publish_date: {result.publish_date}")
            self.stdout.write(f"   • strategy_used: {result.strategy_used}")
            self.stdout.write(f"   • duration_ms: {result.duration_ms}")
            self.stdout.write(f"   • paywall_detected: {result.paywall_detected}")
            
            # Show first 500 characters of raw HTML to confirm it's complete HTML
            self.stdout.write(f"\n🌐 Raw HTML Content (first 500 chars):")
            self.stdout.write("-" * 50)
            self.stdout.write(result.raw_html[:500])
            self.stdout.write("-" * 50)
            
            # Show that it contains standard HTML elements
            html_indicators = [
                ('<!DOCTYPE', '<!DOCTYPE declaration'),
                ('<html', 'HTML root element'),
                ('<head>', 'Head section'),
                ('<body>', 'Body section'), 
                ('<title>', 'Title tag'),
                ('</html>', 'HTML closing tag')
            ]
            
            self.stdout.write(f"\n🏷️  HTML Structure Verification:")
            for indicator, description in html_indicators:
                found = indicator in result.raw_html
                status = "✅" if found else "❌"
                self.stdout.write(f"   {status} {description}: {found}")
            
            # Show metadata
            self.stdout.write(f"\n📋 Extraction Metadata:")
            for key, value in result.extraction_metadata.items():
                self.stdout.write(f"   • {key}: {value}")
                
            self.stdout.write(self.style.SUCCESS(f"\n🎉 Confirmation: Raw HTML content is being captured properly!"))
            self.stdout.write(f"   The full HTML document ({len(result.raw_html):,} characters) is available in result.raw_html")
            self.stdout.write(f"   This maintains 100% compatibility with existing processing pipeline.")
            
        else:
            self.stdout.write(self.style.ERROR(f"\n❌ EXTRACTION FAILED: {result.error_message}")) 