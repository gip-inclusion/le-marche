# https://github.com/betagouv/itou/blob/master/itou/utils/urls.py
from codecs import encode as codecs_encode
from urllib.parse import quote, urlencode

from django.conf import settings
from django.contrib.sites.models import Site
from django.db.models import Model
from django.urls import reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme


def get_domain_url():
    """
    review apps have dynamic urls
    TODO: find a way to update their Site.object instead
    """
    if settings.DEPLOY_URL:
        return settings.DEPLOY_URL
    return Site.objects.get_current().domain


def get_safe_url(request, param_name=None, fallback_url=None, url=None):
    url = url or request.GET.get(param_name) or request.POST.get(param_name)

    allowed_hosts = settings.ALLOWED_HOSTS
    require_https = request.is_secure()

    if url:
        if settings.DEBUG:
            # In DEBUG mode the network location part `127.0.0.1:8000` contains
            # a port and fails the validation of `url_has_allowed_host_and_scheme`
            # since it's not a member of `allowed_hosts`:
            # https://github.com/django/django/blob/525274f/django/utils/http.py#L413
            # As a quick fix, we build a new URL without the port.
            from urllib.parse import ParseResult, urlparse

            url_info = urlparse(url)
            url_without_port = ParseResult(
                scheme=url_info.scheme,
                netloc=url_info.hostname,
                path=url_info.path,
                params=url_info.params,
                query=url_info.query,
                fragment=url_info.fragment,
            ).geturl()
            if url_has_allowed_host_and_scheme(url_without_port, allowed_hosts, require_https):
                return url

        else:
            if url_has_allowed_host_and_scheme(url, allowed_hosts, require_https):
                return url

    return fallback_url


def get_object_share_url(obj: Model):
    return f"https://{get_domain_url()}{obj.get_absolute_url()}"


def get_object_admin_url(obj: Model):
    admin_url = reverse_lazy(f"admin:{obj._meta.app_label}_{obj._meta.model_name}_change", args=[obj.id])
    return f"https://{get_domain_url()}{admin_url}"


def get_encoded_url_from_params(params: dict, encoding: str = "rot_13"):
    return codecs_encode(urlencode(params, quote_via=quote), encoding=encoding)


def get_tender_siae_download_url(tender: Model, status: str = ""):
    params = {  # use the params of form SiaeSelectFieldsForm
        "download_form-format": "xlsx",
        "tendersiae_status": status,
        "download_form-selected_fields": [
            "name",
            "siret",
            "kind",
            "address",
            "city",
            "post_code",
            "region",
            "department",
            "ca",
            "employees_insertion_count",
            "contact_first_name",
            "contact_last_name",
            "contact_email",
            "contact_phone",
            "siae_answers",
        ],
    }
    return (
        f"https://{get_domain_url()}"
        f"{reverse_lazy('tenders:download-siae-list', args=[tender.slug])}"
        f"?{urlencode(params, doseq=True)}"
    )
