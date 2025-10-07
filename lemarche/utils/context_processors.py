from urllib.parse import urlencode


def matomo(request):
    if not request.resolver_match:
        return {}

    url = request.resolver_match.route
    # Only keep Matomo-related params for now.
    params = {k: v for k, v in request.GET.lists() if k.startswith(("utm_", "mtm_", "piwik_"))}
    if params:
        url = f"{url}?{urlencode(sorted(params.items()), doseq=True)}"
    return {"matomo_custom_url": url}
