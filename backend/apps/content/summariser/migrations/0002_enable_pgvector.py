# Generated manually for pgvector integration

from django.db import migrations
from pgvector.django import VectorExtension


class Migration(migrations.Migration):

    dependencies = [
        ('summariser', '0001_initial'),
    ]

    operations = [
        VectorExtension(),
    ] 