from django.apps import AppConfig


class AnalyzerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.content.analyzer'
    verbose_name = 'Content Analyzer' 