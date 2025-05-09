import logging
from celery import shared_task
from apps.newsapi.services.sync_manager import SyncManager

logger = logging.getLogger(__name__)

@shared_task(name="newsapi.sync_headlines")
def sync_headlines():
    """
    Sync top headlines from NewsAPI.
    Runs twice daily to get the latest breaking news from all categories.
    """
    logger.info("Starting top headlines sync task")
    manager = SyncManager()
    created, updated, success = manager.sync_top_headlines()
    
    result = {
        'success': success,
        'articles_created': created,
        'articles_updated': updated,
        'total': created + updated
    }
    
    if success:
        logger.info(f"Headlines sync completed: {created} created, {updated} updated")
    else:
        logger.error(f"Headlines sync failed with partial results: {created} created, {updated} updated")
        
    return result

@shared_task(name="newsapi.sync_recent_by_sources")
def sync_recent_by_sources(hours=24, batch_size=20):
    """
    Sync recent articles from specific sources using batched requests.
    Runs daily to get articles published the previous day.
    
    Args:
        hours (int): Hours to look back (default 24 to get previous day)
        batch_size (int): Max sources per request (max 20 for NewsAPI)
    """
    logger.info(f"Starting recent articles by sources sync task (last {hours} hours)")
    manager = SyncManager()
    created, updated, success = manager.sync_recent_by_sources_batched(
        hours=hours,
        batch_size=batch_size
    )
    
    result = {
        'success': success,
        'articles_created': created,
        'articles_updated': updated,
        'total': created + updated
    }
    
    if success:
        logger.info(f"Recent articles by sources sync completed: {created} created, {updated} updated")
    else:
        logger.error(f"Recent articles by sources sync failed")
        
    return result

@shared_task(name="newsapi.sync_by_publication")
def sync_by_publication(days=1):
    """
    Sync articles from specific publications.
    
    Args:
        days (int): Days to look back
    """
    logger.info(f"Starting publication-specific sync task (last {days} days)")
    manager = SyncManager()
    created, updated, success = manager.sync_everything_by_publication(days=days)
    
    result = {
        'success': success,
        'articles_created': created,
        'articles_updated': updated,
        'total': created + updated
    }
    
    if success:
        logger.info(f"Publication sync completed: {created} created, {updated} updated")
    else:
        logger.error(f"Publication sync failed with partial results: {created} created, {updated} updated")
        
    return result

@shared_task(name="newsapi.sync_sources")
def sync_sources(update_existing=True):
    """
    Sync news sources from NewsAPI.
    Updates our publication database with new sources.
    
    Args:
        update_existing (bool): Whether to update existing publications
    """
    from django.core.management import call_command
    
    logger.info("Starting sources sync task")
    
    try:
        # Call the direct management command which doesn't require language
        call_command('sync_sources_direct', update_existing=update_existing)
        logger.info("Sources sync completed successfully")
        return {'success': True}
    except Exception as e:
        logger.error(f"Sources sync failed: {str(e)}")
        return {'success': False, 'error': str(e)}

@shared_task(name="newsapi.backfill_articles")
def backfill_articles(days=30, chunk_size=2, language='en'):
    """
    Backfill articles from NewsAPI for a specific period.
    This is a one-time task that can be run manually.
    
    Args:
        days (int): Days to look back
        chunk_size (int): Size of each date chunk in days
        language (str): Language code
    """
    logger.info(f"Starting backfill task (last {days} days)")
    manager = SyncManager()
    created, updated, success = manager.backfill_articles(
        days=days, 
        chunk_size=chunk_size,
        language=language
    )
    
    result = {
        'success': success,
        'articles_created': created,
        'articles_updated': updated,
        'total': created + updated
    }
    
    if success:
        logger.info(f"Backfill completed: {created} created, {updated} updated")
    else:
        logger.error(f"Backfill failed with partial results: {created} created, {updated} updated")
        
    return result 