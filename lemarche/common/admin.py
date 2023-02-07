from datetime import date

from advanced_filters.admin import AdvancedFilter, AdvancedFilterAdmin
from django.conf import settings
from django.contrib import admin
from django.contrib.sites.models import Site

from lemarche.utils.s3 import API_CONNECTION_DICT


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


admin_site = MarcheAdminSite(name="myadmin")
admin_site.register(Site)
admin_site.register(AdvancedFilter, AdvancedFilterAdmin)
