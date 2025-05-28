from django.core.management.base import BaseCommand, CommandError
from bs4 import BeautifulSoup
import re
from apps.articles.models import Article


class Command(BaseCommand):
    help = 'Debug legitimate images being filtered out to understand overly aggressive filtering'

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

        self.stdout.write(f'Debugging legitimate images in article {article_id}: {article.title[:80]}...')
        
        # Parse the raw HTML
        soup = BeautifulSoup(article.raw_html, 'html.parser')
        
        # Find legitimate images (King Charles related)
        legitimate_imgs = []
        for img in soup.find_all('img'):
            alt = img.get('alt', '').lower()
            if 'king' in alt or 'charles' in alt or 'queen' in alt or 'camilla' in alt:
                legitimate_imgs.append(img)
        
        self.stdout.write(f'Found {len(legitimate_imgs)} legitimate images')
        
        # Import the processor to test the filtering
        from apps.content.processor.algorithmic_processor import AlgorithmicProcessor
        processor = AlgorithmicProcessor()
        
        for i, img in enumerate(legitimate_imgs[:3]):  # Check first 3
            self.stdout.write(f'\n--- Legitimate Image {i+1} ---')
            self.stdout.write(f'Alt: {img.get("alt", "")}')
            self.stdout.write(f'Src: {img.get("src", "")[:100]}...')
            
            # Test our filtering logic
            should_skip = processor._should_skip_element_for_content_blocks(img)
            should_exclude_img = processor._should_exclude_section(img)
            is_content_img = processor._is_content_image(img)
            
            self.stdout.write(f'\nFiltering results:')
            self.stdout.write(f'  _should_skip_element_for_content_blocks: {should_skip}')
            self.stdout.write(f'  _should_exclude_section (img itself): {should_exclude_img}')
            self.stdout.write(f'  _is_content_image: {is_content_img}')
            
            if should_skip:
                self.stdout.write(f'  🔴 This legitimate image is being WRONGLY FILTERED OUT!')
                
                # Find which parent is causing the exclusion
                current = img.parent
                level = 0
                problematic_parents = []
                
                while current and level < 10:
                    should_exclude_parent = processor._should_exclude_section(current)
                    if should_exclude_parent:
                        classes = current.get('class', [])
                        element_id = current.get('id', '')
                        data_attrs = {k: v for k, v in current.attrs.items() if k.startswith('data-')}
                        
                        problematic_parents.append({
                            'level': level,
                            'tag': current.name,
                            'classes': classes,
                            'id': element_id,
                            'data_attrs': data_attrs
                        })
                    
                    current = current.parent
                    level += 1
                    if current and current.name in ['body', 'html']:
                        break
                
                if problematic_parents:
                    self.stdout.write(f'  Problematic parent(s) causing exclusion:')
                    for parent in problematic_parents:
                        self.stdout.write(f'    Level {parent["level"]}: <{parent["tag"]}>')
                        if parent['classes']:
                            self.stdout.write(f'      Classes: {parent["classes"]}')
                        if parent['id']:
                            self.stdout.write(f'      ID: {parent["id"]}')
                        if parent['data_attrs']:
                            self.stdout.write(f'      Data attrs: {parent["data_attrs"]}')
            else:
                self.stdout.write(f'  ✅ This image would be properly included')

        self.stdout.write(self.style.SUCCESS('\n✅ Legitimate images analysis complete!')) 