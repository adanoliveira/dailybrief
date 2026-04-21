"""Add HeadlineCluster model and headline_score/headline_cluster fields to Article."""

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('articles', '0015_add_unique_content_hash'),
    ]

    operations = [
        migrations.CreateModel(
            name='HeadlineCluster',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('representative_title', models.CharField(max_length=512)),
                ('article_count', models.IntegerField(default=1)),
                ('first_seen', models.DateTimeField()),
                ('last_updated', models.DateTimeField()),
                ('burst_score', models.FloatField(default=0.0)),
                ('is_active', models.BooleanField(default=True)),
                ('language', models.CharField(default='en', max_length=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'indexes': [
                    models.Index(fields=['is_active', 'last_updated'], name='articles_he_is_acti_idx'),
                    models.Index(fields=['language', 'is_active'], name='articles_he_languag_idx'),
                ],
            },
        ),
        migrations.AddField(
            model_name='article',
            name='headline_score',
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name='article',
            name='headline_cluster',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='articles',
                to='articles.headlinecluster',
            ),
        ),
        migrations.AddIndex(
            model_name='article',
            index=models.Index(fields=['headline_score'], name='articles_ar_headlin_idx'),
        ),
    ]
