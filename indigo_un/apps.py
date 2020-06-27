from django.apps import AppConfig


class IndigoUNAppConfig(AppConfig):
    name = 'indigo_un'
    verbose_name = 'Indigo United Nations'

    def ready(self):
        # ensure our plugins are pulled in
        import indigo_un.importer  # noqa
        import indigo_un.toc  # noqa
