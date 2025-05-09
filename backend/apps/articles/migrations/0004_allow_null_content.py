from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('articles', '0003_increase_url_length'),
    ]

    operations = [
        migrations.AlterField(
            model_name='article',
            name='content',
            field=models.TextField(blank=True, null=True),
        ),
    ] 