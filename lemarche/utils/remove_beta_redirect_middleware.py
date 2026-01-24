from django.http import HttpResponsePermanentRedirect


class RemoveBetaRedirectMiddleware:
    """
    Middleware to permanently redirect all requests from hosts containing '.beta'
    to the same URL on the main domain, except for API requests (home page API only).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # If the host does not contain '.beta.', don't redirect
        if ".beta." not in request.get_host():
            return self.get_response(request)

        # Don't redirect API requests, just home page API, to give users time to make the switch
        if request.path.startswith("/api/") and request.path != "/api/":
            return self.get_response(request)

        # Get the main domain by removing '.beta' from the host
        main_host = request.get_host().replace(".beta", "")
        redirect_url = f"https://{main_host}{request.get_full_path()}"
        return HttpResponsePermanentRedirect(redirect_url)
