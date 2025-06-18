from django.apps import AppConfig


class ContentConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.content'
    
    def ready(self):
        # Import tasks when Django apps are ready to avoid circular imports
        try:
            from . import tasks  # noqa
        except ImportError:
            pass 