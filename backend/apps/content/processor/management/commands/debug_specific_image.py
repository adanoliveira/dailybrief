from django.core.management.base import BaseCommand, CommandError
from bs4 import BeautifulSoup
import re
from apps.articles.models import Article


class Command(BaseCommand):
    help = 'Debug a specific image by alt text to understand why it is being filtered out'

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

        self.stdout.write(f'Debugging image containing "{alt_contains}" in article {article_id}')
        
        # Parse the raw HTML
        soup = BeautifulSoup(article.raw_html, 'html.parser')
        
        # Find the specific image
        img = soup.find('img', alt=lambda x: x and alt_contains in x.lower())
        
        if not img:
            self.stdout.write(f'❌ No image found with alt containing "{alt_contains}"')
            return
        
        self.stdout.write(f'✅ Found image!')
        self.stdout.write(f'Alt: {img.get("alt", "")}')
        self.stdout.write(f'Src: {img.get("src", "")[:100]}...')
        
        # Import the processor to test the filtering
        from apps.content.processor.algorithmic_processor import AlgorithmicProcessor
        processor = AlgorithmicProcessor()
        
        # Test our filtering logic
        should_skip = processor._should_skip_element_for_content_blocks(img)
        should_exclude_img = processor._should_exclude_section(img)
        is_content_img = processor._is_content_image(img)
        
        self.stdout.write(f'\n🧪 Filtering results:')
        self.stdout.write(f'  _should_skip_element_for_content_blocks: {should_skip}')
        self.stdout.write(f'  _should_exclude_section (img itself): {should_exclude_img}')
        self.stdout.write(f'  _is_content_image: {is_content_img}')
        
        if should_skip:
            self.stdout.write(f'  🔴 This image is being FILTERED OUT!')
            
            # Analyze the parent hierarchy to find what's causing the exclusion
            self.stdout.write(f'\n🔍 Analyzing parent hierarchy:')
            current = img
            level = 0
            
            while current and level < 10:
                classes = current.get('class', [])
                element_id = current.get('id', '')
                tag_name = current.name
                
                self.stdout.write(f'\nLevel {level}: <{tag_name}>')
                
                if classes:
                    self.stdout.write(f'  Classes: {classes}')
                
                if element_id:
                    self.stdout.write(f'  ID: {element_id}')
                
                # Check if this level should be excluded
                should_exclude_parent = processor._should_exclude_section(current)
                if should_exclude_parent:
                    self.stdout.write(f'  🔴 EXCLUDED at this level!')
                    
                    # Show detailed exclusion reason
                    data_parsely_title = current.get('data-parsely-title', '')
                    has_hub_peek = current.get('data-is-hub-peek') is not None
                    
                    self.stdout.write(f'  Exclusion analysis:')
                    if data_parsely_title:
                        self.stdout.write(f'    data-parsely-title: "{data_parsely_title}"')
                    if has_hub_peek:
                        self.stdout.write(f'    has data-is-hub-peek: {has_hub_peek}')
                    
                    # Check class combinations
                    classes_lower = ' '.join(classes).lower()
                    if 'pagelistenhancementgeneric' in classes_lower and 'enhancement' in classes_lower:
                        self.stdout.write(f'    ⚠️  Has PageListEnhancementGeneric + Enhancement combination')
                    
                    if has_hub_peek and any(pattern in classes_lower for pattern in ['pageliststandard', 'pagepromo', 'pagelist-items']):
                        self.stdout.write(f'    ⚠️  Has hub-peek + specific class combination')
                
                # Check for data attributes
                data_attrs = {k: v for k, v in current.attrs.items() if k.startswith('data-')}
                if data_attrs:
                    self.stdout.write(f'  Data attrs: {list(data_attrs.keys())[:5]}...')  # Show first 5 keys
                
                current = current.parent
                level += 1
                
                if current and current.name in ['body', 'html']:
                    break
        else:
            self.stdout.write(f'  ✅ This image would be properly included')

        self.stdout.write(self.style.SUCCESS('\n✅ Specific image analysis complete!')) 