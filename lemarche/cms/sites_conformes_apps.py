from sites_conformes.customimages.apps import CustomimagesConfig


class SitesConformesCustomImagesConfig(CustomimagesConfig):
    # The package app doesn't set default_auto_field and its migrations were generated with AutoField
    # (sites-conformes DEFAULT_AUTO_FIELD), while le-marche uses BigAutoField: without this, Django
    # detects a migration to generate in the installed package.
    default_auto_field = "django.db.models.AutoField"
