from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('articles', '0004_allow_null_content'),
    ]

    operations = [
        migrations.AlterField(
            model_name='article',
            name='description',
            field=models.TextField(blank=True, null=True),
        ),
    ] 