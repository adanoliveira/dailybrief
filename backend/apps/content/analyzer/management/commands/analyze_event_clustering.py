from django.core.management.base import BaseCommand
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from apps.content.analyzer.models import Event, ArticleEvent, EventEntity
from collections import defaultdict
import time


class Command(BaseCommand):
    help = 'Analyze potential event clustering based on semantic similarity (distance < 0.25)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--recent-days',
            type=int,
            default=7,
            help='Only analyze events from the last N days (default: 7)'
        )
        
        parser.add_argument(
            '--distance-threshold',
            type=float,
            default=0.25,
            help='Distance threshold for clustering (default: 0.25)'
        )
        
        parser.add_argument(
            '--min-embedding-events',
            type=int,
            default=50,
            help='Minimum number of events with embeddings to analyze (default: 50)'
        )
        
        parser.add_argument(
            '--detailed-analysis',
            action='store_true',
            help='Show detailed analysis with full event titles for qualitative review'
        )
        
        parser.add_argument(
            '--top-clusters',
            type=int,
            default=15,
            help='Number of top clustering events to analyze in detail (default: 15)'
        )
        
        parser.add_argument(
            '--require-shared-entities',
            type=int,
            default=0,
            help='Require minimum shared entities for clustering (0=disabled, 1+=enabled, default: 0)'
        )

    def handle(self, *args, **options):
        recent_days = options['recent_days']
        distance_threshold = options['distance_threshold']
        min_embedding_events = options['min_embedding_events']
        detailed_analysis = options['detailed_analysis']
        top_clusters = options['top_clusters']
        require_shared_entities = options['require_shared_entities']
        
        # Filter for recent events with embeddings
        cutoff_date = timezone.now() - timedelta(days=recent_days)
        events_with_embeddings = Event.objects.filter(
            last_seen_at__gte=cutoff_date,
            centroid_embed__isnull=False
        ).annotate(
            total_articles=Count('articles')
        ).order_by('-total_articles', '-last_seen_at')

        total_events = events_with_embeddings.count()
        
        self.stdout.write('🔍 ANALYZING EVENT CLUSTERING POTENTIAL')
        self.stdout.write('=' * 60)
        self.stdout.write(f'📅 Looking at events from last {recent_days} days')
        self.stdout.write(f'🎯 Distance threshold: {distance_threshold}')
        if require_shared_entities > 0:
            self.stdout.write(f'🔗 Shared entities required: {require_shared_entities}+')
        else:
            self.stdout.write('🔗 Entity overlap: Not required')
        self.stdout.write(f'📊 Events with embeddings: {total_events}')
        
        if total_events < min_embedding_events:
            self.stdout.write(f'❌ Not enough events with embeddings (minimum: {min_embedding_events})')
            return
        
        self.stdout.write('')
        self.stdout.write('🔄 Computing semantic similarities...')
        
        # Dictionary to store similarity results
        event_similarities = {}  # event_id -> list of similar event ids
        similarity_counts = {}   # event_id -> count of similar events
        
        start_time = time.time()
        processed = 0
        
        # For each event, find similar events
        for event in events_with_embeddings:
            try:
                from pgvector.django import CosineDistance
                
                # Find similar events (excluding itself)
                similar_events = Event.objects.filter(
                    last_seen_at__gte=cutoff_date,
                    centroid_embed__isnull=False
                ).exclude(
                    id=event.id
                ).annotate(
                    distance=CosineDistance('centroid_embed', event.centroid_embed)
                ).filter(
                    distance__lt=distance_threshold
                ).order_by('distance')
                
                # Apply entity overlap filtering if requested
                if require_shared_entities > 0:
                    # Get entities for the current event
                    current_event_entity_ids = set(
                        EventEntity.objects.filter(event=event)
                        .values_list('entity_id', flat=True)
                    )
                    
                    # Filter similar events by entity overlap
                    filtered_similar_events = []
                    for similar_event in similar_events:
                        similar_event_entity_ids = set(
                            EventEntity.objects.filter(event=similar_event)
                            .values_list('entity_id', flat=True)
                        )
                        
                        shared_entities = len(current_event_entity_ids.intersection(similar_event_entity_ids))
                        
                        if shared_entities >= require_shared_entities:
                            filtered_similar_events.append(similar_event.id)
                    
                    similar_event_ids = filtered_similar_events
                else:
                    similar_event_ids = list(similar_events.values_list('id', flat=True))
                
                event_similarities[event.id] = similar_event_ids
                similarity_counts[event.id] = len(similar_event_ids)
                
                processed += 1
                if processed % 50 == 0:
                    elapsed = time.time() - start_time
                    self.stdout.write(f'   Processed {processed}/{total_events} events ({elapsed:.1f}s)')
                
            except Exception as e:
                self.stdout.write(f'❌ Error processing event {event.id}: {e}')
                event_similarities[event.id] = []
                similarity_counts[event.id] = 0
        
        elapsed = time.time() - start_time
        self.stdout.write(f'✅ Completed analysis in {elapsed:.1f}s')
        self.stdout.write('')
        
        # Analyze clustering potential
        self.stdout.write('📊 CLUSTERING ANALYSIS RESULTS')
        self.stdout.write('=' * 60)
        
        # Distribution of similarity counts
        similarity_distribution = defaultdict(int)
        for count in similarity_counts.values():
            similarity_distribution[count] += 1
        
        self.stdout.write('📈 SIMILARITY COUNT DISTRIBUTION:')
        total_analyzed = len(similarity_counts)
        for sim_count in sorted(similarity_distribution.keys(), reverse=True):
            event_count = similarity_distribution[sim_count]
            percentage = event_count / total_analyzed * 100
            self.stdout.write(f'{sim_count:3d} similar events: {event_count:4d} events ({percentage:5.1f}%)')
        
        self.stdout.write('')
        
        # Events with most potential clustering
        self.stdout.write('🔝 TOP EVENTS BY CLUSTERING POTENTIAL:')
        self.stdout.write('(Events that could be merged with the most other events)')
        self.stdout.write('')
        
        # Sort events by similarity count (descending)
        sorted_events = sorted(
            [(event_id, count) for event_id, count in similarity_counts.items()],
            key=lambda x: x[1],
            reverse=True
        )
        
        # Deduplicate clusters - only show the first representative from each cluster
        shown_event_ids = set()  # Track events we've already shown
        cluster_representatives = []  # Store (event_id, similar_count, cluster_members)
        
        for event_id, similar_count in sorted_events:
            if event_id in shown_event_ids:
                continue  # Skip if this event was already shown as part of another cluster
            
            # This event becomes the representative of its cluster
            cluster_members = event_similarities[event_id]
            cluster_representatives.append((event_id, similar_count, cluster_members))
            
            # Mark this event and all its similar events as "shown"
            shown_event_ids.add(event_id)
            shown_event_ids.update(cluster_members)
        
        # Show top cluster representatives
        for i, (event_id, similar_count, cluster_members) in enumerate(cluster_representatives[:top_clusters], 1):
            try:
                event = Event.objects.get(id=event_id)
                
                self.stdout.write(f'{i:2d}. "{event.title[:60]}..."')
                self.stdout.write(f'    📊 Could cluster with {similar_count} other events')
                self.stdout.write(f'    📅 Created: {event.first_seen_at.strftime("%Y-%m-%d %H:%M")}')
                self.stdout.write(f'    📰 Articles: {event.article_count}')
                
                # Show similar events with more detail if requested
                if detailed_analysis and similar_count > 0:
                    from pgvector.django import CosineDistance
                    
                    # Get similar events with distances for detailed analysis
                    similar_events_detailed = Event.objects.filter(
                        id__in=cluster_members
                    ).annotate(
                        distance=CosineDistance('centroid_embed', event.centroid_embed)
                    ).order_by('distance')
                    
                    self.stdout.write('    🔗 All similar events (with distances):')
                    for j, similar_event in enumerate(similar_events_detailed, 1):
                        self.stdout.write(f'       {j:2d}. [{similar_event.distance:.3f}] "{similar_event.title}"')
                        if j >= 10:  # Limit to first 10 for readability
                            remaining = similar_count - 10
                            if remaining > 0:
                                self.stdout.write(f'       ... and {remaining} more similar events')
                            break
                else:
                    # Show a few similar events as examples (original behavior)
                    if similar_count > 0:
                        sample_similar = Event.objects.filter(
                            id__in=cluster_members[:3]
                        ).values_list('title', flat=True)
                        
                        self.stdout.write('    🔗 Similar events:')
                        for j, similar_title in enumerate(sample_similar, 1):
                            self.stdout.write(f'       {j}. "{similar_title[:50]}..."')
                        
                        if similar_count > 3:
                            self.stdout.write(f'       ... and {similar_count - 3} more similar events')
                
                self.stdout.write('')
                
            except Event.DoesNotExist:
                continue
        
        # Calculate potential clustering impact
        self.stdout.write('💡 CLUSTERING IMPACT ANALYSIS:')
        self.stdout.write('=' * 60)
        
        # Events that could be clustered (have at least 1 similar event)
        clusterable_events = sum(1 for count in similarity_counts.values() if count > 0)
        isolated_events = total_analyzed - clusterable_events
        
        self.stdout.write(f'• Events that could be clustered: {clusterable_events}/{total_analyzed} ({clusterable_events/total_analyzed*100:.1f}%)')
        self.stdout.write(f'• Events that remain isolated: {isolated_events}/{total_analyzed} ({isolated_events/total_analyzed*100:.1f}%)')
        
        # Estimate cluster reduction
        total_similarities = sum(similarity_counts.values())
        avg_cluster_size = total_similarities / clusterable_events if clusterable_events > 0 else 0
        estimated_clusters = total_analyzed - (total_similarities // 2)  # Rough estimate
        
        self.stdout.write(f'• Average similar events per clusterable event: {avg_cluster_size:.1f}')
        self.stdout.write(f'• Estimated final cluster count: ~{estimated_clusters} (vs {total_analyzed} current)')
        self.stdout.write(f'• Potential reduction: {((total_analyzed - estimated_clusters) / total_analyzed * 100):.1f}%')
        
        # High-clustering events (could merge with 5+ others)
        high_clustering = sum(1 for count in similarity_counts.values() if count >= 5)
        if high_clustering > 0:
            self.stdout.write('')
            self.stdout.write(f'🎯 HIGH-CLUSTERING EVENTS: {high_clustering} events could each merge with 5+ others')
            self.stdout.write('   These represent the biggest clustering opportunities!')
        
        # Recommendations
        self.stdout.write('')
        self.stdout.write('🔧 RECOMMENDATIONS:')
        if clusterable_events > total_analyzed * 0.3:  # More than 30% could be clustered
            self.stdout.write(f'✅ HIGH CLUSTERING POTENTIAL: {clusterable_events/total_analyzed*100:.1f}% of events could be merged')
            self.stdout.write('   → Implement relaxed semantic matching (distance < 0.25)')
            self.stdout.write('   → Remove entity overlap requirement')
        else:
            self.stdout.write(f'⚠️  MODERATE CLUSTERING POTENTIAL: {clusterable_events/total_analyzed*100:.1f}% of events could be merged')
            self.stdout.write('   → Consider other clustering approaches')
        
        if high_clustering > 10:
            self.stdout.write(f'🎯 Focus on high-clustering events first ({high_clustering} events with 5+ matches)') 