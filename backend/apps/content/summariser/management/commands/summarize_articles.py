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
    process_pending_summarizations,
    retry_failed_summarizations
)
from apps.content.summariser.services import get_summarization_service


class Command(BaseCommand):
    help = 'Process article summarizations with various options'
    
    def add_arguments(self, parser):
        # Mode selection
        mode_group = parser.add_mutually_exclusive_group(required=True)
        mode_group.add_argument('--single', type=int, metavar='ARTICLE_ID',
                               help='Summarize a single article by ID')
        mode_group.add_argument('--batch', type=str, metavar='IDS',
                               help='Comma-separated list of article IDs to summarize')
        mode_group.add_argument('--pending', action='store_true',
                               help='Process all pending articles')
        mode_group.add_argument('--retry', action='store_true',
                               help='Retry failed summarizations')
        mode_group.add_argument('--status', action='store_true',
                               help='Show summarization status overview')
        mode_group.add_argument('--generate-embeddings', action='store_true',
                               help='Generate embeddings for articles with summaries')
        mode_group.add_argument('--embedding-batch', type=str, metavar='IDS',
                               help='Generate embeddings for specific article IDs')
        mode_group.add_argument('--find-similar', type=int, metavar='ARTICLE_ID',
                               help='Find articles similar to given article ID')
        mode_group.add_argument('--cleanup-embeddings', action='store_true',
                               help='Clean up orphaned embeddings')
        
        # Filtering options
        parser.add_argument('--content-source', 
                           choices=['imcomplete_text', 'full_cleaned_text', 'rich_content_blocks'],
                           help='Filter by content source type')
        parser.add_argument('--limit', type=int, default=50,
                           help='Maximum number of articles to process (default: 50)')
        parser.add_argument('--force', action='store_true',
                           help='Force re-processing even if already completed')
        parser.add_argument('--async', dest='use_async', action='store_true',
                           help='Use Celery for async processing')
        
        # Date filtering
        parser.add_argument('--since', type=str,
                           help='Process articles published since date (YYYY-MM-DD)')
        parser.add_argument('--until', type=str,
                           help='Process articles published until date (YYYY-MM-DD)')
        
        # Embedding options
        parser.add_argument('--similarity-threshold', type=float, default=0.22,
                           help='Similarity threshold for finding similar articles (default: 0.22)')
        parser.add_argument('--max-similar', type=int, default=5,
                           help='Maximum number of similar articles to return (default: 5)')
    
    def handle(self, *args, **options):
        """Main command handler."""
        
        # Determine mode from the mutually exclusive arguments
        if options['single']:
            mode = 'single'
        elif options['batch']:
            mode = 'batch'
        elif options['pending']:
            mode = 'pending'
        elif options['retry']:
            mode = 'retry'
        elif options['status']:
            mode = 'status'
        elif options['generate_embeddings']:
            mode = 'generate-embeddings'
        elif options['embedding_batch']:
            mode = 'embedding-batch'
        elif options['find_similar']:
            mode = 'find-similar'
        elif options['cleanup_embeddings']:
            mode = 'cleanup-embeddings'
        else:
            raise CommandError("No mode specified")
        
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
        elif mode == 'generate-embeddings':
            self.handle_generate_embeddings(options)
        elif mode == 'embedding-batch':
            self.handle_embedding_batch(options)
        elif mode == 'find-similar':
            self.handle_find_similar(options)
        elif mode == 'cleanup-embeddings':
            self.handle_cleanup_embeddings(options)
        else:
            raise CommandError(f"Unknown mode: {mode}")
    
    def handle_single_article(self, options):
        """Process a single article."""
        article_id = options['single']
        
        try:
            article = Article.objects.get(id=article_id)
        except Article.DoesNotExist:
            raise CommandError(f"Article {article_id} not found")
        
        self.stdout.write(f"Summarizing article {article_id}: {article.title[:50]}...")
        
        if options['use_async']:
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
<<<<<<< HEAD
=======
                        f"Longer Abstract: {result.longer_abstract}\n"
