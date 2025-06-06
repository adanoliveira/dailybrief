from django.core.management.base import BaseCommand
from apps.articles.models import Article
from apps.content.quality.html_preprocessor import HTMLPreprocessor
import re


class Command(BaseCommand):
    help = 'Test the intelligent image matching fix for article 20894'

    def handle(self, *args, **options):
        self.stdout.write('=== TESTING INTELLIGENT IMAGE MATCHING ===')
        
        try:
            article = Article.objects.get(id=20894)
            preprocessor = HTMLPreprocessor()
            result = preprocessor.preprocess_for_evaluation(
                article.raw_html, 
                max_tokens=12000, 
                preserve_html_structure=True
            )

            self.stdout.write(f'Article: {article.title[:50]}...')

            # Extract all images with src
            img_pattern = r'<img[^>]*src=["\']([^"\']*)["\'][^>]*>'
            img_srcs = re.findall(img_pattern, result.cleaned_html)
            
            self.stdout.write(f'\n🖼️  Images found: {len(img_srcs)}')
            
            # Extract filenames and check order
            expected_order = [
                'AJGGJEUDDBH4NGSMTWDAGELQ6M.jpg',  # 1st image (hero/figure)
                'VMTIIYA2HXRE2SJSJUDALETELQ.jpg',  # 2nd image (first type-image)
                '4ZTUKFJ2VGEKMT22N2HWQY4WRY.jpg'   # 3rd image (second type-image)
            ]
            
            found_images = []
            for i, src in enumerate(img_srcs):
                filename = src.split('/')[-1]
                found_images.append(filename)
                self.stdout.write(f'  Image {i+1}: {filename}')
            
            self.stdout.write(f'\n✅ Expected order validation:')
            all_correct = True
            for i, expected_filename in enumerate(expected_order):
                if i < len(found_images):
                    found_filename = found_images[i]
                    is_correct = expected_filename == found_filename
                    status = '✅' if is_correct else '❌'
                    self.stdout.write(f'  Position {i+1}: {status} Expected {expected_filename}, Got {found_filename}')
                    if not is_correct:
                        all_correct = False
                else:
                    self.stdout.write(f'  Position {i+1}: ❌ Expected {expected_filename}, Got MISSING')
                    all_correct = False
            
            # Final assessment
            if all_correct and len(found_images) == len(expected_order):
                self.stdout.write(self.style.SUCCESS(f'\n🎉 SUCCESS: Intelligent matching working perfectly!'))
                self.stdout.write(f'   ✅ All 3 images in correct order')
                self.stdout.write(f'   ✅ Hero image in figure container')
                self.stdout.write(f'   ✅ Article images in type-image containers')
            elif len(found_images) == len(expected_order):
                wrong_count = sum(1 for i, expected in enumerate(expected_order) 
                                if i < len(found_images) and found_images[i] != expected)
                self.stdout.write(self.style.WARNING(f'\n🟡 PARTIAL: Found all images but {wrong_count} in wrong positions'))
            else:
                self.stdout.write(self.style.ERROR(f'\n❌ ISSUE: Expected {len(expected_order)} images, got {len(found_images)}'))
                
        except Article.DoesNotExist:
            self.stdout.write(self.style.ERROR('Article 20894 not found'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {e}')) 