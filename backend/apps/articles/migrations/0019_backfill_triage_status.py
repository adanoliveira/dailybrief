"""Backfill triage_status for existing articles.

Articles that have already completed the full pipeline get 'accepted' (legacy).
Everything else stays at 'pending' (the field default).
"""

from django.db import migrations


def backfill_triage(apps, schema_editor):
    Article = apps.get_model('articles', 'Article')
    # Mark fully-processed articles as accepted
    updated = Article.objects.filter(
        analyzer_status='completed',
    ).update(
        triage_status='accepted',
        triage_method='legacy',
        triage_reason='Backfilled: already fully processed before triage system',
    )
    print(f"  Backfilled {updated} completed articles as triage_status='accepted'")


def reverse_backfill(apps, schema_editor):
    Article = apps.get_model('articles', 'Article')
    Article.objects.filter(triage_method='legacy').update(
        triage_status='pending',
        triage_method='',
        triage_reason='',
    )


class Migration(migrations.Migration):
    dependencies = [
        ('articles', '0018_triage_fields'),
    ]

    operations = [
        migrations.RunPython(backfill_triage, reverse_backfill),
    ]