>>>>>>> main
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
        article_ids_str = options['batch']
        try:
            article_ids = [int(id.strip()) for id in article_ids_str.split(',')]
        except ValueError:
            raise CommandError("Invalid article IDs format. Use comma-separated integers.")
        
        self.stdout.write(f"Summarizing {len(article_ids)} articles...")
        
        if options['use_async']:
            # Use Celery tasks for each article
            for article_id in article_ids:
                result = summarize_article_pipeline.delay(article_id, options['force'])
            self.stdout.write(
                self.style.SUCCESS(f"Queued {len(article_ids)} summarization tasks")
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
<<<<<<< HEAD
=======
                                f"Longer Abstract: {result.longer_abstract}\n"
>>>>>>> main
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
<<<<<<< HEAD
=======
                            f"Longer Abstract: {result.longer_abstract}\n"
>>>>>>> main
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

    def handle_generate_embeddings(self, options):
        """Generate embeddings for articles with summaries."""
        from apps.content.summariser.tasks import generate_embeddings_for_pending_summaries
        
        limit = options['limit']
        use_async = options['use_async']
        
        self.stdout.write(f"Generating embeddings for up to {limit} articles with summaries...")
        
        if use_async:
            # Use Celery task
            task = generate_embeddings_for_pending_summaries.delay(limit=limit)
            self.stdout.write(
                self.style.SUCCESS(f"Embedding generation task queued: {task.id}")
            )
        else:
            # Run synchronously
            result = generate_embeddings_for_pending_summaries(limit=limit)
            
            if result['status'] == 'batches_queued':
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Queued {result['batches_created']} batches for {result['total_articles']} articles"
                    )
                )
            elif result['status'] == 'no_pending_articles':
                self.stdout.write(self.style.WARNING("No articles found that need embeddings"))
            else:
                self.stdout.write(self.style.ERROR(f"Failed: {result.get('error', 'Unknown error')}"))

    def handle_embedding_batch(self, options):
        """Generate embeddings for specific article IDs."""
        from apps.content.summariser.tasks import generate_embeddings_batch
        
        article_ids_str = options['embedding_batch']
        force = options['force']
        use_async = options['use_async']
        
        try:
            article_ids = [int(id.strip()) for id in article_ids_str.split(',')]
        except ValueError:
            raise CommandError("Invalid article IDs format. Use comma-separated integers.")
        
        self.stdout.write(f"Generating embeddings for {len(article_ids)} articles...")
        
        if use_async:
            # Use Celery task
            task = generate_embeddings_batch.delay(article_ids, force_regenerate=force)
            self.stdout.write(
                self.style.SUCCESS(f"Embedding batch task queued: {task.id}")
            )
        else:
            # Run synchronously (simulate the task)
            result = generate_embeddings_batch(article_ids, force_regenerate=force)
            
            if result['status'] == 'success':
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Generated embeddings: {result['created']} created, {result['updated']} updated"
                    )
                )
                self.stdout.write(f"  Total cost: ${result['total_cost_usd']:.6f}")
                self.stdout.write(f"  Processing time: {result['processing_time_ms']}ms")
            elif result['status'] == 'split_into_batches':
                self.stdout.write(
                    self.style.SUCCESS(f"Split {result['total_articles']} articles into smaller batches")
                )
            else:
                self.stdout.write(self.style.ERROR(f"Failed: {result.get('error', 'Unknown error')}"))

    def handle_find_similar(self, options):
        """Find articles similar to a given article."""
        from apps.content.summariser.tasks import find_similar_articles
        
        article_id = options['find_similar']
        similarity_threshold = options['similarity_threshold']
        max_similar = options['max_similar']
        
        self.stdout.write(f"Finding articles similar to article {article_id}...")
        
        result = find_similar_articles(
            article_id=article_id,
            similarity_threshold=similarity_threshold,
            limit=max_similar
        )
        
        if result['status'] == 'success':
            similar_articles = result['similar_articles']
            if similar_articles:
                self.stdout.write(
                    self.style.SUCCESS(f"Found {result['total_found']} similar articles:")
                )
                
                for article in similar_articles:
                    self.stdout.write(
                        f"  Article {article['article_id']}: {article['headline']} "
                        f"(similarity: {article['similarity_score']:.3f})"
                    )
            else:
                self.stdout.write(self.style.WARNING("No similar articles found"))
        elif result['status'] == 'no_embedding':
            self.stdout.write(self.style.ERROR(f"Article {article_id} has no embedding"))
        else:
            self.stdout.write(self.style.ERROR(f"Failed: {result.get('error', 'Unknown error')}"))

    def handle_cleanup_embeddings(self, options):
        """Clean up orphaned embeddings."""
        from apps.content.summariser.tasks import cleanup_orphaned_embeddings
        
        self.stdout.write("Cleaning up orphaned embeddings...")
        
        result = cleanup_orphaned_embeddings()
        
        if result['status'] == 'success':
            cleaned_count = result['cleaned_up']
            if cleaned_count > 0:
                self.stdout.write(
                    self.style.SUCCESS(f"Cleaned up {cleaned_count} orphaned embeddings")
                )
            else:
                self.stdout.write(self.style.SUCCESS("No orphaned embeddings found"))
        else:
            self.stdout.write(self.style.ERROR(f"Failed: {result.get('error', 'Unknown error')}")) 