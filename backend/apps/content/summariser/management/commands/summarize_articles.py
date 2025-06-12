"""
Management command to process article summarizations.

Provides various options for summarizing articles including batch processing,
retry failed summaries, and processing by content source.
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import models
from django.utils import timezone

from apps.articles.models import Article, SummarizationStatus
from apps.content.summariser.tasks import (
    summarize_article_pipeline, 
    batch_summarize_articles,
    process_pending_summarizations,
    retry_failed_summarizations
)
from apps.content.summariser.services import get_summarization_service


class Command(BaseCommand):
    help = 'Process article summarizations with various options'
    
    def add_arguments(self, parser):
        # Processing mode
        parser.add_argument(
            '--mode',
            choices=['single', 'batch', 'pending', 'retry', 'status'],
            default='pending',
            help='Processing mode'
        )
        
        # Article selection
        parser.add_argument(
            '--article-id',
            type=int,
            help='Specific article ID to summarize (for single mode)'
        )
        
        parser.add_argument(
            '--article-ids',
            nargs='+',
            type=int,
            help='List of article IDs to summarize (for batch mode)'
        )
        
        parser.add_argument(
            '--content-source',
            choices=['basic_content', 'clean_content', 'any'],
            default='any',
            help='Content source to filter articles'
        )
        
        # Processing options
        parser.add_argument(
            '--limit',
            type=int,
            default=20,
            help='Maximum number of articles to process'
        )
        
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force regeneration of existing summaries'
        )
        
        parser.add_argument(
            '--async',
            action='store_true',
            help='Use Celery tasks for async processing'
        )
        
        # Filtering options
        parser.add_argument(
            '--min-content-length',
            type=int,
            default=200,
            help='Minimum content length for processing'
        )
        
        parser.add_argument(
            '--days-back',
            type=int,
            help='Only process articles from the last N days'
        )
    
    def handle(self, *args, **options):
        """Main command handler."""
        mode = options['mode']
        
        # Auto-detect mode based on arguments if mode is still default 'pending'
        if mode == 'pending':
            if options.get('article_id'):
                mode = 'single'
                self.stdout.write("Auto-detected mode: single (based on --article-id)")
            elif options.get('article_ids'):
                mode = 'batch'
                self.stdout.write("Auto-detected mode: batch (based on --article-ids)")
        
        if mode == 'single':
            self.handle_single_article(options)
        elif mode == 'batch':
            self.handle_batch_articles(options)
        elif mode == 'pending':
            self.handle_pending_articles(options)
        elif mode == 'retry':
            self.handle_retry_failed(options)
        elif mode == 'status':
            self.handle_status_report(options)
        else:
            raise CommandError(f"Unknown mode: {mode}")
    
    def handle_single_article(self, options):
        """Process a single article."""
        article_id = options.get('article_id')
        if not article_id:
            raise CommandError("--article-id is required for single mode")
        
        try:
            article = Article.objects.get(id=article_id)
        except Article.DoesNotExist:
            raise CommandError(f"Article {article_id} not found")
        
        self.stdout.write(f"Summarizing article {article_id}: {article.title[:50]}...")
        
        if options['async']:
            # Use Celery task
            result = summarize_article_pipeline.delay(article_id, options['force'])
            self.stdout.write(
                self.style.SUCCESS(f"Queued summarization task: {result.id}")
            )
        else:
            # Process synchronously
            service = get_summarization_service()
            result = service.summarize_article(article, force_regenerate=options['force'])
            
            if result.success:
                # Get the content that was fed to the model
                content, content_source = article.best_content_for_summarization
                content_preview = content[:500] + "..." if content and len(content) > 500 else content or "No content"
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Successfully summarized article {article_id}\n"
                        f"Title: {article.title}\n"
                        f"Content Source: {content_source}\n"
                        f"Content Preview: {content_preview}\n"
                        f"\n--- SUMMARY ---\n"
                        f"Headline: {result.headline}\n"
                        f"Abstract: {result.abstract}\n"
                        f"Facts: {result.facts}\n"
                        f"Opinions: {result.opinions}\n"
                        f"Impact: {result.impact}\n"
                        f"\nCost: ${result.total_cost_usd:.6f}\n"
                        f"Stages: {', '.join(result.stages_completed or [])}"
                    )
                )
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f"Failed to summarize article {article_id}: {result.error_message}"
                    )
                )
    
    def handle_batch_articles(self, options):
        """Process a batch of specific articles."""
        article_ids = options.get('article_ids')
        if not article_ids:
            raise CommandError("--article-ids is required for batch mode")
        
        self.stdout.write(f"Summarizing {len(article_ids)} articles...")
        
        if options['async']:
            # Use Celery batch task
            result = batch_summarize_articles.delay(article_ids, options['force'])
            self.stdout.write(
                self.style.SUCCESS(f"Queued batch summarization task: {result.id}")
            )
        else:
            # Process synchronously
            service = get_summarization_service()
            successful = 0
            failed = 0
            total_cost = 0.0
            
            for article_id in article_ids:
                try:
                    article = Article.objects.get(id=article_id)
                    result = service.summarize_article(article, force_regenerate=options['force'])
                    
                    if result.success:
                        successful += 1
                        total_cost += float(result.total_cost_usd)
                        
                        # Get the content that was fed to the model
                        content, content_source = article.best_content_for_summarization
                        content_preview = content[:500] + "..." if content and len(content) > 500 else content or "No content"
                        
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"Successfully summarized article {article_id}\n"
                                f"Title: {article.title}\n"
                                f"Content Source: {content_source}\n"
                                f"Content Preview: {content_preview}\n"
                                f"\n--- SUMMARY ---\n"
                                f"Headline: {result.headline}\n"
                                f"Abstract: {result.abstract}\n"
                                f"Facts: {result.facts}\n"
                                f"Opinions: {result.opinions}\n"
                                f"Impact: {result.impact}\n"
                                f"\nCost: ${result.total_cost_usd:.6f}\n"
                                f"Stages: {', '.join(result.stages_completed or [])}"
                            )
                        )
                    else:
                        failed += 1
                        self.stdout.write(f"✗ Article {article_id}: {result.error_message}")
                        
                except Article.DoesNotExist:
                    failed += 1
                    self.stdout.write(f"✗ Article {article_id}: Not found")
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"Batch processing completed: {successful} successful, {failed} failed, "
                    f"total cost: ${total_cost:.4f}"
                )
            )
    
    def handle_pending_articles(self, options):
        """Process pending articles that need summarization."""
        self.stdout.write("Processing pending articles...")
        
        # Build query for pending articles
        query = Article.objects.filter(
            summarization_status=SummarizationStatus.PENDING,
            summarization_attempts__lt=3
        )
        
        # Filter by content source
        content_source = options['content_source']
        min_length = options['min_content_length']
        
        if content_source == 'basic_content':
            query = query.filter(
                basic_content__isnull=False,
                basic_content__regex=f'.{{{min_length},}}'
            )
        elif content_source == 'clean_content':
            query = query.filter(
                clean_content__isnull=False,
                clean_content__regex=f'.{{{min_length},}}'
            )
        else:  # any
            query = query.filter(
                models.Q(clean_content__isnull=False, clean_content__regex=f'.{{{min_length},}}') |
                models.Q(basic_content__isnull=False, basic_content__regex=f'.{{{min_length},}}')
            )
        
        # Filter by date if specified
        if options['days_back']:
            cutoff_date = timezone.now() - timezone.timedelta(days=options['days_back'])
            query = query.filter(published_at__gte=cutoff_date)
        
        # Apply limit and order
        articles = query.order_by('published_at')[:options['limit']]
        
        if not articles:
            self.stdout.write("No pending articles found for summarization")
            return
        
        self.stdout.write(f"Found {len(articles)} articles to summarize")
        
        if options['async']:
            # Use Celery task
            result = process_pending_summarizations.delay(options['limit'])
            self.stdout.write(
                self.style.SUCCESS(f"Queued pending processing task: {result.id}")
            )
        else:
            # Process synchronously
            service = get_summarization_service()
            successful = 0
            failed = 0
            total_cost = 0.0
            
            for article in articles:
                result = service.summarize_article(article, force_regenerate=options['force'])
                
                if result.success:
                    successful += 1
                    total_cost += float(result.total_cost_usd)
                    
                    # Get the content that was fed to the model
                    content, content_source = article.best_content_for_summarization
                    content_preview = content[:500] + "..." if content and len(content) > 500 else content or "No content"
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Successfully summarized article {article.id}\n"
                            f"Title: {article.title}\n"
                            f"Content Source: {content_source}\n"
                            f"Content Preview: {content_preview}\n"
                            f"\n--- SUMMARY ---\n"
                            f"Headline: {result.headline}\n"
                            f"Abstract: {result.abstract}\n"
                            f"Facts: {result.facts}\n"
                            f"Opinions: {result.opinions}\n"
                            f"Impact: {result.impact}\n"
                            f"\nCost: ${result.total_cost_usd:.6f}\n"
                            f"Stages: {', '.join(result.stages_completed or [])}"
                        )
                    )
                else:
                    failed += 1
                    self.stdout.write(f"✗ {article.id}: {result.error_message}")
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"Processing completed: {successful} successful, {failed} failed, "
                    f"total cost: ${total_cost:.4f}"
                )
            )
    
    def handle_retry_failed(self, options):
        """Retry failed summarizations."""
        self.stdout.write("Retrying failed summarizations...")
        
        if options['async']:
            # Use Celery task
            result = retry_failed_summarizations.delay()
            self.stdout.write(
                self.style.SUCCESS(f"Queued retry task: {result.id}")
            )
        else:
            # Find failed articles
            failed_articles = Article.objects.filter(
                summarization_status=SummarizationStatus.FAILED,
                summarization_attempts__lt=3
            )[:options['limit']]
            
            if not failed_articles:
                self.stdout.write("No failed articles found for retry")
                return
            
            self.stdout.write(f"Retrying {len(failed_articles)} failed articles")
            
            service = get_summarization_service()
            successful = 0
            failed = 0
            
            for article in failed_articles:
                # Reset status
                article.summarization_status = SummarizationStatus.PENDING
                article.summarization_error_message = ""
                article.save(update_fields=['summarization_status', 'summarization_error_message'])
                
                # Retry summarization
                result = service.summarize_article(article)
                
                if result.success:
                    successful += 1
                    self.stdout.write(f"✓ Retry {article.id}: Success")
                else:
                    failed += 1
                    self.stdout.write(f"✗ Retry {article.id}: {result.error_message}")
            
            self.stdout.write(
                self.style.SUCCESS(f"Retry completed: {successful} successful, {failed} failed")
            )
    
    def handle_status_report(self, options):
        """Generate a status report."""
        self.stdout.write("Summarization Status Report")
        self.stdout.write("=" * 50)
        
        # Count articles by status
        pending = Article.objects.filter(summarization_status=SummarizationStatus.PENDING).count()
        processing = Article.objects.filter(summarization_status=SummarizationStatus.PROCESSING).count()
        completed = Article.objects.filter(summarization_status=SummarizationStatus.COMPLETED).count()
        failed = Article.objects.filter(summarization_status=SummarizationStatus.FAILED).count()
        
        self.stdout.write(f"Pending:    {pending:,}")
        self.stdout.write(f"Processing: {processing:,}")
        self.stdout.write(f"Completed:  {completed:,}")
        self.stdout.write(f"Failed:     {failed:,}")
        self.stdout.write(f"Total:      {pending + processing + completed + failed:,}")
        
        # Recent activity (last 24 hours)
        yesterday = timezone.now() - timezone.timedelta(hours=24)
        recent_completed = Article.objects.filter(
            summarization_status=SummarizationStatus.COMPLETED,
            summarized_at__gte=yesterday
        ).count()
        
        self.stdout.write(f"\nCompleted in last 24h: {recent_completed:,}")
        
        # Average cost calculation
        recent_summaries = Article.objects.filter(
            summarization_status=SummarizationStatus.COMPLETED,
            summarization_cost_usd__isnull=False
        ).order_by('-summarized_at')[:100]
        
        if recent_summaries:
            total_cost = sum(float(article.summarization_cost_usd or 0) for article in recent_summaries)
            avg_cost = total_cost / len(recent_summaries)
            self.stdout.write(f"Average cost per article: ${avg_cost:.6f}")
            
            # Estimate daily cost
            daily_estimate = avg_cost * recent_completed if recent_completed > 0 else 0
            self.stdout.write(f"Estimated daily cost: ${daily_estimate:.4f}")
        
        # Content source breakdown
        self.stdout.write("\nContent Source Breakdown:")
        basic_only = Article.objects.filter(
            summarization_status=SummarizationStatus.COMPLETED,
            summary_content_source='basic_content'
        ).count()
        clean_content = Article.objects.filter(
            summarization_status=SummarizationStatus.COMPLETED,
            summary_content_source='clean_content'
        ).count()
        
        self.stdout.write(f"Basic content: {basic_only:,}")
        self.stdout.write(f"Clean content: {clean_content:,}")
        
        # Error analysis
        if failed > 0:
            self.stdout.write(f"\nRecent Errors (last {failed} failed):")
            recent_failures = Article.objects.filter(
                summarization_status=SummarizationStatus.FAILED
            ).order_by('-last_summarization_attempt')[:5]
            
            for article in recent_failures:
                error_msg = article.summarization_error_message[:50] + "..." if len(article.summarization_error_message) > 50 else article.summarization_error_message
                self.stdout.write(f"  Article {article.id}: {error_msg}") 