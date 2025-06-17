from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('analyzer', '0002_remove_duplicate_fields'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='articleanalysis',
            name='primary_region_code',
        ),
        migrations.RemoveField(
            model_name='articleanalysis',
            name='secondary_region_codes',
        ),
        migrations.RemoveField(
            model_name='articleanalysis',
            name='region_relevance',
        ),
        migrations.RemoveField(
            model_name='articleanalysis',
            name='primary_topic_slug',
        ),
        migrations.RemoveField(
            model_name='articleanalysis',
            name='secondary_topic_slugs',
        ),
        migrations.RemoveField(
            model_name='articleanalysis',
            name='topic_relevance',
        ),
        migrations.RemoveField(
            model_name='articleanalysis',
            name='secondary_topics',
        ),
        migrations.RemoveField(
            model_name='articleanalysis',
            name='secondary_regions',
        ),
    ] 