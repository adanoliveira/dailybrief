from django.apps import AppConfig


class FetcherConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.content.fetcher'
    verbose_name = 'Content Fetcher'
