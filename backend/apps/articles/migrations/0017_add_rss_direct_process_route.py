"""Add rss_direct choice to Article.process_route."""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('articles', '0016_headline_cluster_and_score'),
    ]

    operations = [
        migrations.AlterField(
            model_name='article',
            name='process_route',
            field=models.CharField(
                blank=True,
                choices=[
                    ('safari_mode', 'Safari Reader Mode'),
                    ('llm_enhanced', 'LLM Enhanced'),
                    ('hybrid', 'Hybrid Processing'),
                    ('rss_direct', 'RSS Direct'),
                ],
                max_length=20,
                null=True,
            ),
        ),
    ]
