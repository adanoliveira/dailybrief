from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from apps.content.analyzer.models import Event, ArticleEvent, EventEntity
from collections import defaultdict
import time


class Command(BaseCommand):
    help = 'Retroactively deduplicate events using new clustering criteria (distance < 0.25 + 1 shared entity)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--recent-days',
            type=int,
            default=30,
            help='Only process events from the last N days (default: 30)'
        )
        
        parser.add_argument(
            '--distance-threshold',
            type=float,
            default=0.25,
            help='Distance threshold for clustering (default: 0.25)'
        )
        
        parser.add_argument(
            '--min-shared-entities',
            type=int,
            default=1,
            help='Minimum shared entities required (default: 1)'
        )
        
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be merged without making changes'
        )
        
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Process events in batches of this size (default: 100)'
        )

    def handle(self, *args, **options):
        recent_days = options['recent_days']
        distance_threshold = options['distance_threshold']
        min_shared_entities = options['min_shared_entities']
        dry_run = options['dry_run']
        batch_size = options['batch_size']
        
        self.stdout.write('🔄 RETROACTIVE EVENT DEDUPLICATION')
        self.stdout.write('=' * 60)
        self.stdout.write(f'📅 Processing events from last {recent_days} days')
        self.stdout.write(f'🎯 Distance threshold: {distance_threshold}')
        self.stdout.write(f'🔗 Min shared entities: {min_shared_entities}')
        self.stdout.write(f'🧪 Dry run: {"Yes" if dry_run else "No"}')
        self.stdout.write('')
        
        # Get events to process
        cutoff_date = timezone.now() - timedelta(days=recent_days)
        events_to_process = Event.objects.filter(
            last_seen_at__gte=cutoff_date,
            centroid_embed__isnull=False
        ).order_by('first_seen_at')  # Process oldest first to keep earliest as canonical
        
        total_events = events_to_process.count()
        self.stdout.write(f'📊 Found {total_events} events with embeddings to process')
        
        if total_events == 0:
            self.stdout.write('❌ No events found to process')
            return
        
        # Track clustering results
        clusters = []  # List of (canonical_event_id, duplicate_event_ids)
        processed_event_ids = set()
        
        start_time = time.time()
        processed_count = 0
        
        self.stdout.write('🔍 Finding event clusters...')
        
        # Process events in batches
        for i in range(0, total_events, batch_size):
            batch = events_to_process[i:i + batch_size]
            
            for event in batch:
                if event.id in processed_event_ids:
                    continue  # Already processed as part of another cluster
                
                # Find similar events using new criteria
                similar_events = self._find_similar_events(
                    event, events_to_process, distance_threshold, min_shared_entities
                )
                
                if similar_events:
                    # Create cluster with this event as canonical (earliest)
                    duplicate_ids = [e.id for e in similar_events if e.id != event.id]
                    clusters.append((event.id, duplicate_ids))
                    
                    # Mark all events in this cluster as processed
                    processed_event_ids.add(event.id)
                    processed_event_ids.update(duplicate_ids)
                    
                    self.stdout.write(f'   📎 Cluster found: Event {event.id} + {len(duplicate_ids)} duplicates')
                
                processed_count += 1
                if processed_count % 50 == 0:
                    elapsed = time.time() - start_time
                    self.stdout.write(f'   Processed {processed_count}/{total_events} events ({elapsed:.1f}s)')
        
        elapsed = time.time() - start_time
        self.stdout.write(f'✅ Clustering analysis completed in {elapsed:.1f}s')
        self.stdout.write('')
        
        # Report clustering results
        total_duplicates = sum(len(duplicates) for _, duplicates in clusters)
        self.stdout.write('📊 CLUSTERING RESULTS:')
        self.stdout.write(f'• Clusters found: {len(clusters)}')
        self.stdout.write(f'• Events to be merged: {total_duplicates}')
        self.stdout.write(f'• Events remaining after dedup: {total_events - total_duplicates}')
        self.stdout.write(f'• Reduction: {(total_duplicates / total_events * 100):.1f}%')
        self.stdout.write('')
        
        if not clusters:
            self.stdout.write('✅ No duplicate events found - database is already clean!')
            return
        
        # Show top clusters
        self.stdout.write('🔝 TOP 10 CLUSTERS TO BE MERGED:')
        sorted_clusters = sorted(clusters, key=lambda x: len(x[1]), reverse=True)
        for i, (canonical_id, duplicate_ids) in enumerate(sorted_clusters[:10], 1):
            try:
                canonical_event = Event.objects.get(id=canonical_id)
                self.stdout.write(f'{i:2d}. "{canonical_event.title[:50]}..." (Event {canonical_id})')
                self.stdout.write(f'    📎 Will absorb {len(duplicate_ids)} duplicate events')
                self.stdout.write(f'    📅 Created: {canonical_event.first_seen_at.strftime("%Y-%m-%d %H:%M")}')
                
                # Show some duplicates
                if len(duplicate_ids) > 0:
                    sample_duplicates = Event.objects.filter(id__in=duplicate_ids[:3])
                    for j, dup_event in enumerate(sample_duplicates, 1):
                        self.stdout.write(f'       {j}. "{dup_event.title[:40]}..." (Event {dup_event.id})')
                    if len(duplicate_ids) > 3:
                        self.stdout.write(f'       ... and {len(duplicate_ids) - 3} more duplicates')
                
                self.stdout.write('')
            except Event.DoesNotExist:
                continue
        
        if dry_run:
            self.stdout.write('🧪 DRY RUN - No changes made to database')
            self.stdout.write('Remove --dry-run flag to apply changes')
            return
        
        # Apply the merges
        self.stdout.write('🔄 Applying event merges...')
        
        articles_moved = 0
        events_deleted = 0
        
        for i, (canonical_id, duplicate_ids) in enumerate(clusters, 1):
            try:
                with transaction.atomic():
                    canonical_event = Event.objects.get(id=canonical_id)
                    
                    # Process each duplicate event
                    for duplicate_id in duplicate_ids:
                        try:
                            duplicate_event = Event.objects.get(id=duplicate_id)
                            
                            # Move all articles from duplicate to canonical event
                            article_events = ArticleEvent.objects.filter(event=duplicate_event)
                            
                            for article_event in article_events:
                                # Check if article is already linked to canonical event
                                existing_link = ArticleEvent.objects.filter(
                                    article=article_event.article,
                                    event=canonical_event
                                ).first()
                                
                                if existing_link:
                                    # Keep the better relevance score
                                    if article_event.relevance_score > existing_link.relevance_score:
                                        existing_link.relevance_score = article_event.relevance_score
                                        existing_link.is_primary = article_event.is_primary or existing_link.is_primary
                                        existing_link.save()
                                    # Delete the duplicate link
                                    article_event.delete()
                                else:
                                    # Move the article to canonical event
                                    article_event.event = canonical_event
                                    article_event.save()
                                    articles_moved += 1
                            
                            # Move entities from duplicate to canonical event
                            duplicate_entities = EventEntity.objects.filter(event=duplicate_event)
                            for entity_link in duplicate_entities:
                                # Check if entity is already linked to canonical event
                                existing_entity_link = EventEntity.objects.filter(
                                    event=canonical_event,
                                    entity=entity_link.entity
                                ).first()
                                
                                if not existing_entity_link:
                                    # Move entity to canonical event
                                    entity_link.event = canonical_event
                                    entity_link.save()
                                else:
                                    # Keep the better relevance score
                                    if entity_link.relevance_score > existing_entity_link.relevance_score:
                                        existing_entity_link.relevance_score = entity_link.relevance_score
                                        existing_entity_link.save()
                                    entity_link.delete()
                            
                            # Update canonical event metadata
                            canonical_event.article_count = ArticleEvent.objects.filter(event=canonical_event).count()
                            canonical_event.last_seen_at = max(canonical_event.last_seen_at, duplicate_event.last_seen_at)
                            canonical_event.save()
                            
                            # Delete the duplicate event
                            duplicate_event.delete()
                            events_deleted += 1
                            
                        except Event.DoesNotExist:
                            self.stdout.write(f'   ⚠️  Duplicate event {duplicate_id} already deleted')
                            continue
                    
                    if i % 10 == 0:
                        self.stdout.write(f'   Processed {i}/{len(clusters)} clusters')
                        
            except Event.DoesNotExist:
                self.stdout.write(f'   ⚠️  Canonical event {canonical_id} not found')
                continue
            except Exception as e:
                self.stdout.write(f'   ❌ Error processing cluster {canonical_id}: {e}')
                continue
        
        elapsed_total = time.time() - start_time
        self.stdout.write('')
        self.stdout.write('✅ EVENT DEDUPLICATION COMPLETED!')
        self.stdout.write('=' * 60)
        self.stdout.write(f'• Clusters merged: {len(clusters)}')
        self.stdout.write(f'• Articles moved: {articles_moved}')
        self.stdout.write(f'• Events deleted: {events_deleted}')
        self.stdout.write(f'• Total time: {elapsed_total:.1f}s')
        self.stdout.write('')
        self.stdout.write('🎯 Database now uses improved event clustering!')
        self.stdout.write('   Run digest generation to see improved results.')

    def _find_similar_events(self, target_event, all_events, distance_threshold, min_shared_entities):
        """Find events similar to target_event using the new clustering criteria."""
        from pgvector.django import CosineDistance
        
        # Get target event entities
        target_entity_ids = set(
            EventEntity.objects.filter(event=target_event)
            .values_list('entity_id', flat=True)
        )
        
        # Find events with similar embeddings
        similar_events = all_events.filter(
            centroid_embed__isnull=False
        ).exclude(
            id=target_event.id
        ).annotate(
            distance=CosineDistance('centroid_embed', target_event.centroid_embed)
        ).filter(
            distance__lt=distance_threshold
        )
        
        # Filter by entity overlap
        matching_events = [target_event]  # Include the target event itself
        
        for event in similar_events:
            event_entity_ids = set(
                EventEntity.objects.filter(event=event)
                .values_list('entity_id', flat=True)
            )
            
            shared_entities = len(target_entity_ids.intersection(event_entity_ids))
            
            if shared_entities >= min_shared_entities:
                matching_events.append(event)
        
        return matching_events if len(matching_events) > 1 else [] 