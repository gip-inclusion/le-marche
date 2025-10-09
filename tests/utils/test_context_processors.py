from django.test import TestCase, override_settings
from django.urls import reverse

from tests.tenders.factories import TenderFactory


class ContextProcessorsTest(TestCase):
    @override_settings(MATOMO_HOST="https://fake.matomo.url")
    def test_matomo_context_processor(self):
        """Test on a canically problematic view that we get the right Matomo properties.

        Namely, verify that the URL params are cleaned, sorted, the title is forced, and
        the path params are replaced by a the variadic version.

        Also ensure the user ID is correctly set.
        """
        # An unknown url always matches to wagtail urls
        response = self.client.get("/tenders/doesnotexist/?token=blah&mtm_foo=truc")
        self.assertEqual(response.context["matomo_custom_url"], "^((?:[\\w\\-]+/)*)$?mtm_foo=truc")

        # canonical case
        tender = TenderFactory()
        url = reverse("tenders:detail", kwargs={"slug": tender.slug})
        response = self.client.get(f"{url}?foo=bar&mtm_foo=truc&mtm_bar=bidule")
        self.assertEqual(response.context["matomo_custom_url"], "besoins/<str:slug>?mtm_bar=bidule&mtm_foo=truc")
