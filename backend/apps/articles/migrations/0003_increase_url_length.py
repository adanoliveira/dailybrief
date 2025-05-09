from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('articles', '0002_storygroup_remove_article_news_api_id_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='article',
            name='url',
            field=models.URLField(max_length=1024),
        ),
        migrations.AlterField(
            model_name='article',
            name='image_url',
            field=models.URLField(max_length=1024, null=True, blank=True),
        ),
    ] 