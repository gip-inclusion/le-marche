from lemarche.tracker.tracker import track


IGNORE_FILTER = [
    "favicon",
    "static",
    "api/perimeters",
]


class TokenVisitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        token = request.GET.get("token", "0")
        page = request.path

        # We make sure no "filtered" keyword is in the path before tracking
        if all([s not in page for s in IGNORE_FILTER]):
            track(page, "load", meta={"token": token})

        response = self.get_response(request)
        return response
