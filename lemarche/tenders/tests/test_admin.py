from unittest.mock import patch

from django.contrib.admin.sites import AdminSite
from django.contrib.messages import get_messages
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import HttpResponse
from django.test import RequestFactory, TestCase

from lemarche.tenders.admin import TenderAdmin
from lemarche.tenders.factories import TenderFactory
from lemarche.tenders.models import Tender
from lemarche.users.factories import UserFactory


# Create a dummy response function for the middleware
def get_response(request):
    return HttpResponse("OK")


class TenderAdminTestCase(TestCase):
    def setUp(self):
        # Initialize required objects for testing
        self.factory = RequestFactory()
        self.admin_site = AdminSite()
        self.user_admin = UserFactory(is_superuser=True)  # Admin user
        self.admin = TenderAdmin(Tender, self.admin_site)

    def setUpRequest(self):
        request = self.factory.post("/", data={"_validate_send_to_siaes": "1"})
        request.user = self.user_admin

        # Initialize and apply SessionMiddleware
        middleware = SessionMiddleware(get_response)
        middleware.process_request(request)

        # Attach a message storage system to the request
        setattr(request, "_messages", FallbackStorage(request))

        return request

    @patch("lemarche.tenders.admin.api_brevo.create_deal")  # Mock the create_deal API call
    @patch("lemarche.tenders.admin.api_brevo.link_deal_with_contact_list")  # Mock the link_deal API call
    def test_validate_send_to_siaes_not_synch_brevo(self, mock_link_deal, mock_create_deal):
        tender = TenderFactory(is_followed_by_us=False)  # Tender object
        request = self.setUpRequest()

        # Call the response_change method without the validation action enabled
        response = self.admin.response_change(request, tender)

        # Check that the create_deal and link_deal functions were not called
        mock_create_deal.assert_not_called()
        mock_link_deal.assert_not_called()

        # Verify the response
        self.assertEqual(response.status_code, 302)
        self.assertIn(".", response.url)

        # Verify the flash messages
        messages = list(get_messages(request))
        self.assertEqual(len(messages), 1)  # Expecting only one message
        self.assertEqual(str(messages[0]), "Ce dépôt de besoin a été validé. Il sera envoyé en temps voulu :)")

    @patch("lemarche.tenders.admin.api_brevo.create_deal")  # Mock the create_deal API call
    @patch("lemarche.tenders.admin.api_brevo.link_deal_with_contact_list")  # Mock the link_deal API call
    def test_validate_send_to_siaes_with_sync_brevo(self, mock_link_deal, mock_create_deal):
        tender = TenderFactory(is_followed_by_us=True)  # Tender object
        request = self.setUpRequest()

        # Call the response_change method
        response = self.admin.response_change(request, tender)

        # Verify that the tender is marked as validated
        tender.refresh_from_db()
        self.assertTrue(tender.is_validated)

        # Check if the create_deal and link_deal API methods were called
        mock_create_deal.assert_called_once_with(tender=tender, owner_email=self.user_admin.email)
        mock_link_deal.assert_called_once_with(tender=tender)

        # Ensure the response redirects correctly
        self.assertEqual(response.status_code, 302)
        self.assertIn(".", response.url)

        # Verify flash messages
        messages = list(get_messages(request))
        self.assertEqual(len(messages), 2)  # Expecting two messages
        self.assertEqual(str(messages[0]), "Ce dépôt de besoin a été synchronisé avec Brevo")
        self.assertEqual(str(messages[1]), "Ce dépôt de besoin a été validé. Il sera envoyé en temps voulu :)")
