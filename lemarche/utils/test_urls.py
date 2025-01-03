from django.test import TestCase
from django.urls import reverse

from lemarche.tenders.models import Tender
from lemarche.utils.urls import get_object_update_url


class GetObjectUrlTest(TestCase):
    def test_get_object_update_url(self):
        """
        Check the function returns the correct update object URL.
        """
        obj = Tender(slug="test-slug")

        update_url = get_object_update_url(obj, "tenders")  # any app should work
        expected_url = reverse("tenders:update", kwargs={"slug": "test-slug"})

        self.assertEqual(update_url, expected_url)
