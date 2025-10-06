from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from lemarche.tenders import constants as tender_constants
from lemarche.tenders.constants import KIND_PROJECT, KIND_TENDER
from lemarche.tenders.enums import TenderSourcesChoices
from lemarche.tenders.models import Tender, TenderInstruction
from lemarche.users import constants as user_constants
from lemarche.users.models import User
from tests.perimeters.factories import PerimeterFactory
from tests.sectors.factories import SectorFactory
from tests.tenders.factories import TenderFactory
from tests.users.factories import UserFactory


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
    "amount_exact": 693,
    # "why_amount_is_blank": "DONT_KNOW",
    "accept_share_amount": True,
    "contact_first_name": "Prénom",
    "contact_last_name": "Nom",
    "contact_email": USER_CONTACT_EMAIL,
    "contact_phone": "0123456789",
    "response_kind": ["EMAIL"],
    "deadline_date": "2023-03-14",
    # "extra_data": {}
}


class TenderCreateApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_token = "a" * 64
        cls.url = reverse("api:tenders-list")
        cls.user = UserFactory()
        cls.user_buyer = UserFactory(kind=User.KIND_BUYER, company_name="Entreprise Buyer")
        cls.user_with_token = UserFactory(email="admin@example.com", api_key=cls.user_token)
        cls.perimeter = PerimeterFactory()
        cls.sector_1 = SectorFactory()
        cls.sector_2 = SectorFactory()

        TenderInstruction.objects.create(
            title="tally_instruction",
            text="instruction",
            tender_type=KIND_TENDER,
            tender_source=TenderSourcesChoices.SOURCE_TALLY,
        )

        TenderInstruction.objects.create(
            title="api_instruction",
            text="instruction",
            tender_type=KIND_TENDER,
            tender_source=TenderSourcesChoices.SOURCE_API,
        )

    @patch("lemarche.api.tenders.views.get_or_create_user_from_anonymous_content")
    def setup_mock_user_and_tender_creation(self, mock_get_user, user=None, title="Test Tally", extra_data=None):
        """Helper method to setup mock user and create a tender."""
        user = user if user else self.user
        mock_get_user.return_value = user

        # Tender data
        tender_data = TENDER_JSON.copy()
        tender_data["title"] = title
        tender_data["extra_data"] = extra_data or {}

        # Tender creation
        response = self.client.post(
            self.url,
            data=tender_data,
            content_type="application/json",
            headers={"authorization": f"Bearer {self.user_token}"},
        )
        tender = Tender.objects.get(title=title)

        return response, tender, user

    def test_anonymous_user_cannot_create_tender(self):
        url = reverse("api:tenders-list")
        response = self.client.post(url, data=TENDER_JSON, content_type="application/json")
        self.assertEqual(response.status_code, 401)

    def test_user_with_unknown_api_key_cannot_create_tender(self):
        url = reverse("api:tenders-list")
        response = self.client.post(
            url, data=TENDER_JSON, content_type="application/json", headers={"authorization": "Bearer !!!!!!"}
        )
        self.assertEqual(response.status_code, 401)

    @patch("lemarche.api.tenders.views.add_to_contact_list")
    def test_user_with_valid_api_key_can_create_tender(self, mock_add_to_contact_list):
        # test with other email
        tender_data = TENDER_JSON.copy()
        tender_data["title"] = "Test author 1"
        response = self.client.post(
            self.url,
            data=tender_data,
            content_type="application/json",
            headers={"authorization": f"Bearer {self.user_token}"},
        )
        self.assertEqual(response.status_code, 201)
        self.assertIn("slug", response.data.keys())
        tender = Tender.objects.get(title="Test author 1")
        self.assertEqual(User.objects.count(), 3 + 1)  # created a new user
        self.assertEqual(tender.author.email, USER_CONTACT_EMAIL)
        self.assertEqual(tender.status, Tender.StatusChoices.STATUS_SUBMITTED)
        self.assertEqual(tender.source, TenderSourcesChoices.SOURCE_API)
        self.assertIsNotNone(tender.import_raw_object)
        self.assertEqual(tender.import_raw_object["title"], "Test author 1")
        # test with own email
        tender_data = TENDER_JSON.copy()
        tender_data["title"] = "Test author 2"
        tender_data["contact_email"] = self.user_with_token.email
        response = self.client.post(
            self.url,
            data=tender_data,
            content_type="application/json",
            headers={"authorization": f"Bearer {self.user_token}"},
        )
        self.assertEqual(response.status_code, 201)
        self.assertIn("slug", response.data.keys())
        tender = Tender.objects.get(title="Test author 2")
        self.assertEqual(User.objects.count(), 4)  # did not create a new user
        self.assertEqual(tender.author, self.user_with_token)
        self.assertEqual(tender.status, Tender.StatusChoices.STATUS_SUBMITTED)
        self.assertEqual(tender.source, TenderSourcesChoices.SOURCE_API)
        self.assertIsNotNone(tender.import_raw_object)
        self.assertEqual(tender.import_raw_object["title"], "Test author 2")

    def test_create_tender_with_location(self):
        tender_data = TENDER_JSON.copy()
        tender_data["title"] = "Test location"
        tender_data["location"] = self.perimeter.slug
        response = self.client.post(
            self.url,
            data=tender_data,
            content_type="application/json",
            headers={"authorization": f"Bearer {self.user_token}"},
        )
        self.assertEqual(response.status_code, 201)
        tender = Tender.objects.get(title="Test location")
        self.assertEqual(tender.location, self.perimeter)
        # location can be empty
        tender_data = TENDER_JSON.copy()
        tender_data["title"] = "Test empty location"
        tender_data["location"] = ""
        response = self.client.post(
            self.url,
            data=tender_data,
            content_type="application/json",
            headers={"authorization": f"Bearer {self.user_token}"},
        )
        self.assertEqual(response.status_code, 201)
        # location must be valid
        tender_data = TENDER_JSON.copy()
        tender_data["title"] = "Test wrong location"
        tender_data["location"] = self.perimeter.slug + "wrong"
        response = self.client.post(
            self.url,
            data=tender_data,
            content_type="application/json",
            headers={"authorization": f"Bearer {self.user_token}"},
        )
        self.assertEqual(response.status_code, 400)

    def test_create_tender_with_sectors(self):
        tender_data = TENDER_JSON.copy()
        tender_data["title"] = "Test sectors"
        tender_data["sectors"] = [self.sector_1.slug, self.sector_2.slug]
        response = self.client.post(
            self.url,
            data=tender_data,
            content_type="application/json",
            headers={"authorization": f"Bearer {self.user_token}"},
        )
        self.assertEqual(response.status_code, 201)
        tender = Tender.objects.get(title="Test sectors")
        self.assertEqual(tender.sectors.count(), 2)
        # sectors can be empty
        tender_data = TENDER_JSON.copy()
        tender_data["title"] = "Test empty sectors"
        tender_data["sectors"] = []
        response = self.client.post(
            self.url,
            data=tender_data,
            content_type="application/json",
            headers={"authorization": f"Bearer {self.user_token}"},
        )
        self.assertEqual(response.status_code, 201)
        # sectors must be valid
        tender_data = TENDER_JSON.copy()
        tender_data["title"] = "Test wrong sectors"
        tender_data["sectors"] = [self.sector_1.slug + "wrong"]
        response = self.client.post(
            self.url,
            data=tender_data,
            content_type="application/json",
            headers={"authorization": f"Bearer {self.user_token}"},
        )
        self.assertEqual(response.status_code, 400)
        tender_data = TENDER_JSON.copy()
        tender_data["title"] = "Test wrong empty sectors"
        tender_data["sectors"] = ""
        response = self.client.post(self.url, data=tender_data, headers={"authorization": f"Bearer {self.user_token}"})
        self.assertEqual(response.status_code, 400)

    @patch("lemarche.api.tenders.views.add_to_contact_list")
    def test_create_tender_with_tally_source(self, mock_add_to_contact_list):
        extra_data = {"source": "TALLY"}
        response, tender, user = self.setup_mock_user_and_tender_creation(title="Test tally", extra_data=extra_data)

        mock_add_to_contact_list.assert_called_once()
        args, kwargs = mock_add_to_contact_list.call_args

        self.assertEqual(response.status_code, 201)
        self.assertEqual(tender.source, TenderSourcesChoices.SOURCE_TALLY)
        # Check other arguments like user, type, and source
        self.assertEqual(kwargs["user"], user)
        self.assertEqual(kwargs["contact_type"], "signup")
        # Verify that `tender` is an instance of Tender
        self.assertIsInstance(
            kwargs.get("tender"), Tender, "Expected an instance of Tender for the 'tender' argument."
        )
        self.assertEqual(kwargs.get("tender").constraints_title, "tally_instruction")

    @patch("lemarche.api.tenders.views.add_to_contact_list")
    def test_reset_modification_request(self, mock_add_to_contact_list):
        """Test 'reset_modification_request' method to check tender fields updates"""
        extra_data = {"source": "TALLY"}
        _, tender, _ = self.setup_mock_user_and_tender_creation(
            title="Test tally", user=self.user_buyer, extra_data=extra_data
        )
        tender.reset_modification_request()
        tender.save()

        self.assertEqual(tender.status, Tender.StatusChoices.STATUS_SUBMITTED)
        self.assertEqual(tender.email_sent_for_modification, False)

    @patch("lemarche.api.tenders.views.add_to_contact_list")
    def test_create_tender_with_different_contact_data(self, mock_add_to_contact_list):
        tender_data = TENDER_JSON.copy()
        tender_data["title"] = "Test tally contact"
        tender_data["contact_email"] = "contact@example.com"
        tender_data["contact_kind"] = user_constants.KIND_BUYER
        tender_data["contact_buyer_kind_detail"] = user_constants.BUYER_KIND_DETAIL_PUBLIC_ASSOCIATION
        tender_data["contact_company_name"] = "Une asso"
        tender_data["extra_data"] = {"source": "TALLY"}
        response = self.client.post(
            self.url,
            data=tender_data,
            content_type="application/json",
            headers={"authorization": f"Bearer {self.user_token}"},
        )
        self.assertEqual(response.status_code, 201)
        tender = Tender.objects.get(title="Test tally contact")
        self.assertEqual(tender.source, TenderSourcesChoices.SOURCE_TALLY)
        author = tender.author
        self.assertEqual(author.email, "contact@example.com")
        self.assertEqual(author.kind, user_constants.KIND_BUYER)
        self.assertEqual(author.buyer_kind_detail, user_constants.BUYER_KIND_DETAIL_PUBLIC_ASSOCIATION)

    def test_create_tender_without_constraint(self):
        """An associated TenderInstruction does not exist but tender creation still proceed"""
        tender_data = TENDER_JSON.copy()
        tender_data["kind"] = "PROJ"
        response = self.client.post(
            self.url,
            data=tender_data,
            content_type="application/json",
            headers={"authorization": f"Bearer {self.user_token}"},
        )
        self.assertEqual(response.status_code, 201)


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
        cls.api_token_approch = "a" * 64
        cls.url = reverse("api:tenders-list")
        cls.user_partner_with_token = UserFactory(email="approch@example.com", api_key=cls.api_token_approch)

        TenderInstruction.objects.create(
            title="api_instruction",
            text="instruction",
            tender_type=KIND_TENDER,
            tender_source=TenderSourcesChoices.SOURCE_API,
        )

        TenderInstruction.objects.create(
            title="api_instruction",
            text="instruction",
            tender_type=KIND_PROJECT,
            tender_source=TenderSourcesChoices.SOURCE_API,
        )

    @patch("lemarche.api.tenders.views.add_to_contact_list")
    def test_partner_approch_can_create_tender(self, mock_add_to_contact_list):
        with self.settings(PARTNER_APPROCH_USER_ID=self.user_partner_with_token.id):
            # new tender
            tender_data = TENDER_JSON.copy()
            tender_data["contact_email"] = self.user_partner_with_token.email
            tender_data["extra_data"] = {"id": 123}
            response = self.client.post(
                self.url,
                data=tender_data,
                content_type="application/json",
                headers={"authorization": f"Bearer {self.api_token_approch}"},
            )
            self.assertEqual(response.status_code, 201)
            self.assertEqual(Tender.objects.count(), 1)
            tender = Tender.objects.last()
            self.assertEqual(tender.author, self.user_partner_with_token)
            self.assertEqual(tender.partner_approch_id, 123)

    @patch("lemarche.api.tenders.views.add_to_contact_list")
    def test_partner_approch_can_update_tender(self, mock_add_to_contact_list):
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
                self.url,
                data={**TENDER_JSON.copy(), **new_tender_partner_data},
                content_type="application/json",
                headers={"authorization": f"Bearer {self.api_token_approch}"},
            )
            self.assertEqual(response.status_code, 201)
            self.assertEqual(Tender.objects.count(), 1)
            self.assertEqual(Tender.objects.first().title, "Test changed")
            self.assertEqual(Tender.objects.first().deadline_date.strftime("%Y-%m-%d"), "2024-12-31")

    @patch("lemarche.api.tenders.views.add_to_contact_list")
    def test_partner_approch_new_tender_if_kind_changes(self, mock_add_to_contact_list):
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
                self.url,
                data={**TENDER_JSON.copy(), **new_tender_partner_data},
                content_type="application/json",
                headers={"authorization": f"Bearer {self.api_token_approch}"},
            )
            self.assertEqual(response.status_code, 201)
            self.assertEqual(Tender.objects.count(), 2)
            self.assertEqual(Tender.objects.last().title, "Test")
            self.assertEqual(Tender.objects.last().deadline_date.strftime("%Y-%m-%d"), "2024-06-30")
            self.assertEqual(Tender.objects.first().title, "Test changed")
            self.assertEqual(Tender.objects.first().deadline_date.strftime("%Y-%m-%d"), "2024-12-31")


class TenderChoicesApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_token = "a" * 64
        UserFactory(api_key=cls.user_token)
        cls.authenticated_client = cls.client_class(headers={"authorization": f"Bearer {cls.user_token}"})

    def test_should_return_tender_kinds_list(self):
        url = reverse("api:tender-kinds-list")
        response = self.authenticated_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 3)
        self.assertEqual(len(response.data["results"]), 3)
        self.assertTrue("id" in response.data["results"][0])
        self.assertTrue("name" in response.data["results"][0])

    def test_should_return_tender_amounts_list(self):
        url = reverse("api:tender-amounts-list")
        response = self.authenticated_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 14)
        self.assertEqual(len(response.data["results"]), 14)
        self.assertTrue("id" in response.data["results"][0])
        self.assertTrue("name" in response.data["results"][0])
