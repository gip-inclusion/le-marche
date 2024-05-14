from django.test import TestCase
from django.urls import reverse

from lemarche.perimeters.factories import PerimeterFactory
from lemarche.sectors.factories import SectorFactory
from lemarche.tenders import constants as tender_constants
from lemarche.tenders.factories import TenderFactory
from lemarche.tenders.models import Tender
from lemarche.users import constants as user_constants
from lemarche.users.factories import UserFactory
from lemarche.users.models import User


USER_CONTACT_EMAIL = "prenom.nom@example.com"

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
    "amount_exact": "693",
    # "why_amount_is_blank": "DONT_KNOW",
    "accept_share_amount": True,
    "accept_cocontracting": True,
    "contact_first_name": "Prénom",
    "contact_last_name": "Nom",
    "contact_email": USER_CONTACT_EMAIL,
    "contact_phone": "string",
    "response_kind": ["EMAIL"],
    "deadline_date": "2023-03-14",
    # "extra_data": {}
}


class TenderCreateApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse("api:tenders-list") + "?token=admin"
        cls.user = UserFactory()
        cls.user_with_token = UserFactory(email="admin@example.com", api_key="admin")
        cls.perimeter = PerimeterFactory()
        cls.sector_1 = SectorFactory()
        cls.sector_2 = SectorFactory()

    def test_anonymous_user_cannot_create_tender(self):
        url = reverse("api:tenders-list")
        response = self.client.post(url, data=TENDER_JSON, content_type="application/json")
        self.assertEqual(response.status_code, 401)

    def test_user_with_unknown_api_key_cannot_create_tender(self):
        url = reverse("api:tenders-list") + "?token=test"
        response = self.client.post(url, data=TENDER_JSON, content_type="application/json")
        self.assertEqual(response.status_code, 401)

    def test_user_with_valid_api_key_can_create_tender(self):
        # test with other email
        tender_data = TENDER_JSON.copy()
        tender_data["title"] = "Test author 1"
        response = self.client.post(self.url, data=tender_data, content_type="application/json")
        self.assertEqual(response.status_code, 201)
        self.assertIn("slug", response.data.keys())
        tender = Tender.objects.get(title="Test author 1")
        self.assertEqual(User.objects.count(), 2 + 1)  # created a new user
        self.assertEqual(tender.author.email, USER_CONTACT_EMAIL)
        self.assertEqual(tender.status, tender_constants.STATUS_PUBLISHED)
        self.assertEqual(tender.source, tender_constants.SOURCE_API)
        self.assertIsNotNone(tender.import_raw_object)
        self.assertEqual(tender.import_raw_object["title"], "Test author 1")
        # test with own email
        tender_data = TENDER_JSON.copy()
        tender_data["title"] = "Test author 2"
        tender_data["contact_email"] = self.user_with_token.email
        response = self.client.post(self.url, data=tender_data, content_type="application/json")
        self.assertEqual(response.status_code, 201)
        self.assertIn("slug", response.data.keys())
        tender = Tender.objects.get(title="Test author 2")
        self.assertEqual(User.objects.count(), 3)  # did not create a new user
        self.assertEqual(tender.author, self.user_with_token)
        self.assertEqual(tender.status, tender_constants.STATUS_PUBLISHED)
        self.assertEqual(tender.source, tender_constants.SOURCE_API)
        self.assertIsNotNone(tender.import_raw_object)
        self.assertEqual(tender.import_raw_object["title"], "Test author 2")

    def test_create_tender_with_location(self):
        tender_data = TENDER_JSON.copy()
        tender_data["title"] = "Test location"
        tender_data["location"] = self.perimeter.slug
        response = self.client.post(self.url, data=tender_data, content_type="application/json")
        self.assertEqual(response.status_code, 201)
        tender = Tender.objects.get(title="Test location")
        self.assertEqual(tender.location, self.perimeter)
        # location can be empty
        tender_data = TENDER_JSON.copy()
        tender_data["title"] = "Test empty location"
        tender_data["location"] = ""
        response = self.client.post(self.url, data=tender_data, content_type="application/json")
        self.assertEqual(response.status_code, 201)
        # location must be valid
        tender_data = TENDER_JSON.copy()
        tender_data["title"] = "Test wrong location"
        tender_data["location"] = self.perimeter.slug + "wrong"
        response = self.client.post(self.url, data=tender_data, content_type="application/json")
        self.assertEqual(response.status_code, 400)

    def test_create_tender_with_sectors(self):
        tender_data = TENDER_JSON.copy()
        tender_data["title"] = "Test sectors"
        tender_data["sectors"] = [self.sector_1.slug, self.sector_2.slug]
        response = self.client.post(self.url, data=tender_data, content_type="application/json")
        self.assertEqual(response.status_code, 201)
        tender = Tender.objects.get(title="Test sectors")
        self.assertEqual(tender.sectors.count(), 2)
        # sectors can be empty
        tender_data = TENDER_JSON.copy()
        tender_data["title"] = "Test empty sectors"
        tender_data["sectors"] = []
        response = self.client.post(self.url, data=tender_data, content_type="application/json")
        self.assertEqual(response.status_code, 201)
        # sectors must be valid
        tender_data = TENDER_JSON.copy()
        tender_data["title"] = "Test wrong sectors"
        tender_data["sectors"] = [self.sector_1.slug + "wrong"]
        response = self.client.post(self.url, data=tender_data, content_type="application/json")
        self.assertEqual(response.status_code, 400)
        tender_data = TENDER_JSON.copy()
        tender_data["title"] = "Test wrong empty sectors"
        tender_data["sectors"] = ""
        response = self.client.post(self.url, data=tender_data)
        self.assertEqual(response.status_code, 400)

    def test_create_tender_with_tally_source(self):
        tender_data = TENDER_JSON.copy()
        tender_data["title"] = "Test tally"
        tender_data["extra_data"] = {"source": "TALLY"}
        response = self.client.post(self.url, data=tender_data, content_type="application/json")
        self.assertEqual(response.status_code, 201)
        tender = Tender.objects.get(title="Test tally")
        self.assertEqual(tender.source, tender_constants.SOURCE_TALLY)

    def test_create_tender_with_different_contact_data(self):
        tender_data = TENDER_JSON.copy()
        tender_data["title"] = "Test tally contact"
        tender_data["contact_email"] = "contact@example.com"
        tender_data["contact_kind"] = user_constants.KIND_BUYER
        tender_data["contact_buyer_kind_detail"] = user_constants.BUYER_KIND_DETAIL_PUBLIC_ASSOCIATION
        tender_data["contact_company_name"] = "Une asso"
        tender_data["extra_data"] = {"source": "TALLY"}
        response = self.client.post(self.url, data=tender_data, content_type="application/json")
        self.assertEqual(response.status_code, 201)
        tender = Tender.objects.get(title="Test tally contact")
        self.assertEqual(tender.source, tender_constants.SOURCE_TALLY)
        author = tender.author
        self.assertEqual(author.email, "contact@example.com")
        self.assertEqual(author.kind, user_constants.KIND_BUYER)
        self.assertEqual(author.buyer_kind_detail, user_constants.BUYER_KIND_DETAIL_PUBLIC_ASSOCIATION)


