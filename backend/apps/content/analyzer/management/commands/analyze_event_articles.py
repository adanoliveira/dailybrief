from django.core.management.base import BaseCommand
from django.db.models import Count, Q
from apps.content.analyzer.models import Event, ArticleEvent


class Command(BaseCommand):
    help = 'Analyze event-article relationships to see distribution of articles per event'

    def add_arguments(self, parser):
        parser.add_argument(
            '--recent-days',
            type=int,
            default=7,
            help='Only analyze events from the last N days (default: 7)'
        )
        
        parser.add_argument(
            '--show-examples',
            action='store_true',
            help='Show examples of events with multiple articles'
        )

    def handle(self, *args, **options):
        from datetime import datetime, timedelta
        
        recent_days = options['recent_days']
        show_examples = options['show_examples']
        
        # Filter for recent events if specified
        queryset = Event.objects
        if recent_days:
            cutoff_date = datetime.now() - timedelta(days=recent_days)
            queryset = queryset.filter(first_seen_at__gte=cutoff_date)
            self.stdout.write(f"📅 Analyzing events from the last {recent_days} days")
        else:
            self.stdout.write("📅 Analyzing all events")
        
        # Get events with their article counts
        events_with_counts = queryset.annotate(
            total_articles=Count('articles'),
            primary_articles=Count('articles', filter=Q(articles__is_primary=True)),
            secondary_articles=Count('articles', filter=Q(articles__is_primary=False))
        ).filter(total_articles__gt=0).order_by('-total_articles')

        self.stdout.write('📊 EVENT-ARTICLE RELATIONSHIP ANALYSIS')
        self.stdout.write('=' * 60)

        # Overall statistics
        total_events = events_with_counts.count()
        if total_events == 0:
            self.stdout.write("❌ No events found with articles")
            return
        
        events_with_multiple = events_with_counts.filter(total_articles__gt=1).count()
        events_with_single = events_with_counts.filter(total_articles=1).count()

        self.stdout.write(f'Total events with articles: {total_events}')
        self.stdout.write(f'Events with multiple articles: {events_with_multiple} ({events_with_multiple/total_events*100:.1f}%)')
        self.stdout.write(f'Events with single article: {events_with_single} ({events_with_single/total_events*100:.1f}%)')
        self.stdout.write('')

        # Show breakdown by article count
        self.stdout.write('📈 BREAKDOWN BY ARTICLE COUNT:')
        max_articles = events_with_counts.first().total_articles if events_with_counts.exists() else 0
        
        for i in range(1, min(max_articles + 1, 21)):  # Check up to 20 articles or max, whichever is lower
            count = events_with_counts.filter(total_articles=i).count()
            if count > 0:
                percentage = count / total_events * 100
                self.stdout.write(f'{i:2d} article(s): {count:4d} events ({percentage:5.1f}%)')

        # Check for events with more than 20 articles
        if max_articles > 20:
            many_articles = events_with_counts.filter(total_articles__gt=20).count()
            if many_articles > 0:
                percentage = many_articles / total_events * 100
                self.stdout.write(f'20+ articles: {many_articles:4d} events ({percentage:5.1f}%)')

        self.stdout.write('')

        # Show top events with most articles
        self.stdout.write('🔝 TOP 10 EVENTS WITH MOST ARTICLES:')
        for i, event in enumerate(events_with_counts[:10], 1):
            self.stdout.write(f'{i:2d}. {event.title[:70]}...')
            self.stdout.write(f'    📊 Total: {event.total_articles} (Primary: {event.primary_articles}, Secondary: {event.secondary_articles})')
            self.stdout.write(f'    🕐 Created: {event.first_seen_at.strftime("%Y-%m-%d %H:%M:%S")}')
            
            if show_examples:
                # Show some article titles for this event
                sample_articles = event.articles.all()[:5]
                for j, article_event in enumerate(sample_articles, 1):
                    article = article_event.article
                    mention_type = 'Primary' if article_event.is_primary else 'Secondary'
                    pub_name = article.publication.name if article.publication else article.source_name
                    self.stdout.write(f'       {j}. [{mention_type}] {article.title[:60]}... ({pub_name})')
                
                if event.total_articles > 5:
                    self.stdout.write(f'       ... and {event.total_articles - 5} more articles')
            
            self.stdout.write('')
        
        # Additional insights
        self.stdout.write('💡 INSIGHTS:')
        
        avg_articles_per_event = sum(e.total_articles for e in events_with_counts) / total_events
        self.stdout.write(f'• Average articles per event: {avg_articles_per_event:.2f}')
        
        # Find events with high secondary mention counts
        high_secondary = events_with_counts.filter(secondary_articles__gte=5).count()
        if high_secondary > 0:
            self.stdout.write(f'• Events with 5+ secondary mentions: {high_secondary}')
        
        # Primary vs secondary distribution
        total_primary = sum(e.primary_articles for e in events_with_counts)
        total_secondary = sum(e.secondary_articles for e in events_with_counts)
        self.stdout.write(f'• Total primary mentions: {total_primary}')
        self.stdout.write(f'• Total secondary mentions: {total_secondary}')
        self.stdout.write(f'• Primary:Secondary ratio: {total_primary/total_secondary:.2f}:1' if total_secondary > 0 else '• Primary:Secondary ratio: All primary') 