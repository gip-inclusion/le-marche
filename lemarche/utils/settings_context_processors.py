from django.conf import settings


def expose_settings(request):
    """
    Put things into the context to make them available in templates.
    https://docs.djangoproject.com/en/2.1/ref/templates/api/#using-requestcontext
    """
    base_template = "layouts/base_htmx.html" if request.htmx else "layouts/base.html"

    return {
        "BASE_TEMPLATE": base_template,
        "BITOUBI_ENV": settings.BITOUBI_ENV,
        "BITOUBI_ENV_COLOR": settings.BITOUBI_ENV_COLOR,
        "HOTJAR_ID": settings.HOTJAR_ID,
        "MATOMO_SITE_ID": settings.MATOMO_SITE_ID,
        "MATOMO_HOST": settings.MATOMO_HOST,
        "MATOMO_TAG_MANAGER_CONTAINER_ID": settings.MATOMO_TAG_MANAGER_CONTAINER_ID,
        "CRISP_ID": settings.CRISP_ID,
        "API_GOUV_URL": settings.API_GOUV_URL,
        # forms & docs
        "FACILITATOR_SLIDE": settings.FACILITATOR_SLIDE,
        "FACILITATOR_LIST": settings.FACILITATOR_LIST,
        "TYPEFORM_BESOIN_ACHAT": settings.TYPEFORM_BESOIN_ACHAT,
        "TYPEFORM_BESOIN_ACHAT_RECHERCHE": settings.TYPEFORM_BESOIN_ACHAT_RECHERCHE,
        "TYPEFORM_BESOIN_ACHAT_GROUPE": settings.TYPEFORM_BESOIN_ACHAT_GROUPE,
        "TYPEFORM_GROUPEMENT_AJOUT": settings.TYPEFORM_GROUPEMENT_AJOUT,
        "FORM_PARTENAIRES": settings.FORM_PARTENAIRES,
    }
