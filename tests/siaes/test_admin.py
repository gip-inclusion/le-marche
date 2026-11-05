from django.contrib.admin.sites import AdminSite
from django.test import SimpleTestCase

from lemarche.siaes.admin import SiaeAdmin, SiaeClientReferenceAdmin, SiaeGroupAdmin, SiaeImageAdmin
from lemarche.siaes.models import Siae, SiaeClientReference, SiaeGroup, SiaeImage


XSS_URL = 'https://example.com/"><svg/onload=alert(1)>'
ESCAPED_XSS_URL = "https://example.com/&quot;&gt;&lt;svg/onload=alert(1)&gt;"


class SiaeAdminImageUrlDisplayTest(SimpleTestCase):
    def setUp(self):
        self.admin_site = AdminSite()

    def assert_url_is_escaped(self, html):
        self.assertNotIn("<svg", html)
        self.assertEqual(html.count(ESCAPED_XSS_URL), 3)

    def test_siae_logo_url_display_escapes_url(self):
        model_admin = SiaeAdmin(Siae, self.admin_site)
        self.assert_url_is_escaped(model_admin.logo_url_display(Siae(logo_url=XSS_URL)))

    def test_siae_client_reference_logo_url_display_escapes_url(self):
        model_admin = SiaeClientReferenceAdmin(SiaeClientReference, self.admin_site)
        self.assert_url_is_escaped(model_admin.logo_url_display(SiaeClientReference(logo_url=XSS_URL)))

    def test_siae_image_image_url_display_escapes_url(self):
        model_admin = SiaeImageAdmin(SiaeImage, self.admin_site)
        self.assert_url_is_escaped(model_admin.image_url_display(SiaeImage(image_url=XSS_URL)))

    def test_siae_group_logo_url_display_escapes_url(self):
        model_admin = SiaeGroupAdmin(SiaeGroup, self.admin_site)
        self.assert_url_is_escaped(model_admin.logo_url_display(SiaeGroup(logo_url=XSS_URL)))
