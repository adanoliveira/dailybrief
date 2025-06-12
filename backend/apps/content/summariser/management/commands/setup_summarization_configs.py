"""
Management command to set up AI provider configurations for summarization.

Creates the necessary AIProviderConfig entries for all summarization pipeline stages.
"""
from django.core.management.base import BaseCommand
from apps.aiproviders.models import AIProviderConfig


class Command(BaseCommand):
    help = 'Set up AI provider configurations for article summarization pipeline'
    
    def handle(self, *args, **options):
        self.stdout.write("Setting up AI provider configurations for summarization...")
        
        # RBC Compression Configuration
        rbc_config, created = AIProviderConfig.objects.get_or_create(
            operation='rbc_compression',
            defaults={
                'provider': 'openai',
                'model': 'gpt-4o-mini',
                'config': {
                    'temperature': 0.3,
                    'max_tokens': 1000,
                    'description': 'Rich Bullet Compression stage of summarization pipeline'
                },
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f"✓ Created RBC compression config: {rbc_config.model}")
            )
        else:
            self.stdout.write(f"- RBC compression config already exists: {rbc_config.model}")
        
        # Skeleton Summary Configuration
        summary_config, created = AIProviderConfig.objects.get_or_create(
            operation='skeleton_summary',
            defaults={
                'provider': 'openai',
                'model': 'gpt-4o-mini',
                'config': {
                    'temperature': 0.3,
                    'max_tokens': 800,
                    'description': 'Skeleton summary generation stage'
                },
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f"✓ Created skeleton summary config: {summary_config.model}")
            )
        else:
            self.stdout.write(f"- Skeleton summary config already exists: {summary_config.model}")
        
        # Critic Review Configuration
        critic_config, created = AIProviderConfig.objects.get_or_create(
            operation='summary_critique',
            defaults={
                'provider': 'openai',
                'model': 'gpt-4o-mini',
                'config': {
                    'temperature': 0.1,
                    'max_tokens': 500,
                    'description': 'Summary critique and quality review stage'
                },
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f"✓ Created critic review config: {critic_config.model}")
            )
        else:
            self.stdout.write(f"- Critic review config already exists: {critic_config.model}")
        
        # Summary Repair Configuration
        repair_config, created = AIProviderConfig.objects.get_or_create(
            operation='summary_repair',
            defaults={
                'provider': 'openai',
                'model': 'gpt-4o-mini',
                'config': {
                    'temperature': 0.2,
                    'max_tokens': 800,
                    'description': 'Summary repair and improvement stage'
                },
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f"✓ Created summary repair config: {repair_config.model}")
            )
        else:
            self.stdout.write(f"- Summary repair config already exists: {repair_config.model}")
        
        # Embedding Generation Configuration
        embedding_config, created = AIProviderConfig.objects.get_or_create(
            operation='embedding_generation',
            defaults={
                'provider': 'openai',
                'model': 'text-embedding-3-small',  # Note: text-embedding-4-small not available yet
                'config': {
                    'dimensions': 1536,
                    'batch_size': 50,
                    'description': 'Semantic embedding generation for article similarity search'
                },
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f"✓ Created embedding generation config: {embedding_config.model}")
            )
        else:
            self.stdout.write(f"- Embedding generation config already exists: {embedding_config.model}")
        
        self.stdout.write(
            self.style.SUCCESS("\n✓ AI provider configuration setup completed!")
        ) 