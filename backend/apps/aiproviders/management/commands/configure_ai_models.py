"""
Configure AI Models

Management command to view and configure which models are used
for different AI operations in the system.
"""
from django.core.management.base import BaseCommand
from apps.aiproviders.models import AIProviderConfig


class Command(BaseCommand):
    help = 'Configure AI models for different operations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--list',
            action='store_true',
            help='List current AI provider configurations'
        )
        parser.add_argument(
            '--set',
            type=str,
            help='Set configuration in format: operation:provider:model (e.g., quality_assessment:openai:gpt-4.1-mini)'
        )
        parser.add_argument(
            '--operation',
            type=str,
            choices=['quality_assessment', 'summarization', 'digest_generation', 'translation', 'content_extraction'],
            help='Operation to configure'
        )
        parser.add_argument(
            '--provider',
            type=str,
            choices=['openai', 'anthropic'],
            help='AI provider to use'
        )
        parser.add_argument(
            '--model',
            type=str,
            help='Model name to use (e.g., gpt-4.1-mini, gpt-4.1, gpt-4.1-nano)'
        )
        parser.add_argument(
            '--activate',
            type=str,
            help='Activate configuration for operation'
        )
        parser.add_argument(
            '--deactivate',
            type=str,
            help='Deactivate configuration for operation'
        )

    def handle(self, *args, **options):
        if options['list']:
            self._list_configurations()
        elif options['set']:
            self._parse_and_set_configuration(options['set'])
        elif options['operation'] and options['provider'] and options['model']:
            self._set_configuration(
                options['operation'], 
                options['provider'], 
                options['model']
            )
        elif options['activate']:
            self._activate_configuration(options['activate'])
        elif options['deactivate']:
            self._deactivate_configuration(options['deactivate'])
        else:
            self._list_configurations()
            self.stdout.write("\n" + self.style.WARNING('Usage examples:'))
            self.stdout.write("  🔍 List configurations: --list")
            self.stdout.write("  ⚙️  Set configuration: --operation quality_assessment --provider openai --model gpt-4.1-mini")
            self.stdout.write("  🚀 Quick set: --set quality_assessment:openai:gpt-4.1-mini")
            self.stdout.write("  ✅ Activate: --activate quality_assessment")
            self.stdout.write("  ❌ Deactivate: --deactivate quality_assessment")

    def _list_configurations(self):
        """List all AI provider configurations."""
        self.stdout.write(
            self.style.SUCCESS('🤖 AI Provider Configurations')
        )
        
        configs = AIProviderConfig.objects.all().order_by('operation')
        
        if not configs:
            self.stdout.write(
                self.style.WARNING('No configurations found. Create one first!')
            )
            return
        
        self.stdout.write(f"\n{'Operation':<20} {'Provider':<12} {'Model':<20} {'Status':<8} {'Updated'}")
        self.stdout.write("-" * 80)
        
        for config in configs:
            status = "✅ Active" if config.is_active else "❌ Inactive"
            status_style = self.style.SUCCESS if config.is_active else self.style.ERROR
            
            self.stdout.write(
                f"{config.operation:<20} "
                f"{config.provider:<12} "
                f"{config.model:<20} "
                f"{status_style(status):<8} "
                f"{config.updated_at.strftime('%Y-%m-%d %H:%M')}"
            )
        
        # Show current models for common operations
        self.stdout.write(f"\n📊 Current Models:")
        for operation in ['quality_assessment', 'content_extraction', 'summarization', 'digest_generation']:
            config = AIProviderConfig.objects.filter(
                operation=operation, 
                is_active=True
            ).first()
            
            if config:
                self.stdout.write(f"   🔸 {operation}: {config.provider}/{config.model}")
            else:
                self.stdout.write(
                    self.style.WARNING(f"   ⚠️  {operation}: Not configured")
                )

    def _parse_and_set_configuration(self, config_string):
        """Parse configuration string and set it."""
        try:
            operation, provider, model = config_string.split(':')
            self._set_configuration(operation, provider, model)
        except ValueError:
            self.stdout.write(
                self.style.ERROR('Invalid format. Use: operation:provider:model')
            )

    def _set_configuration(self, operation, provider, model):
        """Set AI provider configuration."""
        # Validate operation
        valid_operations = [choice[0] for choice in AIProviderConfig.OPERATION_TYPES]
        if operation not in valid_operations:
            self.stdout.write(
                self.style.ERROR(f'Invalid operation. Choose from: {", ".join(valid_operations)}')
            )
            return
        
        # Validate provider
        valid_providers = [choice[0] for choice in AIProviderConfig.PROVIDER_CHOICES]
        if provider not in valid_providers:
            self.stdout.write(
                self.style.ERROR(f'Invalid provider. Choose from: {", ".join(valid_providers)}')
            )
            return
        
        # Create or update configuration
        config, created = AIProviderConfig.objects.update_or_create(
            operation=operation,
            defaults={
                'provider': provider,
                'model': model,
                'is_active': True,
                'config': {}
            }
        )
        
        action = "Created" if created else "Updated"
        self.stdout.write(
            self.style.SUCCESS(f'✅ {action} configuration: {operation} → {provider}/{model}')
        )
        
        # Show cost estimate for quality assessment and content extraction
        if operation in ['quality_assessment', 'content_extraction']:
            self._show_cost_estimate(model, operation)

    def _activate_configuration(self, operation):
        """Activate configuration for operation."""
        try:
            config = AIProviderConfig.objects.get(operation=operation)
            config.is_active = True
            config.save()
            self.stdout.write(
                self.style.SUCCESS(f'✅ Activated {operation} configuration')
            )
        except AIProviderConfig.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Configuration for {operation} not found')
            )

    def _deactivate_configuration(self, operation):
        """Deactivate configuration for operation."""
        try:
            config = AIProviderConfig.objects.get(operation=operation)
            config.is_active = False
            config.save()
            self.stdout.write(
                self.style.WARNING(f'⚠️ Deactivated {operation} configuration')
            )
        except AIProviderConfig.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Configuration for {operation} not found')
            )

    def _show_cost_estimate(self, model, operation='quality_assessment'):
        """Show cost estimate for AI operations."""
        if operation == 'quality_assessment':
            self.stdout.write(f"\n💰 Cost Estimates (per 1000 evaluations):")
            # Typical quality assessment: ~8000 input tokens, ~800 output tokens
            typical_input = 8000
            typical_output = 800
        elif operation == 'content_extraction':
            self.stdout.write(f"\n💰 Cost Estimates (per 1000 extractions):")
            # Typical content extraction: ~15000 input tokens, ~2000 output tokens
            typical_input = 15000
            typical_output = 2000
        else:
            return
        
        model_lower = model.lower()
        
        if 'gpt-4.1' in model_lower:
            if 'nano' in model_lower:
                # GPT-4.1 Nano: $0.10/1M input, $0.40/1M output
                cost_per_eval = (typical_input * 0.0000001) + (typical_output * 0.0000004)
                cost_1k = cost_per_eval * 1000
                suffix = "evaluation" if operation == 'quality_assessment' else "extraction"
                self.stdout.write(f"   🟢 GPT-4.1 Nano: ~${cost_1k:.2f} (${cost_per_eval:.6f} per {suffix})")
            elif 'mini' in model_lower:
                # GPT-4.1 Mini: $0.40/1M input, $1.60/1M output
                cost_per_eval = (typical_input * 0.0000004) + (typical_output * 0.0000016)
                cost_1k = cost_per_eval * 1000
                suffix = "evaluation" if operation == 'quality_assessment' else "extraction"
                self.stdout.write(f"   🟡 GPT-4.1 Mini: ~${cost_1k:.2f} (${cost_per_eval:.6f} per {suffix})")
            else:
                # GPT-4.1 (full): $2.00/1M input, $8.00/1M output
                cost_per_eval = (typical_input * 0.000002) + (typical_output * 0.000008)
                cost_1k = cost_per_eval * 1000
                suffix = "evaluation" if operation == 'quality_assessment' else "extraction"
                self.stdout.write(f"   🔴 GPT-4.1 Full: ~${cost_1k:.2f} (${cost_per_eval:.6f} per {suffix})")
        elif 'gpt-4o-mini' in model_lower:
            # GPT-4o-mini: $0.15/1M input, $0.075/1M output
            cost_per_eval = (typical_input * 0.00000015) + (typical_output * 0.000000075)
            cost_1k = cost_per_eval * 1000
            suffix = "evaluation" if operation == 'quality_assessment' else "extraction"
            self.stdout.write(f"   💚 GPT-4o-mini: ~${cost_1k:.2f} (${cost_per_eval:.6f} per {suffix})")
        
        self.stdout.write(f"   📊 Based on ~{typical_input:,} input + {typical_output:,} output tokens per {suffix}") 