from django.apps import AppConfig


class CmsConfig(AppConfig):
    name = "lemarche.cms"

    def ready(self):
        import lemarche.cms.snippets  # noqa
