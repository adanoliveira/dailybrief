from django.apps import AppConfig


class RssfeedsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.rssfeeds'
    verbose_name = 'RSS Feeds'

    def ready(self):
        # Register signal handlers (RSSFeed -> Publication metadata sync).
        from . import signals  # noqa: F401
