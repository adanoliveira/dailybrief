"""
Process Article Command
Processes an article with the AlgorithmicProcessor and saves the results to the database.
"""

import time
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from apps.articles.models import Article
from apps.content.processor.algorithmic_processor import AlgorithmicProcessor


class Command(BaseCommand):
    help = 'Process an article with AlgorithmicProcessor and save results to database'

    def add_arguments(self, parser):
        parser.add_argument(
            'article_id',
            type=int,
            help='Article ID to process'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force reprocessing even if already processed'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed processing information'
        )

    def handle(self, *args, **options):
        article_id = options['article_id']
        force = options['force']
        verbose = options['verbose']
        
        # Get the article
        try:
            article = Article.objects.get(id=article_id)
        except Article.DoesNotExist:
            raise CommandError(f"Article with ID {article_id} not found")
        
        # Check if already processed
        if not force and article.process_status == 'completed':
            self.stdout.write(
                self.style.WARNING(f"Article {article_id} already processed. Use --force to reprocess.")
            )
            return
        
        # Check if we have raw HTML
        if not article.raw_html:
            raise CommandError(f"Article {article_id} has no raw HTML content to process")
        
        self.stdout.write(f"🔄 Processing article: {article.title[:60]}...")
        
        # Initialize processor
        processor = AlgorithmicProcessor()
        
        # Prepare article metadata
        article_metadata = {
            'title': article.title,
            'author': article.author,
            'published_date': article.published_at,
            'source_name': article.source_name,
            'url': article.url
        }
        
        # Process the article
        start_time = time.time()
        
        with transaction.atomic():
            # Update status to processing
            article.process_status = 'processing'
            article.process_route = 'algorithmic'
            article.save(update_fields=['process_status', 'process_route'])
            
            try:
                # Process with algorithmic processor
                result = processor.process_content(article.raw_html, article_metadata)
                processing_time = int((time.time() - start_time) * 1000)
                
                if result.success:
                    # Convert content blocks to dictionaries for JSON serialization
                    content_blocks_data = []
                    for block in result.content_blocks:
                        if hasattr(block, '__dict__'):
                            # Convert ContentBlock object to dictionary
                            block_data = {
                                'type': block.type,
                                'position': block.position,
                                'content': getattr(block, 'content', None),
                                'text': getattr(block, 'text', None),
                                'level': getattr(block, 'level', None),
                                'id': getattr(block, 'id', None),
                                'classes': getattr(block, 'classes', None),
                                'src': getattr(block, 'src', None),
                                'alt': getattr(block, 'alt', None),
                                'caption': getattr(block, 'caption', None),
                                'title': getattr(block, 'title', None),
                                'metadata': getattr(block, 'metadata', None),
                                'listType': getattr(block, 'listType', None),
                                'items': getattr(block, 'items', None),
                                'cite': getattr(block, 'cite', None),
                                'language': getattr(block, 'language', None),
                            }
                            # Remove None values
                            block_data = {k: v for k, v in block_data.items() if v is not None}
                            content_blocks_data.append(block_data)
                        else:
                            # Already a dictionary
                            content_blocks_data.append(block)
                    
                    # Save the results
                    article.clean_content = result.clean_content
                    article.content_blocks = content_blocks_data
                    article.extracted_metadata = result.extracted_metadata
                    article.content_quality_metrics = {
                        'completeness': result.quality_score,
                        'quality_score': result.quality_score,
                        'word_count': result.extracted_metadata.get('word_count', 0),
                        'block_count': len(content_blocks_data)
                    }
                    article.process_status = 'completed'
                    article.process_duration_ms = result.processing_time_ms
                    article.process_cost_usd = 0.001  # Algorithmic processing cost
                    article.process_attempts = (article.process_attempts or 0) + 1
                    article.last_process_attempt = article.updated_at
                    
                    # Update rich content metadata using the model method
                    article.update_rich_content_metadata()
                    
                    # Clear any previous error
                    article.process_error_message = ''
                    
                    article.save()
                    
                    # Print success message
                    self.stdout.write(
                        self.style.SUCCESS(f"✅ Successfully processed article {article_id}")
                    )
                    
                    if verbose:
                        self.stdout.write(f"   📊 Quality Score: {result.quality_score:.3f}")
                        self.stdout.write(f"   ⏱️  Processing Time: {result.processing_time_ms}ms")
                        self.stdout.write(f"   📝 Content: {len(result.clean_content):,} chars")
                        self.stdout.write(f"   🧱 Content Blocks: {len(content_blocks_data)}")
                        self.stdout.write(f"   📊 Metadata Fields: {len(result.extracted_metadata)}")
                        self.stdout.write(f"   🖼️  Media Count: {article.media_count}")
                        self.stdout.write(f"   🎯 Has Rich Content: {article.has_rich_content}")
                
                else:
                    # Save error state
                    article.process_status = 'failed'
                    article.process_error_message = result.error_message
                    article.process_attempts = (article.process_attempts or 0) + 1
                    article.last_process_attempt = article.updated_at
                    article.save()
                    
                    raise CommandError(f"Processing failed: {result.error_message}")
                    
            except Exception as e:
                # Save error state
                article.process_status = 'failed'
                article.process_error_message = str(e)
                article.process_attempts = (article.process_attempts or 0) + 1
                article.last_process_attempt = article.updated_at
                article.save()
                
                raise CommandError(f"Processing failed with exception: {str(e)}")
        
        self.stdout.write(
            self.style.SUCCESS(f"🎉 Article {article_id} processed and saved successfully!")
        ) 