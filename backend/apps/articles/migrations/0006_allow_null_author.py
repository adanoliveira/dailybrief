from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('articles', '0005_allow_null_description'),
    ]

    operations = [
        migrations.AlterField(
            model_name='article',
            name='author',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='article',
            name='source_name',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ] 