def test_create_tender_with_include_country_area(self):
    tender_data = TENDER_JSON.copy()
    title = "Test tally include_country_area"
    tender_data["title"] = title
    tender_data["extra_data"] = {"source": "TALLY"}
    response = self.client.post(self.url, data=tender_data, content_type="application/json")
    self.assertEqual(response.status_code, 201)
    tender = Tender.objects.get(title=title)
    self.assertEqual(tender.include_country_area, False)
    # when include country area is True
    title = "Test tally include_country_area is True"
    tender_data["title"] = title
    tender_data["include_country_area"] = "true"
    response = self.client.post(self.url, data=tender_data, content_type="application/json")
    self.assertEqual(response.status_code, 201)
    tender = Tender.objects.get(title=title)
    self.assertEqual(tender.include_country_area, True)


def test_create_tender_with_distance_location(self):
    tender_data = TENDER_JSON.copy()
    title = "Test tally distance_location"
    tender_data["title"] = title
    tender_data["extra_data"] = {"source": "TALLY"}
    response = self.client.post(self.url, data=tender_data, content_type="application/json")
    self.assertEqual(response.status_code, 201)
    tender = Tender.objects.get(title=title)
    self.assertEqual(tender.distance_location, None)
    # when distance_location is set
    tender_data["distance_location"] = 60
    title = "Test tally distance_location is 60"
    tender_data["title"] = title
    tender_data["extra_data"] = {"source": "TALLY"}
    response = self.client.post(self.url, data=tender_data, content_type="application/json")
    self.assertEqual(response.status_code, 201)
    tender = Tender.objects.get(title=title)
    self.assertEqual(tender.distance_location, 60)


class TenderCreateApiPartnerTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse("api:tenders-list") + "?token=approch"
        cls.user_partner_with_token = UserFactory(email="approch@example.com", api_key="approch")

    def test_partner_approch_can_create_tender(self):
        with self.settings(PARTNER_APPROCH_USER_ID=self.user_partner_with_token.id):
            # new tender
            tender_data = TENDER_JSON.copy()
            tender_data["contact_email"] = self.user_partner_with_token.email
            tender_data["extra_data"] = {"id": 123}
            response = self.client.post(self.url, data=tender_data, content_type="application/json")
            self.assertEqual(response.status_code, 201)
            self.assertEqual(Tender.objects.count(), 1)
            tender = Tender.objects.last()
            self.assertEqual(tender.author, self.user_partner_with_token)
            self.assertEqual(tender.partner_approch_id, 123)

    def test_partner_approch_can_update_tender(self):
        with self.settings(PARTNER_APPROCH_USER_ID=self.user_partner_with_token.id):
            existing_tender_partner_data = {
                "contact_email": self.user_partner_with_token.email,
                "extra_data": {"id": 123},
                "partner_approch_id": 123,
                "kind": tender_constants.KIND_PROJECT,
                "title": "Test",
                "description": "Description",
                "deadline_date": "2024-06-30",
            }
            TenderFactory(**{**TENDER_JSON.copy(), **existing_tender_partner_data})
            self.assertEqual(Tender.objects.count(), 1)
            self.assertEqual(Tender.objects.first().title, "Test")
            self.assertEqual(Tender.objects.first().deadline_date.strftime("%Y-%m-%d"), "2024-06-30")
            # existing tender: won't be re-created
            new_tender_partner_data = {
                **existing_tender_partner_data,
                "title": "Test changed",
                "deadline_date": "2024-12-31",
            }
            response = self.client.post(
                self.url, data={**TENDER_JSON.copy(), **new_tender_partner_data}, content_type="application/json"
            )
            self.assertEqual(response.status_code, 201)
            self.assertEqual(Tender.objects.count(), 1)
            self.assertEqual(Tender.objects.first().title, "Test changed")
            self.assertEqual(Tender.objects.first().deadline_date.strftime("%Y-%m-%d"), "2024-12-31")

    def test_partner_approch_new_tender_if_kind_changes(self):
        with self.settings(PARTNER_APPROCH_USER_ID=self.user_partner_with_token.id):
            existing_tender_partner_data = {
                "contact_email": self.user_partner_with_token.email,
                "extra_data": {"id": 123},
                "partner_approch_id": 123,
                "kind": tender_constants.KIND_PROJECT,
                "title": "Test",
                "description": "Description",
                "deadline_date": "2024-06-30",
            }
            TenderFactory(**{**TENDER_JSON.copy(), **existing_tender_partner_data})
            self.assertEqual(Tender.objects.count(), 1)
            self.assertEqual(Tender.objects.first().title, "Test")
            self.assertEqual(Tender.objects.first().deadline_date.strftime("%Y-%m-%d"), "2024-06-30")
            # existing tender but kind changed ! we re-create a new one
            new_tender_partner_data = {
                **existing_tender_partner_data,
                "kind": tender_constants.KIND_TENDER,
                "title": "Test changed",
                "deadline_date": "2024-12-31",
            }
            response = self.client.post(
                self.url, data={**TENDER_JSON.copy(), **new_tender_partner_data}, content_type="application/json"
            )
            self.assertEqual(response.status_code, 201)
            self.assertEqual(Tender.objects.count(), 2)
            self.assertEqual(Tender.objects.last().title, "Test")
            self.assertEqual(Tender.objects.last().deadline_date.strftime("%Y-%m-%d"), "2024-06-30")
            self.assertEqual(Tender.objects.first().title, "Test changed")
            self.assertEqual(Tender.objects.first().deadline_date.strftime("%Y-%m-%d"), "2024-12-31")


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
