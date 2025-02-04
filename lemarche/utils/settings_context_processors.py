from django.conf import settings
from django.urls import reverse_lazy

from lemarche.users.models import User


def expose_settings(request):
    """
    Put things into the context to make them available in templates.
    https://docs.djangoproject.com/en/5.0/ref/templates/api/#using-requestcontext
    """
    base_template = "layouts/base_htmx.html" if request.htmx else "layouts/base.html"

    home_page = reverse_lazy("wagtail_serve", args=("",))
    if request.user.is_authenticated and request.user.kind == User.KIND_SIAE:
        home_page = settings.SIAE_HOME_PAGE

    return {
        "BITOUBI_ENV": settings.BITOUBI_ENV,
        "BITOUBI_ENV_COLOR": settings.BITOUBI_ENV_COLOR,
        # external services
        "GOOGLE_TAG_MANAGER_ID": settings.GOOGLE_TAG_MANAGER_ID,
        "MATOMO_SITE_ID": settings.MATOMO_SITE_ID,
        "MATOMO_HOST": settings.MATOMO_HOST,
        "MATOMO_TAG_MANAGER_CONTAINER_ID": settings.MATOMO_TAG_MANAGER_CONTAINER_ID,
        "CRISP_ID": settings.CRISP_ID,
        # template & wording
        "BASE_TEMPLATE": base_template,
        "HOME_PAGE_PATH": home_page,
        "ABOUT": settings.ABOUT,
        "ACCESSIBILITY": settings.ACCESSIBILITY,
        "CGU": settings.CGU,
        "CGU_API": settings.CGU_API,
        "LEGAL_INFO": settings.LEGAL_INFO,
        "PRIVACY_POLICY": settings.PRIVACY_POLICY,
        "RESSOURCES": settings.RESSOURCES,
        "FAQ": settings.FAQ,
        "DASHBOARD_TITLE": settings.DASHBOARD_TITLE,
        "DASHBOARD_NETWORK_DETAIL_TITLE": settings.DASHBOARD_NETWORK_DETAIL_TITLE,
        "DASHBOARD_NETWORK_SIAE_LIST_TITLE": settings.DASHBOARD_NETWORK_SIAE_LIST_TITLE,
        "DASHBOARD_NETWORK_TENDER_LIST_TITLE": settings.DASHBOARD_NETWORK_TENDER_LIST_TITLE,
        "TENDER_DETAIL_TITLE_SIAE": settings.TENDER_DETAIL_TITLE_SIAE,
        "TENDER_DETAIL_TITLE_OTHERS": settings.TENDER_DETAIL_TITLE_OTHERS,
        "FAVORITE_LIST_TITLE": settings.FAVORITE_LIST_TITLE,
        # emails & urls
        "API_GOUV_URL": settings.API_GOUV_URL,
        "CONTACT_EMAIL": settings.CONTACT_EMAIL,
        "TEAM_CONTACT_EMAIL": settings.TEAM_CONTACT_EMAIL,
        "GIP_CONTACT_EMAIL": settings.GIP_CONTACT_EMAIL,
        "EMPLOIS_INCLUSION_HELP_URL": settings.EMPLOIS_INCLUSION_HELP_URL,
        # forms & docs
        "FACILITATOR_SLIDE": settings.FACILITATOR_SLIDE,
        "FACILITATOR_LIST": settings.FACILITATOR_LIST,
        "TYPEFORM_BESOIN_ACHAT": settings.TYPEFORM_BESOIN_ACHAT,
        "TYPEFORM_BESOIN_ACHAT_RECHERCHE": settings.TYPEFORM_BESOIN_ACHAT_RECHERCHE,
        "TYPEFORM_GROUPEMENT_AJOUT": settings.TYPEFORM_GROUPEMENT_AJOUT,
        "FORM_PARTENAIRES": settings.FORM_PARTENAIRES,
        "MTCAPTCHA_PUBLIC_KEY": settings.MTCAPTCHA_PUBLIC_KEY,
        "SIAE_HOME_PAGE": settings.SIAE_HOME_PAGE,
        "PURCHASING_IMPACT_PAGE": settings.PURCHASING_IMPACT_PAGE,
    }


def expose_guide_context(request):
    display_guide = True
    return {"DISPLAY_GUIDE": display_guide}
