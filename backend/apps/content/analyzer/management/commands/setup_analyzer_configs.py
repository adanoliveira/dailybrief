"""
Management command to set up AI provider configurations for analyzer operations.

This creates the necessary AIProviderConfig entries for all analyzer stages.
"""
from django.core.management.base import BaseCommand
from apps.aiproviders.models import AIProviderConfig
from apps.content.analyzer.prompt_templates import AnalyzerPrompts


class Command(BaseCommand):
    help = 'Set up AI provider configurations for analyzer operations'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force update existing configurations'
        )
    
    def handle(self, *args, **options):
        """Create AI provider configurations for analyzer operations."""
        force = options.get('force', False)
        
        # Define analyzer operations
        analyzer_operations = [
            'linguistic_analysis',
            'entity_extraction', 
            'event_detection',
            'topic_classification',
            'region_classification'
        ]
        
        created_count = 0
        updated_count = 0
        skipped_count = 0
        
        for operation in analyzer_operations:
            # Get metadata from prompt templates
            metadata = AnalyzerPrompts.get_prompt_metadata(operation)
            
            if not metadata:
                self.stdout.write(
                    self.style.WARNING(f'No metadata found for operation: {operation}')
                )
                continue
            
            # Check if config already exists
            existing_config = AIProviderConfig.objects.filter(operation=operation).first()
            
            if existing_config and not force:
                self.stdout.write(
                    self.style.WARNING(f'Configuration for {operation} already exists (use --force to update)')
                )
                skipped_count += 1
                continue
            
            # Create or update configuration
            config_data = {
                'provider': 'openai',
                'model': metadata['model_preference'],
                'operation': operation,
                'is_active': True,
                'config': {
                    'max_tokens': metadata['max_tokens'],
                    'temperature': metadata['temperature'],
                    'description': metadata['description'],
                    'template_version': metadata['template_version'],
                    'response_format': 'json',
                    'timeout': 30,
                    'max_retries': 3
                }
            }
            
            if existing_config:
                # Update existing
                for key, value in config_data.items():
                    setattr(existing_config, key, value)
                existing_config.save()
                updated_count += 1
                
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Updated configuration for {operation}')
                )
            else:
                # Create new
                AIProviderConfig.objects.create(**config_data)
                created_count += 1
                
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created configuration for {operation}')
                )
        
        # Summary
        self.stdout.write('\n' + '='*50)
        self.stdout.write('AI Provider Configuration Setup Summary:')
        self.stdout.write(f'  Created: {created_count}')
        self.stdout.write(f'  Updated: {updated_count}')
        self.stdout.write(f'  Skipped: {skipped_count}')
        
        if created_count > 0 or updated_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'\n✓ Analyzer AI configurations are ready!')
            )
        
        # Show current configurations
        self.stdout.write('\nCurrent Analyzer Configurations:')
        configs = AIProviderConfig.objects.filter(
            operation__in=analyzer_operations
        ).order_by('operation')
        
        for config in configs:
            status = '✓ Active' if config.is_active else '✗ Inactive'
            self.stdout.write(f'  - {config.operation}: {config.provider}/{config.model} ({status})') 