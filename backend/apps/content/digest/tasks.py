"""
Celery tasks for digest generation.

This module contains the background tasks that handle:
- Scheduled daily digest generation for all users
- Individual user digest generation
- Digest regeneration and cleanup tasks
- Performance monitoring and error handling
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from decimal import Decimal

from celery import shared_task
from django.contrib.auth.models import User
from django.utils import timezone
from django.conf import settings
from django.db.models import Q

from .services import DigestService
from .models import Digest

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def generate_daily_digests_for_all_users(self, target_date: str = None, force_regenerate: bool = False):
    """
    Generate daily digests for all eligible users.
    
    This is the main scheduled task that runs daily to generate digests
    for all active users who have followed topics.
    
    Args:
        target_date: Date string in YYYY-MM-DD format (defaults to today)
        force_regenerate: Whether to regenerate existing digests
        
    Returns:
        Dict with generation statistics
    """
    
    try:
        # Parse target date
        if target_date:
            parsed_date = datetime.strptime(target_date, '%Y-%m-%d')
            target_datetime = timezone.make_aware(parsed_date)
        else:
            target_datetime = timezone.now()
        
        logger.info(f"Starting daily digest generation for {target_datetime.date()}")
        
        # Get eligible users
        eligible_users = _get_eligible_users_for_digest(target_datetime, force_regenerate)
        
        if not eligible_users:
            logger.info("No eligible users found for digest generation")
            return {
                'success': True,
                'total_users': 0,
                'processed': 0,
                'successful': 0,
                'failed': 0,
                'skipped': 0
            }
        
        logger.info(f"Found {len(eligible_users)} eligible users for digest generation")
        
        # Process users in batches to avoid memory issues
        batch_size = getattr(settings, 'DIGEST_BATCH_SIZE', 50)
        total_successful = 0
        total_failed = 0
        total_skipped = 0
        
        for i in range(0, len(eligible_users), batch_size):
            batch_users = eligible_users[i:i + batch_size]
            
            logger.info(f"Processing batch {i//batch_size + 1}: {len(batch_users)} users")
            
            # Process batch
            batch_results = _process_user_batch(batch_users, target_datetime, force_regenerate)
            
            total_successful += batch_results['successful']
            total_failed += batch_results['failed']
            total_skipped += batch_results['skipped']
            
            # Log batch progress
            logger.info(
                f"Batch {i//batch_size + 1} completed: "
                f"{batch_results['successful']} successful, "
                f"{batch_results['failed']} failed, "
                f"{batch_results['skipped']} skipped"
            )
        
        # Final statistics
        total_processed = total_successful + total_failed + total_skipped
        
        logger.info(
            f"Daily digest generation completed: "
            f"{total_successful}/{total_processed} successful "
            f"({total_failed} failed, {total_skipped} skipped)"
        )
        
        return {
            'success': True,
            'total_users': len(eligible_users),
            'processed': total_processed,
            'successful': total_successful,
            'failed': total_failed,
            'skipped': total_skipped,
            'target_date': target_datetime.date().isoformat()
        }
        
    except Exception as exc:
        logger.error(f"Daily digest generation failed: {exc}", exc_info=True)
        
        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying daily digest generation (attempt {self.request.retries + 1})")
            raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
        
        return {
            'success': False,
            'error': str(exc),
            'retries': self.request.retries
        }


@shared_task(bind=True, max_retries=2, default_retry_delay=60)
def generate_user_digest(
    self, 
    user_id: int, 
    target_date: str = None, 
    force_regenerate: bool = False
):
    """
    Generate digest for a specific user.
    
    Args:
        user_id: ID of the user to generate digest for
        target_date: Date string in YYYY-MM-DD format (defaults to today)
        force_regenerate: Whether to regenerate existing digest
        
    Returns:
        Dict with generation result
    """
    
    try:
        # Get user
        try:
            user = User.objects.get(id=user_id, is_active=True)
        except User.DoesNotExist:
            return {
                'success': False,
                'error': f'User {user_id} not found or inactive'
            }
        
        # Parse target date
        if target_date:
            parsed_date = datetime.strptime(target_date, '%Y-%m-%d')
            target_datetime = timezone.make_aware(parsed_date)
        else:
            target_datetime = timezone.now()
        
        logger.info(f"Generating digest for user {user.username} ({user_id}) for {target_datetime.date()}")
        
        # Check if user is eligible
        if not _is_user_eligible_for_digest(user, target_datetime, force_regenerate):
            reason = _get_user_ineligibility_reason(user, target_datetime, force_regenerate)
            logger.info(f"User {user.username} not eligible: {reason}")
            return {
                'success': True,
                'skipped': True,
                'reason': reason
            }
        
        # Generate digest
        digest_service = DigestService()
        result = digest_service.generate_user_digest(
            user=user,
            date=target_datetime.date(),
            force_regenerate=force_regenerate
        )
        
        if result['success']:
            digest = result['digest']
            metrics = result.get('metrics', {})
            
            logger.info(
                f"Digest generated for user {user.username}: {digest.public_id} "
                f"({metrics.get('topics_included', 0)} topics, "
                f"${metrics.get('total_cost_usd', 0):.4f})"
            )
            
            return {
                'success': True,
                'digest_id': str(digest.public_id),
                'metrics': metrics,
                'regenerated': result.get('regenerated', False)
            }
        else:
            error = result.get('error', 'Unknown error')
            logger.error(f"Digest generation failed for user {user.username}: {error}")
            
            return {
                'success': False,
                'error': error,
                'digest_id': str(result['digest'].public_id) if 'digest' in result else None
            }
        
    except Exception as exc:
        logger.error(f"User digest generation failed for user {user_id}: {exc}", exc_info=True)
        
        # Retry with shorter delay for individual users
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying user digest generation (attempt {self.request.retries + 1})")
            raise self.retry(exc=exc, countdown=30 * (self.request.retries + 1))
        
        return {
            'success': False,
            'error': str(exc),
            'retries': self.request.retries
        }


@shared_task
def cleanup_old_digests(days_to_keep: int = 90):
    """
    Clean up old digest records to save database space.
    
    Args:
        days_to_keep: Number of days of digests to retain (default: 90)
        
    Returns:
        Dict with cleanup statistics
    """
    
    try:
        cutoff_date = timezone.now().date() - timedelta(days=days_to_keep)
        
        logger.info(f"Cleaning up digests older than {cutoff_date}")
        
        # Count digests to be deleted
        old_digests = Digest.objects.filter(date__lt=cutoff_date)
        digest_count = old_digests.count()
        
        if digest_count == 0:
            logger.info("No old digests to clean up")
            return {
                'success': True,
                'deleted_count': 0,
                'cutoff_date': cutoff_date.isoformat()
            }
        
        # Delete old digests (cascade will handle related records)
        deleted_count, deleted_details = old_digests.delete()
        
        logger.info(f"Cleaned up {deleted_count} old digest records")
        
        return {
            'success': True,
            'deleted_count': deleted_count,
            'cutoff_date': cutoff_date.isoformat(),
            'details': deleted_details
        }
        
    except Exception as exc:
        logger.error(f"Digest cleanup failed: {exc}", exc_info=True)
        return {
            'success': False,
            'error': str(exc)
        }


@shared_task
def regenerate_failed_digests(target_date: str = None, max_attempts: int = 3):
    """
    Regenerate digests that failed during generation.
    
    Args:
        target_date: Date string in YYYY-MM-DD format (defaults to today)
        max_attempts: Maximum regeneration attempts per digest
        
    Returns:
        Dict with regeneration statistics
    """
    
    try:
        # Parse target date
        if target_date:
            parsed_date = datetime.strptime(target_date, '%Y-%m-%d')
            target_date_obj = parsed_date.date()
        else:
            target_date_obj = timezone.now().date()
        
        logger.info(f"Regenerating failed digests for {target_date_obj}")
        
        # Find failed digests
        failed_digests = Digest.objects.filter(
            date=target_date_obj,
            generation_status='FAILED'
        )
        
        if not failed_digests.exists():
            logger.info("No failed digests found to regenerate")
            return {
                'success': True,
                'total_failed': 0,
                'regenerated': 0,
                'still_failed': 0
            }
        
        logger.info(f"Found {failed_digests.count()} failed digests to regenerate")
        
        regenerated_count = 0
        still_failed_count = 0
        
        for failed_digest in failed_digests:
            try:
                # Skip if too many attempts
                if failed_digest.error_message and 'retries' in failed_digest.error_message:
                    continue
                
                # Try to regenerate
                digest_service = DigestService()
                result = digest_service.generate_user_digest(
                    user=failed_digest.user,
                    date=target_date_obj,
                    force_regenerate=True
                )
                
                if result['success']:
                    regenerated_count += 1
                    logger.info(f"Successfully regenerated digest for user {failed_digest.user.username}")
                else:
                    still_failed_count += 1
                    logger.warning(f"Failed to regenerate digest for user {failed_digest.user.username}")
                    
            except Exception as e:
                still_failed_count += 1
                logger.error(f"Error regenerating digest for user {failed_digest.user.username}: {e}")
        
        logger.info(f"Regeneration completed: {regenerated_count} successful, {still_failed_count} still failed")
        
        return {
            'success': True,
            'total_failed': failed_digests.count(),
            'regenerated': regenerated_count,
            'still_failed': still_failed_count,
            'target_date': target_date_obj.isoformat()
        }
        
    except Exception as exc:
        logger.error(f"Failed digest regeneration failed: {exc}", exc_info=True)
        return {
            'success': False,
            'error': str(exc)
        }


# Helper functions

def _get_eligible_users_for_digest(target_date: datetime, force_regenerate: bool = False) -> List[User]:
    """Get list of users eligible for digest generation."""
    
    # Base query: active users with followed topics
    queryset = User.objects.filter(
        is_active=True,
        preferred_topics__isnull=False  # Has followed topics
    ).distinct()
    
    # If not forcing regeneration, exclude users who already have digests
    if not force_regenerate:
        queryset = queryset.exclude(
            digests__date=target_date.date()
        )
    
    # Additional filtering can be added here based on user preferences
    # For example: users who have enabled digest notifications
    
    return list(queryset)


def _is_user_eligible_for_digest(user: User, target_date: datetime, force_regenerate: bool = False) -> bool:
    """Check if a user is eligible for digest generation."""
    
    # Must be active
    if not user.is_active:
        return False
    
    # Must have user profile
    if not hasattr(user, 'profile'):
        return False
    
    # Must have followed topics
    if not user.preferred_topics.exists():
        return False
    
    # Check for existing digest in the last 24 hours
    if not force_regenerate:
        # Calculate 24 hours ago from target_date
        twenty_four_hours_ago = target_date - timedelta(hours=24)
        
        existing_digest = Digest.objects.filter(
            user=user,
            created_at__gte=twenty_four_hours_ago
        ).exists()
        
        if existing_digest:
            return False
    
    return True


def _get_user_ineligibility_reason(user: User, target_date: datetime, force_regenerate: bool = False) -> str:
    """Get reason why user is not eligible for digest generation."""
    
    if not user.is_active:
        return "User not active"
    
    if not hasattr(user, 'profile'):
        return "No user profile"
    
    if not user.preferred_topics.exists():
        return "No followed topics"
    
    if not force_regenerate:
        # Calculate 24 hours ago from target_date
        twenty_four_hours_ago = target_date - timedelta(hours=24)
        
        existing_digest = Digest.objects.filter(
            user=user,
            created_at__gte=twenty_four_hours_ago
        ).first()
        
        if existing_digest:
            return f"Digest already exists ({existing_digest.public_id})"
    
    return "Unknown reason"


def _process_user_batch(users: List[User], target_date: datetime, force_regenerate: bool) -> Dict[str, int]:
    """Process a batch of users for digest generation."""
    
    successful = 0
    failed = 0
    skipped = 0
    
    digest_service = DigestService()
    
    for user in users:
        try:
            # Check eligibility
            if not _is_user_eligible_for_digest(user, target_date, force_regenerate):
                skipped += 1
                continue
            
            # Generate digest
            result = digest_service.generate_user_digest(
                user=user,
                date=target_date,
                force_regenerate=force_regenerate
            )
            
            if result['success']:
                successful += 1
            else:
                failed += 1
                logger.error(f"Digest generation failed for user {user.username}: {result.get('error')}")
                
        except Exception as e:
            failed += 1
            logger.error(f"Exception during digest generation for user {user.username}: {e}", exc_info=True)
    
    return {
        'successful': successful,
        'failed': failed,
        'skipped': skipped
    } 