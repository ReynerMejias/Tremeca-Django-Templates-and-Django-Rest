from django.apps import AppConfig

class TuAppConfig(AppConfig):
    name = 'control'

    def ready(self):
        import control.signals
