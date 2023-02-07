from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from wagtail import urls as wagtail_urls
from wagtail.admin import urls as wagtailadmin_urls
from wagtail.documents import urls as wagtaildocs_urls

from lemarche.common.admin import admin_site


urlpatterns = [
    path("admin/", admin_site.urls),
    path("api/", include("lemarche.api.urls")),
    path("accounts/", include("lemarche.www.auth.urls")),
    path("besoins/", include("lemarche.www.tenders.urls")),
    path("prestataires/", include("lemarche.www.siaes.urls")),
    path("profil/", include("lemarche.www.dashboard.urls")),
    path("select2/", include("django_select2.urls")),
    # advanced filters urls
    path("advanced_filters/", include("advanced_filters.urls")),
    # admin blog
    path("cms/", include(wagtailadmin_urls)),
    # url docuemnts of glog
    path("documents/", include(wagtaildocs_urls)),
    # urls pages blog
    path("ressources/", include(wagtail_urls)),
    path("", include("lemarche.www.pages.urls")),
]

if settings.DEBUG and "debug_toolbar" in settings.INSTALLED_APPS:
    import debug_toolbar

    urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns

if settings.BITOUBI_ENV in (
    "dev",
    "review_app",
):
    urlpatterns = static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + urlpatterns
