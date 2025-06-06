from django.core.management.base import BaseCommand
from apps.content.quality.html_preprocessor import HTMLPreprocessor
from bs4 import BeautifulSoup


class Command(BaseCommand):
    help = 'Test the improved image filtering logic (AND vs OR)'

    def handle(self, *args, **options):
        self.stdout.write('=== TESTING IMPROVED IMAGE FILTERING ===')
        
        preprocessor = HTMLPreprocessor()
        
        # Test cases: [width, height, should_be_kept, description]
        test_cases = [
            (800, 150, True, "Banner image (wide and adequate height)"),
            (150, 600, True, "Vertical banner (adequate width and tall)"),
            (150, 150, True, "Medium square image (both dimensions adequate)"),
            (100, 100, True, "Exactly 100x100 (boundary case)"),
            (200, 200, True, "Large square image"),
            (99, 200, False, "Thin vertical line (width too small)"),
            (200, 99, False, "Thin horizontal line (height too small)"),
            (100, 250, True, "Narrow but tall (exactly at width threshold)"),
            (250, 100, True, "Wide but short (exactly at height threshold)"),
            (50, 800, False, "Very thin vertical separator"),
            (800, 50, False, "Very thin horizontal separator"),
            (99, 99, False, "Small image (both dimensions under threshold)"),
        ]
        
        self.stdout.write(f'\n🧪 Testing {len(test_cases)} image filtering scenarios:\n')
        
        passed = 0
        failed = 0
        
        for width, height, should_be_kept, description in test_cases:
            # Create a mock image element
            html = f'<img src="test.jpg" alt="test image" width="{width}" height="{height}">'
            soup = BeautifulSoup(html, 'html.parser')
            img = soup.find('img')
            
            # Test the filtering logic
            is_small = preprocessor._is_small_image(img)
            is_kept = not is_small
            
            # Check result
            status = "✅ PASS" if is_kept == should_be_kept else "❌ FAIL"
            action = "kept" if is_kept else "filtered"
            expected_action = "kept" if should_be_kept else "filtered"
            
            self.stdout.write(f'  {status} {width}x{height}: {description}')
            self.stdout.write(f'       Expected: {expected_action}, Got: {action}')
            
            if is_kept == should_be_kept:
                passed += 1
            else:
                failed += 1
            
            self.stdout.write("")  # Empty line for readability
        
        # Summary
        total = passed + failed
        self.stdout.write(f'📊 Results: {passed}/{total} tests passed')
        
        if failed == 0:
            self.stdout.write(self.style.SUCCESS('🎉 All tests passed! Image filtering with 100px OR logic working perfectly.'))
            self.stdout.write('   ✅ Meaningful content images (≥100px both dimensions) are preserved')
            self.stdout.write('   ✅ Thin separators and tiny images (<100px either dimension) are filtered')
        else:
            self.stdout.write(self.style.ERROR(f'❌ {failed} tests failed. Image filtering needs adjustment.'))
            
        # Test specific edge cases
        self.stdout.write(f'\n🔍 Testing edge cases:')
        
        edge_cases = [
            ('<img src="test.jpg" alt="" width="40" height="40">', False, "Generic alt + very small dims"),
            ('<img src="test.jpg" alt="" width="300" height="40">', False, "Generic alt + thin separator"),
            ('<img src="test.jpg" alt="banner" width="40" height="40">', False, "Descriptive alt + very small dims"),
            ('<img src="test.jpg" alt="" width="120" height="120">', True, "Generic alt + adequate dims"),
        ]
        
        for html, should_be_kept, description in edge_cases:
            soup = BeautifulSoup(html, 'html.parser')
            img = soup.find('img')
            is_kept = not preprocessor._is_small_image(img)
            
            status = "✅ PASS" if is_kept == should_be_kept else "❌ FAIL"
            action = "kept" if is_kept else "filtered"
            expected_action = "kept" if should_be_kept else "filtered"
            
            self.stdout.write(f'  {status} {description}: Expected {expected_action}, Got {action}') 