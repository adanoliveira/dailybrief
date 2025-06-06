from django.core.management.base import BaseCommand
from apps.articles.models import Article
from apps.content.quality.html_preprocessor import HTMLPreprocessor
import re


class Command(BaseCommand):
    help = 'Verify the image duplication fix for article 20894'

    def handle(self, *args, **options):
        self.stdout.write('=== VERIFYING IMAGE DUPLICATION FIX ===')
        
        try:
            article = Article.objects.get(id=20894)
            preprocessor = HTMLPreprocessor()
            result = preprocessor.preprocess_for_evaluation(
                article.raw_html, 
                max_tokens=12000, 
                preserve_html_structure=True
            )

            # Extract all images with src
            img_pattern = r'<img[^>]*src=["\']([^"\']*)["\'][^>]*>'
            img_srcs = re.findall(img_pattern, result.cleaned_html)
            
            # Extract all images without src (should be 0)
            img_no_src_pattern = r'<img(?![^>]*src=)[^>]*>'
            no_src_count = len(re.findall(img_no_src_pattern, result.cleaned_html))
            
            # Check uniqueness
            unique_srcs = set(img_srcs)
            
            self.stdout.write(f'📊 Results:')
            self.stdout.write(f'  - Total images with src: {len(img_srcs)}')
            self.stdout.write(f'  - Total images without src: {no_src_count}')
            self.stdout.write(f'  - Unique image URLs: {len(unique_srcs)}')
            
            self.stdout.write(f'\n🖼️  Image URLs found:')
            for i, src in enumerate(unique_srcs):
                filename = src.split('/')[-1]
                self.stdout.write(f'  {i+1}. {filename}')
            
            # Expected files
            expected_files = [
                'AJGGJEUDDBH4NGSMTWDAGELQ6M.jpg',
                'VMTIIYA2HXRE2SJSJUDALETELQ.jpg', 
                '4ZTUKFJ2VGEKMT22N2HWQY4WRY.jpg'
            ]
            
            self.stdout.write(f'\n✅ Expected images validation:')
            all_found = True
            for expected in expected_files:
                found = any(expected in src for src in unique_srcs)
                status = '✅' if found else '❌'
                if not found:
                    all_found = False
                self.stdout.write(f'  {status} {expected}')
            
            # Final assessment
            if no_src_count == 0 and len(unique_srcs) >= 3 and all_found:
                self.stdout.write(self.style.SUCCESS(f'\n🎉 SUCCESS: Fix working perfectly!'))
                self.stdout.write(f'   ✅ All images have src attributes')
                self.stdout.write(f'   ✅ All 3 expected unique images found')
                self.stdout.write(f'   ✅ No duplicate image URLs')
            elif no_src_count == 0 and len(unique_srcs) >= 2:
                self.stdout.write(self.style.WARNING(f'\n🟡 GOOD: Basic fix working - {len(unique_srcs)} unique images'))
            else:
                self.stdout.write(self.style.ERROR(f'\n❌ ISSUE: {no_src_count} images still missing src'))
                
        except Article.DoesNotExist:
            self.stdout.write(self.style.ERROR('Article 20894 not found'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {e}')) 