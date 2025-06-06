from django.core.management.base import BaseCommand
from apps.articles.models import Article
from apps.content.quality.html_preprocessor import HTMLPreprocessor
import re


class Command(BaseCommand):
    help = 'Test the image duplication fix for article 20894'

    def handle(self, *args, **options):
        self.stdout.write('=== IMAGE DUPLICATION FIX TEST ===')
        
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

            # Check for images
            img_matches = re.findall(r'<img[^>]*src=["\']([^"\']*)["\'][^>]*>', result.cleaned_html)
            self.stdout.write(f'\n🖼️  Images found: {len(img_matches)}')
            for i, src in enumerate(img_matches[:5]):
                self.stdout.write(f'  Img {i+1}: ...{src[-60:]}')

            # Check injection logging
            injection_logged = any('injected_nextjs_images' in elem for elem in result.removed_elements)
            enhanced_logged = any('enhanced_responsive_images' in elem for elem in result.removed_elements)
            
            self.stdout.write(f'\n📝 Next.js injection logged: {injection_logged}')
            self.stdout.write(f'📝 Responsive enhancement logged: {enhanced_logged}')
            self.stdout.write(f'📝 Removed elements: {result.removed_elements[:5]}')

            # Look for unique image URLs
            unique_images = set(img_matches)
            self.stdout.write(f'\n🎯 Unique image URLs: {len(unique_images)}')
            for i, url in enumerate(unique_images):
                self.stdout.write(f'  URL {i+1}: ...{url[-50:]}')
            
            # Expected URLs from user query
            expected_urls = [
                'AJGGJEUDDBH4NGSMTWDAGELQ6M.jpg',  # 1st image
                'VMTIIYA2HXRE2SJSJUDALETELQ.jpg',  # 2nd image 
                '4ZTUKFJ2VGEKMT22N2HWQY4WRY_size-normalized.jpg'  # 3rd image
            ]
            
            self.stdout.write(f'\n🔍 VALIDATION:')
            found_expected = []
            for expected in expected_urls:
                found = any(expected in url for url in img_matches)
                found_expected.append(found)
                status = '✅' if found else '❌'
                self.stdout.write(f'  {status} Expected image ending in "{expected}": {"FOUND" if found else "NOT FOUND"}')
            
            # Final assessment
            if len(unique_images) >= 3 and all(found_expected):
                self.stdout.write(self.style.SUCCESS(f'\n🎉 SUCCESS: Found {len(unique_images)} unique images with all expected URLs!'))
            elif len(unique_images) >= 2:
                self.stdout.write(self.style.WARNING(f'\n🟡 PARTIAL: Found {len(unique_images)} unique images (improvement from before)'))
            else:
                self.stdout.write(self.style.ERROR(f'\n❌ ISSUE: Only {len(unique_images)} unique images found'))
                
        except Article.DoesNotExist:
            self.stdout.write(self.style.ERROR('Article 20894 not found'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {e}')) 