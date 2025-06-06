from django.core.management.base import BaseCommand
from apps.articles.models import Article
from apps.content.quality.html_preprocessor import HTMLPreprocessor
import re


class Command(BaseCommand):
    help = 'Test the enhanced image injection fix for article 20894'

    def handle(self, *args, **options):
        self.stdout.write('=== ENHANCED IMAGE INJECTION TEST ===')
        
        try:
            article = Article.objects.get(id=20894)
            preprocessor = HTMLPreprocessor()
            result = preprocessor.preprocess_for_evaluation(
                article.raw_html, 
                max_tokens=12000, 
                preserve_html_structure=True
            )

            self.stdout.write(f'Article: {article.title[:50]}...')
            self.stdout.write(f'Processed size: {len(result.cleaned_html):,} chars')

            # Check for images with details
            img_pattern = r'<img[^>]*?(?:src=["\']([^"\']*)["\'])?[^>]*?(?:alt=["\']([^"\']*)["\'])?[^>]*?>'
            img_matches = re.findall(img_pattern, result.cleaned_html)
            
            self.stdout.write(f'\n🖼️  Image analysis:')
            
            images_with_src = []
            images_without_src = []
            
            for i, (src, alt) in enumerate(img_matches):
                if src:
                    images_with_src.append((src, alt))
                    self.stdout.write(f'  Image {i+1}: HAS SRC - ...{src[-50:]}')
                    self.stdout.write(f'            Alt: {alt[:30]}...')
                else:
                    images_without_src.append(alt)
                    self.stdout.write(f'  Image {i+1}: NO SRC - Alt: {alt[:30]}...')
            
            self.stdout.write(f'\n📊 Summary:')
            self.stdout.write(f'  - Images with src: {len(images_with_src)}')
            self.stdout.write(f'  - Images without src: {len(images_without_src)}')
            
            # Check injection and enhancement logging
            injection_logged = any('injected_nextjs_images' in elem for elem in result.removed_elements)
            enhanced_logged = any('enhanced_responsive_images' in elem for elem in result.removed_elements)
            
            self.stdout.write(f'\n📝 Processing logs:')
            self.stdout.write(f'  - Next.js injection: {injection_logged}')
            self.stdout.write(f'  - Responsive enhancement: {enhanced_logged}')
            self.stdout.write(f'  - Removed elements: {result.removed_elements[:5]}')

            # Check for unique URLs
            unique_srcs = set(src for src, _ in images_with_src if src)
            self.stdout.write(f'\n🎯 Unique image URLs: {len(unique_srcs)}')
            for i, url in enumerate(unique_srcs):
                self.stdout.write(f'  URL {i+1}: ...{url[-50:]}')
            
            # Expected URLs validation
            expected_urls = [
                'AJGGJEUDDBH4NGSMTWDAGELQ6M.jpg',  # 1st image
                'VMTIIYA2HXRE2SJSJUDALETELQ.jpg',  # 2nd image 
                '4ZTUKFJ2VGEKMT22N2HWQY4WRY_size-normalized.jpg'  # 3rd image
            ]
            
            self.stdout.write(f'\n🔍 Expected image validation:')
            found_expected = []
            for expected in expected_urls:
                found = any(expected in url for url in unique_srcs)
                found_expected.append(found)
                status = '✅' if found else '❌'
                self.stdout.write(f'  {status} {expected}: {"FOUND" if found else "NOT FOUND"}')
            
            # Final assessment
            success_criteria = [
                len(images_without_src) == 0,  # All images should have src
                len(unique_srcs) >= 2,         # At least 2 unique images
                injection_logged,              # Next.js injection should work
            ]
            
            if all(success_criteria):
                self.stdout.write(self.style.SUCCESS(f'\n🎉 SUCCESS: Enhanced fix working perfectly!'))
            elif len(images_without_src) == 0 and len(unique_srcs) >= 2:
                self.stdout.write(self.style.WARNING(f'\n🟡 GOOD: All images have src, found {len(unique_srcs)} unique URLs'))
            else:
                self.stdout.write(self.style.ERROR(f'\n❌ ISSUE: Still have problems - {len(images_without_src)} images missing src'))
                
        except Article.DoesNotExist:
            self.stdout.write(self.style.ERROR('Article 20894 not found'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {e}')) 