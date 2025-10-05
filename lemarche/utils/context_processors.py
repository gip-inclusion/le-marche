from urllib.parse import urlencode


def matomo(request):
    if not request.resolver_match:
        return {"send_to_matomo": False}

    context = {"send_to_matomo": True}
    url = request.resolver_match.route
    # Only keep Matomo-related params for now.
    params = {k: v for k, v in request.GET.lists() if k.startswith(("utm_", "mtm_", "piwik_"))}
    if params:
        url = f"{url}?{urlencode(sorted(params.items()), doseq=True)}"
    context["matomo_custom_url"] = url
    return context
