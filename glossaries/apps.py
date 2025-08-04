from django.apps import AppConfig


class GlossariesConfig(AppConfig):
    name = 'glossaries'

    def ready(self):
        import glossaries.signals
