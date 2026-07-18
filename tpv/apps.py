from django.apps import AppConfig


class TpvConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tpv'

    def ready(self):
        import tpv.signals  # noqa: F401
