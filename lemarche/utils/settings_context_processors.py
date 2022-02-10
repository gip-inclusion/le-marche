from django.conf import settings


def expose_settings(request):
    """
    Put things into the context to make them available in templates.
    https://docs.djangoproject.com/en/2.1/ref/templates/api/#using-requestcontext
    """

    return {
        "BITOUBI_ENV": settings.BITOUBI_ENV,
        "BITOUBI_ENV_COLOR": settings.BITOUBI_ENV_COLOR,
        "TRACKER_HOST": settings.TRACKER_HOST,
        "HOTJAR_ID": settings.HOTJAR_ID,
        "MATOMO_SITE_ID": settings.MATOMO_SITE_ID,
        "MATOMO_HOST": settings.MATOMO_HOST,
        "CRISP_ID": settings.CRISP_ID,
        "FACILITATOR_SLIDE": settings.FACILITATOR_SLIDE,
        "FACILITATOR_LIST": settings.FACILITATOR_LIST,
        "TYPEFORM_BESOIN_ACHAT": settings.TYPEFORM_BESOIN_ACHAT,
        "TYPEFORM_BESOIN_ACHAT_RECHERCHE": settings.TYPEFORM_BESOIN_ACHAT_RECHERCHE,
        "TYPEFORM_BESOIN_ACHAT_GROUPE": settings.TYPEFORM_BESOIN_ACHAT_GROUPE,
        "API_GOUV_URL": settings.API_GOUV_URL,
    }
