import logging
from django.core.management.base import BaseCommand
from apps.newsapi.tasks import sync_headlines, sync_recent_by_sources, sync_by_publication, sync_sources

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Test running a NewsAPI sync task'

    def add_arguments(self, parser):
        parser.add_argument(
            'task_name', 
            type=str, 
            nargs='?',
            default='sync_headlines',
            help='Task to run (sync_headlines, sync_recent_by_sources, sync_by_publication, sync_sources)'
        )

    def handle(self, *args, **options):
        task_name = options['task_name']
        self.stdout.write(self.style.SUCCESS(f'Running {task_name} task...'))
        
        try:
            # Choose the task based on the argument
            tasks = {
                'sync_headlines': sync_headlines,
                'sync_recent_by_sources': sync_recent_by_sources,
                'sync_by_publication': sync_by_publication,
                'sync_sources': sync_sources
            }
            
            if task_name not in tasks:
                self.stdout.write(self.style.ERROR(
                    f"Unknown task: {task_name}. Available tasks: {', '.join(tasks.keys())}"
                ))
                return
            
            # Run the selected task
            result = tasks[task_name]()
            
            # Print the result
            if result.get('success', False):
                self.stdout.write(self.style.SUCCESS(
                    f"Task completed successfully: {result.get('articles_created', 0)} created, "
                    f"{result.get('articles_updated', 0)} updated"
                ))
            else:
                self.stdout.write(self.style.ERROR(
                    f"Task failed: {result}"
                ))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error running task: {str(e)}')) 