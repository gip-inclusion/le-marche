from django.test import RequestFactory, TestCase
from rest_framework.exceptions import AuthenticationFailed

from lemarche.api.authentication import CustomBearerAuthentication
from lemarche.api.utils import generate_random_string
from lemarche.users.factories import UserFactory


class CustomBearerAuthenticationTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.authentication = CustomBearerAuthentication()

        self.user_token = generate_random_string()
        self.user = UserFactory(api_key=self.user_token)
        self.url = "/api/endpoint/"

    def test_authentication_with_authorization_header(self):
        """
        Test the authentication process using the Authorization header.

        This test simulates a GET request with a Bearer token in the Authorization header.
        It verifies that the authentication method correctly identifies the user and token.

        Steps:
        1. Create a GET request to the specified URL.
        2. Add the Authorization header with a Bearer token.
        3. Authenticate the request.
        4. Assert that the returned user matches the expected user.
        5. Assert that the returned token matches the expected token.
        """
        request = self.factory.get(self.url)

        request.headers = {"Authorization": "Bearer " + self.user_token}

        user, token = self.authentication.authenticate(request)

        self.assertEqual(user, self.user)
        self.assertEqual(token, self.user_token)

    def test_authentication_with_short_token(self):
        """
        Test the authentication process with a short token.

        This test simulates a request with a token that is too short and verifies
        that the authentication process raises an AuthenticationFailed exception
        with the appropriate error message.

        Steps:
        1. Create a GET request with a short token in the Authorization header.
        2. Attempt to authenticate the request.
        3. Assert that an AuthenticationFailed exception is raised.
        4. Verify that the exception message is "Token too short. Possible security issue detected."
        """
        # Requête avec un token trop court
        request = self.factory.get(self.url)
        request.headers = {"Authorization": "Bearer short"}

        with self.assertRaises(AuthenticationFailed) as context:
            self.authentication.authenticate(request)

        self.assertEqual(str(context.exception), "Token too short. Possible security issue detected.")

    def test_authentication_with_invalid_token(self):
        """
        Test the authentication process with an invalid token.

        This test ensures that the authentication mechanism correctly raises an
        AuthenticationFailed exception when an invalid or expired token is provided
        in the request headers.

        Steps:
        1. Create a GET request with an invalid token in the Authorization header.
        2. Attempt to authenticate the request.
        3. Verify that an AuthenticationFailed exception is raised.
        4. Check that the exception message is "Invalid or expired token".
        """
        # Requête avec un token invalide
        request = self.factory.get(self.url)
        request.headers = {"Authorization": "Bearer in" + self.user_token}

        with self.assertRaises(AuthenticationFailed) as context:
            self.authentication.authenticate(request)

        self.assertEqual(str(context.exception), "Invalid or expired token")

    def test_authentication_with_no_token(self):
        """
        Test case for authentication without a token.

        This test verifies that the authentication method returns None
        when no token is provided in the request.
        """
        # Requête sans token
        request = self.factory.get(self.url)

        result = self.authentication.authenticate(request)

        self.assertIsNone(result)
