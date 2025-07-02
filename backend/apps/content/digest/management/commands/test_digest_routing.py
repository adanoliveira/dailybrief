"""
Management command to test the new digest routing system.

This command demonstrates how to:
- Switch between different digest strategies
- Test both events-based and articles-based approaches
- Compare strategy performance
- Validate the routing mechanism
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.utils import timezone

from apps.content.digest.services import DigestService
from apps.content.digest.services.digest_router import DigestRouter
from apps.content.digest.models import Digest, DigestTopic

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = """
    Test the digest routing system and strategy switching.
    
    Examples:
    - Test both strategies for user: --user-id 123 --test-both
    - Test specific strategy: --user-id 123 --strategy articles_based
    - Compare strategies: --user-id 123 --compare
    - Show available strategies: --list-strategies
    """
    
    def add_arguments(self, parser):
        # User selection
        parser.add_argument(
            '--user-id',
            type=int,
            help='Test digest generation for specific user ID'
        )
        
        parser.add_argument(
            '--username',
            type=str,
            help='Test digest generation for specific username'
        )
        
        # Strategy options
        parser.add_argument(
            '--strategy',
            type=str,
            choices=['events_based', 'articles_based'],
            help='Test specific strategy'
        )
        
        parser.add_argument(
            '--test-both',
            action='store_true',
            help='Test both strategies sequentially'
        )
        
        parser.add_argument(
            '--compare',
            action='store_true',
            help='Compare both strategies side by side'
        )
        
        parser.add_argument(
            '--list-strategies',
            action='store_true',
            help='List available strategies and current default'
        )
        
        # Date and options
        parser.add_argument(
            '--date',
            type=str,
            help='Target date for digest (YYYY-MM-DD format, defaults to today)'
        )
        
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Validate setup without generating digests'
        )
    
    def handle(self, *args, **options):
        """Main command handler."""
        
        if options['list_strategies']:
            self._list_strategies()
            return
        
        if options['dry_run']:
            self._run_validation(options)
            return
        
        # Parse target date
        target_date = self._parse_target_date(options['date'])
        
        # Get target user
        user = self._get_target_user(options)
        if not user:
            raise CommandError("Must specify either --user-id or --username")
        
        # Initialize services
        digest_service = DigestService()
        
        self.stdout.write(self.style.SUCCESS('🧪 Testing Digest Routing System'))
        self.stdout.write(f"👤 User: {user.username}")
        self.stdout.write(f"📅 Date: {target_date.strftime('%Y-%m-%d')}")
        
        if options['compare']:
            self._compare_strategies(digest_service, user, target_date)
        elif options['test_both']:
            self._test_both_strategies(digest_service, user, target_date)
        elif options['strategy']:
            self._test_specific_strategy(digest_service, user, target_date, options['strategy'])
        else:
            self._test_default_strategy(digest_service, user, target_date)
    
    def _list_strategies(self):
        """List available strategies and current default."""
        digest_service = DigestService()
        
        self.stdout.write(self.style.SUCCESS('📋 Available Digest Strategies:'))
        
        strategies = digest_service.get_available_strategies()
        current_default = digest_service.get_current_default_strategy()
        
        for key, name in strategies.items():
            is_default = "✅ [DEFAULT]" if key == current_default else ""
            self.stdout.write(f"  • {key}: {name} {is_default}")
        
        self.stdout.write(f"\n🎯 Current Default: {current_default}")
    
    def _test_default_strategy(self, digest_service: DigestService, user: User, target_date: datetime):
        """Test digest generation with default strategy."""
        self.stdout.write("\n🔄 Testing Default Strategy...")
        
        try:
            start_time = timezone.now()
            
            digest = digest_service.generate_user_digest(
                user=user,
                date=target_date.date(),
                force_regenerate=True
            )
            
            end_time = timezone.now()
            duration = (end_time - start_time).total_seconds()
            
            # Get strategy used from digest preferences
            strategy_used = digest.digest_preferences.get('strategy_used', 'Unknown')
            
            self._display_digest_results(digest, strategy_used, duration)
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Default strategy failed: {e}"))
    
    def _test_specific_strategy(
        self, 
        digest_service: DigestService, 
        user: User, 
        target_date: datetime, 
        strategy_key: str
    ):
        """Test digest generation with specific strategy."""
        self.stdout.write(f"\n🎯 Testing Specific Strategy: {strategy_key}")
        
        # Temporarily override user preferences to force strategy
        original_preferences = user.profile.get_digest_preferences()
        test_preferences = original_preferences.copy()
        test_preferences['digest_strategy'] = strategy_key
        
        # Temporarily patch user profile
        user.profile.digest_preferences = test_preferences
        user.profile.save()
        
        try:
            start_time = timezone.now()
            
            digest = digest_service.generate_user_digest(
                user=user,
                date=target_date.date(),
                force_regenerate=True
            )
            
            end_time = timezone.now()
            duration = (end_time - start_time).total_seconds()
            
            strategy_used = digest.digest_preferences.get('strategy_used', 'Unknown')
            
            self._display_digest_results(digest, strategy_used, duration)
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Strategy {strategy_key} failed: {e}"))
        
        finally:
            # Restore original preferences
            user.profile.digest_preferences = original_preferences
            user.profile.save()
    
    def _test_both_strategies(self, digest_service: DigestService, user: User, target_date: datetime):
        """Test both strategies sequentially."""
        self.stdout.write("\n🔄 Testing Both Strategies Sequentially...")
        
        strategies = ['articles_based', 'events_based']
        results = {}
        
        for strategy_key in strategies:
            self.stdout.write(f"\n📍 Testing {strategy_key}...")
            
            try:
                # Force strategy preference
                original_preferences = user.profile.get_digest_preferences()
                test_preferences = original_preferences.copy()
                test_preferences['digest_strategy'] = strategy_key
                
                user.profile.digest_preferences = test_preferences
                user.profile.save()
                
                start_time = timezone.now()
                
                digest = digest_service.generate_user_digest(
                    user=user,
                    date=target_date.date(),
                    force_regenerate=True
                )
                
                end_time = timezone.now()
                duration = (end_time - start_time).total_seconds()
                
                results[strategy_key] = {
                    'digest': digest,
                    'duration': duration,
                    'success': True
                }
                
                self.stdout.write(self.style.SUCCESS(f"✅ {strategy_key} completed in {duration:.2f}s"))
                
            except Exception as e:
                results[strategy_key] = {
                    'error': str(e),
                    'success': False
                }
                self.stdout.write(self.style.ERROR(f"❌ {strategy_key} failed: {e}"))
            
            finally:
                # Restore original preferences
                user.profile.digest_preferences = original_preferences
                user.profile.save()
        
        # Display summary
        self._display_strategy_comparison(results)
    
    def _compare_strategies(self, digest_service: DigestService, user: User, target_date: datetime):
        """Compare both strategies side by side."""
        self.stdout.write("\n⚖️  Comparing Digest Strategies...")
        
        # This is the same as test_both but with detailed comparison
        self._test_both_strategies(digest_service, user, target_date)
    
    def _display_digest_results(self, digest: Digest, strategy_used: str, duration: float):
        """Display digest generation results."""
        self.stdout.write(self.style.SUCCESS(f"\n✅ Digest Generated Successfully!"))
        self.stdout.write(f"🔧 Strategy Used: {strategy_used}")
        self.stdout.write(f"⏱️  Generation Time: {duration:.2f} seconds")
        self.stdout.write(f"📊 Metrics:")
        self.stdout.write(f"   • Topics: {digest.topics_included}")
        self.stdout.write(f"   • Events: {digest.events_included}")
        self.stdout.write(f"   • Articles: {digest.articles_processed}")
        
        # Show detailed article breakdown per topic
        topics = DigestTopic.objects.filter(digest=digest).order_by('order')
        if topics:
            self.stdout.write(f"   • Articles per topic:")
            for topic in topics:
                self.stdout.write(f"     - {topic.topic.name}: {topic.article_count} articles")
        
        self.stdout.write(f"   • Cost: ${float(digest.generation_cost_usd):.4f}")
        self.stdout.write(f"   • Tokens: {digest.tokens_input + digest.tokens_output:,} input, {digest.tokens_output:,} output")
        self.stdout.write(f"🆔 Digest ID: {digest.public_id}")
    
    def _display_strategy_comparison(self, results: Dict[str, Dict]):
        """Display comparison between strategies."""
        self.stdout.write("\n" + "="*60)
        self.stdout.write(self.style.SUCCESS("📊 Strategy Comparison Summary"))
        self.stdout.write("="*60)
        
        for strategy_key, result in results.items():
            self.stdout.write(f"\n🔧 {strategy_key.upper().replace('_', '-')} STRATEGY:")
            
            if result['success']:
                digest = result['digest']
                duration = result['duration']
                
                self.stdout.write(f"   ✅ Status: SUCCESS")
                self.stdout.write(f"   ⏱️  Duration: {duration:.2f}s")
                self.stdout.write(f"   📊 Topics: {digest.topics_included}")
                self.stdout.write(f"   📊 Events: {digest.events_included}")
                self.stdout.write(f"   📊 Articles: {digest.articles_processed}")
                self.stdout.write(f"   💰 Cost: ${digest.generation_cost_usd:.4f}")
                self.stdout.write(f"   🔗 ID: {digest.public_id}")
            else:
                self.stdout.write(f"   ❌ Status: FAILED")
                self.stdout.write(f"   💥 Error: {result['error']}")
        
        # Recommend best strategy
        successful_results = {k: v for k, v in results.items() if v['success']}
        if len(successful_results) > 1:
            # Compare by speed and cost
            fastest = min(successful_results.items(), key=lambda x: x[1]['duration'])
            cheapest = min(successful_results.items(), key=lambda x: x[1]['digest'].generation_cost_usd)
            
            self.stdout.write(f"\n🏆 RECOMMENDATIONS:")
            self.stdout.write(f"   ⚡ Fastest: {fastest[0]} ({fastest[1]['duration']:.2f}s)")
            self.stdout.write(f"   💰 Cheapest: {cheapest[0]} (${cheapest[1]['digest'].generation_cost_usd:.4f})")
    
    def _run_validation(self, options):
        """Run validation without generating digests."""
        self.stdout.write(self.style.WARNING("🧪 Running Validation Mode (no digests generated)"))
        
        # Test router initialization
        try:
            digest_service = DigestService()
            self.stdout.write("✅ DigestService initialized successfully")
            
            # Test strategy registration
            strategies = digest_service.get_available_strategies()
            self.stdout.write(f"✅ Found {len(strategies)} strategies: {list(strategies.keys())}")
            
            # Test user validation if provided
            if options.get('user_id') or options.get('username'):
                user = self._get_target_user(options)
                if user:
                    self.stdout.write(f"✅ User {user.username} found and has profile")
                    
                    # Check followed topics
                    topics_count = user.preferred_topics.count()
                    if topics_count > 0:
                        self.stdout.write(f"✅ User has {topics_count} followed topics")
                    else:
                        self.stdout.write(self.style.WARNING(f"⚠️  User has no followed topics"))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Validation failed: {e}"))
    
    def _parse_target_date(self, date_str: str) -> datetime:
        """Parse target date from string or use today."""
        if date_str:
            try:
                parsed_date = datetime.strptime(date_str, '%Y-%m-%d')
                return timezone.make_aware(parsed_date)
            except ValueError:
                raise CommandError(f"Invalid date format: {date_str}. Use YYYY-MM-DD")
        
        return timezone.now()
    
    def _get_target_user(self, options) -> User:
        """Get target user from options."""
        if options['user_id']:
            try:
                return User.objects.get(id=options['user_id'])
            except User.DoesNotExist:
                raise CommandError(f"User with ID {options['user_id']} not found")
        
        elif options['username']:
            try:
                return User.objects.get(username=options['username'])
            except User.DoesNotExist:
                raise CommandError(f"User '{options['username']}' not found")
        
        return None 