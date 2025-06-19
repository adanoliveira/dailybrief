from django.core.management.base import BaseCommand
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
from apps.content.analyzer.models import Event, EventEntity


class Command(BaseCommand):
    help = 'Analyze entity patterns in events to understand semantic matching failures'

    def add_arguments(self, parser):
        parser.add_argument(
            '--hours',
            type=int,
            default=48,
            help='Hours to look back for recent events (default: 48)'
        )

    def handle(self, *args, **options):
        hours = options['hours']
        cutoff = timezone.now() - timedelta(hours=hours)
        
        # Get recent events with entity counts
        recent_events = Event.objects.filter(
            last_seen_at__gte=cutoff
        ).annotate(
            entity_count=Count('event_entities')
        ).order_by('-entity_count')

        self.stdout.write('🔍 ANALYZING ENTITY PATTERNS IN EVENTS')
        self.stdout.write('=' * 60)
        self.stdout.write(f'Looking at events from last {hours} hours')
        self.stdout.write(f'Total recent events: {recent_events.count()}')
        self.stdout.write('')

        # Entity distribution
        self.stdout.write('📊 ENTITY COUNT DISTRIBUTION:')
        entity_distribution = {}
        for event in recent_events:
            count = event.entity_count
            entity_distribution[count] = entity_distribution.get(count, 0) + 1

        total_events = recent_events.count()
        for entity_count in sorted(entity_distribution.keys()):
            event_count = entity_distribution[entity_count]
            percentage = event_count / total_events * 100 if total_events > 0 else 0
            self.stdout.write(f'{entity_count:2d} entities: {event_count:4d} events ({percentage:5.1f}%)')

        # Analysis of semantic matching potential
        self.stdout.write('')
        self.stdout.write('🎯 SEMANTIC MATCHING ANALYSIS:')
        events_with_0_entities = recent_events.filter(entity_count=0).count()
        events_with_1_entity = recent_events.filter(entity_count=1).count()  
        events_with_2plus = recent_events.filter(entity_count__gte=2).count()
        
        self.stdout.write(f'• Events with 0 entities: {events_with_0_entities} ({events_with_0_entities/total_events*100:.1f}%)')
        self.stdout.write(f'• Events with 1 entity: {events_with_1_entity} ({events_with_1_entity/total_events*100:.1f}%)')
        self.stdout.write(f'• Events with 2+ entities: {events_with_2plus} ({events_with_2plus/total_events*100:.1f}%)')
        
        self.stdout.write('')
        self.stdout.write('💡 SEMANTIC MATCHING REQUIREMENTS:')
        self.stdout.write('Current algorithm requires BOTH:')
        self.stdout.write('  1. Similar embedding (distance < 0.15)')
        self.stdout.write('  2. At least 2 shared entities')
        self.stdout.write('')
        self.stdout.write(f'❌ PROBLEM: Only {events_with_2plus} events can potentially match!')
        self.stdout.write(f'❌ IMPACT: {events_with_0_entities + events_with_1_entity}/{total_events} events ({(events_with_0_entities + events_with_1_entity)/total_events*100:.1f}%) will NEVER match')

        # Show sample events with 2+ entities
        if events_with_2plus > 0:
            self.stdout.write('')
            self.stdout.write('📋 SAMPLE EVENTS WITH 2+ ENTITIES:')
            sample_events = recent_events.filter(entity_count__gte=2)[:10]
            
            for i, event in enumerate(sample_events, 1):
                entities = [ee.entity.display_name for ee in event.event_entities.all()[:5]]
                self.stdout.write(f'{i:2d}. "{event.title[:60]}..."')
                self.stdout.write(f'    Entities ({event.entity_count}): {", ".join(entities)}')
                if event.entity_count > 5:
                    self.stdout.write(f'    ... and {event.entity_count - 5} more')
                self.stdout.write('')

        # Recommendations
        self.stdout.write('🔧 RECOMMENDED FIXES:')
        self.stdout.write('1. Lower entity requirement (2+ → 1+ shared entities)')
        self.stdout.write('2. Relax embedding similarity threshold (0.15 → 0.25)')
        self.stdout.write('3. Add fallback matching without entity requirement')
        self.stdout.write('4. Improve event title normalization for hash matching') 