from datetime import date

from django.conf import settings
from django.contrib import admin, messages
from django.contrib.sites.models import Site
from django.shortcuts import redirect
from django.urls import reverse

from lemarche.utils.s3 import API_CONNECTION_DICT


def get_admin_change_view_url(obj: object) -> str:
    return reverse(f"admin:{obj._meta.app_label}_{type(obj).__name__.lower()}_change", args=(obj.pk,))


class MarcheAdminSite(admin.AdminSite):
    """
    Override the default admin
    """

    site_header = "Administration du Marché de l'Inclusion"  # default: "Django Administration"  # noqa
    index_title = "Accueil"  # default: "Site administration"  # noqa
    site_title = "Administration du Marché de l'Inclusion"  # default: "Django site admin"  # noqa
    # enable_nav_sidebar = False
    index_template = "admin/index_with_export.html"

    def index(self, request, extra_context=None):
        user_download_list_file_path = f"{API_CONNECTION_DICT['endpoint_url']}/{settings.S3_STORAGE_BUCKET_NAME}/{settings.STAT_EXPORT_FOLDER_NAME}/liste_telechargements_{date.today()}.csv"  # noqa
        user_search_list_file_path = f"{API_CONNECTION_DICT['endpoint_url']}/{settings.S3_STORAGE_BUCKET_NAME}/{settings.STAT_EXPORT_FOLDER_NAME}/liste_recherches_{date.today()}.csv"  # noqa
        extra_context = extra_context or {
            "user_download_list_file_path": user_download_list_file_path,
            "user_search_list_file_path": user_search_list_file_path,
        }
        return super().index(request, extra_context=extra_context)

    def login(self, request, extra_context=None):
        """
        Replace the Django admin login form by the django-allauth one.
        - anonymous user: go to the allauth login page, keeping the `next` param
        - user with access to the admin: go to the admin index
        - user without access: go to the homepage with an error message.
          Redirecting to the login page would loop: allauth sends authenticated users back to `next`.
        """
        # avoid a circular import (admin modules are loaded with the apps)
        from lemarche.www.auth.views import redirect_to_allauth_login

        if request.user.is_authenticated:
            if self.has_permission(request):
                return redirect(f"{self.name}:index")
            messages.error(request, "Vous n'avez pas accès à l'administration.")
            return redirect(settings.LOGIN_REDIRECT_URL)
        return redirect_to_allauth_login(request)


admin_site = MarcheAdminSite(name="myadmin")
admin_site.register(Site)
