from django.apps import AppConfig


class BackendConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name               = 'backend'
    verbose_name       = 'Smart Lecturer Review System'

    def ready(self):
        import backend.arq  # noqa: F401 — wire up post_save signals
