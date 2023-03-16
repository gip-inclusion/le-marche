from django.test import TestCase
from django.urls import reverse

from lemarche.tenders.models import Tender
from lemarche.users.factories import UserFactory


TENDER_JSON = {
    "kind": "TENDER",
    "title": "string",
    "sectors": [],
    "presta_type": ["DISP"],
    "location": "",
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
        response = self.client.post(url, data=TENDER_JSON)
        self.assertEqual(response.status_code, 201)
        tender = Tender.objects.first()
        self.assertEqual(tender.author, self.user_with_token)
