from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from wagtail.admin import urls as wagtailadmin_urls
from wagtail.core import urls as wagtail_urls
from wagtail.documents import urls as wagtaildocs_urls


# Admin
admin.site.site_header = "Administration du Marché de l'Inclusion"  # default: "Django Administration"  # noqa
admin.site.index_title = "Accueil"  # default: "Site administration"  # noqa
admin.site.site_title = "Administration du Marché de l'Inclusion"  # default: "Django site admin"  # noqa
# admin.site.enable_nav_sidebar = False


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("lemarche.api.urls")),
    path("accounts/", include("lemarche.www.auth.urls")),
    path("besoins/", include("lemarche.www.tenders.urls")),
    path("prestataires/", include("lemarche.www.siaes.urls")),
    path("profil/", include("lemarche.www.dashboard.urls")),
    path("select2/", include("django_select2.urls")),
    # admin blog
    path("cms/", include(wagtailadmin_urls)),
    # url docuemnts of glog
    path("documents/", include(wagtaildocs_urls)),
    # urls pages blog
    path("ressources/", include(wagtail_urls)),
    path("pages/", include("lemarche.www.pages.urls")),
]

if settings.DEBUG and "debug_toolbar" in settings.INSTALLED_APPS:
    import debug_toolbar

    urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns

if settings.BITOUBI_ENV == "dev":
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
