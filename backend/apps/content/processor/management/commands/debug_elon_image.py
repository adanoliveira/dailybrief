from django.core.management.base import BaseCommand, CommandError
from bs4 import BeautifulSoup
import re
from apps.articles.models import Article


class Command(BaseCommand):
    help = 'Debug the Elon Musk image parent hierarchy to understand why it is not being filtered out'

    def add_arguments(self, parser):
        parser.add_argument(
            '--article-id',
            type=int,
            default=15193,
            help='Article ID to debug (default: 15193)'
        )

    def handle(self, *args, **options):
        article_id = options['article_id']
        
        try:
            article = Article.objects.get(id=article_id)
        except Article.DoesNotExist:
            raise CommandError(f'Article with ID {article_id} does not exist')

        self.stdout.write(f'Debugging article {article_id}: {article.title[:80]}...')
        
        # Parse the raw HTML
        soup = BeautifulSoup(article.raw_html, 'html.parser')
        
        # Find the Elon Musk images
        elon_imgs = soup.find_all('img', alt=re.compile(r'Elon.*Musk', re.IGNORECASE))
        self.stdout.write(f'Found {len(elon_imgs)} Elon Musk images in raw HTML')
        
        for i, img in enumerate(elon_imgs):
            self.stdout.write(f'\n--- Image {i+1} ---')
            self.stdout.write(f'Alt: {img.get("alt", "")}')
            self.stdout.write(f'Src: {img.get("src", "")}')
            
            # Check parent hierarchy up to 10 levels
            current = img
            level = 0
            page_below_found = False
            taboola_found = False
            
            while current and level < 10:
                classes = current.get('class', [])
                element_id = current.get('id', '')
                tag_name = current.name
                
                self.stdout.write(f'Level {level}: <{tag_name}>')
                
                if classes:
                    self.stdout.write(f'  Classes: {classes}')
                    
                    # Check for Page-below specifically
                    if 'Page-below' in classes:
                        page_below_found = True
                        self.stdout.write(f'  ⚠️  FOUND Page-below at level {level}!')
                
                if element_id:
                    self.stdout.write(f'  ID: {element_id}')
                
                # Check for data attributes that might indicate widgets
                data_attrs = {}
                for attr_name in current.attrs:
                    if attr_name.startswith('data-'):
                        data_attrs[attr_name] = current.attrs[attr_name]
                
                if data_attrs:
                    self.stdout.write(f'  Data attrs: {data_attrs}')
                    
                    # Check for Taboola specifically
                    for attr_name, attr_value in data_attrs.items():
                        if 'taboola' in str(attr_value).lower() or 'taboola' in attr_name.lower():
                            taboola_found = True
                            self.stdout.write(f'  ⚠️  FOUND Taboola reference: {attr_name}={attr_value}')
                
                current = current.parent
                level += 1
                
                if current and current.name in ['body', 'html']:
                    break
            
            # Summary for this image
            self.stdout.write(f'\n📊 Summary for Image {i+1}:')
            self.stdout.write(f'  Page-below found: {page_below_found}')
            self.stdout.write(f'  Taboola found: {taboola_found}')
            
            if page_below_found or taboola_found:
                self.stdout.write('  🔴 This image SHOULD be filtered out!')
            else:
                self.stdout.write('  🟡 This image might not be in a filterable section')
        
        # Also test our filtering logic
        self.stdout.write(f'\n🧪 Testing our filtering logic...')
        
        # Import the processor to test the filtering
        from apps.content.processor.algorithmic_processor import AlgorithmicProcessor
        processor = AlgorithmicProcessor()
        
        for i, img in enumerate(elon_imgs):
            should_skip = processor._should_skip_element_for_content_blocks(img)
            should_exclude_img = processor._should_exclude_section(img)
            is_content_img = processor._is_content_image(img)
            
            self.stdout.write(f'\nImage {i+1} filtering results:')
            self.stdout.write(f'  _should_skip_element_for_content_blocks: {should_skip}')
            self.stdout.write(f'  _should_exclude_section (img itself): {should_exclude_img}')
            self.stdout.write(f'  _is_content_image: {is_content_img}')
            
            # Test parent exclusion manually
            current = img.parent
            level = 0
            parent_exclusions = []
            while current and level < 10:
                should_exclude_parent = processor._should_exclude_section(current)
                if should_exclude_parent:
                    parent_exclusions.append(f'Level {level}: <{current.name}> classes={current.get("class", [])}')
                current = current.parent
                level += 1
                if current and current.name in ['body', 'html']:
                    break
            
            if parent_exclusions:
                self.stdout.write(f'  Parent exclusions found:')
                for exclusion in parent_exclusions:
                    self.stdout.write(f'    {exclusion}')
            else:
                self.stdout.write(f'  No parent exclusions found')

        self.stdout.write(self.style.SUCCESS('\n✅ Debug analysis complete!')) 