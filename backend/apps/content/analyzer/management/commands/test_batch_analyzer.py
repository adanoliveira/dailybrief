"""
Test command to analyze a batch of articles and show results.
"""
import time
from django.core.management.base import BaseCommand
from django.db import models
from apps.articles.models import Article
from apps.content.analyzer.services import AnalyzerService
from apps.content.analyzer.models import Event, Entity, ArticleEvent, ArticleEntity


class Command(BaseCommand):
    help = 'Test analyzer on a batch of articles'

    def add_arguments(self, parser):
        parser.add_argument(
            '--article-ids',
            type=str,
            required=True,
            help='Comma-separated list of article IDs to analyze'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force re-analysis of already analyzed articles'
        )

    def handle(self, *args, **options):
        # Parse article IDs
        article_ids_str = options['article_ids']
        try:
            article_ids = [int(aid.strip()) for aid in article_ids_str.split(',')]
        except ValueError:
            self.stdout.write(self.style.ERROR("Invalid article IDs format. Use comma-separated integers."))
            return

        force = options.get('force', False)
        
        self.stdout.write(self.style.SUCCESS(f"Testing analyzer with {len(article_ids)} articles"))
        self.stdout.write(f"Article IDs: {article_ids}")
        
        # Get articles
        articles = Article.objects.filter(id__in=article_ids).order_by('id')
        found_ids = list(articles.values_list('id', flat=True))
        missing_ids = set(article_ids) - set(found_ids)
        
        if missing_ids:
            self.stdout.write(self.style.WARNING(f"Missing articles: {missing_ids}"))
        
        self.stdout.write(f"Found {articles.count()} articles to analyze\n")
        
        # Initialize analyzer
        analyzer = AnalyzerService()
        
        # Track results
        results = {
            'successful': 0,
            'failed': 0,
            'total_cost': 0.0,
            'total_time': 0,
            'events_created': 0,
            'events_linked': 0,
            'entities_created': 0,
            'entities_linked': 0
        }
        
        # Get initial counts
        initial_events = Event.objects.count()
        initial_entities = Entity.objects.count()
        
        start_time = time.time()
        
        # Analyze each article
        for i, article in enumerate(articles, 1):
            self.stdout.write(f"\n[{i}/{articles.count()}] Analyzing article {article.id}: {article.title[:60]}...")
            
            try:
                # Run analysis
                result = analyzer.analyze_article(article, force=force)
                
                if result['success']:
                    results['successful'] += 1
                    results['total_cost'] += float(result.get('cost_usd', 0))
                    results['total_time'] += result.get('duration_ms', 0)
                    
                    # Show all events for this article (including primary and non-primary)
                    article_events = ArticleEvent.objects.filter(article=article).select_related('event').order_by('-relevance_score')
                    if article_events.exists():
                        self.stdout.write(f"  → Events ({article_events.count()} total):")
                        for ae in article_events:
                            event = ae.event
                            primary_indicator = " (PRIMARY)" if ae.is_primary else ""
                            self.stdout.write(f"      • {event.title}{primary_indicator}")
                            self.stdout.write(f"        Type: {event.event_type} | Relevance: {ae.relevance_score} | Articles: {event.article_count}")
                            self.stdout.write(f"        Abstract: {event.abstract[:100]}...")
                            if event.facts:
                                facts_preview = ', '.join(event.facts[:2])  # First 2 facts
                                self.stdout.write(f"        Facts: {facts_preview}")
                    else:
                        self.stdout.write("  → No events linked to this article")
                    
                    # Show entities for this article
                    article_entities = ArticleEntity.objects.filter(article=article).select_related('entity')[:5]  # First 5
                    if article_entities.exists():
                        entity_names = [ae.entity.display_name for ae in article_entities]
                        self.stdout.write(f"  → Entities: {', '.join(entity_names)}")
                    
                    self.stdout.write(self.style.SUCCESS(f"  ✓ Success (${result.get('cost_usd', 0):.6f}, {result.get('duration_ms', 0)}ms)"))
                    
                else:
                    results['failed'] += 1
                    self.stdout.write(self.style.ERROR(f"  ✗ Failed: {result.get('error', 'Unknown error')}"))
                    
            except Exception as e:
                results['failed'] += 1
                self.stdout.write(self.style.ERROR(f"  ✗ Exception: {str(e)}"))
        
        # Calculate final stats
        total_time = time.time() - start_time
        final_events = Event.objects.count()
        final_entities = Entity.objects.count()
        
        results['events_created'] = final_events - initial_events
        results['entities_created'] = final_entities - initial_entities
        
        # Count linked relationships
        results['events_linked'] = ArticleEvent.objects.filter(article__in=articles).count()
        results['entities_linked'] = ArticleEntity.objects.filter(article__in=articles).count()
        
        # Display summary
        self.stdout.write("\n" + "="*60)
        self.stdout.write(self.style.SUCCESS("BATCH ANALYSIS SUMMARY"))
        self.stdout.write("="*60)
        
        self.stdout.write(f"Articles processed: {results['successful']}/{len(article_ids)}")
        self.stdout.write(f"Failed: {results['failed']}")
        self.stdout.write(f"Total time: {total_time:.1f}s")
        self.stdout.write(f"Total cost: ${results['total_cost']:.6f}")
        self.stdout.write(f"Avg cost per article: ${results['total_cost']/max(results['successful'], 1):.6f}")
        
        self.stdout.write(f"\nEvents created: {results['events_created']}")
        self.stdout.write(f"Events linked to articles: {results['events_linked']}")
        self.stdout.write(f"Entities created: {results['entities_created']}")
        self.stdout.write(f"Entities linked to articles: {results['entities_linked']}")
        
        # Show event clustering stats
        if results['events_linked'] > 0:
            avg_articles_per_event = results['events_linked'] / max(final_events, 1)
            self.stdout.write(f"Average articles per event: {avg_articles_per_event:.1f}")
        
        # Show all events created
        if results['events_created'] > 0:
            self.stdout.write(f"\nALL EVENTS CREATED ({results['events_created']} total):")
            recent_events = Event.objects.order_by('-created_at')[:results['events_created']]
            for i, event in enumerate(recent_events, 1):
                self.stdout.write(f"\n{i}. {event.title}")
                self.stdout.write(f"   Type: {event.event_type} | Articles: {event.article_count}")
                self.stdout.write(f"   Abstract: {event.abstract}")
                if event.facts:
                    self.stdout.write(f"   Facts: {', '.join(event.facts[:3])}")  # First 3 facts
        
        self.stdout.write("\n" + "="*60) 