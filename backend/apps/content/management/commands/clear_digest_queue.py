import redis
import json
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Clear digest generation tasks from the Celery queue'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be cleared without actually clearing',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        self.stdout.write("🔍 Connecting to Redis...")
        
        try:
            # Connect to Redis
            r = redis.from_url(settings.CELERY_BROKER_URL)
            
            # Get all tasks from queue
            tasks = r.lrange('celery', 0, -1)
            removed_count = 0
            total_tasks = len(tasks)
            
            self.stdout.write(f'📊 Found {total_tasks} queued tasks')
            
            if dry_run:
                self.stdout.write(self.style.WARNING("🧪 DRY RUN - No changes will be made"))
            
            # Process tasks from the end (to avoid index shifting)
            digest_tasks = []
            for i, task in enumerate(tasks):
                try:
                    task_data = json.loads(task)
                    task_name = task_data.get('task', '').lower()
                    
                    # Check if it's a digest-related task
                    if any(keyword in task_name for keyword in ['digest', 'generate-daily-digests']):
                        digest_tasks.append((i, task, task_data))
                        
                except Exception as e:
                    self.stdout.write(f'  ⚠️  Error processing task {i}: {e}')
            
            self.stdout.write(f'🍰 Found {len(digest_tasks)} digest tasks to clear')
            
            # Remove digest tasks (from the end to avoid index shifting)
            for i, task, task_data in reversed(digest_tasks):
                if not dry_run:
                    r.lrem('celery', 1, task)
                    removed_count += 1
                
                # Show what we're removing/would remove
                user_id = 'Unknown'
                args = task_data.get('args', [])
                if args:
                    user_id = str(args[0])[:8] if args else 'Unknown'
                
                action = "Would remove" if dry_run else "Removed"
                self.stdout.write(f'  ❌ {action}: {task_data.get("task", "Unknown")} (User: {user_id})')
            
            # Final status
            if not dry_run:
                remaining_tasks = r.llen('celery')
                self.stdout.write(f'\n✅ Cleanup complete:')
                self.stdout.write(f'   Removed: {removed_count} digest tasks')
                self.stdout.write(f'   Remaining: {remaining_tasks} total tasks')
            else:
                self.stdout.write(f'\n🧪 Dry run complete - would remove {len(digest_tasks)} digest tasks')
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error: {e}')
            ) 