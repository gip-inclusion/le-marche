import logging

from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from lemarche.users.models import User


logger = logging.getLogger(__name__)


class CustomBearerAuthentication(BaseAuthentication):
    """
    Authentication via:
    1. Authorization header: Bearer <token> (recommended).
    """

    def authenticate(self, request):
        token = None

        # Priority to the Authorization header
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split("Bearer ")[1]

        # If no token is provided
        if not token:
            raise AuthenticationFailed("No token provided")

        # Check the minimum length of the token
        if len(token) < 64:
            raise AuthenticationFailed("Token too short. Possible security issue detected.")

        if not token.isalnum():
            raise AuthenticationFailed("Token contains invalid characters. Possible security issue detected.")

        # Validate the token
        try:
            user = User.objects.has_api_key().get(api_key=token)
        except User.DoesNotExist:
            raise AuthenticationFailed("Invalid or expired token")

        # Return the user and the token
        return (user, token)

    def authenticate_header(self, request):
        """
        Returns the expected header for 401 responses.
        """
        return 'Bearer realm="api"'
