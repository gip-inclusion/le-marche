# https://github.com/betagouv/itou/blob/master/itou/utils/urls.py

from django.conf import settings
from django.contrib.sites.models import Site
from django.db.models import Model
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


def get_share_url_object(obj: Model):
    return f"https://{get_domain_url()}{obj.get_absolute_url()}"
