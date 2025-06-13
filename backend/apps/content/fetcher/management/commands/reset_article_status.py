"""
Django management command to reset article fetch or process status to pending.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.articles.models import Article, FetchStatus, ProcessingStatus


class Command(BaseCommand):
    """Management command to reset article status to pending."""
    
    help = 'Reset article fetch or process status to pending'
    
    def add_arguments(self, parser):
        parser.add_argument(
            'article_id',
            type=int,
            help='Article ID to reset'
        )
        
        group = parser.add_mutually_exclusive_group()
        group.add_argument(
            '--fetch',
            action='store_true',
            help='Reset fetch status only'
        )
        group.add_argument(
            '--process',
            action='store_true',
            help='Reset process status only'
        )
        group.add_argument(
            '--both',
            action='store_true',
            help='Reset both statuses'
        )
    
    def handle(self, *args, **options):
        """Handle the command execution."""
        
        article_id = options['article_id']
        
        # Default to both if no specific option is provided
        if not (options['fetch'] or options['process'] or options['both']):
            options['both'] = True
        
        reset_fetch = options['fetch'] or options['both']
        reset_process = options['process'] or options['both']
        
        self.stdout.write(f"🔄 Resetting article {article_id}...")
        
        success, message, article_info = self.reset_article_status(
            article_id, 
            reset_fetch=reset_fetch, 
            reset_process=reset_process
        )
        
        if not success:
            self.stdout.write(self.style.ERROR(f"❌ Error: {message}"))
            return
        
        # Display article info
        self.stdout.write(f"\n📰 Article {article_info['id']}:")
        self.stdout.write(f"   Title: {article_info['title']}")
        self.stdout.write(f"   URL: {article_info['url']}")
        self.stdout.write(f"   📥 Fetch Status: {article_info['fetch_status']}")
        self.stdout.write(f"   ⚙️  Process Status: {article_info['process_status']}")
        self.stdout.write(f"   📅 Published: {article_info['published_at']}")
        
        # Display changes made
        if article_info['changes']:
            self.stdout.write(f"\n🔄 Changes made:")
            for change in article_info['changes']:
                if "→" in change:
                    self.stdout.write(self.style.SUCCESS(f"   ✅ {change}"))
                else:
                    self.stdout.write(f"   ℹ️  {change}")
        
        self.stdout.write(self.style.SUCCESS(f"\n✅ {message}"))
        
        # Provide helpful next steps
        if reset_fetch and article_info['fetch_status'] == FetchStatus.PENDING:
            self.stdout.write(f"💡 To refetch: ./docker.sh django fetch_content --article-id {article_id}")
        
        if reset_process and article_info['process_status'] == ProcessingStatus.PENDING:
            self.stdout.write(f"💡 To reprocess: ./docker.sh django process_articles --article-id {article_id}")
    
    def reset_article_status(self, article_id, reset_fetch=False, reset_process=False):
        """
        Reset article status(es) to pending.
        
        Args:
            article_id (int): Article ID to reset
            reset_fetch (bool): Whether to reset fetch status
            reset_process (bool): Whether to reset process status
            
        Returns:
            tuple: (success, message, article_info)
        """
        
        try:
            article = Article.objects.get(id=article_id)
        except Article.DoesNotExist:
            return False, f"Article with ID {article_id} not found", None
        
        # Store original statuses
        original_fetch_status = article.fetch_status
        original_process_status = article.process_status
        
        changes_made = []
        
        with transaction.atomic():
            if reset_fetch:
                if article.fetch_status != FetchStatus.PENDING:
                    article.fetch_status = FetchStatus.PENDING
                    changes_made.append(f"fetch: {original_fetch_status} → pending")
                else:
                    changes_made.append("fetch: already pending")
            
            if reset_process:
                if article.process_status != ProcessingStatus.PENDING:
                    article.process_status = ProcessingStatus.PENDING
                    changes_made.append(f"process: {original_process_status} → pending")
                else:
                    changes_made.append("process: already pending")
            
            if changes_made and any("→" in change for change in changes_made):
                article.save()
        
        article_info = {
            'id': article.id,
            'title': article.title[:70] + "..." if len(article.title) > 70 else article.title,
            'url': article.url,
            'fetch_status': article.fetch_status,
            'process_status': article.process_status,
            'published_at': article.published_at,
            'changes': changes_made
        }
        
        return True, "Status updated successfully", article_info 