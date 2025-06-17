# Generated manually for converting ArticleEvent to support multiple events per article

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('analyzer', '0011_add_article_event_fields'),
        ('articles', '0001_initial'),
    ]

    operations = [
        # Step 1: Remove the primary key constraint from article field
        migrations.RunSQL(
            "ALTER TABLE analyzer_article_event DROP CONSTRAINT analyzer_article_event_pkey;",
            reverse_sql="ALTER TABLE analyzer_article_event ADD CONSTRAINT analyzer_article_event_pkey PRIMARY KEY (article_id);"
        ),
        
        # Step 2: Add an auto-incrementing id field as the new primary key
        migrations.RunSQL(
            "ALTER TABLE analyzer_article_event ADD COLUMN id SERIAL PRIMARY KEY;",
            reverse_sql="ALTER TABLE analyzer_article_event DROP COLUMN id;"
        ),
        
        # Step 3: Change article field from OneToOneField to ForeignKey (remove unique constraint)
        migrations.RunSQL(
            "ALTER TABLE analyzer_article_event DROP CONSTRAINT IF EXISTS analyzer_article_event_article_id_key;",
            reverse_sql="ALTER TABLE analyzer_article_event ADD CONSTRAINT analyzer_article_event_article_id_key UNIQUE (article_id);"
        ),
        
        # Step 4: Add unique constraint for article+event combination
        migrations.RunSQL(
            "ALTER TABLE analyzer_article_event ADD CONSTRAINT unique_article_event UNIQUE (article_id, event_id);",
            reverse_sql="ALTER TABLE analyzer_article_event DROP CONSTRAINT unique_article_event;"
        ),
        
        # Step 5: Add indexes for better performance
        migrations.RunSQL(
            """
            CREATE INDEX IF NOT EXISTS analyzer_article_event_article_idx ON analyzer_article_event (article_id);
            CREATE INDEX IF NOT EXISTS analyzer_article_event_event_idx ON analyzer_article_event (event_id);
            """,
            reverse_sql="""
            DROP INDEX IF EXISTS analyzer_article_event_article_idx;
            DROP INDEX IF EXISTS analyzer_article_event_event_idx;
            """
        ),
    ] 