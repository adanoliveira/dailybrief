"""
Management command to configure the default digest strategy.

This command allows administrators to switch the default digest generation
strategy between events-based and articles-based approaches.
"""

import logging
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from apps.content.digest.services import DigestService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = """
    Configure the default digest generation strategy.
    
    Examples:
    - Set articles-based as default: --strategy articles_based
    - Set events-based as default: --strategy events_based
    - Show current configuration: --show-current
    - List available strategies: --list
    """
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--strategy',
            type=str,
            choices=['events_based', 'articles_based'],
            help='Set the default digest strategy'
        )
        
        parser.add_argument(
            '--show-current',
            action='store_true',
            help='Show current default strategy'
        )
        
        parser.add_argument(
            '--list',
            action='store_true',
            help='List all available strategies'
        )
        
        parser.add_argument(
            '--validate',
            action='store_true',
            help='Validate strategy configuration'
        )
    
    def handle(self, *args, **options):
        """Main command handler."""
        
        digest_service = DigestService()
        
        if options['list']:
            self._list_strategies(digest_service)
            return
        
        if options['show_current']:
            self._show_current_strategy(digest_service)
            return
        
        if options['validate']:
            self._validate_configuration(digest_service)
            return
        
        if options['strategy']:
            self._set_strategy(digest_service, options['strategy'])
            return
        
        # Default: show current configuration
        self._show_current_strategy(digest_service)
    
    def _list_strategies(self, digest_service: DigestService):
        """List all available strategies."""
        self.stdout.write(self.style.SUCCESS('📋 Available Digest Strategies:'))
        
        strategies = digest_service.get_available_strategies()
        current_default = digest_service.get_current_default_strategy()
        
        for key, name in strategies.items():
            is_default = " ✅ [CURRENT DEFAULT]" if key == current_default else ""
            self.stdout.write(f"  • {key}: {name}{is_default}")
        
        self.stdout.write(f"\n💡 Use --strategy <key> to change the default strategy")
    
    def _show_current_strategy(self, digest_service: DigestService):
        """Show current default strategy."""
        current_strategy = digest_service.get_current_default_strategy()
        strategies = digest_service.get_available_strategies()
        strategy_name = strategies.get(current_strategy, 'Unknown')
        
        self.stdout.write(self.style.SUCCESS('🎯 Current Default Digest Strategy:'))
        self.stdout.write(f"  Strategy: {current_strategy}")
        self.stdout.write(f"  Name: {strategy_name}")
        
        # Check if overridden in Django settings
        settings_override = getattr(settings, 'DIGEST_DEFAULT_STRATEGY', None)
        if settings_override and settings_override != current_strategy:
            self.stdout.write(
                self.style.WARNING(
                    f"⚠️  Note: Django settings override detected: {settings_override}"
                )
            )
        
        self.stdout.write(f"\n💡 To change strategy, use: --strategy <new_strategy>")
    
    def _set_strategy(self, digest_service: DigestService, strategy_key: str):
        """Set the default strategy."""
        
        self.stdout.write(f"🔄 Setting default strategy to: {strategy_key}")
        
        # Validate strategy exists
        strategies = digest_service.get_available_strategies()
        if strategy_key not in strategies:
            raise CommandError(f"Unknown strategy: {strategy_key}")
        
        # Check current strategy
        current_strategy = digest_service.get_current_default_strategy()
        if current_strategy == strategy_key:
            self.stdout.write(
                self.style.WARNING(f"⚠️  Strategy {strategy_key} is already the default")
            )
            return
        
        # Set new strategy
        success = digest_service.set_default_strategy(strategy_key)
        
        if success:
            strategy_name = strategies[strategy_key]
            self.stdout.write(
                self.style.SUCCESS(
                    f"✅ Default strategy changed to: {strategy_key} ({strategy_name})"
                )
            )
            
            # Show recommendation about Django settings
            self.stdout.write("\n💡 Recommendation:")
            self.stdout.write(
                f"   Add this to your Django settings.py to persist the change:"
            )
            self.stdout.write(f"   DIGEST_DEFAULT_STRATEGY = '{strategy_key}'")
            
            # Warn about temporary nature
            self.stdout.write(
                self.style.WARNING(
                    "\n⚠️  Note: This change is temporary and will reset on server restart."
                )
            )
            self.stdout.write(
                "   To make it permanent, update your Django settings file."
            )
        else:
            raise CommandError(f"Failed to set strategy: {strategy_key}")
    
    def _validate_configuration(self, digest_service: DigestService):
        """Validate the current digest strategy configuration."""
        self.stdout.write(self.style.SUCCESS('🔍 Validating Digest Strategy Configuration...'))
        
        try:
            # Test service initialization
            strategies = digest_service.get_available_strategies()
            current_strategy = digest_service.get_current_default_strategy()
            
            self.stdout.write(f"✅ DigestService initialized successfully")
            self.stdout.write(f"✅ Found {len(strategies)} available strategies")
            self.stdout.write(f"✅ Current default strategy: {current_strategy}")
            
            # Validate each strategy can be instantiated
            for strategy_key in strategies.keys():
                try:
                    # Temporarily set and test strategy
                    original_strategy = digest_service.get_current_default_strategy()
                    digest_service.set_default_strategy(strategy_key)
                    
                    # Test router with this strategy
                    router = digest_service.router
                    test_user = type('MockUser', (), {'username': 'test'})()  # Mock user
                    test_preferences = {'digest_strategy': strategy_key}
                    
                    strategy_instance = router.get_strategy_for_user(test_user, test_preferences)
                    strategy_name = strategy_instance.get_strategy_name()
                    
                    self.stdout.write(f"✅ Strategy '{strategy_key}' ({strategy_name}) is valid")
                    
                    # Restore original strategy
                    digest_service.set_default_strategy(original_strategy)
                    
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"❌ Strategy '{strategy_key}' validation failed: {e}")
                    )
            
            # Check Django settings
            settings_override = getattr(settings, 'DIGEST_DEFAULT_STRATEGY', None)
            if settings_override:
                if settings_override in strategies:
                    self.stdout.write(f"✅ Django settings override is valid: {settings_override}")
                else:
                    self.stdout.write(
                        self.style.ERROR(
                            f"❌ Django settings override is invalid: {settings_override}"
                        )
                    )
            else:
                self.stdout.write("ℹ️  No Django settings override configured")
            
            self.stdout.write(self.style.SUCCESS("\n🎉 Configuration validation completed successfully!"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Configuration validation failed: {e}"))
            raise CommandError("Digest strategy configuration is invalid") 