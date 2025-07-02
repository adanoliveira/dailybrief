"""
Digest Router Service for orchestrating different digest generation strategies.

This service provides a configurable routing mechanism to switch between:
1. Events-based digest generation (ideal but complex)
2. Articles-based digest generation (reliable fallback)

The router allows us to easily change the primary strategy as the system evolves.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from django.contrib.auth.models import User
from django.conf import settings

from apps.content.digest.models import Digest
from apps.feeds.models import Topic

logger = logging.getLogger(__name__)


class DigestStrategy:
    """Base class for digest generation strategies."""
    
    def generate_digest_content(
        self,
        digest: Digest,
        followed_topics: List[Topic],
        preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate digest content using this strategy.
        
        Args:
            digest: Digest instance to populate
            followed_topics: Topics the user follows
            preferences: User's digest preferences
            
        Returns:
            Dictionary with generation metrics and results
        """
        raise NotImplementedError("Subclasses must implement generate_digest_content")
    
    def get_strategy_name(self) -> str:
        """Get human-readable name for this strategy."""
        raise NotImplementedError("Subclasses must implement get_strategy_name")


class DigestRouter:
    """
    Routes digest generation to appropriate strategy based on configuration.
    
    Supports dynamic strategy switching for experimentation and gradual migration
    between different digest generation approaches.
    """
    
    # Available strategies
    STRATEGY_EVENTS_BASED = 'events_based'
    STRATEGY_ARTICLES_BASED = 'articles_based'
    
    # Default strategy configuration
    DEFAULT_STRATEGY = STRATEGY_ARTICLES_BASED  # Currently prioritizing articles-based
    
    def __init__(self):
        self.logger = logger
        self._strategies = {}
        self._register_strategies()
    
    def _register_strategies(self):
        """Register available digest generation strategies."""
        from apps.content.digest.services.events_digest_strategy import EventsDigestStrategy
        from apps.content.digest.services.articles_digest_strategy import ArticlesDigestStrategy
        
        self._strategies[self.STRATEGY_EVENTS_BASED] = EventsDigestStrategy()
        self._strategies[self.STRATEGY_ARTICLES_BASED] = ArticlesDigestStrategy()
        
        self.logger.info(f"Registered {len(self._strategies)} digest strategies")
    
    def get_strategy_for_user(
        self, 
        user: User, 
        preferences: Dict[str, Any]
    ) -> DigestStrategy:
        """
        Determine which strategy to use for a specific user.
        
        Args:
            user: User requesting the digest
            preferences: User's digest preferences
            
        Returns:
            DigestStrategy instance to use
        """
        # Check for user-specific strategy preference
        strategy_name = preferences.get('digest_strategy', self.DEFAULT_STRATEGY)
        
        # Allow override via Django settings (for global configuration)
        strategy_name = getattr(settings, 'DIGEST_DEFAULT_STRATEGY', strategy_name)
        
        # Fallback to default if strategy not found
        if strategy_name not in self._strategies:
            self.logger.warning(
                f"Unknown strategy '{strategy_name}' for user {user.username}, "
                f"falling back to {self.DEFAULT_STRATEGY}"
            )
            strategy_name = self.DEFAULT_STRATEGY
        
        strategy = self._strategies[strategy_name]
        
        self.logger.info(
            f"Selected strategy '{strategy.get_strategy_name()}' for user {user.username}"
        )
        
        return strategy
    
    def generate_digest_content(
        self,
        digest: Digest,
        followed_topics: List[Topic],
        preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Route digest generation to appropriate strategy.
        
        Args:
            digest: Digest instance to populate
            followed_topics: Topics the user follows
            preferences: User's digest preferences
            
        Returns:
            Dictionary with generation metrics and results
        """
        strategy = self.get_strategy_for_user(digest.user, preferences)
        
        self.logger.info(
            f"Generating digest for {digest.user.username} using {strategy.get_strategy_name()}"
        )
        
        try:
            result = strategy.generate_digest_content(digest, followed_topics, preferences)
            
            # Add strategy information to result
            result['strategy_used'] = strategy.get_strategy_name()
            
            return result
            
        except Exception as e:
            self.logger.error(
                f"Strategy '{strategy.get_strategy_name()}' failed for user {digest.user.username}: {e}"
            )
            
            # If the primary strategy fails, try fallback to articles-based
            if strategy.get_strategy_name() != 'Articles-Based Digest':
                self.logger.info(f"Attempting fallback to articles-based strategy")
                
                fallback_strategy = self._strategies[self.STRATEGY_ARTICLES_BASED]
                try:
                    result = fallback_strategy.generate_digest_content(
                        digest, followed_topics, preferences
                    )
                    result['strategy_used'] = f"{strategy.get_strategy_name()} (failed) → {fallback_strategy.get_strategy_name()}"
                    result['fallback_used'] = True
                    
                    self.logger.info(
                        f"Fallback strategy succeeded for user {digest.user.username}"
                    )
                    
                    return result
                    
                except Exception as fallback_error:
                    self.logger.error(
                        f"Fallback strategy also failed for user {digest.user.username}: {fallback_error}"
                    )
                    raise fallback_error
            else:
                # Already using fallback strategy, re-raise original error
                raise e
    
    def get_available_strategies(self) -> Dict[str, str]:
        """
        Get mapping of strategy keys to human-readable names.
        
        Returns:
            Dictionary mapping strategy keys to display names
        """
        return {
            key: strategy.get_strategy_name() 
            for key, strategy in self._strategies.items()
        }
    
    def get_current_default_strategy(self) -> str:
        """Get the current default strategy name."""
        return self.DEFAULT_STRATEGY
    
    def set_default_strategy(self, strategy_name: str) -> bool:
        """
        Set the default strategy (for testing/configuration).
        
        Args:
            strategy_name: Strategy key to set as default
            
        Returns:
            True if strategy was set, False if strategy not found
        """
        if strategy_name not in self._strategies:
            self.logger.error(f"Cannot set unknown strategy as default: {strategy_name}")
            return False
        
        self.DEFAULT_STRATEGY = strategy_name
        self.logger.info(f"Default strategy changed to: {strategy_name}")
        return True 