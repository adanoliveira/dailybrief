from django.core.management.base import BaseCommand, CommandError
from bs4 import BeautifulSoup
import re
from apps.articles.models import Article


class Command(BaseCommand):
    help = 'Step through _is_content_image method to debug why specific images are returning False'

    def add_arguments(self, parser):
        parser.add_argument(
            '--article-id',
            type=int,
            default=15193,
            help='Article ID to debug (default: 15193)'
        )
        parser.add_argument(
            '--alt-contains',
            type=str,
            default='canada house',
            help='Text that should be contained in the alt attribute'
        )

    def handle(self, *args, **options):
        article_id = options['article_id']
        alt_contains = options['alt_contains'].lower()
        
        try:
            article = Article.objects.get(id=article_id)
        except Article.DoesNotExist:
            raise CommandError(f'Article with ID {article_id} does not exist')

        self.stdout.write(f'Step-by-step debugging _is_content_image for "{alt_contains}"')
        
        # Parse the raw HTML
        soup = BeautifulSoup(article.raw_html, 'html.parser')
        
        # Find the specific image
        img = soup.find('img', alt=lambda x: x and alt_contains in x.lower())
        
        if not img:
            self.stdout.write(f'❌ No image found with alt containing "{alt_contains}"')
            return
        
        self.stdout.write(f'✅ Found image!')
        self.stdout.write(f'Alt: {img.get("alt", "")}')
        self.stdout.write(f'Src: {img.get("src", "")}')
        
        # Step through _is_content_image logic manually
        self.stdout.write(f'\n🔍 Step-by-step _is_content_image analysis:')
        
        # Step 1: Check src for non-content patterns
        src = img.get('src', '').lower()
        self.stdout.write(f'\nStep 1: Check src patterns')
        self.stdout.write(f'  src (lowercase): {src}')
        
        non_content_patterns = [
            'icon', 'logo', 'avatar', 'badge', 'button', 'arrow', 'sprite',
            'newsletter', 'signup', 'subscribe', 'generic', 'placeholder',
            'banner', 'ad', 'advertisement', 'promo', 'marketing',
            'social', 'share', 'facebook', 'twitter', 'linkedin',
            'footer', 'header', 'nav', 'sidebar', 'widget'
        ]
        
        found_patterns = [pattern for pattern in non_content_patterns if pattern in src]
        if found_patterns:
            self.stdout.write(f'  ❌ Found non-content patterns: {found_patterns}')
            self.stdout.write(f'  🔴 Would return False here!')
            return
        else:
            self.stdout.write(f'  ✅ No non-content patterns found')
        
        # Step 2: Check problematic paths
        self.stdout.write(f'\nStep 2: Check problematic paths')
        problematic_paths = ['/dr/resources/', '/assets/icons/', '/static/icons/']
        found_paths = [path for path in problematic_paths if path in src]
        if found_paths:
            self.stdout.write(f'  ❌ Found problematic paths: {found_paths}')
            self.stdout.write(f'  🔴 Would return False here!')
            return
        else:
            self.stdout.write(f'  ✅ No problematic paths found')
        
        # Step 3: Check alt text
        alt = img.get('alt', '').lower()
        self.stdout.write(f'\nStep 3: Check alt text')
        self.stdout.write(f'  alt (lowercase): {alt[:100]}...')
        self.stdout.write(f'  alt length: {len(alt)}')
        
        if len(alt) > 10:
            self.stdout.write(f'  ✅ Alt text is substantial (len > 10)')
            self.stdout.write(f'  🟢 Should return True here!')
            self.stdout.write(f'  🤔 But if we got False, something else must be overriding...')
        else:
            self.stdout.write(f'  ❌ Alt text not substantial (len <= 10)')
        
        # Continue with other checks to see if anything overrides
        self.stdout.write(f'\nStep 4: Check decorative alt patterns')
        decorative_alts = ['', 'image', 'photo', 'picture']
        icon_patterns = ['icon', 'logo']
        
        if alt in decorative_alts:
            self.stdout.write(f'  ⚠️  Alt is decorative: "{alt}"')
        elif any(pattern in alt for pattern in icon_patterns):
            self.stdout.write(f'  ⚠️  Alt contains icon patterns: {[p for p in icon_patterns if p in alt]}')
        else:
            self.stdout.write(f'  ✅ Alt is not decorative')
        
        # Step 5: Check dimensions
        self.stdout.write(f'\nStep 5: Check dimensions')
        width = img.get('width')
        height = img.get('height')
        self.stdout.write(f'  width: {width}, height: {height}')
        
        if width and height:
            try:
                w, h = int(width), int(height)
                if w < 30 or h < 30:
                    self.stdout.write(f'  ❌ Too small: {w}x{h}')
                    self.stdout.write(f'  🔴 Would return False here!')
                    return
                elif w > 80 and h > 80:
                    self.stdout.write(f'  ✅ Good size: {w}x{h}')
                    self.stdout.write(f'  🟢 Would return True here!')
                else:
                    self.stdout.write(f'  ⚠️  Medium size: {w}x{h}')
            except ValueError:
                self.stdout.write(f'  ⚠️  Invalid dimensions')
        else:
            self.stdout.write(f'  ⚠️  No dimensions available')
        
        # Now test the actual method
        from apps.content.processor.algorithmic_processor import AlgorithmicProcessor
        processor = AlgorithmicProcessor()
        result = processor._is_content_image(img)
        
        self.stdout.write(f'\n🧪 Final result from _is_content_image: {result}')
        
        if result:
            self.stdout.write(f'  ✅ Image correctly identified as content')
        else:
            self.stdout.write(f'  ❌ Image incorrectly identified as non-content')
            self.stdout.write(f'  🔍 This suggests there might be additional logic not covered above')

        self.stdout.write(self.style.SUCCESS('\n✅ Image filtering debug complete!')) 