"""
Main Digest Service for orchestrating personalized daily digest generation.

This service coordinates the entire digest creation process by routing
to appropriate digest generation strategies via the DigestRouter.
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any, Tuple
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import transaction

from apps.content.digest.models import Digest, DigestTopic, DigestStory
from apps.content.digest.services.digest_router import DigestRouter
from apps.feeds.models import Topic, UserTopic
from apps.articles.models import Article


logger = logging.getLogger(__name__)


class DigestService:
    """
    Main service for generating personalized daily digests.
    
    This service now acts as a lightweight orchestrator that routes
    digest generation to appropriate strategies via the DigestRouter.
    """
    
    def __init__(self):
        self.router = DigestRouter()
    
    def generate_user_digest(
        self, 
        user: User, 
        date: datetime.date,
        force_regenerate: bool = False
    ) -> Digest:
        """
        Generate a personalized digest for a user on a specific date.
        
        Args:
            user: User to generate digest for
            date: Date to generate digest for
            force_regenerate: Whether to regenerate if digest already exists
            
        Returns:
            Digest: The generated or existing digest
            
        Raises:
            ValueError: If user has no followed topics or insufficient content
        """
        logger.info(f"Starting digest generation for user {user.username} on {date}")
        
        # Check if digest already exists
        try:
            existing_digest = Digest.objects.get(user=user, date=date)
            if not force_regenerate:
                logger.info(f"Digest already exists for {user.username} on {date}")
                return existing_digest
            logger.info(f"Force regenerating existing digest for {user.username} on {date}")
        except Digest.DoesNotExist:
            pass
        
        # Get user's digest preferences with defaults
        digest_preferences = user.profile.get_digest_preferences()
        
        # Get user's followed topics
        followed_topics = self._get_user_followed_topics(user)
        if not followed_topics:
            raise ValueError(f"User {user.username} has no followed topics")
        
        # Start generation process
        start_time = timezone.now()
        
        try:
            with transaction.atomic():
                # Create or update digest record
                digest, created = Digest.objects.get_or_create(
                    user=user,
                    date=date,
                    defaults={
                        'title': f"Your Daily Brief for {date.strftime('%B %d, %Y')}",
                        'generation_status': 'processing',
                        'user_timezone': user.profile.timezone,
                        'digest_preferences': digest_preferences,
                    }
                )
                
                if not created:
                    # Update existing digest for regeneration
                    digest.generation_status = 'processing'
                    digest.error_message = ''
                    digest.save()
                
                # Route digest generation to appropriate strategy
                result = self.router.generate_digest_content(
                    digest=digest,
                    followed_topics=followed_topics,
                    preferences=digest_preferences
                )
                
                # Mark as completed
                end_time = timezone.now()
                duration_ms = int((end_time - start_time).total_seconds() * 1000)
                
                # Calculate and save reading time
                digest.reading_time_minutes = digest.calculate_reading_time()
                
                digest.generation_status = 'completed'
                digest.generation_duration_ms = duration_ms
                digest.is_published = True
                
                # Add strategy information to digest metadata
                if 'strategy_used' in result:
                    digest_preferences['strategy_used'] = result['strategy_used']
                    digest.digest_preferences = digest_preferences
                
                digest.save()
                
                strategy_info = result.get('strategy_used', 'Unknown')
                logger.info(
                    f"Successfully generated digest for {user.username} on {date} "
                    f"using {strategy_info} in {duration_ms}ms"
                )
                return digest
                
        except Exception as e:
            logger.error(f"Failed to generate digest for {user.username} on {date}: {str(e)}")
            
            # Update digest with error status
            if 'digest' in locals():
                digest.generation_status = 'failed'
                digest.error_message = str(e)
                digest.save()
            
            raise
    
    def _get_user_followed_topics(self, user: User) -> List[Topic]:
        """Get list of topics the user follows."""
        return [
            user_topic.topic 
            for user_topic in UserTopic.objects.filter(user=user).select_related('topic')
        ]
    
    def get_user_digest(self, user: User, date: datetime.date) -> Optional[Digest]:
        """
        Get existing digest for a user and date.
        
        Args:
            user: User to get digest for
            date: Date to get digest for
            
        Returns:
            Digest instance if exists, None otherwise
        """
        try:
            return Digest.objects.get(user=user, date=date)
        except Digest.DoesNotExist:
            return None
    
    def get_recent_digests(self, user: User, limit: int = 7) -> List[Digest]:
        """
        Get recent digests for a user.
        
        Args:
            user: User to get digests for
            limit: Maximum number of digests to return
            
        Returns:
            List of recent Digest instances
        """
        return list(
            Digest.objects.filter(
                user=user,
                generation_status='completed'
            ).order_by('-date')[:limit]
        )
    
    def get_available_strategies(self) -> Dict[str, str]:
        """
        Get available digest generation strategies.
        
        Returns:
            Dictionary mapping strategy keys to display names
        """
        return self.router.get_available_strategies()
    
    def get_current_default_strategy(self) -> str:
        """Get the current default digest strategy."""
        return self.router.get_current_default_strategy()
    
    def set_default_strategy(self, strategy_name: str) -> bool:
        """
        Set the default digest strategy.
        
        Args:
            strategy_name: Strategy key to set as default
            
        Returns:
            True if strategy was set, False if strategy not found
        """
        return self.router.set_default_strategy(strategy_name) 