from django.http import HttpResponsePermanentRedirect


class RemoveBetaRedirectMiddleware:
    """
    Middleware to permanently redirect all requests from hosts containing '.beta'
    to the same URL on the main domain, except for API requests.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if the host contains '.beta'
        if ".beta." in request.get_host():
            # Don't redirect API requests to give users time to make the switch
            if not request.path.startswith("/api/"):
                # Get the main domain by removing '.beta' from the host
                main_host = request.get_host().replace(".beta", "")

                # Build the redirect URL
                redirect_url = f"https://{main_host}{request.get_full_path()}"

                return HttpResponsePermanentRedirect(redirect_url)

        return self.get_response(request)
