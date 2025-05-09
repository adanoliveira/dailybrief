from django.core.management.base import BaseCommand
from apps.articles.models import Article
from apps.newsapi.models import NewsAPIArticle

class Command(BaseCommand):
    help = 'Check field lengths in Article and NewsAPIArticle models'

    def handle(self, *args, **options):
        self.stdout.write('Field lengths for Article model:')
        for field in Article._meta.fields:
            if hasattr(field, 'max_length') and field.max_length is not None:
                self.stdout.write(f'  {field.name}: {field.max_length}')
        
        self.stdout.write('\nField lengths for NewsAPIArticle model:')
        for field in NewsAPIArticle._meta.fields:
            if hasattr(field, 'max_length') and field.max_length is not None:
                self.stdout.write(f'  {field.name}: {field.max_length}') 