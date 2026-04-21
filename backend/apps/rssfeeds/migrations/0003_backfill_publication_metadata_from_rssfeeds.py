from django.db import migrations


def backfill_publication_metadata_from_rssfeeds(apps, schema_editor):
    Publication = apps.get_model('feeds', 'Publication')
    RSSFeed = apps.get_model('rssfeeds', 'RSSFeed')

    publication_topic = Publication._meta.get_field('topics').remote_field.through
    publication_region = Publication._meta.get_field('regions').remote_field.through
    publication_language = Publication._meta.get_field('languages').remote_field.through

    topic_links = set()
    region_links = set()
    language_links = set()

    feeds = RSSFeed.objects.exclude(publication_id__isnull=True).values_list(
        'publication_id', 'topic_id', 'region_id', 'language_id'
    )

    for publication_id, topic_id, region_id, language_id in feeds.iterator():
        if topic_id:
            topic_links.add((publication_id, topic_id))
        if region_id:
            region_links.add((publication_id, region_id))
        if language_id:
            language_links.add((publication_id, language_id))

    publication_topic.objects.bulk_create(
        [
            publication_topic(publication_id=publication_id, topic_id=topic_id)
            for publication_id, topic_id in topic_links
        ],
        ignore_conflicts=True,
    )

    publication_region.objects.bulk_create(
        [
            publication_region(publication_id=publication_id, region_id=region_id)
            for publication_id, region_id in region_links
        ],
        ignore_conflicts=True,
    )

    publication_language.objects.bulk_create(
        [
            publication_language(publication_id=publication_id, language_id=language_id)
            for publication_id, language_id in language_links
        ],
        ignore_conflicts=True,
    )


class Migration(migrations.Migration):

    dependencies = [
        ('feeds', '0003_language_description_region_description_and_more'),
        ('rssfeeds', '0002_rssfeed_is_curated'),
    ]

    operations = [
        migrations.RunPython(
            backfill_publication_metadata_from_rssfeeds,
            migrations.RunPython.noop,
        ),
    ]
