from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from wagtail import urls as wagtail_urls
from wagtail.admin import urls as wagtailadmin_urls
from wagtail.contrib.sitemaps.views import sitemap
from wagtail.documents import urls as wagtaildocs_urls
from wagtail_transfer import urls as wagtailtransfer_urls

from lemarche.utils.admin.admin_site import admin_site


urlpatterns = [
    path("admin/", admin_site.urls),
    path("api/", include("lemarche.api.urls")),
    path("django_shepherd/", include("lemarche.django_shepherd.urls")),
    # path("accounts/", include("lemarche.www.auth.urls")),
    # path('accounts/', include(('allauth.urls', 'allauth'), namespace='allauth')),
    path("accounts/", include("allauth.urls")),
    # path('accounts/confirm-email/<str:key>/', confirm_email, name='account_confirm_email'),
    path("besoins/", include("lemarche.www.tenders.urls")),
    path("prestataires/", include("lemarche.www.siaes.urls")),
    path("profil/", include("lemarche.www.dashboard.urls")),
    path("profil/prestataires/", include("lemarche.www.dashboard_siaes.urls")),
    path("profil/reseaux/", include("lemarche.www.dashboard_networks.urls")),
    path("profil/listes-dachats/", include("lemarche.www.dashboard_favorites.urls")),
    path("select2/", include("django_select2.urls")),
    # sitemap
    path("sitemap.xml", sitemap, name="sitemap"),  # appears above the default Wagtail page serving route
    # admin blog
    path("cms/", include(wagtailadmin_urls)),
    path("blog/", include("blog.urls")),
    # url docuemnts of glog
    path("documents/", include(wagtaildocs_urls)),
    path("wagtail-transfer/", include(wagtailtransfer_urls)),
    # urls pages blog
    path("", include("lemarche.www.pages.urls")),
    path("", include(wagtail_urls)),
]

if settings.DEBUG and "debug_toolbar" in settings.INSTALLED_APPS:
    import debug_toolbar

    urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns

if settings.BITOUBI_ENV in (
    "dev",
    "review_app",
):
    urlpatterns = static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + urlpatterns
