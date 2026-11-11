from django.apps import AppConfig


class LostfoundConfig(AppConfig):
    name = 'lostfound'

    def ready(self):
        from . import signals
        from . import achievements
