# Generated manually for Step 1/Step 2 refactor

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('articles', '0009_auto_20250528_1707'),
    ]

    operations = [
        # Add Step 1 (Fetch) fields
        migrations.AddField(
            model_name='article',
            name='raw_html',
            field=models.TextField(blank=True, help_text='Full raw HTML content for Step 2 processing'),
        ),
        migrations.AddField(
            model_name='article',
            name='basic_content',
            field=models.TextField(blank=True, help_text='Quick extracted text for immediate display'),
        ),
        migrations.AddField(
            model_name='article',
            name='extraction_metadata',
            field=models.JSONField(default=dict, help_text='Basic extraction metadata from Step 1'),
        ),
        migrations.AddField(
            model_name='article',
            name='fetch_status',
            field=models.CharField(
                choices=[
                    ('pending', 'Pending'),
                    ('fetching', 'Fetching'),
                    ('completed', 'Completed'),
                    ('failed', 'Failed')
                ],
                default='pending',
                max_length=20,
                db_index=True,
                help_text='Step 1 fetch status'
            ),
        ),
        migrations.AddField(
            model_name='article',
            name='fetch_strategy_used',
            field=models.CharField(blank=True, max_length=50, help_text='Strategy used for content extraction'),
        ),
        migrations.AddField(
            model_name='article',
            name='fetch_duration_ms',
            field=models.IntegerField(blank=True, null=True, help_text='Time taken for content extraction in milliseconds'),
        ),
        migrations.AddField(
            model_name='article',
            name='fetch_attempts',
            field=models.IntegerField(default=0, help_text='Number of fetch attempts made'),
        ),
        migrations.AddField(
            model_name='article',
            name='paywall_detected',
            field=models.BooleanField(default=False, help_text='Whether paywall was detected during extraction'),
        ),
        migrations.AddField(
            model_name='article',
            name='paywall_indicators',
            field=models.JSONField(default=list, help_text='List of paywall indicators found'),
        ),
        
        # Add Step 2 (Process) fields
        migrations.AddField(
            model_name='article',
            name='process_status',
            field=models.CharField(
                choices=[
                    ('pending', 'Pending'),
                    ('processing', 'Processing'),
                    ('completed', 'Completed'),
                    ('failed', 'Failed')
                ],
                default='pending',
                max_length=20,
                db_index=True,
                help_text='Step 2 processing status'
            ),
        ),
        migrations.AddField(
            model_name='article',
            name='process_route',
            field=models.CharField(
                blank=True,
                choices=[
                    ('safari_mode', 'Safari Reader Mode'),
                    ('llm_enhanced', 'LLM Enhanced'),
                    ('hybrid', 'Hybrid Processing')
                ],
                max_length=20,
                null=True,
                help_text='Processing route used in Step 2'
            ),
        ),
        migrations.AddField(
            model_name='article',
            name='clean_content',
            field=models.TextField(blank=True, help_text='Clean processed content from Step 2'),
        ),
        migrations.AddField(
            model_name='article',
            name='content_blocks',
            field=models.JSONField(default=list, help_text='Structured content blocks from Step 2 processing'),
        ),
        migrations.AddField(
            model_name='article',
            name='extracted_metadata',
            field=models.JSONField(default=dict, help_text='Enhanced metadata extracted during Step 2 processing'),
        ),
        migrations.AddField(
            model_name='article',
            name='content_quality_metrics',
            field=models.JSONField(default=dict, help_text='Quality assessment metrics from Step 2 processing'),
        ),
        migrations.AddField(
            model_name='article',
            name='process_duration_ms',
            field=models.IntegerField(blank=True, null=True, help_text='Time taken for Step 2 processing in milliseconds'),
        ),
        migrations.AddField(
            model_name='article',
            name='process_cost_usd',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=8, null=True, help_text='Cost of Step 2 processing in USD'),
        ),
        migrations.AddField(
            model_name='article',
            name='process_attempts',
            field=models.IntegerField(default=0, help_text='Number of processing attempts made'),
        ),
        migrations.AddField(
            model_name='article',
            name='last_process_attempt',
            field=models.DateTimeField(blank=True, null=True, help_text='Timestamp of last processing attempt'),
        ),
        migrations.AddField(
            model_name='article',
            name='process_error_message',
            field=models.TextField(blank=True, help_text='Error message from failed processing attempts'),
        ),
        
        # Rename existing fetch_error_message field to match new structure
        migrations.RenameField(
            model_name='article',
            old_name='fetch_error_message',
            new_name='fetch_error_message_old',
        ),
        migrations.AddField(
            model_name='article',
            name='fetch_error_message',
            field=models.TextField(blank=True, help_text='Error message from failed fetch attempts'),
        ),
        
        # Remove old legacy fields that are no longer needed
        migrations.RemoveField(
            model_name='article',
            name='content_status',
        ),
        migrations.RemoveField(
            model_name='article',
            name='content_fetch_attempts',
        ),
        migrations.RemoveField(
            model_name='article',
            name='max_fetch_attempts',
        ),
        migrations.RemoveField(
            model_name='article',
            name='content_completeness',
        ),
        migrations.RemoveField(
            model_name='article',
            name='content_quality_score',
        ),
        migrations.RemoveField(
            model_name='article',
            name='rich_content',
        ),
        migrations.RemoveField(
            model_name='article',
            name='media_assets',
        ),
        migrations.RemoveField(
            model_name='article',
            name='formatting_data',
        ),
        migrations.RemoveField(
            model_name='article',
            name='content_structure',
        ),
        migrations.RemoveField(
            model_name='article',
            name='formatting_score',
        ),
        migrations.RemoveField(
            model_name='article',
            name='processing_status',
        ),
        migrations.RemoveField(
            model_name='article',
            name='processing_attempts',
        ),
        migrations.RemoveField(
            model_name='article',
            name='last_processing_attempt',
        ),
        migrations.RemoveField(
            model_name='article',
            name='use_description_as_content',
        ),
        migrations.RemoveField(
            model_name='article',
            name='content_source',
        ),
        migrations.RemoveField(
            model_name='article',
            name='fetch_error_message_old',
        ),
    ] 