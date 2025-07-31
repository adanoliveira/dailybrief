import os
import json
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import transaction
from apps.aiproviders.models import AIProviderConfig

class Command(BaseCommand):
    help = 'Seeds production/staging database with AI provider configurations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force reload even if configurations exist',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be loaded without making changes',
        )

    def handle(self, *args, **options):
        # Use fixtures directory
        fixtures_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            'fixtures'
        )
        config_file = os.path.join(fixtures_dir, 'ai_provider_config.json')
        
        force = options.get('force', False)
        dry_run = options.get('dry-run', False)
        
        self.stdout.write("🤖 AI Provider Configuration Seeding")
        self.stdout.write(f"   Config file: {config_file}")
        self.stdout.write(f"   Force reload: {force}")
        self.stdout.write(f"   Dry run: {dry_run}")
        
        if not os.path.exists(config_file):
            self.stdout.write(
                self.style.ERROR(f"Configuration file not found: {config_file}")
            )
            return
        
        # Check existing data
        existing_count = AIProviderConfig.objects.count()
        self.stdout.write(f"   Existing configurations: {existing_count}")
        
        if existing_count > 0 and not force:
            self.stdout.write(
                self.style.WARNING(
                    "AI provider configurations already exist. Use --force to reload."
                )
            )
            return
        
        with transaction.atomic():
            self.load_ai_config(config_file, force, dry_run)
    
    def load_ai_config(self, config_file, force=False, dry_run=False):
        """Load AI provider configurations from fixture file."""
        
        self.stdout.write(f"\n📂 Loading AI provider configurations...")
        
        # Load and parse the fixture file
        try:
            with open(config_file, 'r') as f:
                data = json.load(f)
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Failed to load config file: {e}")
            )
            return
        
        if not isinstance(data, list):
            self.stdout.write(
                self.style.ERROR("Config file should contain a list of configurations")
            )
            return
        
        self.stdout.write(f"   Found {len(data)} configurations in file")
        
        if dry_run:
            self.stdout.write(self.style.WARNING("\n🧪 DRY RUN - No changes will be made"))
            for item in data:
                fields = item.get('fields', {})
                self.stdout.write(
                    f"   Would create: {fields.get('operation')} → "
                    f"{fields.get('provider')}/{fields.get('model')} "
                    f"(active: {fields.get('is_active')})"
                )
            return
        
        # Clear existing data if force reload
        if force:
            deleted_count = AIProviderConfig.objects.count()
            AIProviderConfig.objects.all().delete()
            self.stdout.write(f"   🗑️  Cleared {deleted_count} existing configurations")
        
        # Load configurations
        created_count = 0
        updated_count = 0
        
        for item in data:
            if item.get('model') != 'aiproviders.aiproviderconfig':
                continue
                
            fields = item.get('fields', {})
            operation = fields.get('operation')
            
            if not operation:
                self.stdout.write(
                    self.style.WARNING(f"   ⚠️  Skipping item without operation")
                )
                continue
            
            # Create or update configuration
            config, created = AIProviderConfig.objects.update_or_create(
                operation=operation,
                defaults={
                    'provider': fields.get('provider'),
                    'model': fields.get('model'),
                    'config': fields.get('config', {}),
                    'is_active': fields.get('is_active', True),
                }
            )
            
            if created:
                created_count += 1
                status = "✅ Created"
            else:
                updated_count += 1
                status = "🔄 Updated"
            
            self.stdout.write(
                f"   {status}: {operation} → {config.provider}/{config.model} "
                f"(active: {config.is_active})"
            )
        
        # Summary
        self.stdout.write(f"\n📊 Summary:")
        self.stdout.write(f"   Created: {created_count} configurations")
        self.stdout.write(f"   Updated: {updated_count} configurations")
        self.stdout.write(f"   Total: {created_count + updated_count} configurations")
        
        # Show current active configurations
        self.stdout.write(f"\n🔧 Active Configurations:")
        active_configs = AIProviderConfig.objects.filter(is_active=True).order_by('operation')
        for config in active_configs:
            self.stdout.write(f"   🔸 {config.operation}: {config.provider}/{config.model}")
        
        if not active_configs:
            self.stdout.write("   ⚠️  No active configurations found!")
        
        self.stdout.write(
            self.style.SUCCESS("\n✅ AI provider configuration seeding completed!")
        ) 