from django.db import migrations
from pgvector.django import VectorField

def clear_embeddings(apps, schema_editor):
    Entity = apps.get_model('analyzer', 'Entity')
    Entity.objects.all().update(embedding=None)

class Migration(migrations.Migration):
    dependencies = [
        ('analyzer', '0002_remove_duplicate_fields'),  # Updated to correct previous migration
    ]

    operations = [
        # First clear existing embeddings
        migrations.RunPython(clear_embeddings),
        
        # Then alter the field
        migrations.AlterField(
            model_name='entity',
            name='embedding',
            field=VectorField(
                blank=True,
                dimensions=1536,
                help_text='1536-dimensional OpenAI vector for semantic similarity',
                null=True
            ),
        ),
    ] 