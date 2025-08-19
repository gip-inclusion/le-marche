from django.http import HttpResponse, HttpResponsePermanentRedirect
from django.test import RequestFactory, TestCase, override_settings

from lemarche.utils.remove_beta_redirect_middleware import RemoveBetaRedirectMiddleware


class RemoveBetaRedirectMiddlewareTest(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = RemoveBetaRedirectMiddleware(lambda request: HttpResponse(status=200))

    @override_settings(ALLOWED_HOSTS=["example.com", "example.beta.com"])
    def test_beta_host_redirects_to_https(self):
        """Test that requests from .beta hosts are redirected to HTTPS"""
        request = self.factory.get("/some-page/", HTTP_HOST="example.beta.com")
        response = self.middleware(request)

        self.assertIsInstance(response, HttpResponsePermanentRedirect)
        self.assertEqual(response.url, "https://example.com/some-page/")

    @override_settings(ALLOWED_HOSTS=["example.com", "example.beta.com"])
    def test_beta_host_https_redirects_to_https(self):
        """Test that HTTPS requests are redirected to HTTPS"""
        request = self.factory.get("/secure-page/", HTTP_HOST="example.beta.com", secure=True)
        request.is_secure = lambda: True
        response = self.middleware(request)

        self.assertIsInstance(response, HttpResponsePermanentRedirect)
        self.assertEqual(response.url, "https://example.com/secure-page/")

    @override_settings(ALLOWED_HOSTS=["example.com", "example.beta.com"])
    def test_beta_host_redirects(self):
        """Test that requests from .beta hosts are redirected"""
        request = self.factory.get("/some-page/", HTTP_HOST="example.beta.com", secure=True)
        response = self.middleware(request)

        self.assertIsInstance(response, HttpResponsePermanentRedirect)
        self.assertEqual(response.url, "https://example.com/some-page/")

    @override_settings(ALLOWED_HOSTS=["example.com", "example.beta.com"])
    def test_beta_host_with_path_and_query(self):
        """Test that requests with path and query parameters are redirected correctly"""
        request = self.factory.get("/search/?q=test&page=2", HTTP_HOST="example.beta.com", secure=True)
        response = self.middleware(request)

        self.assertIsInstance(response, HttpResponsePermanentRedirect)
        self.assertEqual(response.url, "https://example.com/search/?q=test&page=2")

    @override_settings(ALLOWED_HOSTS=["example.com", "example.beta.com"])
    def test_api_requests_not_redirected(self):
        """Test that API requests are not redirected"""
        request = self.factory.get("/api/users/", HTTP_HOST="example.beta.com")
        response = self.middleware(request)

        # Should not redirect, middleware should return None to continue processing
        self.assertEqual(response.status_code, 200)

    @override_settings(ALLOWED_HOSTS=["example.com", "example.beta.com"])
    def test_api_requests_with_beta_in_path_not_redirected(self):
        """Test that API requests with 'beta' in the path are not redirected"""
        request = self.factory.get("/api/beta-features/", HTTP_HOST="example.beta.com")
        response = self.middleware(request)

        # Should not redirect, middleware should return None to continue processing
        self.assertEqual(response.status_code, 200)

    @override_settings(ALLOWED_HOSTS=["example.com", "example.beta.com"])
    def test_non_beta_host_no_redirect(self):
        """Test that requests from non-beta hosts are not redirected"""
        request = self.factory.get("/some-page/", HTTP_HOST="example.com")
        response = self.middleware(request)

        # Should not redirect, middleware should return None to continue processing
        self.assertEqual(response.status_code, 200)

    @override_settings(ALLOWED_HOSTS=["example.com", "example.beta.com"])
    def test_beta_in_path_not_host_no_redirect(self):
        """Test that requests with 'beta' in the path but not in host are not redirected"""
        request = self.factory.get("/beta-features/", HTTP_HOST="example.com")
        response = self.middleware(request)

        # Should not redirect, middleware should return None to continue processing
        self.assertEqual(response.status_code, 200)
