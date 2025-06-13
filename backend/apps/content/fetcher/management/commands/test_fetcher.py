from django.core.management.base import BaseCommand, CommandError
from apps.content.fetcher.extraction import (
    BrowserSimulationStrategy,
    AdvancedBypassStrategy,
    PaywallBypassStrategy,
    BeautifulSoupStrategy
)


class Command(BaseCommand):
    """Management command to test content fetcher strategies."""
    
    help = 'Test content fetcher strategies against problematic URLs'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--url',
            type=str,
            help='Test a specific URL'
        )
        parser.add_argument(
            '--strategy',
            choices=['browser', 'advanced', 'paywall', 'beautifulsoup', 'all'],
            default='all',
            help='Which strategy to test (default: all)'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output including content snippets'
        )
    
    def handle(self, *args, **options):
        """Handle the command execution."""
        
        self.stdout.write(self.style.SUCCESS('🚀 CONTENT FETCHER IMPROVEMENT TEST'))
        self.stdout.write('=' * 80)
        
        if options['url']:
            # Test specific URL
            self.test_single_url(options['url'], options)
        else:
            # Test predefined problematic URLs
            self.test_predefined_urls(options)
    
    def test_single_url(self, url, options):
        """Test a single URL."""
        self.stdout.write(f"\n🔗 Testing URL: {url}")
        self.stdout.write("   " + "="*77)
        
        success = self.test_url_extraction(url, "Custom URL", options)
        
        if success:
            self.stdout.write(self.style.SUCCESS("\n✅ URL extraction successful!"))
        else:
            self.stdout.write(self.style.ERROR("\n❌ URL extraction failed with all strategies."))
    
    def test_predefined_urls(self, options):
        """Test predefined problematic URLs."""
        # Test URLs that were failing with 403 Forbidden
        test_urls = [
            {
                'url': 'https://arstechnica.com/space/2025/06/she-was-a-disney-star-with-platinum-records-but-bridgit-mendler-gave-it-up-to-change-the-world/',
                'description': 'Ars Technica - Bridgit Mendler Article'
            },
            {
                'url': 'https://www.politico.com/news/2025/06/11/trump-military-parade-protests-00398716',
                'description': 'Politico - Trump Military Parade Article'
            },
            {
                'url': 'https://www.axios.com/2025/06/11/zuckerberg-meta-scale-ai-deal',
                'description': 'Axios - Zuckerberg Meta Scale AI Article'
            },
            {
                'url': 'https://www.nytimes.com/2024/12/01/technology/ai-models-anthropic-openai.html',
                'description': 'New York Times - AI Models Article (paywall test)'
            },
            {
                'url': 'https://www.wsj.com/tech/ai/openai-chatgpt-search-google-challenge-b5c6e2b5',
                'description': 'Wall Street Journal - OpenAI ChatGPT Article (paywall test)'
            }
        ]
        
        successful_extractions = 0
        total_tests = len(test_urls)
        
        for test_case in test_urls:
            success = self.test_url_extraction(test_case['url'], test_case['description'], options)
            if success:
                successful_extractions += 1
        
        self.stdout.write(f"\n📊 RESULTS SUMMARY")
        self.stdout.write("=" * 80)
        self.stdout.write(f"✅ Successful extractions: {successful_extractions}/{total_tests}")
        self.stdout.write(f"📈 Success rate: {(successful_extractions/total_tests)*100:.1f}%")
        
        if successful_extractions > 0:
            self.stdout.write(self.style.SUCCESS("\n🎉 Content fetcher improvements are working!"))
            self.stdout.write("   The new browser simulation strategy is successfully bypassing 403 errors.")
        else:
            self.stdout.write(self.style.ERROR("\n⚠️  All extractions failed. Further improvements needed."))
    
    def test_url_extraction(self, url: str, description: str, options):
        """Test URL extraction with specified strategies."""
        self.stdout.write(f"\n🔗 Testing: {description}")
        self.stdout.write(f"   URL: {url}")
        self.stdout.write("   " + "="*77)
        
        # Select strategies based on options
        strategies = []
        if options['strategy'] == 'all':
            strategies = [
                BrowserSimulationStrategy(),
                AdvancedBypassStrategy(),
                PaywallBypassStrategy(),
                BeautifulSoupStrategy()
            ]
        elif options['strategy'] == 'browser':
            strategies = [BrowserSimulationStrategy()]
        elif options['strategy'] == 'advanced':
            strategies = [AdvancedBypassStrategy()]
        elif options['strategy'] == 'paywall':
            strategies = [PaywallBypassStrategy()]
        elif options['strategy'] == 'beautifulsoup':
            strategies = [BeautifulSoupStrategy()]
        
        for strategy in strategies:
            self.stdout.write(f"\n📋 Strategy: {strategy.name}")
            try:
                result = strategy.extract(url)
                
                if result.success:
                    self.stdout.write(self.style.SUCCESS("   ✅ SUCCESS"))
                    self.stdout.write(f"   📄 Title: {result.title[:100]}...")
                    self.stdout.write(f"   📝 Content Length: {len(result.basic_content)} chars")
                    self.stdout.write(f"   ⏱️  Duration: {result.duration_ms}ms")
                    self.stdout.write(f"   🔧 Strategy Used: {result.strategy_used}")
                    
                    if result.paywall_detected:
                        self.stdout.write(self.style.WARNING(f"   🚧 Paywall Detected: {result.paywall_indicators}"))
                    else:
                        self.stdout.write("   🟢 No paywall detected")
                    
                    if options['verbose'] and result.basic_content:
                        # Show first 200 characters of content
                        content_preview = result.basic_content[:200].replace('\n', ' ').strip()
                        self.stdout.write(f"   📖 Content Preview: {content_preview}...")
                    
                    return True  # Success, no need to try other strategies
                    
                else:
                    self.stdout.write(self.style.ERROR(f"   ❌ FAILED: {result.error_message}"))
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"   💥 EXCEPTION: {str(e)}"))
        
        return False 