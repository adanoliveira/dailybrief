from django.core.management.base import BaseCommand
from apps.articles.models import Article
from apps.content.quality.html_preprocessor import HTMLPreprocessor
from bs4 import BeautifulSoup
import re


class Command(BaseCommand):
    help = 'Debug image injection step by step for article 20894'

    def handle(self, *args, **options):
        self.stdout.write('=== STEP-BY-STEP INJECTION DEBUG ===')
        
        try:
            article = Article.objects.get(id=20894)
            preprocessor = HTMLPreprocessor()
            
            self.stdout.write(f'Article: {article.title[:50]}...')
            
            # Step 1: Extract Next.js images
            soup = BeautifulSoup(article.raw_html, 'html.parser')
            nextjs_images = preprocessor._extract_nextjs_images(soup)
            
            self.stdout.write(f'\n📦 STEP 1: Next.js Image Extraction')
            self.stdout.write(f'  Extracted {len(nextjs_images)} images from __NEXT_DATA__:')
            for i, img in enumerate(nextjs_images):
                self.stdout.write(f'    Image {i+1}: ...{img["url"][-50:]}')
                self.stdout.write(f'             Alt: {img["alt_text"][:30]}...')
                self.stdout.write(f'             Size: {img["width"]}x{img["height"]}')
            
            # Step 2: Find image containers in raw HTML
            self.stdout.write(f'\n🔍 STEP 2: Container Discovery')
            
            # Find type-image containers
            type_image_divs = soup.find_all('div', class_=lambda x: x and 'type-image' in x)
            self.stdout.write(f'  Found {len(type_image_divs)} type-image containers:')
            for i, container in enumerate(type_image_divs):
                existing_img = container.find('img')
                src_status = 'HAS SRC' if existing_img and existing_img.get('src') else 'NO SRC'
                self.stdout.write(f'    Container {i+1}: {src_status}')
            
            # Find figure elements  
            figures = soup.find_all('figure')
            figures_with_missing_src = []
            for figure in figures:
                img_in_figure = figure.find('img')
                if img_in_figure and not img_in_figure.get('src'):
                    figures_with_missing_src.append(figure)
            
            self.stdout.write(f'  Found {len(figures)} total figures, {len(figures_with_missing_src)} with missing src:')
            for i, figure in enumerate(figures_with_missing_src):
                img = figure.find('img')
                alt = img.get('alt', 'NO_ALT')[:30] if img else 'NO_IMG'
                self.stdout.write(f'    Figure {i+1}: Alt={alt}...')
            
            # Step 3: Test injection manually
            self.stdout.write(f'\n💉 STEP 3: Manual Injection Test')
            soup_copy = BeautifulSoup(article.raw_html, 'html.parser')
            injected_count = preprocessor._inject_missing_images(soup_copy, nextjs_images)
            self.stdout.write(f'  Injection returned: {injected_count} images injected')
            
            # Check what happened after injection
            self.stdout.write(f'\n📋 STEP 4: Post-Injection Analysis')
            
            # Check figures after injection
            figures_after = soup_copy.find_all('figure')
            self.stdout.write(f'  Figures after injection:')
            for i, figure in enumerate(figures_after):
                img = figure.find('img')
                if img:
                    src_status = 'HAS SRC' if img.get('src') else 'NO SRC'
                    src_value = img.get('src', 'NONE')[-50:] if img.get('src') else 'NONE'
                    self.stdout.write(f'    Figure {i+1}: {src_status} - ...{src_value}')
            
            # Check type-image containers after injection  
            type_image_divs_after = soup_copy.find_all('div', class_=lambda x: x and 'type-image' in x)
            self.stdout.write(f'  Type-image containers after injection:')
            for i, container in enumerate(type_image_divs_after):
                img = container.find('img')
                if img:
                    src_status = 'HAS SRC' if img.get('src') else 'NO SRC'
                    src_value = img.get('src', 'NONE')[-50:] if img.get('src') else 'NONE'
                    self.stdout.write(f'    Container {i+1}: {src_status} - ...{src_value}')
            
            # Step 5: Full processing test
            self.stdout.write(f'\n🔧 STEP 5: Full Processing Pipeline')
            result = preprocessor.preprocess_for_evaluation(
                article.raw_html, 
                max_tokens=12000, 
                preserve_html_structure=True
            )
            
            # Check final images
            img_pattern = r'<img[^>]*src=["\']([^"\']*)["\'][^>]*>'
            final_images = re.findall(img_pattern, result.cleaned_html)
            
            self.stdout.write(f'  Final processed images with src: {len(final_images)}')
            for i, src in enumerate(final_images):
                self.stdout.write(f'    Final {i+1}: ...{src[-50:]}')
            
            # Check if any images without src remain
            img_no_src_pattern = r'<img(?![^>]*src=)[^>]*>'
            no_src_images = re.findall(img_no_src_pattern, result.cleaned_html)
            self.stdout.write(f'  Final images WITHOUT src: {len(no_src_images)}')
            
            if no_src_images:
                self.stdout.write(f'    Example: {no_src_images[0][:100]}...')
            
            self.stdout.write(f'\n📝 Processing elements: {result.removed_elements[:5]}')
                
        except Article.DoesNotExist:
            self.stdout.write(self.style.ERROR('Article 20894 not found'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {e}')) 