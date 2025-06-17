# Generated manually for adding fields to ArticleEvent

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('analyzer', '0010_add_economic_crisis_event_type'),
    ]

    operations = [
        # Add new fields to existing ArticleEvent model
        migrations.AddField(
            model_name='articleevent',
            name='relevance_score',
            field=models.FloatField(default=1.0, help_text='Relevance of this event to the article (0.0-1.0)'),
        ),
        migrations.AddField(
            model_name='articleevent',
            name='is_primary',
            field=models.BooleanField(default=True, help_text='Whether this is the primary/main event for the article'),
        ),
        
        # Add index for is_primary field
        migrations.AddIndex(
            model_name='articleevent',
            index=models.Index(fields=['is_primary'], name='analyzer_article_event_is_primary_idx'),
        ),
    ] 