import redis
import json
from django.conf import settings

# Connect to Redis
r = redis.from_url(settings.CELERY_BROKER_URL)

# Get all tasks from queue
tasks = r.lrange('celery', 0, -1)
removed_count = 0
total_tasks = len(tasks)

print(f'🔍 Scanning {total_tasks} queued tasks for digest generation...')

# Remove digest tasks from the end (to avoid index shifting)
for i in reversed(range(len(tasks))):
    try:
        task_data = json.loads(tasks[i])
        task_name = task_data.get('task', '').lower()
        
        # Check if it's a digest-related task
        if any(keyword in task_name for keyword in ['digest', 'generate-daily-digests']):
            # Remove this specific task
            r.lrem('celery', 1, tasks[i])
            removed_count += 1
            
            # Show what we removed
            user_id = 'Unknown'
            args = task_data.get('args', [])
            if args:
                user_id = str(args[0])[:8] if args else 'Unknown'
            
            print(f'  ❌ Removed: {task_data.get("task", "Unknown")} (User: {user_id})')
            
    except Exception as e:
        print(f'  ⚠️  Error processing task {i}: {e}')

# Final status
remaining_tasks = r.llen('celery')
print(f'\n✅ Cleanup complete:')
print(f'   Removed: {removed_count} digest tasks')
print(f'   Remaining: {remaining_tasks} total tasks')
print(f'   Cleared: {total_tasks - remaining_tasks} tasks total')
