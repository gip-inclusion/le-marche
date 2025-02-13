from unittest.mock import patch, MagicMock

from django.test import TestCase

from lemarche.companies.factories import CompanyFactory


class CompanySignalTest(TestCase):
    @patch("lemarche.utils.apis.api_brevo.create_company")
    def test_create_company_in_brevo_signal(self, mock_create_company):
        """Test that creating a new company triggers the Brevo sync"""
        # Create a new company
        company = CompanyFactory()

        # Verify create_company was called once with the company instance
        mock_create_company.assert_called_once_with(company)

        # Create another company
        company2 = CompanyFactory()
        self.assertEqual(mock_create_company.call_count, 2)
        mock_create_company.assert_called_with(company2)

        # Update existing company
        company.name = "Updated Name"
        company.save()

        # Call count should still be 2 since we only sync on creation
        self.assertEqual(mock_create_company.call_count, 2)

    @patch("lemarche.utils.apis.api_brevo.sib_api_v3_sdk.CompaniesApi")
    def test_company_attributes_sent_to_brevo(self, mock_companies_api):
        """Test the attributes sent to Brevo when creating a company"""
        # Setup the mock response
        mock_response = MagicMock()
        mock_response.id = 12345
        mock_instance = mock_companies_api.return_value
        mock_instance.companies_post.return_value = mock_response

        # Create a company
        company = CompanyFactory(name="Test Company", website="https://example.com")

        # Get the Body instance that was passed to companies_post
        args, kwargs = mock_instance.companies_post.call_args
        body_obj = args[0]

        self.assertEqual(body_obj.name, "Test Company")
        self.assertEqual(body_obj.attributes, {"domain": "https://example.com", "app_id": company.id, "siae": False})

        self.assertEqual(company.brevo_company_id, 12345)
