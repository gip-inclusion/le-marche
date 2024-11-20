import logging

from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from lemarche.users.models import User


logger = logging.getLogger(__name__)


class CustomBearerAuthentication(BaseAuthentication):
    """
    Authentication via:
    1. Authorization header: Bearer <token> (recommended).
    2. URL parameter ?token=<token> (deprecated, temporary support).
    """

    def authenticate(self, request):
        token = None
        warning_issued = False

        # Priority to the Authorization header
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split("Bearer ")[1]
        elif request.GET.get("token"):  # Otherwise, try the URL parameter
            token = request.GET.get("token")
            warning_issued = True
            logger.warning("Authentication via URL token detected. This method is deprecated and less secure.")

        # If no token is provided
        if not token:
            return None

        # Check the minimum length of the token
        if len(token) < 20:
            raise AuthenticationFailed("Token too short. Possible security issue detected.")

        # Validate the token
        try:
            user = User.objects.has_api_key().get(api_key=token)
        except User.DoesNotExist:
            raise AuthenticationFailed("Invalid or expired token")

        # Add a warning in the response for URL tokens
        if warning_issued:
            request._deprecated_auth_warning = True  # Marker for middleware or view

        # Return the user and the token
        return (user, token)

    def authenticate_header(self, request):
        """
        Returns the expected header for 401 responses.
        """
        return 'Bearer realm="api"'


class DeprecationWarningMiddleware:
    """
    Middleware pour informer les utilisateurs que l'authentification via URL `?token=` est dépréciée.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Ajoute un warning si le marqueur est défini dans la requête
        if hasattr(request, "_deprecated_auth_warning") and request._deprecated_auth_warning:
            response["Deprecation-Warning"] = (
                "URL token authentication is deprecated and will be removed on [date]. "
                "Please use Authorization header with Bearer tokens."
            )

        return response
