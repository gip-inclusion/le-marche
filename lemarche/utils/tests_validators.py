import socket
from unittest.mock import patch

import requests
from django.core.exceptions import ValidationError
from django.test import TestCase

from lemarche.utils.validators import (
    OptionalSchemeURLValidator,
    validate_naf,
    validate_post_code,
    validate_siren,
    validate_siret,
)


class ValidatorsTest(TestCase):
    def test_optional_scheme_url_validator(self):
        validator = OptionalSchemeURLValidator()
        URL_OK = ["example.com", "www.example.com", "http://www.example.com", "https://www.example.com"]
        for item in URL_OK:
            validator(item)
        URL_NOT_OK = ["test"]
        for item in URL_NOT_OK:
            self.assertRaises(ValidationError, validator, item)

    def test_post_code_validator(self):
        validator = validate_post_code
        POST_CODE_OK = ["00000", "12345", "38000"]
        for item in POST_CODE_OK:
            validator(item)
        POST_CODE_NOT_OK = ["0", "1234"]
        for item in POST_CODE_NOT_OK:
            self.assertRaises(ValidationError, validator, item)

    def test_siren_validator(self):
        validator = validate_siren
        SIREN_OK = ["123123123"]
        for item in SIREN_OK:
            validator(item)
        SIREN_NOT_OK = ["123"]
        for item in SIREN_NOT_OK:
            self.assertRaises(ValidationError, validator, item)

    def test_siret_validator(self):
        validator = validate_siret
        SIRET_OK = ["12312312312345"]
        for item in SIRET_OK:
            validator(item)
        SIRET_NOT_OK = ["123123123"]
        for item in SIRET_NOT_OK:
            self.assertRaises(ValidationError, validator, item)

    def test_naf_validator(self):
        validator = validate_naf
        NAF_OK = ["1234A"]
        for item in NAF_OK:
            validator(item)
        NAF_NOT_OK = ["1234", "12345", "ABCDE"]
        for item in NAF_NOT_OK:
            self.assertRaises(ValidationError, validator, item)


class StrictURLValidatorTests(TestCase):
    """
    Test suite for the `StrictURLValidator` class.
    Covers syntax validation, DNS resolution, and HTTP response checks.
    """

    def setUp(self):
        """Set up a reusable instance of the validator."""
        self.validator = OptionalSchemeURLValidator()

    @patch("socket.gethostbyname")
    @patch("requests.get")
    def test_valid_url(self, mock_requests_get, mock_socket_gethostbyname):
        """
        Test: Valid URL with proper DNS resolution and HTTP server response.
        Expected: No exception raised.
        """
        mock_socket_gethostbyname.return_value = "127.0.0.1"
        mock_requests_get.return_value.status_code = 200

        try:
            self.validator("http://example.com")
        except ValidationError:
            self.fail("StrictURLValidator raised ValidationError for a valid URL.")

    def test_invalid_syntax(self):
        """
        Test: URL with invalid syntax (e.g., missing scheme or malformed domain).
        Expected: ValidationError with a user-friendly message.
        """
        with self.assertRaises(ValidationError) as context:
            self.validator("http://en cours")
        self.assertIn("Saisissez une URL valide.", str(context.exception))

    @patch("socket.gethostbyname")
    def test_dns_failure(self, mock_socket_gethostbyname):
        """
        Test: URL with a domain that cannot be resolved (DNS failure).
        Expected: ValidationError with a message indicating the domain is invalid.
        """
        mock_socket_gethostbyname.side_effect = socket.gaierror

        with self.assertRaises(ValidationError) as context:
            self.validator("http://invalid-domain.com")
        self.assertIn("Le site web associé à cette adresse n'existe pas", str(context.exception))

    @patch("socket.gethostbyname")
    @patch("requests.get")
    def test_http_error(self, mock_requests_get, mock_socket_gethostbyname):
        """
        Test: URL with a valid domain but the HTTP server returns an error response.
        Expected: ValidationError with a message indicating a server issue.
        """
        mock_socket_gethostbyname.return_value = "127.0.0.1"
        mock_requests_get.return_value.status_code = 500

        with self.assertRaises(ValidationError) as context:
            self.validator("http://example.com")
        self.assertIn("Le site web semble rencontrer un problème", str(context.exception))

    @patch("socket.gethostbyname")
    @patch("requests.get")
    def test_http_timeout(self, mock_requests_get, mock_socket_gethostbyname):
        """
        Test: URL with a valid domain but the HTTP server takes too long to respond (timeout).
        Expected: ValidationError with a message indicating a timeout.
        """
        mock_socket_gethostbyname.return_value = "127.0.0.1"
        mock_requests_get.side_effect = requests.Timeout

        with self.assertRaises(ValidationError) as context:
            self.validator("http://example.com")
        self.assertIn("Une erreur est survenue en essayant de vérifier cette adresse", str(context.exception))

    def test_real_world_integration(self):
        """
        Integration Test: Real-world validation using actual DNS and HTTP requests.
        Note: Slower and depends on external resources being available.
        """
        try:
            self.validator("http://example.com")  # Known valid domain
        except ValidationError:
            self.fail("StrictURLValidator raised ValidationError for a valid real-world URL.")

        with self.assertRaises(ValidationError) as context:
            self.validator("http://invalid-domain-123456789.com")
        self.assertIn("Le site web associé à cette adresse n'existe pas", str(context.exception))

    @patch("requests.get")
    def test_localhost_url(self, mock_requests_get):
        """
        Test: Localhost URL to verify compatibility with development or internal environments.
        Expected: No exception raised.
        """
        mock_requests_get.return_value.status_code = 200

        try:
            self.validator("http://localhost")
        except ValidationError:
            self.fail("StrictURLValidator raised ValidationError for a valid localhost URL.")

    def test_missing_scheme(self):
        """
        Test: URL without a scheme (e.g., 'example.com').
        Expected: Automatically prepend 'https://' and validate successfully.
        """
        with patch("socket.gethostbyname") as mock_socket_gethostbyname, patch("requests.get") as mock_requests_get:
            mock_socket_gethostbyname.return_value = "127.0.0.1"
            mock_requests_get.return_value.status_code = 200

            try:
                self.validator("example.com")  # Should be treated as https://example.com
            except ValidationError:
                self.fail("StrictURLValidator raised ValidationError for a valid URL without scheme.")
