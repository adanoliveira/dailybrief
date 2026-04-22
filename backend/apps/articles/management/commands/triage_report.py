"""
Management command to show triage statistics.

Usage:
    python manage.py triage_report              # Today's stats
    python manage.py triage_report --days 3     # Last 3 days
"""

import logging
from collections import defaultdict
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import models
from django.utils import timezone

from apps.articles.models import Article

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Show article triage statistics'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days', type=int, default=1,
            help='Number of days back to report (default: 1)'
        )

    def handle(self, *args, **options):
        days = options['days']
        cutoff = timezone.now() - timedelta(days=days)

        triaged = Article.objects.filter(triaged_at__gte=cutoff)
        total = triaged.count()

        if total == 0:
            self.stdout.write(self.style.WARNING("No triaged articles found."))
            return

        self.stdout.write(self.style.SUCCESS(f"\nTriage Report (last {days} day(s))"))
        self.stdout.write("=" * 60)

        # Status breakdown
        self.stdout.write("\nBy Status:")
        for row in triaged.values('triage_status').annotate(
            cnt=models.Count('id')
        ).order_by('-cnt'):
            pct = row['cnt'] / total * 100
            self.stdout.write(f"  {row['triage_status']:15s} {row['cnt']:5d}  ({pct:.1f}%)")

        # Method breakdown
        self.stdout.write("\nBy Method:")
        for row in triaged.values('triage_method').annotate(
            cnt=models.Count('id')
        ).order_by('-cnt'):
            self.stdout.write(f"  {row['triage_method'] or 'unset':20s} {row['cnt']:5d}")

        # Publisher breakdown (top 10)
        self.stdout.write("\nBy Publisher (top 10):")
        pub_stats = triaged.values(
            'publication__name'
        ).annotate(
            total=models.Count('id'),
            accepted=models.Count('id', filter=models.Q(triage_status='accepted')),
            rejected=models.Count('id', filter=models.Q(triage_status='rejected')),
            pending=models.Count('id', filter=models.Q(triage_status__in=['pending', 'pending_llm'])),
        ).order_by('-total')[:10]

        for row in pub_stats:
            name = (row['publication__name'] or 'Unknown')[:25]
            self.stdout.write(
                f"  {name:25s}  total={row['total']:4d}  "
                f"accepted={row['accepted']:3d}  rejected={row['rejected']:3d}  "
                f"pending={row['pending']:3d}"
            )

        # Topic breakdown
        self.stdout.write("\nBy Topic:")
        topic_stats = triaged.values(
            'topics__name'
        ).annotate(
            total=models.Count('id', distinct=True),
            accepted=models.Count('id', distinct=True, filter=models.Q(triage_status='accepted')),
        ).order_by('-total')

        for row in topic_stats:
            if row['topics__name']:
                self.stdout.write(
                    f"  {row['topics__name']:20s}  total={row['total']:4d}  accepted={row['accepted']:3d}"
                )

        # Cost summary
        total_cost = triaged.filter(
            triage_cost_usd__isnull=False
        ).aggregate(
            cost=models.Sum('triage_cost_usd')
        )['cost'] or 0
        llm_count = triaged.filter(triage_method='llm').count()

        self.stdout.write(f"\nLLM Triage: {llm_count} calls, ${total_cost:.4f} total cost")
        self.stdout.write(self.style.SUCCESS("\nDone."))
