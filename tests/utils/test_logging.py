import json
import logging
from unittest.mock import patch

from django.test import RequestFactory, SimpleTestCase
from django.urls import reverse

from lemarche.utils.logging import CustomDataDogJSONFormatter


SECRET = "s3cr3tV4lu3"


class CustomDataDogJSONFormatterTest(SimpleTestCase):
    def format(self, request, message="HTTP 200 OK"):
        formatter = CustomDataDogJSONFormatter()
        record = logging.LogRecord("test", logging.INFO, __file__, 1, message, None, None)
        with patch.object(CustomDataDogJSONFormatter, "get_wsgi_request", return_value=request):
            return json.loads(formatter.format(record))

    def assertSecretRedacted(self, log_entry):
        self.assertNotIn(SECRET, json.dumps(log_entry))
        self.assertIn("[REDACTED]", json.dumps(log_entry))

    def test_sesame_token_in_query_string_and_referer_is_redacted(self):
        url = reverse("tenders:detail-survey-transactioned", args=["mon-besoin"]) + f"?token={SECRET}&answer=true"
        request = RequestFactory().get(url, HTTP_REFERER=f"https://example.com{url}")
        log_entry = self.format(request)
        self.assertSecretRedacted(log_entry)
        self.assertEqual(log_entry["http.url_details.queryString"], {"token": "[REDACTED]", "answer": "true"})
        self.assertIn("answer=true", log_entry["http.url"])
        self.assertTrue(log_entry["http.referer"].startswith("https://example.com/besoins/mon-besoin/"))

    def test_django_password_reset_token_in_path_is_redacted(self):
        url = reverse("auth:password_reset_confirm", kwargs={"uidb64": "MTI", "token": SECRET})
        log_entry = self.format(RequestFactory().get(url), message=f"Not Found: {url}")
        self.assertSecretRedacted(log_entry)
        self.assertEqual(log_entry["http.url_details.path"], "/accounts/password-reset/MTI/[REDACTED]/")

    def test_allauth_password_reset_key_in_path_is_redacted(self):
        url = reverse("account_reset_password_from_key", kwargs={"uidb36": "c", "key": SECRET})
        log_entry = self.format(RequestFactory().get(url, HTTP_REFERER=f"https://example.com{url}"))
        self.assertSecretRedacted(log_entry)

    def test_allauth_email_confirmation_key_in_path_is_redacted(self):
        url = reverse("account_confirm_email", kwargs={"key": SECRET})
        log_entry = self.format(RequestFactory().get(url))
        self.assertSecretRedacted(log_entry)

    def test_non_sensitive_url_is_kept(self):
        url = reverse("tenders:detail-survey-transactioned", args=["mon-besoin"]) + "?answer=true"
        log_entry = self.format(RequestFactory().get(url))
        self.assertEqual(log_entry["http.url"], url)
        self.assertNotIn("[REDACTED]", json.dumps(log_entry))
