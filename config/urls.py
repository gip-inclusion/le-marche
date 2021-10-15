from django.conf import settings
from django.contrib import admin
from django.urls import include, path


# Admin
admin.site.site_header = "Administration du Marché de l'Inclusion"  # default: "Django Administration"  # noqa
admin.site.index_title = "Accueil"  # default: "Site administration"  # noqa
admin.site.site_title = "Administration du Marché de l'Inclusion"  # default: "Django site admin"  # noqa
# admin.site.enable_nav_sidebar = False


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("lemarche.api.urls")),
    path("accounts/", include("lemarche.www.auth.urls")),
    path("prestataires/", include("lemarche.www.siae.urls")),
    path("profil/", include("lemarche.www.dashboard.urls")),
    path("", include("lemarche.www.pages.urls")),
]

if settings.DEBUG and "debug_toolbar" in settings.INSTALLED_APPS:
    import debug_toolbar

    urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
