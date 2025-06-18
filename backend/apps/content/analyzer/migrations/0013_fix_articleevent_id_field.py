# Generated manually to fix ArticleEvent id field issue

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('analyzer', '0012_convert_to_many_events_per_article'),
        ('articles', '0001_initial'),
    ]

    operations = [
        # This is a state-only migration that tells Django the ArticleEvent model
        # now has an explicit id field, without actually creating it in the database
        # (since it already exists from the previous manual migration)
        migrations.SeparateDatabaseAndState(
            state_operations=[
                # Update the model state to include the explicit id field
                migrations.AlterField(
                    model_name='articleevent',
                    name='id',
                    field=models.AutoField(primary_key=True),
                ),
                # Update indexes to match the current model definition
                migrations.AlterModelOptions(
                    name='articleevent',
                    options={},
                ),
                migrations.AlterIndexTogether(
                    name='articleevent',
                    index_together=set(),
                ),
                migrations.AddIndex(
                    model_name='articleevent',
                    index=models.Index(fields=['article'], name='analyzer_ar_article_8a4e2c_idx'),
                ),
                migrations.AddIndex(
                    model_name='articleevent',
                    index=models.Index(fields=['event'], name='analyzer_ar_event_i_76e54d_idx'),
                ),
                migrations.AddIndex(
                    model_name='articleevent',
                    index=models.Index(fields=['is_primary'], name='analyzer_ar_is_prim_e80111_idx'),
                ),
            ],
            database_operations=[
                # No database operations - the field and indexes already exist
            ],
        ),
    ] 