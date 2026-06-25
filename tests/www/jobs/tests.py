from django.test import TestCase
from django.urls import reverse

from tests.jobs.factories import AppellationFactory
from tests.sectors.factories import SectorFactory


class SectorAppellationsFormViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.sector = SectorFactory()
        cls.appellation = AppellationFactory(sectors=[cls.sector])

    def test_demo_page_loads(self):
        """Test that the demo page loads successfully."""
        url = reverse("jobs:sector-appellations-form")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Secteurs d'activité et métiers correspondants")
        self.assertContains(response, "Sélectionnez des secteurs")

    def test_demo_page_has_form(self):
        """Test that the demo page contains the sector selection form."""
        url = reverse("jobs:sector-appellations-form")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="appellations-container"')
        self.assertContains(response, "hx-get=")
        self.assertContains(response, "multiselect:change")


class SectorAppellationsViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.sector = SectorFactory()
        cls.sector2 = SectorFactory()
        cls.sector3 = SectorFactory()
        cls.appellation = AppellationFactory(sectors=[cls.sector])
        cls.appellation2 = AppellationFactory(sectors=[cls.sector2])
        cls.appellation3 = AppellationFactory(sectors=[cls.sector, cls.sector2])

    def test_sector_appellations_view(self):
        url = reverse("jobs:sector-appellations")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "")

        url = reverse("jobs:sector-appellations") + f"?sectors={self.sector.slug}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.appellation.name, count=1)
        self.assertNotContains(response, self.appellation2.name)
        self.assertContains(response, self.appellation3.name, count=1)

    def test_sector_appellations_view_multiple_sectors(self):
        url = reverse("jobs:sector-appellations") + f"?sectors={self.sector.slug}&sectors={self.sector2.slug}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.appellation.name, count=1)
        self.assertContains(response, self.appellation2.name, count=1)
        self.assertContains(response, self.appellation3.name, count=1)
