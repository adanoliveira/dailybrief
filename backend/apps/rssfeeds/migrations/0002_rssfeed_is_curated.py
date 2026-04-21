"""Add is_curated field to RSSFeed and set it for known curated feeds."""

from django.db import migrations, models


def set_curated_feeds(apps, schema_editor):
    """Mark known top-stories/homepage feeds as curated."""
    RSSFeed = apps.get_model('rssfeeds', 'RSSFeed')

    # Feed titles/PKs that are editorially curated (top stories, homepage)
    curated_titles = [
        'NYT Homepage',
        'BBC News Top Stories',
        'G1 Top News',
        'Folha de S.Paulo \u2014 Em Cima da Hora',  # Em Cima da Hora
        'ESPN Top News',
        'CBS Sports Headlines',
        'Washington Post National',
        'Reuters Top News',
        'Bloomberg Markets',
    ]

    RSSFeed.objects.filter(title__in=curated_titles).update(is_curated=True)


class Migration(migrations.Migration):

    dependencies = [
        ('rssfeeds', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='rssfeed',
            name='is_curated',
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(set_curated_feeds, migrations.RunPython.noop),
    ]
