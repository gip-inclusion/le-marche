from django.test import TestCase
from django.urls import reverse

from lemarche.perimeters.factories import PerimeterFactory
from lemarche.sectors.factories import SectorFactory
from lemarche.tenders.models import Tender
from lemarche.users.factories import UserFactory


TENDER_JSON = {
    "kind": "TENDER",
    "title": "Test",
    # "sectors": [],
    "presta_type": ["DISP"],
    # "location": "",
    # "is_country_area": True,
    "description": "string",
    "start_working_date": "2023-03-14",
    "external_link": "",
    "constraints": "string",
    "amount": "0-1K",
    # "why_amount_is_blank": "DONT_KNOW",
    "accept_share_amount": True,
    "accept_cocontracting": True,
    "contact_first_name": "Prénom",
    "contact_last_name": "Nom",
    "contact_email": "prenom.nom@example.com",
    # "contact_phone": "string",
    "response_kind": ["EMAIL"],
    "deadline_date": "2023-03-14",
}


class TenderCreateApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        UserFactory()
        cls.user_with_token = UserFactory(api_key="admin")
        cls.perimeter = PerimeterFactory()
        cls.sector_1 = SectorFactory()
        cls.sector_2 = SectorFactory()

    def test_anonymous_user_cannot_create_tender(self):
        url = reverse("api:tenders-list")
        response = self.client.post(url, data=TENDER_JSON)
        self.assertEqual(response.status_code, 401)

    def test_user_with_unknown_api_key_cannot_create_tender(self):
        url = reverse("api:tenders-list") + "?token=test"
        response = self.client.post(url, data=TENDER_JSON)
        self.assertEqual(response.status_code, 401)

    def test_user_with_valid_api_key_can_create_tender(self):
        url = reverse("api:tenders-list") + "?token=admin"
        tender_data = TENDER_JSON.copy()
        tender_data["title"] = "Test author"
        response = self.client.post(url, data=tender_data)
        self.assertEqual(response.status_code, 201)
        self.assertIn("slug", response.data.keys())
        tender = Tender.objects.get(title="Test author")
        self.assertEqual(tender.author, self.user_with_token)
        self.assertEqual(tender.status, Tender.STATUS_PUBLISHED)
        self.assertEqual(tender.source, Tender.SOURCE_API)

    def test_create_tender_with_location(self):
        url = reverse("api:tenders-list") + "?token=admin"
        tender_data = TENDER_JSON.copy()
        tender_data["title"] = "Test location"
        tender_data["location"] = self.perimeter.slug
        response = self.client.post(url, data=tender_data)
        self.assertEqual(response.status_code, 201)
        tender = Tender.objects.get(title="Test location")
        self.assertEqual(tender.location, self.perimeter)
        # location can be empty
        tender_data = TENDER_JSON.copy()
        tender_data["title"] = "Test empty location"
        tender_data["location"] = ""
        response = self.client.post(url, data=tender_data)
        self.assertEqual(response.status_code, 201)
        # location must be valid
        tender_data = TENDER_JSON.copy()
        tender_data["title"] = "Test wrong location"
        tender_data["location"] = self.perimeter.slug + "wrong"
        response = self.client.post(url, data=tender_data)
        self.assertEqual(response.status_code, 400)

    def test_create_tender_with_sectors(self):
        url = reverse("api:tenders-list") + "?token=admin"
        tender_data = TENDER_JSON.copy()
        tender_data["title"] = "Test sectors"
        tender_data["sectors"] = [self.sector_1.slug, self.sector_2.slug]
        response = self.client.post(url, data=tender_data)
        self.assertEqual(response.status_code, 201)
        tender = Tender.objects.get(title="Test sectors")
        self.assertEqual(tender.sectors.count(), 2)
        # sectors can be empty
        tender_data = TENDER_JSON.copy()
        tender_data["title"] = "Test empty sectors"
        tender_data["sectors"] = []
        response = self.client.post(url, data=tender_data)
        self.assertEqual(response.status_code, 201)
        # sectors must be valid
        tender_data = TENDER_JSON.copy()
        tender_data["title"] = "Test wrong sectors"
        tender_data["sectors"] = [self.sector_1.slug + "wrong"]
        response = self.client.post(url, data=tender_data)
        self.assertEqual(response.status_code, 400)
        tender_data = TENDER_JSON.copy()
        tender_data["title"] = "Test wrong empty sectors"
        tender_data["sectors"] = ""
        response = self.client.post(url, data=tender_data)
        self.assertEqual(response.status_code, 400)


class TenderChoicesApiTest(TestCase):
    def test_should_return_tender_kinds_list(self):
        url = reverse("api:tender-kinds-list")  # anonymous user
        response = self.client.get(url)
        self.assertEqual(response.data["count"], 3)
        self.assertEqual(len(response.data["results"]), 3)
        self.assertTrue("id" in response.data["results"][0])
        self.assertTrue("name" in response.data["results"][0])

    def test_should_return_tender_amounts_list(self):
        url = reverse("api:tender-amounts-list")  # anonymous user
        response = self.client.get(url)
        self.assertEqual(response.data["count"], 14)
        self.assertEqual(len(response.data["results"]), 14)
        self.assertTrue("id" in response.data["results"][0])
        self.assertTrue("name" in response.data["results"][0])
